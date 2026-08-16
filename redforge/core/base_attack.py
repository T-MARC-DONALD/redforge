"""redforge.core.base_attack - the attack contract.

An "attack" in redforge has two jobs:

    1. build()    - generate the conversation that carries the attack
                    (one or more user turns; multi-turn is fully supported)
    2. evaluate() - look at the resulting conversation and judge whether
                    the attack succeeded

Every attack also carries AttackMeta: framework IDs (OWASP / ATLAS),
category, severity, and a description. These metadata fields are what make
the reports meaningful - findings map back to industry frameworks.

Two levels of abstraction:

    BaseAttack  - implement build() and evaluate() yourself (for attacks
                  with custom logic, e.g. multi-turn escalation).
    PromptAttack- declare `prompts` + signal lists; evaluation is handled
                  by the shared scorer. Most attacks are this simple.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from redforge.core.models import Evaluation, Turn


@dataclass(frozen=True)
class AttackMeta:
    """Immutable metadata every attack must declare."""
    id: str                 # unique machine-readable id, e.g. "direct-jailbreak"
    name: str               # human-readable name
    category: str           # attack family, e.g. "prompt_injection"
    owasp: str              # OWASP LLM Top 10 (2025) id, e.g. "LLM01:2025"
    atlas: str              # MITRE ATLAS technique name
    severity: str = "medium"  # low | medium | high | critical
    description: str = ""


class BaseAttack(ABC):
    """Abstract attack. Subclasses set `meta` and implement the two methods."""

    meta: AttackMeta = None  # type: ignore[assignment] - set by subclasses

    @abstractmethod
    def build(self) -> list[Turn]:
        """Generate the attack's conversation.

        The runner sends each returned turn IN ORDER, feeding the model's
        previous replies back as context - so turn N can build on turn 1.
        """

    @abstractmethod
    def evaluate(self, conversation: list[Turn]) -> Evaluation:
        """Judge the conversation.

        `conversation` contains the system turn (from config), every user
        turn, and every assistant reply - the full record.
        """


class PromptAttack(BaseAttack):
    """Declarative attack: prompts + signal lists, no logic to write.

    Subclasses only declare class attributes:

        prompts          - one user turn per entry (sent sequentially)
        success_signals  - response text proving the attack worked
        refusal_signals  - response text proving the model refused
        heuristic_patterns - optional extra (regex, score, reason) rules

    evaluate() delegates to the shared scorer, checking every assistant
    turn (any variant bypassing = attack succeeded).
    """

    prompts: list[str] = []
    success_signals: list[str] = []
    refusal_signals: list[str] = []
    heuristic_patterns: list[tuple[str, float, str]] = []

    def build(self) -> list[Turn]:
        return [Turn("user", p) for p in self.prompts]

    def evaluate(self, conversation: list[Turn]) -> Evaluation:
        from redforge.core.scorer import evaluate_conversation

        return evaluate_conversation(
            conversation,
            success_signals=self.success_signals,
            refusal_signals=self.refusal_signals or None,
            heuristic_patterns=self.heuristic_patterns or None,
        )
