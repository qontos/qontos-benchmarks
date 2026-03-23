# QONTOS Benchmark Evidence

## Current Baseline: v0.1.0

**Backend**: Qiskit Aer statevector simulator (noiseless)
**Date**: 2026-03-23
**Shots**: 8,192 per circuit

### Correctness Suite

| Benchmark | Qubits | Fidelity | Latency | Status |
|-----------|--------|----------|---------|--------|
| Bell Pair | 2 | 1.000 | 45ms | PASS |
| GHZ-3 | 3 | 1.000 | 52ms | PASS |
| GHZ-5 | 5 | 1.000 | 68ms | PASS |
| QFT-4 | 4 | 1.000 | 58ms | PASS |
| Bernstein-Vazirani | 4 | 1.000 | 42ms | PASS |
| H2 VQE Ansatz | 2 | 1.000 | 40ms | PASS |
| Random 5Q | 5 | 1.000 | 71ms | PASS |

**Pass rate: 7/7 (100%)**
**Average fidelity: 1.000**

### What These Results Mean

These benchmarks validate **pipeline correctness** — the QONTOS ingest → normalize → execute → aggregate path preserves circuit semantics. They are measured on a noiseless simulator and demonstrate that the software pipeline does not introduce errors.

### What These Results Do NOT Mean

- These are not hardware QPU measurements
- Noiseless fidelity = 1.0 is expected; it validates software, not hardware
- Hardware benchmarks will be published when native QONTOS hardware is available

### Comparison Baseline

| What | Current | Future Target |
|------|---------|---------------|
| Backend | Simulator | Native QONTOS hardware |
| Physical qubits | N/A (simulated) | Stretch: 1,000,000 |
| Logical qubits | N/A (simulated) | Stretch: 10,000 |
| Noise model | Noiseless | Real hardware noise |
