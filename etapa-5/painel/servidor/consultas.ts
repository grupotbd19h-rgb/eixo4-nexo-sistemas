// As consultas que alimentam o painel, executadas no Athena sobre o modelo
// estrela (nexo_dw), e a montagem do objeto Painel que o front desenha.
//
// O SQL das duas perguntas de negócio segue etapa-3/sql/03_perguntas.sql — as
// mesmas definições do documento —, e o restante replica o que antes saía do
// exportador em Python, agora lido direto do banco.

import { consultar, type Execucao, type Linha } from './athena'
import { quiQuadrado } from './estatistica'
import type {
  Atributo,
  Campanha,
  Closer,
  Combinacao,
  FaixaResposta,
  MesFunil,
  MesMeta,
  MetaSemConfronto,
  Painel,
  Pessoa,
  Plano,
  Rastreio,
  Tier,
  TimePapel,
} from '../src/tipos'

const SINTETICAS = "('SEM_UTM', 'UTM_QUEBRADA')"
// A janela de operação começa em março; janeiro e fevereiro são aquecimento do
// funil e ficam fora da série mensal (continuam nos totais).
const INICIO_SERIE = "DATE '2026-03-01'"
// Combinação com menos que isso gera taxa sem sentido estatístico.
const MINIMO_COMBINACAO = 100

export const SQL = {
  resumo: `
    SELECT
      count(*)                                                    AS oportunidades,
      sum(if(ganha, 1, 0))                                        AS contratos,
      sum(if(ganha, valor_contrato_12m, 0))                       AS receita12m,
      sum(if(ganha AND coalesce(id_campanha, '') NOT IN ${SINTETICAS}, 1, 0))                  AS contratos_atribuidos,
      sum(if(ganha AND coalesce(id_campanha, '') NOT IN ${SINTETICAS}, valor_contrato_12m, 0)) AS receita_atribuida,
      (SELECT sum(investimento) FROM fato_investimento_anuncio)   AS investimento,
      (SELECT cast(min(data) AS varchar) FROM fato_investimento_anuncio) AS inicio,
      (SELECT cast(max(data) AS varchar) FROM fato_investimento_anuncio) AS fim,
      (SELECT count(*) FROM dim_campanha WHERE id_campanha NOT IN ${SINTETICAS}) AS campanhas,
      (SELECT count(DISTINCT id_colaborador) FROM dim_colaborador) AS efetivo
    FROM fato_oportunidade`,

  // Pergunta 1.a — mesma faixa do documento (Tabela 1).
  resposta: `
    SELECT
      CASE
        WHEN horas_ate_primeiro_contato IS NULL THEN 5
        WHEN horas_ate_primeiro_contato < 1     THEN 1
        WHEN horas_ate_primeiro_contato < 24    THEN 2
        WHEN horas_ate_primeiro_contato < 72    THEN 3
        ELSE 4
      END                    AS ordem,
      count(*)               AS oportunidades,
      sum(if(ganha, 1, 0))   AS contratos
    FROM fato_oportunidade
    GROUP BY 1
    ORDER BY 1`,

  funil: `
    SELECT
      date_format(data_criacao, '%Y-%m')      AS mes,
      count(*)                                AS oportunidades,
      sum(if(ganha, 1, 0))                    AS contratos,
      sum(if(ganha, valor_contrato_12m, 0))   AS receita12m
    FROM fato_oportunidade
    WHERE data_criacao >= ${INICIO_SERIE}
    GROUP BY 1
    ORDER BY 1`,

  // Pergunta 2.a — custo de aquisição por campanha.
  campanhas: `
    WITH investimento AS (
      SELECT id_campanha, sum(investimento) AS investimento
      FROM fato_investimento_anuncio GROUP BY 1
    ),
    resultado AS (
      SELECT id_campanha,
             count(*)                              AS oportunidades,
             sum(if(ganha, 1, 0))                  AS contratos,
             sum(if(ganha, valor_contrato_12m, 0)) AS receita12m
      FROM fato_oportunidade GROUP BY 1
    )
    SELECT r.id_campanha, c.nome_campanha, c.objetivo,
           r.oportunidades, r.contratos, r.receita12m,
           round(coalesce(i.investimento, 0), 2) AS investimento
    FROM resultado r
    LEFT JOIN dim_campanha c ON c.id_campanha = r.id_campanha
    LEFT JOIN investimento i ON i.id_campanha = r.id_campanha`,

  // Pergunta 2.b — investimento de cada campanha rateado entre os planos que ela fechou.
  planos: `
    WITH investimento AS (
      SELECT id_campanha, sum(investimento) AS investimento
      FROM fato_investimento_anuncio GROUP BY 1
    ),
    contratos AS (
      SELECT id_campanha, plano_contratado, count(*) AS contratos
      FROM fato_oportunidade WHERE ganha GROUP BY 1, 2
    ),
    total AS (SELECT id_campanha, sum(contratos) AS contratos FROM contratos GROUP BY 1)
    SELECT c.plano_contratado                                         AS plano,
           sum(c.contratos)                                           AS contratos,
           round(sum(i.investimento * c.contratos / t.contratos), 2)  AS investimento
    FROM contratos c
    JOIN total t        ON t.id_campanha = c.id_campanha
    JOIN investimento i ON i.id_campanha = c.id_campanha
    GROUP BY 1
    ORDER BY 1`,

  rastreio: `
    SELECT
      CASE id_campanha WHEN 'SEM_UTM' THEN 2 WHEN 'UTM_QUEBRADA' THEN 3 ELSE 1 END AS ordem,
      count(*)             AS oportunidades,
      sum(if(ganha, 1, 0)) AS contratos
    FROM fato_oportunidade
    GROUP BY 1
    ORDER BY 1`,

  ranking: `
    SELECT c.id_colaborador, c.time, c.tier,
           count(*)                                  AS oportunidades,
           sum(if(f.ganha, 1, 0))                    AS contratos,
           sum(if(f.ganha, f.valor_contrato_12m, 0)) AS receita12m
    FROM fato_oportunidade f
    JOIN dim_colaborador c ON c.id_colaborador = f.id_closer
    GROUP BY 1, 2, 3
    ORDER BY receita12m DESC
    LIMIT 10`,

  // Cada pessoa na função em que atua no funil (SDR qualifica, closer fecha),
  // com a meta de valor vendido confrontada ao realizado — só a do closer é
  // verificável contra o funil.
  pessoas: `
    WITH atuacao AS (
      SELECT id_sdr AS id_colaborador, 'SDR' AS papel, ganha, valor_contrato_12m AS valor,
             horas_ate_primeiro_contato AS horas
      FROM fato_oportunidade WHERE coalesce(id_sdr, '') <> ''
      UNION ALL
      SELECT id_closer, 'Closer', ganha, valor_contrato_12m, horas_ate_primeiro_contato
      FROM fato_oportunidade WHERE coalesce(id_closer, '') <> ''
    ),
    agregado AS (
      SELECT id_colaborador, papel,
             count(*)                 AS oportunidades,
             sum(if(ganha, 1, 0))     AS contratos,
             sum(if(ganha, valor, 0)) AS receita12m,
             array_sort(filter(array_agg(horas), h -> h IS NOT NULL)) AS hs
      FROM atuacao GROUP BY 1, 2
    ),
    alvo AS (
      SELECT id_colaborador, sum(meta) AS meta, sum(realizado) AS realizado
      FROM confronto GROUP BY 1
    )
    SELECT a.id_colaborador, a.papel, c.funcao, c.time, c.tier,
           a.oportunidades, a.contratos, a.receita12m,
           -- mediana exata: média dos dois elementos centrais (iguais se n é ímpar)
           CASE WHEN cardinality(a.hs) = 0 THEN NULL
                ELSE (element_at(a.hs, (cardinality(a.hs) + 1) / 2)
                      + element_at(a.hs, cardinality(a.hs) / 2 + 1)) / 2 END AS mediana_horas,
           t.meta, t.realizado
    FROM agregado a
    JOIN dim_colaborador c ON c.id_colaborador = a.id_colaborador
    LEFT JOIN alvo t       ON t.id_colaborador = a.id_colaborador
    ORDER BY a.receita12m DESC, a.id_colaborador`,

  metaMensal: `
    SELECT mes, sum(meta) AS meta, sum(realizado) AS realizado
    FROM confronto
    GROUP BY 1
    ORDER BY 1`,

  metasSemConfronto: `
    SELECT funcao, tipo_meta,
           count(DISTINCT id_colaborador) AS pessoas,
           round(avg(valor_meta), 1)      AS media
    FROM fato_meta_vendedor
    WHERE tipo_meta <> 'valor_vendido_anual'
    GROUP BY 1, 2
    ORDER BY 1, 2`,

  // Pergunta 1.b — o escore da fila, com intervalo de confiança de Wilson a 95%.
  // O intervalo mostra o quanto cada taxa é confiável: combinação pequena tem
  // intervalo largo, e duas combinações cujos intervalos se sobrepõem não são,
  // de fato, distinguíveis.
  combinacoes: `
    WITH g AS (
      SELECT fonte, temperatura, porte_empresa, plano_interesse,
             count(*)                                AS n,
             sum(if(ganha, 1, 0))                    AS c,
             avg(if(ganha, valor_contrato_12m))      AS ticket
      FROM fato_oportunidade
      GROUP BY 1, 2, 3, 4
      HAVING count(*) >= ${MINIMO_COMBINACAO}
    ),
    p AS (SELECT *, cast(c AS double) / n AS taxa, 1.959964 * 1.959964 AS z2 FROM g)
    SELECT fonte, cast(temperatura AS varchar) AS temperatura, porte_empresa, plano_interesse,
           n AS oportunidades, c AS contratos,
           round(100 * taxa, 2) AS conversao,
           round(100 * (taxa + z2 / (2 * n) - 1.959964 * sqrt(taxa * (1 - taxa) / n + z2 / (4 * n * n))) / (1 + z2 / n), 2) AS ic_inferior,
           round(100 * (taxa + z2 / (2 * n) + 1.959964 * sqrt(taxa * (1 - taxa) / n + z2 / (4 * n * n))) / (1 + z2 / n), 2) AS ic_superior,
           round(ticket, 0) AS ticket
    FROM p
    ORDER BY taxa DESC, n DESC`,

  // Conversão por nível de cada atributo do escore — base do teste qui-quadrado.
  atributos: ['fonte', 'temperatura', 'porte_empresa', 'plano_interesse']
    .map(
      (a) => `
      SELECT '${a}' AS atributo, cast(${a} AS varchar) AS nivel,
             count(*) AS oportunidades, sum(if(ganha, 1, 0)) AS contratos
      FROM fato_oportunidade GROUP BY 1, 2`,
    )
    .join('\n      UNION ALL') + '\n    ORDER BY 1, 2',

  saude: `
    SELECT
      (SELECT count(*) FROM fato_oportunidade)         AS oportunidades,
      (SELECT count(*) FROM fato_investimento_anuncio) AS investimentos,
      (SELECT count(*) FROM fato_meta_vendedor)        AS metas,
      (SELECT count(*) FROM dim_colaborador)           AS colaboradores`,
}

// Meta de valor vendido contra o realizado, por closer e mês — compartilhada
// pelas consultas de pessoas e de meta mensal.
const CONFRONTO = `
  WITH realizado AS (
    SELECT id_closer AS id_colaborador, date_format(data_fechamento, '%Y-%m') AS mes,
           sum(valor_contrato_12m) AS realizado
    FROM fato_oportunidade
    WHERE ganha AND coalesce(id_closer, '') <> ''
    GROUP BY 1, 2
  ),
  meta AS (
    SELECT id_colaborador, date_format(data, '%Y-%m') AS mes, sum(valor_meta) AS meta
    FROM fato_meta_vendedor WHERE tipo_meta = 'valor_vendido_anual'
    GROUP BY 1, 2
  ),
  confronto AS (
    SELECT coalesce(m.id_colaborador, r.id_colaborador) AS id_colaborador,
           coalesce(m.mes, r.mes)                       AS mes,
           coalesce(m.meta, 0)                          AS meta,
           coalesce(r.realizado, 0)                     AS realizado
    FROM meta m
    FULL OUTER JOIN realizado r ON r.id_colaborador = m.id_colaborador AND r.mes = m.mes
  )`

// Encaixa as CTEs de uma consulta depois das do confronto, num único WITH.
const comConfronto = (sql: string) => CONFRONTO + ',\n' + sql.trim().replace(/^WITH\s+/i, '')

// ---------------------------------------------------------------- utilidades

const n = (v: unknown) => (typeof v === 'number' ? v : Number(v ?? 0))
const nulo = (v: unknown) => (v === null || v === undefined ? null : n(v))
const r2 = (v: number) => Math.round(v * 100) / 100
const r1 = (v: number) => Math.round(v * 10) / 10
const taxa = (c: number, t: number) => (t > 0 ? r2((100 * c) / t) : 0)

// Rótulos de leitura para os códigos gravados no modelo estrela.
const ROTULOS: Record<string, Record<string, string>> = {
  temperatura: { '0.25': 'Baixa', '0.5': 'Média', '0.75': 'Alta' },
  fonte: { direto: 'Acesso direto', indicacao: 'Indicação', meta_ads: 'Meta Ads', organico: 'Orgânico' },
}
const rotulo = (atributo: string, v: unknown) =>
  v === null || v === undefined ? '(vazio)' : (ROTULOS[atributo]?.[String(v)] ?? String(v))

const FAIXAS = ['','Até 1h', '1 a 24h', '24 a 72h', 'Mais de 72h', 'Nunca contatada']
const SITUACOES = ['', 'Atribuída a campanha', 'Sem UTM', 'UTM não substituída']

export type Diagnostico = {
  consultas: number
  bytesLidos: number
  ms: number
  ids: string[]
}

// ------------------------------------------------------------------- montagem

export async function montarPainel(): Promise<{ painel: Painel; diagnostico: Diagnostico }> {
  const inicio = Date.now()
  const nomes = [
    'resumo', 'resposta', 'funil', 'campanhas', 'planos', 'rastreio', 'ranking',
    'pessoas', 'metaMensal', 'metasSemConfronto', 'combinacoes', 'atributos',
  ] as const
  const textos: Record<(typeof nomes)[number], string> = {
    ...SQL,
    pessoas: comConfronto(SQL.pessoas),
    metaMensal: CONFRONTO + '\n' + SQL.metaMensal,
  }

  // Todas em paralelo: cada uma leva de 1 a 3 s no Athena, e são independentes.
  const execucoes = await Promise.all(nomes.map((k) => consultar(textos[k])))
  const res = Object.fromEntries(nomes.map((k, i) => [k, execucoes[i].linhas])) as Record<
    (typeof nomes)[number],
    Linha[]
  >

  const t = res.resumo[0]
  const contratos = n(t.contratos)
  const oportunidades = n(t.oportunidades)
  const investimento = n(t.investimento)
  const contratosAtribuidos = n(t.contratos_atribuidos)
  const receitaAtribuida = n(t.receita_atribuida)
  const receita12m = n(t.receita12m)

  const resposta: FaixaResposta[] = res.resposta.map((l) => ({
    faixa: FAIXAS[n(l.ordem)],
    oportunidades: n(l.oportunidades),
    contratos: n(l.contratos),
    conversao: taxa(n(l.contratos), n(l.oportunidades)),
  }))

  const funil: MesFunil[] = res.funil.map((l) => ({
    mes: String(l.mes),
    oportunidades: n(l.oportunidades),
    contratos: n(l.contratos),
    conversao: taxa(n(l.contratos), n(l.oportunidades)),
    receita12m: r2(n(l.receita12m)),
  }))

  const campanhas: Campanha[] = res.campanhas.map((l) => {
    const inv = n(l.investimento)
    const ct = n(l.contratos)
    const rec = n(l.receita12m)
    return {
      id_campanha: String(l.id_campanha),
      nome_campanha: String(l.nome_campanha ?? l.id_campanha),
      objetivo: String(l.objetivo ?? ''),
      oportunidades: n(l.oportunidades),
      contratos: ct,
      receita12m: rec,
      investimento: inv,
      cac: ct > 0 ? r2(inv / ct) : null,
      retorno: inv > 0 ? r2(rec / inv) : null,
    }
  })

  const planos: Plano[] = res.planos.map((l) => ({
    plano: String(l.plano),
    contratos: n(l.contratos),
    investimento: n(l.investimento),
    cac: r2(n(l.investimento) / n(l.contratos)),
  }))

  const rastreio: Rastreio[] = res.rastreio.map((l) => ({
    situacao: SITUACOES[n(l.ordem)],
    oportunidades: n(l.oportunidades),
    contratos: n(l.contratos),
  }))

  const ranking: Closer[] = res.ranking.map((l) => ({
    id_colaborador: String(l.id_colaborador),
    time: String(l.time),
    tier: n(l.tier),
    oportunidades: n(l.oportunidades),
    contratos: n(l.contratos),
    receita12m: n(l.receita12m),
    conversao: taxa(n(l.contratos), n(l.oportunidades)),
  }))

  const pessoas: Pessoa[] = res.pessoas.map((l) => {
    const meta = nulo(l.meta)
    const realizado = nulo(l.realizado)
    const mediana = nulo(l.mediana_horas)
    return {
      id_colaborador: String(l.id_colaborador),
      papel: String(l.papel),
      funcao: String(l.funcao),
      time: String(l.time),
      tier: nulo(l.tier),
      oportunidades: n(l.oportunidades),
      contratos: n(l.contratos),
      receita12m: n(l.receita12m),
      conversao: taxa(n(l.contratos), n(l.oportunidades)),
      medianaHoras: mediana === null ? null : r1(mediana),
      meta,
      realizado,
      atingimento: meta && realizado !== null ? r1((100 * realizado) / meta) : null,
    }
  })

  // Agregados de time e tier saem das pessoas, para não divergirem delas.
  const agrupar = <K extends string>(lista: Pessoa[], chave: (p: Pessoa) => K) => {
    const grupos = new Map<K, Pessoa[]>()
    for (const p of lista) grupos.set(chave(p), [...(grupos.get(chave(p)) ?? []), p])
    return [...grupos.entries()].map(([k, ps]) => {
      const op = ps.reduce((s, p) => s + p.oportunidades, 0)
      const ct = ps.reduce((s, p) => s + p.contratos, 0)
      return {
        chave: k,
        primeiro: ps[0],
        pessoas: new Set(ps.map((p) => p.id_colaborador)).size,
        oportunidades: op,
        contratos: ct,
        receita12m: ps.reduce((s, p) => s + p.receita12m, 0),
        conversao: taxa(ct, op),
      }
    })
  }

  const porTime: TimePapel[] = agrupar(pessoas, (p) => `${p.time}|${p.papel}`)
    .map(({ primeiro, chave: _, ...g }) => ({ time: primeiro.time, papel: primeiro.papel, ...g }))
    .sort((a, b) => a.time.localeCompare(b.time) || a.papel.localeCompare(b.papel))

  const porTier: Tier[] = agrupar(
    pessoas.filter((p) => p.papel === 'Closer' && p.tier !== null),
    (p) => String(p.tier),
  )
    .map(({ primeiro, chave: _, ...g }) => ({ tier: primeiro.tier as number, ...g }))
    .sort((a, b) => a.tier - b.tier)

  const metaMensal: MesMeta[] = res.metaMensal.map((l) => ({
    mes: String(l.mes),
    meta: n(l.meta),
    realizado: r2(n(l.realizado)),
    atingimento: r1((100 * n(l.realizado)) / n(l.meta)),
  }))

  const metasSemConfronto: MetaSemConfronto[] = res.metasSemConfronto.map((l) => ({
    funcao: String(l.funcao),
    tipo_meta: String(l.tipo_meta),
    pessoas: n(l.pessoas),
    media: n(l.media),
  }))

  const combinacoes: Combinacao[] = res.combinacoes.map((l, i) => ({
    posicao: i + 1,
    fonte: rotulo('fonte', l.fonte),
    temperatura: rotulo('temperatura', l.temperatura),
    porte: String(l.porte_empresa),
    plano: String(l.plano_interesse),
    oportunidades: n(l.oportunidades),
    contratos: n(l.contratos),
    conversao: n(l.conversao),
    icInferior: n(l.ic_inferior),
    icSuperior: n(l.ic_superior),
    ticket: nulo(l.ticket),
  }))

  const atributos: Atributo[] = ['fonte', 'temperatura', 'porte_empresa', 'plano_interesse'].map((a) => {
    const niveis = res.atributos
      .filter((l) => l.atributo === a)
      .map((l) => ({
        nivel: rotulo(a, l.nivel),
        oportunidades: n(l.oportunidades),
        contratos: n(l.contratos),
        conversao: taxa(n(l.contratos), n(l.oportunidades)),
      }))
    return { atributo: a, niveis, teste: quiQuadrado(niveis) }
  })

  const painel: Painel = {
    geradoEm: new Date().toLocaleString('pt-BR', {
      timeZone: 'America/Sao_Paulo',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).replace(',', ''),
    periodo: {
      inicio: String(t.inicio),
      fim: String(t.fim),
      origens: 3,
      campanhas: n(t.campanhas),
    },
    times: { porTime, porTier, metaMensal, pessoas, metasSemConfronto, efetivo: n(t.efetivo) },
    resumo: {
      oportunidades,
      contratos,
      conversao: taxa(contratos, oportunidades),
      investimento: r2(investimento),
      receita12m: r2(receita12m),
      contratosAtribuidos,
      receitaAtribuida: r2(receitaAtribuida),
      cac: r2(investimento / contratosAtribuidos),
      retorno: r2(receitaAtribuida / investimento),
      ticketMedio: r2(receita12m / contratos),
    },
    resposta,
    funil,
    campanhas,
    planos,
    rastreio,
    ranking,
    fila: {
      minimo: MINIMO_COMBINACAO,
      combinacoes,
      atributos,
      cobertas: combinacoes.reduce((s, c) => s + c.oportunidades, 0),
    },
  }

  return {
    painel,
    diagnostico: {
      consultas: execucoes.length,
      bytesLidos: execucoes.reduce((s, e: Execucao) => s + e.bytesLidos, 0),
      ms: Date.now() - inicio,
      ids: execucoes.map((e) => e.idConsulta),
    },
  }
}
