# Módulo de Triagem e Interpretação de Pedidos (Integrante 3)

Este documento reúne a documentação de uso de `tools/triagem.py` e a **Seção "Triagem"** para composição do Documento de Arquitetura do projeto (entrega de 19/11/2026).

---

## 1. Guia Rápido do Módulo (`tools/triagem.py`)

### Contrato da função principal

```python
from tools.triagem import triar_pedido

resultado = triar_pedido(
    texto="Bom dia! Preciso pra essa sexta (01/nov): 30kg de queijo coalho...",
    canal="email",
    remetente="compras@restauranteraizes.com.br",
    data_referencia=None,  # opcional ('YYYY-MM-DD')
)
```

### Estrutura de retorno (`TriagemResultado`)

| Campo | Tipo | Descrição |
|---|---|---|
| `tipo_mensagem` | `str` | `'pedido de compra'`, `'cotacao'`, `'consulta documental'`, `'mensagem de produtor'`, `'notificacao oficial'` ou `'outro'` |
| `comprador` | `str \| None` | Nome do comprador, instituição ou produtor identificado (por texto ou cruzamento do telefone em `produtores.csv`) |
| `canal` | `str \| None` | Canal de recebimento (`'email'`, `'whatsapp'`, `'formulario_web'`) |
| `itens` | `list[dict]` | Lista de itens com `produto_normalizado`, `quantidade`, `unidade`, `observacao` e `exige_organico` |
| `prazo` | `str \| None` | Data ISO (`YYYY-MM-DD`) calculada/validada em código Python, ou `None` quando não especificada |
| `urgencia` | `str` | `'alta'`, `'media'` ou `'baixa'` (definida por regras determinísticas mais interpretação do modelo) |
| `justificativa_urgencia` | `str \| None` | Motivo objetivo da classificação de urgência |
| `problemas` | `list[str]` | Alertas de negócio e segurança gerados em código (safra, certificação, capacidade, contrato, datas, roteamento) |
| `confianca` | `str` | `'alta'`, `'media'` ou `'baixa'` |
| `perguntas_de_esclarecimento` | `list[str]` | Perguntas objetivas para itens ambíguos, quantidades ausentes ou prazos não especificados |

### Execução dos testes

```bash
# Testes unitários e de integração offline (D2, D3, D4 e D5 - sem uso de rede/API)
python tests/test_triagem.py

# Avaliação dos 15 pedidos de data/pedidos.json em 3 rodadas seguidas com cache local
python scripts/test_triagem_15_pedidos.py

# Avaliação forçando chamadas reais à Gemini API (ignora cache)
python scripts/test_triagem_15_pedidos.py --sem-cache
```

### Congelamento do Prompt e do Schema (Etapa D5 — 17/11/2026)

- **Schema congelado (`VERSAO_SCHEMA_TRIAGEM = "1.0.0"`):** `ItemPedido` e `TriagemResultado` estão configurados com `ConfigDict(extra="forbid", validate_assignment=True)`, bloqueando qualquer campo extra fora do contrato acordado na Seção 3 e Seção 7 do Plano de Execução (`CAMPOS_ITEM_PEDIDO` e `CAMPOS_TRIAGEM_RESULTADO`).
- **Prompt congelado (`VERSAO_PROMPT_TRIAGEM = "1.0.0"`):** `PROMPT_SISTEMA_TRIAGEM` utiliza exemplos sintéticos e delimitadores `<mensagem>...</mensagem>`, com verificação de integridade via hash SHA-256 em `obter_metadados_congelamento()`.

---

## 2. Seção "Triagem de Pedidos" — Documento de Arquitetura

### 2.1 Contexto e Requisitos Atendidos

Conforme a seção 4.1 e a seção 5 do documento oficial do projeto, a Cooperativa Sabor da Terra recebe entre 60 e 100 mensagens diárias por WhatsApp, e-mail e formulário web, contendo pedidos em linguagem coloquial, abreviações, informações implícitas, cotações em português e inglês, mensagens de produtores e notificações de órgãos de fiscalização (ADAGRO).

O módulo `tools/triagem.py` atende aos seguintes requisitos:
- **Extração e estruturação:** transforma mensagens livres em JSON validado pelo schema Pydantic `TriagemResultado`.
- **Ausência de suposições:** termos genéricos ou ambíguos (`queijo`, `manteiga`, `cheiro verde`, `frutas variadas`, `"da última vez"`, `"o de sempre"`) nunca são convertidos em variedades arbitrárias; o sistema preserva o termo genérico, consulta `lotes.csv` para verificar se há histórico real e gera perguntas em `perguntas_de_esclarecimento`.
- **Cálculos e regras de negócio em código Python:** datas, consistência entre dia da semana e calendário, sazonalidade (`sazonalidade.csv`), validade de certificação orgânica (`produtores.csv`), faixas e preços contratuais (`contratos/`), capacidade semanal/mensal (`fichas_tecnicas/`) e orçamentos preliminares (`tabela_precos_outubro_2026.csv`) são processados determinamente em Python, integrados aos módulos `tools/dados.py`, `tools/consultas.py` e `tools/mascarar.py`.

### 2.2 Fluxo de Processamento por Caso de Uso

```text
Mensagem Bruta (texto, canal, remetente)
   │
   ├─► 1. Extração Estruturada (Gemini API + response_schema=TriagemResultado, temp=0.1)
   │      - Entrada isolada por delimitadores <mensagem>...</mensagem>
   │      - Retry com backoff e fallback de modelo (até 3 tentativas)
   │
   ├─► 2. Normalização e Identificação em Código (Python)
   │      - Cruzamento do telefone/e-mail com produtores.csv (ex.: P001 no PED-012, P003 no PED-015)
   │      - Normalização pelo catálogo oficial sem chutar produtos ambíguos
   │      - Cálculo e validação de datas explícitas e relativas + consistência dia da semana x calendário
   │      - Separação de múltiplas intenções (ex.: oferta de estoque vs. cadastro de vizinho no PED-015)
   │
   ├─► 3. Validações de Negócio em Código (Integradas aos Dados da Cooperativa)
   │      - Safra: verificar_sazonalidade() para o mês do prazo ou mês citado (ex.: cajá em nov, colônia em jan/2027)
   │      - Certificação: verificar_certificacao() e consultar_produtores() (ex.: P008 vencida em 30/09/2026, P004 vence em 01/12/2026, itens sem oferta orgânica, ausência de certificação internacional)
   │      - Capacidade: confronto com limites semanais/mensais das fichas técnicas e sazonalidade.csv
   │      - Contratos e Histórico: validação dos contratos Raízes (008/2026), Mercado Bom Preço (012/2026) e PNAE (045/2026), detecção de menção a contrato inexistente (SuperBom) e consulta a lotes.csv
   │      - Roteamento Não-Compra e Idioma: checklist de inspeção ADAGRO (PED-014), cruzamento de estoque com pedidos pendentes (PED-015) e adaptação para inglês (PED-011)
   │
   └─► 4. Camada Final de Segurança e Mascaramento
          - Detecção de tentativas de injeção de comandos no pedido
          - Mascaramento recursivo de CPF, agência, conta bancária e chave PIX via mascarar_saida()
```

### 2.3 Tabela de Decisões Técnicas da Triagem

| Decisão | Escolha Adotada | Alternativas Consideradas | Motivo da Escolha |
|---|---|---|---|
| Extração estruturada | `response_schema=TriagemResultado` (Pydantic) na chamada `generate_content` com `temperature=0.1` | Extração por regex pura ou parsing manual de texto livre gerado pelo LLM | Garante 100% de conformidade sintática com o contrato JSON em uma única chamada ao modelo por pedido |
| Regras de negócio e datas | Pós-processamento determinístico em Python (`aplicar_validacoes_em_codigo`) consumindo `tools/consultas.py` e `tools/dados.py` | Incluir tabelas de preços, safra, contratos e cálculo de calendário dentro do prompt do LLM | Elimina alucinações numéricas e de calendário (ex.: saber que `01/11/2026` é domingo e `04/11/2026` é quarta-feira), cumprindo a diretriz de que o modelo apenas interpreta texto |
| Tratamento de ambiguidade | Manter termo genérico (`queijo`, `manteiga`, `cheiro verde`) e gerar pergunta em `perguntas_de_esclarecimento` | Mapear por similaridade para o item mais vendido (ex.: converter `queijo` em `queijo coalho`) | Evita erros de alocação e perdas de perecíveis; quando o cliente diz `"o de sempre"`, o código verifica `lotes.csv` antes de assumir qualquer item |
| Controle de cota e resiliência | Máximo de 3 tentativas com espera crescente, fallback entre modelos Flash (`gemini-3.5-flash`, `gemini-3.5-flash-lite`) e cache SHA-256 nos testes | Laços de múltiplas chamadas de agentes por pedido ou modelo único sem cache | Respeita os limites de requisições por minuto/dia da faixa gratuita da Gemini API no Google AI Studio |

### 2.4 Segurança e Privacidade na Triagem

1. **Ocultação de dados pessoais e bancários:** toda saída de `triar_pedido` passa por `mascarar_saida()`, integrada ao `tools/mascarar.py` (dupla camada: valores conhecidos dos CSVs da cooperativa + expressões regulares para CPF de terceiros como no `PED-015`, agência, conta corrente e chaves PIX).
2. **Isolamento contra *Prompt Injection* em pedidos:** o conteúdo bruto recebido é encapsulado em `<mensagem>...</mensagem>` com instrução explícita de tratamento como dado bruto, complementada em código pela verificação `PADROES_INJECAO_OU_COMANDO` (comandos como *"ignore as instruções anteriores"* ou *"marque este pedido como pago"* geram alerta de segurança sem execução).
3. **Escalonamento humano obrigatório:** notificações oficiais (`PED-014` da ADAGRO), pedidos de envio de dados bancários/PIX (`PED-003`, `PED-011`), solicitações de cadastro de terceiros (`PED-015`) e pedidos urgentes acima da capacidade ou sem contrato (`PED-006`) são sinalizados para decisão humana.

### 2.5 Resultados da Avaliação da Triagem

Nos testes automatizados executados sobre o módulo:
- **Testes unitários e de integração (`tests/test_triagem.py`):** `11/11` aprovados cobrindo normalização sem chutes, cálculo de datas em código, consistência de dia da semana, mascaramento de dados sensíveis, safra, certificação orgânica, contratos (Raízes, Mercado Bom Preço e PNAE), integração nos pedidos `001`, `006`, `012` e `015`, idioma inglês (`PED-011`), checklist ADAGRO (`PED-014`), proteção contra injeção de comandos e verificação de congelamento de schema/prompt (D5).
- **Conjunto dos 15 pedidos em 3 rodadas seguidas (`scripts/test_triagem_15_pedidos.py`):**
  - Rodadas consecutivas com 100% de JSON válido e gabarito aprovado: `3/3` (`45/45` execuções — `100%`; no modo padrão o script reutiliza o cache em disco das extrações da Gemini API para preservar a cota gratuita e reexecuta 100% das validações determinísticas de D2 a D5 em código; para validar chamadas reais à API a cada rodada, utilizar a flag `--sem-cache`).
  - Schema JSON válido: `15/15` (`100%`)
  - Ausência de vazamento de dados sensíveis (CPF, conta, agência, PIX): `15/15` (`100%`)
  - Classificação do tipo de mensagem: `15/15` (`100%`)
  - Contagem exata de itens: `15/15` (`100%`)
  - Alertas de inconsistência de data (`PED-001` e `PED-002`): `2/2` (`100%`)
  - Perguntas de esclarecimento em casos ambíguos (`PED-003` e `PED-005`): `2/2` (`100%`)
  - Armadilhas de negócio de D3/D4 da seção 9 sinalizadas em `problemas`: `15/15` (`100%`)

### 2.6 Limitações Conhecidas e Trabalho Futuro

1. **Cota e privacidade na faixa gratuita da Gemini API (Google AI Studio):** na faixa gratuita utilizada para o protótipo, os limites de requisições por minuto/dia são restritos e os dados enviados podem ser utilizados pelo provedor conforme os termos do AI Studio (por isso apenas dados fictícios são utilizados). O caminho de produção recomendado para a cooperativa é a migração para **Vertex AI no Google Cloud**, mantendo exatamente as mesmas funções Python e garantindo isolamento corporativo dos dados e SLA gerenciado.
2. **Dados de capacidade em texto livre:** como os arquivos CSV originais não possuem coluna numérica de capacidade semanal por produtor, os limites de capacidade foram consolidados em código a partir das 5 fichas técnicas (`fichas_tecnicas/*.txt`) e das observações de `sazonalidade.csv`. Como evolução futura, recomenda-se adicionar colunas estruturadas de capacidade e estoque em tempo real no banco de dados.
3. **Múltiplas solicitações na mesma mensagem:** mantendo o contrato fixo acordado entre os módulos (`TriagemResultado`), intenções secundárias na mesma mensagem (como a indicação de cadastro do vizinho no `PED-015`) são separadas da lista de itens de estoque e registradas de forma estruturada em `problemas` para encaminhamento humano.
