-- Camada bruta: tabelas externas do Athena sobre os CSVs como chegaram das origens.
--
-- Tudo é declarado como texto de propósito. A camada bruta guarda o dado no formato
-- do sistema de origem; converter tipo é trabalho da transformação, não da leitura.
--
-- Não há crawler. As partições são declaradas por "partition projection": o Athena
-- calcula os caminhos a partir da faixa de datas abaixo, em vez de varrer o bucket.
-- Isso evita tanto o custo do crawler quanto o MSCK REPAIR TABLE a cada carga.
--
-- Bucket: trocar nexo-eixo4-dados aqui se o nome já estiver em uso (eles são únicos
-- no mundo). É o único valor a ajustar neste arquivo.

CREATE DATABASE IF NOT EXISTS nexo_raw;

-- ---------------------------------------------------------------------------- CRM
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.crm_oportunidades (
  id_oportunidade          string,
  data_criacao             string,
  pipeline                 string,
  plano_interesse          string,
  fase_atual               string,
  data_entrada_fase        string,
  status                   string,
  fonte                    string,
  utm_source               string,
  utm_medium               string,
  utm_campaign             string,
  utm_content              string,
  utm_term                 string,
  origem_lead              string,
  passou_por_chat          string,
  reuniao_agendada_bot     string,
  temperatura              string,
  id_sdr                   string,
  id_closer                string,
  id_recuperador           string,
  data_primeiro_contato    string,
  qtd_tentativas_contato   string,
  data_qualificacao        string,
  data_reuniao             string,
  data_follow_up           string,
  data_forecast            string,
  data_fechamento          string,
  fase_perda               string,
  motivo_perda             string,
  plano_contratado         string,
  valor_mensal_negociado   string,
  valor_contrato_12m       string,
  segmento_varejo          string,
  porte_empresa            string,
  uf                       string,
  faturamento_mensal_faixa string
)
PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/crm_oportunidades/'
TBLPROPERTIES (
  'skip.header.line.count'      = '1',
  'projection.enabled'          = 'true',
  'projection.dt.type'          = 'date',
  'projection.dt.format'        = 'yyyy-MM-dd',
  -- Começa em janeiro: as oportunidades dos meses de aquecimento que ainda estavam
  -- abertas em março entraram no CRM, e a primeira partição real é 2026-01-12.
  'projection.dt.range'         = '2026-01-01,2026-08-31',
  'projection.dt.interval'      = '1',
  'projection.dt.interval.unit' = 'DAYS',
  'storage.location.template'   = 's3://nexo-eixo4-dados/raw/crm_oportunidades/dt=${dt}/'
);

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.crm_equipe_comercial (
  id_colaborador string,
  funcao         string,
  tier           string,
  pipeline       string,
  data_admissao  string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/crm_equipe_comercial/'
TBLPROPERTIES ('skip.header.line.count' = '1');

-- ----------------------------------------------------------------------- Meta Ads
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.meta_insights_diario (
  date_start       string,
  date_stop        string,
  campaign_id      string,
  campaign_name    string,
  objective        string,
  impressions      string,
  clicks           string,
  cpm              string,
  ctr              string,
  spend            string,
  leads            string,
  account_currency string
)
PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/meta_insights_diario/'
TBLPROPERTIES (
  'skip.header.line.count'      = '1',
  'projection.enabled'          = 'true',
  'projection.dt.type'          = 'date',
  'projection.dt.format'        = 'yyyy-MM-dd',
  'projection.dt.range'         = '2026-03-01,2026-08-31',
  'projection.dt.interval'      = '1',
  'projection.dt.interval.unit' = 'DAYS',
  'storage.location.template'   = 's3://nexo-eixo4-dados/raw/meta_insights_diario/dt=${dt}/'
);

-- -------------------------------------------------------------------- Planilhas
CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.planilhas_metas_mensais (
  mes            string,
  id_colaborador string,
  funcao         string,
  tipo_meta      string,
  valor_meta     string
)
PARTITIONED BY (dt string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/planilhas_metas_mensais/'
TBLPROPERTIES (
  'skip.header.line.count'      = '1',
  'projection.enabled'          = 'true',
  'projection.dt.type'          = 'date',
  'projection.dt.format'        = 'yyyy-MM-dd',
  'projection.dt.range'         = '2026-03-01,2026-08-01',
  'projection.dt.interval'      = '1',
  'projection.dt.interval.unit' = 'MONTHS',
  'storage.location.template'   = 's3://nexo-eixo4-dados/raw/planilhas_metas_mensais/dt=${dt}/'
);

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.planilhas_faixas_comissao (
  faixa               string,
  venda_anual_min     string,
  venda_anual_max     string,
  percentual_comissao string,
  caixa_minimo        string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/planilhas_faixas_comissao/'
TBLPROPERTIES ('skip.header.line.count' = '1');

CREATE EXTERNAL TABLE IF NOT EXISTS nexo_raw.planilhas_regras_bonus (
  papel string,
  regra string,
  valor string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ('separatorChar' = ',', 'quoteChar' = '"', 'escapeChar' = '\\')
STORED AS TEXTFILE
LOCATION 's3://nexo-eixo4-dados/raw/planilhas_regras_bonus/'
TBLPROPERTIES ('skip.header.line.count' = '1');

-- Conferência da leitura (deve devolver 19280, 920, 180, 30, 5 e 6):
-- SELECT 'crm_oportunidades' AS tabela, count(*) FROM nexo_raw.crm_oportunidades
-- UNION ALL SELECT 'meta_insights_diario',      count(*) FROM nexo_raw.meta_insights_diario
-- UNION ALL SELECT 'planilhas_metas_mensais',   count(*) FROM nexo_raw.planilhas_metas_mensais
-- UNION ALL SELECT 'crm_equipe_comercial',      count(*) FROM nexo_raw.crm_equipe_comercial
-- UNION ALL SELECT 'planilhas_faixas_comissao', count(*) FROM nexo_raw.planilhas_faixas_comissao
-- UNION ALL SELECT 'planilhas_regras_bonus',    count(*) FROM nexo_raw.planilhas_regras_bonus;
