// Painel da Nexo Sistemas. Duas páginas: aquisição e times.
//
// Nenhum número é calculado aqui: tudo vem de src/dados.json, que o exportador
// gera a partir do mesmo modelo estrela que o Athena consulta. É o que garante
// que o gráfico e a consulta SQL contem a mesma história.

import { useState } from 'react'
import PaginaAquisicao from './PaginaAquisicao'
import PaginaTimes from './PaginaTimes'
import { mesCurto } from './formato'
import dados from './dados.json'
import type { Painel } from './tipos'

const painel = dados as unknown as Painel

const PAGINAS = [
  { chave: 'aquisicao', nome: 'Aquisição' },
  { chave: 'times', nome: 'Times' },
] as const

type Chave = (typeof PAGINAS)[number]['chave']

// O recorte é fixo: a base é sintética e a janela está fechada. Em vez de
// desenhar seletores que não filtram nada, o recorte aparece como fato.
function Recorte({ periodo }: { periodo: Painel['periodo'] }) {
  const campos = [
    { rotulo: 'Período', valor: `${mesCurto(periodo.inicio.slice(0, 7))} — ${mesCurto(periodo.fim.slice(0, 7))}` },
    { rotulo: 'Origens', valor: 'CRM · Meta Ads · Planilhas' },
    { rotulo: 'Campanhas', valor: String(periodo.campanhas) },
    { rotulo: 'Moeda', valor: 'BRL' },
  ]
  return (
    <div className="filtros">
      {campos.map((c) => (
        <div key={c.rotulo}>
          <label>{c.rotulo}</label>
          <div className="campo">{c.valor}</div>
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [pagina, setPagina] = useState<Chave>('aquisicao')

  return (
    <>
      <div className="barra-topo">
        <div className="trilha">
          <span>Painéis</span>
          <span>/</span>
          <strong>Comercial</strong>
        </div>
        <div className="quem">Nexo Sistemas · dados sintéticos</div>
      </div>

      <div className="pagina">
        <div className="cabecalho">
          <h1>Comercial</h1>
          <nav className="abas" aria-label="Seções do painel">
            {PAGINAS.map((p) => (
              <button
                key={p.chave}
                type="button"
                className={pagina === p.chave ? 'ativa' : undefined}
                aria-current={pagina === p.chave ? 'page' : undefined}
                onClick={() => setPagina(p.chave)}
              >
                {p.nome}
              </button>
            ))}
          </nav>
          <div className="carimbo">
            Atualização
            <strong>{painel.geradoEm}</strong>
          </div>
        </div>

        <Recorte periodo={painel.periodo} />

        {pagina === 'aquisicao' ? <PaginaAquisicao painel={painel} /> : <PaginaTimes times={painel.times} />}

        <footer>
          Dados sintéticos, gerados por <code>etapa-2/gerar_bases.py</code> com semente fixa. O conjunto
          que alimenta este painel é produzido por <code>etapa-5/exportar_painel.py</code> a partir do
          modelo estrela — as mesmas tabelas consultadas pelo Athena.
        </footer>
      </div>
    </>
  )
}
