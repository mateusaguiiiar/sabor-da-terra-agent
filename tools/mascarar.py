"""Mascaramento de dados sensíveis (CPF, agência, conta e chave PIX).

Use mascarar() em TODO texto que vai para o usuário: respostas do agente,
trechos devolvidos pelo RAG, resumos e notificações.

Funciona em duas camadas:
1. Valores conhecidos: todo CPF, conta corrente e chave PIX que existe nos
   CSVs da cooperativa é ocultado onde aparecer, em qualquer formato de texto.
   Isso pega também chaves PIX que são e-mail ou telefone.
2. Padrões (regex): CPFs em geral (inclusive de pessoas fora do cadastro),
   números depois de "agência"/"conta" e valores depois de "pix".

Nenhuma das duas camadas é perfeita sozinha. A regra principal continua
sendo: as funções de consulta não devolvem colunas sensíveis.
"""

import re
from functools import lru_cache

import pandas as pd

from tools import dados

OCULTO = "[oculto]"

# CPF com ou sem pontuação: 123.456.789-00 ou 12345678900.
# Os lookarounds evitam pegar pedaço de um número maior (ex.: CNPJ).
RE_CPF = re.compile(r"(?<![\d./])\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?![\d/])")

# "agência 0437", "ag. 1582", "agencia nº 0023-1"
RE_AGENCIA = re.compile(
    r"\b(ag[êe]ncia|ag)\b\.?\s*(?:n[º°o]\.?\s*)?:?\s*\d{3,5}(?:-[\dxX])?",
    re.IGNORECASE,
)

# "conta 28901-3", "conta corrente: 0073921-7", "c/c 41087-6"
RE_CONTA = re.compile(
    r"(\bconta(?:\s+corrente)?\b|\bc/c\b|\bcc\b)\.?\s*(?:n[º°o]\.?\s*)?:?\s*\d[\d.]{3,}(?:-[\dxX])?",
    re.IGNORECASE,
)

# "pix: email@x.com", "chave pix (87) 99901-5567", "pix é 123.456.789-00"
RE_PIX = re.compile(
    r"\b(chave\s+)?pix\b\s*(?::|-|é|e)?\s*"
    r"(\S+@\S+|\(?\d{2}\)?\s*9?\d{4}-?\d{4}|\d[\d.\-]{10,13}\d|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)


@lru_cache(maxsize=None)
def _valores_conhecidos() -> tuple:
    """CPFs, contas e chaves PIX que existem nos CSVs, do maior para o menor."""
    valores = set()
    try:
        prod = dados.produtores()
        valores.update(prod["cpf"])
        valores.update(prod["chave_pix"])
        valores.update(prod["conta_corrente"])
        fin = dados.financeiro()
        valores.update(fin["produtor_cpf"])
        valores.update(fin["chave_pix_deposito"])
    except FileNotFoundError:
        # Sem os CSVs, segue só com as regex
        pass
    valores = {str(v).strip() for v in valores if isinstance(v, str) and len(v.strip()) >= 6}
    # Maiores primeiro, para um valor curto não quebrar um maior no meio
    return tuple(sorted(valores, key=len, reverse=True))


def mascarar(texto: str) -> str:
    """Oculta CPF, agência, conta bancária e chave PIX de um texto.

    Args:
        texto: qualquer texto que será mostrado ao usuário.

    Returns:
        O mesmo texto, com os dados sensíveis trocados por marcadores
        como '***.***.***-**', 'agência ****', 'conta ****' e '[oculto]'.
        Textos vazios ou None voltam como ''.
    """
    if not texto:
        return ""
    texto = str(texto)

    for valor in _valores_conhecidos():
        texto = texto.replace(valor, OCULTO)

    texto = RE_PIX.sub(lambda m: f"{m.group(1) or ''}pix {OCULTO}", texto)
    texto = RE_AGENCIA.sub(lambda m: f"{m.group(1)} ****", texto)
    texto = RE_CONTA.sub(lambda m: f"{m.group(1)} ****", texto)
    texto = RE_CPF.sub("***.***.***-**", texto)
    return texto


def mascarar_dados(valor):
    """Aplica mascarar() a todos os textos de um dict, lista ou texto.

    Útil para passar o retorno inteiro de uma ferramenta pelo mascaramento.
    """
    if isinstance(valor, str):
        return mascarar(valor)
    if isinstance(valor, dict):
        return {k: mascarar_dados(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return type(valor)(mascarar_dados(v) for v in valor)
    return valor
