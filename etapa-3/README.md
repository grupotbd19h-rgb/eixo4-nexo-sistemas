# Etapa 3 — a plataforma de dados da Nexo Sistemas

Esta pasta contém a implementação do pipeline: do CSV cru até as consultas que
respondem às duas perguntas de negócio do capítulo 3 do documento. Tudo roda na
conta do AWS Academy Learner Lab, sem nenhum recurso que cobre por hora.

## O desenho em uma frase

Os arquivos das três origens são organizados por data, enviados para o **S3**,
declarados como tabelas no **Athena**, transformados em modelo estrela por um job
do **AWS Glue**, e a ordem dos passos é controlada pelo **Step Functions**.

```
CSV das origens              S3 raw/            Glue              S3 dw/           Athena
(CRM, Meta Ads,   ──────▶   camada      ──────▶ job        ──────▶ modelo   ──────▶ consultas
 planilhas)                 bruta               nexo-estrela       estrela
                                 ▲                   ▲                 ▲
                                 └───────────────────┴─────────────────┘
                                      Step Functions: nexo-carga
```

## O caminho do dado, passo a passo

| # | O que acontece | Onde está no repositório |
|---|---|---|
| 1 | Os 6 CSVs são reorganizados em pastas `dt=AAAA-MM-DD` | `particionar.py` |
| 2 | As 418 pastas sobem para `s3://nexo-eixo4-dados/raw/` | `subir_s3.py` |
| 3 | Seis tabelas externas são declaradas sobre esses arquivos | `sql/01_raw.sql` |
| 4 | Um job do Glue lê a camada bruta e grava 7 Parquet | `glue/job_estrela.py` |
| 5 | Sete tabelas são declaradas sobre os Parquet | `sql/02_estrela.sql` |
| 6 | As consultas respondem às perguntas de negócio | `sql/03_perguntas.sql` |

Os passos 2 a 5 têm, cada um, um script que os executa a partir do arquivo
versionado — `subir_s3.py`, `rodar_athena.py`, `criar_job_glue.py`,
`criar_fluxo.py`. Nada foi configurado em formulário do console: o que está aqui
é exatamente o que rodou na AWS, e pode ser recriado do zero quando a sessão do
laboratório expirar.

## As decisões, e o motivo de cada uma

**Por que o dado é particionado por data.** Porque o Athena cobra por byte lido:
com as pastas `dt=`, uma consulta filtrada por período não abre os arquivos dos
outros dias. E porque é assim que o dado chegaria de verdade — cada extração
diária grava uma pasta nova sem reescrever o passado, o que torna a carga
incremental e permite reprocessar um único dia trocando uma pasta.
Com 5,7 MB isso ainda não economiza dinheiro, já que o Athena tem cobrança
mínima de 10 MB por consulta; o ganho é o desenho estar correto para o volume
que a empresa teria em produção.

**Por que `partition projection` em vez de crawler.** O crawler do Glue cobra por
execução e precisaria rodar a cada carga para descobrir partições novas. A
*partition projection* declara a faixa de datas no próprio DDL, e o Athena
calcula os caminhos sozinho — sem custo e sem `MSCK REPAIR TABLE`.

**Por que o job é Python Shell e não Spark.** A base inteira tem 5,7 MB. Um
cluster Spark custaria mais do que o restante do projeto somado. O job usa
pandas e roda com 1/16 de DPU, a menor unidade cobrada.

**Por que Parquet na camada analítica.** Os mesmos dados ocupam 5,7 MB em CSV e
353 KB em Parquet — 16 vezes menos. Como o Athena cobra pelo que lê, o formato
colunar é o que torna a consulta barata.

**Por que Step Functions e não Glue Workflow.** O Glue Workflow só orquestra
recursos do próprio Glue. Este fluxo precisa chamar o Athena duas vezes, para
validar a entrada e a saída, então precisa de um orquestrador que converse com
os dois serviços.

**Por que a camada bruta é toda `string`.** Porque ela guarda o dado como o
sistema de origem entregou. Converter tipo é trabalho da transformação; se a
conversão acontecesse na leitura, um valor inesperado quebraria a ingestão em
vez de aparecer como problema de qualidade.

## O que mudou em relação à Etapa 2

A Etapa 2 propunha Apache Airflow numa instância EC2 e PostgreSQL no RDS. A
troca não foi preferência: o readme do Learner Lab informa que, ao fim da
sessão, as instâncias EC2 são **paradas e religadas automaticamente** na sessão
seguinte, e que o RDS pode não ser parado — e a própria AWS religa uma instância
RDS parada após 7 dias. Um desenho baseado em servidores voltaria a ligar
sozinho e consumiria o orçamento de US$ 50 sem ninguém usar.

S3, Glue, Athena e Step Functions não têm nada que ligue sozinho: cobram por
execução e por byte. Entre um desenho que o ambiente não sustenta e um que
custa centavos, a escolha é técnica, não estética.

## O fluxo de controle

A máquina de estados `nexo-carga` tem oito estados:

1. **ValidarCamadaBruta** — conta as linhas em `nexo_raw.crm_oportunidades`
2. **LerContagemBruta** — lê o resultado da contagem
3. **HaDadoBruto** — se for zero, falha aqui; não adianta transformar o vazio
4. **ConstruirEstrela** — executa o job do Glue e espera o fim
5. **ValidarEstrela** — conta as linhas em `nexo_dw.fato_oportunidade`
6. **LerContagemEstrela** — lê o resultado
7. **EstrelaConsistente** — se for zero, falha; o job pode terminar bem e não
   gravar nada
8. **CargaConcluida**

O passo do Glue repete até três vezes em caso de concorrência (o laboratório
permite uma execução simultânea) e desvia para um estado de falha explícito em
qualquer outro erro, com a mensagem apontando o log do CloudWatch.

## O que foi medido

| Verificação | Resultado |
|---|---|
| Linhas lidas na camada bruta | 19.280 / 920 / 180 / 30 / 6 / 5 — idênticas aos CSVs |
| Partições encontradas sem crawler | 225 (CRM) e 184 (Meta Ads) |
| Execução do job do Glue | SUCCEEDED, 59 segundos |
| Compressão CSV → Parquet | 5,7 MB → 353 KB |
| Execução da máquina de estados | SUCCEEDED, oito estados |
| Custo de aquisição por plano | R$ 1.465 a R$ 1.532 |

O custo de aquisição é a validação mais importante: o caso da Nexo estima
R$ 1.450, e o valor calculado sobre o modelo estrela chegou perto disso por um
caminho independente — partindo do investimento diário do Meta Ads rateado
entre os contratos de cada campanha.

## Custo real

| Item | Gasto |
|---|---|
| Armazenamento no S3 (6 MB) | menos de US$ 0,01 por mês |
| DDL no Athena | zero — comando de definição não é cobrado |
| Consultas no Athena | US$ 0,0002 por execução do conjunto |
| Job do Glue | US$ 0,0005 por execução |
| Step Functions | gratuito até 4.000 transições por mês; o fluxo usa 8 |

**Total gasto até aqui: cerca de US$ 0,002 dos US$ 50.**

## Como reproduzir

As credenciais do laboratório expiram a cada sessão: pegue-as em **AWS Details**,
grave em `~/.aws/credentials` e defina `AWS_DEFAULT_REGION=us-east-1`.

```bash
python particionar.py                                            # organiza por data
python subir_s3.py dados_particionados --bucket nexo-eixo4-dados # simula
python subir_s3.py dados_particionados --bucket nexo-eixo4-dados --confirmar
python rodar_athena.py sql/01_raw.sql
python criar_job_glue.py --executar
python rodar_athena.py sql/02_estrela.sql
python criar_fluxo.py --executar                                 # fluxo completo
python rodar_athena.py sql/03_perguntas.sql                      # as respostas
```

O `subir_s3.py` só envia com `--confirmar`, e pula arquivo que já está no
destino com o mesmo tamanho. O job do Glue também pode rodar na máquina local,
sem AWS nenhuma:

```bash
python glue/job_estrela.py --origem dados_particionados --destino saida_estrela
```

É o que permitiu depurar a transformação inteira antes de gastar o primeiro
centavo do orçamento.
