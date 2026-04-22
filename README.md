<div align="center">
  <a href="https://github.com/qontos">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/qontos/.github/main/assets/qontos-logo-white.png">
      <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/qontos/.github/main/assets/qontos-logo.png">
      <img src="https://raw.githubusercontent.com/qontos/.github/main/assets/qontos-logo.png" alt="QONTOS" width="260">
    </picture>
  </a>

  <h3>QONTOS Benchmarks</h3>
  <p><strong>Reproducible evidence, methodology, and regression validation for the QONTOS platform.</strong></p>
  <p>The public proof layer for correctness claims across the SDK, simulator, and modular execution stack.</p>

  <p>
    <img src="https://img.shields.io/badge/Visibility-Public-0f766e?style=flat-square" alt="Visibility: Public">
    <img src="https://img.shields.io/badge/Track-Evidence-0b3b8f?style=flat-square" alt="Track: Evidence">
    <img src="https://img.shields.io/badge/Status-Pre--release-c2410c?style=flat-square" alt="Status: Pre-release">
    <a href="https://github.com/qontos/qontos-benchmarks/actions"><img src="https://img.shields.io/github/actions/workflow/status/qontos/qontos-benchmarks/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI"></a>
  </p>

  <p>
    <a href="#overview">Overview</a> &middot;
    <a href="#installation">Installation</a> &middot;
    <a href="#quick-start">Quick Start</a> &middot;
    <a href="docs/index.md">Docs Hub</a> &middot;
    <a href="#benchmark-suite">Benchmark Suite</a> &middot;
    <a href="#methodology">Methodology</a> &middot;
    <a href="#report-format">Report Format</a>
  </p>
</div>

---

## Overview

QONTOS Benchmarks is the public evidence repo for the QONTOS platform. It contains benchmark definitions, execution methodology, report schemas, and reproducible outputs used to validate correctness, performance, and regression behavior across the public QONTOS stack. This repository is the reference point for public technical claims made by QONTOS.

Start with [docs/index.md](docs/index.md) for the lightweight docs hub and the key benchmark evidence pages.
For the canonical install and release policy across the public repos, use [the shared policy](https://github.com/qontos/.github/blob/main/docs/release-install-policy.md).

## Installation

### Pre-release (current)

```bash
pip install "qontos-bench @ git+https://github.com/qontos/qontos-benchmarks.git@v0.1.0"
```

> **Note**: Once published to PyPI, this will simplify to `pip install qontos-bench`.

### For contributors (local development)

```bash
git clone https://github.com/qontos/qontos-benchmarks.git
cd qontos-benchmarks
pip install -e ".[dev]"
pytest
```

CI validates both paths: the released-tag install (on main push) and the local-checkout install (on every PR).
CI also now emits a `hybrid-benchmark-report` artifact from the live hybrid benchmark pack so downstream systems workflows can consume a real generated JSON report instead of a static fixture.
The repo now also ships a separate **hybrid stress** pack so we can probe the superconducting-photonic seam with workloads that specifically target transduction, retry, memory-wait, control-jitter, and entanglement-supply pressure.

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
| :--- | :--- | :--- | :--- | :--- |
| Bell Pair | H + CNOT | 2 | \|00>, \|11> | >= 0.85 |
| GHZ-3 | H + 2 CNOT | 3 | \|000>, \|111> | >= 0.85 |
| GHZ-5 | H + 4 CNOT | 5 | \|00000>, \|11111> | >= 0.85 |
| QFT-4 | H + CU1 + SWAP | 4 | Uniform (16 states) | >= 0.85 |
| Bernstein-Vazirani | H + CNOT oracle | 4 | \|101> | >= 0.85 |
| H2 VQE Ansatz | RY + CNOT + RY | 2 | All 2-qubit states | >= 0.85 |
| Random 5Q | Mixed (depth=10) | 5 | All 5-qubit states | >= 0.85 |

### Hybrid Modular Pack

- `photonic-bell`
- `teleport`
- `remote-cnot`
- `distributed-ghz`
- `syndrome-burst`

### Hybrid Stress Pack

- `entanglement-swap`
- `teleport-ladder`
- `remote-parity`
- `distributed-ghz-ladder`
- `patch-syndrome`

Run the stress pack directly:

```bash
python -m qontos_bench --circuit hybrid-stress
```

## Methodology

Each benchmark is executed through the full QONTOS pipeline:

1. **Circuit normalization** via `CircuitNormalizer`
2. **Execution** via `LocalSimulatorExecutor` (Qiskit Aer)
3. **Fidelity computation**: `F = (expected state counts) / total_shots`

Pass threshold: **0.85**. Default shot count: **8,192**.

The report schema now also includes a `stressor_summary` section derived from benchmark metadata so downstream systems workflows can see which hybrid bottleneck classes are still weak, not just which circuit families passed.

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
| :--- | :--- |
| [qontos](https://github.com/qontos/qontos) | Flagship Python SDK |
| [qontos-sim](https://github.com/qontos/qontos-sim) | Simulators and digital twin |
| [qontos-examples](https://github.com/qontos/qontos-examples) | Tutorials and examples |
| [qontos-benchmarks](https://github.com/qontos/qontos-benchmarks) | Benchmark evidence |
| [qontos-research](https://github.com/qontos/qontos-research) | Research papers and roadmap |

## License

[Apache License 2.0](LICENSE)

---

*Built by [Zhyra Quantum Research Institute (ZQRI)](https://zhyra.xyz) — Abu Dhabi, UAE*
