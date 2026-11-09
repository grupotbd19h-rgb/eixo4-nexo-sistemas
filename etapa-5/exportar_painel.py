"""Exporta, do modelo estrela, os conjuntos que o painel consome, em JSON.

    python exportar_painel.py <saida_estrela> <destino.json>

Os números saem daqui, do mesmo modelo que o Athena lê — o painel não recalcula
nada, só desenha. É o que garante que o gráfico e a consulta contem a mesma coisa.
"""
import json
import sys
from pathlib import Path

import pandas as pd

origem, destino = Path(sys.argv[1]), Path(sys.argv[2])
ler = lambda t: pd.read_parquet(origem / t / f"{t}.parquet")

f = ler("fato_oportunidade")
inv = ler("fato_investimento_anuncio")
camp = ler("dim_campanha")
col = ler("dim_colaborador")

investimento_total = float(inv.investimento.sum())
contratos = int(f.ganha.sum())
receita = float(f.loc[f.ganha, "valor_contrato_12m"].sum())

# Custo de aquisição só faz sentido sobre o que o investimento explica. Dividir
# o gasto por todos os contratos — inclusive os que chegaram sem campanha
# identificada — barateia o indicador artificialmente. Esse foi exatamente o
# erro corrigido na consulta 2.b, e ele não pode voltar pela porta dos fundos.
SINTETICAS = ["SEM_UTM", "UTM_QUEBRADA"]
atribuido = f.ganha & ~f.id_campanha.isin(SINTETICAS)
contratos_atribuidos = int(atribuido.sum())
receita_atribuida = float(f.loc[atribuido, "valor_contrato_12m"].sum())

# --- indicadores de topo -----------------------------------------------------
resumo = {
    "oportunidades": int(len(f)),
    "contratos": contratos,
    "conversao": round(100 * contratos / len(f), 2),
    "investimento": round(investimento_total, 2),
    "receita12m": round(receita, 2),
    "contratosAtribuidos": contratos_atribuidos,
    "receitaAtribuida": round(receita_atribuida, 2),
    "cac": round(investimento_total / contratos_atribuidos, 2),
    "retorno": round(receita_atribuida / investimento_total, 2),
    "ticketMedio": round(receita / contratos, 2),
}

# --- conversão por faixa de tempo até o primeiro contato ---------------------
faixas = pd.cut(f.horas_ate_primeiro_contato, [-1, 1, 24, 72, 1e9],
                labels=["Até 1h", "1 a 24h", "24 a 72h", "Mais de 72h"])
faixas = faixas.cat.add_categories(["Nunca contatada"]).fillna("Nunca contatada")
resposta = (f.groupby(faixas, observed=True)
            .agg(oportunidades=("ganha", "size"), contratos=("ganha", "sum"))
            .reset_index(names="faixa"))
resposta["conversao"] = (100 * resposta.contratos / resposta.oportunidades).round(2)

# --- funil mês a mês ---------------------------------------------------------
mes = pd.to_datetime(f.data_criacao).dt.to_period("M").astype(str)
funil = (f.groupby(mes, observed=True)
         .agg(oportunidades=("ganha", "size"), contratos=("ganha", "sum"))
         .reset_index(names="mes"))
funil["conversao"] = (100 * funil.contratos / funil.oportunidades).round(2)
receita_mes = f[f.ganha].groupby(mes).valor_contrato_12m.sum().round(2)
funil["receita12m"] = funil.mes.map(receita_mes).fillna(0)
# O recorte da operação começa em março. Janeiro e fevereiro só têm as poucas
# oportunidades de aquecimento que seguiram abertas, e uma base de duas ou três
# linhas produz percentual sem significado — que ainda por cima domina a escala
# do gráfico. Ficam de fora da série temporal, e continuam no total.
funil = funil[funil.mes >= "2026-03"].reset_index(drop=True)

# --- desempenho por campanha -------------------------------------------------
gasto = inv.groupby("id_campanha").investimento.sum()
por_campanha = f.groupby("id_campanha").agg(
    oportunidades=("ganha", "size"),
    contratos=("ganha", "sum"),
    receita12m=("valor_contrato_12m", lambda s: s[f.loc[s.index, "ganha"]].sum()),
).join(gasto).join(camp.set_index("id_campanha")[["nome_campanha", "objetivo"]])
por_campanha["investimento"] = por_campanha.investimento.fillna(0).round(2)
por_campanha["cac"] = (por_campanha.investimento / por_campanha.contratos).round(2)
por_campanha["retorno"] = (por_campanha.receita12m / por_campanha.investimento).round(2)
por_campanha = por_campanha.replace([float("inf")], None).reset_index()

# --- CAC por plano, com rateio proporcional ----------------------------------
ganhas = f[f.ganha]
pares = ganhas.groupby(["id_campanha", "plano_contratado"]).size().rename("contratos").reset_index()
total = pares.groupby("id_campanha").contratos.sum().rename("total")
pares = pares.join(total, on="id_campanha").join(gasto, on="id_campanha")
pares["rateio"] = pares.investimento * pares.contratos / pares.total
por_plano = (pares.dropna(subset=["rateio"])
             .groupby("plano_contratado")
             .agg(contratos=("contratos", "sum"), investimento=("rateio", "sum"))
             .reset_index(names="plano"))
por_plano["cac"] = (por_plano.investimento / por_plano.contratos).round(2)
por_plano["investimento"] = por_plano.investimento.round(2)

# --- cobertura de rastreio ---------------------------------------------------
sinteticas = ["SEM_UTM", "UTM_QUEBRADA"]
atribuida = ~f.id_campanha.isin(sinteticas)
rastreio = [
    {"situacao": "Atribuída a campanha", "oportunidades": int(atribuida.sum()),
     "contratos": int(f.ganha[atribuida].sum())},
    {"situacao": "Sem UTM", "oportunidades": int((f.id_campanha == "SEM_UTM").sum()),
     "contratos": int(f.ganha[f.id_campanha == "SEM_UTM"].sum())},
    {"situacao": "UTM não substituída", "oportunidades": int((f.id_campanha == "UTM_QUEBRADA").sum()),
     "contratos": int(f.ganha[f.id_campanha == "UTM_QUEBRADA"].sum())},
]

# --- ranking de closer -------------------------------------------------------
closers = f.merge(col, left_on="id_closer", right_on="id_colaborador")
ranking = (closers.groupby(["id_colaborador", "time", "tier"])
           .agg(oportunidades=("ganha", "size"), contratos=("ganha", "sum"),
                receita12m=("valor_contrato_12m", lambda s: s[closers.loc[s.index, "ganha"]].sum()))
           .reset_index())
ranking["conversao"] = (100 * ranking.contratos / ranking.oportunidades).round(2)
ranking = ranking.sort_values("receita12m", ascending=False).head(10)

# --- times: quem trabalhou o funil, e contra que meta --------------------------
# O time comercial da Nexo tem quatro frentes operacionais: Pré-vendas qualifica,
# Pequeno Varejo e Contas Corporativas fecham, Recuperação retoma contrato perdido.
# Cada função tem um tipo de meta diferente, e só a do closer é verificável contra
# o funil — as outras dependem de evento que a base não registra. Isso é dito na
# página, em vez de maquiado com um número inventado.
metas = ler("fato_meta_vendedor")
mes_fechamento = pd.to_datetime(f.data_fechamento).dt.to_period("M").astype(str)
mes_meta = pd.to_datetime(metas.data).dt.to_period("M").astype(str)

# realizado do closer: valor dos contratos de 12 meses fechados no mês
realizado = (f[f.ganha].assign(mes=mes_fechamento[f.ganha])
             .groupby(["id_closer", "mes"]).valor_contrato_12m.sum().rename("realizado"))
meta_closer = (metas[metas.tipo_meta == "valor_vendido_anual"]
               .assign(mes=mes_meta[metas.tipo_meta == "valor_vendido_anual"])
               .set_index(["id_colaborador", "mes"]).valor_meta.rename("meta"))
confronto = pd.concat([meta_closer, realizado], axis=1).fillna(0).reset_index()
confronto.columns = ["id_colaborador", "mes", "meta", "realizado"]

meta_mensal = confronto.groupby("mes")[["meta", "realizado"]].sum().round(2).reset_index()
meta_mensal["atingimento"] = (100 * meta_mensal.realizado / meta_mensal.meta).round(1)

# desempenho individual: cada pessoa na função em que ela atua no funil
atuacao = pd.concat([
    f[["id_sdr", "ganha", "valor_contrato_12m", "horas_ate_primeiro_contato"]]
        .rename(columns={"id_sdr": "id_colaborador"}).assign(papel="SDR"),
    f[f.id_closer.notna() & (f.id_closer != "")][
        ["id_closer", "ganha", "valor_contrato_12m", "horas_ate_primeiro_contato"]]
        .rename(columns={"id_closer": "id_colaborador"}).assign(papel="Closer"),
])
atuacao = atuacao[atuacao.id_colaborador.notna() & (atuacao.id_colaborador != "")]
# o concat acima repete índice; a receita vai em coluna própria para não depender dele
atuacao["receita_ganha"] = atuacao.valor_contrato_12m.where(atuacao.ganha, 0.0)

pessoas = (atuacao.groupby(["id_colaborador", "papel"])
           .agg(oportunidades=("ganha", "size"),
                contratos=("ganha", "sum"),
                receita12m=("receita_ganha", "sum"),
                medianaHoras=("horas_ate_primeiro_contato", "median"))
           .reset_index()
           .merge(col[["id_colaborador", "funcao", "tier", "time"]], on="id_colaborador"))
pessoas["conversao"] = (100 * pessoas.contratos / pessoas.oportunidades).round(2)
pessoas["medianaHoras"] = pessoas.medianaHoras.round(1)
alvo = confronto.groupby("id_colaborador")[["meta", "realizado"]].sum()
pessoas = pessoas.join(alvo, on="id_colaborador")
pessoas["atingimento"] = (100 * pessoas.realizado / pessoas.meta).round(1)

def limpar(registros):
    """NaN não existe em JSON: vira null, que o TypeScript trata como ausência."""
    return [{c: (None if isinstance(v, float) and pd.isna(v) else v) for c, v in r.items()}
            for r in registros]


por_time = (pessoas.groupby(["time", "papel"])
            .agg(pessoas=("id_colaborador", "nunique"),
                 oportunidades=("oportunidades", "sum"),
                 contratos=("contratos", "sum"),
                 receita12m=("receita12m", "sum"))
            .reset_index())
por_time["conversao"] = (100 * por_time.contratos / por_time.oportunidades).round(2)

fechadores = pessoas[pessoas.papel == "Closer"]
por_tier = (fechadores.groupby("tier")
            .agg(pessoas=("id_colaborador", "nunique"),
                 oportunidades=("oportunidades", "sum"),
                 contratos=("contratos", "sum"),
                 receita12m=("receita12m", "sum"))
            .reset_index())
por_tier["conversao"] = (100 * por_tier.contratos / por_tier.oportunidades).round(2)
por_tier["tier"] = por_tier.tier.astype(int)

metas_sem_confronto = (metas[metas.tipo_meta != "valor_vendido_anual"]
                       .groupby(["funcao", "tipo_meta"])
                       .agg(pessoas=("id_colaborador", "nunique"),
                            media=("valor_meta", "mean"))
                       .reset_index())
metas_sem_confronto["media"] = metas_sem_confronto.media.round(1)

times = {
    "porTime": limpar(por_time.to_dict("records")),
    "porTier": limpar(por_tier.to_dict("records")),
    "metaMensal": limpar(meta_mensal.to_dict("records")),
    "pessoas": limpar(pessoas.sort_values("receita12m", ascending=False).to_dict("records")),
    "metasSemConfronto": limpar(metas_sem_confronto.to_dict("records")),
    "efetivo": int(col.id_colaborador.nunique()),
}

painel = {
    "geradoEm": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
    "periodo": {
        "inicio": str(pd.to_datetime(inv.data).min().date()),
        "fim": str(pd.to_datetime(inv.data).max().date()),
        "origens": 3,
        "campanhas": int((~camp.id_campanha.isin(SINTETICAS)).sum()),
    },
    "times": times,
    "resumo": resumo,
    "resposta": resposta.to_dict("records"),
    "funil": funil.to_dict("records"),
    "campanhas": por_campanha.to_dict("records"),
    "planos": por_plano.to_dict("records"),
    "rastreio": rastreio,
    "ranking": ranking.to_dict("records"),
}

destino.write_text(json.dumps(painel, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{destino} — {destino.stat().st_size / 1024:.1f} KB")
for chave, valor in painel.items():
    print(f"  {chave}: {len(valor) if isinstance(valor, list) else len(valor)} itens")
