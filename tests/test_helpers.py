import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.helpers import (
    check_not_empty,
    check_numeric,
    check_range,
    check_date_format,
    check_alphabetical,
    check_length,
    check_regex,
    calculate_age,
    extract_year,
    check_logic_equal,
    check_logic_greater,
    check_logic_smaller,
    check_list_membership,
    check_email,
    check_visa,
    check_mastercard,
    check_swift_bic,
    check_currency_format
)

def test_check_not_empty():
    assert check_not_empty("Hello")[0] is True
    assert check_not_empty("")[0] is False
    assert check_not_empty("  ")[0] is False

def test_check_numeric():
    assert check_numeric("123")[0] is True
    assert check_numeric("12.3")[0] is True
    assert check_numeric("20%")[0] is True
    assert check_numeric("abc")[0] is False

def test_check_range():
    assert check_range("50", 0, 100)[0] is True
    assert check_range("150", 0, 100)[0] is False
    assert check_range("20%", 0, 100)[0] is True
    assert check_range("abc", 0, 100)[0] is False

def test_check_date_format():
    assert check_date_format("30-03-2026", "%d-%m-%Y")[0] is True
    assert check_date_format("2026-03-30", "%Y-%m-%d")[0] is True
    assert check_date_format("30/03/2026", "%d-%m-%Y")[0] is False

def test_check_alphabetical():
    assert check_alphabetical("Nguyễn Văn A")[0] is True
    assert check_alphabetical("Nguyen Van A 123")[0] is False

def test_check_length():
    assert check_length("Hello", 2, 10)[0] is True
    assert check_length("A", 2, 10)[0] is False
    assert check_length("Very long string", 2, 10)[0] is False

def test_check_regex():
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    assert check_regex("test@example.com", email_regex)[0] is True
    assert check_regex("invalid-email", email_regex)[0] is False

def test_calculate_age():
    from datetime import datetime
    current_year = datetime.now().year
    # Fix syntax error: remove walrus operator inside assert
    age = calculate_age(str(current_year - 20))
    assert age == 20
    assert calculate_age("01-01-2000") == current_year - 2000
    assert calculate_age("invalid") == -1

def test_extract_year():
    assert extract_year("30-03-2026", "%d-%m-%Y") == 2026
    assert extract_year("2025/12/31", "%Y/%m/%d") == 2025
    assert extract_year("invalid", "%d-%m-%Y") == 0

def test_logic_comparisons():
    assert check_logic_equal("100", "100")[0] is True
    assert check_logic_equal("100", 100)[0] is True
    assert check_logic_greater("100", "50")[0] is True
    assert check_logic_smaller("50", "100")[0] is True
    assert check_logic_equal("20%", "0.2")[0] is True

def test_check_list_membership():
    assert check_list_membership("A", ["A", "B", "C"])[0] is True
    assert check_list_membership("D", ["A", "B", "C"])[0] is False

def test_new_format_helpers():
    # Email
    assert check_email("test@example.com")[0] is True
    assert check_email("invalid-email")[0] is False
    
    # Visa
    assert check_visa("4111 1111 1111 1111")[0] is True
    assert check_visa("5111 1111 1111 1111")[0] is False # Starts with 5
    
    # Mastercard
    assert check_mastercard("5111 1111 1111 1111")[0] is True
    assert check_mastercard("4111 1111 1111 1111")[0] is False
    
    # SWIFT/BIC
    assert check_swift_bic("ABCDEFGH")[0] is True
    assert check_swift_bic("ABCDEFGHIJK")[0] is True
    assert check_swift_bic("ABCDE")[0] is False
    
    # Currency
    assert check_currency_format("$1,000.00")[0] is True
    assert check_currency_format("1.000.000 VND")[0] is True
    assert check_currency_format("500.000đ")[0] is True
    assert check_currency_format("abc")[0] is False
