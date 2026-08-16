"""redforge.config - configuration loading and validation.

The whole toolkit is driven by one config object. We model it with three
sub-sections, each its own Pydantic model:

    TargetConfig   - WHO we attack and HOW we reach it
    ScorerConfig   - HOW we judge whether an attack succeeded
    OutputConfig   - WHERE and in WHICH formats we write reports

Pydantic gives us three things for free:
    1. Type checking  - a bad value (e.g. rpm="fast") fails loudly at load
    2. Defaults       - every field has a sensible fallback
    3. Validation     - clear error messages instead of silent breakage
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class TargetConfig(BaseModel):
    """Everything needed to reach and talk to the model under test.

    `provider` selects which adapter is used at runtime. The four values map
    to concrete adapter classes:
        openai     -> adapters.OpenAIAdapter     (OpenAI + any OpenAI-compatible)
        anthropic  -> adapters.AnthropicAdapter  (Claude models)
        ollama     -> adapters.OllamaAdapter     (local models, no API key)
        generic    -> adapters.GenericAdapter    (any OpenAI-compatible URL)
    """
    provider: str = "openai"
    model: str = "gpt-4o"

    # The environment variable that holds the API key. None means "no key
    # needed" (true for Ollama). We reference the env var NAME, never the
    # secret itself, so keys never end up in config files or logs.
    api_key_env: Optional[str] = "OPENAI_API_KEY"

    # Only required for generic/Ollama. For openai/anthropic the adapter
    # already knows the canonical endpoint.
    base_url: Optional[str] = None

    # The system prompt we install on the simulated target. Attacks try to
    # make the model violate or leak this.
    system_prompt: str = "You are a helpful assistant."

    temperature: float = 0.0      # 0 = deterministic, better for reproducible tests
    max_tokens: int = 1024
    timeout: float = 60.0         # seconds per request

    # Requests-per-minute cap. Red teaming should be polite: we space requests
    # out so we don't hammer a provider's free tier into a rate-limit.
    rpm: int = 60

    # Extra HTTP headers (e.g. OpenRouter wants HTTP-Referer / X-Title).
    headers: dict[str, str] = Field(default_factory=dict)


class ScorerConfig(BaseModel):
    """How we decide if an attack worked.

    By default we use deterministic signal matching (fast, free, repeatable).
    Optionally we can call a second LLM as a "judge" to evaluate responses
    that rule-based matching can't classify confidently.
    """
    use_llm_judge: bool = False
    judge_provider: str = "openai"
    judge_model: str = "gpt-4o-mini"


class OutputConfig(BaseModel):
    """Where reports land and which formats are generated."""
    directory: Path = Path("results")
    formats: list[str] = Field(default_factory=lambda: ["json", "markdown"])


class RedforgeConfig(BaseModel):
    """Root config: the three sub-sections above, plus which suites to run.

    `suites` is a list of attack-category names. Empty list = run everything.
    """
    target: TargetConfig = Field(default_factory=TargetConfig)
    scorer: ScorerConfig = Field(default_factory=ScorerConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    suites: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "RedforgeConfig":
        """Load a YAML file (or defaults if the file is missing) into a config."""
        path = Path(path)
        raw: dict[str, Any] = {}
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        return cls.model_validate(raw)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RedforgeConfig":
        """Build a config straight from a plain dict (used by the CLI)."""
        return cls.model_validate(data)
