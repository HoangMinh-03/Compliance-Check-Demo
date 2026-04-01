import pytest
from src.core.orchestrator import run_compliance_check

def test_nested_crossfield_resolution():
    """
    Kiểm tra case: Trường 'Người đại diện' có rule phụ thuộc vào giá trị của 'Ngày tháng năm sinh'.
    Đây là mô phỏng nút 'Chạy thử' trong modal Approval (chưa có mapping).
    """
    data = {
        "Ngày tháng năm sinh": "01-01-2010", # 16 tuổi (năm 2026)
        "Người đại diện": "" # Đang trống
    }
    
    # Rule: check_if(Tuổi < 18, check_not_empty)
    # Tuổi được tính từ 'Ngày tháng năm sinh'
    rule_map = {
        "Người đại diện": ["check_if(check_logic_smaller(calculate_age(extract_year(Ngày tháng năm sinh, '%d-%m-%Y')), 18), check_not_empty)"]
    }
    
    # Thực thi
    all_pass, results = run_compliance_check(data, rule_map)
    
    # Kết quả kỳ vọng: 
    # 1. calculate_age(2010) -> 16
    # 2. check_logic_smaller(16, 18) -> True
    # 3. check_if(True, check_not_empty) -> thực thi check_not_empty("") -> False
    # => all_pass should be False
    
    print(f"RESULTS: {results}")
    assert all_pass is False
    assert any("Người đại diện" in r and "INVALID" in r for r in results)

def test_nested_crossfield_resolution_pass():
    """Kiểm tra case tương tự nhưng pass (tuổi > 18)"""
    data = {
        "Ngày tháng năm sinh": "01-01-2000", # 26 tuổi
        "Người đại diện": ""
    }
    
    rule_map = {
        "Người đại diện": ["check_if(check_logic_smaller(calculate_age(extract_year(Ngày tháng năm sinh, '%d-%m-%Y')), 18), check_not_empty)"]
    }
    
    all_pass, results = run_compliance_check(data, rule_map)
    
    # Tuổi = 26. 26 < 18 is False. check_if(False, ...) returns True.
    assert all_pass is True
    assert len(results) == 0
