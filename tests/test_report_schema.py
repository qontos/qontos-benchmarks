"""Tests that benchmark report output conforms to the expected JSON schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "reports" / "schema" / "benchmark_report.schema.json"
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "reports" / "samples" / "baseline_v0.1.0.json"


@pytest.fixture
def schema() -> dict:
    """Load the benchmark report JSON schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture
def sample_report() -> dict:
    """Load the sample baseline report."""
    return json.loads(SAMPLE_PATH.read_text())


def _validate_against_schema(data: dict, schema: dict) -> list[str]:
    """Lightweight schema validation without jsonschema dependency.

    Checks required fields, types, and nested structure as defined in the
    schema. Returns a list of error strings (empty means valid).
    """
    errors: list[str] = []

    def _check_type(value, expected_type: str, path: str) -> bool:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        expected = type_map.get(expected_type)
        if expected is None:
            return True
        if not isinstance(value, expected):
            errors.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
            return False
        return True

    def _check_object(obj: dict, obj_schema: dict, path: str) -> None:
        if "required" in obj_schema:
            for req in obj_schema["required"]:
                if req not in obj:
                    errors.append(f"{path}: missing required field '{req}'")

        props = obj_schema.get("properties", {})
        for key, prop_schema in props.items():
            if key not in obj:
                continue
            field_path = f"{path}.{key}"
            value = obj[key]

            if "type" in prop_schema:
                _check_type(value, prop_schema["type"], field_path)

            if prop_schema.get("type") == "object" and isinstance(value, dict):
                _check_object(value, prop_schema, field_path)

            if prop_schema.get("type") == "array" and isinstance(value, list):
                items_schema = prop_schema.get("items", {})
                for i, item in enumerate(value):
                    item_path = f"{field_path}[{i}]"
                    if "type" in items_schema:
                        _check_type(item, items_schema["type"], item_path)
                    if items_schema.get("type") == "object" and isinstance(item, dict):
                        _check_object(item, items_schema, item_path)

    if schema.get("type") == "object":
        _check_object(data, schema, "$")

    return errors


class TestSchemaFileExists:
    def test_schema_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, schema: dict):
        assert "$schema" in schema or "type" in schema

    def test_sample_exists(self):
        assert SAMPLE_PATH.exists(), f"Sample report not found at {SAMPLE_PATH}"


class TestSampleMatchesSchema:
    def test_top_level_fields(self, sample_report: dict, schema: dict):
        errors = _validate_against_schema(sample_report, schema)
        assert errors == [], f"Schema validation errors:\n" + "\n".join(errors)

    def test_has_results(self, sample_report: dict):
        assert "results" in sample_report
        assert isinstance(sample_report["results"], list)
        assert len(sample_report["results"]) > 0

    def test_result_fields(self, sample_report: dict):
        """Each result must have the core benchmark fields."""
        required_keys = {
            "name",
            "circuit_type",
            "num_qubits",
            "shots",
            "fidelity",
            "passed",
            "execution_time_ms",
            "timestamp",
        }
        for i, result in enumerate(sample_report["results"]):
            missing = required_keys - set(result.keys())
            assert not missing, f"Result [{i}] ({result.get('name', '?')}) missing: {missing}"

    def test_fidelity_range(self, sample_report: dict):
        for result in sample_report["results"]:
            assert 0.0 <= result["fidelity"] <= 1.0, (
                f"{result['name']}: fidelity {result['fidelity']} out of range"
            )

    def test_passed_is_boolean(self, sample_report: dict):
        for result in sample_report["results"]:
            assert isinstance(result["passed"], bool)

    def test_summary_counts(self, sample_report: dict):
        """Verify total/passed/failed counts are consistent."""
        total = sample_report["total_benchmarks"]
        passed = sample_report["passed"]
        failed = sample_report["failed"]
        assert total == passed + failed
        assert total == len(sample_report["results"])
        assert passed == sum(1 for r in sample_report["results"] if r["passed"])
