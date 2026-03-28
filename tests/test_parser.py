import pytest
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import parse_dummy_file

def test_parse_dummy_file(tmp_path):
    d = tmp_path / "test_dummy.md"
    content = "Họ và tên: Lê Hoàng Minh\nTuổi: 4\nNăm sinh: 11-09-2022"
    d.write_text(content, encoding='utf-8')
    
    result = parse_dummy_file(str(d))
    assert result == {
        "Họ và tên": "Lê Hoàng Minh",
        "Tuổi": "4",
        "Năm sinh": "11-09-2022"
    }

def test_parse_empty_file(tmp_path):
    d = tmp_path / "empty.md"
    d.write_text("", encoding='utf-8')
    assert parse_dummy_file(str(d)) == {}
