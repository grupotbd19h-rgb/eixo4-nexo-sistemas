"""
Gera as bases sintéticas da Nexo Sistemas (Eixo 4 — Etapa 2).

Uso:  python gerar_bases.py <pasta_dados>

A ESTRUTURA segue regras_base_ficticia.md: etapas do funil, campos do CRM, UTMs (com
leads sem UTM e UTM quebrada), temperatura do lead, papéis e tiers do time, tipos de
campanha, inadimplência, distratos e comissão por faixa de volume com trava de caixa.
Os NÚMEROS seguem o caso da Nexo na Etapa 1: ~3.000 oportunidades/mês, ~3% de
conversão, 31% sem contato em 72h, planos de R$ 190/390/990 e ~2.500 clientes ativos.

Janela: 6 meses (mar a ago/2026). Jan e fev também são simulados para o funil já
chegar cheio em março; dessas, só entram no CRM as oportunidades não encerradas até 01/03.

Escreve uma pasta por sistema de origem, cada uma no formato do próprio sistema:
  meta_ads/  crm/  planilhas_comerciais/
O CRM guarda só a UTM, não o ID da campanha: ligar oportunidade a investimento é
trabalho da integração. Semente fixa: rodar de novo produz os mesmos arquivos.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEMENTE = 42
AQUECIMENTO = pd.period_range("2026-01", "2026-02", freq="M")
MESES = pd.period_range("2026-03", "2026-08", freq="M")
INICIO = MESES[0].start_time
FIM = MESES[-1].end_time.floor("s")
INICIO_BASE_ANTIGA = pd.Timestamp("2016-03-01")  # fundação da empresa

# ---------------------------------------------------------------- funil / CRM
LEADS_MES = 3000
SAZONALIDADE = {1: 0.88, 2: 0.90, 8: 1.08}  # md: jan–fev fracos, ago–nov fortes
CONVERSAO_ALVO = 0.030

# Tempo até o 1º contato, no formato da md e calibrado para 31% sem contato em 72h:
# (probabilidade acumulada, horas mín., horas máx.); o restante (12%) nunca é contatado.
FAIXAS_CONTATO = [(0.35, 0.02, 1), (0.58, 1, 24), (0.69, 24, 72), (0.88, 72, 240)]
EFEITO_CONTATO = [(1, 1.8), (24, 1.2), (72, 0.8), (np.inf, 0.35)]  # (até N horas, efeito na qualificação)

# Transições do funil: (etapa alcançada, taxa, dias desde a etapa anterior).
# Taxas na forma da md, ajustadas para o total dar ~3% com FUP → venda ≈ 20%.
TRANSICOES = [
    ("qualificado", 0.33, (1, 3)),
    ("contato_1", 0.90, (0.2, 1.5)),
    ("reuniao", 0.65, (2, 5)),
    ("follow_up", 0.78, (3, 10)),
    ("forecast", 0.21, (5, 20)),
    ("fechado_ganho", 0.95, (3, 14)),
]
FASES = ["lead_recebido", "qualificacao", "contato_1", "contato_2", "contato_3", "reuniao", "follow_up", "forecast"]

MOTIVOS_PERDA = {  # grupo: (motivos, pesos)
    "inicio": (["sem_interesse_nao_respondeu", "nao_qualifica", "sem_retorno_lead_frio"], [0.45, 0.30, 0.25]),
    "meio": (["sem_interesse_nao_respondeu", "nao_e_o_momento", "sem_retorno_lead_frio",
              "vai_continuar_com_planilha", "nao_qualifica"], [0.30, 0.25, 0.20, 0.15, 0.10]),
    "fim": (["preco", "escolheu_concorrente", "nao_e_o_momento", "vai_continuar_com_planilha"], [0.40, 0.28, 0.22, 0.10]),
}
GRUPO_PERDA = {"qualificado": "inicio", "contato_1": "meio", "reuniao": "meio",
               "follow_up": "fim", "forecast": "fim", "fechado_ganho": "fim"}

TEMPERATURAS = [0.25, 0.50, 0.75]
EFEITO_TEMPERATURA = {0.25: 0.6, 0.50: 1.3, 0.75: 2.3}
PESO_TIER = {1: 1.5, 2: 1.0, 3: 0.6}  # round-robin ponderado pela tier

# ---------------------------------------------------------------- produto
PLANOS = pd.DataFrame({
    "plano": ["Essencial", "Profissional", "Corporativo"],
    "mensalidade": [190.0, 390.0, 990.0],
    "perfil_cliente": ["Microempresas e autônomos", "Pequenas empresas", "Médias empresas e redes de lojas"],
})
NOMES_PLANOS = list(PLANOS.plano)
MENSALIDADE = dict(zip(PLANOS.plano, PLANOS.mensalidade))
PORTE_DO_PLANO = {"Essencial": "Micro", "Profissional": "Pequena", "Corporativo": "Média"}
CONV_PLANO = {"Essencial": 1.00, "Profissional": 1.05, "Corporativo": 0.75}
DESCONTOS, PESO_DESCONTOS = [0.0, 0.10, 0.20], [0.85, 0.10, 0.05]
SEGMENTOS = {  # segmento: (peso na captação, efeito na conversão)
    "Mercado e mercearia": (0.22, 1.10), "Vestuário e calçados": (0.18, 0.95),
    "Materiais de construção": (0.10, 1.20), "Farmácia e perfumaria": (0.08, 1.05),
    "Autopeças": (0.08, 1.00), "Papelaria e presentes": (0.07, 0.85),
    "Pet shop": (0.07, 0.90), "Outros": (0.20, 0.80),
}
REGIOES = {  # região: (parcela, UFs, peso de cada UF na região) — parcelas da md
    "Sudeste": (0.62, ["SP", "MG", "RJ", "ES"], [0.62, 0.20, 0.14, 0.04]),
    "Sul": (0.21, ["PR", "RS", "SC"], [0.37, 0.36, 0.27]),
    "Nordeste": (0.10, ["BA", "PE", "CE", "MA", "PB", "RN", "AL", "PI", "SE"],
                 [0.28, 0.20, 0.18, 0.08, 0.07, 0.07, 0.05, 0.04, 0.03]),
    "Centro-Oeste": (0.045, ["GO", "DF", "MT", "MS"], [0.45, 0.25, 0.17, 0.13]),
    "Norte": (0.025, ["PA", "AM", "RO", "TO", "AC", "AP", "RR"], [0.40, 0.30, 0.12, 0.08, 0.04, 0.03, 0.03]),
}
UFS = [uf for _, ufs, _ in REGIOES.values() for uf in ufs]
PESO_UF = np.array([p * w for p, _, ws in REGIOES.values() for w in ws])
PESO_UF = PESO_UF / PESO_UF.sum()

# ---------------------------------------------------------------- canais e campanhas
# O Google Ads ficou fora do recorte da Etapa 2: as parcelas dos canais restantes foram
# renormalizadas entre si, o que mantém o volume de 3.000 leads/mês do caso.
CANAIS = {  # parcela na entrada (md, sem TikTok/outros), efeito na conversão, mix de planos, origem, temperatura
    "meta_ads": {"parcela": 0.76, "conv": 0.85, "mix_planos": [0.58, 0.35, 0.07],
                 "origens": (["formulario", "chat", "agendamento_bot"], [0.60, 0.30, 0.10]),
                 "temperatura": [0.63, 0.26, 0.11]},
    "organico": {"parcela": 0.15, "conv": 1.30, "mix_planos": [0.45, 0.42, 0.13],
                 "origens": (["chat", "formulario", "ligacao"], [0.40, 0.40, 0.20]),
                 "temperatura": [0.55, 0.30, 0.15]},
    "indicacao": {"parcela": 0.09, "conv": 2.20, "mix_planos": [0.35, 0.45, 0.20],
                  "origens": (["indicacao"], [1.0]),
                  "temperatura": [0.35, 0.35, 0.30]},
}
UTM_SOURCE = {"meta_ads": "meta"}
SEM_UTM, UTM_QUEBRADA = 0.07, 0.02  # parcela dos leads pagos

# CPC e CTR nas faixas da md por tipo; CPL calibrado para ~R$ 90 mil/mês de mídia (Etapa 1).
CAMPANHAS = pd.DataFrame([
    ("meta_ads", "MT_LEADS_PEQ_VAREJO_001", "OUTCOME_LEADS", "cpc", 0.32, 24, 1.0, 0.025),
    ("meta_ads", "MT_LEADS_REDES_LOJAS_002", "OUTCOME_LEADS", "cpc", 0.18, 30, 1.3, 0.022),
    ("meta_ads", "MT_TRAFEGO_LP_001", "OUTCOME_TRAFFIC", "cpc", 0.20, 34, 1.1, 0.024),
    ("meta_ads", "MT_RMKT_SITE_001", "OUTCOME_SALES", "cpm", 0.18, 22, 1.2, 0.028),
    ("meta_ads", "MT_VIDEO_ESTOQUE_001", "OUTCOME_AWARENESS", "social", 0.12, 38, 0.9, 0.020),
], columns=["plataforma", "nome_campanha", "tipo", "utm_medium", "peso", "cpl", "cpc", "ctr"])
TERMOS_BUSCA = {}  # só campanha de busca tem termo; não há nenhuma no recorte atual

# ---------------------------------------------------------------- cobrança
CHURN_MENSAL = {"Essencial": 0.042, "Profissional": 0.033, "Corporativo": 0.035}
BASE_INICIAL = {"Essencial": 1100, "Profissional": 1150, "Corporativo": 250}
ARREPENDIMENTO_7D, DISTRATO_8_90D = 0.008, 0.015  # parcela das vendas novas (md)
MOTIVOS_DISTRATO = ["mudanca_de_decisao", "atraso_na_implantacao", "problema_financeiro", "insatisfacao_atendimento"]
MOTIVOS_CANCELAMENTO = (["preco", "encerrou_atividade", "migrou_concorrente", "insatisfacao_atendimento",
                         "atraso_na_implantacao", "problema_financeiro"], [0.20, 0.22, 0.18, 0.18, 0.07, 0.15])
MEIOS_PAGAMENTO = (["cartao_credito", "boleto", "pix", "transferencia", "outros"], [0.55, 0.22, 0.13, 0.08, 0.02])
# Pagamento da fatura (md): em dia, atraso < 30d, 30–60d, > 60d; o restante (2%) nunca paga.
FAIXAS_ATRASO = [(0.84, -5, 0), (0.94, 1, 29), (0.96, 30, 60), (0.98, 61, 120)]

# ---------------------------------------------------------------- comissão e metas
# Faixas da md, em escala Nexo: venda do mês = soma do valor anual dos contratos fechados.
# Caixa = parcela desse valor cuja 1ª mensalidade foi paga em até 30 dias; abaixo do mínimo cai uma faixa.
FAIXAS_COMISSAO = pd.DataFrame({
    "faixa": [1, 2, 3, 4, 5],
    "venda_anual_min": [0.0, 12000.0, 20000.0, 30000.0, 45000.0],
    "venda_anual_max": [11999.99, 19999.99, 29999.99, 44999.99, None],
    "percentual_comissao": [0.00, 0.06, 0.08, 0.10, 0.12],
    "caixa_minimo": [None, 0.75, 0.75, 0.75, 0.75],
})
REGRAS_BONUS = pd.DataFrame([
    ("Recuperador", "percentual sobre o valor anual do contrato recuperado", 0.05),
    ("Gestor", "percentual sobre o valor anual vendido pelo time", 0.003),
    ("Gestor", "peso do caixa no multiplicador", 0.50),
    ("Gestor", "peso da venda no multiplicador", 0.50),
    ("Gestor", "trava: atingimento mínimo da meta de venda do time", 0.60),
    ("Gestor", "trava: caixa mínimo do time", 0.75),
], columns=["papel", "regra", "valor"])
META_CLOSER = {("Pequeno Varejo", 1): 32000, ("Pequeno Varejo", 2): 21000, ("Pequeno Varejo", 3): 13000,
               ("Contas Corporativas", 1): 40000, ("Contas Corporativas", 2): 28000, ("Contas Corporativas", 3): 18000}
META_SDR = {1: 80, 2: 65, 3: 50}  # reuniões realizadas no mês
META_RECUPERADOR = 3  # contratos recuperados no mês

PESO_HORA = np.array([0.2] * 7 + [1.0] + [3.0] * 11 + [2.0] * 3 + [0.8] * 2)
PESO_HORA = PESO_HORA / PESO_HORA.sum()

rng = np.random.default_rng(SEMENTE)


def instantes_no_mes(mes, n):
    dias = rng.integers(0, mes.days_in_month, n)
    horas = rng.choice(24, n, p=PESO_HORA)
    segundos = rng.integers(0, 3600, n)
    return (mes.start_time + pd.to_timedelta(dias, "D") + pd.to_timedelta(horas, "h")
            + pd.to_timedelta(segundos, "s"))


def sorteio_por_faixas(n, faixas):
    """Sorteia um valor uniforme dentro de faixas (prob. acumulada, mín., máx.); fora delas, NaN."""
    r = rng.random(n)
    valores = np.full(n, np.nan)
    anterior = 0.0
    for acumulado, vmin, vmax in faixas:
        m = (r >= anterior) & (r < acumulado)
        valores[m] = rng.uniform(vmin, vmax, m.sum())
        anterior = acumulado
    return valores


def sortear_por_tier(pessoas, n):
    peso = pessoas.tier.map(PESO_TIER).to_numpy(float)
    return rng.choice(pessoas.id_colaborador.to_numpy(), n, p=peso / peso.sum())


def gerar_equipe():
    linhas = [("GES01", "Gestor", None, "Comercial")]
    linhas += [(f"SDR{i:02d}", "SDR", t, "Pré-vendas") for i, t in enumerate([1, 1, 1, 2, 2, 2, 3, 3, 3], 1)]
    linhas += [(f"CLO{i:02d}", "Closer", t, "Contas Corporativas") for i, t in enumerate([1, 1, 2, 3], 1)]
    linhas += [(f"CLO{i:02d}", "Closer", t, "Pequeno Varejo")
               for i, t in enumerate([1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3], 5)]
    linhas += [(f"REC{i:02d}", "Recuperador", None, "Recuperação") for i in range(1, 4)]
    equipe = pd.DataFrame(linhas, columns=["id_colaborador", "funcao", "tier", "pipeline"])
    equipe["tier"] = equipe.tier.astype("Int64")
    equipe["data_admissao"] = (pd.Timestamp("2019-01-01")
                               + pd.to_timedelta(rng.integers(0, 2500, len(equipe)), "D")).date
    return equipe


def gerar_oportunidades(equipe):
    lotes = [instantes_no_mes(m, rng.poisson(LEADS_MES * SAZONALIDADE.get(m.month, 1.0)))
             for m in AQUECIMENTO.append(MESES)]
    op = pd.DataFrame({"data_criacao": np.concatenate([l.to_numpy() for l in lotes])})
    op = op.sort_values("data_criacao").reset_index(drop=True)
    n = len(op)

    # ---- perfil do lead
    canais = list(CANAIS)
    op["canal"] = rng.choice(canais, n, p=[CANAIS[c]["parcela"] for c in canais])
    op["plano_interesse"] = None
    op["origem_lead"] = None
    op["temperatura"] = 0.0
    op["campanha"] = -1
    for canal, cfg in CANAIS.items():
        m = (op.canal == canal).to_numpy()
        k = m.sum()
        op.loc[m, "plano_interesse"] = rng.choice(NOMES_PLANOS, k, p=cfg["mix_planos"])
        origens, pesos = cfg["origens"]
        op.loc[m, "origem_lead"] = rng.choice(origens, k, p=pesos)
        op.loc[m, "temperatura"] = rng.choice(TEMPERATURAS, k, p=cfg["temperatura"])
        if canal in UTM_SOURCE:
            idx = CAMPANHAS.index[CAMPANHAS.plataforma == canal].to_numpy()
            peso = CAMPANHAS.peso[idx].to_numpy()
            op.loc[m, "campanha"] = rng.choice(idx, k, p=peso / peso.sum())
    op["segmento_varejo"] = rng.choice(list(SEGMENTOS), n, p=[v[0] for v in SEGMENTOS.values()])
    op["uf"] = rng.choice(UFS, n, p=PESO_UF)
    op["porte_empresa"] = np.where(rng.random(n) < 0.85, op.plano_interesse.map(PORTE_DO_PLANO),
                                   rng.choice(list(PORTE_DO_PLANO.values()), n))
    op["pipeline"] = np.where(op.plano_interesse == "Corporativo", "Contas Corporativas", "Pequeno Varejo")

    # ---- probabilidade de avançar em cada transição
    horas = sorteio_por_faixas(n, FAIXAS_CONTATO)
    op["horas_contato"] = horas
    efeito_contato = np.select([horas < lim for lim, _ in EFEITO_CONTATO], [e for _, e in EFEITO_CONTATO], 0.0)
    perfil = (op.canal.map(lambda c: CANAIS[c]["conv"]) * op.plano_interesse.map(CONV_PLANO)
              * op.segmento_varejo.map(lambda s: SEGMENTOS[s][1]) * op.temperatura.map(EFEITO_TEMPERATURA)).to_numpy()
    perfil = perfil / perfil.mean()

    prob = {etapa: np.full(n, taxa) for etapa, taxa, _ in TRANSICOES}
    prob["qualificado"] = prob["qualificado"] * efeito_contato * perfil ** 0.5
    for etapa in ["contato_1", "reuniao", "follow_up", "forecast"]:
        prob[etapa] = prob[etapa] * perfil ** 0.125
    resto = np.prod([np.minimum(prob[e], 0.98) for e, _, _ in TRANSICOES[1:]], axis=0)
    base, fator = prob["qualificado"], 1.0
    for _ in range(10):  # calibra a qualificação para a conversão total dar CONVERSAO_ALVO
        fator *= CONVERSAO_ALVO / (np.minimum(base * fator, 0.98) * resto).mean()
    prob["qualificado"] = np.minimum(base * fator, 0.98)

    # ---- percurso de cada lead pelo funil
    contato = op.data_criacao + pd.to_timedelta(horas, "h")  # NaT se nunca contatado
    alcancada = {}
    vivo = contato.notna().to_numpy()
    anterior = contato
    data_perda = op.data_criacao + pd.to_timedelta(rng.uniform(10, 20, n), "D")  # nunca contatado
    etapa_perda = np.where(vivo, None, "qualificado").astype(object)
    for etapa, _, (dmin, dmax) in TRANSICOES:
        passa = vivo & (rng.random(n) < prob[etapa])
        perde = vivo & ~passa
        data = anterior + pd.to_timedelta(rng.uniform(dmin, dmax, n), "D")
        data_perda = data_perda.where(~perde, anterior + pd.to_timedelta(rng.uniform(1, 7, n), "D"))
        etapa_perda[perde] = etapa
        alcancada[etapa] = data.where(passa)
        vivo, anterior = passa, data
    ganho = vivo

    entrada = {
        "lead_recebido": op.data_criacao, "qualificacao": contato, "contato_1": alcancada["contato_1"],
        "contato_2": alcancada["contato_1"] + pd.Timedelta(days=1.5),
        "contato_3": alcancada["contato_1"] + pd.Timedelta(days=3),
        "reuniao": alcancada["reuniao"], "follow_up": alcancada["follow_up"], "forecast": alcancada["forecast"],
    }

    def fase_em(instante):
        idx = np.zeros(n, dtype=int)
        for i, fase in enumerate(FASES):
            idx[(entrada[fase] <= instante).to_numpy()] = i
        return idx

    final = alcancada["fechado_ganho"].where(ganho, data_perda)
    fechado = (final <= FIM).to_numpy()
    op["status"] = np.where(~fechado, "aberta", np.where(ganho, "ganha", "perdida"))
    fase_aberta = fase_em(FIM)
    entrada_aberta = pd.Series(pd.NaT, index=op.index, dtype="datetime64[ns]")
    for i, fase in enumerate(FASES):
        m = fase_aberta == i
        entrada_aberta[m] = entrada[fase][m]
    op["fase_atual"] = np.select([op.status == "ganha", op.status == "perdida"],
                                 ["fechado_ganho", "fechado_perdido"], np.array(FASES)[fase_aberta])
    op["data_entrada_fase"] = entrada_aberta.where(~fechado, final)
    perdida = (op.status == "perdida").to_numpy()
    op["fase_perda"] = np.where(perdida, np.array(FASES)[fase_em(data_perda - pd.Timedelta(seconds=1))], None)
    motivo = np.full(n, None, dtype=object)
    for grupo, (motivos, pesos) in MOTIVOS_PERDA.items():
        m = perdida & np.isin(etapa_perda, [e for e, g in GRUPO_PERDA.items() if g == grupo])
        motivo[m] = rng.choice(motivos, m.sum(), p=pesos)
    op["motivo_perda"] = motivo

    def ate_fim(s):
        return s.where(s <= FIM)

    op["data_primeiro_contato"] = ate_fim(contato)
    op["data_qualificacao"] = ate_fim(alcancada["qualificado"])
    op["data_reuniao"] = ate_fim(alcancada["reuniao"])
    op["data_follow_up"] = ate_fim(alcancada["follow_up"])
    op["data_forecast"] = ate_fim(alcancada["forecast"])
    op["data_fechamento"] = final.where(fechado)

    # ---- responsáveis
    contatado = contato.notna().to_numpy()
    no_pool = ~contatado & (rng.random(n) < 0.40)
    op["id_sdr"] = np.where(no_pool, None, sortear_por_tier(equipe[equipe.funcao == "SDR"], n))
    closers = equipe[equipe.funcao == "Closer"]
    closer = np.where(op.pipeline == "Contas Corporativas",
                      sortear_por_tier(closers[closers.pipeline == "Contas Corporativas"], n),
                      sortear_por_tier(closers[closers.pipeline == "Pequeno Varejo"], n))
    op["id_closer"] = np.where((alcancada["contato_1"] <= FIM).to_numpy(), closer, None)
    recuperado = (((op.status == "ganha").to_numpy() & (rng.random(n) < 0.07))
                  | (perdida & np.isin(etapa_perda, ["reuniao", "follow_up"]) & (rng.random(n) < 0.10)))
    op["id_recuperador"] = np.where(recuperado, rng.choice(equipe.id_colaborador[equipe.funcao == "Recuperador"], n), None)
    op["qtd_tentativas_contato"] = np.where(contatado, 1 + np.minimum(rng.poisson(1.5, n), 5), rng.integers(0, 4, n))
    op["passou_por_chat"] = (op.origem_lead == "chat") | (rng.random(n) < 0.10)
    op["reuniao_agendada_bot"] = (op.origem_lead == "agendamento_bot") & op.data_reuniao.notna()

    # ---- campos de qualificação (preenchimento baixo, 7%)
    preenchido = rng.random(n) < 0.07
    faturamento = np.select(
        [op.porte_empresa == "Micro", op.porte_empresa == "Pequena"],
        [rng.choice(["ate_30k", "30k_100k"], n, p=[0.7, 0.3]), rng.choice(["30k_100k", "100k_300k"], n)],
        rng.choice(["100k_300k", "300k_1mi", "acima_1mi"], n, p=[0.3, 0.5, 0.2]))
    op["faturamento_mensal_faixa"] = np.where(preenchido, faturamento, None)

    # ---- valor fechado
    ganha = (op.status == "ganha").to_numpy()
    plano = np.where(rng.random(n) < 0.08, rng.choice(NOMES_PLANOS, n), op.plano_interesse)
    op["plano_contratado"] = np.where(ganha, plano, None)
    valor = op.plano_contratado.map(MENSALIDADE) * (1 - rng.choice(DESCONTOS, n, p=PESO_DESCONTOS))
    op["valor_mensal_negociado"] = valor.round(2)
    op["valor_contrato_12m"] = (valor * 12).round(2)

    # ---- UTMs
    pago = (op.campanha >= 0).to_numpy()
    r = rng.random(n)
    sem_utm = pago & (r < SEM_UTM)
    com_utm = pago & ~sem_utm
    quebrada = pago & (r >= SEM_UTM) & (r < SEM_UTM + UTM_QUEBRADA)
    camp = CAMPANHAS.reindex(op.campanha.to_numpy())
    op["fonte"] = np.where(sem_utm, "direto", op.canal)
    op["utm_source"] = np.where(com_utm, op.canal.map(UTM_SOURCE), None)
    op["utm_medium"] = np.where(com_utm, camp.utm_medium.to_numpy(), None)
    op["utm_campaign"] = np.where(quebrada, "{{campaign.name}}", np.where(com_utm, camp.nome_campanha.to_numpy(), None))
    op["utm_content"] = np.where(com_utm, np.char.add("criativo_0", rng.integers(1, 7, n).astype(str)), None)
    termo = np.array([rng.choice(TERMOS_BUSCA[c]) if c in TERMOS_BUSCA else None for c in camp.nome_campanha], dtype=object)
    op["utm_term"] = np.where(com_utm, termo, None)

    # ---- só entra no CRM o que não estava encerrado antes da janela
    op = op[(final >= INICIO).to_numpy()].reset_index(drop=True)
    op.insert(0, "id_oportunidade", "OP" + pd.Series(range(1, len(op) + 1)).astype(str).str.zfill(6))
    return op


def gerar_anuncios(op):
    camp = CAMPANHAS.copy()
    camp["campaign_id"] = [f"2{rng.integers(10**9, 10**10)}" if p == "google_ads" else f"1202{rng.integers(10**13, 10**14)}"
                           for p in camp.plataforma]
    dias = pd.date_range(INICIO, FIM.normalize(), freq="D")
    grade = pd.MultiIndex.from_product([dias, camp.index], names=["data", "campanha"]).to_frame(index=False)
    # A plataforma conta todos os seus leads, inclusive os que chegam ao CRM sem UTM ou com UTM quebrada.
    pagos = op[(op.campanha >= 0) & (op.data_criacao >= INICIO)]
    leads = pagos.groupby([pagos.data_criacao.dt.normalize().rename("data"), "campanha"]).size().rename("leads")
    d = grade.merge(leads.reset_index(), on=["data", "campanha"], how="left").fillna({"leads": 0})
    d = d.merge(camp, left_on="campanha", right_index=True)
    k = len(d)
    d["investimento"] = (np.maximum(d.leads, 0.5) * d.cpl * rng.lognormal(0, 0.25, k)).round(2)
    d["cliques"] = np.ceil(d.investimento / (d.cpc * rng.lognormal(0, 0.15, k))).astype(int)
    d["impressoes"] = np.ceil(d.cliques / (d.ctr * rng.lognormal(0, 0.15, k))).astype(int)
    d["leads"] = d.leads.astype(int)
    d = d.sort_values(["data", "campanha"])

    g = d[d.plataforma == "google_ads"]
    google = pd.DataFrame({
        "segments_date": g.data.dt.strftime("%Y-%m-%d"),
        "campaign_id": g.campaign_id,
        "campaign_name": g.nome_campanha,
        "campaign_advertising_channel_type": g.tipo,
        "metrics_impressions": g.impressoes,
        "metrics_clicks": g.cliques,
        "metrics_conversions": g.leads.astype(float),
        "metrics_cost_micros": (g.investimento * 1_000_000).round().astype("int64"),
        "customer_currency_code": "BRL",
    })
    m = d[d.plataforma == "meta_ads"]
    meta = pd.DataFrame({
        "date_start": m.data.dt.strftime("%Y-%m-%d"),
        "date_stop": m.data.dt.strftime("%Y-%m-%d"),
        "campaign_id": m.campaign_id,
        "campaign_name": m.nome_campanha,
        "objective": m.tipo,
        "impressions": m.impressoes,
        "clicks": m.cliques,
        "cpm": (m.investimento / m.impressoes * 1000).map("{:.2f}".format),
        "ctr": (m.cliques / m.impressoes * 100).map("{:.4f}".format),
        "spend": m.investimento.map("{:.2f}".format),
        "leads": m.leads,
        "account_currency": "BRL",
    })
    return google, meta, d


def gerar_cobranca(op):
    antigos = pd.DataFrame({"plano": np.repeat(list(BASE_INICIAL), list(BASE_INICIAL.values()))})
    n_ant = len(antigos)
    antigos["data_inicio"] = INICIO_BASE_ANTIGA + pd.to_timedelta(
        rng.integers(0, (INICIO - INICIO_BASE_ANTIGA).days, n_ant), "D")
    antigos["id_oportunidade"] = None
    antigos["segmento_varejo"] = rng.choice(list(SEGMENTOS), n_ant, p=[v[0] for v in SEGMENTOS.values()])
    antigos["porte_empresa"] = antigos.plano.map(PORTE_DO_PLANO)
    antigos["uf"] = rng.choice(UFS, n_ant, p=PESO_UF)
    antigos["valor_mensal"] = antigos.plano.map(MENSALIDADE)
    antigos["mes_idx"] = 0

    ganhas = op[op.status == "ganha"]
    novos = pd.DataFrame({
        "plano": ganhas.plano_contratado.to_numpy(),
        "data_inicio": ganhas.data_fechamento.dt.normalize().to_numpy(),
        "id_oportunidade": ganhas.id_oportunidade.to_numpy(),
        "segmento_varejo": ganhas.segmento_varejo.to_numpy(),
        "porte_empresa": ganhas.porte_empresa.to_numpy(),
        "uf": ganhas.uf.to_numpy(),
        "valor_mensal": ganhas.valor_mensal_negociado.to_numpy(),
    })
    novos["mes_idx"] = novos.data_inicio.dt.to_period("M").map(lambda p: MESES.get_loc(p))

    ass = pd.concat([antigos.sort_values("data_inicio"), novos.sort_values("data_inicio")], ignore_index=True)
    n = len(ass)
    ass["id_cliente"] = "CL" + pd.Series(range(1, n + 1)).astype(str).str.zfill(5)
    ass["id_assinatura"] = "AS" + pd.Series(range(1, n + 1)).astype(str).str.zfill(5)
    ass["meio_pagamento"] = rng.choice(*MEIOS_PAGAMENTO[:1], n, p=MEIOS_PAGAMENTO[1])

    # ---- cancelamentos: distrato das vendas novas (md) ou churn mensal do plano (Etapa 1)
    novo = ass.id_oportunidade.notna().to_numpy()
    r = rng.random(n)
    arrependimento = novo & (r < ARREPENDIMENTO_7D)
    distrato = novo & (r >= ARREPENDIMENTO_7D) & (r < ARREPENDIMENTO_7D + DISTRATO_8_90D)
    dias_distrato = np.where(arrependimento, rng.integers(0, 8, n), rng.integers(8, 91, n))
    data_distrato = ass.data_inicio + pd.to_timedelta(dias_distrato, "D")
    # base antiga pode cancelar já em março; venda nova só a partir do mês seguinte
    mes_cancel = ass.mes_idx.to_numpy() + rng.geometric(ass.plano.map(CHURN_MENSAL).to_numpy()) - np.where(novo, 0, 1)
    data_churn = pd.Series(pd.NaT, index=ass.index, dtype="datetime64[ns]")
    for i in np.where(mes_cancel < len(MESES))[0]:
        mes = MESES[mes_cancel[i]]
        data_churn.iat[i] = mes.start_time + pd.Timedelta(days=int(rng.integers(0, mes.days_in_month)))
    eh_distrato = arrependimento | distrato
    data_cancel = data_distrato.where(eh_distrato, data_churn)
    data_cancel = data_cancel.where(data_cancel <= FIM)
    cancela = data_cancel.notna().to_numpy()
    ass["data_cancelamento"] = data_cancel
    ass["status"] = np.where(cancela, "cancelada", "ativa")

    motivo = np.where(arrependimento, "arrependimento_7_dias",
                      np.where(distrato, rng.choice(MOTIVOS_DISTRATO, n),
                               rng.choice(MOTIVOS_CANCELAMENTO[0], n, p=MOTIVOS_CANCELAMENTO[1])))
    reembolso = np.where(arrependimento, "total", np.where(distrato & (dias_distrato <= 30), "parcial", "nenhum"))
    valor_reembolso = np.select([reembolso == "total", reembolso == "parcial"],
                                [ass.valor_mensal, (ass.valor_mensal * 0.5).round(2)], 0.0)
    ass["tipo_cancelamento"] = np.where(cancela, np.where(eh_distrato, "distrato", "cancelamento"), None)
    ass["motivo_cancelamento"] = np.where(cancela, motivo, None)
    ass["reembolso"] = np.where(cancela, reembolso, None)
    ass["valor_reembolso"] = np.where(cancela, valor_reembolso, None)

    # ---- uma fatura por mês de vigência, vencendo no dia do aniversário do contrato
    faturas = []
    for a in ass.itertuples():
        dia = min(a.data_inicio.day, 28)
        for j in range(a.mes_idx, len(MESES)):
            venc = MESES[j].start_time + pd.Timedelta(days=dia - 1)
            if j == a.mes_idx and pd.notna(a.id_oportunidade):
                venc = max(venc, a.data_inicio)
            if pd.notna(a.data_cancelamento) and venc >= a.data_cancelamento:
                break
            faturas.append((a.id_assinatura, str(MESES[j]), venc, a.valor_mensal, a.meio_pagamento))
    fat = pd.DataFrame(faturas, columns=["id_assinatura", "competencia", "data_vencimento", "valor", "meio_pagamento"])
    fat.insert(0, "id_fatura", "FT" + pd.Series(range(1, len(fat) + 1)).astype(str).str.zfill(6))
    fat["data_emissao"] = fat.data_vencimento - pd.Timedelta(days=10)

    nf = len(fat)
    atraso = sorteio_por_faixas(nf, FAIXAS_ATRASO)
    data_pag = fat.data_vencimento + pd.to_timedelta(atraso, "D") + pd.to_timedelta(rng.integers(8, 20, nf), "h")
    data_pag = data_pag.where(data_pag <= FIM)
    pagos = data_pag.notna().to_numpy()
    fat["status"] = np.where(pagos, "paga", np.where(fat.data_vencimento < FIM.normalize(), "vencida", "em_aberto"))
    fat["data_pagamento"] = data_pag.dt.floor("min")
    fat["valor_pago"] = fat.valor.where(pagos)

    # uma assinatura por cliente: dados do cliente e do cancelamento ficam na própria assinatura
    assinaturas = ass[["id_assinatura", "id_cliente", "id_oportunidade", "plano", "valor_mensal", "meio_pagamento",
                       "segmento_varejo", "porte_empresa", "uf", "data_inicio", "status", "data_cancelamento",
                       "tipo_cancelamento", "motivo_cancelamento", "reembolso", "valor_reembolso"]].copy()
    assinaturas["data_inicio"] = assinaturas.data_inicio.dt.date
    assinaturas["data_cancelamento"] = assinaturas.data_cancelamento.dt.date
    fat["data_vencimento"] = fat.data_vencimento.dt.date
    fat["data_emissao"] = fat.data_emissao.dt.date
    # no máximo um pagamento por fatura: o pagamento fica na própria fatura
    fat = fat[["id_fatura", "id_assinatura", "competencia", "data_emissao", "data_vencimento", "valor", "status",
               "data_pagamento", "valor_pago", "meio_pagamento"]]
    return assinaturas, fat


def gerar_metas(equipe):
    linhas = []
    for mes in MESES:
        for p in equipe.itertuples():
            if p.funcao == "Closer":
                tipo, valor = "valor_vendido_anual", META_CLOSER[(p.pipeline, p.tier)]
            elif p.funcao == "SDR":
                tipo, valor = "reunioes_realizadas", META_SDR[p.tier]
            elif p.funcao == "Recuperador":
                tipo, valor = "contratos_recuperados", META_RECUPERADOR
            else:
                tipo, valor = "valor_vendido_anual_time", sum(META_CLOSER[(c.pipeline, c.tier)]
                                                              for c in equipe[equipe.funcao == "Closer"].itertuples())
            linhas.append({"mes": str(mes), "id_colaborador": p.id_colaborador, "funcao": p.funcao,
                           "tipo_meta": tipo, "valor_meta": valor})
    return pd.DataFrame(linhas)


def conferir(op, diario, assinaturas, faturas):
    """Imprime os números do caso para comparar com a Etapa 1 e com a md antes de publicar."""
    janela = op[op.data_criacao >= INICIO]
    pct = lambda s: s.value_counts(normalize=True).round(3).to_dict()
    print(f"Oportunidades criadas na janela: {len(janela):,} ({len(janela) / len(MESES):,.0f}/mês); "
          f"herdadas de jan–fev: {len(op) - len(janela):,}")
    sem72 = (janela.horas_contato.isna() | (janela.horas_contato >= 72)).mean()
    print(f"Sem contato em 72h: {sem72:.1%} | em 1h: {(janela.horas_contato < 1).mean():.1%} | "
          f"nunca: {janela.horas_contato.isna().mean():.1%}")

    coorte = janela[janela.data_criacao < pd.Timestamp("2026-06-01")]  # 3 meses com tempo de fechar
    meses_coorte = 3
    funil = {
        "leads": len(coorte), "qualificados": coorte.data_qualificacao.notna().sum(),
        "reunioes": coorte.data_reuniao.notna().sum(), "follow_up": coorte.data_follow_up.notna().sum(),
        "forecast": coorte.data_forecast.notna().sum(), "ganhas": (coorte.status == "ganha").sum(),
    }
    print("Funil por mês (coorte mar–mai):", {k: round(v / meses_coorte) for k, v in funil.items()})
    print(f"Conversão lead → venda: {funil['ganhas'] / funil['leads']:.2%} | "
          f"FUP → venda: {funil['ganhas'] / funil['follow_up']:.1%}")
    ganhas = op[op.status == "ganha"].copy()
    print(f"Ciclo mediano (dias): {(ganhas.data_fechamento - ganhas.data_criacao).dt.days.median():.0f}")
    print("Fonte:", pct(janela.fonte))
    print("Temperatura:", pct(janela.temperatura))
    pago = janela[janela.campanha >= 0]
    print(f"Leads pagos sem UTM: {pago.utm_source.isna().mean():.1%} | "
          f"UTM quebrada: {(pago.utm_campaign == '{{campaign.name}}').mean():.1%}")

    # comissão pela regra das faixas, com a trava de caixa (1ª mensalidade paga em até 30 dias)
    fat = faturas.merge(assinaturas[["id_assinatura", "id_oportunidade"]], on="id_assinatura")
    primeira = fat[fat.id_oportunidade.notna()].sort_values("data_vencimento").groupby("id_assinatura").head(1)
    caixa_ok = primeira.set_index("id_oportunidade").apply(
        lambda f: pd.notna(f.data_pagamento)
        and pd.Timestamp(f.data_pagamento) <= pd.Timestamp(f.data_vencimento) + pd.Timedelta(days=30), axis=1)
    ganhas["caixa_ok"] = ganhas.id_oportunidade.map(caixa_ok).fillna(False).astype(bool)
    ganhas["mes"] = ganhas.data_fechamento.dt.to_period("M")
    ganhas["valor_caixa"] = ganhas.valor_contrato_12m.where(ganhas.caixa_ok, 0.0)
    por_closer = ganhas.groupby(["mes", "id_closer"]).agg(venda=("valor_contrato_12m", "sum"),
                                                          caixa=("valor_caixa", "sum")).reset_index()
    faixa = np.searchsorted(FAIXAS_COMISSAO.venda_anual_min.to_numpy(), por_closer.venda, side="right") - 1
    faixa = np.where((por_closer.caixa / por_closer.venda < 0.75) & (faixa > 0), faixa - 1, faixa)
    por_closer["comissao"] = por_closer.venda * FAIXAS_COMISSAO.percentual_comissao.to_numpy()[faixa]

    por_mes = pd.DataFrame({
        "contratos": ganhas.groupby("mes").size(),
        "investimento": diario.groupby(diario.data.dt.to_period("M")).investimento.sum(),
        "comissao": por_closer.groupby("mes").comissao.sum(),
    })
    por_mes["cac"] = (por_mes.investimento + por_mes.comissao) / por_mes.contratos
    print("\n" + por_mes.round(0).to_string())
    print(f"Comissão média por contrato: R$ {por_closer.comissao.sum() / len(ganhas):,.0f}")
    ativas = assinaturas[assinaturas.status == "ativa"]
    print(f"Assinaturas ativas no fim: {len(ativas)} -> {ativas.plano.value_counts().to_dict()}")
    print(f"Receita anual (ativas x mensalidade x 12): R$ {ativas.valor_mensal.sum() * 12:,.0f}")
    print("Status das faturas:", pct(faturas.status))


def main():
    pasta = Path(sys.argv[1])
    equipe = gerar_equipe()
    op = gerar_oportunidades(equipe)
    _, meta, diario = gerar_anuncios(op)
    assinaturas, faturas = gerar_cobranca(op)
    conferir(op, diario, assinaturas, faturas)

    crm = op[["id_oportunidade", "data_criacao", "pipeline", "plano_interesse", "fase_atual", "data_entrada_fase",
              "status", "fonte", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "origem_lead",
              "passou_por_chat", "reuniao_agendada_bot", "temperatura", "id_sdr", "id_closer", "id_recuperador",
              "data_primeiro_contato", "qtd_tentativas_contato", "data_qualificacao", "data_reuniao",
              "data_follow_up", "data_forecast", "data_fechamento", "fase_perda", "motivo_perda",
              "plano_contratado", "valor_mensal_negociado", "valor_contrato_12m", "segmento_varejo",
              "porte_empresa", "uf", "faturamento_mensal_faixa"]]
    # A cobrança continua sendo simulada, porque a conferência usa assinaturas e faturas para
    # checar os números do caso, mas não é escrita: ficou fora das origens do projeto.
    saidas = {
        "meta_ads/insights_campanhas_diario.csv": meta,
        "crm/oportunidades.csv": crm,
        "crm/equipe_comercial.csv": equipe,
        "planilhas_comerciais/metas_mensais.csv": gerar_metas(equipe),
        "planilhas_comerciais/faixas_comissao.csv": FAIXAS_COMISSAO,
        "planilhas_comerciais/regras_bonus.csv": REGRAS_BONUS,
    }
    print()
    for nome, df in saidas.items():
        arquivo = pasta / nome
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(arquivo, index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
        print(f"{nome:45s} {len(df):>8,} linhas")


if __name__ == "__main__":
    main()
