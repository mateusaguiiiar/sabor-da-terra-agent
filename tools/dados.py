"""Camada de dados da cooperativa Sabor da Terra.

Carrega os CSVs da pasta data/, normaliza textos e datas e devolve
DataFrames prontos para as funções de consulta.

As funções devolvem sempre uma CÓPIA dos dados, para que nenhuma
consulta altere o que foi carregado.

Configuração (variáveis de ambiente, opcionais):
    PASTA_DADOS      pasta dos CSVs (padrão: <raiz do projeto>/data)
    DATA_REFERENCIA  data usada como "hoje" nas validações, no formato
                     AAAA-MM-DD (padrão: 2026-10-30, data dos últimos pedidos).
                     Fixar essa data deixa os testes repetíveis.
"""

import os
import unicodedata
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DADOS = Path(os.getenv("PASTA_DADOS", RAIZ_PROJETO / "data"))
DATA_REFERENCIA = date.fromisoformat(os.getenv("DATA_REFERENCIA", "2026-10-30"))

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]

# Colunas com dados pessoais ou bancários. Nunca devem sair das funções de consulta.
COLUNAS_SENSIVEIS = {
    "cpf", "produtor_cpf", "data_nascimento", "endereco", "telefone", "email",
    "chave_pix", "chave_pix_deposito", "banco", "agencia", "conta_corrente",
}


def normalizar(texto) -> str:
    """Deixa o texto em minúsculas, sem acentos e sem espaços nas pontas.

    Exemplo: '  Maracujá ' -> 'maracuja'. Valores vazios viram ''.
    """
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.lower().split())


def _ler_csv(nome: str) -> pd.DataFrame:
    return pd.read_csv(PASTA_DADOS / nome, dtype=str, keep_default_na=False)


@lru_cache(maxsize=None)
def _produtores() -> pd.DataFrame:
    df = _ler_csv("produtores.csv")
    df["produtos_lista"] = df["produtos"].apply(
        lambda s: [normalizar(p) for p in s.split(",") if p.strip()]
    )
    df["organico"] = df["certificacao_organica"].map(normalizar).eq("sim")
    df["validade_certificacao"] = pd.to_datetime(df["validade_certificacao"], errors="coerce")
    df["ativo"] = df["status"].map(normalizar).eq("ativo")
    df["municipio_norm"] = df["municipio"].map(normalizar)
    return df


@lru_cache(maxsize=None)
def _financeiro() -> pd.DataFrame:
    df = _ler_csv("financeiro.csv")
    for col in ["data", "data_vencimento", "data_pagamento"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["quantidade_kg", "valor_unitario", "valor_total"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["produto_norm"] = df["produto"].map(normalizar)
    df["status_pagamento"] = df["status_pagamento"].map(normalizar)
    return df


@lru_cache(maxsize=None)
def _lotes() -> pd.DataFrame:
    df = _ler_csv("lotes.csv")
    for col in ["data_colheita", "data_entrega", "validade"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["quantidade_kg"] = pd.to_numeric(df["quantidade_kg"], errors="coerce")
    df["produto_norm"] = df["produto"].map(normalizar)
    return df


@lru_cache(maxsize=None)
def _sazonalidade() -> pd.DataFrame:
    df = _ler_csv("sazonalidade.csv")
    df["produto_norm"] = df["produto"].map(normalizar)
    for mes in MESES:
        df[mes] = df[mes].map(normalizar)
    return df


@lru_cache(maxsize=None)
def _precos() -> pd.DataFrame:
    df = _ler_csv("tabela_precos_outubro_2026.csv")
    df["produto_norm"] = df["produto"].map(normalizar)
    for col in ["preco_convencional", "preco_organico", "desconto_atacado_pct", "volume_minimo_atacado_kg"]:
        df[col] = pd.to_numeric(df[col].replace("n/d", pd.NA), errors="coerce")
    return df


def produtores() -> pd.DataFrame:
    """Cadastro dos produtores (inclui colunas sensíveis: não devolver direto ao usuário)."""
    return _produtores().copy()


def financeiro() -> pd.DataFrame:
    """Transações financeiras de set-out/2026 (inclui CPF e chave PIX)."""
    return _financeiro().copy()


def lotes() -> pd.DataFrame:
    """Rastreabilidade dos lotes entregues (inclui CPF do produtor)."""
    return _lotes().copy()


def sazonalidade() -> pd.DataFrame:
    """Nível de disponibilidade de cada produto por mês (alta, media, baixa, nenhuma)."""
    return _sazonalidade().copy()


def precos() -> pd.DataFrame:
    """Tabela de preços de outubro/2026, convencional e orgânico."""
    return _precos().copy()


def sem_sensiveis(df: pd.DataFrame) -> pd.DataFrame:
    """Remove do DataFrame todas as colunas com dados pessoais ou bancários."""
    return df.drop(columns=[c for c in df.columns if c in COLUNAS_SENSIVEIS])
