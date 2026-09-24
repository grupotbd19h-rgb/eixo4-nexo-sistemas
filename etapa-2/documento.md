:::meta
instituicao: Pontifícia Universidade Católica de Minas Gerais
curso: Tecnologia em Banco de Dados - EAD
unidade: Graduação Virtual
titulo: Plataforma de dados para priorização de leads e análise do custo de aquisição de clientes
etapa: Etapa 2 — Replicação e integração dos dados
autores: Alberto Santana Santos; Alessandro Junio Lopes Rodrigues; Gabriel Figueiredo do Nascimento; João Victor de Andrade Guedes; Lucas Naves da Silveira; Luiza Gonçalves Zacarias
local: Belo Horizonte
ano: 2026
natureza: Projeto apresentado ao Curso de Tecnologia em Banco de Dados da Pontifícia Universidade Católica de Minas Gerais, como requisito parcial da Etapa 2 do Projeto de Big Data Analytics — Eixo 4.
orientador: Prof. Marco Paulo
quebra_secao: nao
:::

# 1 INTRODUÇÃO

Castells (1999) caracteriza a sociedade contemporânea como uma sociedade em rede: a informação se torna a matéria-prima da atividade econômica, e a rede, viabilizada pelas tecnologias de informação e comunicação, passa a ser a forma predominante de organizar a produção, o trabalho e o consumo. Nessa configuração, a tecnologia não é algo que se acrescenta a um negócio já formado — é em torno dela que o negócio se estrutura.

A Nexo Sistemas, organização **fictícia** tomada como objeto deste projeto, vende software de gestão por assinatura para pequenas empresas do varejo e se caracteriza como empresa dessa sociedade em rede em todas as frentes. Vende à distância, sem visita presencial; entrega um produto que só funciona em nuvem; e encontra seus clientes por busca e anúncio na internet, em plataformas de mídia cujas regras não controla. Mais do que isso, o que ela vende é a digitalização de outros negócios: cada contrato fechado tira um pequeno lojista do caderno e da planilha e o coloca num sistema conectado.

O projeto consiste em construir, para ela, uma plataforma de dados que reúna informações hoje espalhadas em sistemas separados, de modo que a empresa consiga priorizar o atendimento aos interessados com maior chance de fechar negócio e saber quanto custa, em cada canal, conquistar um cliente.

# 2 A EMPRESA

## 2.1 Ramo de Atuação, Porte e Produtos

A Nexo Sistemas atua no ramo de desenvolvimento e licenciamento de software. Seu produto reúne frente de caixa, controle de estoque, emissão de notas fiscais e gestão financeira, e é vendido por assinatura mensal. Foi fundada em 2016, fica em Belo Horizonte e opera de forma remota: a venda é feita à distância, por um time comercial próprio, e a implantação acontece sem visita presencial.

A empresa tem **70 funcionários**: 30 na área comercial, 18 em desenvolvimento, 12 em suporte e 10 no administrativo, financeiro e TI. Atende cerca de 2.500 clientes e fecha aproximadamente mil novos contratos por ano, com receita anual em torno de R$ 10,9 milhões. Pelo número de funcionários e pelo faturamento, é classificada como **média empresa**.

São vendidos três planos de assinatura, que se diferenciam pelo porte do cliente e pelos recursos liberados.

^Quadro 1 – Produtos comercializados
| Plano | Mensalidade (R$) | Perfil de cliente | Clientes ativos |
|---|---|---|---|
| Essencial | 190 | Microempresas e autônomos | 1.100 |
| Profissional | 390 | Pequenas empresas | 1.150 |
| Corporativo | 990 | Médias empresas e redes de lojas | 250 |
!Fonte: elaborado pelos autores (2026).

## 2.2 Recursos de TI

A empresa não tem servidores próprios. O produto e os sistemas internos rodam em nuvem contratada como serviço, e o hardware se resume aos notebooks dos funcionários, aos headsets do time comercial e ao link de internet da sede.

Em software, a operação comercial se apoia em quatro fontes de informação, mantidas separadamente:

- **CRM**, com os contatos, as oportunidades e as etapas da venda;
- **Plataformas de anúncios**, com o quanto foi investido e o que cada campanha trouxe;
- **Plataforma de cobrança**, com os planos contratados, as faturas, os pagamentos e os cancelamentos;
- **Planilhas do time comercial**, com as metas de cada vendedor, as faixas de comissão e a apuração refeita à mão todo mês.

Destas quatro, três serão as origens de dados do projeto: o CRM, a plataforma de anúncios da Meta e as planilhas do time comercial. O recorte é justificado no capítulo 5.

Há ainda a base de uso do próprio produto, que registra o que cada cliente faz no sistema. É a maior de todas em quantidade de registros, mas hoje não é aproveitada fora do suporte.

Em serviços de TI, quase tudo é contratado por assinatura, mais o suporte técnico terceirizado e a hospedagem em nuvem. A equipe de tecnologia cuida só do produto: não existe ninguém dedicado a dados na operação comercial.

# 3 O PROBLEMA

A Nexo recebe cerca de 3.000 oportunidades de venda por mês e fecha negócio com 3% delas. O time comercial atende por ordem de chegada, e não por quem tem mais chance de comprar, simplesmente porque não existe critério para ordenar a fila: 31% do que entra não recebe nenhum contato em 72 horas, justo o período em que o interesse ainda está quente.

Ao mesmo tempo, o custo para conquistar um cliente — somando o investimento em anúncios e a comissão paga na venda — subiu de R$ 900 para R$ 1.450 em dois anos, e a empresa não consegue dizer qual canal ou qual plano está puxando essa alta. O motivo é sempre o mesmo: o investimento em anúncio está numa plataforma, o histórico da negociação está no CRM, o dinheiro que entrou está na cobrança, e nada disso se conversa. Pelo mesmo motivo, a comissão do time comercial é reapurada à mão a cada virada de mês.

O projeto pretende responder a duas perguntas: como ordenar a fila de atendimento por chance de conversão, e quanto custa conquistar um cliente em cada canal e em cada plano. Para isso, os dados do funil serão gerados de forma sintética, reproduzindo só a estrutura do negócio.

# 4 A EMPRESA E A SOCIEDADE DIGITAL

Hoje a Nexo usa tecnologia só para operar, não para decidir. Com a plataforma de dados, isso muda de três formas. O trabalho do vendedor muda, porque ele deixa de escolher a quem ligar e passa a seguir uma fila ordenada. As competências mudam, porque a empresa vai precisar de gente de dados, função que hoje não existe. E a responsabilidade aumenta, porque juntar num só lugar os dados de todos os sistemas cria um ponto único de risco, o que exige controle de acesso e regra clara sobre por quanto tempo cada dado é guardado.

Do lado da sociedade, o ponto sensível é quem a empresa decide atender primeiro. Uma fila ordenada por potencial econômico tende a priorizar o cliente maior e deixar o microempreendedor para o final — justamente quem mais ganharia com o controle que o produto oferece. Por isso o grupo assume desde já duas regras: a ordenação organiza a fila, mas não exclui ninguém dela, garantindo um prazo máximo para o primeiro contato; e o critério usado para ordenar fica documentado e aberto ao time comercial. Vale lembrar ainda que a lei brasileira garante ao cliente o direito de pedir revisão de decisões tomadas só por máquina (BRASIL, 2018).

Na outra direção, a sociedade digital também mexe com a empresa. Mudanças em obrigações fiscais eletrônicas provocam picos de procura por sistemas de gestão, e ela precisa antecipar isso para dimensionar equipe e verba de anúncio. E como depende de plataformas de mídia cujas regras mudam sem aviso, seu custo de aquisição é em parte decidido por terceiros — o que reforça a necessidade de ter medição própria.

# 5 BASES DE DADOS

Como a Nexo é fictícia, os dados das três origens foram gerados por um programa em Python, com semente fixa: rodar de novo produz exatamente os mesmos arquivos. A janela é de seis meses, de março a agosto de 2026, com janeiro e fevereiro também simulados para que o funil já chegue cheio em março. Os arquivos reproduzem os números do caso apresentados no capítulo 3: 3.051 oportunidades por mês, 2,99% de conversão de oportunidade em contrato, 30,8% sem nenhum contato em 72 horas e custo de aquisição entre R$ 1.004 e R$ 1.276 ao mês.

Cada origem vem no formato do próprio sistema, e não num formato já pronto para análise. A Meta informa o valor gasto como texto e identifica a campanha por um código numérico de quinze dígitos; o CRM não guarda esse código, apenas a identificação de origem do link (UTM). Entre os leads pagos, 6,8% chegam sem UTM alguma e 2,0% chegam com o texto `{{campaign.name}}` literal, um marcador que a plataforma deixou de substituir. As planilhas comerciais, por sua vez, são tabelas digitadas à mão, sem chave que as ligue ao CRM além do código do colaborador. Resolver essas diferenças é justamente o trabalho do processo de integração.

^Quadro 2 – Bases de dados de origem
| Origem | Arquivos | Conteúdo | Registros |
|---|---|---|---|
| CRM | oportunidades | Oportunidades com origem, UTM, datas de criação, primeiro contato e fechamento, responsáveis, resultado e plano contratado | 19.280 |
| CRM | equipe_comercial | Cadastro do time comercial, com função, tier e data de admissão | 30 |
| Meta Ads | insights_campanhas_diario | Impressões, cliques, leads e valor gasto, por campanha e dia | 920 |
| Planilhas comerciais | metas_mensais | Meta mensal de cada colaborador, por tipo de meta | 180 |
| Planilhas comerciais | faixas_comissao | Percentual de comissão por faixa de venda anual, com a trava de caixa | 5 |
| Planilhas comerciais | regras_bonus | Regras de bônus por papel do time comercial | 6 |
!Fonte: elaborado pelos autores (2026).

A plataforma de cobrança, quarta fonte descrita no item 2.2, ficou fora deste recorte: as duas perguntas do capítulo 3 se resolvem no funil e no investimento em mídia, sem depender do que foi faturado depois. Isso mantém a etapa no tamanho que o grupo consegue implementar e deixa a receita recebida como extensão natural para as etapas seguintes.

# 6 MODELAGEM DOS DADOS

## 6.1 Modelo Conceitual

A Figura 1 representa o negócio como conjuntos de entidades e as relações entre eles. Três relações são centrais para o problema. A ligação entre campanha e oportunidade é opcional, porque parte das oportunidades chega sem origem — é por isso que hoje não se sabe o custo de aquisição por canal. A oportunidade é atendida por colaboradores, o pré-vendedor que faz o primeiro contato e o vendedor que fecha, e cada oportunidade ganha registra o plano contratado e o valor do contrato. Por fim, cada colaborador tem uma meta por mês, o que liga o time comercial às planilhas e permite apurar a comissão sobre o que foi assinado.

^Figura 1 – Modelo conceitual
@diagramas/modelo_conceitual.png | 16
!Fonte: elaborado pelos autores (2026).

## 6.2 Modelo do Armazém de Dados

No destino, os dados são organizados em modelo estrela: tabelas de fato, que registram os acontecimentos medidos, cercadas por tabelas de dimensão, que descrevem por quais ângulos esses fatos são analisados (KIMBALL; ROSS, 2013). Os três fatos não são do mesmo tipo, e isso define como cada um é carregado. O fato da oportunidade é um *snapshot* acumulado: a mesma linha guarda as datas de criação, de primeiro contato e de fechamento, e é reescrita conforme a negociação avança. O fato do investimento é transacional diário, uma linha por campanha e dia, que nunca muda depois de gravada. O fato da meta é um *snapshot* periódico, fechado uma vez por mês.

^Quadro 3 – Tabelas do armazém de dados
| Tabela | Tipo | Uma linha por | Uso no problema |
|---|---|---|---|
| fato_oportunidade | Fato — *snapshot* acumulado | Oportunidade | Tempo até o primeiro contato e conversão por canal, plano e perfil — base para ordenar a fila |
| fato_investimento_anuncio | Fato — transacional diário | Campanha por dia | Investimento em mídia por campanha — base do custo de aquisição |
| fato_meta_vendedor | Fato — *snapshot* periódico | Colaborador por mês | Meta contra realizado e faixa de comissão |
| dim_data | Dimensão | Dia | Calendário comum a todos os fatos |
| dim_campanha | Dimensão | Campanha | Plataforma, nome e UTM — liga o anúncio à oportunidade |
| dim_plano | Dimensão | Plano | Mensalidade e perfil de cliente |
| dim_colaborador | Dimensão | Colaborador | Função, tier e time |
!Fonte: elaborado pelos autores (2026).

A dimensão do plano não vem de nenhuma das três origens: é uma tabela de referência, com os três planos do Quadro 1, carregada uma única vez. As demais dimensões são extraídas das origens e mantidas sem histórico de alteração nesta etapa, o que é suficiente porque a janela de dados é de seis meses e nenhum atributo dimensional muda dentro dela.

# 7 ARQUITETURA E INTEGRAÇÃO

## 7.1 Infraestrutura

^Quadro 4 – Componentes da arquitetura
| Componente | Escolha | Motivo |
|---|---|---|
| Nuvem | Amazon Web Services (AWS), pelo laboratório do AWS Academy, região Norte da Virgínia (us-east-1) | O laboratório dá à turma um orçamento fechado e só libera as regiões us-east-1 e us-west-2 |
| Armazenamento bruto | Amazon S3 | Guarda os arquivos como chegaram, separados por origem e data de carga, o que permite reprocessar |
| SGBD | PostgreSQL no Amazon RDS | Banco relacional com SQL padrão; backup e atualização ficam a cargo da AWS |
| Contêineres | Docker e Docker Compose | O mesmo ambiente roda na máquina de cada integrante e na nuvem |
| Orquestração | Apache Airflow, em contêiner, numa máquina Amazon EC2 t4g.small ligada sob demanda | Ferramenta aberta e padrão de mercado; a versão gerenciada da AWS custaria cerca de US$ 212 por mês, mais de quatro vezes o orçamento inteiro do laboratório |
| Linguagens e bibliotecas | Python (pandas, boto3, SQLAlchemy) e SQL | Extração e carga em Python; transformação em SQL |
| Repositório | GitHub | Código do gerador, dos fluxos do Airflow e dos scripts SQL |
!Fonte: elaborado pelos autores (2026).

## 7.2 Processo de Integração

O processo, representado na Figura 2, é particionado por dia: cada execução trata um único dia de dados, identificado pela data de referência que o Airflow passa à tarefa. São cinco passos:

1. **Extração:** os registros daquele dia são coletados em cada origem.
2. **Camada bruta:** o que foi extraído é gravado sem alteração no S3, numa pasta com o nome da origem e a data de referência.
3. **Staging:** os arquivos são carregados em tabelas espelho no PostgreSQL, uma para cada arquivo de origem.
4. **Transformação:** comandos SQL padronizam tipos e unidades (o valor gasto da Meta, que vem como texto, torna-se número), ligam cada oportunidade à campanha pela UTM, tratam as oportunidades sem UTM e as que trazem o marcador não substituído, calculam o tempo até o primeiro contato e gravam o resultado no modelo estrela.
5. **Conferência:** a cada execução, o número de registros lidos na origem é comparado com o número gravado no destino.

Como os dados são sintéticos e a janela é fechada, não existe carga nova chegando todo dia: a execução real é um *backfill*, em que o Airflow roda a mesma tarefa uma vez para cada um dos 184 dias da janela. É por isso que cada passo precisa ser idempotente — reprocessar um dia tem que sobrescrever aquele dia, nunca duplicá-lo. Numa operação contínua, a mesma rotina rodaria uma vez ao dia, sem alteração nenhuma no código.

^Figura 2 – Arquitetura do processo de integração
@diagramas/arquitetura.png | 16
!Fonte: elaborado pelos autores (2026).

# 8 CUSTOS

O projeto roda no laboratório do AWS Academy, que dá à turma um orçamento fechado de **US$ 50** para todo o semestre. Esse limite é rígido: esgotado o orçamento, a conta é desativada e o trabalho armazenado nela se perde. Não há, portanto, a folga de uma conta comum, em que o estouro apenas passa a ser cobrado. É essa restrição, e não o preço de tabela, que define a arquitetura.

O volume de dados é irrelevante para o custo — os seis arquivos de origem somam menos de 6 MB. O que custa é o tempo em que as máquinas ficam ligadas. Por isso nem a EC2 nem o banco ficam de pé: ambos são iniciados quando há trabalho a fazer e desligados em seguida. O Quadro 5 compara esse regime com o de máquinas sempre ligadas, pelos preços sob demanda da região escolhida (AMAZON WEB SERVICES, 2026a; 2026b).

^Quadro 5 – Consumo mensal estimado no laboratório (us-east-1)
| Serviço | Configuração | Preço | Sob demanda, ~10 h/mês (US$) | Sempre ligado (US$) |
|---|---|---|---|---|
| Amazon EC2 | t4g.small, 2 processadores e 2 GB | US$ 0,0168/h | 0,17 | 12,26 |
| Amazon RDS for PostgreSQL | db.t4g.micro | US$ 0,016/h | 0,16 | 11,68 |
| Endereço IP público | cobrado enquanto a máquina está ligada | US$ 0,005/h | 0,05 | 3,65 |
| Disco da máquina (EBS gp3) | 10 GB | US$ 0,08/GB ao mês | 0,80 | 0,80 |
| Armazenamento do banco | 20 GB | US$ 0,115/GB ao mês | 2,30 | 2,30 |
| Amazon S3 | menos de 1 GB | US$ 0,023/GB ao mês | 0,02 | 0,02 |
| **Total por mês** | | | **3,50** | **30,71** |
!Fonte: elaborado pelos autores com base nos preços da AWS (2026).

De setembro a dezembro, o regime sob demanda consome cerca de **US$ 9 dos US$ 50** disponíveis. Com as duas máquinas sempre ligadas, o mesmo período custaria cerca de US$ 77 e estouraria o orçamento antes da última etapa.

Duas consequências merecem registro. A primeira é que o piso do custo é o armazenamento: disco de máquina desligada e armazenamento de banco parado continuam sendo cobrados, e somam US$ 3,10 por mês independentemente de uso — ou seja, 89% do consumo previsto. A segunda é que o maior risco não é técnico, e sim de esquecimento: um banco deixado ligado por um mês consome US$ 14, mais do que o projeto inteiro. Como o indicador de saldo do laboratório é alimentado pelo serviço de orçamentos da AWS e atrasa de oito a doze horas (AMAZON WEB SERVICES, 2026c), ele não serve de alarme. A proteção é procedimental e está no próprio pipeline: a última tarefa do fluxo desliga a máquina de processamento, e o encerramento de cada sessão de trabalho para o banco.

# 9 REPOSITÓRIO

O código do projeto está disponível em: https://github.com/grupotbd19h-rgb/eixo4-nexo-sistemas.

O repositório reúne o programa que gera as bases sintéticas das três origens, o programa que desenha os diagramas, o gerador deste documento e os arquivos de dados produzidos. Os fluxos do Airflow e os comandos SQL da transformação serão acrescentados na Etapa 3, quando o pipeline for implementado.

# 10 REFERÊNCIAS

AMAZON WEB SERVICES. Amazon EC2 On-Demand Pricing. 2026a. Disponível em: https://aws.amazon.com/ec2/pricing/on-demand/. Acesso em: 24 set. 2026.

AMAZON WEB SERVICES. Amazon RDS for PostgreSQL Pricing. 2026b. Disponível em: https://aws.amazon.com/rds/postgresql/pricing/. Acesso em: 24 set. 2026.

AMAZON WEB SERVICES. AWS Academy Learner Lab: educator guide. 2026c. Disponível em: https://d1.awsstatic.com/AWS%20Academy%20Learner%20Lab%20Educator%20Guide.pdf. Acesso em: 24 set. 2026.

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 30 ago. 2026.

CASTELLS, Manuel. A sociedade em rede. São Paulo: Paz e Terra, 1999. (A era da informação: economia, sociedade e cultura, v. 1).

KIMBALL, Ralph; ROSS, Margy. The data warehouse toolkit: the definitive guide to dimensional modeling. 3. ed. Indianapolis: Wiley, 2013.
