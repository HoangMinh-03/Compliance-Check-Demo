import pytest
from src.core.orchestrator import run_compliance_check

def test_nested_check_if_with_string_helper():
    """Kiểm tra check_if với helper được truyền dưới dạng string (không có ngoặc)"""
    data = {
        "Tuổi": "15",
        "Người đại diện": ""
    }
    # Nếu Tuổi < 18, Người đại diện không được để trống
    rule_map = {
        "Người đại diện": ["check_if(check_logic_smaller(Tuổi, 18), check_not_empty)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    
    assert all_pass is False
    assert any("Người" in r and "check_if" in r for r in results)

def test_nested_check_if_pass():
    """Kiểm tra check_if pass khi điều kiện sai"""
    data = {
        "Tuổi": "20",
        "Người đại diện": ""
    }
    # Nếu Tuổi < 18, Người đại diện không được để trống. Ở đây Tuổi=20 -> pass.
    rule_map = {
        "Người đại diện": ["check_if(check_logic_smaller(Tuổi, 18), check_not_empty)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    
    assert all_pass is True
    assert len(results) == 0

def test_logic_greater_between_fields():
    """Kiểm tra so sánh giữa 2 trường dữ liệu"""
    data = {
        "Số tiền yêu cầu": "1000",
        "Số dư tài khoản": "500"
    }
    # Số dư phải lớn hơn Số tiền yêu cầu
    rule_map = {
        "Số dư tài khoản": ["check_logic_greater(Số dư tài khoản, Số tiền yêu cầu)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    print(f"DEBUG RESULTS: {results}")
    
    assert all_pass is False
    assert any("Số dư tài khoản" in r and "check_logic_greater" in r for r in results)

def test_logic_greater_pass():
    data = {
        "Số tiền yêu cầu": "1000",
        "Số dư tài khoản": "2000"
    }
    rule_map = {
        "Số dư tài khoản": ["check_logic_greater(Số dư tài khoản, Số tiền yêu cầu)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    
    assert all_pass is True

def test_calculate_age_nested():
    data = {
        "Ngày sinh": "01-01-2010", # 16 tuổi (giả sử năm hiện tại là 2026 như trong context)
        "Người giám hộ": ""
    }
    # check_if(calculate_age(Ngày sinh) < 18, check_not_empty)
    # Lưu ý: calculate_age trả về int, check_logic_smaller dùng để so sánh
    rule_map = {
        "Người giám hộ": ["check_if(check_logic_smaller(calculate_age(Ngày sinh), 18), check_not_empty)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    
    assert all_pass is False
    assert any("Người" in r and "check_if" in r for r in results)

def test_math_mapping_execution():
    """Kiểm tra việc thực thi biểu thức toán học trong mapping"""
    data = {
        "Tiền lời": "100",
        "Tiền gửi": "1000"
    }
    # Lãi suất = 100/1000 = 0.1
    mapping = {
        "Lãi suất": "divide(Tiền lời, Tiền gửi)"
    }
    # Kiểm tra Lãi suất == 10% (0.1)
    rule_map = {
        "Lãi suất": ["check_logic_equal(0.1)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map, mapping=mapping)
    
    assert all_pass is True
