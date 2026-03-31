import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.orchestrator import run_compliance_check

def test_run_with_mapping():
    data = {"dob": "1990-01-01"}
    plan = {"Ngày sinh": ["check_not_empty"]}
    mapping = {"Ngày sinh": "dob"}
    is_valid, results = run_compliance_check(data, plan, mapping=mapping)
    assert is_valid is True
    assert len(results) == 0

def test_run_with_missing_mapped_field():
    data = {"full_name": "Nguyen Van A"}
    plan = {"Ngày sinh": ["check_not_empty"]}
    mapping = {"Ngày sinh": "dob"}
    is_valid, results = run_compliance_check(data, plan, mapping=mapping)
    assert is_valid is False
    assert any("MISSING_FIELD: 'dob' (mapped from 'Ngày sinh')" in r for r in results)

def test_run_without_mapping_fallback():
    data = {"Ngày sinh": "1990-01-01"}
    plan = {"Ngày sinh": ["check_not_empty"]}
    is_valid, results = run_compliance_check(data, plan)
    assert is_valid is True
    assert len(results) == 0

def test_resolve_arg_with_mapping():
    data = {
        "signing_date": "01-11-2023",
        "expiry_date": "02-11-2023"
    }
    # Rule uses 'Ngày ký' which is NOT in data, but is in mapping
    plan = {
        "Ngày hết hạn": ["check_date_after(Ngày ký)"]
    }
    mapping = {
        "Ngày hết hạn": "expiry_date",
        "Ngày ký": "signing_date"
    }
    is_valid, results = run_compliance_check(data, plan, mapping=mapping)
    assert is_valid is True
    assert len(results) == 0
