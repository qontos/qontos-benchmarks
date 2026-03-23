# QONTOS Benchmark Metrics

| Metric | Definition | Unit | Benchmark Class |
|--------|-----------|------|-----------------|
| Fidelity | Fraction of shots in expected states | 0.0–1.0 | Correctness |
| Total Latency | End-to-end pipeline execution time | ms | Performance |
| Ingest Latency | Circuit normalization time | ms | Performance |
| Partition Latency | Partitioning computation time | ms | Performance |
| Schedule Latency | Backend assignment time | ms | Performance |
| Execute Latency | Simulator/provider execution time | ms | Performance |
| Aggregate Latency | Result aggregation time | ms | Performance |
| Cut Ratio | Inter-module gates / total gates | 0.0–1.0 | Modularity |
| Partition Balance | min(partition_size) / max(partition_size) | 0.0–1.0 | Modularity |
| Noisy Fidelity | Fidelity under noise model | 0.0–1.0 | Fidelity Proxy |
| Proof Determinism | Same input → same proof_hash | bool | Integrity |
