// Teste qui-quadrado de independência entre um atributo da oportunidade e o
// resultado (ganha ou não). Responde: a diferença de conversão entre os níveis
// do atributo é maior do que o acaso explicaria?
//
// Tabela k × 2 (níveis × ganha/perdida). Graus de liberdade = k − 1.
// O V de Cramér mede o tamanho do efeito, que o p-valor sozinho não mostra:
// com 19 mil linhas, quase qualquer diferença vira "significativa".

import type { TesteQui } from '../src/tipos'

type Nivel = { oportunidades: number; contratos: number }

export function quiQuadrado(niveis: Nivel[]): TesteQui {
  const total = niveis.reduce((s, l) => s + l.oportunidades, 0)
  const ganhas = niveis.reduce((s, l) => s + l.contratos, 0)
  const perdidas = total - ganhas
  let estatistica = 0
  let menorEsperado = Infinity
  for (const l of niveis) {
    const esperadoG = (l.oportunidades * ganhas) / total
    const esperadoP = (l.oportunidades * perdidas) / total
    menorEsperado = Math.min(menorEsperado, esperadoG, esperadoP)
    if (esperadoG > 0) estatistica += (l.contratos - esperadoG) ** 2 / esperadoG
    if (esperadoP > 0) estatistica += (l.oportunidades - l.contratos - esperadoP) ** 2 / esperadoP
  }
  const gl = niveis.length - 1
  return {
    estatistica: Math.round(estatistica * 100) / 100,
    grausLiberdade: gl,
    pValor: gl > 0 ? gamaSuperiorRegularizada(gl / 2, estatistica / 2) : 1,
    vCramer: Math.round(Math.sqrt(estatistica / total) * 1000) / 1000,
    // a aproximação do qui-quadrado exige frequência esperada de pelo menos 5 por célula
    valido: menorEsperado >= 5,
  }
}

// Q(a, x) = Γ(a, x) / Γ(a): a cauda superior da qui-quadrado com 2a graus de
// liberdade em 2x. Série para x < a + 1, fração continuada no resto
// (Press et al., Numerical Recipes, cap. 6.2).
function gamaSuperiorRegularizada(a: number, x: number): number {
  if (x <= 0) return 1
  const lnGamaA = lnGama(a)
  if (x < a + 1) {
    let soma = 1 / a
    let termo = soma
    for (let n = 1; n < 500; n++) {
      termo *= x / (a + n)
      soma += termo
      if (Math.abs(termo) < Math.abs(soma) * 1e-15) break
    }
    return 1 - soma * Math.exp(-x + a * Math.log(x) - lnGamaA)
  }
  const minimo = 1e-300
  let b = x + 1 - a
  let c = 1 / minimo
  let d = 1 / b
  let h = d
  for (let i = 1; i < 500; i++) {
    const an = -i * (i - a)
    b += 2
    d = an * d + b
    if (Math.abs(d) < minimo) d = minimo
    c = b + an / c
    if (Math.abs(c) < minimo) c = minimo
    d = 1 / d
    const delta = d * c
    h *= delta
    if (Math.abs(delta - 1) < 1e-15) break
  }
  return Math.exp(-x + a * Math.log(x) - lnGamaA) * h
}

// Aproximação de Lanczos para ln Γ(z).
function lnGama(z: number): number {
  const g = 7
  const c = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
    1.5056327351493116e-7,
  ]
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - lnGama(1 - z)
  z -= 1
  let x = c[0]
  for (let i = 1; i < g + 2; i++) x += c[i] / (z + i)
  const t = z + g + 0.5
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x)
}
