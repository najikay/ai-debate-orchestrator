"""LLM provider abstraction — Anthropic and OpenAI-compatible backends.

Provider selection is driven by environment variables:

    ANTHROPIC_API_KEY        → AnthropicProvider (used when set, default)
    LLM_API_KEY / OPENAI_API_KEY  → OpenAICompatibleProvider (auto-detected)
    LLM_BASE_URL             → base URL override for OpenAI-compatible endpoint
                               (DeepSeek, Qwen/DashScope, Ollama, local, etc.)
    LLM_PROVIDER             → explicit override: "anthropic" | "openai" |
                               "deepseek" | "qwen" | "openai_compatible"
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Normalised response returned by every :class:`LLMProvider`."""

    content: str
    prompt_tokens: int
    completion_tokens: int


class LLMProvider(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    def complete(
        self, model: str, prompt: str, max_tokens: int = 4096
    ) -> LLMResponse:
        """Send *prompt* to *model* and return a normalised response."""


class AnthropicProvider(LLMProvider):
    """Calls the Anthropic Messages API.

    Reads ``ANTHROPIC_API_KEY`` from the environment unless *api_key* is given.
    """

    def __init__(self, api_key: str | None = None) -> None:
        try:
            import anthropic as _ant
        except ImportError as exc:
            raise ImportError(
                "anthropic package is required: pip install anthropic"
            ) from exc
        self._client = _ant.Anthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )

    def complete(
        self, model: str, prompt: str, max_tokens: int = 4096
    ) -> LLMResponse:
        msg = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            content=msg.content[0].text,
            prompt_tokens=msg.usage.input_tokens,
            completion_tokens=msg.usage.output_tokens,
        )


class OpenAICompatibleProvider(LLMProvider):
    """Calls any OpenAI-compatible chat-completions endpoint.

    Works with OpenAI, DeepSeek, Qwen (DashScope), Ollama, and others.
    Reads ``LLM_API_KEY`` (or ``OPENAI_API_KEY``) and optionally
    ``LLM_BASE_URL`` from the environment unless arguments are given.
    """

    def __init__(
        self, api_key: str | None = None, base_url: str | None = None
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required for non-Anthropic providers: "
                "pip install openai"
            ) from exc
        resolved_key = (
            api_key
            or os.environ.get("LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        resolved_url = base_url or os.environ.get("LLM_BASE_URL")
        self._client = OpenAI(api_key=resolved_key, base_url=resolved_url)

    def complete(
        self, model: str, prompt: str, max_tokens: int = 4096
    ) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        usage = resp.usage
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )


_OPENAI_COMPAT = {"openai", "deepseek", "qwen", "openai_compatible"}


def build_provider() -> LLMProvider:
    """Auto-detect and instantiate the correct :class:`LLMProvider`.

    Priority:
        1. ``LLM_PROVIDER`` env var (explicit override).
        2. ``ANTHROPIC_API_KEY`` present → :class:`AnthropicProvider`.
        3. ``LLM_API_KEY`` / ``OPENAI_API_KEY`` present →
           :class:`OpenAICompatibleProvider`.

    Raises:
        EnvironmentError: When no recognised API key is found.
    """
    explicit = os.environ.get("LLM_PROVIDER", "").lower()
    if explicit == "anthropic" or (
        not explicit and os.environ.get("ANTHROPIC_API_KEY")
    ):
        return AnthropicProvider()
    if explicit in _OPENAI_COMPAT or (
        os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    ):
        return OpenAICompatibleProvider()
    raise EnvironmentError(
        "[ERROR] No LLM API key found. "
        "Set ANTHROPIC_API_KEY for Anthropic, or "
        "LLM_API_KEY + LLM_BASE_URL for any OpenAI-compatible provider "
        "(DeepSeek, Qwen, OpenAI, Ollama, etc.)."
    )
