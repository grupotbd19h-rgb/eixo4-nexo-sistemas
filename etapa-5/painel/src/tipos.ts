// Contrato entre o servidor (servidor/consultas.ts, que lê o Athena) e o front.
// Os dois lados importam este arquivo: se um mudar, o TypeScript acusa no outro.

export type Resumo = {
  oportunidades: number
  contratos: number
  conversao: number
  investimento: number
  receita12m: number
  contratosAtribuidos: number
  receitaAtribuida: number
  cac: number
  retorno: number
  ticketMedio: number
}

export type FaixaResposta = {
  faixa: string
  oportunidades: number
  contratos: number
  conversao: number
}

export type MesFunil = {
  mes: string
  oportunidades: number
  contratos: number
  conversao: number
  receita12m: number
}

export type Campanha = {
  id_campanha: string
  nome_campanha: string
  objetivo: string
  oportunidades: number
  contratos: number
  receita12m: number
  investimento: number
  cac: number | null
  retorno: number | null
}

export type Plano = {
  plano: string
  contratos: number
  investimento: number
  cac: number
}

export type Rastreio = {
  situacao: string
  oportunidades: number
  contratos: number
}

export type Closer = {
  id_colaborador: string
  time: string
  tier: number
  oportunidades: number
  contratos: number
  receita12m: number
  conversao: number
}

export type TimePapel = {
  time: string
  papel: string
  pessoas: number
  oportunidades: number
  contratos: number
  receita12m: number
  conversao: number
}

export type Tier = {
  tier: number
  pessoas: number
  oportunidades: number
  contratos: number
  receita12m: number
  conversao: number
}

export type MesMeta = {
  mes: string
  meta: number
  realizado: number
  atingimento: number
}

export type Pessoa = {
  id_colaborador: string
  papel: string
  funcao: string
  time: string
  tier: number | null
  oportunidades: number
  contratos: number
  receita12m: number
  conversao: number
  medianaHoras: number | null
  meta: number | null
  realizado: number | null
  atingimento: number | null
}

export type MetaSemConfronto = {
  funcao: string
  tipo_meta: string
  pessoas: number
  media: number
}

export type Times = {
  porTime: TimePapel[]
  porTier: Tier[]
  metaMensal: MesMeta[]
  pessoas: Pessoa[]
  metasSemConfronto: MetaSemConfronto[]
  efetivo: number
}

export type Periodo = {
  inicio: string
  fim: string
  origens: number
  campanhas: number
}

// --- fila de atendimento (pergunta 1) -----------------------------------------

export type Combinacao = {
  posicao: number
  fonte: string
  temperatura: string
  porte: string
  plano: string
  oportunidades: number
  contratos: number
  conversao: number
  icInferior: number
  icSuperior: number
  ticket: number | null
}

export type TesteQui = {
  estatistica: number
  grausLiberdade: number
  pValor: number
  vCramer: number
  valido: boolean
}

export type NivelAtributo = {
  nivel: string
  oportunidades: number
  contratos: number
  conversao: number
}

export type Atributo = {
  atributo: string
  niveis: NivelAtributo[]
  teste: TesteQui
}

export type Fila = {
  minimo: number
  combinacoes: Combinacao[]
  atributos: Atributo[]
  cobertas: number
}

// --- resposta da API ------------------------------------------------------------

export type RespostaPainel = {
  origem: 'athena'
  banco: string
  regiao: string
  lidoEm: string
  diagnostico: { consultas: number; bytesLidos: number; ms: number; ids: string[] }
  painel: Painel
}

export type RespostaSaude =
  | {
      ok: true
      banco: string
      regiao: string
      tabelas: Record<string, number>
      ms: number
      bytesLidos: number
      idConsulta: string
      quando: string
    }
  | { ok: false; banco: string; regiao: string; ms: number; motivo: string; detalhe: string }

export type Painel = {
  geradoEm: string
  periodo: Periodo
  times: Times
  resumo: Resumo
  resposta: FaixaResposta[]
  funil: MesFunil[]
  campanhas: Campanha[]
  planos: Plano[]
  rastreio: Rastreio[]
  ranking: Closer[]
  fila: Fila
}
