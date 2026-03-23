<div align="center">

<img src="assets/qontos-logo.png" alt="QONTOS" width="400">

### Benchmarks

**Quantum benchmark framework and reproducible methodology for the QONTOS platform**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/qontos/qontos-benchmarks/ci.yml?branch=main&label=CI&logo=github)](https://github.com/qontos/qontos-benchmarks/actions)

[Installation](#installation) &middot;
[Quick Start](#quick-start) &middot;
[Benchmark Suite](#benchmark-suite) &middot;
[Methodology](#methodology) &middot;
[Reports](#reports)

</div>

---

## What is this?

QONTOS Benchmarks is the public evidence repo for the QONTOS platform. It contains benchmark definitions, execution methodology, report schemas, and reproducible outputs used to validate correctness, performance, and regression behavior across the public QONTOS stack. This repository is the reference point for public technical claims made by QONTOS.

## Installation

### Pre-release (current)

```bash
pip install "qontos-bench @ git+https://github.com/qontos/qontos-benchmarks.git@v0.1.0"
```

> **Note**: Once published to PyPI, this will simplify to `pip install qontos-bench`.

## Quick Start

```bash
# Run the full benchmark suite
python -m qontos_bench

# Run a specific benchmark
python -m qontos_bench --benchmark bell_pair

# Generate a report
python -m qontos_bench --report json --output results.json
```

## Benchmark Suite

| Benchmark | Circuit | Qubits | Expected States | Fidelity Threshold |
|---|---|---|---|---|
| Bell Pair | H + CNOT | 2 | \|00>, \|11> | >= 0.85 |
| GHZ-3 | H + 2 CNOT | 3 | \|000>, \|111> | >= 0.85 |
| GHZ-5 | H + 4 CNOT | 5 | \|00000>, \|11111> | >= 0.85 |
| QFT-4 | H + CU1 + SWAP | 4 | Uniform (16 states) | >= 0.85 |
| Bernstein-Vazirani | H + CNOT oracle | 4 | \|101> | >= 0.85 |
| H2 VQE Ansatz | RY + CNOT + RY | 2 | All 2-qubit states | >= 0.85 |
| Random 5Q | Mixed (depth=10) | 5 | All 5-qubit states | >= 0.85 |

## Methodology

Each benchmark is executed through the full QONTOS pipeline:

1. **Circuit normalization** via `CircuitNormalizer`
2. **Execution** via `LocalSimulatorExecutor` (Qiskit Aer)
3. **Fidelity computation**: `F = (expected state counts) / total_shots`

Pass threshold: **0.85**. Default shot count: **8,192**.

### What the benchmarks prove

These benchmarks validate **pipeline correctness** — that the ingest-normalize-execute path preserves circuit semantics. They are designed to detect regressions, not to measure hardware noise characteristics.

### Measurement conditions

- Backend: Qiskit Aer `AerSimulator` (noiseless statevector)
- Shot count: 8,192 (configurable)
- Fidelity definition: fraction of shots landing in expected states
- All results are simulator-based until hardware QPU integration

## Report Format

```json
{
  "timestamp": "2026-03-23T12:00:00Z",
  "backend": "aer_simulator",
  "shots": 8192,
  "benchmarks": [
    {
      "name": "bell_pair",
      "qubits": 2,
      "fidelity": 1.0,
      "passed": true,
      "counts": {"00": 4096, "11": 4096}
    }
  ]
}
```

## Related Repositories

| Repository | Description |
|------------|-------------|
| [qontos](https://github.com/qontos/qontos) | Flagship Python SDK |
| [qontos-sim](https://github.com/qontos/qontos-sim) | Simulators and digital twin |
| [qontos-examples](https://github.com/qontos/qontos-examples) | Tutorials and examples |
| [qontos-benchmarks](https://github.com/qontos/qontos-benchmarks) | Benchmark evidence |
| [qontos-research](https://github.com/qontos/qontos-research) | Research papers and roadmap |

## License

[Apache License 2.0](LICENSE)

---

*Built by [Zhyra Quantum Research Institute (ZQRI)](https://zhyra.xyz) — Abu Dhabi, UAE*
