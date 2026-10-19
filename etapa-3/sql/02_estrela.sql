-- Armazém de dados: tabelas externas do Athena sobre os Parquet gravados pelo job
-- do Glue (glue/job_estrela.py). São as tabelas do Quadro 3 do documento.
--
-- Aqui os tipos existem: data é data, medida é número, indicador é booleano. É a
-- diferença entre esta camada e a bruta.

CREATE DATABASE IF NOT EXISTS nexo_dw;

-- -------------------------------------------------------------------- dimensões
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.dim_data (
  data          date,
  ano           int,
  mes           int,
  dia           int,
  trimestre     int,
  nome_mes      string,
  dia_semana    string,
  fim_de_semana boolean
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/dim_data/';

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.dim_campanha (
  id_campanha   string,
  nome_campanha string,
  objetivo      string,
  plataforma    string
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/dim_campanha/';

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.dim_plano (
  id_plano       string,
  mensalidade    double,
  perfil_cliente string
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/dim_plano/';

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.dim_colaborador (
  id_colaborador string,
  funcao         string,
  tier           double,
  time           string,
  data_admissao  date
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/dim_colaborador/';

-- ------------------------------------------------------------------------ fatos
-- Snapshot acumulado: uma linha por oportunidade, reescrita conforme a negociação anda.
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.fato_oportunidade (
  id_oportunidade            string,
  data_criacao               date,
  data_fechamento            date,
  horas_ate_primeiro_contato double,
  sem_contato_72h            boolean,
  id_campanha                string,
  fonte                      string,
  origem_lead                string,
  plano_interesse            string,
  plano_contratado           string,
  id_sdr                     string,
  id_closer                  string,
  segmento_varejo            string,
  porte_empresa              string,
  uf                         string,
  temperatura                double,
  qtd_tentativas_contato     bigint,
  valor_mensal_negociado     double,
  valor_contrato_12m         double,
  status                     string,
  ganha                      boolean,
  motivo_perda               string
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/fato_oportunidade/';

-- Transacional diário: uma linha por campanha e dia, nunca alterada depois de gravada.
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.fato_investimento_anuncio (
  data         date,
  id_campanha  string,
  impressoes   bigint,
  cliques      bigint,
  leads        bigint,
  investimento double,
  moeda        string
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/fato_investimento_anuncio/';

-- Snapshot periódico: uma linha por colaborador e mês, fechada na virada do mês.
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_dw.fato_meta_vendedor (
  data           date,
  id_colaborador string,
  funcao         string,
  tipo_meta      string,
  valor_meta     double
)
STORED AS PARQUET
LOCATION 's3://nexo-eixo4-dados/dw/fato_meta_vendedor/';
