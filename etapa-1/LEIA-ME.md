# Documento do Projeto — Eixo 4 (Projeto Radice)

O documento do projeto é **cumulativo**: o mesmo texto ganha um capítulo por etapa.
Por isso ele é mantido em um **Markdown-fonte único** (`documento.md`) e os arquivos de
entrega (PDF e DOCX) são **gerados** a partir dele, já formatados.

O layout segue o modelo usado pelo grupo no semestre passado (`projeto.20.05.docx`).

## Arquivos

| Arquivo | Papel |
|---|---|
| `documento.md` | **Fonte.** É o único arquivo que se edita. |
| `gerar_documento.py` | Gerador (PDF + DOCX). |
| `Eixo4_Etapa1_Radice.pdf` | Entrega do Canvas. |
| `Eixo4_Etapa1_Radice.docx` | Cópia editável, para revisar no Word. |

## Como regenerar

```
pip install reportlab python-docx
python gerar_documento.py documento.md Eixo4_Etapa1_Radice
```

O DOCX traz o sumário como campo do Word: ao abrir, clicar com o botão direito sobre ele
e escolher **Atualizar campo** para preencher os números de página.

## Formatação aplicada (padrão do modelo)

- A4, margens 3 cm (esquerda e superior) e 2 cm (direita) / 3 cm (inferior).
- Arial 12, entrelinha simples, texto justificado, sem recuo de primeira linha,
  espaçamento de 5 pt entre parágrafos.
- Capa única, reunindo instituição, curso, integrantes, título, nota de apresentação e
  orientador; sumário na página seguinte.
- Seções **contínuas**, sem quebra de página entre elas (controlado por
  `quebra_secao: nao` no bloco de metadados).
- Número de página no rodapé à direita, a partir da segunda página.
- Quadros com moldura fechada; tabelas com laterais abertas (padrão IBGE).
  Legenda acima, fonte abaixo, ambos coladas ao quadro.
- Citação direta longa com recuo de 4 cm, corpo 10 e entrelinha simples.
- Referências alinhadas à esquerda, entrelinha simples, separadas por linha em branco.

## Sintaxe do Markdown-fonte

| Marca | Significado |
|---|---|
| `:::meta ... :::` | Metadados da capa |
| `# 1 TÍTULO` | Seção primária |
| `# *TÍTULO` | Seção primária sem numeração (centralizada) |
| `## 1.1 Título` | Seção secundária |
| `### 1.1.1 Título` | Seção terciária |
| `^Quadro 1 – Legenda` | Legenda, colocada antes da tabela |
| `\| a \| b \|` | Tabela |
| `!Fonte: ...` | Nota de fonte, colocada depois da tabela |
| `> texto` | Citação direta longa |
| `- item` / `1. item` | Listas |
| `**negrito**` / `*itálico*` | Formatação inline |

O tipo da tabela é inferido pela legenda: legenda começando em "Tabela" gera tabela
aberta; qualquer outra ("Quadro") gera moldura fechada. A seção cujo título contém
"REFER" é formatada como lista de referências.

Metadados aceitos no bloco `:::meta`: `instituicao`, `curso`, `unidade`, `titulo`,
`etapa`, `autores` (separados por `;`), `natureza`, `orientador`, `local`, `ano`,
`quebra_secao`.

## Para as próximas etapas

Basta acrescentar as novas seções ao `documento.md`, antes de `# 7 REFERÊNCIAS`, e
regenerar. A numeração das seções é escrita à mão no próprio título, o que mantém o
controle com o grupo.
