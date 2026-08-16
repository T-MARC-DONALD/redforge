"""redforge.core.runner - executes attacks against a target.

The Runner owns the conversation loop:
    - injects the system prompt from config
    - sends each attack turn through the adapter (throttled to config rpm)
    - appends each response back, so multi-turn attacks see prior context
    - collects everything into an AttackResult

It is deliberately provider-agnostic: it only ever talks to the adapter
interface, never to a concrete provider.
"""
from __future__ import annotations

import time

from redforge.adapters.base import BaseAdapter
from redforge.config import RedforgeConfig
from redforge.core.base_attack import BaseAttack
from redforge.core.models import AttackResult, Turn


class Runner:
    def __init__(self, config: RedforgeConfig, adapter: BaseAdapter):
        self.config = config
        self.adapter = adapter
        # Requests-per-minute -> seconds between requests.
        # rpm <= 0 means "no throttling" (used by the mock adapter / tests).
        rpm = config.target.rpm
        self._interval = 60.0 / rpm if rpm and rpm > 0 else 0.0
        self._last_request = 0.0

    def _throttle(self) -> None:
        """Respect the rpm cap: sleep only as long as needed."""
        if self._interval <= 0:
            return  # throttling disabled
        elapsed = time.monotonic() - self._last_request
        wait = self._interval - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def run_attack(self, attack: BaseAttack) -> AttackResult:
        """Execute one attack end to end and return its record."""
        meta = attack.meta

        # Start the conversation with the target's system prompt.
        conversation: list[Turn] = []
        if self.config.target.system_prompt:
            conversation.append(Turn("system", self.config.target.system_prompt))

        latency_ms = 0
        error = ""

        try:
            for turn in attack.build():
                # The model must SEE this turn before it can answer.
                conversation.append(turn)
                self._throttle()
                resp = self.adapter.complete(conversation)
                conversation.append(Turn("assistant", resp.text))
                latency_ms += resp.latency_ms
        except Exception as e:
            # Provider/network failure: record it, never crash the suite.
            error = f"{type(e).__name__}: {e}"

        if error:
            return AttackResult(
                attack_id=meta.id, attack_name=meta.name,
                category=meta.category, owasp=meta.owasp, atlas=meta.atlas,
                severity=meta.severity,
                success=False, confidence=0.0, conversation=conversation,
                explanation="attack failed before evaluation",
                latency_ms=latency_ms, error=error,
            )

        evaluation = attack.evaluate(conversation)
        return AttackResult(
            attack_id=meta.id, attack_name=meta.name,
            category=meta.category, owasp=meta.owasp, atlas=meta.atlas,
            severity=meta.severity,
            success=evaluation.success, confidence=evaluation.confidence,
            conversation=conversation,
            matched_signal=evaluation.matched_signal,
            explanation=evaluation.explanation,
            latency_ms=latency_ms,
        )

    def run_suite(self, attacks: list[BaseAttack]) -> list[AttackResult]:
        """Run every attack in sequence and return all results."""
        return [self.run_attack(a) for a in attacks]
