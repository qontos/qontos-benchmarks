"""CLI for running benchmarks: python -m benchmarks.cli"""

from __future__ import annotations

import argparse
import sys

from qontos_bench.runner import BenchmarkRunner
from qontos_bench.report import generate_report


def main() -> int:
    parser = argparse.ArgumentParser(description="QONTOS Benchmark Suite")
    parser.add_argument(
        "--shots",
        type=int,
        default=8192,
        help="Number of shots per circuit (default: 8192)",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/reports",
        help="Output directory for reports (default: benchmarks/reports)",
    )
    parser.add_argument(
        "--circuit",
        choices=[
            "bell",
            "ghz",
            "ghz5",
            "qft",
            "bv",
            "vqe",
            "random",
            "photonic-bell",
            "teleport",
            "remote-cnot",
            "distributed-ghz",
            "syndrome-burst",
            "entanglement-swap",
            "teleport-ladder",
            "remote-parity",
            "distributed-ghz-ladder",
            "patch-syndrome",
            "transducer-cal",
            "logical-patch-handoff",
            "all",
            "hybrid",
            "hybrid-stress",
            "transduction-closure",
            "full",
        ],
        default="all",
        help="Which benchmark to run (default: all)",
    )
    args = parser.parse_args()

    runner = BenchmarkRunner(shots=args.shots)

    suite = "correctness"
    if args.circuit == "all":
        results = runner.run_all()
    elif args.circuit == "hybrid":
        results = runner.run_hybrid_pack()
        suite = "hybrid"
    elif args.circuit == "hybrid-stress":
        results = runner.run_hybrid_stress_pack()
        suite = "hybrid_stress"
    elif args.circuit == "transduction-closure":
        results = runner.run_transduction_closure_pack()
        suite = "transduction_closure"
    elif args.circuit == "full":
        results = runner.run_suite("full")
        suite = "full-stack"
    else:
        results = [runner.run_single(args.circuit)]
        if args.circuit in {
            "photonic-bell",
            "teleport",
            "remote-cnot",
            "distributed-ghz",
            "syndrome-burst",
        }:
            suite = "hybrid"
        elif args.circuit in {
            "entanglement-swap",
            "teleport-ladder",
            "remote-parity",
            "distributed-ghz-ladder",
            "patch-syndrome",
        }:
            suite = "hybrid_stress"
        elif args.circuit in {
            "transducer-cal",
            "logical-patch-handoff",
        }:
            suite = "transduction_closure"

    report_path = generate_report(results, args.output, suite=suite)

    # Print summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)

    print(f"\n{'=' * 60}")
    print("QONTOS Benchmark Report")
    print(f"{'=' * 60}")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(
            f"  [{status}] {r.name}: "
            f"fidelity={r.fidelity:.4f}, "
            f"time={r.execution_time_ms:.1f}ms"
        )
    print(f"\n  {passed}/{total} benchmarks passed")
    print(f"  Report: {report_path}")
    print(f"{'=' * 60}")

    # Exit with failure if any benchmark failed
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
