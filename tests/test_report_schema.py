"""Tests that benchmark report output conforms to the expected JSON schema.

Validates:
- JSON report validates against schema
- Sample report validates
- Missing required field fails validation
- Report version is correct
"""

from __future__ import annotations

import copy
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


# ---------------------------------------------------------------------------
# Lightweight schema validator (no jsonschema dependency)
# ---------------------------------------------------------------------------

def _validate_against_schema(data: dict, schema: dict) -> list[str]:
    """Lightweight schema validation without jsonschema dependency.

    Checks required fields, types, const values, and nested structure as
    defined in the schema.  Returns a list of error strings (empty == valid).
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

            if "const" in prop_schema and value != prop_schema["const"]:
                errors.append(f"{field_path}: expected const {prop_schema['const']!r}, got {value!r}")

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


# ===================================================================
# Test: schema & sample files exist
# ===================================================================

class TestSchemaFileExists:
    def test_schema_exists(self):
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_json(self, schema: dict):
        assert "$schema" in schema or "type" in schema

    def test_sample_exists(self):
        assert SAMPLE_PATH.exists(), f"Sample report not found at {SAMPLE_PATH}"


# ===================================================================
# Test: JSON report validates against schema
# ===================================================================

class TestJsonReportValidatesAgainstSchema:
    def test_sample_validates(self, sample_report: dict, schema: dict):
        errors = _validate_against_schema(sample_report, schema)
        assert errors == [], "Schema validation errors:\n" + "\n".join(errors)

    def test_has_required_top_level_fields(self, sample_report: dict, schema: dict):
        for field in schema.get("required", []):
            assert field in sample_report, f"Missing required top-level field: {field}"

    def test_results_is_nonempty_list(self, sample_report: dict):
        assert isinstance(sample_report["results"], list)
        assert len(sample_report["results"]) > 0

    def test_each_result_has_required_fields(self, sample_report: dict, schema: dict):
        items_schema = schema["properties"]["results"]["items"]
        required = items_schema.get("required", [])
        for i, result in enumerate(sample_report["results"]):
            for req in required:
                assert req in result, f"Result [{i}] ({result.get('name', '?')}) missing '{req}'"

    def test_fidelity_range(self, sample_report: dict):
        for r in sample_report["results"]:
            assert 0.0 <= r["fidelity"] <= 1.0, f"{r['name']}: fidelity out of range"

    def test_passed_is_boolean(self, sample_report: dict):
        for r in sample_report["results"]:
            assert isinstance(r["passed"], bool)

    def test_family_summary_present(self, sample_report: dict):
        assert "family_summary" in sample_report
        assert isinstance(sample_report["family_summary"], list)


# ===================================================================
# Test: missing required field fails validation
# ===================================================================

class TestMissingFieldFailsValidation:
    @pytest.mark.parametrize("field", ["version", "timestamp", "suite", "environment", "results", "summary"])
    def test_remove_top_level_field(self, sample_report: dict, schema: dict, field: str):
        broken = copy.deepcopy(sample_report)
        del broken[field]
        errors = _validate_against_schema(broken, schema)
        assert any(field in e for e in errors), f"Removing '{field}' should produce a validation error"

    def test_remove_result_name(self, sample_report: dict, schema: dict):
        broken = copy.deepcopy(sample_report)
        del broken["results"][0]["name"]
        errors = _validate_against_schema(broken, schema)
        assert any("name" in e for e in errors)

    def test_remove_result_fidelity(self, sample_report: dict, schema: dict):
        broken = copy.deepcopy(sample_report)
        del broken["results"][0]["fidelity"]
        errors = _validate_against_schema(broken, schema)
        assert any("fidelity" in e for e in errors)

    def test_remove_result_passed(self, sample_report: dict, schema: dict):
        broken = copy.deepcopy(sample_report)
        del broken["results"][0]["passed"]
        errors = _validate_against_schema(broken, schema)
        assert any("passed" in e for e in errors)

    def test_remove_result_latency(self, sample_report: dict, schema: dict):
        broken = copy.deepcopy(sample_report)
        del broken["results"][0]["latency_ms"]
        errors = _validate_against_schema(broken, schema)
        assert any("latency_ms" in e for e in errors)


# ===================================================================
# Test: report version is correct
# ===================================================================

class TestReportVersionCorrect:
    def test_sample_version_is_1_0_0(self, sample_report: dict):
        assert sample_report["version"] == "1.0.0"

    def test_wrong_version_fails(self, sample_report: dict, schema: dict):
        broken = copy.deepcopy(sample_report)
        broken["version"] = "0.0.1"
        errors = _validate_against_schema(broken, schema)
        assert any("version" in e and "const" in e for e in errors)


# ===================================================================
# Test: summary statistics are consistent
# ===================================================================

class TestSummaryConsistency:
    def test_total_equals_results_length(self, sample_report: dict):
        assert sample_report["summary"]["total"] == len(sample_report["results"])

    def test_passed_plus_failed_equals_total(self, sample_report: dict):
        s = sample_report["summary"]
        assert s["passed"] + s["failed"] == s["total"]

    def test_passed_count_matches_results(self, sample_report: dict):
        actual_passed = sum(1 for r in sample_report["results"] if r["passed"])
        assert sample_report["summary"]["passed"] == actual_passed

    def test_pass_rate_value(self, sample_report: dict):
        s = sample_report["summary"]
        expected_rate = s["passed"] / s["total"] if s["total"] else 0.0
        assert abs(s["pass_rate"] - expected_rate) < 1e-4
