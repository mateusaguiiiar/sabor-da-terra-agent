import re
from tools.mascarar import mascarar

CPF = re.compile(r"(?<![\d.\-/])(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})(?![\d\-/]|\.\d)")
# "Ag. 0437", "Agência 0437"
AGENCIA = re.compile(r"(\bAg(?:\.|[êe]ncia)?\s*)\d[\d\-]*", re.IGNORECASE)
# "C/C 55.678-9", "Conta corrente 12345-6"
CONTA = re.compile(r"(\b(?:C/C|conta(?:\s+corrente)?)\s*:?\s*)\d[\d.\-]*", re.IGNORECASE)
# "Chave PIX: qualquer-coisa" (a chave tem que estar na mesma linha)
PIX = re.compile(r"(chave\s+PIX[^:\n]*:[ \t]*)\S[^\n]*", re.IGNORECASE)


def mascarar_texto(texto):
    """Preserva os marcadores esperados pelo RAG e aplica a camada unificada de mascaramento."""
    texto = PIX.sub(r"\1[PIX OCULTO]", texto)
    texto = CPF.sub("[CPF OCULTO]", texto)
    texto = AGENCIA.sub(r"\1[AGÊNCIA OCULTA]", texto)
    texto = CONTA.sub(r"\1[CONTA OCULTA]", texto)
    return mascarar(texto)