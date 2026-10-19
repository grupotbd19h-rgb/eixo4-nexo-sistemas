"""
Envia a camada bruta particionada para o S3.

    python subir_s3.py dados_particionados --bucket nexo-eixo4-dados --simular
    python subir_s3.py dados_particionados --bucket nexo-eixo4-dados

O padrão é simular: sem --confirmar nada sai da máquina. É proposital, porque o
orçamento do laboratório é fechado e não se recupera.

O envio é idempotente: arquivo que já está no destino com o mesmo tamanho é
pulado. Rodar de novo depois de regerar as bases só envia o que mudou.

Credenciais: o laboratório as renova a cada sessão. Pegue-as em AWS Details, na
tela do lab, e grave em ~/.aws/credentials antes de rodar. Elas expiram quando a
sessão termina — se der erro de token expirado, é isso.
"""
import argparse
from pathlib import Path


def arquivos(raiz):
    """Devolve (caminho local, chave no S3) para cada CSV, preservando a partição."""
    for caminho in sorted(raiz.rglob("*.csv")):
        yield caminho, f"raw/{caminho.relative_to(raiz).as_posix()}"


def garantir_bucket(s3, bucket):
    """Cria o bucket se ainda não existir. Em us-east-1 não se passa região:
    a API recusa LocationConstraint para a região padrão."""
    from botocore.exceptions import ClientError
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"Bucket {bucket} já existe.")
    except ClientError:
        s3.create_bucket(Bucket=bucket)
        print(f"Bucket {bucket} criado.")


def tamanhos_no_destino(s3, bucket, prefixo):
    """Lê o que já está lá, para não pagar por enviar duas vezes a mesma coisa."""
    atual = {}
    pagina = s3.get_paginator("list_objects_v2")
    for resposta in pagina.paginate(Bucket=bucket, Prefix=prefixo):
        for obj in resposta.get("Contents", []):
            atual[obj["Key"]] = obj["Size"]
    return atual


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("origem", help="pasta produzida por particionar.py")
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--confirmar", action="store_true", help="envia de verdade")
    args = ap.parse_args()

    raiz = Path(args.origem)
    lista = list(arquivos(raiz))
    total = sum(c.stat().st_size for c, _ in lista)

    if not args.confirmar:
        for _, chave in lista[:3]:
            print(f"  s3://{args.bucket}/{chave}")
        print(f"  ... ({len(lista)} arquivos)")
        print(f"\nSimulação: {len(lista)} arquivos, {total / 1024 / 1024:.1f} MB.")
        print("Nada foi enviado. Repita com --confirmar para enviar.")
        return

    import boto3

    s3 = boto3.client("s3")
    garantir_bucket(s3, args.bucket)
    ja_estao = tamanhos_no_destino(s3, args.bucket, "raw/")
    enviados = pulados = 0
    for caminho, chave in lista:
        if ja_estao.get(chave) == caminho.stat().st_size:
            pulados += 1
            continue
        s3.upload_file(str(caminho), args.bucket, chave)
        enviados += 1

    print(f"{enviados:,} enviados, {pulados:,} já estavam lá, de {len(lista):,} arquivos.")


if __name__ == "__main__":
    main()
