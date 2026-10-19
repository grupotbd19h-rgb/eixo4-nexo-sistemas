"""
Cria (ou atualiza) o job do Glue que constrói o modelo estrela.

    python criar_job_glue.py                 # cria ou atualiza o job
    python criar_job_glue.py --executar      # cria/atualiza e executa uma vez

A configuração do ambiente fica aqui, em código, e não em formulário do console:
é o que permite recriar o job do zero depois que a sessão do laboratório expira.

Cada parâmetro abaixo tem motivo, e nenhum é o padrão do console:

  pythonshell, não Spark     a base inteira tem menos de 6 MB
  MaxCapacity 0.0625         a menor unidade do Python Shell (1/16 de DPU)
  library-set analytics      é o que entrega pandas e pyarrow no Python Shell
  Timeout 15 min             teto de gasto: o job roda em ~2 min
  MaxRetries 0               falha tem que aparecer, não ser repetida sozinha
"""
import argparse
import time

import boto3

BUCKET = "nexo-eixo4-dados"
NOME = "nexo-estrela"
ROLE = "LabRole"                 # role pré-existente do AWS Academy Learner Lab

CONFIGURACAO = {
    "Role": ROLE,
    "Command": {
        "Name": "pythonshell",
        "ScriptLocation": f"s3://{BUCKET}/scripts/job_estrela.py",
        "PythonVersion": "3.9",
    },
    "DefaultArguments": {
        "--origem": f"s3://{BUCKET}/raw",
        "--destino": f"s3://{BUCKET}/dw",
        "--library-set": "analytics",
    },
    "MaxCapacity": 0.0625,
    "MaxRetries": 0,
    "Timeout": 15,
    "GlueVersion": "3.0",
    "Description": "Nexo Sistemas - camada bruta para modelo estrela (Etapa 3)",
}


def acompanhar(glue, execucao):
    """Espera o fim da execução e devolve o estado final."""
    while True:
        info = glue.get_job_run(JobName=NOME, RunId=execucao)["JobRun"]
        estado = info["JobRunState"]
        if estado not in ("STARTING", "RUNNING", "STOPPING"):
            return info
        time.sleep(10)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--executar", action="store_true", help="executa o job depois de criar")
    args = ap.parse_args()

    glue = boto3.client("glue")
    existentes = [j["Name"] for j in glue.get_jobs()["Jobs"]]
    if NOME in existentes:
        glue.update_job(JobName=NOME, JobUpdate=CONFIGURACAO)
        print(f"Job {NOME} atualizado.")
    else:
        glue.create_job(Name=NOME, **CONFIGURACAO)
        print(f"Job {NOME} criado.")

    if not args.executar:
        return 0

    execucao = glue.start_job_run(JobName=NOME)["JobRunId"]
    print(f"Execução {execucao} iniciada; aguardando...")
    info = acompanhar(glue, execucao)
    segundos = info.get("ExecutionTime", 0)
    print(f"Estado: {info['JobRunState']}  ({segundos}s)")
    if info.get("ErrorMessage"):
        print(f"Erro: {info['ErrorMessage']}")
        print(f"Log: grupo /aws-glue/python-jobs/output, fluxo {execucao}")
        return 1

    # Python Shell: US$ 0,44 por DPU-hora, cobrança por segundo.
    print(f"Custo da execução: US$ {0.0625 * 0.44 * segundos / 3600:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
