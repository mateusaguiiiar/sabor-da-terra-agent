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

   Tratamento: tabela de sinônimos nas funções de consulta.
3. **Produtos sem sazonalidade nem preço:** feijão, milho e fava (só do P015, que está inativo).
4. **`quantidade_kg` nem sempre é kg.** Alface vem em unidades, coentro e couve em maços e ovos em dúzias (a `observacao` avisa). A unidade certa está na tabela de preços.
5. **Pendências vencidas.** Na data de referência, 5 transações pendentes já passaram do vencimento (P002, P004 e P003). Só as do P003 estão marcadas `ATRASADO - cobrar` na observação. O atraso deve ser calculado pela data, não pela observação.
6. **Certificações:** P008 (Josefa) vencida em 2026-09-30. P004 (Ana Lúcia) vence em 2026-12-01.
7. **Dados sensíveis espalhados.** CPF aparece em produtores, financeiro e lotes; chaves PIX são às vezes e-mail ou telefone. As funções nunca devolvem essas colunas (`dados.sem_sensiveis()`), e todo texto passa por `mascarar()`.
