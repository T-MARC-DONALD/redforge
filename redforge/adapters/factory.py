"""Adapter factory - build the right adapter from a TargetConfig.

This is the single place that maps a config's `provider` string to a
concrete adapter class. Adding a new provider = add one line here.
"""
from __future__ import annotations

from redforge.adapters.anthropic_adapter import AnthropicAdapter
from redforge.adapters.base import BaseAdapter
from redforge.adapters.mock_adapter import MockAdapter
from redforge.adapters.openai_adapter import (
    GenericAdapter,
    OllamaAdapter,
    OpenAIAdapter,
)
from redforge.config import TargetConfig

# provider string -> adapter class
_PROVIDERS = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "ollama": OllamaAdapter,
    "generic": GenericAdapter,
    "mock": MockAdapter,
}


def build_adapter(config: TargetConfig) -> BaseAdapter:
    """Return the adapter instance matching config.provider."""
    try:
        cls = _PROVIDERS[config.provider.lower()]
    except KeyError:
        valid = ", ".join(sorted(_PROVIDERS))
        raise ValueError(
            f"Unknown provider '{config.provider}'. Valid providers: {valid}"
        ) from None
    return cls(config)
