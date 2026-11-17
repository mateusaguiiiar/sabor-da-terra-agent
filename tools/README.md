# tools/ — dados e comunicação (Integrante 4)

- `dados.py`: carrega e normaliza os CSVs de `data/`. Use `dados.produtores()`, `dados.financeiro()`, etc.
- `mascarar.py`: `mascarar(texto)` oculta CPF, agência, conta e chave PIX. `mascarar_dados(obj)` faz o mesmo em dicts e listas.

Uso:

```python
from tools.mascarar import mascarar
resposta = mascarar(resposta)
```

Testes: `python -m pytest` na raiz do projeto. Dicionário de dados em `docs/dados.md`.
