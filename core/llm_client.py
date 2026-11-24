
"""The ONLY file that talks to Ollama.

If you ever want to switch to another LLM, change this file only.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Iterator

from pydantic import BaseModel

from core import config


logger = logging.getLogger(__name__)

_client = None


# ============================================================
# OLLAMA CLIENT
# ============================================================

def get_client():
    global _client

    if _client is None:
        import ollama

        _client = ollama.Client(
            host=config.OLLAMA_HOST,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )

    return _client


def _require_model() -> str:
    if (
        not config.OLLAMA_MODEL
        or config.OLLAMA_MODEL == "your-model-name"
    ):
        raise RuntimeError(
            "OLLAMA_MODEL is not set. "
            "Open the .env file and set OLLAMA_MODEL "
            "to an installed model. "
            "Run `ollama list` to see your models."
        )

    return config.OLLAMA_MODEL


# ============================================================
# CONNECTION AND MODEL VALIDATION
# ============================================================

def check_ollama() -> tuple[bool, str]:
    """Check Ollama availability and model installation."""

    try:
        model = _require_model()

    except RuntimeError as error:
        return False, str(error)

    try:
        response = get_client().list()

    except Exception:
        return False, (
            f"Cannot reach Ollama at {config.OLLAMA_HOST}. "
            "Start the Ollama app or run `ollama serve` "
            "and refresh this page."
        )

    models = getattr(response, "models", None)

    if models is None and isinstance(response, dict):
        models = response.get("models", [])

    names = []

    for item in models or []:
        name = getattr(item, "model", None)

        if name is None and isinstance(item, dict):
            name = item.get("model") or item.get("name")

        if name:
            names.append(name)

    if model not in names and f"{model}:latest" not in names:
        return False, (
            f"Model '{model}' is not installed. "
            f"Run: ollama pull {model}"
        )

    return True, f"Ollama is running with model '{model}'."


# ============================================================
# GENERATION SETTINGS
# ============================================================

def get_token_limit(answer_length: str = "Balanced") -> int:
    """Return the generation budget for the answer length."""

    limits = {
        "Short": config.LLM_MAX_TOKENS_SHORT,
        "Balanced": config.LLM_MAX_TOKENS_BALANCED,
        "Detailed": config.LLM_MAX_TOKENS_DETAILED,
    }

    return limits.get(
        answer_length,
        config.LLM_MAX_TOKENS_BALANCED,
    )


def _generation_options(
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict:
    """Build consistent Ollama generation settings."""

    options = {
        "temperature": (
            config.TEMP_TEACH
            if temperature is None
            else temperature
        ),
        "num_ctx": config.LLM_CONTEXT_WINDOW,
    }

    if max_tokens is not None:
        options["num_predict"] = max_tokens

    return options


# ============================================================
# NORMAL RESPONSE GENERATION
# ============================================================

def _chat_raw(
    messages: list[dict],
    temperature: float | None,
    schema: dict | None,
    max_tokens: int | None = None,
) -> str:
    """Generate a complete Ollama response."""

    model = _require_model()

    try:
        response = get_client().chat(
            model=model,
            messages=messages,
            options=_generation_options(
                temperature,
                max_tokens,
            ),
            format=schema,
            keep_alive=config.LLM_KEEP_ALIVE,
            stream=False,
        )

        content = response["message"]["content"] or ""

        if getattr(response, "done_reason", None) == "length":
            logger.warning(
                "Ollama response reached its generation limit."
            )

        return content

    except Exception as error:
        logger.warning(
            "Ollama generation failed: %s",
            type(error).__name__,
        )

        raise RuntimeError(
            "AI response generation failed. "
            "Check that Ollama is running and has sufficient "
            "system memory."
        ) from error


def chat(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Generate one complete text answer."""

    return _chat_raw(
        messages,
        temperature,
        None,
        max_tokens,
    )


# ============================================================
# STREAMING RESPONSE GENERATION
# ============================================================

def stream_chat(
    messages: list[dict],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Iterator[str]:
    """Yield generated text pieces to the application."""

    model = _require_model()

    try:
        stream = get_client().chat(
            model=model,
            messages=messages,
            options=_generation_options(
                temperature,
                max_tokens,
            ),
            keep_alive=config.LLM_KEEP_ALIVE,
            stream=True,
        )

        for part in stream:
            piece = part["message"]["content"]

            if piece:
                yield piece

            if getattr(part, "done_reason", None) == "length":
                logger.warning(
                    "Streamed response reached its generation limit."
                )

    except Exception as error:
        logger.warning(
            "Ollama streaming failed: %s",
            type(error).__name__,
        )

        raise RuntimeError(
            "AI response generation was interrupted. "
            "Check Ollama and try again."
        ) from error


# ============================================================
# JSON RESPONSE PARSING
# ============================================================

def _parse_json(raw: str) -> dict:
    """Parse JSON while tolerating Markdown code fences."""

    text = raw.strip()

    text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "No JSON object found in the model reply."
        )

    return json.loads(text[start:end + 1])


# ============================================================
# STRUCTURED AI GENERATION
# ============================================================

def chat_validated(
    messages: list[dict],
    model_cls: type[BaseModel],
    temperature: float | None = None,
    retries: int = 2,
) -> BaseModel:
    """Generate and validate structured AI responses."""

    schema = model_cls.model_json_schema()

    temp = (
        config.TEMP_JSON
        if temperature is None
        else temperature
    )

    conversation = list(messages)
    last_error: Exception | None = None

    for attempt in range(retries + 1):

        raw = _chat_raw(
            conversation,
            temp,
            schema,
            max_tokens=config.LLM_MAX_TOKENS_JSON,
        )

        try:
            return model_cls.model_validate(
                _parse_json(raw)
            )

        except ValueError as error:
            last_error = error

            logger.warning(
                "JSON validation failed on attempt %s of %s.",
                attempt + 1,
                retries + 1,
            )

            # Rebuild from the original messages to avoid
            # accumulating invalid responses in the context.
            conversation = list(messages) + [
                {
                    "role": "user",
                    "content": (
                        "The previous response did not match "
                        "the required JSON schema. "
                        "Generate a complete corrected JSON "
                        "object only, with all required fields."
                    ),
                },
            ]

    raise RuntimeError(
        f"The AI did not return valid structured data "
        f"after {retries + 1} attempts. "
        "Please try again."
    ) from last_error
