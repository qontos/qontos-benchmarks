"""Verify that all public qontos_bench modules can be imported."""

from __future__ import annotations


def test_import_top_level():
    import qontos_bench

    assert hasattr(qontos_bench, "__version__")
    assert isinstance(qontos_bench.__version__, str)


def test_import_circuits():
    from qontos_bench import circuits

    # Verify all public circuit generators are importable
    assert callable(circuits.bell_pair)
    assert callable(circuits.ghz_state)
    assert callable(circuits.quantum_fourier_transform)
    assert callable(circuits.bernstein_vazirani)
    assert callable(circuits.h2_vqe_ansatz)
    assert callable(circuits.random_circuit)
    assert callable(circuits.modular_chain_4q)
    assert callable(circuits.random_circuit_5q)
    assert callable(circuits.cut_heavy_6q)
    assert callable(circuits.photonic_link_bell_4q)
    assert callable(circuits.teleportation_chain_4q)
    assert callable(circuits.remote_cnot_surrogate_4q)
    assert callable(circuits.distributed_ghz_6q)
    assert callable(circuits.syndrome_burst_5q)


def test_import_runner():
    from qontos_bench.runner import BenchmarkResult, BenchmarkRunner

    assert BenchmarkResult is not None
    assert BenchmarkRunner is not None


def test_import_report():
    from qontos_bench.report import (
        generate_report,
        generate_json_report,
        generate_markdown_report,
        save_report,
    )

    assert callable(generate_report)
    assert callable(generate_json_report)
    assert callable(generate_markdown_report)
    assert callable(save_report)


def test_import_cli():
    from qontos_bench.cli import main

    assert callable(main)
