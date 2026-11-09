-- Conferência entre origem e destino: o indicador de observabilidade que o
-- documento da Etapa 3 deixou como próximo passo no item 9.4.
--
-- A pergunta é simples e vale para qualquer pipeline: o que saiu da origem
-- chegou inteiro no destino? Contagem de registro e soma de medida são as duas
-- provas que pegam a maioria dos erros de carga — linha perdida num filtro,
-- junção que duplica, conversão de número que zera.
--
-- A camada bruta é toda texto, então a soma exige conversão explícita. É de
-- propósito: a conversão acontece aqui, na leitura analítica, e não na ingestão.

-- Detalhamento, para o documento: uma linha por verificação.
SELECT
    verificacao,
    origem,
    destino,
    round(destino - origem, 2)                                   AS diferenca,
    CASE WHEN abs(destino - origem) < 0.01 THEN 'OK' ELSE 'DIVERGENTE' END AS situacao
FROM (
    SELECT 'Oportunidades (registros)'          AS verificacao,
           (SELECT count(*) FROM nexo_raw.crm_oportunidades)           AS origem,
           (SELECT count(*) FROM nexo_dw.fato_oportunidade)            AS destino
    UNION ALL
    SELECT 'Insights de anúncio (registros)',
           (SELECT count(*) FROM nexo_raw.meta_insights_diario),
           (SELECT count(*) FROM nexo_dw.fato_investimento_anuncio)
    UNION ALL
    SELECT 'Metas mensais (registros)',
           (SELECT count(*) FROM nexo_raw.planilhas_metas_mensais),
           (SELECT count(*) FROM nexo_dw.fato_meta_vendedor)
    UNION ALL
    SELECT 'Investimento em anúncios (R$)',
           (SELECT round(sum(cast(spend AS double)), 2) FROM nexo_raw.meta_insights_diario),
           (SELECT round(sum(investimento), 2) FROM nexo_dw.fato_investimento_anuncio)
    UNION ALL
    SELECT 'Leads informados pela plataforma',
           (SELECT sum(cast(leads AS bigint)) FROM nexo_raw.meta_insights_diario),
           (SELECT sum(leads) FROM nexo_dw.fato_investimento_anuncio)
)
ORDER BY situacao DESC, verificacao;

-- Resumo, para o fluxo de controle: quantas verificações divergiram.
-- A máquina de estados lê este número e reprova a carga quando ele não é zero.
SELECT count(*) AS divergencias
FROM (
    SELECT 1 AS n
    WHERE (SELECT count(*) FROM nexo_raw.crm_oportunidades)
        <> (SELECT count(*) FROM nexo_dw.fato_oportunidade)
    UNION ALL
    SELECT 1
    WHERE (SELECT count(*) FROM nexo_raw.meta_insights_diario)
        <> (SELECT count(*) FROM nexo_dw.fato_investimento_anuncio)
    UNION ALL
    SELECT 1
    WHERE (SELECT count(*) FROM nexo_raw.planilhas_metas_mensais)
        <> (SELECT count(*) FROM nexo_dw.fato_meta_vendedor)
    UNION ALL
    SELECT 1
    WHERE abs((SELECT sum(cast(spend AS double)) FROM nexo_raw.meta_insights_diario)
            - (SELECT sum(investimento) FROM nexo_dw.fato_investimento_anuncio)) >= 0.01
);
