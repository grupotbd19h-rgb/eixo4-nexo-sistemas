# Etapa 5 — Análise e visualização

Painel web em React e TypeScript conectado ao banco do projeto: os números são lidos
no **Amazon Athena**, sobre o modelo estrela `nexo_dw` construído na Etapa 3.

```
navegador (React)  →  /api/...  →  servidor Node/TypeScript  →  Amazon Athena (nexo_dw)  →  S3 (Parquet)
```

O navegador nunca fala com a AWS: as credenciais do laboratório ficam só no servidor.

## Como rodar

Pré-requisitos: Node 20 ou superior, e a sessão do Learner Lab ativa, com as
credenciais de **AWS Details → AWS CLI** gravadas em `~/.aws/credentials`.

```
cd etapa-5/painel
npm install
npm run build       # gera dist/
npm run servidor    # http://localhost:8787
```

Ao abrir a página, o painel consulta o Athena e mostra no topo o estado da conexão:
quantas consultas rodaram, quanto tempo levaram e quantos bytes foram lidos. O botão
**Testar conexão** chama `/api/saude`, que conta as linhas das tabelas do `nexo_dw`
e devolve o identificador da consulta no Athena.

### Se o Windows bloquear a gravação

Com o **Acesso controlado a pastas** do Windows Defender ligado, o `node.exe` não
pode gravar dentro de `Documentos`: o `npm install` trava e o build falha com
`EPERM`/`EBADF`. A solução definitiva é liberar o Node em *Segurança do Windows →
Proteção contra ransomware → Permitir um aplicativo* (`C:\Program Files\nodejs\node.exe`).
Sem isso, dá para gravar tudo fora da pasta:

```
npx vite build --base ./ --outDir C:\Users\<voce>\nexo-dist --emptyOutDir
$env:PAINEL_DIST = "C:\Users\<voce>\nexo-dist"; npm run servidor
```

## Rotas da API

| Rota | O que faz |
|---|---|
| `GET /api/saude` | Teste de conexão: contagem das tabelas de fato e de colaboradores, tempo e bytes lidos |
| `GET /api/painel` | Todos os conjuntos do painel, lidos no Athena (guardados em memória por 10 minutos) |
| `GET /api/painel?atualizar=1` | Força nova leitura no banco |

## Cópia gravada

`npm run copia` grava em `src/dados.json` o resultado das mesmas consultas. O painel
mostra essa cópia, e avisa na tela, quando não há servidor por trás (site estático)
ou quando a sessão do laboratório expirou.

## Arquivos

| Arquivo | Papel |
|---|---|
| `painel/servidor/athena.ts` | Conexão com o Athena: executa a consulta, espera, pagina e converte os tipos |
| `painel/servidor/consultas.ts` | O SQL do painel e a montagem do objeto que o front desenha |
| `painel/servidor/estatistica.ts` | Teste qui-quadrado de independência e V de Cramér |
| `painel/servidor/index.ts` | Servidor HTTP: API e arquivos de `dist/` |
| `painel/servidor/copia.ts` | Grava a cópia em `src/dados.json` |
| `painel/src/` | O painel: páginas Aquisição, Fila e Times |

## Páginas

- **Aquisição** — pergunta 2: custo de aquisição por campanha e por plano, conversão
  por tempo de resposta, série mensal e o custo de não ter rastreio.
- **Fila** — pergunta 1: o escore de atendimento por combinação de origem,
  temperatura, porte e plano, com intervalo de confiança de Wilson a 95%, e o teste
  qui-quadrado de cada atributo.
- **Times** — realizado contra a meta, conversão por time e por tier, pré-vendas.
