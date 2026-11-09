// Espelha o JSON produzido por etapa-5/exportar_painel.py a partir do modelo
// estrela. Se o exportador mudar, o TypeScript acusa aqui, no build.

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
}
