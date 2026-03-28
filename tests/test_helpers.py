import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.helpers import (
    check_not_empty,
    check_numeric,
    check_range,
    check_date_format,
    check_alphabetical
)

def test_check_not_empty():
    assert check_not_empty("Lê Hoàng Minh")[0] is True
    assert check_not_empty("")[0] is False
    assert check_not_empty("   ")[0] is False

def test_check_numeric():
    assert check_numeric("4")[0] is True
    assert check_numeric("abc")[0] is False

def test_check_range():
    assert check_range("4", 0, 100)[0] is True
    assert check_range("105", 0, 100)[0] is False
    assert check_range("abc", 0, 100)[0] is False

def test_check_date_format():
    assert check_date_format("11-09-2022", "%d-%m-%Y")[0] is True
    assert check_date_format("2022-09-11", "%d-%m-%Y")[0] is False

def test_check_alphabetical():
    assert check_alphabetical("Lê Hoàng Minh")[0] is True
    assert check_alphabetical("Tuổi: 4")[0] is False
