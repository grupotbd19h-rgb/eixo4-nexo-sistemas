"""
Cria (ou atualiza) a máquina de estados que orquestra a carga.

    python criar_fluxo.py                # cria ou atualiza
    python criar_fluxo.py --executar     # cria/atualiza e executa uma vez

Por que Step Functions e não Glue Workflow: o Glue Workflow só orquestra
recursos do próprio Glue, e este fluxo precisa chamar o Athena duas vezes — uma
para conferir que a camada bruta chegou, outra para conferir que o modelo
estrela ficou de pé. O Step Functions chama os dois serviços nativamente, tem
repetição e desvio de erro por passo, e desenha o fluxo sozinho.

Tipo STANDARD, não EXPRESS: só o STANDARD suporta a espera síncrona (.sync) pelo
fim do job do Glue. Custo: US$ 0,025 por mil transições, com as primeiras quatro
mil de cada mês gratuitas — o fluxo tem oito.
"""
import argparse
import json
import time
from pathlib import Path

import boto3

NOME = "nexo-carga"
ROLE = "arn:aws:iam::705603283691:role/LabRole"
DEFINICAO = Path(__file__).parent / "stepfunctions" / "fluxo.asl.json"


def arn_existente(sf):
    for m in sf.list_state_machines()["stateMachines"]:
        if m["name"] == NOME:
            return m["stateMachineArn"]
    return None


def acompanhar(sf, execucao):
    while True:
        info = sf.describe_execution(executionArn=execucao)
        if info["status"] != "RUNNING":
            return info
        time.sleep(10)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--executar", action="store_true")
    args = ap.parse_args()

    definicao = DEFINICAO.read_text(encoding="utf-8")
    json.loads(definicao)                      # erro de sintaxe aparece aqui, não na AWS

    sf = boto3.client("stepfunctions")
    arn = arn_existente(sf)
    if arn:
        sf.update_state_machine(stateMachineArn=arn, definition=definicao, roleArn=ROLE)
        print(f"Máquina de estados {NOME} atualizada.")
        time.sleep(5)                          # a atualização leva alguns segundos para valer
    else:
        arn = sf.create_state_machine(
            name=NOME, definition=definicao, roleArn=ROLE, type="STANDARD"
        )["stateMachineArn"]
        print(f"Máquina de estados {NOME} criada.")

    if not args.executar:
        return 0

    execucao = sf.start_execution(stateMachineArn=arn)["executionArn"]
    print("Executando; o job do Glue leva cerca de um minuto...")
    info = acompanhar(sf, execucao)
    print(f"Estado: {info['status']}")

    historico = sf.get_execution_history(executionArn=execucao, maxResults=1000)["events"]
    for evento in historico:
        if evento["type"] == "TaskStateExited":
            print(f"  concluído: {evento['stateExitedEventDetails']['name']}")
        elif evento["type"] in ("ExecutionSucceeded", "ExecutionFailed"):
            print(f"  {evento['type']}: {evento.get('executionFailedEventDetails', {}).get('cause', '')}")
    return 0 if info["status"] == "SUCCEEDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
