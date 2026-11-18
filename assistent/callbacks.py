from .security import check_access_permission, mask_sensitive_text
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

# Configure structured console/file logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sabor_da_terra")

CACHE_FILE = Path(".cache_respostas_teste.json")
USE_TEST_CACHE = os.getenv("USE_TEST_CACHE", "false").lower() == "true"


def _get_cache_key(llm_request: LlmRequest) -> str:
    """Generates a deterministic hash from the conversation contents."""
    serialized = json.dumps(
        [c.model_dump(exclude_none=True) for c in (llm_request.contents or [])],
        sort_keys=True,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def before_model_guard(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Enforces max 3 model calls per turn, logs requests, and serves test cache."""
    # 1. Track and cap model calls per user message (Schedule rule: max 3 calls)
    calls = callback_context.state.get("temp:model_calls", 0) + 1
    callback_context.state["temp:model_calls"] = calls
    logger.info(f"Chamada ao modelo #{calls} na invocação atual.")

    if calls > 3:
        logger.warning("Limite de 3 chamadas ao modelo por pergunta atingido.")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="Limite de processamento atingido para esta pergunta. Por favor, reformule de forma mais específica."
                    )
                ],
            )
        )

    # 2. Check test cache if enabled
    if USE_TEST_CACHE:
        key = _get_cache_key(llm_request)
        cache = _load_cache()
        if key in cache:
            logger.info(f"[CACHE HIT] Retornando resposta em cache (key={key[:8]}).")
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=cache[key])],
                )
            )

    return None


def after_model_logger(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Logs model output, masks leaked PII, and saves test cache when enabled."""
    if not llm_response.content or not llm_response.content.parts:
        return None

    tool_calls = [
        p.function_call.name for p in llm_response.content.parts if p.function_call
    ]
    if tool_calls:
        logger.info(f"Modelo solicitou ferramentas: {tool_calls}")

    modified = False
    new_parts = []
    text_parts = []

    for part in llm_response.content.parts:
        if part.text:
            sanitized = mask_sensitive_text(part.text)
            if sanitized != part.text:
                logger.warning("[SEGURANÇA] Dado sensível mascarado na resposta final.")
                modified = True
            new_parts.append(types.Part(text=sanitized))
            text_parts.append(sanitized)
        else:
            new_parts.append(part)

    if text_parts:
        final_text = "".join(text_parts)
        logger.info(f"Resposta gerada ({len(final_text)} chars).")

        if USE_TEST_CACHE and not tool_calls:
            req_key = callback_context.state.get("temp:last_req_key")
            if req_key:
                cache = _load_cache()
                cache[req_key] = final_text
                _save_cache(cache)

    if modified:
        return LlmResponse(
            content=types.Content(role="model", parts=new_parts)
        )
    return None


def log_tool_execution(tool, args: dict, tool_context) -> Optional[dict]:
    """Logs tool invocation and enforces role-based access control."""
    logger.info(f"[TOOL CALL] Executando '{tool.name}' com args={args}")

    denied = check_access_permission(tool.name, args, tool_context.state)
    if denied:
        logger.warning(f"[ACESSO NEGADO] Bloqueada chamada para '{tool.name}': {denied}")
        return denied

    return None