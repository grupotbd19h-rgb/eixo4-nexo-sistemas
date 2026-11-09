"""
Cria o painel de observabilidade da carga no CloudWatch.

    python criar_painel_cloudwatch.py

Os quatro indicadores que a etapa pede saem de métricas que a AWS já publica
sozinha — não há agente para instalar nem métrica própria para manter:

  volume de dados processado   ProcessedBytes do Athena + tamanho do bucket
  número de erros              ExecutionsFailed do Step Functions
  tempo de processamento       ExecutionTime do Step Functions
  origem x destino             conferido dentro do fluxo, que reprova a carga

O quarto indicador é o único que não vira gráfico, e isso é proposital. Ele é
uma verificação de conteúdo, não um número de infraestrutura: o fluxo roda a
consulta de conferência e desvia para falha quando o destino não bate com a
origem. Ou seja, ele aparece no painel como execução falha — que é o lugar certo
para um problema de qualidade aparecer.

Publicá-lo como métrica própria custaria US$ 0,30 por métrica por mês, mais do
que todo o resto do projeto somado, sem acrescentar informação.
"""
import json

import boto3

NOME = "nexo-observabilidade"
BUCKET = "nexo-eixo4-dados"
MAQUINA = "nexo-carga"
REGIAO = "us-east-1"


def arn_da_maquina(sf):
    for m in sf.list_state_machines()["stateMachines"]:
        if m["name"] == MAQUINA:
            return m["stateMachineArn"]
    raise SystemExit(f"Máquina de estados {MAQUINA} não encontrada; rode criar_fluxo.py antes.")


def widget(x, y, largura, altura, titulo, metricas, periodo, estatistica, extras=None):
    propriedades = {
        "title": titulo,
        "region": REGIAO,
        "metrics": metricas,
        "period": periodo,
        "stat": estatistica,
        "view": "timeSeries",
        "stacked": False,
    }
    propriedades.update(extras or {})
    return {"type": "metric", "x": x, "y": y, "width": largura, "height": altura,
            "properties": propriedades}


def montar(arn):
    texto = (
        "## Observabilidade da carga — Nexo Sistemas\n"
        "Pipeline **S3 → Glue → Athena**, orquestrado pela máquina de estados "
        f"`{MAQUINA}`.\n\n"
        "**Origem × destino:** a conferência roda dentro do fluxo, no estado "
        "`ConferirOrigemDestino`. Ela compara contagem de registros e soma do "
        "investimento entre a camada bruta e o modelo estrela; qualquer "
        "divergência reprova a carga. Por isso ela não tem gráfico próprio: "
        "aparece aqui como execução falha.\n\n"
        "**Periodicidade:** a cada execução para erro e tempo; diária para "
        "volume armazenado, que é a granularidade em que a AWS publica o "
        "tamanho do bucket."
    )

    return {
        "widgets": [
            {"type": "text", "x": 0, "y": 0, "width": 24, "height": 4,
             "properties": {"markdown": texto}},

            widget(0, 4, 12, 6, "Execuções do fluxo — sucesso e falha",
                   [["AWS/States", "ExecutionsSucceeded", "StateMachineArn", arn,
                     {"label": "sucesso", "color": "#2ca02c"}],
                    [".", "ExecutionsFailed", ".", ".",
                     {"label": "falha", "color": "#d62728"}],
                    [".", "ExecutionsAborted", ".", ".", {"label": "abortada"}]],
                   300, "Sum", {"yAxis": {"left": {"min": 0}}}),

            widget(12, 4, 12, 6, "Tempo de processamento do fluxo",
                   [["AWS/States", "ExecutionTime", "StateMachineArn", arn,
                     {"label": "duração (ms)"}]],
                   300, "Average", {"yAxis": {"left": {"min": 0}}}),

            widget(0, 10, 12, 6, "Volume lido pelo Athena",
                   [["AWS/Athena", "ProcessedBytes", "WorkGroup", "primary",
                     "QueryState", "SUCCEEDED", "QueryType", "DML",
                     {"label": "bytes varridos"}]],
                   300, "Sum", {"yAxis": {"left": {"min": 0}}}),

            widget(12, 10, 12, 6, "Armazenamento no S3",
                   [["AWS/S3", "BucketSizeBytes", "BucketName", BUCKET,
                     "StorageType", "StandardStorage", {"label": "bytes"}],
                    [".", "NumberOfObjects", ".", ".", "StorageType", "AllStorageTypes",
                     {"label": "objetos", "yAxis": "right"}]],
                   86400, "Average", {}),

            {"type": "log", "x": 0, "y": 16, "width": 24, "height": 6,
             "properties": {
                 "title": "Últimas mensagens do job do Glue",
                 "region": REGIAO,
                 "query": ("SOURCE '/aws-glue/python-jobs/output'\n"
                           "| fields @timestamp, @message\n"
                           "| sort @timestamp desc\n"
                           "| limit 40"),
                 "view": "table",
             }},
        ]
    }


def main():
    arn = arn_da_maquina(boto3.client("stepfunctions"))
    cw = boto3.client("cloudwatch")
    cw.put_dashboard(DashboardName=NOME, DashboardBody=json.dumps(montar(arn)))
    print(f"Painel {NOME} publicado.")
    print(f"https://{REGIAO}.console.aws.amazon.com/cloudwatch/home"
          f"?region={REGIAO}#dashboards/dashboard/{NOME}")


if __name__ == "__main__":
    raise SystemExit(main())
