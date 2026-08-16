"""redforge.core.models - shared data structures.

Every layer of the toolkit (adapters, attacks, runner, reporting) passes
these same objects around, so the interfaces stay consistent. Using plain
dataclasses (no pydantic here) keeps them lightweight: these are created
thousands of times per run, not validated once like config.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Turn:
    """A single message in a conversation.

    role is one of "system" | "user" | "assistant". The system turn holds the
    target's system prompt; user turns are the attack prompts; assistant turns
    are the model's replies (recorded as the attack progresses).
    """
    role: str
    content: str


@dataclass
class Evaluation:
    """A judge's verdict on whether an attack succeeded.

    success        - True if the model was bypassed (leaked / complied)
    confidence     - 0.0..1.0, how sure the scorer is
    matched_signal - the concrete text/pattern that triggered the verdict
    explanation    - human-readable reasoning
    """
    success: bool
    confidence: float
    matched_signal: str = ""
    explanation: str = ""


@dataclass
class AdapterResponse:
    """Raw response from a target model plus timing.

    text       - the assistant's message content
    latency_ms - round-trip time in milliseconds
    raw        - the full provider response dict, kept for debugging
    """
    text: str
    latency_ms: int
    raw: dict = field(default_factory=dict)


@dataclass
class AttackResult:
    """The complete, self-contained record of one attack against one model.

    This is what the reporting layer consumes. It carries enough context to
    reproduce the test (the full conversation) and enough metadata to map it
    to frameworks (owasp / atlas / category / severity).
    """
    attack_id: str          # e.g. "direct-jailbreak-001"
    attack_name: str        # human-readable name
    category: str           # attack category, e.g. "prompt_injection"
    owasp: str              # e.g. "LLM01:2025"
    atlas: str              # e.g. "ATLAS.T0054"
    severity: str           # low | medium | high | critical

    success: bool
    confidence: float
    conversation: list[Turn] = field(default_factory=list)
    matched_signal: str = ""
    explanation: str = ""
    latency_ms: int = 0
    error: str = ""

    @property
    def verdict(self) -> str:
        """Human-readable outcome label."""
        return "BYPASSED" if self.success else "BLOCKED"
