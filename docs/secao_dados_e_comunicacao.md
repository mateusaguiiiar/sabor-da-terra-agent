# Dados e comunicação com produtores

**Responsável:** Integrante 4. **Código:** `tools/dados.py`, `tools/consultas.py`, `tools/comunicacao.py`, `tools/mascarar.py`. **Testes:** 81 testes em `tests/test_dados.py`, `test_mascarar.py`, `test_consultas.py`, `test_financeiro_lotes.py` e `test_comunicacao.py` (rodar com `python -m pytest tests/test_dados.py tests/test_mascarar.py tests/test_consultas.py tests/test_financeiro_lotes.py tests/test_comunicacao.py`; não usam a API). **Dicionário de dados:** `docs/dados.md`.

## O que esta parte faz

Responde com precisão tudo o que está nos CSVs da cooperativa (produtores, financeiro, safra, preços e lotes), entrega as validações usadas pela triagem e gera resumos e notificações para os produtores sem expor dados sensíveis.

```
data/*.csv ──> dados.py ──> consultas.py ──────────────> agente (ferramentas)
              (carrega,     (consultas e        │
               normaliza)    validações)        └──> comunicacao.py ──> Gemini (só redige)
                                                                  └──> mascarar() ──> texto final
```

## Ferramentas entregues

| Função | Responde | Usada por |
|---|---|---|
| `consultar_produtores` | Quem produz X, por município e certificação válida | Agente, triagem |
| `verificar_certificacao` | A certificação orgânica do produtor está válida? | Agente, triagem |
| `verificar_sazonalidade` | O produto está na safra no mês? (com alerta) | Triagem |
| `obter_preco` | Preço com desconto de atacado | Triagem, agente |
| `vendas_do_produtor` | Vendas, recebido e pendente no período | Agente (perfil Produtor) |
| `saldo_a_receber` | Pendências vencidas e a vencer | Agente (perfil Produtor) |
| `rastrear_lote` | Produtor, produto, comprador, datas e validade do lote | Agente |
| `gerar_resumo_produtor` | Resumo curto e cordial para o produtor | Agente |
| `gerar_notificacao_novo_pedido` | Aviso de pedido novo para o produtor | Agente |
| `mascarar` | Oculta CPF, agência, conta e PIX de qualquer texto | Agente, RAG |

Toda função devolve `{"erro": "mensagem"}` quando a entrada não existe ou é ambígua, em vez de inventar uma resposta.

## Decisões e justificativas

1. **Contas em código, Gemini só redige.** Totais, saldos, descontos, datas e validades são calculados com pandas. O Gemini recebe apenas os fatos já calculados e escreve o texto. Motivo: modelos de linguagem erram aritmética com confiança.
2. **Conferência do texto gerado.** Todo valor em R$ citado pelo Gemini é comparado com os fatos; se aparecer um valor que não está lá, o texto é descartado. Na notificação, qualquer preço descarta o texto (o plano proíbe preços).
3. **Texto de reserva montado em código.** Cada chamada ao Gemini tem limite de 30 segundos. Em erro passageiro (429 cota, 503 modelo sobrecarregado), a função tenta o modelo principal (`GEMINI_MODEL`) duas vezes e depois um modelo reserva (`GEMINI_MODEL_RESERVA`). Sem chave, com erro definitivo ou com texto descartado, ela usa uma mensagem montada em código com os mesmos números. A demo nunca fica sem resposta. Respostas iguais ficam em cache para economizar cota.
4. **Data de referência fixa (30/10/2026).** "Esse mês", vencimentos e validades usam essa data, para os testes e a demo darem sempre o mesmo resultado.
5. **Nomes de produtos diferentes entre arquivos** ("goiaba" × "goiaba paluma extra"). Busca por sinônimo, nome exato e palavras em comum; se houver mais de uma opção, a função devolve erro de produto ambíguo, e o agente pergunta ao usuário.
6. **Vencido pela data, não pela observação.** Só o P003 tem "ATRASADO" escrito no CSV, mas P002 e P004 também estão vencidos.
7. **Regra de safra:** os níveis `nenhuma` e `baixa` geram alerta.
8. **"Pedidos alocados" no resumo** = lotes entregues no período (`lotes.csv`), porque a sugestão de alocação saiu do escopo.

## Proteção de dados sensíveis

Três camadas: (1) as funções escolhem campo por campo o que devolvem, e nunca incluem CPF, telefone, e-mail, endereço ou dados bancários; (2) todo texto gerado passa por `mascarar()`, que oculta os CPFs, contas e chaves PIX do cadastro e, por padrão (regex), CPFs, agências, contas e chaves PIX em geral; (3) testes conferem que nenhum dado do cadastro aparece nos retornos dos 18 produtores. O `mascarar()` também é aplicado pelo RAG nos trechos antes de enviá-los ao Gemini.

**Autorização:** `vendas_do_produtor`, `saldo_a_receber` e `gerar_resumo_produtor` recebem o `produtor_id`. O id de quem está falando nunca vem do texto do usuário, e sim da sessão:

1. A interface (`ui/app.py`, função `resolver_produtor_id`) transforma o telefone em id (ex.: `(87) 99812-3456` → `P001`) e grava `perfil` e `produtor_id` no `state` **ao criar** a sessão.
2. Antes de cada ferramenta, o `security.py` (via `before_tool_callback`) compara o `produtor_id` pedido com o da sessão e bloqueia se forem diferentes, ou se o telefone não for de nenhum produtor.

Testado na interface: a Maria (P001) recebe o próprio saldo (R$ 0,00) e tem o saldo do Cícero (P003) bloqueado; um telefone que não está no cadastro é bloqueado.

Durante os testes integrados foi encontrado um bug na interface, corrigido no `develop` (commit 3c46b90): o `state` era alterado numa cópia da sessão devolvida pelo ADK, então o perfil nunca chegava à segurança, e ela tratava todos como equipe. O teste isolado de `check_access_permission` mostrou que a regra de segurança estava certa e que o problema era só a criação da sessão.

## Como foi testado

- Critérios de aceite do plano: P008 com certificação vencida em 30/09/2026; `rastrear_lote('LOT-2026-0089')` = P003, queijo coalho, 45 kg, Restaurante Raízes, validade 02/10/2026; queijo coalho convencional, 120 kg = R$ 3.648,00; vendas e saldo de P001, P003, P004 e P007 conferidos com soma manual do `financeiro.csv`.
- Resumos e notificações testados com um Gemini simulado (sem gastar cota): texto aceito, valor inventado rejeitado, erro 429, dado sensível mascarado e preço na notificação descartado.

## Limitações

- O mascaramento por padrão (regex) pode deixar passar formatos incomuns (CPF por extenso, conta sem a palavra "conta") que não estejam no cadastro, e pode ocultar números de 11 dígitos que não são CPF.
- A conferência do texto gerado verifica valores em R$, mas não quantidades nem datas escritas pelo modelo.
- Na faixa gratuita da Gemini API, os dados enviados podem ser usados pelo Google; os dados do projeto são fictícios. Em produção, o caminho seria o Vertex AI.
- A coluna `quantidade_kg` nem sempre está em kg (alface em unidades, ovos em dúzias).
- Os dados cobrem apenas setembro e outubro de 2026.
- O perfil é escolhido num menu da interface (simulação). Não há login: em produção, o perfil e o `produtor_id` viriam de uma autenticação real.
