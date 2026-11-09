// Componentes de gráfico. Dois formatos, porque o painel só precisa de dois:
// barras horizontais para comparar grandeza entre categorias, e linha para
// acompanhar uma medida no tempo. Cada marca tem alvo de interação maior que
// ela mesma e dica ao passar o mouse.
//
// As barras são HTML, não SVG: barra horizontal é largura em porcentagem, e em
// HTML o texto não distorce quando o container muda de tamanho.

import { useEffect, useRef, useState, type ReactNode } from 'react'

// --------------------------------------------------------------------- dica
type Posicao = { x: number; y: number; conteudo: ReactNode } | null

export function useDica() {
  const [dica, setDica] = useState<Posicao>(null)

  const aoMover = (conteudo: ReactNode) => (e: React.MouseEvent) =>
    setDica({ x: e.clientX, y: e.clientY, conteudo })

  const aoSair = () => setDica(null)

  const elemento = dica ? (
    <div
      className="dica"
      style={{
        left: Math.min(dica.x + 14, window.innerWidth - 220),
        top: Math.max(dica.y - 12, 8),
      }}
    >
      {dica.conteudo}
    </div>
  ) : null

  return { aoMover, aoSair, elemento }
}

// ------------------------------------------------------------------ barras
export type ItemBarra = {
  rotulo: string
  valor: number
  cor?: string
  texto: string
  dica: ReactNode
}

export function Barras({ itens, larguraRotulo = 150 }: { itens: ItemBarra[]; larguraRotulo?: number }) {
  const { aoMover, aoSair, elemento } = useDica()
  const maximo = Math.max(...itens.map((i) => i.valor), 0) || 1

  return (
    <div>
      {itens.map((item) => (
        <div
          key={item.rotulo}
          onMouseMove={aoMover(item.dica)}
          onMouseLeave={aoSair}
          style={{
            display: 'grid',
            gridTemplateColumns: `${larguraRotulo}px 1fr auto`,
            alignItems: 'center',
            gap: 12,
            padding: '5px 0',
            cursor: 'default',
          }}
        >
          <span className="rotulo" style={{ color: 'var(--tinta-2)', fontSize: 13 }}>
            {item.rotulo}
          </span>
          <span style={{ display: 'block', height: 14 }}>
            <span
              style={{
                display: 'block',
                height: '100%',
                width: `${Math.max((item.valor / maximo) * 100, 0.6)}%`,
                background: item.cor ?? 'var(--serie-1)',
                borderRadius: '2px 4px 4px 2px',
                transition: 'width 240ms ease-out',
              }}
            />
          </span>
          <span style={{ fontSize: 13, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
            {item.texto}
          </span>
        </div>
      ))}
      {elemento}
    </div>
  )
}

// -------------------------------------------------------- barras verticais
// Com linha de referência: a meta é a mesma todo mês, então ela vira uma régua
// atravessando o gráfico, e não uma segunda série repetindo o mesmo valor seis
// vezes. Menos tinta, mesma informação.
export type ColunaVertical = { rotulo: string; valor: number; texto: string; dica: ReactNode }

export function BarrasVerticais({
  colunas,
  referencia,
  formatarEixo,
}: {
  colunas: ColunaVertical[]
  referencia?: { valor: number; rotulo: string }
  formatarEixo: (v: number) => string
}) {
  const caixa = useRef<HTMLDivElement>(null)
  const [largura, setLargura] = useState(640)
  const { aoMover, aoSair, elemento } = useDica()
  const [ativo, setAtivo] = useState<number | null>(null)

  useEffect(() => {
    if (!caixa.current) return
    const observador = new ResizeObserver(([entrada]) => setLargura(entrada.contentRect.width))
    observador.observe(caixa.current)
    return () => observador.disconnect()
  }, [])

  const altura = 260
  const margem = { topo: 18, direita: 12, baixo: 42, esquerda: 68 }
  const larguraPlot = Math.max(largura - margem.esquerda - margem.direita, 10)
  const alturaPlot = altura - margem.topo - margem.baixo

  const teto = Math.max(...colunas.map((c) => c.valor), referencia?.valor ?? 0) * 1.18 || 1
  const passo = larguraPlot / colunas.length
  const larguraBarra = Math.min(passo * 0.56, 46)
  const y = (v: number) => alturaPlot - (v / teto) * alturaPlot

  return (
    <div ref={caixa}>
      <svg height={altura} role="img" aria-label="Realizado por mês">
        <g transform={`translate(${margem.esquerda},${margem.topo})`}>
          {[0, teto / 2, teto].map((m) => (
            <g key={m}>
              <line x1={0} x2={larguraPlot} y1={y(m)} y2={y(m)} stroke="var(--grade)" strokeWidth={1} />
              <text x={-10} y={y(m) + 4} textAnchor="end" className="eixo-texto">
                {formatarEixo(m)}
              </text>
            </g>
          ))}

          {colunas.map((c, i) => (
            <g key={c.rotulo}>
              <rect
                x={i * passo + (passo - larguraBarra) / 2}
                y={y(c.valor)}
                width={larguraBarra}
                height={Math.max(alturaPlot - y(c.valor), 1)}
                rx={4}
                fill="var(--serie-1)"
                opacity={ativo === null || ativo === i ? 1 : 0.55}
              />
              <text x={i * passo + passo / 2} y={y(c.valor) - 7} textAnchor="middle" className="valor">
                {c.texto}
              </text>
              <text x={i * passo + passo / 2} y={alturaPlot + 18} textAnchor="middle" className="eixo-texto">
                {c.rotulo}
              </text>
            </g>
          ))}

          {referencia && (
            <g>
              <line
                x1={0}
                x2={larguraPlot}
                y1={y(referencia.valor)}
                y2={y(referencia.valor)}
                stroke="var(--serie-2)"
                strokeWidth={2}
                strokeDasharray="6 4"
              />
              <text x={larguraPlot} y={y(referencia.valor) - 7} textAnchor="end" className="rotulo"
                    style={{ fill: 'var(--serie-2)', fontWeight: 600 }}>
                {referencia.rotulo}
              </text>
            </g>
          )}

          {colunas.map((c, i) => (
            <rect
              key={`a-${c.rotulo}`}
              className="alvo"
              x={i * passo}
              y={0}
              width={passo}
              height={alturaPlot}
              onMouseMove={(e) => {
                setAtivo(i)
                aoMover(c.dica)(e)
              }}
              onMouseLeave={() => {
                setAtivo(null)
                aoSair()
              }}
            />
          ))}
        </g>
      </svg>
      {elemento}
    </div>
  )
}

// ------------------------------------------------------------------- linha
export type PontoLinha = { rotulo: string; valor: number; dica: ReactNode }

export function Linha({ pontos, sufixo = '' }: { pontos: PontoLinha[]; sufixo?: string }) {
  const caixa = useRef<HTMLDivElement>(null)
  const [largura, setLargura] = useState(640)
  const { aoMover, aoSair, elemento } = useDica()
  const [ativo, setAtivo] = useState<number | null>(null)

  useEffect(() => {
    if (!caixa.current) return
    const observador = new ResizeObserver(([entrada]) => setLargura(entrada.contentRect.width))
    observador.observe(caixa.current)
    return () => observador.disconnect()
  }, [])

  const altura = 220
  const margem = { topo: 16, direita: 16, baixo: 28, esquerda: 44 }
  const larguraPlot = Math.max(largura - margem.esquerda - margem.direita, 10)
  const alturaPlot = altura - margem.topo - margem.baixo

  const maximo = Math.max(...pontos.map((p) => p.valor)) * 1.15 || 1
  const x = (i: number) => (pontos.length === 1 ? larguraPlot / 2 : (i / (pontos.length - 1)) * larguraPlot)
  const y = (v: number) => alturaPlot - (v / maximo) * alturaPlot

  const caminho = pontos.map((p, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(p.valor)}`).join(' ')
  const marcas = [0, maximo / 2, maximo]

  return (
    <div ref={caixa}>
      <svg height={altura} role="img" aria-label="Série temporal">
        <g transform={`translate(${margem.esquerda},${margem.topo})`}>
          {marcas.map((m) => (
            <g key={m}>
              <line x1={0} x2={larguraPlot} y1={y(m)} y2={y(m)} stroke="var(--grade)" strokeWidth={1} />
              <text x={-8} y={y(m) + 4} textAnchor="end" className="eixo-texto">
                {m.toFixed(m < 10 ? 1 : 0)}
                {sufixo}
              </text>
            </g>
          ))}

          <path d={caminho} fill="none" stroke="var(--serie-1)" strokeWidth={2} strokeLinejoin="round" />

          {pontos.map((p, i) => (
            <circle
              key={p.rotulo}
              cx={x(i)}
              cy={y(p.valor)}
              r={ativo === i ? 5.5 : 4}
              fill="var(--serie-1)"
              stroke="var(--superficie)"
              strokeWidth={2}
            />
          ))}

          {pontos.map((p, i) => (
            <text key={`r-${p.rotulo}`} x={x(i)} y={alturaPlot + 18} textAnchor="middle" className="eixo-texto">
              {p.rotulo}
            </text>
          ))}

          {pontos.map((p, i) => (
            <rect
              key={`a-${p.rotulo}`}
              className="alvo"
              x={x(i) - larguraPlot / (pontos.length * 2)}
              y={0}
              width={larguraPlot / pontos.length}
              height={alturaPlot}
              onMouseMove={(e) => {
                setAtivo(i)
                aoMover(p.dica)(e)
              }}
              onMouseLeave={() => {
                setAtivo(null)
                aoSair()
              }}
            />
          ))}
        </g>
      </svg>
      {elemento}
    </div>
  )
}
