"""Tests for the benchmark runner and report generation pipeline.

Validates:
- Runner executes Bell pair benchmark (via mocked pipeline)
- Runner produces correct report structure
- All benchmark circuits are defined
- Fidelity computation is correct
- Pass/fail threshold works
- Summary statistics are accurate
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from qontos_bench.runner import BenchmarkResult, BenchmarkRunner
from qontos_bench.report import (
    generate_json_report,
    generate_markdown_report,
    save_report,
)


# ---------------------------------------------------------------------------
# Helpers — mock the QONTOS pipeline so tests run without real deps
# ---------------------------------------------------------------------------

def _fake_execute(self, qasm: str, shots: int):
    """Simulate a noiseless execution by returning ideal counts.

    The helper inspects the QASM shape so tests remain realistic across
    Bell/GHZ/QFT/BV/VQE/random circuits without pulling in real simulators.
    """
    qreg_match = re.search(r"qreg q\[(\d+)\];", qasm)
    creg_match = re.search(r"creg c\[(\d+)\];", qasm)
    qreg_size = int(qreg_match.group(1)) if qreg_match else 2
    creg_size = int(creg_match.group(1)) if creg_match else qreg_size

    half = shots // 2

    # Bernstein-Vazirani: classical register is smaller than q register,
    # and oracle CNOTs into the final ancilla encode the secret string.
    if creg_size < qreg_size:
        ancilla = qreg_size - 1
        secret_bits = ["0"] * creg_size
        for control in re.findall(rf"cx q\[(\d+)\],q\[{ancilla}\];", qasm):
            idx = int(control)
            if idx < creg_size:
                secret_bits[idx] = "1"
        secret = "".join(secret_bits)
        return {secret: shots}, 10.0

    width = creg_size
    zero = "0" * width
    one = "1" * width

    # GHZ/Bell-like entanglement circuits.
    if "h q[0];" in qasm and "cx q[0],q[1];" in qasm and "cp(" not in qasm:
        return {zero: half, one: shots - half}, 10.0

    # QFT-style uniform-output circuit: a couple of valid basis states are enough
    # for the runner to treat it as a valid distribution.
    if "cp(" in qasm or "swap q[" in qasm:
        first = format(0, f"0{width}b")
        second = format(1, f"0{width}b")
        return {first: half, second: shots - half}, 10.0

    # Default path for VQE/random-style tests.
    return {zero: half, one: shots - half}, 10.0


def _make_result(
    name: str = "test",
    fidelity: float = 1.0,
    passed: bool = True,
    qubits: int = 2,
    latency_ms: float = 10.0,
    shots: int = 8192,
) -> dict:
    """Create a minimal result dict for report tests."""
    return {
        "name": name,
        "qubits": qubits,
        "fidelity": fidelity,
        "passed": passed,
        "latency_ms": latency_ms,
        "shots": shots,
        "expected_states": ["00", "11"],
        "top_counts": {"00": shots // 2, "11": shots // 2},
    }


def _make_readiness() -> dict:
    return {
        "version": "0.1.0",
        "generated_at": "2026-04-20T00:00:00Z",
        "scenario": "software-lab baseline",
        "gate_status": {
            "S1": {"status": "OPEN", "rationale": "Device evidence is still missing."},
            "P1": {"status": "OPEN", "rationale": "Photonic evidence is still missing."},
            "P2": {"status": "OPEN", "rationale": "Hybrid closure is still missing."},
        },
        "prioritized_actions": [
            "Run the first device characterization batch and record T1/T2.",
            "Build and calibrate the first standalone transducer bench.",
        ],
    }


# ===================================================================
# Test: runner executes Bell pair benchmark
# ===================================================================

class TestRunnerExecutesBellPair:
    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_bell_pair_returns_result(self):
        runner = BenchmarkRunner(shots=1024)
        result = runner.run_bell_pair()
        assert isinstance(result, BenchmarkResult)
        assert result.name == "Bell Pair"

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_bell_pair_passes(self):
        runner = BenchmarkRunner(shots=1024)
        result = runner.run_bell_pair()
        assert result.passed is True

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_bell_pair_fidelity(self):
        runner = BenchmarkRunner(shots=1024)
        result = runner.run_bell_pair()
        # All shots land in expected states {00, 11}
        assert result.fidelity == 1.0

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_bell_pair_has_counts(self):
        runner = BenchmarkRunner(shots=1024)
        result = runner.run_bell_pair()
        assert isinstance(result.counts, dict)
        assert sum(result.counts.values()) == 1024


# ===================================================================
# Test: runner produces correct report structure
# ===================================================================

class TestRunnerReportStructure:
    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_run_all_returns_list(self):
        runner = BenchmarkRunner(shots=512)
        results = runner.run_all()
        assert isinstance(results, list)
        assert len(results) == 7  # 7 standard benchmarks

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_each_result_has_required_attrs(self):
        runner = BenchmarkRunner(shots=512)
        results = runner.run_all()
        for r in results:
            assert hasattr(r, "name")
            assert hasattr(r, "fidelity")
            assert hasattr(r, "passed")
            assert hasattr(r, "execution_time_ms")
            assert hasattr(r, "counts")
            assert hasattr(r, "expected_states")

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_to_dict_round_trip(self):
        runner = BenchmarkRunner(shots=512)
        result = runner.run_bell_pair()
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["name"] == "Bell Pair"
        assert "fidelity" in d


# ===================================================================
# Test: all benchmark circuits are defined
# ===================================================================

class TestAllBenchmarksDefined:
    def test_dispatch_contains_all_keys(self):
        runner = BenchmarkRunner()
        expected_keys = {"bell", "ghz", "ghz5", "qft", "bv", "vqe", "random"}
        dispatch = {
            "bell": runner.run_bell_pair,
            "ghz": runner.run_ghz_3,
            "ghz5": runner.run_ghz_5,
            "qft": runner.run_qft_4,
            "bv": runner.run_bernstein_vazirani,
            "vqe": runner.run_h2_vqe,
            "random": runner.run_random_5q,
        }
        assert set(dispatch.keys()) == expected_keys

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_run_single_bell(self):
        runner = BenchmarkRunner(shots=256)
        result = runner.run_single("bell")
        assert result.name == "Bell Pair"

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_run_single_unknown_raises(self):
        runner = BenchmarkRunner(shots=256)
        with pytest.raises(ValueError, match="Unknown benchmark"):
            runner.run_single("nonexistent")

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    @pytest.mark.parametrize("key", ["bell", "ghz", "ghz5", "qft", "bv", "vqe", "random"])
    def test_run_single_each(self, key: str):
        runner = BenchmarkRunner(shots=256)
        result = runner.run_single(key)
        assert isinstance(result, BenchmarkResult)
        assert result.passed is True


# ===================================================================
# Test: fidelity computation is correct
# ===================================================================

class TestFidelityComputation:
    def test_perfect_fidelity(self):
        counts = {"00": 4096, "11": 4096}
        expected = ["00", "11"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 8192)
        assert f == 1.0

    def test_zero_fidelity(self):
        counts = {"01": 4096, "10": 4096}
        expected = ["00", "11"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 8192)
        assert f == 0.0

    def test_partial_fidelity(self):
        counts = {"00": 4000, "11": 2000, "01": 1000, "10": 1192}
        expected = ["00", "11"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 8192)
        assert abs(f - 6000 / 8192) < 1e-6

    def test_empty_counts(self):
        f = BenchmarkRunner._compute_fidelity({}, ["00"], 0)
        assert f == 0.0

    def test_single_expected_state(self):
        counts = {"101": 8000, "000": 192}
        expected = ["101"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 8192)
        assert abs(f - 8000 / 8192) < 1e-6


# ===================================================================
# Test: pass/fail threshold works
# ===================================================================

class TestPassFailThreshold:
    def test_default_threshold(self):
        assert BenchmarkRunner.FIDELITY_THRESHOLD == 0.85

    @patch.object(BenchmarkRunner, "_execute", _fake_execute)
    def test_passing_result(self):
        runner = BenchmarkRunner(shots=1024)
        result = runner.run_bell_pair()
        assert result.fidelity >= runner.FIDELITY_THRESHOLD
        assert result.passed is True

    def test_threshold_boundary_pass(self):
        """Fidelity exactly at threshold should pass."""
        counts = {"00": 850, "01": 150}
        expected = ["00"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 1000)
        assert f >= 0.85
        assert f >= BenchmarkRunner.FIDELITY_THRESHOLD

    def test_threshold_boundary_fail(self):
        """Fidelity below threshold should fail."""
        counts = {"00": 840, "01": 160}
        expected = ["00"]
        f = BenchmarkRunner._compute_fidelity(counts, expected, 1000)
        assert f < BenchmarkRunner.FIDELITY_THRESHOLD

    @patch.object(BenchmarkRunner, "_execute")
    def test_low_fidelity_fails(self, mock_execute):
        """If the execution returns mostly unexpected states, result should fail."""
        mock_execute.return_value = ({"01": 7000, "10": 1000, "00": 100, "11": 92}, 5.0)
        runner = BenchmarkRunner(shots=8192)
        result = runner.run_bell_pair()
        assert result.fidelity < 0.85
        assert result.passed is False


# ===================================================================
# Test: summary statistics are accurate
# ===================================================================

class TestSummaryStatistics:
    def test_generate_json_report_summary(self):
        results = [
            _make_result("a", fidelity=1.0, passed=True, latency_ms=10.0),
            _make_result("b", fidelity=0.9, passed=True, latency_ms=20.0),
            _make_result("c", fidelity=0.5, passed=False, latency_ms=30.0),
        ]
        report = generate_json_report(results)
        s = report["summary"]
        assert s["total"] == 3
        assert s["passed"] == 2
        assert s["failed"] == 1
        assert abs(s["pass_rate"] - 2 / 3) < 1e-3
        assert abs(s["avg_fidelity"] - (1.0 + 0.9 + 0.5) / 3) < 1e-3
        assert abs(s["total_latency_ms"] - 60.0) < 0.2

    def test_generate_json_report_with_readiness(self):
        results = [_make_result("a", fidelity=1.0, passed=True, latency_ms=10.0)]
        readiness = _make_readiness()
        report = generate_json_report(results, readiness=readiness)
        assert report["readiness"]["scenario"] == "software-lab baseline"
        assert report["readiness"]["gate_status"]["S1"]["status"] == "OPEN"

    def test_generate_markdown_report_with_readiness(self):
        results = [_make_result("a", fidelity=1.0, passed=True, latency_ms=10.0)]
        text = generate_markdown_report(results, readiness=_make_readiness())
        assert "## Readiness" in text
        assert isinstance(text, str)
        assert "Top readiness actions:" in text

    def test_generate_json_report_has_version(self):
        results = [_make_result()]
        report = generate_json_report(results)
        assert report["version"] == "1.0.0"

    def test_generate_json_report_has_environment(self):
        results = [_make_result()]
        report = generate_json_report(results)
        env = report["environment"]
        assert "python_version" in env
        assert "qontos_version" in env
        assert "backend" in env
        assert "shots" in env
        assert "seed" in env

    def test_generate_markdown_report_contains_table(self):
        results = [_make_result("bell", fidelity=1.0)]
        md = generate_markdown_report(results)
        assert "| Benchmark |" in md
        assert "| bell " in md
        assert "PASS" in md

    def test_save_report_creates_files(self):
        results = [_make_result("bell")]
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path, md_path = save_report(results, tmpdir)
            assert os.path.exists(json_path)
            assert os.path.exists(md_path)
            assert json_path.endswith(".json")
            assert md_path.endswith(".md")
            # Verify JSON is valid
            with open(json_path) as f:
                data = json.load(f)
            assert data["version"] == "1.0.0"

    def test_save_report_creates_latest_json(self):
        results = [_make_result("bell")]
        with tempfile.TemporaryDirectory() as tmpdir:
            save_report(results, tmpdir)
            latest = os.path.join(tmpdir, "latest.json")
            assert os.path.exists(latest)

    def test_empty_results(self):
        report = generate_json_report([])
        assert report["summary"]["total"] == 0
        assert report["summary"]["passed"] == 0
        assert report["summary"]["pass_rate"] == 0.0
