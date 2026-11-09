// Página de aquisição: o funil e o custo de conquistar um cliente — as duas
// perguntas de negócio registradas no capítulo 3 do documento.

import { Barras, Linha, type ItemBarra } from './graficos'
import { Painel as Cartao, Tile } from './componentes'
import { inteiro, mesCurto, moeda, pct } from './formato'
import type { Painel } from './tipos'

const SINTETICAS = ['SEM_UTM', 'UTM_QUEBRADA']

export default function PaginaAquisicao({ painel }: { painel: Painel }) {
  const { resumo, resposta, funil, campanhas, planos, rastreio, ranking } = painel

  const atribuidas = campanhas.filter((c) => !SINTETICAS.includes(c.id_campanha))
  const totalOportunidades = rastreio.reduce((s, r) => s + r.oportunidades, 0)
  const perdidas = rastreio
    .filter((r) => r.situacao !== 'Atribuída a campanha')
    .reduce((s, r) => s + r.oportunidades, 0)

  const totalCampanhas = campanhas.reduce(
    (acc, c) => ({
      investimento: acc.investimento + c.investimento,
      oportunidades: acc.oportunidades + c.oportunidades,
      contratos: acc.contratos + c.contratos,
      receita12m: acc.receita12m + c.receita12m,
    }),
    { investimento: 0, oportunidades: 0, contratos: 0, receita12m: 0 },
  )

  const barrasResposta: ItemBarra[] = resposta.map((r) => ({
    rotulo: r.faixa,
    valor: r.conversao,
    texto: pct(r.conversao),
    dica: (
      <>
        <strong>{r.faixa}</strong>
        <span>
          {inteiro(r.oportunidades)} oportunidades · {inteiro(r.contratos)} contratos
        </span>
      </>
    ),
  }))

  const barrasCac: ItemBarra[] = atribuidas
    .slice()
    .sort((a, b) => (b.cac ?? 0) - (a.cac ?? 0))
    .map((c) => ({
      rotulo: c.nome_campanha,
      valor: c.cac ?? 0,
      texto: moeda(c.cac ?? 0),
      dica: (
        <>
          <strong>{c.nome_campanha}</strong>
          <span>
            {moeda(c.investimento)} investidos · {inteiro(c.contratos)} contratos
            <br />
            retorno de {c.retorno?.toLocaleString('pt-BR')}× em 12 meses
          </span>
        </>
      ),
    }))

  const barrasPlano: ItemBarra[] = planos
    .slice()
    .sort((a, b) => b.cac - a.cac)
    .map((p) => ({
      rotulo: p.plano,
      valor: p.cac,
      texto: moeda(p.cac),
      dica: (
        <>
          <strong>Plano {p.plano}</strong>
          <span>
            {inteiro(p.contratos)} contratos · {moeda(p.investimento)} rateados
          </span>
        </>
      ),
    }))

  const cores = ['var(--serie-2)', 'var(--serie-1)', 'var(--serie-5)']
  const barrasRastreio: ItemBarra[] = rastreio.map((r, i) => ({
    rotulo: r.situacao,
    valor: r.oportunidades,
    cor: cores[i],
    texto: inteiro(r.oportunidades),
    dica: (
      <>
        <strong>{r.situacao}</strong>
        <span>
          {inteiro(r.contratos)} contratos ·{' '}
          {((100 * r.oportunidades) / totalOportunidades).toFixed(1)}% do funil
        </span>
      </>
    ),
  }))

  return (
    <>
      <dl className="tiles">
        <Tile titulo="Oportunidades" valor={inteiro(resumo.oportunidades)} cor="var(--serie-2)" />
        <Tile
          titulo="Contratos"
          valor={inteiro(resumo.contratos)}
          nota={`${pct(resumo.conversao)} de conversão`}
          cor="var(--serie-3)"
        />
        <Tile
          titulo="Investimento"
          valor={moeda(resumo.investimento)}
          nota="Meta Ads, 6 meses"
          cor="var(--serie-1)"
        />
        <Tile
          titulo="Custo de aquisição"
          valor={moeda(resumo.cac)}
          nota={`sobre ${inteiro(resumo.contratosAtribuidos)} contratos com campanha`}
          cor="var(--serie-5)"
        />
        <Tile
          titulo="Receita 12 meses"
          valor={moeda(resumo.receita12m)}
          nota={`${resumo.retorno}× sobre o investimento rastreado`}
          cor="var(--serie-4)"
        />
        <Tile
          titulo="Ticket médio"
          valor={moeda(resumo.ticketMedio)}
          nota="contrato de 12 meses"
          cor="var(--serie-3)"
        />
      </dl>

      <div className="grade-larga">
        <Cartao
          titulo="Conversão por tempo de resposta"
          legenda="Percentual de oportunidades que viraram contrato, por tempo até o primeiro contato."
          rodape="É o achado que sustenta a priorização da fila: responder na primeira hora converte três vezes mais do que responder depois de três dias."
        >
          <Barras itens={barrasResposta} larguraRotulo={120} />
        </Cartao>

        <Cartao
          titulo="Custo de aquisição por campanha"
          legenda="Apenas as campanhas com investimento identificado. Quanto menor a barra, mais barato o contrato."
        >
          <Barras itens={barrasCac} larguraRotulo={210} />
        </Cartao>
      </div>

      <div className="grade">
        <Cartao
          titulo="Conversão mês a mês"
          legenda="Percentual de oportunidades criadas no mês que fecharam contrato."
          rodape="A queda no último mês é coorte incompleta, não piora de desempenho: uma oportunidade criada em agosto ainda estava em negociação quando a base termina. Só os meses com o ciclo de venda inteiro cumprido são comparáveis entre si."
        >
          <Linha
            sufixo="%"
            pontos={funil.map((m) => ({
              rotulo: mesCurto(m.mes),
              valor: m.conversao,
              dica: (
                <>
                  <strong>{mesCurto(m.mes)}</strong>
                  <span>
                    {inteiro(m.oportunidades)} oportunidades · {inteiro(m.contratos)} contratos
                    <br />
                    {moeda(m.receita12m)} em receita de 12 meses
                  </span>
                </>
              ),
            }))}
          />
        </Cartao>

        <Cartao
          titulo="Custo de aquisição por plano"
          legenda="Investimento de cada campanha rateado entre os planos que ela fechou, na proporção dos contratos."
          rodape={`Os três planos custam quase o mesmo para conquistar — de ${moeda(
            Math.min(...planos.map((p) => p.cac)),
          )} a ${moeda(
            Math.max(...planos.map((p) => p.cac)),
          )} — mas rendem de forma muito diferente: a mensalidade do Corporativo é cinco vezes a do Essencial. É o argumento para deslocar investimento para o topo da tabela de planos.`}
        >
          <Barras itens={barrasPlano} larguraRotulo={110} />
        </Cartao>
      </div>

      <Cartao
        titulo="Desempenho por campanha"
        legenda="As duas últimas linhas são o funil que nenhum investimento explica — elas entram no total de propósito."
      >
        <div className="rolagem">
          <table>
            <thead>
              <tr>
                <th>Campanha</th>
                <th>Objetivo</th>
                <th>Investimento</th>
                <th>Oportunidades</th>
                <th>Contratos</th>
                <th>CAC</th>
                <th>Receita 12m</th>
                <th>Retorno</th>
              </tr>
            </thead>
            <tbody>
              {campanhas
                .slice()
                .sort((a, b) => b.investimento - a.investimento)
                .map((c) => (
                  <tr key={c.id_campanha} className={SINTETICAS.includes(c.id_campanha) ? 'sintetica' : undefined}>
                    <td>{c.nome_campanha}</td>
                    <td>{c.objetivo}</td>
                    <td>{c.investimento > 0 ? moeda(c.investimento) : '—'}</td>
                    <td>{inteiro(c.oportunidades)}</td>
                    <td>{inteiro(c.contratos)}</td>
                    <td>{c.cac ? moeda(c.cac) : '—'}</td>
                    <td>{moeda(c.receita12m)}</td>
                    <td>{c.retorno ? `${c.retorno}×` : '—'}</td>
                  </tr>
                ))}
              <tr className="total">
                <td>Total</td>
                <td />
                <td>{moeda(totalCampanhas.investimento)}</td>
                <td>{inteiro(totalCampanhas.oportunidades)}</td>
                <td>{inteiro(totalCampanhas.contratos)}</td>
                <td>{moeda(resumo.cac)}</td>
                <td>{moeda(totalCampanhas.receita12m)}</td>
                <td>{resumo.retorno}×</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Cartao>

      <div className="grade">
        <Cartao
          titulo="O custo de não ter rastreio"
          legenda={`${inteiro(perdidas)} oportunidades — ${((100 * perdidas) / totalOportunidades).toFixed(1)}% do funil — chegaram sem identificação de campanha: ou a UTM veio vazia, ou a plataforma não substituiu o marcador.`}
        >
          <div className="legendas">
            {rastreio.map((r, i) => (
              <span key={r.situacao}>
                <i style={{ background: cores[i] }} />
                {r.situacao}
              </span>
            ))}
          </div>
          <Barras itens={barrasRastreio} larguraRotulo={170} />
        </Cartao>

        <Cartao titulo="Dez maiores closers por receita" legenda="Contratos de 12 meses fechados no período.">
          <div className="rolagem">
            <table>
              <thead>
                <tr>
                  <th>Closer</th>
                  <th>Time</th>
                  <th>Oport.</th>
                  <th>Contratos</th>
                  <th>Conversão</th>
                  <th>Receita 12m</th>
                </tr>
              </thead>
              <tbody>
                {ranking.map((c) => (
                  <tr key={c.id_colaborador}>
                    <td>{c.id_colaborador}</td>
                    <td>{c.time}</td>
                    <td>{inteiro(c.oportunidades)}</td>
                    <td>{inteiro(c.contratos)}</td>
                    <td>{pct(c.conversao)}</td>
                    <td>{moeda(c.receita12m)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Cartao>
      </div>
    </>
  )
}
