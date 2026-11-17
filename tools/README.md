# tools/ — dados e comunicação (Integrante 4)

- `dados.py`: carrega e normaliza os CSVs de `data/`. Use `dados.produtores()`, `dados.financeiro()`, etc.
- `consultas.py`: `consultar_produtores`, `verificar_certificacao`, `verificar_sazonalidade`, `obter_preco`, `vendas_do_produtor`, `saldo_a_receber` e `rastrear_lote`. Em caso de entrada inválida devolvem `{"erro": ...}`.
- `comunicacao.py`: `gerar_resumo_produtor` e `gerar_notificacao_novo_pedido`. Números calculados em código; o Gemini só redige. Sem chave ou com erro do Gemini, usa um texto montado em código. Configuração no `.env`: `GEMINI_API_KEY` e `GEMINI_MODEL`.
- `mascarar.py`: `mascarar(texto)` oculta CPF, agência, conta e chave PIX. `mascarar_dados(obj)` faz o mesmo em dicts e listas.

Uso:

```python
from tools.mascarar import mascarar
resposta = mascarar(resposta)
```

Testes: `python -m pytest` na raiz do projeto. Dicionário de dados em `docs/dados.md`.
