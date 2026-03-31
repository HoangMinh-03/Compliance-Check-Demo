import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.orchestrator import run_compliance_check, parse_rule_string, resolve_arg

def test_parse_rule_string():
    # Simple rule
    assert parse_rule_string("check_not_empty") == {"function": "check_not_empty", "args": []}
    # Rule with args
    assert parse_rule_string("check_range(0, 100)") == {"function": "check_range", "args": [0, 100]}
    # Rule with string args
    assert parse_rule_string("check_date_format('%d-%m-%Y')") == {"function": "check_date_format", "args": ["%d-%m-%Y"]}
    # Complex nested rule (as string)
    parsed = parse_rule_string("check_range(0, calculate_age(extract_year(Ngày sinh, '%d-%m-%Y')))")
    assert parsed["function"] == "check_range"
    assert parsed["args"][0] == 0
    assert "calculate_age" in parsed["args"][1]

def test_resolve_arg_simple():
    data = {"Tuổi": "25", "Năm sinh": "2000"}
    # Field name resolution
    assert resolve_arg("Tuổi", data) == "25"
    # Literal resolution
    assert resolve_arg("100", data) == 100
    # Function call resolution
    assert resolve_arg("calculate_age(2000)", data) == 26 # Assuming 2026 current year

def test_run_compliance_complex_logic():
    data = {
        "Họ tên": "Nguyễn Văn A",
        "Tuổi": "26",
        "Năm sinh": "11-09-2000"
    }
    # Test case: Tuổi phải khớp với Năm sinh
    rule_map = {
        "Tuổi": ["check_logic_equal(calculate_age(Năm sinh))"]
    }
    success, reports = run_compliance_check(data, rule_map)
    assert success is True
    assert len(reports) == 0

def test_run_compliance_with_failure():
    data = {
        "Tuổi": "30",
        "Năm sinh": "11-09-2000"
    }
    # 2026 - 2000 = 26 != 30
    rule_map = {
        "Tuổi": ["check_logic_equal(calculate_age(Năm sinh))"]
    }
    success, reports = run_compliance_check(data, rule_map)
    assert success is False
    assert any("INVALID" in r for r in reports)

def test_run_compliance_nested_functions():
    data = {
        "Ngày sinh": "11-09-2000",
        "Năm hiện tại": "2026"
    }
    # Logic: Năm sinh không được lớn hơn năm hiện tại
    rule_map = {
        "Ngày sinh": ["check_logic_smaller(extract_year(Ngày sinh), 2027)"]
    }
    success, reports = run_compliance_check(data, rule_map)
    assert success is True
