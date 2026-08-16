"""redforge.adapters.base - the adapter contract.

Every provider adapter implements `complete(conversation) -> AdapterResponse`.
The engine only ever talks to this interface, so swapping OpenAI for Ollama
is a one-line config change, not a code change.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod

from redforge.config import TargetConfig
from redforge.core.models import AdapterResponse, Turn


class AdapterError(Exception):
    """Raised when a provider call fails (auth, rate limit, network...)."""


class BaseAdapter(ABC):
    """Uniform interface to a chat-completion provider.

    Responsibilities shared by every adapter:
      1. Resolve the API key from the environment (by NAME, never by value)
      2. Build the HTTP headers for this provider
      3. Leave the provider-specific request formatting to subclasses
    """

    def __init__(self, config: TargetConfig):
        self.config = config
        # Common headers: JSON body + bearer token when a key is configured.
        self._headers = {"Content-Type": "application/json", **config.headers}
        if config.api_key_env:
            key = os.environ.get(config.api_key_env)
            if not key:
                raise AdapterError(
                    f"{config.api_key_env} is not set. "
                    f"Export it in your shell before running."
                )
            self._headers["Authorization"] = f"Bearer {key}"

    @abstractmethod
    def complete(self, conversation: list[Turn]) -> AdapterResponse:
        """Send a conversation and return the model's reply.

        `conversation` is our canonical list[Turn]. The adapter is
        responsible for converting it into the provider's exact wire
        format and normalizing the response back into AdapterResponse.
        """
