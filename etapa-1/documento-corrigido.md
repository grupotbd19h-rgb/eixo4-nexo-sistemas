:::meta
instituicao: Pontifícia Universidade Católica de Minas Gerais
curso: Tecnologia em Banco de Dados - EAD
unidade: Graduação Virtual
titulo: Plataforma de dados para priorização de leads e análise do custo de aquisição de clientes
etapa: Etapa 1 — Definição do grupo e do objeto do projeto
autores: Alberto Santana Santos; Alessandro Junio Lopes Rodrigues; Gabriel Figueiredo do Nascimento; João Victor de Andrade Guedes; Lucas Naves da Silveira; Luiza Gonçalves Zacarias
local: Belo Horizonte
ano: 2026
natureza: Projeto apresentado ao Curso de Tecnologia em Banco de Dados da Pontifícia Universidade Católica de Minas Gerais, como requisito parcial da Etapa 1 do Projeto de Big Data Analytics — Eixo 4.
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

Em software, a operação comercial se apoia em três fontes de informação, mantidas separadamente, que serão as origens de dados do projeto:

- **CRM**, com os contatos, as oportunidades e as etapas da venda;
- **Plataforma de anúncios**, com o quanto foi investido e o que cada campanha trouxe;
- **Planilhas do time comercial**, com as metas de cada vendedor, as faixas de comissão e a apuração refeita à mão todo mês.

Há ainda a base de uso do próprio produto, que registra o que cada cliente faz no sistema. É a maior de todas em quantidade de registros, mas hoje não é aproveitada fora do suporte.

Em serviços de TI, quase tudo é contratado por assinatura, mais o suporte técnico terceirizado e a hospedagem em nuvem. A equipe de tecnologia cuida só do produto: não existe ninguém dedicado a dados na operação comercial.

# 3 O PROBLEMA

A Nexo recebe cerca de 3.000 oportunidades de venda por mês e fecha negócio com 3% delas. O time comercial atende por ordem de chegada, e não por quem tem mais chance de comprar, simplesmente porque não existe critério para ordenar a fila: 31% do que entra não recebe nenhum contato em 72 horas, justo o período em que o interesse ainda está quente.

Ao mesmo tempo, o custo para conquistar um cliente — somando o investimento em anúncios e a comissão paga na venda — subiu de R$ 900 para R$ 1.450 em dois anos, e a empresa não consegue dizer qual canal ou qual plano está puxando essa alta. O motivo é sempre o mesmo: o investimento em anúncio está numa plataforma, o histórico da negociação está no CRM, as metas e a comissão estão em planilhas, e nada disso se conversa. Pelo mesmo motivo, a comissão do time comercial é reapurada à mão a cada virada de mês.

O projeto pretende responder a duas perguntas: como ordenar a fila de atendimento por chance de conversão, e quanto custa conquistar um cliente em cada canal e em cada plano. Para isso, os dados do funil serão gerados de forma sintética, reproduzindo só a estrutura do negócio.

# 4 A EMPRESA E A SOCIEDADE DIGITAL

Hoje a Nexo usa tecnologia só para operar, não para decidir. Com a plataforma de dados, isso muda de três formas. O trabalho do vendedor muda, porque ele deixa de escolher a quem ligar e passa a seguir uma fila ordenada. As competências mudam, porque a empresa vai precisar de gente de dados, função que hoje não existe. E a responsabilidade aumenta, porque juntar num só lugar os dados de todos os sistemas cria um ponto único de risco, o que exige controle de acesso e regra clara sobre por quanto tempo cada dado é guardado.

Do lado da sociedade, o ponto sensível é quem a empresa decide atender primeiro. Uma fila ordenada por potencial econômico tende a priorizar o cliente maior e deixar o microempreendedor para o final — justamente quem mais ganharia com o controle que o produto oferece. Por isso o grupo assume desde já duas regras: a ordenação organiza a fila, mas não exclui ninguém dela, garantindo um prazo máximo para o primeiro contato; e o critério usado para ordenar fica documentado e aberto ao time comercial. Vale lembrar ainda que a lei brasileira garante ao cliente o direito de pedir revisão de decisões tomadas só por máquina (BRASIL, 2018).

Na outra direção, a sociedade digital também mexe com a empresa. Mudanças em obrigações fiscais eletrônicas provocam picos de procura por sistemas de gestão, e ela precisa antecipar isso para dimensionar equipe e verba de anúncio. E como depende de plataformas de mídia cujas regras mudam sem aviso, seu custo de aquisição é em parte decidido por terceiros — o que reforça a necessidade de ter medição própria.

# 5 REFERÊNCIAS

BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 30 ago. 2026.

CASTELLS, Manuel. A sociedade em rede. São Paulo: Paz e Terra, 1999. (A era da informação: economia, sociedade e cultura, v. 1).
