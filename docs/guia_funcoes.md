# Consultas: guia rápido das funções

Nov 19, 2026 · @Glauco

As 10 funções da camada de dados e comunicação, para quem precisa usar sem ler o código. Todas ficam em `tools/` e devolvem um dicionário.

## Consultas (`tools/consultas.py`)

Os números são calculados com pandas a partir dos CSVs de `data/`, usando 30/10/2026 como "hoje". Nenhuma devolve CPF, telefone, e-mail, endereço ou dados bancários.

```python
from tools.consultas import consultar_produtores, verificar_certificacao, verificar_sazonalidade, obter_preco, vendas_do_produtor, saldo_a_receber, rastrear_lote
```

| Função | O que responde | Recebe | Exemplo |
| --- | --- | --- | --- |
| `consultar_produtores` | Quem produz algo, onde, e se o selo orgânico está válido | `produto`, `municipio`, `organico`, `apenas_ativos` (todos opcionais) | `consultar_produtores(produto="queijo coalho")` → `{"produtores": [{"id": "P003", "nome": ..., "certificacao_valida": ...}]}` |
| `verificar_certificacao` | A certificação orgânica do produtor vale na data? Avisa se vence em até 60 dias | `produtor_id`; opcionais `produto`, `data_ref` (`"AAAA-MM-DD"`) | `verificar_certificacao("P008")` → `{"valida": False, "validade": "2026-09-30", "motivo": "... VENCIDA ..."}` |
| `verificar_sazonalidade` | Nível de safra do produto no mês, com alerta para `baixa` e `nenhuma` | `produto`; opcional `mes` (`11`, `"nov"` ou `"novembro"`) | `verificar_sazonalidade("goiaba", "jun")` → `{"nivel": "baixa", "alerta": "Baixa disponibilidade..."}` |
| `obter_preco` | Preço pela tabela de outubro, com desconto de atacado quando a quantidade atinge o mínimo | `produto`; opcionais `organico`, `quantidade_kg` | `obter_preco("queijo coalho", quantidade_kg=120)` → `{"total": 3648.0, "desconto_atacado": ...}` |
| `vendas_do_produtor` | Quanto o produtor vendeu, recebeu e tem pendente, por comprador e por produto | `produtor_id`; opcional `periodo` | `vendas_do_produtor("P001")` → `{"total_vendido": 1090.0, "total_pendente": 0.0, ...}` |
| `saldo_a_receber` | O que falta receber, separado em vencido e a vencer, com dias de atraso | `produtor_id`; opcional `periodo` | `saldo_a_receber("P003")` → `{"total_a_receber": 6020.0, "total_vencido": 6020.0, ...}` |
| `rastrear_lote` | Produtor, produto, comprador, datas e validade de um lote | `lote_id` (aceita `"89"`) | `rastrear_lote("89")` → `{"produtor_id": "P003", "produto": "queijo coalho", "quantidade": 45.0, ...}` |

Formatos aceitos em `periodo`: vazio (todo o histórico), `"2026-10"`, `"outubro"`, `"out/2026"`, `"mes_atual"`, `"2026"` ou `"2026-09-01:2026-10-31"`.

Nomes de produto podem vir do jeito do comprador: "aipim" acha "macaxeira" e "goiaba" acha "goiaba paluma". Se o nome servir para mais de um produto, a função devolve erro de produto ambíguo, com as opções.

## Comunicação e mascaramento

As contas são feitas em código; o Gemini só escreve o texto. Se ele citar um valor em R$ que não está nos dados, ou falhar (sem chave, erro 429 ou 503), a função usa um texto montado em código com os mesmos números. A resposta nunca vem vazia.

| Função | Onde | O que faz | Recebe | Devolve |
| --- | --- | --- | --- | --- |
| `gerar_resumo_produtor` | `tools/comunicacao.py` | Mensagem curta para o produtor: vendas, recebido, a receber e entregas | `produtor_id`; opcional `periodo` | `{"texto", "origem": "gemini" ou "texto_padrao", "dados"}` |
| `gerar_notificacao_novo_pedido` | `tools/comunicacao.py` | Aviso de pedido novo, só com os itens que o produtor produz, sem preços | `produtor_id`, `pedido` (o JSON da triagem, como dict ou texto) | `{"texto", "origem", "itens", "alertas"}` |
| `mascarar` | `tools/mascarar.py` | Esconde CPF, agência, conta e PIX de qualquer texto | `texto` | o texto com `***.***.***-**`, `agência ****`, `conta ****` e `[oculto]` |

A notificação avisa em `alertas` quando o comprador exige orgânico e a certificação do produtor não está válida. Para mascarar um dicionário inteiro, use `mascarar_dados(obj)`, do mesmo arquivo.

Variáveis do `.env`: `GEMINI_API_KEY`, `GEMINI_MODEL` (modelo principal), `GEMINI_MODEL_RESERVA` (usado se o principal estiver sobrecarregado) e `SABOR_SEM_LLM=1` (desliga o Gemini, usado nos testes).

## Por dentro do código

O trecho que faz o trabalho principal de cada função, para saber o que esperar sem abrir o arquivo.

### consultar\_produtores

```python
prod = dados.produtores()
if apenas_ativos:
    prod = prod[prod["ativo"]]
if municipio:
    prod = prod[prod["municipio_norm"] == dados.normalizar(municipio)]
if produto:
    prod = prod[prod["produtos_lista"].apply(lambda lista: _produtor_produz(lista, produto))]

for _, p in prod.iterrows():
    cert = verificar_certificacao(p["id"])
    if organico is True and not cert["valida"]:
        continue
```

Cada filtro só roda se o parâmetro foi passado. O filtro de orgânico usa a certificação **válida na data**, não só o "sim" do cadastro: quem tem o selo vencido não aparece como orgânico. O dicionário de saída é montado campo por campo, sem colunas sensíveis.

### verificar\_certificacao

```python
if produto and not _produtor_produz(p["produtos_lista"], produto):
    return {"valida": False, "validade": None, "motivo": "... não produz ..."}
if not p["organico"]:
    return {"valida": False, "validade": None, "motivo": "... não possui certificação ..."}
validade = p["validade_certificacao"].date()
if validade < data_ref:
    return {"valida": False, "validade": validade.isoformat(), "motivo": "... VENCIDA ..."}
dias = (validade - data_ref).days
if dias <= 60:
    motivo += f" Atenção: vence em {dias} dias."
```

Quatro verificações em ordem, cada uma com o seu `return`. A data de referência aceita texto `"AAAA-MM-DD"`, porque o agente manda tudo como texto.

### verificar\_sazonalidade

```python
achado = _encontrar_produto(produto, list(saz["produto_norm"]))
if "erro" in achado:
    return achado
linha = saz[saz["produto_norm"] == achado["nome"]].iloc[0]
nivel = linha[dados.MESES[mes - 1]]      # 11 -> coluna "nov"
return {..., "nivel": nivel, "alerta": ALERTAS_SAFRA.get(nivel)}
```

Antes disso, o mês é convertido para número de 1 a 12 (aceita `11`, `"nov"` ou `"novembro"`). `ALERTAS_SAFRA` só tem texto para `baixa` e `nenhuma`; para `alta` e `media`, o alerta vem `None`.

### obter\_preco

```python
coluna = "preco_organico" if organico else "preco_convencional"
preco = linha[coluna]                     # vazio se o CSV dizia "n/d"
tem_desconto = minimo > 0 and quantidade >= minimo and pct > 0
desconto = float(pct) if tem_desconto else 0.0
bruto = round(float(preco) * quantidade, 2)
total = round(bruto * (1 - desconto / 100), 2)
```

Se o produto não tem preço na versão pedida (orgânico "n/d"), devolve erro em vez de preço zero. O desconto de atacado só entra quando a quantidade chega no volume mínimo da tabela.

### O buscador de produtos (usado pelas três acima)

`_encontrar_produto` tenta, nesta ordem: sinônimo ("aipim" → "macaxeira"), nome exato e depois nomes com as mesmas palavras, preferindo os que começam com a mesma palavra ("goiaba" → "goiaba paluma", e não "doce de goiaba"). Se sobrar mais de um, devolve `{"erro": "... é ambíguo. Opções: ..."}`.

### vendas\_do\_produtor

```python
fin = fin[fin["produtor_id"] == pid]
fin = fin[(fin["data"].dt.date >= ini) & (fin["data"].dt.date <= fim)]   # se tiver período
pagos = fin[fin["status_pagamento"] == "pago"]
pendentes = fin[fin["status_pagamento"] != "pago"]
por_comprador = fin.groupby("comprador")["valor_total"].sum()
```

Filtra as transações do produtor no período, separa pagas e pendentes e soma com `groupby`. O período vira duas datas, início e fim, numa função interna (`_intervalo`).

### saldo\_a\_receber

```python
for _, t in fin[fin["status_pagamento"] != "pago"].iterrows():
    dias = (t["data_vencimento"].date() - ref).days
    if dias < 0:
        situacao, total_vencido = "vencido", total_vencido + valor
    else:
        situacao, total_a_vencer = "a vencer", total_a_vencer + valor
```

Vencido é decidido pela **data de vencimento**, não pela observação "ATRASADO" do CSV: só o P003 tinha essa palavra, mas o P004 também estava vencido. `dias` vem sempre positivo na saída (atraso ou dias até vencer).

### rastrear\_lote

```python
texto = str(lote_id or "").strip().upper()
if texto.isdigit():
    texto = f"LOT-{dados.DATA_REFERENCIA.year}-{int(texto):04d}"   # "89" -> "LOT-2026-0089"
linha = lotes[lotes["lote_id"] == texto]
```

Aceita o código completo ou só o número. Devolve as datas em `"AAAA-MM-DD"` e deixa de fora o CPF do produtor que existe no `lotes.csv`.

### gerar\_resumo\_produtor e gerar\_notificacao\_novo\_pedido

As duas montam uma lista de fatos com os números já calculados, um texto de reserva com os mesmos números, e passam os dois para `_redigir`:

```python
prompt = f"{pedido}\n\n<fatos>\n{fatos_texto}\n</fatos>"
tentativas = [MODELO, MODELO, MODELO_RESERVA]
for i, modelo in enumerate(tentativas):
    try:
        texto = _chamar_gemini(prompt, modelo).strip()
        if _texto_confere(texto, fatos_texto):
            return mascarar(texto), "gemini"
        break                              # texto ruim: não adianta repetir
    except Exception as erro:
        if not _erro_passageiro(erro):     # só 429 e 503 justificam tentar de novo
            break
        time.sleep(2)
return mascarar(texto_padrao), "texto_padrao"
```

- No máximo 3 chamadas: o modelo principal duas vezes e o reserva uma. Cada chamada desiste depois de 30 s.
- `_texto_confere` aceita o texto só se todo valor em R$ citado estiver nos fatos (comparação numérica, então `R$ 1.090,00` e `R$1090` contam igual) e se ele tiver até 1.200 caracteres.
- Chamadas iguais ficam em cache (`lru_cache`) e não gastam cota de novo.

Na notificação, antes de montar os fatos, só entram os itens que o produtor produz:

```python
for item in itens_pedido:
    produto = _campo(item, "produto", "nome")
    if not produto or not _produtor_produz(p["produtos_lista"], produto):
        continue
```

`_campo` aceita nomes diferentes para o mesmo campo (`"itens"` ou `"items"`, `"prazo"` ou `"data_entrega"`), para funcionar com o JSON da triagem. No fim, se o texto tiver qualquer valor em R$, ele é trocado pelo texto de reserva: notificação não leva preço.

### mascarar

```python
texto = RE_PIX.sub(lambda m: f"{m.group(1) or ''}pix [oculto]", texto)
texto = RE_AGENCIA.sub(lambda m: f"{m.group(1)} ****", texto)
texto = RE_CONTA.sub(lambda m: f"{m.group(1)} ****", texto)
texto = RE_CPF.sub("***.***.***-**", texto)
for valor in _valores_conhecidos():       # CPFs, contas e PIX que existem nos CSVs
    texto = texto.replace(valor, "[oculto]")
```

Primeiro os padrões (regex), para cada tipo ganhar a sua marcação. Depois troca qualquer CPF, conta ou PIX do cadastro que ainda tenha sobrado, como uma chave PIX que é e-mail escrita sem a palavra "pix". A regex de CPF não pega pedaço de CNPJ.

## Regras para quem chama

1. **Erro vem como dicionário, não como exceção.** Produtor, produto, mês ou período que não existe devolve `{"erro": "mensagem"}`. Confira com `if "erro" in r:` antes de usar o resultado.
2. **No perfil Produtor, o `produtor_id` vem da sessão**, nunca do texto do usuário. `vendas_do_produtor`, `saldo_a_receber` e `gerar_resumo_produtor` são bloqueadas pelo `security.py` quando o id pedido é de outro produtor.
3. **Datas e meses podem vir como texto.** O agente sempre manda texto, e as funções aceitam `"2026-10-30"`, `"11"` ou `"novembro"`.
4. **A data de referência é fixa em 30/10/2026**, para os testes e a demo darem sempre o mesmo resultado. Para mudar, use a variável `DATA_REFERENCIA` no `.env`.
5. **Testes:** `python -m pytest tests/test_dados.py tests/test_mascarar.py tests/test_consultas.py tests/test_financeiro_lotes.py tests/test_comunicacao.py` roda os 81 testes em poucos segundos, sem gastar cota do Gemini.

Detalhes de cada coluna dos CSVs estão em `docs/dados.md`.
