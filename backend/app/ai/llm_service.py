import os
import re
from typing import Any, Dict, List, Optional

from backend.app.utils.logger import app_logger

# Values shipped in .env.example / docker-compose that must NOT be treated as real keys
_PLACEHOLDER_MARKERS = (
    "your-openai-key",
    "your_openai_key",
    "your_api_key",
    "your-api-key",
    "change-me",
    "changeme",
    "<your",
)

_GREETING_RE = re.compile(
    r"^\s*(hi|hey|hello|yo|sup|good\s+(morning|afternoon|evening)|thanks|thank you)\b",
    re.IGNORECASE,
)

_client = None
_client_key: Optional[str] = None


def _configured_api_key() -> Optional[str]:
    """Return a usable API key, or None when it is missing or still a placeholder."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        return None
    lowered = key.lower()
    if any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
        return None
    return key


def is_llm_configured() -> bool:
    """True when a real OPENAI_API_KEY is configured."""
    return _configured_api_key() is not None


def _get_client():
    global _client, _client_key
    key = _configured_api_key()
    if key is None:
        _client = None
        _client_key = None
        return None
    if _client is None or _client_key != key:
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=key)
            _client_key = key
        except ImportError:
            app_logger.warning("openai package not installed")
            _client = None
    return _client


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """Call the LLM and return {content, tokens_used, model, configured}.

    When no usable API key is present (or the provider call fails) this degrades to
    a local answer assembled from the already-retrieved context, so the assistant
    stays useful offline instead of surfacing raw provider errors.
    """
    llm_model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
    client = _get_client()

    if client is None:
        app_logger.info("LLM not configured (placeholder or missing OPENAI_API_KEY); using local mode")
        return {
            "content": _local_answer(
                messages, "OPENAI_API_KEY is not configured, so no language model was called"
            ),
            "tokens_used": 0,
            "model": "local-fallback",
            "configured": False,
        }

    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return {
            "content": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "model": llm_model,
            "configured": True,
        }
    except Exception as e:
        # Never echo the raw provider error: it can quote back the API key.
        app_logger.error("LLM call failed (%s); falling back to local mode", type(e).__name__)
        return {
            "content": _local_answer(
                messages, "the language model request failed (check OPENAI_API_KEY, quota and model name)"
            ),
            "tokens_used": 0,
            "model": "local-fallback",
            "configured": False,
        }


def _extract_context(system_prompt: str) -> str:
    """Pull the CONTEXT block that build_system_prompt() appended."""
    marker = "CONTEXT:"
    idx = system_prompt.find(marker)
    if idx == -1:
        return ""
    return system_prompt[idx + len(marker):].strip()


def _local_answer(messages: List[Dict[str, str]], reason: str) -> str:
    """Compose an answer from context the agent already retrieved (no LLM involved)."""
    system_prompt = next(
        (m.get("content", "") for m in messages if m.get("role") == "system"), ""
    )
    user_query = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), ""
    )
    context = _extract_context(system_prompt)
    has_data = bool(context) and context != "No additional context available."

    parts: List[str] = []

    if _GREETING_RE.match(user_query) and len(user_query.split()) <= 4:
        parts.append(
            "Hello! I can answer questions about customers, churn risk, fraud, "
            "sales trends and overall business performance. Here is the current "
            "platform data:"
        )

    if has_data:
        parts.append(context)
    elif not parts:
        parts.append(
            "No matching records were found in the platform for that question. "
            "Try asking about customers, churn, fraud, sales or reports."
        )

    parts.append(f"Local mode: {reason}. This answer was assembled from the platform's own data.")

    return "\n\n".join(parts)


def build_system_prompt(context_parts: List[str]) -> str:
    context = "\n\n".join(context_parts) if context_parts else "No additional context available."
    return f"""You are an Enterprise AI Decision Intelligence assistant.
You help business analysts understand customer behavior, sales trends, fraud risks, and churn.

Use the following context to answer the user's question accurately.
If the context does not contain enough information, say so clearly.
Do NOT fabricate data or sources.

CONTEXT:
{context}
"""
