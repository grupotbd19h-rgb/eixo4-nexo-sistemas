// Página dos times: quem trabalhou o funil, contra que meta, e o que dá para
// afirmar com a base que temos.
//
// Uma honestidade estrutural que a página precisa carregar: só a meta do closer
// é verificável contra o funil. A do SDR é reunião realizada, a do recuperador é
// contrato recuperado, e nenhum dos dois eventos está no modelo estrela. Mostrar
// um atingimento inventado para eles seria pior do que dizer que não dá.

import { Fragment } from 'react'
import { Barras, BarrasVerticais, type ItemBarra } from './graficos'
import { Painel as Cartao, Tile } from './componentes'
import { horas, inteiro, mesCurto, moeda, moedaCurta, pct, pct1 } from './formato'
import type { Pessoa, Times } from './tipos'

const TIPO_META: Record<string, string> = {
  reunioes_realizadas: 'reuniões realizadas por mês',
  contratos_recuperados: 'contratos recuperados por mês',
  valor_vendido_anual_time: 'valor vendido pelo time, por mês',
}

const FALTA: Record<string, string> = {
  reunioes_realizadas: 'data da reunião na oportunidade',
  contratos_recuperados: 'identificação do recuperador no fato',
  valor_vendido_anual_time: 'nada: é a soma dos closers',
}

export default function PaginaTimes({ times }: { times: Times }) {
  const { porTime, porTier, metaMensal, pessoas, metasSemConfronto, efetivo } = times

  const closers = pessoas.filter((p) => p.papel === 'Closer')
  const sdrs = pessoas.filter((p) => p.papel === 'SDR')

  const metaTotal = metaMensal.reduce((s, m) => s + m.meta, 0)
  const realizadoTotal = metaMensal.reduce((s, m) => s + m.realizado, 0)
  const atingimentoMedio = (100 * realizadoTotal) / metaTotal
  const mesesNaMeta = metaMensal.filter((m) => m.atingimento >= 100).length

  // Agrupa os closers por time, no formato da tabela de performance: linha do
  // time, pessoas recuadas abaixo dela, e um total fechando.
  const timesDoCloser = [...new Set(closers.map((c) => c.time))].sort()
  const soma = (lista: Pessoa[], campo: 'oportunidades' | 'contratos' | 'receita12m' | 'meta' | 'realizado') =>
    lista.reduce((s, p) => s + (p[campo] ?? 0), 0)

  const barrasTime: ItemBarra[] = porTime
    .slice()
    .sort((a, b) => b.conversao - a.conversao)
    .map((t) => ({
      rotulo: `${t.time} (${t.papel})`,
      valor: t.conversao,
      texto: pct(t.conversao),
      dica: (
        <>
          <strong>{t.time}</strong>
          <span>
            {t.pessoas} pessoas · {inteiro(t.oportunidades)} oportunidades
            <br />
            {inteiro(t.contratos)} contratos · {moeda(t.receita12m)}
          </span>
        </>
      ),
    }))

  const barrasTier: ItemBarra[] = porTier.map((t) => ({
    rotulo: `Tier ${t.tier}`,
    valor: t.conversao,
    texto: pct(t.conversao),
    dica: (
      <>
        <strong>Tier {t.tier}</strong>
        <span>
          {t.pessoas} closers · {inteiro(t.oportunidades)} oportunidades
          <br />
          {inteiro(t.contratos)} contratos · {moeda(t.receita12m)}
        </span>
      </>
    ),
  }))

  return (
    <>
      <dl className="tiles">
        <Tile titulo="Efetivo" valor={inteiro(efetivo)} nota="pessoas no comercial" cor="var(--serie-2)" />
        <Tile titulo="Times" valor="4" nota="frentes operacionais" cor="var(--serie-3)" />
        <Tile
          titulo="Atingimento"
          valor={pct1(atingimentoMedio)}
          nota={`${mesesNaMeta} de ${metaMensal.length} meses na meta`}
          cor="var(--serie-1)"
        />
        <Tile titulo="Realizado" valor={moeda(realizadoTotal)} nota="contratos de 12 meses" cor="var(--serie-5)" />
        <Tile titulo="Meta do semestre" valor={moeda(metaTotal)} nota="soma das metas mensais" cor="var(--serie-4)" />
      </dl>

      <Cartao
        titulo="Realizado contra a meta, mês a mês"
        legenda="Soma dos contratos de 12 meses fechados pelos closers em cada mês. A meta é a mesma todos os meses — por isso aparece como régua, e não como segunda barra."
        rodape={`O time fechou ${pct1(atingimentoMedio)} da meta do semestre e bateu em ${mesesNaMeta} dos ${metaMensal.length} meses. Março, primeiro mês do recorte, é o mais fraco: parte dos contratos do mês veio de oportunidades criadas antes do período, que a base não cobre.`}
      >
        <BarrasVerticais
          formatarEixo={moedaCurta}
          referencia={{ valor: metaMensal[0]?.meta ?? 0, rotulo: `meta ${moeda(metaMensal[0]?.meta ?? 0)}` }}
          colunas={metaMensal.map((m) => ({
            rotulo: mesCurto(m.mes),
            valor: m.realizado,
            texto: pct1(m.atingimento),
            dica: (
              <>
                <strong>{mesCurto(m.mes)}</strong>
                <span>
                  realizado {moeda(m.realizado)}
                  <br />
                  meta {moeda(m.meta)} · atingimento {pct1(m.atingimento)}
                </span>
              </>
            ),
          }))}
        />
      </Cartao>

      <div className="grade">
        <Cartao
          titulo="Conversão por time"
          legenda="Atenção ao denominador: o SDR vê toda oportunidade que entra, o closer só as que foram repassadas. Os números não são comparáveis entre as duas funções."
        >
          <Barras itens={barrasTime} larguraRotulo={190} />
        </Cartao>

        <Cartao
          titulo="Conversão por tier do closer"
          legenda="O tier define a faixa de comissão. Se ele não separa desempenho, é critério de remuneração sem lastro no resultado."
          rodape={`As três faixas ficam entre ${pct(Math.min(...porTier.map((t) => t.conversao)))} e ${pct(Math.max(...porTier.map((t) => t.conversao)))}. A diferença é pequena demais para sustentar, sozinha, a hierarquia de comissão.`}
        >
          <Barras itens={barrasTier} larguraRotulo={80} />
        </Cartao>
      </div>

      <Cartao
        titulo="Performance por time"
        legenda="Meta e realizado somados nos seis meses. Atingimento é realizado dividido por meta."
      >
        <div className="rolagem">
          <table>
            <thead>
              <tr>
                <th>Time / closer</th>
                <th>Tier</th>
                <th>Oport.</th>
                <th>Contratos</th>
                <th>Conversão</th>
                <th>Meta</th>
                <th>Realizado</th>
                <th>Atingimento</th>
              </tr>
            </thead>
            <tbody>
              {timesDoCloser.map((time) => {
                const membros = closers
                  .filter((c) => c.time === time)
                  .sort((a, b) => b.receita12m - a.receita12m)
                const meta = soma(membros, 'meta')
                const realizado = soma(membros, 'realizado')
                const oport = soma(membros, 'oportunidades')
                const contratos = soma(membros, 'contratos')
                return (
                  <Fragment key={time}>
                    <tr className="grupo">
                      <td>
                        {time} ({membros.length})
                      </td>
                      <td />
                      <td>{inteiro(oport)}</td>
                      <td>{inteiro(contratos)}</td>
                      <td>{pct((100 * contratos) / oport)}</td>
                      <td>{moeda(meta)}</td>
                      <td>{moeda(realizado)}</td>
                      <td>{pct1((100 * realizado) / meta)}</td>
                    </tr>
                    {membros.map((p) => (
                      <tr className="membro" key={p.id_colaborador}>
                        <td>{p.id_colaborador}</td>
                        <td>{p.tier ?? '—'}</td>
                        <td>{inteiro(p.oportunidades)}</td>
                        <td>{inteiro(p.contratos)}</td>
                        <td>{pct(p.conversao)}</td>
                        <td>{p.meta ? moeda(p.meta) : '—'}</td>
                        <td>{p.realizado ? moeda(p.realizado) : '—'}</td>
                        <td className={(p.atingimento ?? 0) >= 100 ? 'acima' : 'abaixo'}>
                          {p.atingimento !== null ? pct1(p.atingimento) : '—'}
                        </td>
                      </tr>
                    ))}
                  </Fragment>
                )
              })}
              <tr className="total">
                <td>Total</td>
                <td />
                <td>{inteiro(soma(closers, 'oportunidades'))}</td>
                <td>{inteiro(soma(closers, 'contratos'))}</td>
                <td>{pct((100 * soma(closers, 'contratos')) / soma(closers, 'oportunidades'))}</td>
                <td>{moeda(metaTotal)}</td>
                <td>{moeda(realizadoTotal)}</td>
                <td>{pct1(atingimentoMedio)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Cartao>

      <div className="grade-larga">
        <Cartao
          titulo="Pré-vendas"
          legenda="A meta do SDR é reunião realizada, e o modelo estrela não guarda a data da reunião. O que dá para medir é o que mais pesa na conversão: a mediana de horas até o primeiro contato."
        >
          <div className="rolagem">
            <table>
              <thead>
                <tr>
                  <th>SDR</th>
                  <th>Tier</th>
                  <th>Oport.</th>
                  <th>Contratos na ponta</th>
                  <th>Conversão</th>
                  <th>Mediana até 1º contato</th>
                </tr>
              </thead>
              <tbody>
                {sdrs
                  .slice()
                  .sort((a, b) => (a.medianaHoras ?? 0) - (b.medianaHoras ?? 0))
                  .map((p) => (
                    <tr key={p.id_colaborador}>
                      <td>{p.id_colaborador}</td>
                      <td>{p.tier ?? '—'}</td>
                      <td>{inteiro(p.oportunidades)}</td>
                      <td>{inteiro(p.contratos)}</td>
                      <td>{pct(p.conversao)}</td>
                      <td>{horas(p.medianaHoras)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </Cartao>

        <Cartao
          titulo="Metas que a base não fecha"
          legenda="Estas metas existem no sistema de remuneração, mas o evento que as comprova não está no modelo estrela. Fica registrado como limitação, e não disfarçado com um número aproximado."
          rodape="Resolver as duas é barato: basta levar a data da reunião e o identificador do recuperador da camada bruta para o fato de oportunidade."
        >
          <div className="rolagem">
            <table>
              <thead>
                <tr>
                  <th>Função</th>
                  <th>Meta mensal</th>
                  <th>Pessoas</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                {metasSemConfronto.map((m) => (
                  <tr key={m.tipo_meta}>
                    <td>{m.funcao}</td>
                    <td style={{ textAlign: 'left' }}>{TIPO_META[m.tipo_meta] ?? m.tipo_meta}</td>
                    <td>{m.pessoas}</td>
                    <td>{m.media >= 1000 ? moeda(m.media) : inteiro(m.media)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="legenda" style={{ marginTop: 12, marginBottom: 0 }}>
              Falta registrar: {FALTA.reunioes_realizadas} (SDR) e {FALTA.contratos_recuperados}{' '}
              (recuperador). A do gestor {FALTA.valor_vendido_anual_time}.
            </p>
          </div>
        </Cartao>
      </div>
    </>
  )
}
