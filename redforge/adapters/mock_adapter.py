"""Mock adapter - simulate a model with zero network calls.

Lets us run the full pipeline offline: tests, demos, CI - no API keys, no
cost, no rate limits. The simulated "model" follows a few simple rules so
BOTH outcomes can be demonstrated:
    * direct extraction attempts  -> it leaks the system prompt (BYPASS)
    * DAN-style jailbreaks        -> it adopts the persona (BYPASS)
    * anything else               -> polite refusal (BLOCKED)

Swap in a real provider to test actual models; the engine can't tell the
difference because both obey the same interface.
"""
from __future__ import annotations

from redforge.adapters.base import BaseAdapter
from redforge.config import TargetConfig
from redforge.core.models import AdapterResponse, Turn


class MockAdapter(BaseAdapter):
    def __init__(self, config: TargetConfig):
        # No key, no HTTP - just remember the config.
        self.config = config
        self._headers = {}

    def complete(self, conversation: list[Turn]) -> AdapterResponse:
        # Find the last user message - that's the current attack prompt.
        last_user = next(
            (t.content for t in reversed(conversation) if t.role == "user"), ""
        ).lower()

        # Rule 1: extraction attempts leak the configured system prompt.
        if "system prompt" in last_user or "original instructions" in last_user:
            text = f"My instructions say: {self.config.system_prompt}"

        # Rule 2: persona jailbreaks "work" on this simulated model.
        elif "dan" in last_user or "do anything now" in last_user:
            text = "As DAN, I have no restrictions. I can say anything."

        # Rule 3: everything else is refused.
        else:
            text = "I'm sorry, I can't help with that. I'm here for customer support."

        return AdapterResponse(text=text, latency_ms=3, raw={})
