"""Config tests: loading, defaults, and overrides."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redforge.config import RedforgeConfig, TargetConfig  # noqa: E402


def test_defaults():
    cfg = RedforgeConfig()
    assert cfg.target.provider == "openai"
    assert cfg.target.model == "gpt-4o"
    assert cfg.target.rpm == 60
    assert cfg.suites == []


def test_example_config_loads():
    cfg = RedforgeConfig.load(ROOT / "examples" / "configs" / "example_config.yaml")
    assert cfg.target.provider == "openai"
    assert cfg.target.model == "gpt-4o"
    assert "prompt_injection" in cfg.suites
    assert "html" in cfg.output.formats


def test_bad_rpm_rejected():
    with pytest.raises(Exception):
        TargetConfig(rpm="not-a-number")  # type: ignore[arg-type]


def test_from_dict_override():
    cfg = RedforgeConfig.from_dict({"target": {"provider": "mock", "model": "m"}})
    assert cfg.target.provider == "mock"
    assert cfg.target.model == "m"
