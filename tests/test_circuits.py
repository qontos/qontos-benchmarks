"""Tests for benchmark circuit generators.

Validates that each generator produces syntactically valid OpenQASM 2.0
circuits with the expected structure (correct qubit/creg counts, required
gates, measurement instructions).  Also tests determinism with seeds.
"""

from __future__ import annotations

import pytest

from qontos_bench.circuits import (
    bell_pair,
    bernstein_vazirani,
    cut_heavy_6q,
    distributed_ghz_6q,
    ghz_state,
    h2_vqe_ansatz,
    modular_chain_4q,
    photonic_link_bell_4q,
    quantum_fourier_transform,
    random_circuit,
    random_circuit_5q,
    remote_cnot_surrogate_4q,
    syndrome_burst_5q,
    teleportation_chain_4q,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_qasm_header(qasm: str) -> dict:
    """Extract basic info from a QASM string."""
    lines = qasm.strip().splitlines()
    info: dict = {"lines": lines, "raw": qasm}

    for line in lines:
        line = line.strip()
        if line.startswith("qreg"):
            info["num_qubits"] = int(line.split("[")[1].split("]")[0])
        elif line.startswith("creg"):
            info["num_cregs"] = int(line.split("[")[1].split("]")[0])
        elif line.startswith("measure"):
            info.setdefault("measurements", 0)
            info["measurements"] = info.get("measurements", 0) + 1

    return info


def _count_gates(qasm: str, gate: str) -> int:
    """Count occurrences of a specific gate mnemonic in QASM text."""
    count = 0
    for line in qasm.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith(gate + " ") or stripped.startswith(gate + "("):
            count += 1
    return count


# ===================================================================
# Bell Pair
# ===================================================================

class TestBellPair:
    def test_returns_string(self):
        assert isinstance(bell_pair(), str)

    def test_openqasm_header(self):
        assert bell_pair().strip().startswith("OPENQASM 2.0;")

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

    def test_valid_qasm_structure(self):
        qasm = bell_pair()
        assert 'include "qelib1.inc"' in qasm

    def test_deterministic(self):
        assert bell_pair() == bell_pair()


# ===================================================================
# GHZ State
# ===================================================================

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

    def test_starts_with_hadamard(self):
        qasm = ghz_state(4)
        assert "h q[0]" in qasm

    def test_gate_count(self):
        # GHZ-3: 1 H + 2 CX
        qasm = ghz_state(3)
        assert _count_gates(qasm, "h") == 1
        assert _count_gates(qasm, "cx") == 2

    def test_deterministic(self):
        assert ghz_state(5) == ghz_state(5)


# ===================================================================
# QFT
# ===================================================================

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

    def test_hadamard_count_equals_n(self):
        n = 4
        qasm = quantum_fourier_transform(n)
        assert _count_gates(qasm, "h") == n

    def test_deterministic(self):
        assert quantum_fourier_transform(4) == quantum_fourier_transform(4)


# ===================================================================
# Bernstein-Vazirani
# ===================================================================

class TestBernsteinVazirani:
    @pytest.mark.parametrize("secret", ["101", "110", "1", "1111"])
    def test_qubit_count(self, secret: str):
        info = _parse_qasm_header(bernstein_vazirani(secret))
        assert info["num_qubits"] == len(secret) + 1

    def test_measures_input_only(self):
        secret = "101"
        info = _parse_qasm_header(bernstein_vazirani(secret))
        assert info["num_cregs"] == len(secret)
        assert info["measurements"] == len(secret)

    def test_has_oracle_cnots(self):
        qasm = bernstein_vazirani("101")
        assert "cx q[" in qasm

    def test_ancilla_initialized(self):
        qasm = bernstein_vazirani("101")
        # Ancilla is last qubit, initialized with X then H
        assert "x q[3]" in qasm
        assert "h q[3]" in qasm

    def test_deterministic(self):
        assert bernstein_vazirani("101") == bernstein_vazirani("101")


# ===================================================================
# H2 VQE
# ===================================================================

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

    def test_has_cnot(self):
        qasm = h2_vqe_ansatz(0.5)
        assert "cx q[0],q[1]" in qasm

    def test_measurements(self):
        info = _parse_qasm_header(h2_vqe_ansatz(0.5))
        assert info["measurements"] == 2

    def test_deterministic_same_theta(self):
        assert h2_vqe_ansatz(0.7) == h2_vqe_ansatz(0.7)


# ===================================================================
# Random Circuit
# ===================================================================

class TestRandomCircuit:
    def test_deterministic(self):
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

    def test_valid_qasm(self):
        qasm = random_circuit(3, 6, seed=7)
        assert qasm.strip().startswith("OPENQASM 2.0;")

    def test_depth_affects_output(self):
        short = random_circuit(3, 2, seed=42)
        long = random_circuit(3, 20, seed=42)
        assert len(long.splitlines()) > len(short.splitlines())


# ===================================================================
# Random Circuit 5Q (convenience wrapper)
# ===================================================================

class TestRandomCircuit5Q:
    def test_deterministic(self):
        assert random_circuit_5q(42) == random_circuit_5q(42)

    def test_qubit_count(self):
        info = _parse_qasm_header(random_circuit_5q())
        assert info["num_qubits"] == 5

    def test_different_from_other_seed(self):
        assert random_circuit_5q(42) != random_circuit_5q(99)


# ===================================================================
# Modular Chain 4Q
# ===================================================================

class TestModularChain4Q:
    def test_qubit_count(self):
        info = _parse_qasm_header(modular_chain_4q())
        assert info["num_qubits"] == 4

    def test_has_inter_module_cx(self):
        qasm = modular_chain_4q()
        assert "cx q[1],q[2]" in qasm

    def test_all_measured(self):
        info = _parse_qasm_header(modular_chain_4q())
        assert info["measurements"] == 4

    def test_deterministic(self):
        assert modular_chain_4q() == modular_chain_4q()


# ===================================================================
# Cut Heavy 6Q
# ===================================================================

class TestCutHeavy6Q:
    def test_qubit_count(self):
        info = _parse_qasm_header(cut_heavy_6q())
        assert info["num_qubits"] == 6

    def test_has_long_range_cx(self):
        qasm = cut_heavy_6q()
        assert "cx q[1],q[4]" in qasm

    def test_all_measured(self):
        info = _parse_qasm_header(cut_heavy_6q())
        assert info["measurements"] == 6

    def test_has_three_inter_module_gates(self):
        qasm = cut_heavy_6q()
        assert "cx q[1],q[2]" in qasm
        assert "cx q[3],q[4]" in qasm
        assert "cx q[1],q[4]" in qasm

    def test_deterministic(self):
        assert cut_heavy_6q() == cut_heavy_6q()


class TestHybridCircuits:
    def test_photonic_link_bell_structure(self):
        qasm = photonic_link_bell_4q()
        info = _parse_qasm_header(qasm)
        assert info["num_qubits"] == 4
        assert "cx q[1],q[2]" in qasm
        assert info["measurements"] == 4

    def test_teleportation_chain_structure(self):
        qasm = teleportation_chain_4q()
        info = _parse_qasm_header(qasm)
        assert info["num_qubits"] == 4
        assert "cx q[1],q[2]" in qasm
        assert info["measurements"] == 4

    def test_remote_cnot_structure(self):
        qasm = remote_cnot_surrogate_4q()
        info = _parse_qasm_header(qasm)
        assert info["num_qubits"] == 4
        assert "cx q[1],q[3]" in qasm
        assert info["measurements"] == 4

    def test_distributed_ghz_structure(self):
        qasm = distributed_ghz_6q()
        info = _parse_qasm_header(qasm)
        assert info["num_qubits"] == 6
        assert "cx q[4],q[5]" in qasm
        assert info["measurements"] == 6

    def test_syndrome_burst_structure(self):
        qasm = syndrome_burst_5q()
        info = _parse_qasm_header(qasm)
        assert info["num_qubits"] == 5
        assert "cx q[1],q[4]" in qasm
        assert info["measurements"] == 5


# ===================================================================
# Cross-circuit: valid QASM and metadata consistency
# ===================================================================

_ALL_CIRCUITS = [
    ("bell_pair", bell_pair, {}, 2),
    ("ghz_3", ghz_state, {"n": 3}, 3),
    ("ghz_5", ghz_state, {"n": 5}, 5),
    ("qft_4", quantum_fourier_transform, {"n": 4}, 4),
    ("bv_101", bernstein_vazirani, {"secret": "101"}, 4),  # 3+1 ancilla
    ("h2_vqe", h2_vqe_ansatz, {"theta": 0.5}, 2),
    ("modular_4q", modular_chain_4q, {}, 4),
    ("cut_heavy_6q", cut_heavy_6q, {}, 6),
    ("photonic_link_bell_4q", photonic_link_bell_4q, {}, 4),
    ("teleportation_chain_4q", teleportation_chain_4q, {}, 4),
    ("remote_cnot_surrogate_4q", remote_cnot_surrogate_4q, {}, 4),
    ("distributed_ghz_6q", distributed_ghz_6q, {}, 6),
    ("syndrome_burst_5q", syndrome_burst_5q, {}, 5),
    ("random_5q", random_circuit_5q, {}, 5),
]


class TestAllCircuitsValidQASM:
    @pytest.mark.parametrize("label,fn,kwargs,expected_qubits", _ALL_CIRCUITS)
    def test_starts_with_openqasm(self, label, fn, kwargs, expected_qubits):
        qasm = fn(**kwargs)
        assert qasm.strip().startswith("OPENQASM 2.0;"), f"{label}: missing OPENQASM header"

    @pytest.mark.parametrize("label,fn,kwargs,expected_qubits", _ALL_CIRCUITS)
    def test_qubit_count_matches(self, label, fn, kwargs, expected_qubits):
        info = _parse_qasm_header(fn(**kwargs))
        assert info["num_qubits"] == expected_qubits, f"{label}: qubit count mismatch"

    @pytest.mark.parametrize("label,fn,kwargs,expected_qubits", _ALL_CIRCUITS)
    def test_has_measurements(self, label, fn, kwargs, expected_qubits):
        info = _parse_qasm_header(fn(**kwargs))
        assert info.get("measurements", 0) > 0, f"{label}: no measurements found"

    @pytest.mark.parametrize("label,fn,kwargs,expected_qubits", _ALL_CIRCUITS)
    def test_includes_qelib(self, label, fn, kwargs, expected_qubits):
        qasm = fn(**kwargs)
        assert "qelib1.inc" in qasm, f"{label}: missing qelib1.inc include"


class TestCircuitsDeterministicWithSeed:
    """Verify that circuits with seed parameters are deterministic."""

    def test_random_circuit_same_seed(self):
        a = random_circuit(4, 8, seed=123)
        b = random_circuit(4, 8, seed=123)
        assert a == b

    def test_random_circuit_5q_same_seed(self):
        a = random_circuit_5q(seed=77)
        b = random_circuit_5q(seed=77)
        assert a == b

    def test_ghz_is_deterministic(self):
        a = ghz_state(4)
        b = ghz_state(4)
        assert a == b

    def test_qft_is_deterministic(self):
        a = quantum_fourier_transform(3)
        b = quantum_fourier_transform(3)
        assert a == b

    def test_bv_is_deterministic(self):
        a = bernstein_vazirani("1010")
        b = bernstein_vazirani("1010")
        assert a == b
