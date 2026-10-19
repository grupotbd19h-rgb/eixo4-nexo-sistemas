-- As duas perguntas do capítulo 3 do documento, respondidas sobre o modelo estrela.
-- São estas consultas que justificam a plataforma: antes dela, nenhuma delas podia
-- ser escrita, porque cada pedaço do dado morava num sistema diferente.

-- ===========================================================================
-- Pergunta 1 — Como ordenar a fila de atendimento por chance de conversão?
-- ===========================================================================

-- 1.a  O efeito do tempo de resposta. É o achado que sustenta a fila: a conversão
--      despenca conforme o primeiro contato demora.
SELECT
    CASE
        WHEN horas_ate_primeiro_contato IS NULL  THEN '5. nunca contatada'
        WHEN horas_ate_primeiro_contato < 1      THEN '1. ate 1 hora'
        WHEN horas_ate_primeiro_contato < 24     THEN '2. 1 a 24 horas'
        WHEN horas_ate_primeiro_contato < 72     THEN '3. 24 a 72 horas'
        ELSE                                          '4. mais de 72 horas'
    END                                                      AS faixa_de_resposta,
    count(*)                                                 AS oportunidades,
    sum(CASE WHEN ganha THEN 1 ELSE 0 END)                   AS contratos,
    round(100.0 * sum(CASE WHEN ganha THEN 1 ELSE 0 END) / count(*), 2) AS conversao_pct
FROM nexo_dw.fato_oportunidade
GROUP BY 1
ORDER BY 1;

-- 1.b  O escore da fila: conversão histórica por combinação de atributos conhecidos
--      no momento em que a oportunidade entra. Só isso já ordena o atendimento.
SELECT
    f.fonte,
    f.temperatura,
    f.porte_empresa,
    f.plano_interesse,
    count(*)                                                 AS oportunidades,
    sum(CASE WHEN f.ganha THEN 1 ELSE 0 END)                 AS contratos,
    round(100.0 * sum(CASE WHEN f.ganha THEN 1 ELSE 0 END) / count(*), 2) AS conversao_pct,
    round(avg(f.valor_contrato_12m), 0)                      AS ticket_medio_12m
FROM nexo_dw.fato_oportunidade f
GROUP BY 1, 2, 3, 4
HAVING count(*) >= 100                 -- corta combinação rara, que gera taxa sem sentido
ORDER BY conversao_pct DESC;

-- ===========================================================================
-- Pergunta 2 — Quanto custa conquistar um cliente, por canal e por plano?
-- ===========================================================================

-- 2.a  Custo de aquisição por campanha. A linha "(sem UTM)" é a parte do funil que
--      nenhum investimento explica — é o custo de não ter rastreio, e aparece de propósito.
WITH investimento AS (
    SELECT id_campanha, sum(investimento) AS investimento
    FROM nexo_dw.fato_investimento_anuncio
    GROUP BY 1
),
resultado AS (
    SELECT id_campanha,
           count(*)                        AS oportunidades,
           sum(CASE WHEN ganha THEN 1 ELSE 0 END) AS contratos,
           sum(CASE WHEN ganha THEN valor_contrato_12m ELSE 0 END) AS receita_12m
    FROM nexo_dw.fato_oportunidade
    GROUP BY 1
)
SELECT
    c.nome_campanha,
    c.plataforma,
    coalesce(i.investimento, 0)                              AS investimento,
    r.oportunidades,
    r.contratos,
    CASE WHEN r.contratos > 0
         THEN round(coalesce(i.investimento, 0) / r.contratos, 2) END AS cac,
    r.receita_12m,
    CASE WHEN coalesce(i.investimento, 0) > 0
         THEN round(r.receita_12m / i.investimento, 2) END    AS retorno_sobre_investimento
FROM resultado r
JOIN nexo_dw.dim_campanha c ON c.id_campanha = r.id_campanha
LEFT JOIN investimento i    ON i.id_campanha = r.id_campanha
ORDER BY investimento DESC;

-- 2.b  Custo de aquisição por plano. O investimento de cada campanha é rateado entre
--      os planos que ela fechou, na proporção dos contratos.
WITH investimento AS (
    SELECT id_campanha, sum(investimento) AS investimento
    FROM nexo_dw.fato_investimento_anuncio
    GROUP BY 1
),
contratos AS (
    SELECT id_campanha, plano_contratado, count(*) AS contratos
    FROM nexo_dw.fato_oportunidade
    WHERE ganha
    GROUP BY 1, 2
),
total_por_campanha AS (
    SELECT id_campanha, sum(contratos) AS contratos FROM contratos GROUP BY 1
)
SELECT
    c.plano_contratado                                       AS plano,
    p.mensalidade,
    sum(c.contratos)                                         AS contratos,
    round(sum(i.investimento * c.contratos / t.contratos), 2) AS investimento_rateado,
    round(sum(i.investimento * c.contratos / t.contratos) / sum(c.contratos), 2) AS cac
FROM contratos c
JOIN total_por_campanha t ON t.id_campanha = c.id_campanha
JOIN investimento i       ON i.id_campanha = c.id_campanha
LEFT JOIN nexo_dw.dim_plano p ON p.id_plano = c.plano_contratado
GROUP BY 1, 2
ORDER BY cac DESC;
