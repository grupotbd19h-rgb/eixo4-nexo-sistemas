"""
Executa um arquivo .sql no Athena, comando por comando.

    python rodar_athena.py sql/01_raw.sql
    python rodar_athena.py sql/03_perguntas.sql --limite 10

Existe para que o DDL rode a partir do arquivo versionado, e não de um copiar e
colar no console: o que está no repositório é exatamente o que foi executado.

Os resultados do Athena vão para uma pasta no mesmo bucket — o serviço exige um
destino, mesmo para comando que não devolve linha.

Credenciais: as do laboratório, em ~/.aws/credentials, renovadas a cada sessão.
"""
import argparse
import re
import time

import boto3

SAIDA_PADRAO = "s3://nexo-eixo4-dados/athena-results/"


def comandos(texto):
    """Separa o arquivo em comandos, descartando as linhas de comentário."""
    limpo = "\n".join(l for l in texto.splitlines() if not l.strip().startswith("--"))
    for bruto in limpo.split(";"):
        if bruto.strip():
            yield bruto.strip()


def rotulo(sql):
    """Primeira linha útil do comando, para acompanhar a execução."""
    return re.sub(r"\s+", " ", sql)[:70]


def executar(athena, sql, saida, limite):
    inicio = athena.start_query_execution(
        QueryString=sql,
        ResultConfiguration={"OutputLocation": saida},
    )["QueryExecutionId"]

    while True:
        info = athena.get_query_execution(QueryExecutionId=inicio)["QueryExecution"]
        estado = info["Status"]["State"]
        if estado in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(1)

    varrido = info.get("Statistics", {}).get("DataScannedInBytes", 0)
    if estado != "SUCCEEDED":
        print(f"  FALHOU: {info['Status'].get('StateChangeReason', '')}")
        return False, varrido

    pagina = athena.get_paginator("get_query_results")
    linhas = []
    for resposta in pagina.paginate(QueryExecutionId=inicio, PaginationConfig={"MaxItems": limite + 1}):
        for linha in resposta["ResultSet"]["Rows"]:
            linhas.append([c.get("VarCharValue", "") for c in linha["Data"]])

    if len(linhas) > 1:                      # a primeira linha é o cabeçalho
        larguras = [max(len(l[i]) for l in linhas) for i in range(len(linhas[0]))]
        for n, linha in enumerate(linhas[: limite + 1]):
            print("   " + "  ".join(v.ljust(w) for v, w in zip(linha, larguras)))
            if n == 0:
                print("   " + "  ".join("-" * w for w in larguras))
    return True, varrido


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arquivo")
    ap.add_argument("--saida", default=SAIDA_PADRAO)
    ap.add_argument("--limite", type=int, default=25, help="linhas exibidas por consulta")
    args = ap.parse_args()

    with open(args.arquivo, encoding="utf-8") as f:
        lista = list(comandos(f.read()))

    athena = boto3.client("athena")
    total = 0
    for n, sql in enumerate(lista, 1):
        print(f"[{n}/{len(lista)}] {rotulo(sql)}")
        ok, varrido = executar(athena, sql, args.saida, args.limite)
        total += varrido
        if not ok:
            print("\nParei no primeiro erro: o resto do arquivo depende do que falhou.")
            return 1

    # O Athena cobra por byte varrido, com mínimo de 10 MB por comando.
    cobrado = max(total, 10 * 1024 * 1024 * len(lista))
    print(f"\n{len(lista)} comandos. Varridos {total / 1024 / 1024:.1f} MB; "
          f"cobrança mínima equivalente a {cobrado / 1024 / 1024:.0f} MB "
          f"(US$ {cobrado / 1024**4 * 5:.4f}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
