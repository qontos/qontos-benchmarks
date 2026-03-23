# QONTOS Benchmark Methodology

## Benchmark Classes

### 1. Correctness Benchmarks
Verify that the QONTOS pipeline preserves circuit semantics from ingestion through result output.

- **Measurement**: Fidelity = (shots in expected states) / total_shots
- **Backend**: Qiskit Aer noiseless simulator
- **Pass threshold**: F ≥ 0.85 (configurable)
- **Default shots**: 8,192

### 2. Performance Benchmarks
Measure pipeline throughput, latency, and resource utilization.

- **Measurement**: Wall-clock time per pipeline stage
- **Metrics**: Total latency (ms), per-stage breakdown, shots/second
- **Backend**: Local simulator

### 3. Modularity Benchmarks
Evaluate partitioning quality and multi-module execution overhead.

- **Measurement**: Cut ratio, partition balance, inter-module gate count
- **Scenarios**: 2-module, 5-module, 10-module configurations

### 4. Fidelity Proxy Benchmarks
Estimate expected fidelity under noise models without hardware.

- **Measurement**: Fidelity vs noise rate curves
- **Backend**: Noisy simulator with configurable depolarizing error
- **Noise rates**: 0.001, 0.005, 0.01, 0.05

### 5. Proof and Integrity Benchmarks
Verify that the proof chain is correct and deterministic.

- **Measurement**: Hash determinism, proof completeness
- **Validation**: Same input always produces same proof_hash

## Measurement Conditions

| Parameter | Default | Configurable |
|-----------|---------|:---:|
| Shots | 8,192 | ✓ |
| Optimization level | 1 | ✓ |
| Simulator backend | Qiskit Aer statevector | ✓ |
| Noise model | None (correctness) / Depolarizing (fidelity) | ✓ |
| Seed | 42 (deterministic) | ✓ |

## Report Schema

All benchmark runs produce a JSON report conforming to `reports/schema/benchmark_report.schema.json`.

## Reproducibility

All benchmarks are designed to be fully reproducible:
1. Fixed random seeds
2. Versioned circuit definitions
3. Explicit backend and noise configurations
4. CI-validated report generation
