// Servidor do painel: entrega a página (dist/) e a API que consulta o Athena.
//
//    npm run build      — gera dist/
//    npm run servidor   — sobe em http://localhost:8787
//
// Rotas:
//    GET /api/saude                 teste de conexão: conta as linhas das tabelas do nexo_dw
//    GET /api/painel[?atualizar=1]  todos os conjuntos do painel, lidos no Athena
//
// O navegador nunca fala com a AWS: as credenciais ficam só aqui, no servidor.
// O resultado do painel fica em memória por 10 minutos — o dado só muda quando
// o pipeline da Etapa 3 roda de novo, e cada leitura no Athena é cobrada.

import { createServer, type ServerResponse } from 'node:http'
import { readFile } from 'node:fs/promises'
import { extname, join, normalize } from 'node:path'
import { fileURLToPath } from 'node:url'
import { BANCO, REGIAO, consultar } from './athena'
import { SQL, montarPainel } from './consultas'

const PORTA = Number(process.env.PORT ?? 8787)
// PAINEL_DIST permite servir um build gravado em outra pasta (útil quando o
// Windows bloqueia o node.exe de gravar dentro de Documentos).
const DIST = process.env.PAINEL_DIST
  ? join(process.env.PAINEL_DIST, '/')
  : fileURLToPath(new URL('../dist/', import.meta.url))
const VALIDADE_MS = 10 * 60 * 1000

let cache: { quando: number; corpo: string } | null = null
let emAndamento: Promise<string> | null = null

function json(res: ServerResponse, status: number, corpo: unknown) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' })
  res.end(typeof corpo === 'string' ? corpo : JSON.stringify(corpo))
}

// A mensagem que o painel mostra quando a conexão falha: o motivo mais comum
// no laboratório é a sessão expirada, e isso tem solução conhecida.
function explicar(erro: unknown) {
  const texto = erro instanceof Error ? erro.message : String(erro)
  const nome = erro instanceof Error ? erro.name : ''
  if (/ExpiredToken|expired/i.test(nome + texto))
    return { motivo: 'Credenciais do laboratório expiradas', detalhe: 'Renove ~/.aws/credentials com os dados de AWS Details no Learner Lab.' }
  if (/Could not load credentials|CredentialsProviderError/i.test(nome + texto))
    return { motivo: 'Credenciais da AWS não encontradas', detalhe: 'Grave as credenciais do Learner Lab em ~/.aws/credentials.' }
  if (/ENOTFOUND|EAI_AGAIN|ECONNREFUSED|ETIMEDOUT/i.test(texto))
    return { motivo: 'Sem acesso à rede', detalhe: texto }
  return { motivo: 'O Athena recusou a consulta', detalhe: texto }
}

async function saude(res: ServerResponse) {
  const inicio = Date.now()
  try {
    const e = await consultar(SQL.saude)
    const l = e.linhas[0]
    json(res, 200, {
      ok: true,
      banco: BANCO,
      regiao: REGIAO,
      tabelas: {
        fato_oportunidade: l.oportunidades,
        fato_investimento_anuncio: l.investimentos,
        fato_meta_vendedor: l.metas,
        dim_colaborador: l.colaboradores,
      },
      ms: Date.now() - inicio,
      bytesLidos: e.bytesLidos,
      idConsulta: e.idConsulta,
      quando: new Date().toISOString(),
    })
  } catch (erro) {
    json(res, 503, { ok: false, banco: BANCO, regiao: REGIAO, ms: Date.now() - inicio, ...explicar(erro) })
  }
}

async function painel(res: ServerResponse, atualizar: boolean) {
  if (!atualizar && cache && Date.now() - cache.quando < VALIDADE_MS) return json(res, 200, cache.corpo)
  try {
    // Pedidos simultâneos compartilham a mesma leitura, em vez de disparar várias.
    emAndamento ??= montarPainel().then(({ painel, diagnostico }) =>
      JSON.stringify({ origem: 'athena', banco: BANCO, regiao: REGIAO, lidoEm: new Date().toISOString(), diagnostico, painel }),
    )
    const corpo = await emAndamento
    cache = { quando: Date.now(), corpo }
    json(res, 200, corpo)
  } catch (erro) {
    console.error(erro)
    json(res, 503, { origem: 'erro', ...explicar(erro) })
  } finally {
    emAndamento = null
  }
}

const TIPOS: Record<string, string> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.json': 'application/json; charset=utf-8',
  '.ico': 'image/x-icon',
}

async function estatico(res: ServerResponse, caminho: string) {
  const relativo = normalize(decodeURIComponent(caminho)).replace(/^([/\\])+/, '') || 'index.html'
  const alvo = join(DIST, relativo)
  if (!alvo.startsWith(DIST)) return json(res, 403, { erro: 'caminho inválido' })
  try {
    const conteudo = await readFile(alvo)
    res.writeHead(200, { 'Content-Type': TIPOS[extname(alvo)] ?? 'application/octet-stream' })
    res.end(conteudo)
  } catch {
    try {
      res.writeHead(200, { 'Content-Type': TIPOS['.html'] })
      res.end(await readFile(join(DIST, 'index.html')))
    } catch {
      json(res, 404, { erro: 'dist/ não encontrado — rode npm run build antes' })
    }
  }
}

createServer((req, res) => {
  const url = new URL(req.url ?? '/', 'http://localhost')
  if (req.method !== 'GET') return json(res, 405, { erro: 'só GET' })
  if (url.pathname === '/api/saude') return void saude(res)
  if (url.pathname === '/api/painel') return void painel(res, url.searchParams.has('atualizar'))
  return void estatico(res, url.pathname)
}).listen(PORTA, () => {
  console.log(`Painel em http://localhost:${PORTA}  ·  Athena ${BANCO} (${REGIAO})`)
})
