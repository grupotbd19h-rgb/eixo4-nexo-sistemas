// Painel da Nexo Sistemas. Três páginas: aquisição, fila e times.
//
// Os números vêm do Athena, pela API do servidor (servidor/index.ts), que roda
// as consultas sobre o modelo estrela nexo_dw. Nenhum número é calculado aqui:
// o front só desenha.
//
// Se o servidor não responder — painel publicado como site estático, ou sessão
// do laboratório expirada —, o painel mostra a cópia em src/dados.json, gravada
// pelas mesmas consultas (npm run copia), e diz isso na tela em vez de quebrar.

import { useCallback, useEffect, useState } from 'react'
import PaginaAquisicao from './PaginaAquisicao'
import PaginaFila from './PaginaFila'
import PaginaTimes from './PaginaTimes'
import { inteiro, mesCurto } from './formato'
import copia from './dados.json'
import type { Painel, RespostaPainel, RespostaSaude } from './tipos'

const COPIA = copia as unknown as Painel

const PAGINAS = [
  { chave: 'aquisicao', nome: 'Aquisição' },
  { chave: 'fila', nome: 'Fila' },
  { chave: 'times', nome: 'Times' },
] as const

type Chave = (typeof PAGINAS)[number]['chave']

type Fonte =
  | { tipo: 'carregando' }
  | { tipo: 'athena'; resposta: Omit<RespostaPainel, 'painel'> }
  | { tipo: 'copia'; motivo: string; detalhe?: string }

const segundos = (ms: number) => `${(ms / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} s`
const kb = (b: number) => `${(b / 1024).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} KB`
const hora = (iso: string) => new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

// Lê JSON da API; se a resposta for a própria página (site estático sem
// servidor), trata como "sem API" em vez de tentar interpretar HTML.
async function lerApi<T>(caminho: string): Promise<{ status: number; corpo: T }> {
  const r = await fetch(caminho, { cache: 'no-store' })
  if (!(r.headers.get('content-type') ?? '').includes('application/json'))
    throw new Error('Servidor da API não encontrado — painel aberto como site estático.')
  return { status: r.status, corpo: (await r.json()) as T }
}

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

function Conexao({
  fonte,
  saude,
  testando,
  aoTestar,
  aoAtualizar,
}: {
  fonte: Fonte
  saude: RespostaSaude | null
  testando: boolean
  aoTestar: () => void
  aoAtualizar: () => void
}) {
  const classe = fonte.tipo === 'athena' ? 'ok' : fonte.tipo === 'copia' ? 'falha' : 'carregando'
  return (
    <div className={`conexao ${classe}`} role="status">
      <span className="luz" />
      {fonte.tipo === 'carregando' && <span>Consultando o Athena…</span>}
      {fonte.tipo === 'athena' && (
        <span>
          <strong>Ao vivo · Amazon Athena</strong> <span className="detalhe">({fonte.resposta.banco}, {fonte.resposta.regiao})</span>
          {' — '}
          {fonte.resposta.diagnostico.consultas} consultas em {segundos(fonte.resposta.diagnostico.ms)},{' '}
          {kb(fonte.resposta.diagnostico.bytesLidos)} lidos, às {hora(fonte.resposta.lidoEm)}
        </span>
      )}
      {fonte.tipo === 'copia' && (
        <span>
          <strong>Cópia gravada</strong> — {fonte.motivo}
          {fonte.detalhe && <span className="detalhe"> {fonte.detalhe}</span>}
        </span>
      )}
      <div className="acoes">
        <button type="button" onClick={aoTestar} disabled={testando}>
          {testando ? 'Testando…' : 'Testar conexão'}
        </button>
        <button type="button" onClick={aoAtualizar} disabled={fonte.tipo === 'carregando'}>
          Recarregar do banco
        </button>
      </div>
      {saude && (
        <dl className="teste">
          <div>
            <dt>Teste de conexão</dt>
            <dd style={{ color: saude.ok ? 'var(--positivo)' : 'var(--negativo)' }}>
              {saude.ok ? 'Conectado' : saude.motivo}
            </dd>
          </div>
          <div>
            <dt>Banco · região</dt>
            <dd>
              {saude.banco} · {saude.regiao}
            </dd>
          </div>
          <div>
            <dt>Tempo de resposta</dt>
            <dd>{segundos(saude.ms)}</dd>
          </div>
          {saude.ok ? (
            <>
              {Object.entries(saude.tabelas).map(([t, n]) => (
                <div key={t}>
                  <dt>{t}</dt>
                  <dd>{inteiro(n)} linhas</dd>
                </div>
              ))}
              <div>
                <dt>Consulta no Athena</dt>
                <dd>{saude.idConsulta}</dd>
              </div>
            </>
          ) : (
            <div style={{ gridColumn: '1 / -1' }}>
              <dt>Detalhe</dt>
              <dd style={{ fontWeight: 400 }}>{saude.detalhe}</dd>
            </div>
          )}
        </dl>
      )}
    </div>
  )
}

export default function App() {
  const [pagina, setPagina] = useState<Chave>('aquisicao')
  const [painel, setPainel] = useState<Painel>(COPIA)
  const [fonte, setFonte] = useState<Fonte>({ tipo: 'carregando' })
  const [saude, setSaude] = useState<RespostaSaude | null>(null)
  const [testando, setTestando] = useState(false)

  const carregar = useCallback(async (atualizar: boolean) => {
    setFonte({ tipo: 'carregando' })
    try {
      const { status, corpo } = await lerApi<RespostaPainel | { motivo: string; detalhe: string }>(
        `api/painel${atualizar ? '?atualizar=1' : ''}`,
      )
      if (status !== 200 || !('painel' in corpo)) {
        const falha = corpo as { motivo: string; detalhe: string }
        setFonte({ tipo: 'copia', motivo: falha.motivo, detalhe: falha.detalhe })
        return
      }
      const { painel: vivo, ...resto } = corpo
      setPainel(vivo)
      setFonte({ tipo: 'athena', resposta: resto })
    } catch (erro) {
      setFonte({ tipo: 'copia', motivo: erro instanceof Error ? erro.message : String(erro) })
    }
  }, [])

  const testar = useCallback(async () => {
    setTestando(true)
    try {
      setSaude((await lerApi<RespostaSaude>('api/saude')).corpo)
    } catch (erro) {
      setSaude({
        ok: false,
        banco: 'nexo_dw',
        regiao: '—',
        ms: 0,
        motivo: 'Sem servidor',
        detalhe: erro instanceof Error ? erro.message : String(erro),
      })
    } finally {
      setTestando(false)
    }
  }, [])

  useEffect(() => {
    void carregar(false)
  }, [carregar])

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

        <Conexao
          fonte={fonte}
          saude={saude}
          testando={testando}
          aoTestar={() => void testar()}
          aoAtualizar={() => void carregar(true)}
        />

        <Recorte periodo={painel.periodo} />

        {pagina === 'aquisicao' && <PaginaAquisicao painel={painel} />}
        {pagina === 'fila' && <PaginaFila fila={painel.fila} totalOportunidades={painel.resumo.oportunidades} />}
        {pagina === 'times' && <PaginaTimes times={painel.times} />}

        <footer>
          Dados sintéticos, gerados por <code>etapa-2/gerar_bases.py</code> com semente fixa. Os números
          são lidos no Amazon Athena, sobre o modelo estrela <code>nexo_dw</code>, pelas consultas de{' '}
          <code>etapa-5/painel/servidor/consultas.ts</code> — as mesmas definições de{' '}
          <code>etapa-3/sql/03_perguntas.sql</code>.
        </footer>
      </div>
    </>
  )
}
