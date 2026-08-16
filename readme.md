# redforge — AI Red Team Attack Toolkit

Automated adversarial testing against any LLM endpoint, with findings mapped
to **OWASP LLM Top 10 (2025)** and **MITRE ATLAS**.

Point it at a model, run the attack suite, get a scored report. Extensible by
design: new attacks are just files dropped into `redforge/attacks/`.

## What it does

- Runs **10 attack families** (multi-prompt and multi-turn) against any target
- Supports **OpenAI, Anthropic, Ollama, generic OpenAI-compatible endpoints**, plus an offline **mock adapter** for testing without keys
- Classifies each response with a priority-ordered scorer (refusal → signal → heuristic) — optional LLM-as-judge for ambiguous cases
- Writes **JSON, Markdown, and HTML** reports with OWASP/ATLAS mapping and mitigations

## Quick start

```bash
# 1. Install dependencies into the self-contained .deps/ folder
python -m pip install --target .deps pyyaml pydantic httpx typer jinja2 rich

# 2. Offline end-to-end demo (no API key needed)
python run.py smoke

# 3. List the attack library
python run.py list

# 4. Run against a real model (set the key first, e.g. $env:OPENAI_API_KEY=...)
python run.py run --config examples/configs/example_config.yaml
```

Run against any provider without editing YAML:

```bash
python run.py run --provider openai  --model gpt-4o    --suite prompt_injection
python run.py run --provider ollama  --model llama3.2  --suite prompt_injection,info_disclosure
python run.py run --provider anthropic --model claude-sonnet-4-6
```

`rpm: 0` in config disables rate-limiting (useful for the mock/local adapters).

## Architecture

```
config.py          target / scorer / output config (Pydantic + YAML)
adapters/          one interface to every provider (openai, anthropic, ollama, generic, mock)
core/
  base_attack.py   the attack contract: build() + evaluate() + AttackMeta
  registry.py      auto-discovers attacks - no registration table
  scorer.py        refusal → signal → heuristic → default (priority matters)
  runner.py        conversation loop: system prompt, throttle, multi-turn context
  models.py        shared dataclasses (Turn, Evaluation, AttackResult, ...)
attacks/           10 attack families, one file each
reporting/         OWASP mapping + JSON/Markdown/HTML generators
cli.py             the `redforge` command (Typer + Rich)
```

## Attack library

| Attack | Category | OWASP | Notes |
|---|---|---|---|
| Direct Jailbreak | prompt_injection | LLM01:2025 | classic override family + admin override |
| Fake Prompt Boundaries | prompt_injection | LLM01:2025 | `<\|system\|>` / `</end>` delimiter injection |
| Persona Hijacking | prompt_injection | LLM01:2025 | DAN / developer-mode roleplay |
| Authority Override | prompt_injection | LLM01:2025 | operator impersonation (100% bypass in one study) |
| Indirect Injection | prompt_injection | LLM01:2025 | hidden instructions in documents |
| Encoding Obfuscation | prompt_injection | LLM01:2025 | base64 / ROT13 / reversed / leetspeak |
| Multi-Turn Escalation | prompt_injection | LLM01:2025 | benign turns that escalate into a hijack |
| System Prompt Extraction | info_disclosure | LLM07:2025 | verbatim / translation / completion tricks |
| Sensitive Info Disclosure | info_disclosure | LLM02:2025 | credentials / PII / training-data probes |
| Hallucination Elicitation | misinformation | LLM09:2025 | confident fabrication under pressure |

## Adding an attack

Drop one file into `redforge/attacks/`. The registry finds it automatically:

```python
from redforge.core.base_attack import AttackMeta, PromptAttack

class MyAttack(PromptAttack):
    meta = AttackMeta(
        id="my-attack", name="My Attack", category="prompt_injection",
        owasp="LLM01:2025", atlas="LLM Prompt Injection", severity="medium",
    )
    prompts = ["Your payload here"]
    success_signals = ["proof the attack worked"]
    refusal_signals = ["i cannot", "i'm sorry"]
```

For custom logic (multi-turn, structured documents, bespoke evaluation)
subclass `BaseAttack` and implement `build()` / `evaluate()` — see
`redforge/attacks/multi_turn_escalation.py` and `hallucination.py` for examples.

## Running the tests

```bash
python -c "import sys; sys.path.insert(0, '.deps'); sys.path.insert(0, '.'); import pytest; raise SystemExit(pytest.main(['tests', '-q']))"
```

## Ethics

redforge is for testing models you are authorized to test — your own
deployments, sandboxed models, or targets with written permission. All
payloads target system-prompt leakage and safety-bypass testing; nothing in
the library generates harmful content, extracts private user data, or targets
production systems without authorization. Respect provider terms of service.

## Roadmap

- [ ] RL-trained multi-turn adversary (adaptive sequencing)
- [ ] Multi-modal attacks (adversarial images, screenshot injection)
- [ ] MCP server scanning
- [ ] Agentic tool-misuse testing (goal hijacking, memory poisoning)
- [ ] CI/CD GitHub Action
