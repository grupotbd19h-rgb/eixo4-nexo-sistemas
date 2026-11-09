// Peças de interface compartilhadas entre as páginas.

import type { ReactNode } from 'react'

// A cor da borda identifica o indicador e não muda de um render para outro:
// é rótulo, não classificação. Por isso ela vem declarada em cada chamada.
export function Tile({
  titulo,
  valor,
  nota,
  cor = 'var(--serie-1)',
}: {
  titulo: string
  valor: string
  nota?: string
  cor?: string
}) {
  return (
    <div className="tile" style={{ borderLeftColor: cor }}>
      <dt>{titulo}</dt>
      <dd>
        {valor}
        {nota && <span className="nota">{nota}</span>}
      </dd>
    </div>
  )
}

export function Painel({
  titulo,
  legenda,
  children,
  rodape,
}: {
  titulo: string
  legenda?: ReactNode
  children: ReactNode
  rodape?: ReactNode
}) {
  return (
    <section className="painel">
      <h2>{titulo}</h2>
      {legenda && <p className="legenda">{legenda}</p>}
      <div className="corpo">{children}</div>
      {rodape && (
        <p className="legenda" style={{ marginTop: 14, marginBottom: 0 }}>
          {rodape}
        </p>
      )}
    </section>
  )
}
