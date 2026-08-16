"""OpenAI-compatible chat completions - the most common API shape.

OpenAI, Ollama, Groq, DeepSeek, OpenRouter, Qwen, Mistral, Zhipu... all
implement the same POST /chat/completions endpoint with a JSON body of
{model, messages, max_tokens, temperature}. One implementation covers
them all; subclasses only override the base URL.
"""
from __future__ import annotations

import time

import httpx

from redforge.adapters.base import AdapterError, BaseAdapter
from redforge.config import TargetConfig
from redforge.core.models import AdapterResponse, Turn

DEFAULT_MAX_TOKENS = 1024


class OpenAICompatAdapter(BaseAdapter):
    """Chat completions against any OpenAI-compatible endpoint."""

    BASE_URL = "https://api.openai.com/v1"  # overridden by subclasses

    def __init__(self, config: TargetConfig):
        super().__init__(config)
        self.base_url = (config.base_url or self.BASE_URL).rstrip("/")
        # One persistent client = connection pooling + reusable timeouts.
        self._client = httpx.Client(timeout=config.timeout, headers=self._headers)

    def complete(self, conversation: list[Turn]) -> AdapterResponse:
        # 1. Convert our canonical Turn list to the provider wire format.
        messages = [{"role": t.role, "content": t.content} for t in conversation]

        # 2. Build the request body.
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens or DEFAULT_MAX_TOKENS,
            "temperature": self.config.temperature,
        }

        # 3. Send, timing the round trip.
        start = time.perf_counter()
        try:
            resp = self._client.post(f"{self.base_url}/chat/completions", json=payload)
        except httpx.HTTPError as e:
            raise AdapterError(f"Network error talking to {self.base_url}: {e}") from e

        # 4. Fail loudly with the provider's error text (auth, quota, ...).
        if resp.status_code >= 400:
            raise AdapterError(
                f"HTTP {resp.status_code} from {self.base_url}: {resp.text[:300]}"
            )

        # 5. Normalize the response into our AdapterResponse.
        data = resp.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise AdapterError(
                f"Unexpected response shape from {self.base_url}: {str(data)[:200]}"
            ) from e

        latency_ms = int((time.perf_counter() - start) * 1000)
        return AdapterResponse(text=text or "", latency_ms=latency_ms, raw=data)
