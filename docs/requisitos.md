# Requisitos do Sistema

## Introdução

Este documento reúne os requisitos do **Assistente Inteligente para Gestão da Cooperativa Sabor da Terra**, desenvolvido no Projeto Intermediário da disciplina de IA Generativa e Agentes (UPE Garanhuns em parceria com a Sauter). O assistente atende a três necessidades da cooperativa: a triagem de pedidos escritos em linguagem natural, a consulta a documentos com respostas fundamentadas em fontes e a comunicação com os produtores.

Os requisitos estão divididos em funcionais (o que o sistema faz) e não funcionais (como ele deve se comportar). Eles seguem a proposta do projeto e descrevem a solução implementada.

**Legenda:** `RF` = requisito funcional · `RNF` = requisito não funcional.

---

## 1. Requisitos Funcionais

### 1.1 Interface conversacional e sessão

| ID | Requisito |
|---|---|
| RF-01 | O sistema deve oferecer uma interface de chat por texto (Streamlit) para uso da equipe da cooperativa. |
| RF-02 | O sistema deve manter o contexto da conversa ao longo da sessão, identificada pelo telefone informado, e permitir iniciar uma nova conversa a qualquer momento. |
| RF-03 | O sistema deve permitir selecionar o perfil de acesso da sessão (Equipe, Produtor ou Comprador) e informar o telefone para identificar o produtor. |
| RF-04 | O sistema deve identificar a intenção de cada mensagem (triagem de pedido, consulta documental, consulta ou comunicação com produtores, ou assunto geral) e, diante de mensagem ambígua, fazer uma pergunta objetiva de esclarecimento. |
| RF-05 | O sistema deve exibir junto à resposta as fontes citadas e o pedido estruturado em JSON, e oferecer atalhos de teste com cenários do gabarito. |

### 1.2 Interpretação e triagem de pedidos

| ID | Requisito |
|---|---|
| RF-06 | O sistema deve receber pedidos em português coloquial, com abreviações, erros de digitação e informações implícitas, informando também o canal (e-mail, WhatsApp ou formulário web) e o remetente. |
| RF-07 | O sistema deve devolver o pedido em JSON validado por schema, com tipo da mensagem, comprador, canal, itens (produto, quantidade, unidade, observação, exige orgânico), prazo, urgência, justificativa, problemas, confiança e perguntas de esclarecimento. |
| RF-08 | O sistema deve classificar cada mensagem como pedido de compra, cotação, consulta documental, mensagem de produtor, notificação oficial ou outro. |
| RF-09 | O sistema deve normalizar os produtos pelo catálogo oficial sem assumir termos genéricos ("queijo", "cheiro verde"). Para "o de sempre" ou "da última vez", deve consultar o histórico de lotes antes de assumir qualquer item e, havendo dúvida, gerar perguntas de esclarecimento. |
| RF-10 | O sistema deve calcular em código os prazos explícitos e relativos (por exemplo, "sexta") e alertar quando o dia da semana não corresponde à data informada. |
| RF-11 | O sistema deve classificar a urgência do pedido (alta, média ou baixa) e justificar a classificação. |
| RF-12 | O sistema deve sinalizar em `problemas` os pedidos com produto fora de safra, certificação orgânica vencida, inexistente ou prestes a vencer, quantidade acima da capacidade, ausência ou divergência de contrato e preço fora das condições contratuais. |
| RF-13 | O sistema deve identificar o remetente cruzando telefone ou e-mail com o cadastro de produtores. |
| RF-14 | O sistema deve tratar mensagens que não são compra (notificações da ADAGRO, ofertas de estoque, indicação de cadastro de terceiros), separar múltiplas intenções da mesma mensagem e processar mensagens em inglês. |
| RF-15 | O sistema deve encaminhar para decisão humana notificações oficiais, pedidos de dados bancários ou PIX, cadastro de terceiros e pedidos urgentes sem contrato ou acima da capacidade. |
| RF-16 | O sistema deve gerar cotações e orçamentos preliminares com a tabela de preços vigente, considerando preço convencional ou orgânico e desconto de atacado por volume. |

### 1.3 Consulta inteligente à base documental

| ID | Requisito |
|---|---|
| RF-17 | O sistema deve indexar, por seção, os documentos da cooperativa (certificações, laudos, inspeção ADAGRO, contratos e fichas técnicas) e permitir busca semântica com filtro opcional por produtor e tipo de documento. |
| RF-18 | O sistema deve responder com base apenas nos trechos recuperados e citar, em cada resposta, o arquivo e a seção de origem. |
| RF-19 | Quando não encontrar a informação nos documentos, o sistema deve informar isso claramente, sem inventar resposta. |
| RF-20 | O sistema deve verificar a vigência da certificação orgânica de um produtor, em um produto e em uma data de referência. |
| RF-21 | O sistema deve informar a sazonalidade dos produtos por mês (alta, média, baixa ou nenhuma). |
| RF-22 | O sistema deve listar produtores com filtros por produto, município, certificação orgânica válida e status ativo, sem expor dados pessoais ou bancários. |
| RF-23 | O sistema deve informar as vendas, o saldo a receber e as pendências financeiras de um produtor em um período. |
| RF-24 | O sistema deve rastrear um lote entregue (produtor, produto, quantidade, comprador, pedido, datas, temperatura de transporte e inspeção), aceitando o código completo ou só o número. |

### 1.4 Comunicação com produtores

| ID | Requisito |
|---|---|
| RF-25 | O sistema deve gerar, sob solicitação, um resumo personalizado para cada produtor, com vendas, entregas e pendências financeiras. |
| RF-26 | O sistema deve redigir a notificação de novo pedido, com produto, quantidade, prazo, comprador e próximos passos, incluindo apenas os itens que o produtor produz. As mensagens devem ser curtas e cordiais, adequadas ao WhatsApp. |
| RF-27 | Se o modelo de linguagem estiver indisponível ou gerar texto inválido, o sistema deve usar um texto padrão montado em código e informar a origem do texto (modelo ou texto padrão). |

### 1.5 Segurança e controle de acesso

| ID | Requisito |
|---|---|
| RF-28 | O sistema deve aplicar controle de acesso por perfil. A Equipe tem acesso completo; o Produtor só consulta vendas, saldo e resumo do próprio cadastro, e pedidos de dados de terceiros devem ser negados com mensagem explicativa. |
| RF-29 | O sistema nunca deve exibir CPF, agência, conta bancária ou chave PIX completos. CNPJ da cooperativa e código de lote são dados públicos e podem ser exibidos. |
| RF-30 | O sistema deve tratar mensagens de clientes, observações de pedidos e trechos de documentos como dado literal, ignorando comandos embutidos, e sinalizar na triagem as tentativas de injeção de comandos. |

---

## 2. Requisitos Não Funcionais

| ID | Requisito |
|---|---|
| RNF-01 | **Mascaramento em camadas.** Dados sensíveis devem ser protegidos em várias etapas: as consultas não retornam colunas sensíveis, os trechos do RAG são mascarados, e as respostas do modelo e as saídas da triagem passam por mascaramento final (expressões regulares e valores conhecidos dos CSVs). |
| RNF-02 | **Permissões em código.** O controle de acesso deve ser verificado em código antes da execução das ferramentas sensíveis, sem depender apenas da instrução dada ao modelo. |
| RNF-03 | **Determinismo.** O modelo de linguagem deve apenas interpretar e redigir texto. Cálculos, datas, saldos e regras de negócio devem ser feitos em código Python, com data de referência configurável (`DATA_REFERENCIA`) para resultados repetíveis. |
| RNF-04 | **Saída estruturada e estável.** A triagem deve usar schema com validação estrita, versão congelada de schema e de prompt (verificação por hash) e baixa temperatura (0,1). |
| RNF-05 | **Respostas sem invenção.** Sem trecho com similaridade mínima (0,7), a busca documental não deve acionar o modelo. |
| RNF-06 | **Conferência dos textos gerados.** Mensagens para produtores devem ser descartadas se citarem valores em reais fora dos fatos calculados, vierem vazias ou passarem de 1.200 caracteres. |
| RNF-07 | **Limite de chamadas.** O agente deve limitar a 3 chamadas ao modelo por pergunta, respondendo com pedido de reformulação ao exceder. |
| RNF-08 | **Resiliência.** As chamadas ao modelo devem repetir com espera exponencial (até 4 tentativas em erros 429 e 5xx), usar modelo reserva na triagem e na comunicação, e respeitar tempo limite de 30 s na redação de mensagens. |
| RNF-09 | **Economia de cota.** O sistema deve reduzir o consumo da faixa gratuita com cache de embeddings de consultas, cache de respostas para testes (`USE_TEST_CACHE`), embeddings em lotes de até 100 textos e limite de 10 trechos por busca (5 por arquivo). |
| RNF-10 | **Funcionamento sem o modelo.** O módulo de comunicação deve operar sem o modelo de linguagem (`SABOR_SEM_LLM=1`), degradando para texto padrão. |
| RNF-11 | **Usabilidade.** A interface deve ser em português do Brasil, com linguagem simples, mensagens aos produtores de até 8 linhas e painéis expansíveis que mostram as fontes e o JSON do pedido. |
| RNF-12 | **Observabilidade.** O sistema deve registrar em log as chamadas ao modelo, as ferramentas executadas, os acessos negados e os mascaramentos aplicados. |
| RNF-13 | **Testabilidade.** O sistema deve ter testes automatizados (pytest) e avaliação com gabarito (`eval/gabarito_v0.json`) cobrindo pedidos, perguntas documentais e cenários de segurança. |
| RNF-14 | **Modularidade e configuração.** O código deve ser separado em módulos (`assistent/`, `rag/`, `tools/`, `ui/`) e configurável por variáveis de ambiente (`GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_MODEL_RESERVA`, `PASTA_DADOS`, `DATA_REFERENCIA`), com a chave de API fora do repositório. |
| RNF-15 | **Tecnologia e portabilidade.** A solução deve usar Python, Google ADK, Gemini e `gemini-embedding-001`, com ChromaDB local (criado por `python INICIARBANCO.py`). Deve rodar em Windows, Linux e macOS e permitir migrar para o Vertex AI sem reescrever a lógica de negócio. |

---

