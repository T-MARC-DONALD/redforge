"""Concrete adapters built on OpenAICompatAdapter.

Each subclass only changes BASE_URL (and optionally the default model),
because the request/response shape is identical.
"""
from __future__ import annotations

from redforge.adapters.openai_compat import OpenAICompatAdapter


class OpenAIAdapter(OpenAICompatAdapter):
    """The official OpenAI API."""

    BASE_URL = "https://api.openai.com/v1"


class OllamaAdapter(OpenAICompatAdapter):
    """Local Ollama server (http://localhost:11434). No API key needed."""

    BASE_URL = "http://localhost:11434/v1"


class GenericAdapter(OpenAICompatAdapter):
    """Any OpenAI-compatible endpoint; base_url is REQUIRED in config."""

    BASE_URL = ""  # config.base_url must be set

    def __init__(self, config):
        if not config.base_url:
            raise ValueError(
                "GenericAdapter requires 'base_url' in the target config "
                "(e.g. https://api.deepseek.com/v1)"
            )
        super().__init__(config)
