"""
Multi-provider LLM utility for agentic AI services.

Supports OpenAI, Anthropic, and Google Gemini via LangChain.
Auto-detects provider from environment variables, with explicit override via LLM_PROVIDER.
Falls back to None (keyword heuristics) when no API key is configured.
"""
import os
import logging
from typing import Optional, Type, TypeVar

from opentelemetry import trace
from pydantic import BaseModel

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

T = TypeVar("T", bound=BaseModel)

# Singleton state for runtime model switching
_current_provider: Optional[str] = None
_current_model: Optional[str] = None

# Default models per provider
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-3-flash",
}

# Available models per provider (for frontend selector)
AVAILABLE_MODELS = {
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "tier": "$", "finance_accuracy": "~75%"},
        {"id": "gpt-5-mini", "name": "GPT-5 Mini", "tier": "$$", "finance_accuracy": "87.4%"},
        {"id": "gpt-5", "name": "GPT-5", "tier": "$$$", "finance_accuracy": "88.2%"},
    ],
    "anthropic": [
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "tier": "$", "finance_accuracy": "76%"},
        {"id": "claude-opus-4-20250514", "name": "Claude Opus 4.5", "tier": "$$$", "finance_accuracy": "84%"},
        {"id": "claude-opus-4.6", "name": "Claude Opus 4.6", "tier": "$$$", "finance_accuracy": "87.8%"},
    ],
    "google": [
        {"id": "gemini-3-flash", "name": "Gemini 3 Flash", "tier": "$", "finance_accuracy": "83.6%"},
        {"id": "gemini-3-pro", "name": "Gemini 3 Pro", "tier": "$$", "finance_accuracy": "86.1%"},
    ],
}


def _detect_provider() -> Optional[str]:
    """Auto-detect LLM provider from environment variables."""
    explicit = os.environ.get("LLM_PROVIDER", "").lower().strip()
    if explicit in ("openai", "anthropic", "google"):
        return explicit

    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("GOOGLE_API_KEY"):
        return "google"

    return None


def _get_model_name(provider: str) -> str:
    """Get the configured model name for a provider."""
    global _current_model
    if _current_model:
        return _current_model
    return os.environ.get("LLM_MODEL", DEFAULT_MODELS.get(provider, "gpt-4o"))


def get_chat_model():
    """
    Return a LangChain chat model based on the detected/configured provider.
    Returns None if no API key is available (triggers keyword fallback).
    """
    global _current_provider
    provider = _current_provider or _detect_provider()
    if not provider:
        logger.info("No LLM API key configured — using keyword heuristic fallback")
        return None

    model_name = _get_model_name(provider)
    logger.info(f"Initializing LLM: provider={provider}, model={model_name}")

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=0.0, request_timeout=30)
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model_name, temperature=0.0, timeout=30)
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, temperature=0.0)
        else:
            logger.warning(f"Unknown LLM provider: {provider}")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize LLM ({provider}/{model_name}): {e}")
        return None


def structured_llm_call(
    system_prompt: str,
    user_input: str,
    output_schema: Type[T],
) -> Optional[T]:
    """
    Make a structured LLM call that returns a Pydantic model instance.

    Uses .with_structured_output() which works identically across
    OpenAI, Anthropic, and Google providers via LangChain.

    Returns None if no LLM is available or the call fails (caller should use fallback).
    """
    model = get_chat_model()
    if model is None:
        return None

    provider = _current_provider or _detect_provider() or "unknown"
    model_name = _get_model_name(provider)

    with tracer.start_as_current_span("llm.structured_call") as span:
        span.set_attribute("llm.provider", provider)
        span.set_attribute("llm.model", model_name)
        span.set_attribute("llm.schema", output_schema.__name__)

        try:
            structured_model = model.with_structured_output(output_schema)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]
            result = structured_model.invoke(messages)

            span.set_attribute("llm.success", True)
            logger.info(f"LLM call succeeded: provider={provider}, model={model_name}")
            return result

        except Exception as e:
            span.record_exception(e)
            span.set_attribute("llm.success", False)
            logger.error(f"LLM call failed ({provider}/{model_name}): {e}")
            return None


def get_llm_config() -> dict:
    """Return current LLM configuration for API/frontend display."""
    provider = _current_provider or _detect_provider()
    model_name = _get_model_name(provider) if provider else None

    return {
        "provider": provider,
        "model": model_name,
        "source": "llm" if provider else "heuristic",
        "fallback_active": provider is None,
        "available_providers": list(AVAILABLE_MODELS.keys()),
        "available_models": AVAILABLE_MODELS,
    }


def set_llm_config(provider: Optional[str] = None, model: Optional[str] = None) -> dict:
    """Update LLM provider/model at runtime. Returns new config."""
    global _current_provider, _current_model

    if provider:
        if provider not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown provider: {provider}. Must be one of {list(AVAILABLE_MODELS.keys())}")
        _current_provider = provider

    if model:
        _current_model = model

    logger.info(f"LLM config updated: provider={_current_provider}, model={_current_model}")
    return get_llm_config()
