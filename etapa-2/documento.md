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

Em software, a operação comercial se apoia em quatro fontes de informação, mantidas separadamente, que serão as origens de dados do projeto:

- **CRM**, com os contatos, as oportunidades e as etapas da venda;
- **Plataformas de anúncios**, com o quanto foi investido e o que cada campanha trouxe;
- **Plataforma de cobrança**, com os planos contratados, as faturas, os pagamentos e os cancelamentos;
- **Planilhas do time comercial**, com as metas de cada vendedor, as faixas de comissão e a apuração refeita à mão todo mês.

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

Como a Nexo é fictícia, os dados das quatro origens foram gerados por um programa em Python, com semente fixa: rodar de novo produz exatamente os mesmos arquivos. Eles cobrem 24 meses, de setembro de 2024 a agosto de 2026, e reproduzem os números do caso: cerca de 3.000 oportunidades por mês, 3% de conversão, 31% sem contato em 72 horas, 2.500 clientes ativos e custo de aquisição subindo de cerca de R$ 950 para R$ 1.490.

Cada origem vem no formato do próprio sistema, e não num formato já pronto para análise. O Google Ads informa o custo em milionésimos de real, a Meta informa o valor gasto como texto e o CRM não guarda o código da campanha, só a identificação de origem do link (UTM) — e 6% das oportunidades chegam sem ela. Resolver essas diferenças é justamente o trabalho do processo de integração.

^Quadro 2 – Bases de dados de origem
| Origem | Arquivos | Conteúdo | Registros |
|---|---|---|---|
| Google Ads | campanhas_desempenho_diario | Impressões, cliques, conversões e custo, por campanha e dia | 2.920 |
| Meta Ads | insights_campanhas_diario | Impressões, cliques, leads e valor gasto, por campanha e dia | 2.920 |
| CRM | oportunidades; equipe_comercial | Oportunidades com origem, datas de criação, primeiro contato e fechamento, responsáveis e resultado; cadastro do time comercial | 72.096; 30 |
| Plataforma de cobrança | planos; clientes; assinaturas; faturas; pagamentos; cancelamentos | Planos contratados, faturas mensais, cada pagamento recebido e os cancelamentos com motivo | 3; 4.686; 4.686; 62.880; 60.862; 2.174 |
| Planilhas comerciais | metas_mensais; faixas_comissao | Meta mensal de cada vendedor e percentual de comissão por faixa de atingimento | 480; 5 |
!Fonte: elaborado pelos autores (2026).

# 6 MODELAGEM DOS DADOS

## 6.1 Modelo Conceitual

A Figura 1 representa o negócio como conjuntos de entidades e as relações entre eles. Três relações são centrais para o problema. A ligação entre campanha e oportunidade é opcional, porque parte das oportunidades chega sem origem — é por isso que hoje não se sabe o custo de aquisição por canal. A oportunidade é atendida por colaboradores (o pré-vendedor, que faz o primeiro contato, e o vendedor, que fecha), e só a oportunidade ganha gera um cliente. Por fim, cada fatura guarda seus pagamentos, o que permite calcular a comissão tanto sobre a venda assinada quanto sobre o dinheiro efetivamente recebido.

^Figura 1 – Modelo conceitual
@diagramas/modelo_conceitual.png | 16
!Fonte: elaborado pelos autores (2026).

## 6.2 Modelo do Armazém de Dados

No destino, os dados são organizados em modelo estrela: tabelas de fato, que registram os acontecimentos medidos, cercadas por tabelas de dimensão, que descrevem por quais ângulos esses fatos são analisados (KIMBALL; ROSS, 2013).

^Quadro 3 – Tabelas do armazém de dados
| Tabela | Tipo | Uma linha por | Uso no problema |
|---|---|---|---|
| fato_oportunidade | Fato | Oportunidade | Tempo até o primeiro contato e conversão por canal, plano e perfil — base para ordenar a fila |
| fato_investimento_anuncio | Fato | Campanha por dia | Investimento de Google e Meta numa só tabela — base do custo de aquisição |
| fato_fatura | Fato | Fatura | Receita faturada e recebida, e atraso |
| fato_assinatura | Fato | Assinatura | Clientes ativos, plano e cancelamento |
| fato_meta_vendedor | Fato | Vendedor por mês | Meta contra realizado e faixa de comissão |
| dim_data | Dimensão | Dia | Calendário comum a todos os fatos |
| dim_campanha | Dimensão | Campanha | Plataforma, nome e UTM — liga o anúncio à oportunidade |
| dim_plano | Dimensão | Plano | Mensalidade e perfil de cliente |
| dim_colaborador | Dimensão | Colaborador | Função e time |
| dim_cliente | Dimensão | Cliente | Segmento, porte e estado |
!Fonte: elaborado pelos autores (2026).

# 7 ARQUITETURA E INTEGRAÇÃO

## 7.1 Infraestrutura

^Quadro 4 – Componentes da arquitetura
| Componente | Escolha | Motivo |
|---|---|---|
| Nuvem | Amazon Web Services (AWS), região Norte da Virgínia (us-east-1) | A conta nova recebe créditos que cobrem o semestre, e a região é a de menor preço |
| Armazenamento bruto | Amazon S3 | Guarda os arquivos como chegaram, separados por origem e data de carga, o que permite reprocessar |
| SGBD | PostgreSQL no Amazon RDS | Banco relacional com SQL padrão; backup e atualização ficam a cargo da AWS |
| Contêineres | Docker e Docker Compose | O mesmo ambiente roda na máquina de cada integrante e na nuvem |
| Orquestração | Apache Airflow, em contêiner, numa máquina Amazon EC2 | Ferramenta aberta e padrão de mercado; a versão gerenciada da AWS custaria cerca de US$ 212 por mês |
| Linguagens e bibliotecas | Python (pandas, boto3, SQLAlchemy) e SQL | Extração e carga em Python; transformação em SQL |
| Repositório | GitHub | Código do gerador, dos fluxos do Airflow e dos scripts SQL |
!Fonte: elaborado pelos autores (2026).

## 7.2 Processo de Integração

O processo, representado na Figura 2, roda uma vez por dia, disparado pelo Airflow:

1. **Extração:** os arquivos de cada origem são coletados.
2. **Camada bruta:** cada arquivo é gravado sem alteração no S3, numa pasta com o nome da origem e a data da carga.
3. **Staging:** os arquivos são carregados em tabelas espelho no PostgreSQL, uma para cada arquivo.
4. **Transformação:** comandos SQL padronizam unidades e datas (o custo do Google é dividido por um milhão, o valor gasto da Meta vira número), ligam cada oportunidade à campanha pela UTM, calculam o tempo até o primeiro contato e gravam o resultado no modelo estrela.
5. **Conferência:** a cada carga, o número de registros na origem é comparado com o número gravado no destino.

^Figura 2 – Arquitetura do processo de integração
@diagramas/arquitetura.png | 16
!Fonte: elaborado pelos autores (2026).

# 8 CUSTOS

A conta nova da AWS entra no plano gratuito, que dá até US$ 200 em créditos por seis meses e só permite máquinas de uma lista reduzida (AMAZON WEB SERVICES, 2026a). Por isso foram escolhidas uma máquina c7i-flex.large (2 processadores e 4 GB de memória, o mínimo recomendável para o Airflow) e um banco db.t4g.micro, ambos incluídos no plano. O Quadro 5 mostra o custo mensal pelos preços sob demanda da região escolhida (AMAZON WEB SERVICES, 2026b; 2026c).

^Quadro 5 – Estimativa de custo mensal na AWS (us-east-1)
| Serviço | Configuração | Ligado 24 h/dia (US$) | Máquina ligada 12 h/dia (US$) |
|---|---|---|---|
| Amazon EC2 | c7i-flex.large, US$ 0,0848/h | 61,90 | 30,95 |
| Disco da máquina (EBS gp3) | 30 GB, US$ 0,08/GB | 2,40 | 2,40 |
| Amazon RDS for PostgreSQL | db.t4g.micro, US$ 0,016/h | 11,68 | 11,68 |
| Armazenamento do banco | 20 GB, US$ 0,115/GB | 2,30 | 2,30 |
| Endereço IP público | US$ 0,005/h | 3,65 | 3,65 |
| Amazon S3 | Menos de 1 GB, US$ 0,023/GB | 0,02 | 0,02 |
| **Total** | | **81,95** | **51,00** |
!Fonte: elaborado pelos autores com base nos preços da AWS (2026).

Com a máquina ligada o dia inteiro, o período de setembro a dezembro custaria cerca de US$ 225, acima dos créditos. Com a máquina ligada só 12 horas por dia — o suficiente para a carga diária e para o trabalho do grupo —, o custo cai para cerca de US$ 140. Para não haver surpresa, a conta terá alertas de orçamento, que são gratuitos, avisando o grupo ao atingir US$ 50 e US$ 150.

# 9 REPOSITÓRIO

O código do projeto está disponível em: [INSERIR LINK DO REPOSITÓRIO DO GRUPO NO GITHUB].

# 10 REFERÊNCIAS

AMAZON WEB SERVICES. AWS Free Tier FAQs. 2026a. 2026. Disponível em: https://aws.amazon.com/free/free-tier-faqs/. Acesso em: 14 set. 2026.

AMAZON WEB SERVICES. Amazon EC2 On-Demand Pricing. 2026. Disponível em: https://aws.amazon.com/ec2/pricing/on-demand/. Acesso em: 14 set. 2026.

AMAZON WEB SERVICES. Amazon RDS for PostgreSQL Pricing. 2026. Disponível em: https://aws.amazon.com/rds/postgresql/pricing/. Acesso em: 14 set. 2026.

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 30 ago. 2026.

CASTELLS, Manuel. A sociedade em rede. São Paulo: Paz e Terra, 1999. (A era da informação: economia, sociedade e cultura, v. 1).

KIMBALL, Ralph; ROSS, Margy. The data warehouse toolkit: the definitive guide to dimensional modeling. 3. ed. Indianapolis: Wiley, 2013.
