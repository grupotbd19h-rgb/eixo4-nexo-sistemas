"""
Constrói o modelo estrela a partir da camada bruta.

O mesmo arquivo roda nos dois lugares, sem alteração:

    local   python job_estrela.py --origem ../dados_particionados --destino ../saida_estrela
    Glue    job do tipo Python Shell, com --origem s3://BUCKET/raw --destino s3://BUCKET/dw

Quando o caminho começa com s3://, as partições são baixadas para uma pasta
temporária, transformadas em disco e os Parquet resultantes são enviados de
volta. A transformação em si não sabe onde está: é pandas puro, o que permite
depurar tudo localmente antes de gastar um centavo de orçamento.

O tipo Python Shell foi escolhido no lugar do Spark porque a base inteira tem
menos de 6 MB; um cluster Spark para esse volume custaria mais do que o projeto.
"""
import argparse
import shutil
import tempfile
from pathlib import Path

import pandas as pd

# Tabela de referência: não vem de nenhuma origem, são os planos do Quadro 1 do documento.
PLANOS = pd.DataFrame({
    "plano": ["Essencial", "Profissional", "Corporativo"],
    "mensalidade": [190.0, 390.0, 990.0],
    "perfil_cliente": ["Microempresas e autônomos", "Pequenas empresas", "Médias empresas e redes de lojas"],
})

UTM_QUEBRADA = "{{campaign.name}}"  # marcador que a plataforma deixou de substituir
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


# --------------------------------------------------------------- entrada e saída
def eh_s3(caminho):
    return str(caminho).startswith("s3://")


def partes_s3(caminho):
    resto = str(caminho)[len("s3://"):]
    bucket, _, prefixo = resto.partition("/")
    return bucket, prefixo.strip("/")


def baixar(origem, pasta):
    """Traz o prefixo do S3 para o disco, preservando o caminho relativo."""
    import boto3

    bucket, prefixo = partes_s3(origem)
    s3 = boto3.client("s3")
    pagina = s3.get_paginator("list_objects_v2")
    for resposta in pagina.paginate(Bucket=bucket, Prefix=prefixo):
        for obj in resposta.get("Contents", []):
            destino = pasta / Path(obj["Key"]).relative_to(prefixo)
            destino.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, obj["Key"], str(destino))
    return pasta


def enviar(pasta, destino):
    import boto3

    bucket, prefixo = partes_s3(destino)
    s3 = boto3.client("s3")
    for arquivo in pasta.rglob("*.parquet"):
        chave = f"{prefixo}/{arquivo.relative_to(pasta).as_posix()}"
        s3.upload_file(str(arquivo), bucket, chave)


def ler(raiz, tabela):
    """Lê uma tabela da camada bruta, juntando todas as partições. Tudo como texto."""
    pasta = raiz / tabela
    arquivos = sorted(pasta.rglob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"nenhum CSV em {pasta}")
    blocos = [pd.read_csv(a, dtype=str, keep_default_na=False) for a in arquivos]
    return pd.concat(blocos, ignore_index=True)


def gravar(df, pasta, nome):
    """Uma pasta por tabela: é assim que o Athena espera encontrar os Parquet."""
    alvo = pasta / nome
    alvo.mkdir(parents=True, exist_ok=True)
    df.to_parquet(alvo / f"{nome}.parquet", index=False)
    print(f"{nome:28s} {len(df):>7,} linhas  {len(df.columns):>3} colunas")


# --------------------------------------------------------------------- dimensões
def montar_dim_campanha(meta):
    campanhas = (meta[["campaign_id", "campaign_name", "objective"]]
                 .drop_duplicates()
                 .rename(columns={"campaign_id": "id_campanha",
                                  "campaign_name": "nome_campanha",
                                  "objective": "objetivo"}))
    campanhas["plataforma"] = "Meta Ads"
    # Membros para o que não se resolve: sem a UTM não dá para atribuir custo, e é
    # justamente isso que o problema de negócio quer medir — então vira linha, não nulo.
    faltantes = pd.DataFrame([
        {"id_campanha": "SEM_UTM", "nome_campanha": "(sem UTM)",
         "objetivo": "(desconhecido)", "plataforma": "(não identificada)"},
        {"id_campanha": "UTM_QUEBRADA", "nome_campanha": "(UTM não substituída)",
         "objetivo": "(desconhecido)", "plataforma": "Meta Ads"},
    ])
    return pd.concat([campanhas, faltantes], ignore_index=True)


def montar_dim_data(inicio, fim):
    dias = pd.date_range(inicio, fim, freq="D")
    return pd.DataFrame({
        "data": dias.date,
        "ano": dias.year,
        "mes": dias.month,
        "dia": dias.day,
        "trimestre": dias.quarter,
        "nome_mes": [MESES[m - 1] for m in dias.month],
        "dia_semana": [DIAS[d] for d in dias.dayofweek],
        "fim_de_semana": dias.dayofweek >= 5,
    })


def montar_dim_colaborador(equipe):
    return equipe.rename(columns={"funcao": "funcao", "pipeline": "time"}).assign(
        tier=lambda d: pd.to_numeric(d.tier, errors="coerce"),
        data_admissao=lambda d: pd.to_datetime(d.data_admissao).dt.date,
    )


# ------------------------------------------------------------------------- fatos
def montar_fato_oportunidade(op, dim_campanha):
    f = pd.DataFrame()
    f["id_oportunidade"] = op.id_oportunidade

    datas = {c: pd.to_datetime(op[c], errors="coerce") for c in
             ("data_criacao", "data_primeiro_contato", "data_fechamento")}
    f["data_criacao"] = datas["data_criacao"].dt.date
    f["data_fechamento"] = datas["data_fechamento"].dt.date

    # A medida central do problema: quanto tempo o interessado esperou pelo primeiro contato.
    f["horas_ate_primeiro_contato"] = (
        (datas["data_primeiro_contato"] - datas["data_criacao"]).dt.total_seconds() / 3600
    ).round(2)
    f["sem_contato_72h"] = f.horas_ate_primeiro_contato.isna() | (f.horas_ate_primeiro_contato >= 72)

    # Resolução da campanha: é aqui que a UTM suja vira chave utilizável.
    utm = op.utm_campaign.replace({"": None, UTM_QUEBRADA: None})
    quebrada = op.utm_campaign == UTM_QUEBRADA
    nomes = dim_campanha.set_index("nome_campanha").id_campanha
    f["id_campanha"] = utm.map(nomes).fillna(pd.Series("SEM_UTM", index=op.index).mask(quebrada, "UTM_QUEBRADA"))

    f["fonte"] = op.fonte
    f["origem_lead"] = op.origem_lead
    f["plano_interesse"] = op.plano_interesse
    f["plano_contratado"] = op.plano_contratado.replace({"": None})
    f["id_sdr"] = op.id_sdr.replace({"": None})
    f["id_closer"] = op.id_closer.replace({"": None})
    f["segmento_varejo"] = op.segmento_varejo
    f["porte_empresa"] = op.porte_empresa
    f["uf"] = op.uf

    f["temperatura"] = pd.to_numeric(op.temperatura, errors="coerce")
    f["qtd_tentativas_contato"] = pd.to_numeric(op.qtd_tentativas_contato, errors="coerce").fillna(0).astype(int)
    f["valor_mensal_negociado"] = pd.to_numeric(op.valor_mensal_negociado, errors="coerce")
    f["valor_contrato_12m"] = pd.to_numeric(op.valor_contrato_12m, errors="coerce")

    f["status"] = op.status
    f["ganha"] = op.status == "ganha"
    f["motivo_perda"] = op.motivo_perda.replace({"": None})
    return f


def montar_fato_investimento(meta):
    f = pd.DataFrame()
    f["data"] = pd.to_datetime(meta.date_start).dt.date
    f["id_campanha"] = meta.campaign_id
    f["impressoes"] = pd.to_numeric(meta.impressions, errors="coerce").astype("Int64")
    f["cliques"] = pd.to_numeric(meta.clicks, errors="coerce").astype("Int64")
    f["leads"] = pd.to_numeric(meta.leads, errors="coerce").astype("Int64")
    # A Meta devolve o valor gasto como texto; é a padronização que o capítulo 7 promete.
    f["investimento"] = pd.to_numeric(meta.spend, errors="coerce")
    f["moeda"] = meta.account_currency
    return f


def montar_fato_meta(metas):
    f = pd.DataFrame()
    f["data"] = pd.to_datetime(metas.mes + "-01").dt.date
    f["id_colaborador"] = metas.id_colaborador
    f["funcao"] = metas.funcao
    f["tipo_meta"] = metas.tipo_meta
    f["valor_meta"] = pd.to_numeric(metas.valor_meta, errors="coerce")
    return f


# -------------------------------------------------------------------------- main
def transformar(raiz, saida):
    op = ler(raiz, "crm_oportunidades")
    meta = ler(raiz, "meta_insights_diario")
    equipe = ler(raiz, "crm_equipe_comercial")
    metas = ler(raiz, "planilhas_metas_mensais")

    dim_campanha = montar_dim_campanha(meta)
    fato_oportunidade = montar_fato_oportunidade(op, dim_campanha)
    fato_investimento = montar_fato_investimento(meta)
    fato_meta = montar_fato_meta(metas)

    inicio = min(fato_oportunidade.data_criacao.min(), fato_investimento.data.min())
    fim = max(fato_oportunidade.data_criacao.max(), fato_investimento.data.max())

    gravar(montar_dim_data(inicio, fim), saida, "dim_data")
    gravar(dim_campanha, saida, "dim_campanha")
    gravar(PLANOS.rename(columns={"plano": "id_plano"}), saida, "dim_plano")
    gravar(montar_dim_colaborador(equipe), saida, "dim_colaborador")
    gravar(fato_oportunidade, saida, "fato_oportunidade")
    gravar(fato_investimento, saida, "fato_investimento_anuncio")
    gravar(fato_meta, saida, "fato_meta_vendedor")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--origem", required=True, help="pasta local ou s3://bucket/prefixo da camada bruta")
    ap.add_argument("--destino", required=True, help="pasta local ou s3://bucket/prefixo do armazém")
    args, _ = ap.parse_known_args()  # o Glue acrescenta argumentos próprios

    temporaria = Path(tempfile.mkdtemp(prefix="nexo_"))
    try:
        raiz = baixar(args.origem, temporaria / "raw") if eh_s3(args.origem) else Path(args.origem)
        saida = temporaria / "dw" if eh_s3(args.destino) else Path(args.destino)
        transformar(raiz, saida)
        if eh_s3(args.destino):
            enviar(saida, args.destino)
            print(f"\nenviado para {args.destino}")
        else:
            print(f"\ngravado em {saida}")
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)


if __name__ == "__main__":
    main()
