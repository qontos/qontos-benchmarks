"""Generate benchmark reports in JSON and human-readable formats."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.runner import BenchmarkResult


def generate_report(
    results: list[BenchmarkResult],
    output_dir: str = "benchmarks/reports",
) -> str:
    """Generate a benchmark report and write it to disk.

    Creates two files:
      - A JSON report with full details of every benchmark result.
      - A human-readable text summary.

    Returns the path to the JSON report file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # --- JSON report ---
    report_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_benchmarks": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [r.to_dict() for r in results],
    }

    json_path = os.path.join(output_dir, f"benchmark_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2, default=str)

    # --- Text summary ---
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("QONTOS Benchmark Report")
    lines.append(f"Generated: {report_data['generated_at']}")
    lines.append("=" * 60)
    lines.append("")

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        lines.append(
            f"  [{status}] {r.name}: "
            f"fidelity={r.fidelity:.4f}, "
            f"dominant={r.dominant_state} ({r.dominant_probability:.4f}), "
            f"time={r.execution_time_ms:.1f}ms"
        )

    lines.append("")
    lines.append(f"  {report_data['passed']}/{report_data['total_benchmarks']} benchmarks passed")
    lines.append("=" * 60)

    txt_path = os.path.join(output_dir, f"benchmark_{timestamp}.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Also write a latest symlink / copy for easy CI consumption
    latest_json = os.path.join(output_dir, "latest.json")
    with open(latest_json, "w") as f:
        json.dump(report_data, f, indent=2, default=str)

    return json_path
