// Formatação em português do Brasil, num lugar só: se o padrão mudar, muda aqui.

export const moeda = (v: number) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 })

export const moedaCurta = (v: number) =>
  v >= 1000 ? `${(v / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} mil` : moeda(v)

export const inteiro = (v: number) => v.toLocaleString('pt-BR')

export const pct = (v: number) =>
  `${v.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`

export const pct1 = (v: number) => `${v.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`

export const horas = (v: number | null) => (v === null ? '—' : `${v.toLocaleString('pt-BR')} h`)

export const mesCurto = (iso: string) => {
  const nomes = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
  const [ano, mes] = iso.split('-')
  return `${nomes[Number(mes) - 1]}/${ano.slice(2)}`
}
