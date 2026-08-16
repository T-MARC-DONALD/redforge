"""OWASP LLM Top 10 (2025) quick reference.

Reports enrich every finding with the framework's description and
mitigations, so a bypass isn't just a number - it points to the fix.
"""
from __future__ import annotations

OWASP_2025: dict[str, dict] = {
    "LLM01:2025": {
        "name": "Prompt Injection",
        "description": "Manipulating model behavior via crafted inputs, including indirect injection through content the model processes.",
        "mitigations": [
            "Treat model output as untrusted data; validate before acting",
            "Separate instructions from data with explicit delimiters and instruction hierarchy",
            "Filter/sanitize inputs from external sources (documents, web content)",
            "Restrict agent tool permissions to least privilege",
        ],
    },
    "LLM02:2025": {
        "name": "Sensitive Information Disclosure",
        "description": "Model output leaks PII, credentials, or other private data - from training data or connected systems.",
        "mitigations": [
            "Minimize data exposure to the model; redact PII before input",
            "Apply output filtering for secrets and PII patterns",
            "Enforce access controls on any data source the model can reach",
        ],
    },
    "LLM07:2025": {
        "name": "System Prompt Leakage",
        "description": "Attackers extract the hidden system prompt via social engineering, which enables targeted follow-up attacks.",
        "mitigations": [
            "Treat the system prompt as sensitive; do not echo it in outputs",
            "Add explicit instructions not to reveal internal directives",
            "Monitor for extraction patterns in logs",
        ],
    },
    "LLM09:2025": {
        "name": "Misinformation",
        "description": "The model produces false or fabricated content (hallucinations) presented with false confidence.",
        "mitigations": [
            "Ground responses in retrievable sources (RAG with citations)",
            "Add hedging instructions for unverifiable factual claims",
            "Human review for high-stakes domains (medical, legal, financial)",
        ],
    },
}


def describe(owasp_id: str) -> dict:
    """Return the framework entry for an OWASP id (or a fallback)."""
    entry = OWASP_2025.get(owasp_id)
    if entry:
        return {"id": owasp_id, **entry}
    return {
        "id": owasp_id,
        "name": owasp_id,
        "description": "No framework entry defined yet.",
        "mitigations": [],
    }
