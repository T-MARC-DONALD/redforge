"""Anthropic Messages API adapter (Claude models).

Anthropic's API differs from OpenAI's in three important ways:
  1. The system prompt goes in a top-level `system` field, not in messages
  2. Auth uses `x-api-key` + `anthropic-version` headers, not Bearer
  3. Response text lives in data["content"] as a list of content blocks,
     only some of which are type "text"

The adapter hides all of that so the engine can treat every provider the same.
"""
from __future__ import annotations

import os
import time

import httpx

from redforge.adapters.base import AdapterError, BaseAdapter
from redforge.config import TargetConfig
from redforge.core.models import AdapterResponse, Turn

ANTHROPIC_VERSION = "2023-06-01"


class AnthropicAdapter(BaseAdapter):
    BASE_URL = "https://api.anthropic.com/v1"

    def __init__(self, config: TargetConfig):
        # Anthropic always needs a key - fail fast with a clear message.
        if not config.api_key_env:
            raise AdapterError("Anthropic requires api_key_env (ANTHROPIC_API_KEY)")

        # super().__init__ validates the key and sets Bearer + Content-Type.
        super().__init__(config)
        # ...but Anthropic doesn't use Bearer; replace with its own headers.
        self._headers.pop("Authorization", None)
        self._headers["x-api-key"] = os.environ[config.api_key_env]
        self._headers["anthropic-version"] = ANTHROPIC_VERSION

        self.base_url = (config.base_url or self.BASE_URL).rstrip("/")
        self._client = httpx.Client(timeout=config.timeout, headers=self._headers)

    def complete(self, conversation: list[Turn]) -> AdapterResponse:
        # 1. Pull system turns out of the conversation into the `system` field.
        system = "\n".join(t.content for t in conversation if t.role == "system")

        # 2. Remaining turns become user/assistant messages.
        messages = [
            {"role": t.role, "content": t.content}
            for t in conversation
            if t.role in ("user", "assistant")
        ]

        # 3. Build the body. `system` only included when non-empty.
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": messages,
        }
        if system:
            payload["system"] = system

        # 4. Send + time.
        start = time.perf_counter()
        try:
            resp = self._client.post(f"{self.base_url}/messages", json=payload)
        except httpx.HTTPError as e:
            raise AdapterError(f"Network error talking to {self.base_url}: {e}") from e

        if resp.status_code >= 400:
            raise AdapterError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        # 5. Normalize content blocks -> plain text.
        data = resp.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        return AdapterResponse(text=text, latency_ms=latency_ms, raw=data)
