// Página da fila: a resposta à primeira pergunta de negócio — como ordenar o
// atendimento por chance de conversão (seção 9.2 do documento, consulta 1.b).
//
// Duas camadas de análise: o escore em si (conversão histórica por combinação de
// atributos, com intervalo de confiança de Wilson) e o teste qui-quadrado que
// mostra quais atributos de fato separam quem compra de quem não compra.

import { Barras, useDica, type ItemBarra } from './graficos'
import { Painel as Cartao, Tile } from './componentes'
import { inteiro, moeda, pct } from './formato'
import type { Combinacao, Fila, TesteQui } from './tipos'

const NOMES: Record<string, string> = {
  fonte: 'Origem do lead',
  temperatura: 'Temperatura',
  porte_empresa: 'Porte da empresa',
  plano_interesse: 'Plano de interesse',
}

const pValor = (p: number) =>
  p < 0.001 ? 'p < 0,001' : `p = ${p.toLocaleString('pt-BR', { maximumFractionDigits: 3 })}`

function leituraTeste(t: TesteQui) {
  if (t.pValor >= 0.05) return 'diferença compatível com o acaso'
  if (t.vCramer < 0.05) return 'associação real, mas fraca'
  if (t.vCramer < 0.1) return 'associação moderada'
  return 'associação forte'
}

// Intervalo de confiança desenhado como régua: o traço é o intervalo, o ponto é
// a taxa observada. Duas réguas que se sobrepõem não são distinguíveis.
function Intervalo({ c, maximo }: { c: Combinacao; maximo: number }) {
  const x = (v: number) => `${(v / maximo) * 100}%`
  return (
    <span className="regua" aria-hidden>
      <span className="regua-faixa" style={{ left: x(c.icInferior), width: x(c.icSuperior - c.icInferior) }} />
      <span className="regua-ponto" style={{ left: x(c.conversao) }} />
    </span>
  )
}

export default function PaginaFila({ fila, totalOportunidades }: { fila: Fila; totalOportunidades: number }) {
  const { combinacoes, atributos } = fila
  const { aoMover, aoSair, elemento } = useDica()
  const melhor = combinacoes[0]
  const pior = combinacoes[combinacoes.length - 1]
  const maximo = Math.max(...combinacoes.map((c) => c.icSuperior), 1)
  // Quantas combinações o topo da fila consegue, com 95% de confiança, separar
  // da média geral: o limite inferior do intervalo fica acima dela.
  const media = (100 * combinacoes.reduce((s, c) => s + c.contratos, 0)) / combinacoes.reduce((s, c) => s + c.oportunidades, 0)
  const acimaComCerteza = combinacoes.filter((c) => c.icInferior > media).length

  return (
    <>
      <dl className="tiles">
        <Tile
          titulo="Combinações no escore"
          valor={inteiro(combinacoes.length)}
          nota={`com ${fila.minimo} ou mais oportunidades`}
          cor="var(--serie-2)"
        />
        <Tile
          titulo="Funil coberto"
          valor={pct((100 * fila.cobertas) / totalOportunidades)}
          nota={`${inteiro(fila.cobertas)} oportunidades`}
          cor="var(--serie-3)"
        />
        <Tile
          titulo="Topo da fila"
          valor={pct(melhor.conversao)}
          nota={`${melhor.fonte} · ${melhor.temperatura} · ${melhor.porte}`}
          cor="var(--serie-1)"
        />
        <Tile
          titulo="Fim da fila"
          valor={pct(pior.conversao)}
          nota={`${(melhor.conversao / pior.conversao).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}× menos que o topo`}
          cor="var(--serie-5)"
        />
        <Tile
          titulo="Acima da média, com 95% de confiança"
          valor={inteiro(acimaComCerteza)}
          nota={`média do escore: ${pct(media)}`}
          cor="var(--serie-4)"
        />
      </dl>

      <Cartao
        titulo="O escore da fila"
        legenda={
          <>
            Cada oportunidade nova recebe como escore a conversão histórica da sua combinação de origem,
            temperatura, porte e plano — atributos conhecidos no momento em que ela entra. A régua é o
            intervalo de confiança de Wilson a 95%: quanto menor a combinação, mais largo o intervalo.
          </>
        }
        rodape="A ordenação organiza a fila, mas não exclui ninguém dela: toda oportunidade mantém um prazo máximo para o primeiro contato, e o critério fica aberto ao time comercial (capítulo 4 do documento)."
      >
        <div className="rolagem">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Origem</th>
                <th>Temperatura</th>
                <th>Porte</th>
                <th>Plano</th>
                <th>Oport.</th>
                <th>Contratos</th>
                <th>Conversão</th>
                <th style={{ minWidth: 180 }}>Intervalo de 95%</th>
                <th>Ticket 12m</th>
              </tr>
            </thead>
            <tbody>
              {combinacoes.map((c) => (
                <tr
                  key={c.posicao}
                  onMouseMove={aoMover(
                    <>
                      <strong>
                        {c.fonte} · {c.temperatura} · {c.porte} · {c.plano}
                      </strong>
                      <span>
                        {pct(c.conversao)}, entre {pct(c.icInferior)} e {pct(c.icSuperior)} com 95% de confiança
                      </span>
                    </>,
                  )}
                  onMouseLeave={aoSair}
                >
                  <td>{c.posicao}</td>
                  <td>{c.fonte}</td>
                  <td>{c.temperatura}</td>
                  <td>{c.porte}</td>
                  <td>{c.plano}</td>
                  <td>{inteiro(c.oportunidades)}</td>
                  <td>{inteiro(c.contratos)}</td>
                  <td>{pct(c.conversao)}</td>
                  <td>
                    <Intervalo c={c} maximo={maximo} />
                  </td>
                  <td>{c.ticket ? moeda(c.ticket) : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {elemento}
      </Cartao>

      <div className="grade">
        {atributos.map((a) => {
          const itens: ItemBarra[] = a.niveis
            .slice()
            .sort((x, y) => y.conversao - x.conversao)
            .map((n) => ({
              rotulo: n.nivel,
              valor: n.conversao,
              texto: pct(n.conversao),
              cor: 'var(--serie-2)',
              dica: (
                <>
                  <strong>{n.nivel}</strong>
                  <span>
                    {inteiro(n.oportunidades)} oportunidades · {inteiro(n.contratos)} contratos
                  </span>
                </>
              ),
            }))
          return (
            <Cartao
              key={a.atributo}
              titulo={`Conversão por ${NOMES[a.atributo].toLowerCase()}`}
              rodape={
                <>
                  Qui-quadrado de independência: χ² = {a.teste.estatistica.toLocaleString('pt-BR')} com{' '}
                  {a.teste.grausLiberdade} g.l., {pValor(a.teste.pValor)}; V de Cramér ={' '}
                  {a.teste.vCramer.toLocaleString('pt-BR')} — <strong>{leituraTeste(a.teste)}</strong>.
                  {!a.teste.valido && ' Atenção: há célula com frequência esperada abaixo de 5.'}
                </>
              }
            >
              <Barras itens={itens} larguraRotulo={120} />
            </Cartao>
          )
        })}
      </div>
    </>
  )
}
