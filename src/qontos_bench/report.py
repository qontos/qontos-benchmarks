"""Generate benchmark reports in JSON and human-readable Markdown formats."""

from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import qontos_bench

# ---------------------------------------------------------------------------
# Lazy import: BenchmarkResult may come from runner, but we accept dicts too.
# ---------------------------------------------------------------------------

try:
    from qontos_bench.runner import BenchmarkResult  # noqa: F401 – used by callers
except Exception:  # pragma: no cover – runner may pull heavy deps
    pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_json_report(
    results: list,
    *,
    suite: str = "correctness",
    backend: str = "qiskit_aer_statevector",
    shots: int = 8192,
    seed: int = 42,
    readiness: dict | None = None,
) -> dict:
    """Build a structured JSON report dict from a list of benchmark results.

    Each element in *results* can be either a ``BenchmarkResult`` dataclass
    (with a ``.to_dict()`` method) or a plain dict with at minimum the keys
    ``name``, ``qubits``/``num_qubits``, ``fidelity``, ``passed``,
    ``latency_ms``/``execution_time_ms``.
    """
    normalised: list[dict] = []
    for r in results:
        d = r.to_dict() if hasattr(r, "to_dict") else dict(r)
        # Normalise key names so the output always matches the new schema.
        entry: dict = {
            "name": d.get("name", ""),
            "qubits": d.get("qubits", d.get("num_qubits", 0)),
            "family": d.get("family", "core"),
            "fidelity": d.get("fidelity", 0.0),
            "passed": d.get("passed", False),
            "latency_ms": d.get("latency_ms", d.get("execution_time_ms", 0.0)),
            "shots": d.get("shots", shots),
        }
        if "expected_states" in d:
            entry["expected_states"] = d["expected_states"]
        if "metadata" in d:
            entry["metadata"] = dict(d["metadata"])
        if "top_counts" in d:
            entry["top_counts"] = d["top_counts"]
        elif "counts" in d:
            # Grab the top-4 counts for the summary.
            counts = d["counts"]
            top = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:4])
            entry["top_counts"] = top
        normalised.append(entry)

    total = len(normalised)
    passed = sum(1 for r in normalised if r["passed"])
    failed = total - passed
    fidelities = [r["fidelity"] for r in normalised]
    avg_fidelity = sum(fidelities) / total if total else 0.0
    total_latency = sum(r["latency_ms"] for r in normalised)
    family_summary = _build_family_summary(normalised)
    stressor_summary = _build_stressor_summary(normalised)
    closure_summary = _build_closure_summary(family_summary, stressor_summary)

    report: dict = {
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "suite": suite,
        "environment": {
            "python_version": platform.python_version(),
            "qontos_version": qontos_bench.__version__,
            "backend": backend,
            "shots": shots,
            "seed": seed,
        },
        "results": normalised,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "avg_fidelity": round(avg_fidelity, 4),
            "total_latency_ms": round(total_latency, 1),
        },
        "family_summary": family_summary,
        "stressor_summary": stressor_summary,
        "closure_summary": closure_summary,
    }
    if readiness is not None:
        report["readiness"] = readiness
    return report


def generate_markdown_report(
    results: list,
    *,
    suite: str = "correctness",
    readiness: dict | None = None,
) -> str:
    """Return a human-readable Markdown string summarising benchmark results.

    Accepts the same *results* list as :func:`generate_json_report` (either
    ``BenchmarkResult`` objects or plain dicts).
    """
    report = generate_json_report(results, suite=suite, readiness=readiness)
    return _render_markdown(report)


def save_report(
    results: list,
    output_dir: str = "reports",
    *,
    suite: str = "correctness",
    backend: str = "qiskit_aer_statevector",
    shots: int = 8192,
    seed: int = 42,
    readiness: dict | None = None,
) -> tuple[str, str]:
    """Persist both JSON and Markdown reports to *output_dir*.

    Returns ``(json_path, md_path)``.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    report = generate_json_report(
        results, suite=suite, backend=backend, shots=shots, seed=seed, readiness=readiness,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    json_path = os.path.join(output_dir, f"benchmark_{timestamp}.json")
    with open(json_path, "w") as fh:
        json.dump(report, fh, indent=2, default=str)

    md_text = _render_markdown(report)
    md_path = os.path.join(output_dir, f"benchmark_{timestamp}.md")
    with open(md_path, "w") as fh:
        fh.write(md_text)

    # Also write latest.json for easy CI consumption.
    latest_json = os.path.join(output_dir, "latest.json")
    with open(latest_json, "w") as fh:
        json.dump(report, fh, indent=2, default=str)

    return json_path, md_path


# ---------------------------------------------------------------------------
# Legacy compatibility shim
# ---------------------------------------------------------------------------


def generate_report(
    results: list,
    output_dir: str = "benchmarks/reports",
    *,
    suite: str = "correctness",
    readiness: dict | None = None,
) -> str:
    """Legacy entry-point used by the CLI.  Returns the JSON report path."""
    json_path, _md_path = save_report(results, output_dir, suite=suite, readiness=readiness)
    return json_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _render_markdown(report: dict) -> str:
    """Render a report dict as Markdown."""
    lines: list[str] = []
    env = report.get("environment", {})
    summary = report.get("summary", {})

    lines.append(f"# QONTOS Benchmark Report — {report.get('suite', 'unknown')}")
    lines.append("")
    lines.append(f"**Generated**: {report.get('timestamp', 'N/A')}")
    lines.append(f"**Backend**: {env.get('backend', 'N/A')}")
    lines.append(f"**Shots**: {env.get('shots', 'N/A')}")
    lines.append(f"**Seed**: {env.get('seed', 'N/A')}")
    lines.append(f"**Python**: {env.get('python_version', 'N/A')}")
    lines.append(f"**QONTOS version**: {env.get('qontos_version', 'N/A')}")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Benchmark | Family | Qubits | Fidelity | Latency (ms) | Status |")
    lines.append("|-----------|--------|--------|----------|--------------|--------|")

    for r in report.get("results", []):
        status = "PASS" if r.get("passed") else "FAIL"
        lines.append(
            f"| {r.get('name', '?')} "
            f"| {r.get('family', 'core')} "
            f"| {r.get('qubits', '?')} "
            f"| {r.get('fidelity', 0):.3f} "
            f"| {r.get('latency_ms', 0):.1f} "
            f"| {status} |"
        )

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total**: {summary.get('total', 0)}")
    lines.append(f"- **Passed**: {summary.get('passed', 0)}")
    lines.append(f"- **Failed**: {summary.get('failed', 0)}")
    lines.append(f"- **Pass rate**: {summary.get('pass_rate', 0):.1%}")
    lines.append(f"- **Average fidelity**: {summary.get('avg_fidelity', 0):.4f}")
    lines.append(f"- **Total latency**: {summary.get('total_latency_ms', 0):.1f} ms")
    lines.append("")

    family_summary = report.get("family_summary", [])
    if family_summary:
        lines.append("## Family Summary")
        lines.append("")

    stressor_summary = report.get("stressor_summary", [])
    if stressor_summary:
        lines.append("## Stressor Summary")
        lines.append("")
        lines.append("| Stressor | Total | Passed | Pass Rate | Avg Fidelity |")
        lines.append("|--------|-------|--------|-----------|--------------|")
        for stressor in stressor_summary:
            lines.append(
                f"| {stressor.get('stressor', 'unknown')} "
                f"| {stressor.get('total', 0)} "
                f"| {stressor.get('passed', 0)} "
                f"| {stressor.get('pass_rate', 0):.1%} "
                f"| {stressor.get('avg_fidelity', 0):.4f} |"
            )
        lines.append("")
        lines.append("| Family | Total | Passed | Pass Rate | Avg Fidelity |")
        lines.append("|--------|-------|--------|-----------|--------------|")
        for family in family_summary:
            lines.append(
                f"| {family.get('family', 'unknown')} "
                f"| {family.get('total', 0)} "
                f"| {family.get('passed', 0)} "
                f"| {family.get('pass_rate', 0):.1%} "
                f"| {family.get('avg_fidelity', 0):.4f} |"
            )
        lines.append("")

    closure_summary = report.get("closure_summary") or {}
    if closure_summary:
        lines.append("## Transduction Closure Summary")
        lines.append("")
        lines.append(f"- **Closure status**: {closure_summary.get('closure_status', 'N/A')}")
        lines.append(f"- **Closure score**: {closure_summary.get('closure_score', 'N/A')}")
        lines.append(
            f"- **Transduction-link pass rate**: {closure_summary.get('transduction_link_pass_rate', 'N/A')}"
        )
        lines.append(
            f"- **Retry pass rate**: {closure_summary.get('retry_pass_rate', 'N/A')}"
        )
        lines.append(
            f"- **Logical-patch pass rate**: {closure_summary.get('logical_patch_pass_rate', 'N/A')}"
        )
        lines.append(
            f"- **Remote-entangling pass rate**: {closure_summary.get('remote_entangling_pass_rate', 'N/A')}"
        )
        lines.append(
            f"- **Calibration pass rate**: {closure_summary.get('calibration_pass_rate', 'N/A')}"
        )
        lines.append(
            f"- **Phase-stability pass rate**: {closure_summary.get('phase_stability_pass_rate', 'N/A')}"
        )
        lines.append("")

    readiness = report.get("readiness")
    if readiness:
        lines.append("## Readiness")
        lines.append("")
        gate_status = readiness.get("gate_status", {})
        lines.append("| Gate | Status | Rationale |")
        lines.append("|------|--------|-----------|")
        for gate in ("S1", "P1", "P2"):
            entry = gate_status.get(gate, {})
            lines.append(
                f"| {gate} | {entry.get('status', 'UNKNOWN')} | {entry.get('rationale', 'N/A')} |"
            )
        actions = readiness.get("prioritized_actions", [])
        if actions:
            lines.append("")
            lines.append("Top readiness actions:")
            for action in actions[:5]:
                lines.append(f"- {action}")
        lines.append("")

    return "\n".join(lines)


def _build_family_summary(results: list[dict]) -> list[dict]:
    families: dict[str, dict[str, float | int | str]] = {}
    for result in results:
        family = str(result.get("family", "core"))
        bucket = families.setdefault(
            family,
            {
                "family": family,
                "total": 0,
                "passed": 0,
                "_fidelity_sum": 0.0,
            },
        )
        bucket["total"] += 1
        bucket["passed"] += 1 if result.get("passed") else 0
        bucket["_fidelity_sum"] += float(result.get("fidelity", 0.0))

    summary: list[dict] = []
    for family in sorted(families):
        bucket = families[family]
        total = int(bucket["total"])
        passed = int(bucket["passed"])
        fidelity_sum = float(bucket["_fidelity_sum"])
        summary.append(
            {
                "family": family,
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed / total, 4) if total else 0.0,
                "avg_fidelity": round(fidelity_sum / total, 4) if total else 0.0,
            }
        )

    return summary


def _build_stressor_summary(results: list[dict]) -> list[dict]:
    stressors: dict[str, dict[str, float | int | str]] = {}
    for result in results:
        metadata = result.get("metadata") or {}
        for stressor in metadata.get("stressors", []):
            bucket = stressors.setdefault(
                str(stressor),
                {
                    "stressor": str(stressor),
                    "total": 0,
                    "passed": 0,
                    "_fidelity_sum": 0.0,
                },
            )
            bucket["total"] += 1
            bucket["passed"] += 1 if result.get("passed") else 0
            bucket["_fidelity_sum"] += float(result.get("fidelity", 0.0))

    summary: list[dict] = []
    for stressor in sorted(stressors):
        bucket = stressors[stressor]
        total = int(bucket["total"])
        passed = int(bucket["passed"])
        fidelity_sum = float(bucket["_fidelity_sum"])
        summary.append(
            {
                "stressor": stressor,
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed / total, 4) if total else 0.0,
                "avg_fidelity": round(fidelity_sum / total, 4) if total else 0.0,
            }
        )

    return summary


def _build_closure_summary(
    family_summary: list[dict],
    stressor_summary: list[dict],
) -> dict:
    family_rates = {
        str(entry.get("family")): float(entry.get("pass_rate", 0.0))
        for entry in family_summary
        if entry.get("family") is not None
    }
    stressor_rates = {
        str(entry.get("stressor")): float(entry.get("pass_rate", 0.0))
        for entry in stressor_summary
        if entry.get("stressor") is not None
    }

    transduction_link_rate = stressor_rates.get("transduction_link", 0.0)
    retry_rate = stressor_rates.get("retry", transduction_link_rate)
    calibration_rate = stressor_rates.get("calibration", transduction_link_rate)
    phase_stability_rate = stressor_rates.get("phase_stability", transduction_link_rate)
    logical_patch_sources = [
        family_rates.get("logical_patch_transport"),
        family_rates.get("syndrome_burst"),
    ]
    logical_patch_values = [value for value in logical_patch_sources if value is not None]
    logical_patch_rate = round(sum(logical_patch_values) / len(logical_patch_values), 4) if logical_patch_values else 0.0
    remote_entangling_rate = family_rates.get("remote_entangling", 0.0)

    closure_score = round(
        (
            transduction_link_rate * 0.30
            + retry_rate * 0.15
            + calibration_rate * 0.15
            + phase_stability_rate * 0.10
            + logical_patch_rate * 0.20
            + remote_entangling_rate * 0.10
        ),
        4,
    )

    if closure_score >= 0.98:
        closure_status = "STRONG"
    elif closure_score >= 0.94:
        closure_status = "PASSABLE"
    elif closure_score >= 0.85:
        closure_status = "MARGINAL"
    else:
        closure_status = "OPEN"

    return {
        "closure_status": closure_status,
        "closure_score": closure_score,
        "transduction_link_pass_rate": round(transduction_link_rate, 4),
        "retry_pass_rate": round(retry_rate, 4),
        "calibration_pass_rate": round(calibration_rate, 4),
        "phase_stability_pass_rate": round(phase_stability_rate, 4),
        "logical_patch_pass_rate": round(logical_patch_rate, 4),
        "remote_entangling_pass_rate": round(remote_entangling_rate, 4),
    }
