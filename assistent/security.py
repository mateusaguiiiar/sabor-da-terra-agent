import re
from typing import Any, Dict, Optional
from tools.mascarar import mascarar

# Tools that expose private financial/sales data of a specific producer
SENSITIVE_PRODUCER_TOOLS = {
    "vendas_do_produtor",
    "saldo_a_receber",
    "gerar_resumo_produtor",
}

# Regex patterns for sensitive PII (Note: CNPJ is intentionally NOT masked per project rules)
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
BANK_ACCOUNT_PATTERN = re.compile(
    r"(?i)(conta|ag[êe]ncia|pix)\s*[:\-]?\s*[\d\.\-]{4,}"
)


def mask_sensitive_text(text: str) -> str:
    """
    Defense-in-depth sanitizer: scrubs unmasked CPFs and bank/PIX numbers
    from model outputs while preserving public data like CNPJs and batch IDs.
    """
    if not text:
        return text

    # Mask CPF keeping only the last 2 digits: ***.***.***-XX
    def _mask_cpf(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        return f"***.***.***-{digits[-2:]}" if len(digits) == 11 else "***.***.***-**"

    text = CPF_PATTERN.sub(_mask_cpf, text)
    text = BANK_ACCOUNT_PATTERN.sub(r"\1: [DADO MASCARADO]", text)
    text = mascarar(text)
    return text


def check_access_permission(
    tool_name: str, args: Dict[str, Any], state: Dict[str, Any]
) -> Optional[Dict[str, str]]:
    """
    Enforces role-based access control (RBAC) via session state:
    - 'equipe' (cooperativa staff): full access to producer tools.
    - 'produtor': can only query their own 'produtor_id'.
    """
    if tool_name not in SENSITIVE_PRODUCER_TOOLS:
        return None

    perfil = str(state.get("perfil", "equipe")).strip().lower()
    logged_produtor_id = str(state.get("produtor_id", "")).strip().upper()
    requested_id = str(
    args.get("produtor_id") or args.get("id_produtor") or args.get("produtor") or ""
    ).strip().upper()

    if perfil == "produtor":
        if not logged_produtor_id:
            return {
                "erro": "Acesso negado: perfil de produtor sem identificação autenticada."
            }
        if requested_id and requested_id != logged_produtor_id:
            return {
                "erro": (
                    f"Acesso negado: você tem permissão apenas para consultar os dados "
                    f"do seu próprio cadastro (ID {logged_produtor_id})."
                )
            }

    return None


def wrap_untrusted_order_text(raw_text: str) -> str:
    """
    Wraps external order messages in strict XML data boundaries so prompt
    injections inside customer orders are treated purely as literal data.
    """
    return (
        "<texto_pedido_externo>\n"
        f"{raw_text}\n"
        "</texto_pedido_externo>"
    )