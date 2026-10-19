"""
Reorganiza os CSVs da Etapa 2 no layout de pastas que o S3 vai receber.

Cada arquivo de evento vira uma pasta por dia (dt=AAAA-MM-DD), no padrão de
partição que o Athena entende sem precisar de crawler. Os cadastros e as tabelas
de referência, que não têm data, ficam sem partição.

Nada é enviado para a nuvem: este programa só escreve no disco, para conferir o
resultado antes de pagar por qualquer coisa.

    python particionar.py ../etapa-2/dados dados_particionados

Layout produzido:

    <saida>/crm_oportunidades/dt=2026-03-01/crm_oportunidades.csv
    <saida>/meta_insights_diario/dt=2026-03-01/meta_insights_diario.csv
    <saida>/planilhas_metas_mensais/dt=2026-03-01/planilhas_metas_mensais.csv
    <saida>/crm_equipe_comercial/crm_equipe_comercial.csv
    ...
"""
import shutil
import sys
from pathlib import Path

import pandas as pd

# (caminho na origem, nome da tabela no destino, coluna de data, granularidade)
ORIGENS = [
    ("crm/oportunidades.csv", "crm_oportunidades", "data_criacao", "dia"),
    ("meta_ads/insights_campanhas_diario.csv", "meta_insights_diario", "date_start", "dia"),
    ("planilhas_comerciais/metas_mensais.csv", "planilhas_metas_mensais", "mes", "mes"),
    ("crm/equipe_comercial.csv", "crm_equipe_comercial", None, None),
    ("planilhas_comerciais/faixas_comissao.csv", "planilhas_faixas_comissao", None, None),
    ("planilhas_comerciais/regras_bonus.csv", "planilhas_regras_bonus", None, None),
]


def chave_particao(serie, granularidade):
    """Devolve a data da partição como texto AAAA-MM-DD."""
    datas = pd.to_datetime(serie)
    if granularidade == "mes":
        datas = datas.values.astype("datetime64[M]")  # joga tudo para o dia 1º
    return pd.Series(datas).dt.strftime("%Y-%m-%d")


def particionar(origem, destino):
    total_arquivos = 0
    for caminho, tabela, coluna, granularidade in ORIGENS:
        df = pd.read_csv(origem / caminho, dtype=str, keep_default_na=False)
        pasta = destino / tabela

        if coluna is None:
            pasta.mkdir(parents=True, exist_ok=True)
            df.to_csv(pasta / f"{tabela}.csv", index=False, encoding="utf-8")
            print(f"{tabela:28s} sem partição    {len(df):>7,} linhas")
            total_arquivos += 1
            continue

        df = df.assign(_dt=chave_particao(df[coluna], granularidade))
        for dt, bloco in df.groupby("_dt", sort=True):
            alvo = pasta / f"dt={dt}"
            alvo.mkdir(parents=True, exist_ok=True)
            bloco.drop(columns="_dt").to_csv(alvo / f"{tabela}.csv", index=False, encoding="utf-8")
            total_arquivos += 1
        print(f"{tabela:28s} {df._dt.nunique():>4} partições  {len(df):>7,} linhas")
    return total_arquivos


def main():
    origem = Path(sys.argv[1])
    destino = Path(sys.argv[2])
    if destino.exists():
        shutil.rmtree(destino)  # refaz do zero, para não deixar partição velha para trás
    destino.mkdir(parents=True)

    total = particionar(origem, destino)
    tamanho = sum(f.stat().st_size for f in destino.rglob("*.csv"))
    print(f"\n{total:,} arquivos, {tamanho / 1024 / 1024:.1f} MB em {destino}")


if __name__ == "__main__":
    main()
