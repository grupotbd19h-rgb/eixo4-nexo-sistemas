// Conexão com o Amazon Athena: executa uma consulta SQL sobre o modelo estrela
// e devolve as linhas já com os tipos convertidos.
//
// Credenciais: as do laboratório, em ~/.aws/credentials, renovadas a cada sessão
// do Learner Lab. O SDK as encontra sozinho; nada de chave no código nem no front.

import {
  AthenaClient,
  GetQueryExecutionCommand,
  GetQueryResultsCommand,
  StartQueryExecutionCommand,
  type GetQueryResultsCommandOutput,
} from '@aws-sdk/client-athena'

export const REGIAO = process.env.AWS_REGION ?? 'us-east-1'
export const BANCO = 'nexo_dw'
const SAIDA = process.env.ATHENA_SAIDA ?? 's3://nexo-eixo4-dados/athena-results/'
const WORKGROUP = process.env.ATHENA_WORKGROUP ?? 'primary'

const cliente = new AthenaClient({ region: REGIAO })

export type Valor = string | number | boolean | null
export type Linha = Record<string, Valor>

export type Execucao = {
  linhas: Linha[]
  idConsulta: string
  bytesLidos: number
  ms: number
}

// O Athena devolve tudo como texto; o tipo de cada coluna vem nos metadados.
function converter(texto: string | undefined, tipo: string): Valor {
  if (texto === undefined) return null
  switch (tipo) {
    case 'integer':
    case 'bigint':
    case 'smallint':
    case 'tinyint':
    case 'double':
    case 'float':
    case 'real':
    case 'decimal':
      return Number(texto)
    case 'boolean':
      return texto === 'true'
    default:
      return texto
  }
}

const esperar = (ms: number) => new Promise((r) => setTimeout(r, ms))

export async function consultar(sql: string): Promise<Execucao> {
  const inicio = Date.now()
  const { QueryExecutionId: id } = await cliente.send(
    new StartQueryExecutionCommand({
      QueryString: sql,
      QueryExecutionContext: { Database: BANCO, Catalog: 'AwsDataCatalog' },
      ResultConfiguration: { OutputLocation: SAIDA },
      WorkGroup: WORKGROUP,
    }),
  )
  if (!id) throw new Error('O Athena não devolveu o identificador da consulta.')

  // Espera ativa curta: as consultas do painel levam de 1 a 3 segundos.
  let bytesLidos = 0
  for (let tentativa = 0; ; tentativa++) {
    const { QueryExecution: ex } = await cliente.send(new GetQueryExecutionCommand({ QueryExecutionId: id }))
    const estado = ex?.Status?.State
    if (estado === 'SUCCEEDED') {
      bytesLidos = ex?.Statistics?.DataScannedInBytes ?? 0
      break
    }
    if (estado === 'FAILED' || estado === 'CANCELLED') {
      throw new Error(`Consulta ${estado === 'FAILED' ? 'falhou' : 'cancelada'}: ${ex?.Status?.StateChangeReason ?? 'sem motivo informado'}`)
    }
    if (Date.now() - inicio > 60_000) throw new Error(`Consulta ${id} passou de 60 s sem terminar.`)
    await esperar(Math.min(250 + tentativa * 150, 1000))
  }

  // Paginação: o Athena devolve no máximo mil linhas por chamada. A primeira
  // linha da primeira página é o cabeçalho.
  const linhas: Linha[] = []
  let colunas: { nome: string; tipo: string }[] = []
  let token: string | undefined
  let primeira = true
  do {
    const pagina: GetQueryResultsCommandOutput = await cliente.send(
      new GetQueryResultsCommand({ QueryExecutionId: id, NextToken: token, MaxResults: 1000 }),
    )
    if (primeira) {
      colunas = (pagina.ResultSet?.ResultSetMetadata?.ColumnInfo ?? []).map((c) => ({
        nome: c.Name ?? '',
        tipo: c.Type ?? 'varchar',
      }))
    }
    const rows = pagina.ResultSet?.Rows ?? []
    for (const [i, row] of rows.entries()) {
      if (primeira && i === 0) continue
      const linha: Linha = {}
      colunas.forEach((c, j) => {
        linha[c.nome] = converter(row.Data?.[j]?.VarCharValue, c.tipo)
      })
      linhas.push(linha)
    }
    primeira = false
    token = pagina.NextToken
  } while (token)

  return { linhas, idConsulta: id, bytesLidos, ms: Date.now() - inicio }
}
