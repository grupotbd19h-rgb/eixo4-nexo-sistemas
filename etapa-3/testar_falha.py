"""
Injeta uma falha controlada no fluxo, para provar que o desvio de erro funciona.

    python testar_falha.py

Monitoramento que nunca registrou um erro não provou nada. Este teste troca o
nome do job do Glue por um que não existe, executa o fluxo uma vez, confirma que
ele parou no estado de falha previsto — e devolve a definição original.

A restauração acontece em `finally`: se o teste for interrompido no meio, a
máquina de estados volta ao que era antes de qualquer jeito.

Nenhum recurso é criado e o job do Glue não chega a rodar, porque o erro
acontece ao resolvê-lo. O custo é o de duas transições de estado.
"""
import json
import time
from pathlib import Path

import boto3

NOME = "nexo-carga"
DEFINICAO = Path(__file__).parent / "stepfunctions" / "fluxo.asl.json"
JOB_INEXISTENTE = "nexo-estrela-que-nao-existe"


def arn_da_maquina(sf):
    for m in sf.list_state_machines()["stateMachines"]:
        if m["name"] == NOME:
            return m["stateMachineArn"]
    raise SystemExit(f"Máquina de estados {NOME} não encontrada.")


def acompanhar(sf, execucao):
    while True:
        info = sf.describe_execution(executionArn=execucao)
        if info["status"] != "RUNNING":
            return info
        time.sleep(5)


def main():
    sf = boto3.client("stepfunctions")
    arn = arn_da_maquina(sf)
    original = DEFINICAO.read_text(encoding="utf-8")

    quebrada = json.loads(original)
    quebrada["States"]["ConstruirEstrela"]["Parameters"]["JobName"] = JOB_INEXISTENTE
    # Sem repetição: o job não existe, repetir três vezes só faria esperar.
    quebrada["States"]["ConstruirEstrela"].pop("Retry", None)

    try:
        sf.update_state_machine(stateMachineArn=arn, definition=json.dumps(quebrada))
        time.sleep(5)
        print(f"Definição trocada: o fluxo vai procurar o job {JOB_INEXISTENTE}.")

        execucao = sf.start_execution(stateMachineArn=arn)["executionArn"]
        info = acompanhar(sf, execucao)
        print(f"Execução terminou em {info['status']}.")

        eventos = sf.get_execution_history(executionArn=execucao, maxResults=1000)["events"]
        estados = [e["stateExitedEventDetails"]["name"]
                   for e in eventos if e["type"] == "TaskStateExited"]
        falhas = [e for e in eventos if e["type"] == "ExecutionFailed"]
        print(f"Estados concluídos antes da falha: {', '.join(estados) or 'nenhum'}")
        if falhas:
            detalhe = falhas[0]["executionFailedEventDetails"]
            print(f"Erro registrado: {detalhe.get('error')}")
            print(f"Causa: {detalhe.get('cause', '')[:160]}")

        esperado = info["status"] == "FAILED"
        print("\nResultado:", "o desvio de erro funcionou." if esperado
              else "ATENÇÃO — o fluxo não falhou como deveria.")
    finally:
        sf.update_state_machine(stateMachineArn=arn, definition=original)
        print(f"Definição original restaurada em {NOME}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
