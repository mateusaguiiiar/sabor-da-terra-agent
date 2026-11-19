# Arquitetura e Decisões Tecnológicas — Assistente Sabor da Terra

Este documento descreve a arquitetura de software, as escolhas de stack tecnológica e as justificativas técnicas adotadas no desenvolvimento do **Assistente Inteligente da Cooperativa Sabor da Terra**, comparando nossa abordagem com alternativas tradicionais de mercado — em especial o ecossistema gerenciado do **Google Cloud Vertex AI**.

---

## 1. Visão Geral da Arquitetura

O sistema foi projetado sob uma arquitetura **modular, *code-first* e orientada a ferramentas (*Tool-Use / Function Calling*)**, dividida em cinco camadas principais:

1. **Frontend e Controle de Sessão:** Interface conversacional web com autenticação simulada baseada em papéis (**RBAC**).
2. **Orquestração e Guardrails:** Agente central responsável pelo roteamento de intenções, controle de turnos, isolamento contra *Prompt Injection* e mascaramento de dados sensíveis (**PII**).
3. **Módulo de Ferramentas (*Tools*):** Funções determinísticas em Python para triagem de pedidos, cálculos financeiros, validações contratuais/sanitárias e geração de comunicados.
4. **Pipeline RAG e Dados Híbridos:** Combinação de busca vetorial semântica (documentos não estruturados) com consultas determinísticas (bases tabulares e JSON).
5. **Serviço de LLM:** Inferência via API para compreensão de linguagem natural, extração estruturada e síntese de respostas.

---

## 2. Resumo Comparativo: Stack Adotada vs. Alternativas (Vertex AI e Mercado)

| Camada | Stack Adotada | Alternativas Vertex AI | Outras Alternativas | Principal Vantagem da Escolha |
| :--- | :--- | :--- | :--- | :--- |
| **Orquestração de Agentes** | **Google ADK (`google-adk`)** | Vertex AI Agent Builder / Dialogflow CX | LangChain, LangGraph, CrewAI | Controle total em código Python, callbacks nativos de guarda e zero *lock-in* de console no-code. |
| **LLM & Inferência** | **Google Gemini API (`google-genai` / `gemini-3.5-flash-lite`)** | Vertex AI Model Garden / Endpoints GCP | OpenAI API, Anthropic Claude | Configuração imediata via API Key, baixíssima latência e custo operacional mínimo sem burocracia de IAM/GCP. |
| **Banco Vetorial (RAG)** | **ChromaDB (Embarcado) + Pipeline Customizado** | Vertex AI Vector Search / Vertex AI Search | Pinecone, Weaviate, Qdrant | Custo fixo zero (sem clusters ativos 24/7) e controle granular sobre *chunking*, citações e máscara de PII. |
| **Dados Estruturados** | **CSV / JSON + Python + Pydantic v2** | BigQuery / Cloud SQL / Firestore | PostgreSQL, MongoDB | Simplicidade operacional, execução instantânea em memória e validação estrita de regras de negócio. |
| **Frontend / UI** | **Streamlit** | Gemini Enterprise / Dialogflow Messenger | React / Next.js + FastAPI | Desenvolvimento 100% em Python com painéis de auditoria (JSON e fontes) nativos e alta velocidade de entrega. |
| **Segurança & Privacidade** | **Callbacks ADK + Regex/Mascaramento Local** | Vertex AI Model Armor + Cloud DLP | Guardrails AI, NeMo Guardrails | Proteção determinística em milissegundos, sem custo por requisição/byte inspecionado e sem envio de PII externo. |

---

## 3. Análise Detalhada por Camada

### 3.1. Orquestração: Google ADK vs. Vertex AI Agent Builder & LangChain

* **O que usamos:** `google-adk` (Agent Development Kit) com um agente raiz (`root_agent`) e callbacks de ciclo de vida (`before_model_guard`, `after_model_logger`, `log_tool_execution`).
* **Por que não Vertex AI Agent Builder / Dialogflow CX?**
  * Ferramentas visuais/gerenciadas como o *Vertex AI Agent Builder* aceleram fluxos simples, mas engessam regras complexas de negócio (como validação cruzada de calendário, capacidade semanal por produtor e regras do PNAE) dentro de fluxos visuais difíceis de versionar no Git e testar unitariamente.
  * Com o **Google ADK**, toda a lógica vive em código Python versionado, permitindo testes automatizados com `pytest` a cada *pull request*.
* **Por que não LangChain / CrewAI?**
  * Frameworks como LangChain introduzem múltiplas camadas de abstração que dificultam a depuração e aumentam o consumo de tokens. O ADK oferece integração direta e enxuta com o *function calling* nativo do Gemini.
  * Além disso, o ADK mantém compatibilidade direta caso a cooperativa decida futuramente hospedar o agente no **Vertex AI Agent Engine**, sem necessidade de reescrever as ferramentas.

---

### 3.2. Modelo de Linguagem: Gemini API (`google-genai`) vs. Vertex AI Endpoints

* **O que usamos:** SDK oficial `google-genai` consumindo o modelo `gemini-3.5-flash-lite` com *Structured Outputs* (JSON Schema derivado de modelos Pydantic).
* **Vantagens frente ao Vertex AI Model Garden / Endpoints:**
  * **Agilidade de implantação e governança simplificada:** O consumo direto via `GEMINI_API_KEY` elimina a necessidade de configurar projetos GCP, contas de serviço (*Service Accounts*), políticas de IAM, VPCs e cotas regionais durante o ciclo de desenvolvimento e operação inicial da cooperativa.
  * **Eficiência de custo e latência:** A família *Flash-Lite* foi escolhida por entregar excelente precisão na extração de entidades e chamada de ferramentas com latência mínima e custo por milhão de tokens significativamente inferior a modelos de grande porte ou endpoints dedicados no Vertex AI.
  * **Conformidade de Schema:** O uso de schemas JSON validados garante que a triagem de pedidos retorne estruturas previsíveis, mitigando falhas de *parsing*.

---

### 3.3. Pipeline RAG: ChromaDB Customizado vs. Vertex AI Search / Vector Search

* **O que usamos:** Pipeline próprio em Python (`rag/`) com divisão semântica por seções de documentos, embeddings via API e persistência local em **ChromaDB** (`data/chroma/`).
* **Vantagens frente ao Vertex AI Vector Search (Matching Engine):**
  * **Ausência de custo de infraestrutura ociosa:** O *Vertex AI Vector Search* exige o provisionamento de nós e índices hospedados continuamente, gerando custos fixos mensais elevados mesmo em períodos de baixo volume de consultas. O ChromaDB roda embarcado em disco com custo de infraestrutura zero.
* **Vantagens frente ao Vertex AI Search (solução "caixa-preta"):**
  * **Auditabilidade e citação exata:** Nosso pipeline preserva metadados estruturados (nome do arquivo e seção específica) para exibir exatamente de onde cada regra sanitária (ADAGRO), certificação orgânica ou cláusula contratual foi extraída.
  * **Privacidade antes da geração:** Aplicamos regras de mascaramento (`funcao_mascara.py`) nos trechos recuperados **antes** que eles sejam injetados no contexto do LLM, evitando vazamento acidental de CPFs ou dados bancários presentes em contratos e cadastros.

---

### 3.4. Dados Estruturados e Regras de Negócio: CSV/JSON + Pydantic vs. BigQuery / Cloud SQL

* **O que usamos:** Arquivos tabulares (`produtores.csv`, `financeiro.csv`, `lotes.csv`, `sazonalidade.csv`, `tabela_precos_outubro_2026.csv`) e `pedidos.json`, manipulados em Python com validação via **Pydantic v2**.
* **Vantagens frente a BigQuery e Cloud SQL:**
  * **Sem *overhead* de banco gerenciado:** Instâncias gerenciadas de PostgreSQL/MySQL no *Cloud SQL* implicam custo contínuo de compute/storage, gerenciamento de conexões e migrações. Já o *BigQuery* é voltado para cargas analíticas (OLAP) e possui latência de inicialização inadequada para consultas transacionais pontuais em tempo real de chat.
  * **Determinismo matemático:** Modelos de linguagem não devem realizar cálculos financeiros ou validações de data por conta própria. Ao delegar preços, descontos de atacado, saldos e verificação de vencimento de certificados para funções Python validadas com Pydantic, garantimos **zero alucinação numérica**.

---

### 3.5. Interface Web: Streamlit vs. Gemini Enterprise / React + FastAPI

* **O que usamos:** Aplicação web em **Streamlit** (`ui/app.py`) com gerenciamento de estado de sessão (`st.session_state`), seletor de perfil RBAC e expansores de auditoria.
* **Vantagens frente ao Gemini Enterprise e Stacks Full-Stack (React + FastAPI):**
  * **Unificação de stack:** Toda a equipe trabalha exclusivamente em Python, sem necessidade de manter repositórios separados de frontend (TypeScript/React), APIs intermediárias (FastAPI) ou lidar com CORS e autenticação OAuth complexa nesta fase.
  * **Transparência operacional:** O Streamlit permitiu embutir nativamente painéis de inspeção técnica (**⚙️ Pedido Estruturado** em JSON e **📚 Fontes Citadas**), essenciais para que a equipe administrativa da cooperativa audite as decisões da IA.
  * **Independência de licenciamento:** Evita o custo por assento/usuário exigido por plataformas corporativas fechadas como o *Gemini Enterprise*.

---

### 3.6. Segurança, Guardrails e Testes: Callbacks Locais + Pytest vs. Cloud DLP / Model Armor

* **O que usamos:**
  * **RBAC na sessão e nas ferramentas:** Bloqueio estrito de acesso a dados financeiros de terceiros quando o perfil ativo é `produtor`.
  * **Mascaramento determinístico de PII:** Expressões regulares e filtros aplicados nas saídas das ferramentas para ocultar CPF, agência, conta bancária e chaves PIX.
  * **Proteção contra loops e *Prompt Injection*:** Delimitação explícita de textos externos (`<texto_pedido_externo>`) e limite de chamadas ao modelo por turno (`before_model_guard`).
  * **Qualidade contínua:** Mais de **117 testes automatizados** com `pytest` e script de avaliação com gabarito (`eval/rodar_avaliacao.py`).
* **Vantagens frente ao Cloud DLP e Vertex AI Model Armor:**
  * **Custo previsível e latência sub-milissegundo:** Serviços gerenciados como o *Cloud DLP* cobram por volume de dados inspecionados e adicionam chamadas de rede externas a cada mensagem. Nossa camada local executa instantaneamente, sem custo adicional e com cobertura total testada unitariamente.

---

## 4. Caminho de Evolução (Escalabilidade Futura)

Embora a stack atual tenha sido otimizada para **baixo custo, alta velocidade de desenvolvimento, auditabilidade e facilidade de execução local/on-premise**, a separação clara de responsabilidades permite evoluir gradualmente para uma arquitetura em nuvem caso o volume de produtores e pedidos da cooperativa cresça:

1. **Hospedagem do Agente:** Migrar o `root_agent` (já construído em Google ADK) para o **Vertex AI Agent Engine** ou **Cloud Run**.
2. **Persistência Transacional:** Substituir a leitura de CSVs em `tools/dados.py` por consultas a um banco **Cloud SQL (PostgreSQL)** sem alterar a assinatura das ferramentas nem as instruções do agente.
3. **Escala do RAG:** Migrar o índice local do ChromaDB para **pgvector (no Cloud SQL)** ou **Vertex AI Vector Search** caso o acervo documental ultrapasse dezenas de milhares de documentos.
4. **Observabilidade:** Conectar os callbacks `after_model_logger` e `log_tool_execution` diretamente ao **Google Cloud Logging / Cloud Trace**.