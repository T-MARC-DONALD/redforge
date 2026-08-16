"""Registry tests: discovery finds all attacks, filtering works."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redforge.core.registry import discover_attacks, filter_by_suites, instantiate  # noqa: E402


def test_discovers_attacks():
    attacks = discover_attacks()
    ids = {c.meta.id for c in attacks}
    # The core library should all be found with no manual registration.
    assert "direct-jailbreak" in ids
    assert "system-prompt-extraction" in ids
    assert "multi-turn-escalation" in ids
    assert "hallucination" in ids
    assert len(attacks) >= 10


def test_every_attack_has_metadata():
    for cls in discover_attacks():
        m = cls.meta
        assert m.id and m.name and m.category
        assert m.owasp.startswith("LLM") or m.owasp == ""
        assert m.severity in ("low", "medium", "high", "critical")


def test_filter_by_suites():
    attacks = discover_attacks()
    filtered = filter_by_suites(attacks, ["misinformation"])
    assert all(c.meta.category == "misinformation" for c in filtered)
    assert any(c.meta.id == "hallucination" for c in filtered)


def test_empty_suites_keeps_all():
    assert len(filter_by_suites(discover_attacks(), [])) == len(discover_attacks())


def test_instantiate_runs():
    instances = instantiate(discover_attacks())
    assert all(callable(a.build) for a in instances)
