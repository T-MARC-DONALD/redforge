"""redforge.reporting.generator - turn AttackResults into report files.

Three formats, same data:

    JSON     - machine-readable, for CI/CD and further analysis
    Markdown - human-readable, for docs and pull requests
    HTML     - self-contained styled page, open in any browser

All formats are written from one summary structure, so numbers never
disagree between formats.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Template

from redforge.config import RedforgeConfig
from redforge.core.models import AttackResult
from redforge.reporting.owasp_mapping import describe

_TEMPLATE_PATH = Path(__file__).parent / "templates" / "report.html.j2"


def summarize(results: list[AttackResult], model: str) -> dict:
    """Compute run statistics shared by every report format."""
    total = len(results)
    bypassed = sum(1 for r in results if r.success)
    blocked = total - bypassed
    rate = (bypassed / total * 100) if total else 0.0

    by_category: dict[str, dict] = {}
    by_severity: dict[str, dict] = {}
    for r in results:
        cat = by_category.setdefault(r.category, {"total": 0, "bypassed": 0})
        cat["total"] += 1
        cat["bypassed"] += int(r.success)
        sev = by_severity.setdefault(r.severity, {"total": 0, "bypassed": 0})
        sev["total"] += 1
        sev["bypassed"] += int(r.success)

    return {
        "model": model,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "bypassed": bypassed,
        "blocked": blocked,
        "bypass_rate": round(rate, 1),
        "by_category": by_category,
        "by_severity": by_severity,
    }


def _result_to_dict(r: AttackResult) -> dict:
    """Serialize one AttackResult for JSON output."""
    return {
        "attack_id": r.attack_id,
        "attack_name": r.attack_name,
        "category": r.category,
        "owasp": r.owasp,
        "atlas": r.atlas,
        "severity": r.severity,
        "verdict": r.verdict,
        "success": r.success,
        "confidence": round(r.confidence, 2),
        "matched_signal": r.matched_signal,
        "explanation": r.explanation,
        "latency_ms": r.latency_ms,
        "error": r.error,
        "conversation": [
            {"role": t.role, "content": t.content} for t in r.conversation
        ],
    }


def _render_markdown(results: list[AttackResult], stats: dict) -> str:
    lines = [
        f"# redforge — AI Red Team Report",
        "",
        f"**Model:** `{stats['model']}` · **Run:** {stats['generated_at']}",
        "",
        f"**Bypass rate:** {stats['bypassed']}/{stats['total']} ({stats['bypass_rate']}%)",
        "",
        "## By category",
        "",
        "| Category | Total | Bypassed | Rate |",
        "|---|---|---|---|",
    ]
    for cat, v in sorted(stats["by_category"].items()):
        pct = v["bypassed"] / v["total"] * 100 if v["total"] else 0
        lines.append(f"| {cat} | {v['total']} | {v['bypassed']} | {pct:.0f}% |")

    lines += ["", "## Findings", "", "| ID | Attack | OWASP | Severity | Verdict | Conf | Signal |", "|---|---|---|---|---|---|---|"]
    for r in results:
        conf = f"{r.confidence:.0%}"
        signal = (r.matched_signal or "")[:40]
        lines.append(
            f"| {r.attack_id} | {r.attack_name} | {r.owasp} | {r.severity} | "
            f"{r.verdict} | {conf} | {signal} |"
        )

    lines += ["", "## Details", ""]
    for r in results:
        lines += [f"### {r.attack_id} — {r.attack_name} ({r.verdict})", ""]
        lines.append(f"- **Confidence:** {r.confidence:.0%} · **Signal:** {r.matched_signal or '—'}")
        lines.append(f"- **Explanation:** {r.explanation}")
        if r.error:
            lines.append(f"- **Error:** {r.error}")
        for t in r.conversation:
            snippet = t.content.replace("\n", " ")[:160]
            lines.append(f"- *{t.role}*: {snippet}")
        lines.append("")
    return "\n".join(lines)


def generate(
    results: list[AttackResult],
    config: RedforgeConfig,
    output_dir: str | Path,
) -> list[Path]:
    """Write every configured report format. Returns the created file paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = summarize(results, config.target.model)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_key = config.target.model.replace("/", "-").replace(":", "-")
    stem = f"report_{stamp}_{model_key}"

    written: list[Path] = []
    formats = [f.lower() for f in config.output.formats]

    if "json" in formats:
        path = output_dir / f"{stem}.json"
        path.write_text(
            json.dumps(
                {"summary": stats, "results": [_result_to_dict(r) for r in results]},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        written.append(path)

    if "markdown" in formats:
        path = output_dir / f"{stem}.md"
        path.write_text(_render_markdown(results, stats), encoding="utf-8")
        written.append(path)

    if "html" in formats:
        path = output_dir / f"{stem}.html"
        template = Template(_TEMPLATE_PATH.read_text(encoding="utf-8"))
        path.write_text(
            template.render(
                stats=stats,
                results=results,
                owasp=describe,
            ),
            encoding="utf-8",
        )
        written.append(path)

    return written
