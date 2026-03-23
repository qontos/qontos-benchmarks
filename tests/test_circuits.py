"""Tests for benchmark circuit generators.

Validates that each generator produces syntactically valid OpenQASM 2.0
circuits with the expected structure (correct qubit/creg counts, required
gates, measurement instructions).
"""

from __future__ import annotations

import pytest

from qontos_bench.circuits import (
    bell_pair,
    bernstein_vazirani,
    cut_heavy_6q,
    ghz_state,
    h2_vqe_ansatz,
    modular_chain_4q,
    quantum_fourier_transform,
    random_circuit,
    random_circuit_5q,
)


def _parse_qasm_header(qasm: str) -> dict:
    """Extract basic info from a QASM string."""
    lines = qasm.strip().splitlines()
    info: dict = {"lines": lines, "raw": qasm}

    for line in lines:
        line = line.strip()
        if line.startswith("qreg"):
            # qreg q[N];
            info["num_qubits"] = int(line.split("[")[1].split("]")[0])
        elif line.startswith("creg"):
            info["num_cregs"] = int(line.split("[")[1].split("]")[0])
        elif line.startswith("measure"):
            info.setdefault("measurements", 0)
            info["measurements"] = info.get("measurements", 0) + 1

    return info


class TestBellPair:
    def test_returns_string(self):
        qasm = bell_pair()
        assert isinstance(qasm, str)

    def test_openqasm_header(self):
        qasm = bell_pair()
        assert qasm.strip().startswith("OPENQASM 2.0;")

    def test_qubit_count(self):
        info = _parse_qasm_header(bell_pair())
        assert info["num_qubits"] == 2

    def test_has_hadamard_and_cnot(self):
        qasm = bell_pair()
        assert "h q[0]" in qasm
        assert "cx q[0],q[1]" in qasm

    def test_measurements(self):
        info = _parse_qasm_header(bell_pair())
        assert info["measurements"] == 2


class TestGHZState:
    @pytest.mark.parametrize("n", [2, 3, 5, 8])
    def test_qubit_count(self, n: int):
        info = _parse_qasm_header(ghz_state(n))
        assert info["num_qubits"] == n

    @pytest.mark.parametrize("n", [3, 5])
    def test_cnot_chain(self, n: int):
        qasm = ghz_state(n)
        for i in range(1, n):
            assert f"cx q[0],q[{i}]" in qasm

    @pytest.mark.parametrize("n", [3, 5])
    def test_all_measured(self, n: int):
        info = _parse_qasm_header(ghz_state(n))
        assert info["measurements"] == n


class TestQFT:
    @pytest.mark.parametrize("n", [2, 4, 6])
    def test_qubit_count(self, n: int):
        info = _parse_qasm_header(quantum_fourier_transform(n))
        assert info["num_qubits"] == n

    def test_contains_hadamard(self):
        qasm = quantum_fourier_transform(4)
        assert "h q[0]" in qasm

    def test_contains_controlled_phase(self):
        qasm = quantum_fourier_transform(4)
        assert "cu1(" in qasm

    def test_contains_swap(self):
        qasm = quantum_fourier_transform(4)
        assert "swap" in qasm

    def test_all_measured(self):
        info = _parse_qasm_header(quantum_fourier_transform(4))
        assert info["measurements"] == 4


class TestBernsteinVazirani:
    @pytest.mark.parametrize("secret", ["101", "110", "1", "1111"])
    def test_qubit_count(self, secret: str):
        info = _parse_qasm_header(bernstein_vazirani(secret))
        # n input qubits + 1 ancilla
        assert info["num_qubits"] == len(secret) + 1

    def test_measures_input_only(self):
        secret = "101"
        info = _parse_qasm_header(bernstein_vazirani(secret))
        # Only input qubits are measured, not the ancilla
        assert info["num_cregs"] == len(secret)
        assert info["measurements"] == len(secret)

    def test_has_oracle_cnots(self):
        qasm = bernstein_vazirani("101")
        # secret=101 -> bits at positions 0 and 2 are '1'
        assert "cx q[" in qasm


class TestH2VQE:
    def test_qubit_count(self):
        info = _parse_qasm_header(h2_vqe_ansatz(0.5))
        assert info["num_qubits"] == 2

    def test_has_ry_gate(self):
        qasm = h2_vqe_ansatz(0.5)
        assert "ry(0.5)" in qasm

    def test_different_theta(self):
        qasm = h2_vqe_ansatz(1.23)
        assert "ry(1.23)" in qasm


class TestRandomCircuit:
    def test_deterministic(self):
        """Same seed produces identical circuits."""
        c1 = random_circuit(5, 10, seed=42)
        c2 = random_circuit(5, 10, seed=42)
        assert c1 == c2

    def test_different_seeds(self):
        c1 = random_circuit(5, 10, seed=42)
        c2 = random_circuit(5, 10, seed=99)
        assert c1 != c2

    @pytest.mark.parametrize("n", [2, 5, 8])
    def test_qubit_count(self, n: int):
        info = _parse_qasm_header(random_circuit(n, 10, seed=1))
        assert info["num_qubits"] == n

    def test_all_measured(self):
        info = _parse_qasm_header(random_circuit(5, 10, seed=42))
        assert info["measurements"] == 5


class TestRandomCircuit5Q:
    def test_deterministic(self):
        assert random_circuit_5q(42) == random_circuit_5q(42)

    def test_qubit_count(self):
        info = _parse_qasm_header(random_circuit_5q())
        assert info["num_qubits"] == 5


class TestModularChain4Q:
    def test_qubit_count(self):
        info = _parse_qasm_header(modular_chain_4q())
        assert info["num_qubits"] == 4

    def test_has_inter_module_cx(self):
        qasm = modular_chain_4q()
        assert "cx q[1],q[2]" in qasm


class TestCutHeavy6Q:
    def test_qubit_count(self):
        info = _parse_qasm_header(cut_heavy_6q())
        assert info["num_qubits"] == 6

    def test_has_long_range_cx(self):
        qasm = cut_heavy_6q()
        # Long-range inter-module gate
        assert "cx q[1],q[4]" in qasm

    def test_all_measured(self):
        info = _parse_qasm_header(cut_heavy_6q())
        assert info["measurements"] == 6
