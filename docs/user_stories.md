# User Stories — Assistente Inteligente Sabor da Terra

Este documento descreve as histórias de usuário do **Assistente Inteligente para Gestão da Cooperativa Sabor da Terra** sob a perspectiva de quem utilizará a solução no dia a dia (equipe da cooperativa, produtores rurais e compradores). As referências `RF` e `RNF` apontam para o documento de Requisitos do Sistema.

## US01 - Selecionar perfil de acesso e iniciar atendimento no chat

Como usuário da plataforma (membro da equipe da cooperativa, produtor rural ou comprador), quero selecionar meu perfil de acesso e informar meu telefone ao iniciar o chat, para que o assistente reconheça quem sou e adapte o atendimento ao meu papel.

**Requisitos:** RF-01, RF-02, RF-03, RNF-11.

**Critérios de aceitação:**

* A interface web exibe um seletor de perfil de acesso (`Equipe`, `Produtor` ou `Comprador`) e um campo para informar o telefone de identificação.
* Toda a interface, botões, avisos e mensagens padrão são apresentados em português do Brasil com linguagem simples e direta.
* Durante uma mesma sessão, o assistente mantém o contexto das mensagens anteriores vinculadas ao telefone informado.
* Ao acionar a opção de **Nova Conversa**, o histórico atual da tela é limpo para iniciar um novo atendimento a qualquer momento.
* Enquanto o assistente processa uma solicitação, a tela exibe um indicador visual de carregamento até apresentar a resposta.

## US02 - Inspecionar fontes citadas, dados estruturados e atalhos de teste

Como membro da equipe da cooperativa, quero visualizar as fontes consultadas e os dados estruturados extraídos de cada solicitação, além de utilizar atalhos rápidos de demonstração, para auditar as respostas e validar o comportamento do atendimento.

**Requisitos:** RF-05, RNF-11, RNF-13.

**Critérios de aceitação:**

* Sempre que uma resposta utilizar documentos da cooperativa, a interface exibe um painel recolhível de **Fontes Citadas** com os arquivos consultados.
* Sempre que uma mensagem passar pela triagem de pedidos, a interface exibe um painel recolhível de **Pedido Estruturado** apresentando os dados organizados em formato padronizado (JSON).
* Os painéis recolhíveis de fontes e pedido estruturado permanecem disponíveis no histórico da conversa para consulta posterior.
* A barra lateral oferece atalhos de disparo rápido para cenários representativos (divergência de data, pedido urgente sem contrato, consulta de certificação e bloqueio de acesso a dados de terceiros).

## US03 - Identificar a intenção da mensagem e esclarecer pedidos vagos

Como operador da cooperativa, quero que o assistente identifique automaticamente o objetivo de cada mensagem recebida e faça perguntas objetivas quando houver ambiguidade, para encaminhar cada demanda corretamente sem adivinhar o que o remetente quis dizer.

**Requisitos:** RF-04, RF-08, RNF-07.

**Critérios de aceitação:**

* O assistente identifica se a mensagem trata de triagem de pedido/cotação, consulta a documentos, consulta/comunicação com produtores ou assunto geral.
* Cada mensagem analisada na triagem é classificada em: `pedido de compra`, `cotacao`, `consulta documental`, `mensagem de produtor`, `notificacao oficial` ou `outro`.
* Diante de mensagens vagas ou incompletas, o assistente formula uma pergunta curta e objetiva de esclarecimento antes de assumir itens ou prazos.
* Saudações ou dúvidas gerais sobre o sistema são respondidas diretamente, sem realizar buscas desnecessárias na base de dados.
* Caso uma solicitação exija raciocínio excessivo ou ultrapasse o limite de etapas por turno, o assistente solicita que o usuário reformule a pergunta de forma mais objetiva.

## US04 - Estruturar pedidos recebidos em linguagem informal

Como operador da cooperativa, quero transformar mensagens escritas de forma coloquial por diferentes canais em um registro organizado e padronizado, para agilizar a triagem mesmo quando houver abreviações, gírias ou erros de digitação.

**Requisitos:** RF-06, RF-07, RNF-04.

**Critérios de aceitação:**

* O sistema interpreta pedidos escritos em português coloquial considerando o canal de origem (`e-mail`, `WhatsApp` ou `formulário web`) e o remetente.
* A análise organiza os dados em uma estrutura fixa contendo tipo da mensagem, comprador, canal, itens solicitados, prazo, urgência, justificativa, problemas identificados, nível de confiança e perguntas de esclarecimento.
* Cada item extraído detalha o nome padronizado do produto, a quantidade, a unidade de medida, eventuais observações e se há exigência de produto orgânico.
* O formato estruturado mantém estabilidade e previsibilidade mesmo diante de variações na forma como o cliente escreve.

## US05 - Padronizar produtos pelo catálogo e consultar histórico antes de assumir itens

Como operador da cooperativa, quero que os nomes dos produtos sejam padronizados conforme o catálogo oficial sem que o assistente adivinhe variedades genéricas ou pedidos recorrentes, para evitar erros na separação e na entrega.

**Requisitos:** RF-09, RNF-03.

**Critérios de aceitação:**

* Variações de escrita e acentuação são padronizadas de acordo com o catálogo oficial da cooperativa (por exemplo, reconciliando variações de goiaba ou tomate).
* Termos genéricos como `"queijo"`, `"manteiga"` ou `"cheiro verde"` não são convertidos arbitrariamente em um item específico; o sistema preserva o termo e gera uma pergunta de esclarecimento.
* Quando o comprador solicita `"o de sempre"` ou `"da última vez"`, o sistema consulta obrigatoriamente o histórico de lotes entregues para aquele cliente antes de preencher os itens.
* Caso não exista histórico claro ou haja pedidos anteriores diferentes, o assistente abstém-se de assumir itens e solicita confirmação ao comprador.

## US06 - Interpretar prazos e alertar conflitos entre data e dia da semana

Como operador da cooperativa, quero que prazos explícitos e relativos sejam calculados com exatidão no calendário e conferidos quanto à coerência, para identificar datas inválidas ou divergências entre o dia da semana e a data escrita pelo cliente.

**Requisitos:** RF-10, RNF-03.

**Critérios de aceitação:**

* Expressões relativas como `"hoje"`, `"amanhã"` ou `"sexta"` são convertidas automaticamente para data exata com base na data de referência do atendimento.
* Quando o remetente informa um dia da semana que não coincide com a data escrita no calendário (por exemplo, `"sexta (01/nov)"` em um ano em que dia 1º é domingo), o sistema registra um alerta explícito nos problemas do pedido.
* Datas inexistentes no calendário (como 30 de fevereiro) são rejeitadas e geram alerta e pergunta de esclarecimento.
* Quando o pedido não menciona nenhum prazo de entrega, o sistema registra o prazo como indefinido e solicita a data desejada.

## US07 - Classificar e justificar a urgência das demandas

Como coordenador de logística, quero que cada pedido receba uma classificação clara de urgência acompanhada do motivo, para priorizar o atendimento de entregas imediatas.

**Requisitos:** RF-11, RNF-03.

**Critérios de aceitação:**

* Cada demanda recebe uma classificação padronizada de urgência: `alta`, `media` ou `baixa`.
* Pedidos com entrega prevista para o mesmo dia, para o dia seguinte ou com indicação explícita de emergência são classificados automaticamente como `alta` urgência.
* A triagem apresenta uma justificativa objetiva explicando o critério temporal ou contextual que motivou a classificação.
* Cotações exploratórias, consultas documentais ou pedidos com prazo dilatado recebem classificação compatível (`media` ou `baixa`).

## US08 - Verificar safra, certificação orgânica e capacidade produtiva na triagem

Como coordenador de produção, quero receber alertas automáticos durante a triagem quando um pedido envolver produto fora de safra, certificação orgânica irregular ou volume acima da nossa capacidade, para não assumir compromissos inviáveis.

**Requisitos:** RF-12, RF-20, RF-21, RNF-03.

**Critérios de aceitação:**

* O sistema consulta a sazonalidade do produto no mês da entrega e alerta nos problemas do pedido quando a oferta for `baixa` ou estiver fora de safra (`nenhuma`).
* Quando o pedido ou o contrato do comprador exigir produto orgânico, o sistema verifica se há produtores ativos com certificação válida e alerta caso esteja vencida, ausente ou próxima do vencimento (dentro de 60 dias).
* Volumes solicitados acima da capacidade semanal da cooperativa registrada nas fichas técnicas geram alerta automático nos problemas do pedido.
* Produtos que não possuem opção orgânica cadastrada na tabela de preços geram aviso específico de indisponibilidade.

## US09 - Conferir contratos e condições comerciais dos compradores

Como gestor comercial, quero que a triagem verifique se o comprador possui contrato vigente e se o pedido respeita as regras acordadas, para evitar divergências de preço, prazo ou forma de pagamento.

**Requisitos:** RF-12, RNF-03.

**Critérios de aceitação:**

* Ao identificar o comprador, o sistema verifica se existe contrato ativo registrado na base da cooperativa (como Mercado Bom Preço, PNAE Garanhuns ou Restaurante Raízes).
* Pedidos com pagamento faturado (como boleto de 30 dias) feitos por compradores sem contrato ativo geram alerta nos problemas do pedido.
* O sistema confronta prazos mínimos de antecedência, exigência de certificação orgânica, forma de pagamento e valores solicitados com as cláusulas do contrato correspondente.
* Qualquer divergência comercial encontrada é detalhada objetivamente na lista de problemas da triagem.

## US10 - Reconhecer produtores remetentes e lidar com mensagens atípicas ou em inglês

Como operador da cooperativa, quero identificar automaticamente produtores que enviam mensagens, interpretar pedidos em inglês e separar múltiplas intenções em um mesmo texto, para tratar adequadamente todo tipo de contato recebido.

**Requisitos:** RF-08, RF-13, RF-14, RNF-03.

**Critérios de aceitação:**

* Ao receber uma mensagem, o sistema cruza o telefone ou e-mail do remetente com o cadastro da cooperativa para identificar automaticamente se pertence a um produtor associado.
* Mensagens que não representam pedidos de compra — como notificações oficiais da ADAGRO, ofertas de excedente de safra ou indicações de cadastro de terceiros — são classificadas corretamente sem gerar itens falsos de compra.
* Quando uma mesma mensagem reúne duas intenções distintas (por exemplo, um produtor confirmando entrega e pedindo o cadastro de um vizinho), o sistema separa a demanda principal e registra a intenção secundária nos problemas/pendências.
* Pedidos escritos em inglês são compreendidos e têm seus itens, quantidades e prazos normalizados para o catálogo em português.

## US11 - Sinalizar demandas críticas ou sensíveis para decisão humana

Como supervisor da cooperativa, quero que notificações oficiais, solicitações envolvendo dados bancários ou PIX, pedidos de cadastro de terceiros e urgências críticas sejam encaminhados para avaliação humana, para garantir governança nas decisões de maior risco.

**Requisitos:** RF-15, RNF-03.

**Critérios de aceitação:**

* Notificações oficiais de órgãos sanitários ou de fiscalização (como a ADAGRO) geram alerta obrigatório de encaminhamento para decisão humana.
* Solicitações que peçam documentos, dados pessoais, dados bancários ou chave PIX de produtores são bloqueadas para envio automático e encaminhadas à equipe.
* Pedidos de inclusão ou cadastro de novos produtores ou terceiros na cooperativa são sinalizados para análise administrativa.
* Pedidos classificados com `alta` urgência que apresentem ausência de contrato ou volume acima da capacidade produtiva recebem alerta de escalonamento humano.

## US12 - Gerar cotações preliminares com regras de orgânicos e descontos de atacado

Como operador comercial, quero calcular orçamentos preliminares com base na tabela de preços vigente, aplicando valores convencionais ou orgânicos e descontos por volume, para responder rapidamente a cotações sem erros de conta.

**Requisitos:** RF-16, RNF-03.

**Critérios de aceitação:**

* Os preços unitários são obtidos exclusivamente da tabela de preços vigente da cooperativa, com todos os cálculos realizados com precisão matemática pelo sistema.
* O cálculo aplica o preço orgânico quando o item exigir certificação orgânica e o preço convencional nos demais casos.
* O percentual de desconto de atacado é aplicado automaticamente sempre que a quantidade cotada atingir o volume mínimo exigido para o produto.
* Produtos sem preço disponível na modalidade solicitada retornam aviso claro de indisponibilidade, sem assumir valor zero.

## US13 - Consultar documentos internos por assunto, produtor ou categoria

Como funcionário da cooperativa, quero pesquisar informações em certificações, laudos sanitários, relatórios de inspeção, contratos e fichas técnicas usando linguagem natural e filtros, para encontrar regras e comprovações sem ler dezenas de arquivos manualmente.

**Requisitos:** RF-17, RNF-05, RNF-09, RNF-15.

**Critérios de aceitação:**

* A busca documental pesquisa por seção nos documentos da cooperativa (certificações orgânicas, laudos sanitários, inspeção da ADAGRO, contratos e fichas técnicas).
* A consulta permite filtrar os resultados por produtor específico ou por categoria de documento.
* O sistema retorna apenas trechos com alta relevância para a pergunta realizada, limitando a quantidade de fragmentos por consulta e por arquivo para manter agilidade e economia de recursos.
* Caso a base de documentos ainda não tenha sido preparada para busca, o sistema exibe orientação clara sobre como inicializá-la.

## US14 - Receber respostas documentais com citação de fonte e sem invenções

Como funcionário da cooperativa, quero que toda resposta baseada nos documentos da cooperativa informe exatamente o arquivo e a seção de origem, e avise claramente quando a informação não existir, para tomar decisões seguras e auditáveis.

**Requisitos:** RF-18, RF-19, RNF-05.

**Critérios de aceitação:**

* Quando nenhum trecho dos documentos atingir o nível mínimo de relevância para a pergunta, o sistema informa claramente que a informação não foi encontrada, sem tentar completar a resposta por suposição.
* O assistente fundamenta suas respostas estritamente nos trechos localizados nos documentos da cooperativa.
* Toda resposta documental cita explicitamente o nome do arquivo e a seção de origem de cada informação apresentada.
* Perguntas que cruzam regras de diferentes arquivos (como exigências contratuais e validade de certificados) mantêm a citação de todas as fontes envolvidas.

## US15 - Consultar produtores aptos, vigência de certificações e calendário de safra

Como operador da cooperativa, quero filtrar produtores ativos por produto, município e certificação orgânica válida, além de consultar a disponibilidade mensal de cada cultura, para identificar rapidamente quem pode atender a um pedido.

**Requisitos:** RF-20, RF-21, RF-22, RNF-01.

**Critérios de aceitação:**

* A consulta de produtores permite filtrar por produto cultivado, município, exigência de certificação orgânica válida e status ativo (excluindo automaticamente produtores inativos).
* A listagem exibe apenas dados operacionais permitidos, sem expor CPF, contatos ou dados bancários dos cooperados.
* A verificação de certificação confirma se o certificado orgânico do produtor está vigente para o produto e a data de referência, emitindo aviso preventivo caso vença em até 60 dias.
* A consulta de sazonalidade informa o nível de oferta mensal (`alta`, `media`, `baixa` ou `nenhuma`) e as observações cadastradas para o produto.

## US16 - Consultar vendas, saldos financeiros e rastrear lotes entregues

Como analista financeiro ou operador de qualidade, quero consultar o histórico de vendas, os valores a receber ou vencidos de cada produtor e os detalhes de rastreabilidade dos lotes entregues, para acompanhar os repasses financeiros e o controle sanitário das entregas.

**Requisitos:** RF-23, RF-24, RNF-02, RNF-03.

**Critérios de aceitação:**

* A consulta de vendas calcula os totais comercializados pelo produtor permitindo filtrar por ano, mês, intervalo de datas ou histórico completo.
* A consulta de saldo a receber separa pagamentos já efetuados das pendências, classificando-as em **vencidas** ou **a vencer** conforme a data de referência.
* O rastreamento de lote aceita tanto o código completo (ex.: `LOT-2026-0089`) quanto apenas o número final (ex.: `89`).
* O detalhe do lote apresenta produtor, produto, quantidade e unidade, comprador, pedido associado, datas de colheita, entrega e validade, temperatura de transporte e resultado da inspeção visual.

## US17 - Gerar resumo financeiro e operacional personalizado para o produtor

Como produtor rural associado (ou funcionário atendendo um produtor), quero gerar um resumo curto, cordial e confiável com minhas vendas, entregas realizadas e pendências financeiras, para acompanhar meus pagamentos diretamente pelo WhatsApp.

**Requisitos:** RF-25, RF-28, RNF-03, RNF-06, RNF-11.

**Critérios de aceitação:**

* Todos os valores monetários, datas e quantidades são calculados previamente pelo sistema antes da redação da mensagem.
* O resumo gerado é cordial, escrito em português claro e limitado a no máximo 8 linhas e 1.200 caracteres, adequado para envio por mensagem.
* O sistema confere o texto antes de exibi-lo e descarta a redação caso contenha valores em reais divergentes dos números calculados.
* Quando utilizado com perfil `Produtor`, o sistema gera apenas o resumo referente ao próprio cadastro vinculado ao telefone informado.

## US18 - Redigir notificações de novos pedidos para WhatsApp com contingência

Como operador da cooperativa, quero gerar mensagens curtas e cordiais para avisar produtores sobre novos pedidos contendo apenas os itens que cada um cultiva, com garantia de funcionamento mesmo se a inteligência artificial estiver indisponível, para agilizar a mobilização das entregas.

**Requisitos:** RF-26, RF-27, RNF-06, RNF-08, RNF-10, RNF-11.

**Critérios de aceitação:**

* A mensagem inclui exclusivamente os produtos do pedido que o produtor destinatário cultiva, informando quantidade, prazo, comprador e próximos passos.
* Caso algum item exija certificação orgânica e o produtor não possua certificação válida na data de referência, a notificação inclui um alerta sobre essa pendência.
* Textos que mencionem valores em reais não previstos ou ultrapassem 1.200 caracteres são descartados automaticamente.
* Se o serviço de inteligência artificial estiver desativado, lento (acima de 30 segundos) ou indisponível, o sistema monta automaticamente um texto padrão e informa se a mensagem foi gerada pelo assistente ou pelo modelo padrão.

## US19 - Restringir acesso a dados financeiros por perfil de usuário

Como administrador de segurança da cooperativa, quero garantir que as permissões de cada perfil sejam aplicadas rigorosamente antes de qualquer consulta financeira, para impedir que um produtor acesse vendas, saldos ou resumos de outros cooperados.

**Requisitos:** RF-03, RF-28, RNF-02.

**Critérios de aceitação:**

* O controle de acesso valida o perfil e o telefone do usuário antes de liberar qualquer consulta de vendas, saldo a receber ou resumo financeiro.
* Usuários com perfil `Equipe` têm acesso completo para consultar informações operacionais e financeiras de qualquer produtor.
* Usuários com perfil `Produtor` só podem consultar vendas, saldos e resumos vinculados ao seu próprio cadastro.
* Qualquer tentativa de um produtor consultar dados financeiros de outro cooperado é bloqueada imediatamente com mensagem explicativa, mesmo diante de pedidos insistentes na conversa.

## US20 - Proteger dados pessoais e bancários em todas as etapas do atendimento

Como encarregado de proteção de dados (LGPD) da cooperativa, quero ocultar automaticamente CPF, agência, conta bancária e chave PIX em consultas, documentos e respostas do chat, preservando dados públicos como o CNPJ da cooperativa e códigos de lote, para garantir a privacidade dos cooperados.

**Requisitos:** RF-22, RF-29, RNF-01.

**Critérios de aceitação:**

* Consultas cadastrais omitem dados sensíveis (CPF, data de nascimento, telefone, e-mail, endereço, banco, agência, conta e chave PIX) desde a origem.
* Trechos recuperados de documentos passam por mascaramento automático antes de serem utilizados na elaboração de respostas.
* Todas as respostas finais do chat, triagens e notificações passam por revisão final para ofuscar qualquer CPF, dado bancário ou chave PIX remanescente.
* Informações públicas da cooperativa, como seu CNPJ e os códigos de rastreamento de lotes, permanecem legíveis sem ofuscação.

## US21 - Proteger o atendimento contra comandos ocultos em mensagens e documentos

Como administrador de segurança da cooperativa, quero que mensagens de clientes, observações de pedidos e textos de documentos sejam tratados estritamente como dados informativos, para impedir que instruções maliciosas alterem as regras do sistema ou exponham dados restritos.

**Requisitos:** RF-30, RNF-04.

**Critérios de aceitação:**

* O conteúdo vindo de mensagens externas, observações de pedidos ou documentos é isolado como dado informativo, separado das regras operacionais do assistente.
* O assistente ignora comandos embutidos em textos externos que tentem alterar permissões, revelar instruções internas ou contornar restrições de acesso.
* Tentativas de manipulação ou injeção de comandos detectadas em mensagens são sinalizadas explicitamente na lista de problemas da triagem.

## US22 - Garantir continuidade, auditoria e fácil manutenção da operação

Como gestor e equipe técnica da cooperativa, quero que o sistema opere com estabilidade diante de oscilações externas, registre eventos importantes para auditoria e permita configuração flexível e testes automatizados, para manter o atendimento confiável e preparado para evolução.

**Requisitos:** RNF-08, RNF-09, RNF-12, RNF-13, RNF-14, RNF-15.

**Critérios de aceitação:**

* Diante de falhas temporárias ou limites de uso do serviço de inteligência artificial, o sistema realiza novas tentativas automáticas e aciona um modelo alternativo de contingência.
* Consultas frequentes reaproveitam resultados em cache para manter respostas rápidas e economizar recursos.
* O sistema registra em histórico de auditoria (logs) as interações realizadas, consultas executadas, acessos negados e proteções de dados aplicadas.
* Parâmetros operacionais (como chaves de acesso, modelos, diretório de dados e data de referência) podem ser configurados externamente sem alterar o código, com suporte a testes automatizados e execução em Windows, Linux e macOS.