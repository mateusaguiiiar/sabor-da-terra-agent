# 🌱 Assistente Inteligente — Cooperativa Sabor da Terra

Assistente virtual desenvolvido para apoiar as operações da cooperativa agrícola fictícia **Sabor da Terra** (Agreste Meridional de Pernambuco). O sistema unifica triagem automatizada de pedidos, consulta semântica a documentos normativos e atendimento seguro aos produtores cooperados, compradores e equipe administrativa.

---

## 🚀 Principais Funcionalidades

* **Triagem Estruturada de Pedidos:** Extrai itens, quantidades, unidades, prazos e canais a partir de mensagens em linguagem natural (WhatsApp, e-mail ou formulário web) usando **Pydantic** e validações determinísticas de negócio (calendário, sazonalidade, capacidade semanal por produtor, certificações orgânicas, descontos de atacado e contratos vigentes).
* **Busca Documental com RAG:** Indexa e consulta contratos, certificações orgânicas, laudos sanitários (ADAGRO) e fichas técnicas utilizando busca vetorial com **ChromaDB**, citando os arquivos de origem nas respostas.
* **Consultas Operacionais e Financeiras:** Consulta catálogo de preços, vendas por produtor, saldo a receber, rastreabilidade de lotes e gera resumos comunicacionais.
* **Segurança, RBAC e Guardrails:**
  * **Controle de Acesso por Perfil (`equipe`, `produtor`, `comprador`):** Produtores autenticados acessam exclusivamente seus próprios registros financeiros e de vendas.
  * **Mascaramento de Dados Sensíveis (PII):** Ocultação automática de CPF, agência/conta bancária e chaves PIX nas saídas das ferramentas e do modelo.
  * **Proteção contra Prompt Injection e Loops:** Isolamento de textos externos e limite de chamadas ao modelo por turno de conversa.
* **Interface Interativa:** Aplicação web em **Streamlit** com seletor de perfil de acesso, histórico de sessão persistente, atalhos de teste e painéis de auditoria (JSON estruturado do pedido e fontes citadas).

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Orquestração do Agente:** [Google ADK (`google-adk`)](https://google.github.io/adk-docs/)
* **LLM & Embeddings:** Google Gemini API (`google-genai`)
* **Validação e Schemas:** Pydantic v2
* **Banco Vetorial (RAG):** ChromaDB
* **Interface Web:** Streamlit
* **Testes e Avaliação:** Pytest + suíte de avaliação automatizada (`eval/`)

---

## 📁 Estrutura do Projeto

```text
sabor-da-terra-agent/
├── assistent/               # Definição do agente ADK, callbacks de guarda e regras de RBAC
│   ├── agent.py
│   ├── callbacks.py
│   └── security.py
├── data/                    # Base de conhecimento (CSVs, JSONs, contratos, laudos e índice Chroma)
│   ├── certificacoes/
│   ├── chroma/
│   ├── contratos/
│   ├── fichas_tecnicas/
│   └── *.csv / pedidos.json
├── docs/                    # Documentação técnica dos módulos de dados e triagem
├── eval/                    # Gabarito e script de avaliação de qualidade do agente
├── rag/                     # Pipeline de leitura, chunking, embeddings, indexação e busca
├── scripts/                 # Scripts auxiliares de verificação da API e cenários de triagem
├── tests/                   # Testes unitários e de integração (Pytest)
├── tools/                   # Ferramentas do agente (triagem, consultas, comunicação e máscara)
├── ui/                      # Interface web em Streamlit
│   └── app.py
├── INICIARBANCO.py          # Script de criação/reconstrução do índice vetorial ChromaDB
├── pytest.ini               # Configuração do Pytest
└── requirements.txt         # Dependências do projeto
```

---

## 💻 Guia Completo de Instalação e Execução

### Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:
1. **Git**
2. **Python 3.11 ou superior** (no Windows, marque a opção *"Add Python to PATH"* durante a instalação)
3. Uma **chave de API do Google Gemini** (obtida no [Google AI Studio](https://aistudio.google.com/))

---

### Passo 1 — Clonar o repositório

Abra o terminal (Linux/macOS) ou o PowerShell / Prompt de Comando (Windows) e execute:

```bash
git clone [https://github.com/mateusaguiiiar/sabor-da-terra-agent.git](https://github.com/mateusaguiiiar/sabor-da-terra-agent.git)
cd sabor-da-terra-agent
```

---

### Passo 2 — Criar e ativar o ambiente virtual (`.venv`)

#### 🐧 Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 🍎 macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 🪟 Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
> **Nota (Windows PowerShell):** Caso apareça um erro de política de execução de scripts, execute antes:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

#### 🪟 Windows (Prompt de Comando / CMD)
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

*(Quando o ambiente estiver ativo, o prefixo `(.venv)` aparecerá no início da linha do terminal).*

---

### Passo 3 — Instalar as dependências

Com o ambiente virtual `.venv` ativado, atualize o `pip` e instale os pacotes listados em `requirements.txt` (o comando é idêntico nos três sistemas):

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Passo 4 — Configurar as variáveis de ambiente (`.env`)

Crie um arquivo chamado `.env` na raiz do projeto (`sabor-da-terra-agent/.env`) contendo sua chave da API do Gemini e o modelo desejado:

```env
GEMINI_API_KEY=sua_chave_api_do_gemini_aqui
GEMINI_MODEL=gemini-3.5-flash-lite
```

* **Linux / macOS (via terminal):**
  ```bash
  cat << 'EOF' > .env
  GEMINI_API_KEY=sua_chave_api_do_gemini_aqui
  GEMINI_MODEL=gemini-3.5-flash-lite
  EOF
  ```
* **Windows (PowerShell):**
  ```powershell
  @"
  GEMINI_API_KEY=sua_chave_api_do_gemini_aqui
  GEMINI_MODEL=gemini-3.5-flash-lite
  "@ | Out-File -FilePath .env -Encoding utf8
  ```

---

### Passo 5 — Inicializar o banco vetorial (RAG)

O repositório já acompanha o diretório `data/chroma/`, mas caso queira gerar ou atualizar o índice vetorial a partir dos documentos em `data/`, execute:

```bash
python INICIARBANCO.py
```

---

### Passo 6 — Executar o Assistente (Interface Streamlit)

Com o ambiente `.venv` ativado, inicie a aplicação web:

```bash
python -m streamlit run ui/app.py
```

O navegador abrirá automaticamente em **`http://localhost:8501`**.

#### Como testar na interface:
1. Na **barra lateral esquerda**, escolha o **Perfil de Acesso**:
   * **Equipe (Administrador):** acesso completo à triagem, documentos e relatórios administrativos.
   * **Produtor:** informe um telefone ou ID cadastrado (ex.: `(87) 99812-3456` ou `P001` para Maria) para validar o isolamento de dados financeiros.
   * **Comprador:** simula o atendimento externo de pedidos e cotações.
2. Utilize os **botões de atalho rápido** na barra lateral (`PED-001`, `PED-006`, `RAG: Certificação Josefa`, `Segurança: Dados de terceiros`) ou digite perguntas diretamente no campo de chat inferior.
3. Clique em **🔄 Nova Conversa** sempre que desejar reiniciar o contexto da sessão.

---

## 🧪 Como Executar os Testes Automatizados

### Suíte de Testes Unitários e de Integração (Pytest)
Executa toda a bateria de testes de triagem, segurança, mascaramento, dados e RAG:

```bash
python -m pytest
```

### Avaliação de Desempenho do Agente
Executa os cenários de referência definidos em `eval/gabarito_v0.json`:

```bash
python eval/rodar_avaliacao.py
```
