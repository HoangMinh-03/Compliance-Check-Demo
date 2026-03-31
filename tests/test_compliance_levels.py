import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.orchestrator import run_compliance_check

# Dữ liệu giả lập cho các bài test
COMMON_DATA = {
    "Họ và tên": "Nguyễn Văn A",
    "Tuổi": "25",
    "Ngày sinh": "15-05-1999",
    "Năm sinh": "1999",
    "Email": "test@example.com",
    "Người giám hộ": "Lê Thị B",
    "Lãi suất": "15%"
}

def test_level_1_direct():
    # Quy tắc: Họ và tên không được để trống
    rule_map = {"Họ và tên": ["check_not_empty"]}
    success, _ = run_compliance_check(COMMON_DATA, rule_map)
    assert success is True

def test_level_4_two_independent():
    # Quy tắc: Tuổi phải là số và không được vượt quá 100
    rule_map = {"Tuổi": ["check_numeric", "check_range(0, 100)"]}
    success, _ = run_compliance_check(COMMON_DATA, rule_map)
    assert success is True

def test_level_5_multi_condition():
    # Quy tắc: Họ tên không được trống, chỉ chứa chữ cái và dài từ 2-50 ký tự
    rule_map = {"Họ và tên": ["check_not_empty", "check_alphabetical", "check_length(2, 50)"]}
    success, _ = run_compliance_check(COMMON_DATA, rule_map)
    assert success is True

def test_level_6_chained_logic():
    # Quy tắc: Năm sinh phải khớp với số tuổi đã khai báo (2026 - 1999 = 27)
    # COMMON_DATA có Tuổi=25, Năm sinh=1999 -> 2026 - 1999 = 27 != 25 -> FAIL
    rule_map = {"Tuổi": ["check_logic_equal(calculate_age(Năm sinh))"]}
    success, reports = run_compliance_check(COMMON_DATA, rule_map)
    assert success is False 

def test_level_7_conditional_if_then():
    # Quy tắc: Nếu tuổi nhỏ hơn 18, phải có thêm trường thông tin Người giám hộ.
    # Case 1: Tuổi >= 18 -> True
    data_adult = {**COMMON_DATA, "Tuổi": "25"}
    rule_map = {"Tuổi": ["check_numeric"]} # Logic If-Then cần xử lý ở tầng cao hơn hoặc helper đặc biệt
    # Hiện tại hệ thống chưa có helper logic If-Then trong orchestrator, 
    # nhưng chúng ta có thể giả lập bằng cách LLM chỉ gen rule check_not_empty cho "Người giám hộ" nếu nó thấy tuổi < 18.
    
def test_level_8_real_time_logic():
    # Quy tắc: Ngày tháng năm sinh không được là một ngày trong tương lai.
    rule_map = {"Ngày sinh": ["check_logic_smaller(extract_year(Ngày sinh), 2027)"]}
    success, _ = run_compliance_check(COMMON_DATA, rule_map)
    assert success is True

def test_level_9_implicit_business():
    # Quy tắc: Đối với trẻ em (dưới 6 tuổi), năm sinh phải nằm trong vòng 6 năm trở lại đây.
    # Giả sử current_year = 2026
    data_child = {**COMMON_DATA, "Tuổi": "4", "Năm sinh": "2022"}
    rule_map = {"Năm sinh": ["check_range(2020, 2026)"]}
    success, _ = run_compliance_check(data_child, rule_map)
    assert success is True

def test_level_10_conflict_priority():
    # Quy tắc: Ưu tiên định dạng ngày tháng: Nếu có cả Năm sinh và Tuổi, 
    # hãy dùng Năm sinh để tính lại Tuổi chuẩn.
    # Đây là logic ghi đè dữ liệu trước khi check.
    pass
