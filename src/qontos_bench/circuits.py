"""Standard benchmark circuits for QONTOS platform validation."""

from __future__ import annotations

import math
import random


def bell_pair() -> str:
    """2-qubit Bell state (|00> + |11>)/sqrt(2)."""
    return """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];"""


def ghz_state(n: int = 3) -> str:
    """N-qubit GHZ state: (|00...0> + |11...1>)/sqrt(2)."""
    lines = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        f'qreg q[{n}];',
        f'creg c[{n}];',
        'h q[0];',
    ]
    for i in range(1, n):
        lines.append(f'cx q[0],q[{i}];')
    for i in range(n):
        lines.append(f'measure q[{i}] -> c[{i}];')
    return '\n'.join(lines)


def quantum_fourier_transform(n: int = 4) -> str:
    """N-qubit Quantum Fourier Transform circuit.

    Applies the standard QFT decomposition: for each qubit k, apply H then
    controlled-phase rotations CU1(pi/2^(j-k)) for each subsequent qubit j.
    Finishes with swaps to reverse qubit ordering.
    """
    lines = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        f'qreg q[{n}];',
        f'creg c[{n}];',
    ]

    # QFT core: H + controlled rotations
    for k in range(n):
        lines.append(f'h q[{k}];')
        for j in range(k + 1, n):
            angle = math.pi / (2 ** (j - k))
            lines.append(f'cu1({angle}) q[{j}],q[{k}];')

    # Swap qubits to get correct output ordering
    for i in range(n // 2):
        lines.append(f'swap q[{i}],q[{n - 1 - i}];')

    # Measure all
    for i in range(n):
        lines.append(f'measure q[{i}] -> c[{i}];')

    return '\n'.join(lines)


def bernstein_vazirani(secret: str = "101") -> str:
    """Bernstein-Vazirani algorithm for a given secret bit-string.

    The circuit applies H to all input qubits and an ancilla, then applies
    CNOT gates for each '1' bit in the secret, then H again. Measuring the
    input register should yield the secret string with high probability.
    """
    n = len(secret)
    total_qubits = n + 1  # n input qubits + 1 ancilla

    lines = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        f'qreg q[{total_qubits}];',
        f'creg c[{n}];',
    ]

    # Put ancilla (last qubit) in |-> state
    lines.append(f'x q[{n}];')
    lines.append(f'h q[{n}];')

    # Apply H to all input qubits
    for i in range(n):
        lines.append(f'h q[{i}];')

    # Oracle: CNOT from input qubit i to ancilla where secret[i] == '1'
    # secret is read left-to-right as qubit n-1 down to qubit 0
    for i, bit in enumerate(secret):
        if bit == '1':
            qubit_index = n - 1 - i
            lines.append(f'cx q[{qubit_index}],q[{n}];')

    # Apply H again to input qubits
    for i in range(n):
        lines.append(f'h q[{i}];')

    # Measure input qubits only
    for i in range(n):
        lines.append(f'measure q[{i}] -> c[{i}];')

    return '\n'.join(lines)


def h2_vqe_ansatz(theta: float = 0.5) -> str:
    """Simple H2 VQE ansatz (RY-CNOT-RY) for hydrogen molecule simulation."""
    return f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
ry({theta}) q[0];
cx q[0],q[1];
ry({theta}) q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];"""


def modular_chain_4q() -> str:
    """4-qubit chain circuit designed for 2-partition modular execution.

    Partition 0: qubits [0, 1] — H(0), CX(0,1), Rz(0.3, 1)
    Partition 1: qubits [2, 3] — H(2), CX(2,3), Rz(0.5, 3)
    Inter-module: CX(1, 2) — creates entanglement across boundary
    """
    return """\
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[4];
h q[0];
cx q[0],q[1];
rz(0.3) q[1];
cx q[1],q[2];
h q[2];
cx q[2],q[3];
rz(0.5) q[3];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
"""


def random_circuit_5q(seed: int = 42) -> str:
    """Generate a fixed-seed random 5-qubit circuit for cross-provider benchmarking.

    Uses a deterministic RNG so every invocation with the same seed produces
    the exact same circuit.  The circuit is built from 6 layers of random
    single-qubit gates plus CX entangling gates on adjacent pairs.

    Args:
        seed: RNG seed for reproducibility (default: 42).

    Returns:
        QASM string of the random 5-qubit circuit.
    """
    return random_circuit(n_qubits=5, depth=12, seed=seed)


def cut_heavy_6q() -> str:
    """6-qubit circuit with multiple wire cuts, designed for modular benchmarking.

    Three 2-qubit modules connected by inter-module CX gates:
      Module 0: qubits [0, 1] — H(0), CX(0,1), Rz(0.4, 1)
      Module 1: qubits [2, 3] — H(2), CX(2,3), Rz(0.6, 3)
      Module 2: qubits [4, 5] — H(4), CX(4,5), Rz(0.8, 5)
    Inter-module gates (3 wire cuts):
      CX(1,2) — module 0 <-> module 1
      CX(3,4) — module 1 <-> module 2
      CX(1,4) — module 0 <-> module 2 (long-range)
    """
    return """\
OPENQASM 2.0;
include "qelib1.inc";
qreg q[6];
creg c[6];
h q[0];
cx q[0],q[1];
rz(0.4) q[1];
cx q[1],q[2];
h q[2];
cx q[2],q[3];
rz(0.6) q[3];
cx q[3],q[4];
h q[4];
cx q[4],q[5];
rz(0.8) q[5];
cx q[1],q[4];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
measure q[3] -> c[3];
measure q[4] -> c[4];
measure q[5] -> c[5];
"""


def random_circuit(n_qubits: int = 5, depth: int = 10, seed: int = 42) -> str:
    """Random circuit for stress testing.

    Uses a seeded RNG to produce reproducible random circuits composed of
    single-qubit gates (h, x, y, z, t, s, rx, ry, rz) and two-qubit gates (cx).
    """
    rng = random.Random(seed)

    single_gates_no_param = ['h', 'x', 'y', 'z', 't', 's']
    single_gates_param = ['rx', 'ry', 'rz']

    lines = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        f'qreg q[{n_qubits}];',
        f'creg c[{n_qubits}];',
    ]

    for _layer in range(depth):
        # Randomly decide: single-qubit gate or two-qubit gate
        if n_qubits >= 2 and rng.random() < 0.3:
            # Two-qubit gate (cx)
            q0, q1 = rng.sample(range(n_qubits), 2)
            lines.append(f'cx q[{q0}],q[{q1}];')
        else:
            qubit = rng.randint(0, n_qubits - 1)
            if rng.random() < 0.5:
                gate = rng.choice(single_gates_no_param)
                lines.append(f'{gate} q[{qubit}];')
            else:
                gate = rng.choice(single_gates_param)
                angle = rng.uniform(0, 2 * math.pi)
                lines.append(f'{gate}({angle}) q[{qubit}];')

    # Measure all
    for i in range(n_qubits):
        lines.append(f'measure q[{i}] -> c[{i}];')

    return '\n'.join(lines)
