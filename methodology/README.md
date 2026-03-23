# QONTOS Benchmark Methodology

## Overview

The QONTOS benchmark suite validates the correctness and performance of the
QONTOS quantum orchestration pipeline. Each benchmark run executes a set of
well-understood quantum circuits through the full pipeline (normalization,
compilation, simulation) and measures fidelity against known expected outcomes.

## Metrics

### Fidelity

The primary metric. Defined as the fraction of measurement shots that land in
the set of expected output states:

    fidelity = (shots in expected states) / (total shots)

For example, a Bell pair circuit with expected states {|00>, |11>} and 8192
shots where 8100 shots measure either "00" or "11" yields fidelity = 8100/8192
= 0.9888.

### Gate Count

Total number of gates in the compiled circuit. Reported per benchmark for
tracking compilation efficiency across releases.

### Circuit Depth

The critical-path length of the compiled circuit (number of time steps when
gates are parallelized). Lower depth generally indicates better compilation.

### Execution Time

Wall-clock time in milliseconds for the simulation phase (excluding
normalization and report generation). Reported per-circuit to detect
performance regressions.

## Benchmark Circuits

| Name | Qubits | Type | Expected Output |
|------|--------|------|-----------------|
| Bell Pair | 2 | Entanglement | \|00> + \|11> with ~50/50 |
| GHZ-3 | 3 | Entanglement | \|000> + \|111> with ~50/50 |
| GHZ-5 | 5 | Entanglement | \|00000> + \|11111> with ~50/50 |
| QFT-4 | 4 | Transform | Uniform superposition (all 16 states) |
| Bernstein-Vazirani (s=101) | 4 | Algorithm | Secret string "101" |
| H2 VQE Ansatz | 2 | Variational | Any valid 2-qubit state |
| Random 5Q (depth=10) | 5 | Stress test | Any valid 5-qubit state |

## Backends

### Qiskit Aer — Noiseless (default)

Statevector-equivalent shot-based simulation with no noise model. Used as the
ground truth: all standard circuits should achieve fidelity >= 0.99 on this
backend. Deviations indicate bugs in the pipeline, not hardware noise.

### Qiskit Aer — Noisy (planned)

Simulations with realistic noise models (depolarizing, thermal relaxation,
readout error). Fidelity thresholds are relaxed for noisy runs. This backend
is planned for v0.2.0.

## Pass/Fail Thresholds

| Backend | Fidelity Threshold | Notes |
|---------|-------------------|-------|
| Noiseless | >= 0.85 | Conservative default; most circuits score > 0.99 |
| Noisy (planned) | >= 0.60 | Depends on noise model severity |

A benchmark **passes** if its measured fidelity meets or exceeds the threshold
for the active backend. The overall suite passes only if every individual
benchmark passes.

The 0.85 threshold is intentionally conservative to accommodate:
- Statistical fluctuation at lower shot counts
- QFT circuits where uniform output makes fidelity = 1.0 by definition
- Future noisy backend integration

## Reproducibility

All benchmark results are reproducible given:

1. **Fixed seeds**: Random circuits use deterministic RNG seeds (default: 42).
2. **Pinned dependencies**: The `pyproject.toml` specifies minimum versions for
   all runtime dependencies.
3. **Shot count**: Default is 8192 shots per circuit. Configurable via CLI
   (`--shots`).
4. **Report artifacts**: Every run produces a timestamped JSON report containing
   full circuit parameters, counts, and computed metrics.

To reproduce a specific run:

```bash
pip install -e ".[dev]"
python -m qontos_bench.cli --shots 8192 --output reports/
```

The JSON report schema is defined in `reports/schema/benchmark_report.schema.json`.

## Report Format

Reports are generated in two formats:

- **JSON**: Machine-readable, schema-validated. Contains full counts dictionaries,
  all computed metrics, and metadata.
- **Text**: Human-readable summary with pass/fail status per circuit.

Both are written to the output directory with timestamped filenames plus a
`latest.json` symlink for CI consumption.
