# Dicionário de dados

Dados da Cooperativa Sabor da Terra usados pelas ferramentas de dados (`tools/dados.py`).
Todos os arquivos ficam em `data/`. Datas no formato `AAAA-MM-DD`.

**Data de referência:** as validações usam `DATA_REFERENCIA` (padrão `2026-10-30`, data dos últimos pedidos) em vez da data real, para os testes darem sempre o mesmo resultado. Pode ser trocada pela variável de ambiente de mesmo nome.

## produtores.csv (18 linhas)

| Coluna | Tipo | Descrição | Sensível |
|---|---|---|---|
| id | texto | `P001` a `P018` | |
| nome_completo | texto | | |
| cpf | texto | `000.000.000-00` | **sim** |
| data_nascimento | data | | **sim** |
| telefone | texto | `(87) 99999-9999`. Usado para identificar o produtor que manda mensagem | **sim** |
| email | texto | | **sim** |
| endereco | texto | | **sim** |
| municipio | texto | Garanhuns, Brejão, Caetés, Jucati, Lajedo, Águas Belas, Bom Conselho | |
| produtos | texto | Lista separada por vírgula, ex.: `"goiaba,acerola,manga"` | |
| certificacao_organica | texto | `sim` / `nao` (sem acento) | |
| validade_certificacao | data | Vazia quando não tem certificação | |
| chave_pix | texto | Pode ser CPF, e-mail ou telefone | **sim** |
| banco, agencia, conta_corrente | texto | | **sim** |
| status | texto | `ativo` / `inativo` (só P015 é inativo) | |

## financeiro.csv (30 linhas, set-out/2026)

| Coluna | Tipo | Descrição | Sensível |
|---|---|---|---|
| id_transacao | texto | `FIN-2026-001` | |
| data | data | Data da venda | |
| produtor_id, produtor_nome | texto | | |
| produtor_cpf | texto | | **sim** |
| comprador, tipo, produto | texto | `tipo` é sempre `venda` | |
| quantidade_kg, valor_unitario, valor_total | número | | |
| forma_pagamento | texto | `pix`, `boleto 30 dias`, `empenho 45 dias`, `transferência` | |
| status_pagamento | texto | `pago` (20) / `pendente` (10) | |
| data_vencimento, data_pagamento | data | `data_pagamento` vazia quando pendente | |
| chave_pix_deposito | texto | CPF, e-mail ou telefone | **sim** |
| observacao | texto | Ex.: `ATRASADO - cobrar`, número de empenho | |

## lotes.csv (20 linhas)

| Coluna | Tipo | Descrição | Sensível |
|---|---|---|---|
| lote_id | texto | `LOT-2026-0089` a `LOT-2026-0108` | |
| data_colheita, data_entrega, validade | data | | |
| produtor_id, produtor_nome, produto, comprador | texto | | |
| produtor_cpf | texto | | **sim** |
| quantidade_kg | número | Ver problema 4 | |
| pedido_id | texto | Formato `PED-2026-SEP-003`, diferente dos IDs do pedidos.json | |
| temperatura_transporte_c | texto | Número em °C **ou** `ambiente` | |
| inspecao_visual, observacao | texto | | |

## sazonalidade.csv (50 produtos)

Uma coluna por mês (`jan` a `dez`) com o nível: `alta`, `media`, `baixa` ou `nenhuma`, mais uma `observacao` em texto livre.

## tabela_precos_outubro_2026.csv (53 produtos)

| Coluna | Tipo | Descrição |
|---|---|---|
| produto | texto | |
| unidade | texto | `kg`, `unidade`, `maço`, `dúzia`, `litro` |
| preco_convencional, preco_organico | número | `n/d` quando não existe: tratado como vazio, nunca como zero |
| desconto_atacado_pct | número | Percentual de desconto |
| volume_minimo_atacado_kg | número | Quantidade mínima para ter o desconto. `0` = sem desconto |
| observacao | texto | Ex.: `Apenas P003`, `P017 sem SIE` |

## Problemas encontrados e como foram tratados

1. **Acentos e maiúsculas.** Os pedidos escrevem `maracuja`, `rucula`. Todo nome de produto é comparado depois de `normalizar()` (minúsculas, sem acento).
2. **O mesmo produto com nomes diferentes em cada arquivo:**

   | produtores.csv | sazonalidade.csv | tabela de preços |
   |---|---|---|
   | goiaba | goiaba paluma | goiaba paluma extra / especial |
   | manga | manga tommy | manga tommy |
   | banana | banana prata | banana prata |
   | tomate | tomate | tomate santa cruz |
   | tomate cereja | (não tem) | tomate cereja |
   | pimentão | pimentão | pimentão verde / colorido |
   | tapioca, goma | tapioca/goma | tapioca/goma |
   | mel de abelha jandaíra | mel de jandaíra | mel de jandaíra |

   Tratamento (`tools/consultas.py`): a busca de produto tenta, nesta ordem, um **sinônimo** (`banana` -> `banana prata`, `tomate` -> `tomate santa cruz`, `aipim` -> `macaxeira`...), o **nome exato** e por fim os nomes que **contêm todas as palavras** pedidas, preferindo os que começam com a mesma palavra (`goiaba` -> `goiaba paluma`, não `doce de goiaba`). Se sobrar mais de uma opção (`goiaba` na tabela de preços: extra ou especial; `queijo`: coalho ou manteiga), a função devolve erro de **produto ambíguo** com as opções, em vez de escolher sozinha.
3. **Produtos sem sazonalidade nem preço:** feijão, milho e fava (só do P015, que está inativo).
4. **`quantidade_kg` nem sempre é kg.** Alface vem em unidades, coentro e couve em maços e ovos em dúzias (a `observacao` avisa). A unidade certa está na tabela de preços.
5. **Pendências vencidas.** Na data de referência, 5 transações pendentes já passaram do vencimento (P002, P004 e P003). Só as do P003 estão marcadas `ATRASADO - cobrar` na observação. O atraso deve ser calculado pela data, não pela observação.
6. **Certificações:** P008 (Josefa) vencida em 2026-09-30. P004 (Ana Lúcia) vence em 2026-12-01.
7. **Dados sensíveis espalhados.** CPF aparece em produtores, financeiro e lotes; chaves PIX são às vezes e-mail ou telefone. As funções nunca devolvem essas colunas (`dados.sem_sensiveis()`), e todo texto passa por `mascarar()`.

## Regras de negócio adotadas

**Erros.** Toda função de consulta devolve `{"erro": "mensagem"}` quando o produtor, o produto ou o mês não existe, ou quando o produto é ambíguo. Nunca inventa uma resposta.

**Safra (`verificar_sazonalidade`).** Os níveis `nenhuma` e `baixa` geram alerta; `media` e `alta`, não.
- `nenhuma`: "fora de safra, não há produção".
- `baixa`: "baixa disponibilidade (pode estar fora de safra), confirmar com o produtor".

Motivo: o critério de aceite do plano cita a goiaba, marcada como `baixa` no período que a observação chama de "fora de safra". **Inconsistência encontrada:** no CSV, a goiaba paluma é `baixa` em **mai, jun e jul**, e `media` em agosto, mas a observação diz "Fora de safra jun-ago". A função segue o nível da tabela, e a observação é devolvida junto para o agente mostrar.

**Certificação (`verificar_certificacao`).** Inválida quando o produtor não tem certificação, quando a validade é anterior à data de referência ou quando ele não produz o produto informado. Válida com aviso quando vence em até 60 dias (caso da P004, que vence em 01/12/2026).

**Preço (`obter_preco`).** `total = preço unitário x quantidade x (1 - desconto/100)`. O desconto de atacado só vale quando a quantidade é **maior ou igual** ao volume mínimo da tabela. Produto sem preço na versão pedida (ex.: banana prata orgânica, `n/d`) devolve erro, nunca preço zero. Conferência: queijo coalho convencional, 120 kg -> 32,00 x 120 x 0,95 = **R$ 3.648,00**.

**Vendas e saldo (`vendas_do_produtor`, `saldo_a_receber`).**
- Calculados só a partir do `financeiro.csv`. "Recebido" = `status_pagamento` `pago`; "pendente" = qualquer outro status.
- O `periodo` filtra pela **data da venda** (coluna `data`). Formatos aceitos: vazio (todo o histórico), `AAAA-MM`, `AAAA`, `AAAA-MM-DD:AAAA-MM-DD`, nome ou abreviação do mês com ou sem ano (`outubro`, `out/2026`) e `mes_atual` (mês da data de referência).
- Uma pendência é **vencida** quando a data de vencimento é anterior à data de referência, independentemente da observação (só o P003 tem `ATRASADO - cobrar`, mas P002 e P004 também estão vencidos).
- Conferência manual (data de referência 30/10/2026): P001 vendeu R$ 1.090,00, tudo pago e tudo em setembro (em outubro, zero); P003 vendeu R$ 7.460,00 e tem R$ 6.020,00 vencidos há 12 dias; P004 tem R$ 1.020,00 vencidos há 7 dias; P007 vendeu R$ 3.155,00 e tem R$ 2.480,00 a vencer em 40 dias.
- **Autorização:** as funções recebem o `produtor_id` como parâmetro. No perfil Produtor, esse id deve vir da sessão (telefone), e não do modelo, para um produtor não consultar o saldo de outro (responsabilidade do agente, Integrante 1).

**Lotes (`rastrear_lote`).** Aceita o código completo (`LOT-2026-0089`) ou só o número (`89`). A temperatura vem como `ambiente` ou em °C. O `quantidade` segue a unidade do produto (ver problema 4).
