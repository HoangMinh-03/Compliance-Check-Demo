# Compliance Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Compliance Checker that uses a local LLM to map natural language rules to Python validation functions and executes them on data from a file.

**Architecture:** A modular "Translator & Orchestrator" pattern where data parsing, rule translation (LLM), and execution are decoupled. Uses a library of atomic helper functions for validation.

**Tech Stack:** Python 3.x, `requests`, `python-dotenv`.

---

### Task 1: Setup Environment and Dependencies

**Files:**
- Create: `requirements.txt`
- Modify: `.env` (verify content)

- [ ] **Step 1: Create `requirements.txt`**

```text
python-dotenv
requests
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Installation successful.

- [ ] **Step 3: Verify `.env` file**

Ensure `.env` contains:
```env
LLM_URL=http://localhost:11434
LLM_MODEL=qwen3.5:2b
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt .env
git commit -m "chore: setup environment and dependencies"
```

---

### Task 2: Implement Helper Library (`src/helpers.py`)

**Files:**
- Create: `src/helpers.py`
- Create: `tests/test_helpers.py`

- [ ] **Step 1: Write tests for helpers**

```python
import pytest
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_helpers.py`
Expected: FAIL (Module not found/Functions not defined)

- [ ] **Step 3: Implement `src/helpers.py`**

```python
import re
from datetime import datetime

def check_not_empty(value):
    if value and value.strip():
        return True, ""
    return False, "Trường dữ liệu không được để trống"

def check_numeric(value):
    try:
        float(value)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không phải là số"

def check_range(value, min_val, max_val):
    is_num, msg = check_numeric(value)
    if not is_num:
        return False, msg
    val = float(value)
    if min_val <= val <= max_val:
        return True, ""
    return False, f"Giá trị {val} nằm ngoài khoảng {min_val} đến {max_val}"

def check_date_format(value, date_format="%d-%m-%Y"):
    try:
        datetime.strptime(value, date_format)
        return True, ""
    except (ValueError, TypeError):
        return False, f"'{value}' không đúng định dạng {date_format}"

def check_alphabetical(value):
    # Vietnamese characters support
    if re.match(r"^[a-zA-Z\sÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠàáâãèéêìíòóôõùúăđĩũơƯĂÂÊÔƠƯưăâêôơư]+$", value):
        return True, ""
    return False, f"'{value}' chứa ký tự không phải chữ cái"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_helpers.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/helpers.py tests/test_helpers.py
git commit -m "feat: implement helper library with tests"
```

---

### Task 3: Implement Data Parser (`src/parser.py`)

**Files:**
- Create: `src/parser.py`
- Create: `tests/test_parser.py`

- [ ] **Step 1: Write tests for parser**

```python
import pytest
import os
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_parser.py`
Expected: FAIL

- [ ] **Step 3: Implement `src/parser.py`**

```python
def parse_dummy_file(file_path):
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_parser.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/parser.py tests/test_parser.py
git commit -m "feat: implement data parser with tests"
```

---

### Task 4: Implement LLM Translator (`src/llm_service.py`)

**Files:**
- Create: `src/llm_service.py`

- [ ] **Step 1: Implement `src/llm_service.py`**

```python
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

LLM_URL = os.getenv("LLM_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

def translate_rules(rules_text):
    prompt = f"""
Bạn là một chuyên gia kiểm soát tuân thủ. Hãy dịch các quy tắc (rules) dưới đây sang định dạng JSON ánh xạ tên trường dữ liệu (field) với các hàm kiểm tra (helpers).

Các hàm helper có sẵn:
- check_not_empty(value): Kiểm tra không được để trống.
- check_numeric(value): Kiểm tra là số.
- check_range(value, min_val, max_val): Kiểm tra số nằm trong khoảng [min_val, max_val].
- check_date_format(value, format="%d-%m-%Y"): Kiểm tra định dạng ngày tháng.
- check_alphabetical(value): Kiểm tra chỉ chứa chữ cái.

Quy tắc: {rules_text}

Yêu cầu trả về DUY NHẤT một đối tượng JSON có định dạng như sau:
{{
  "Tên Field": ["hàm_1", "hàm_2(tham_số)"]
}}

Ví dụ:
{{
  "Tuổi": ["check_not_empty", "check_numeric", "check_range(0, 100)"],
  "Năm sinh": ["check_date_format('%d-%m-%Y')"]
}}
"""
    
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    try:
        response = requests.post(f"{LLM_URL}/api/generate", json=payload)
        response.raise_for_status()
        result = response.json()
        return json.loads(result['response'])
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None
```

- [ ] **Step 2: Manual check with local LLM (if running)**

Run: `python -c "from src.llm_service import translate_rules; print(translate_rules('Tuổi phải là số từ 0-100'))"`
Expected: JSON output like `{'Tuổi': ['check_numeric', 'check_range(0, 100)']}`

- [ ] **Step 3: Commit**

```bash
git add src/llm_service.py
git commit -m "feat: implement llm translator service"
```

---

### Task 5: Implement Orchestrator and Main Entry (`src/main.py`)

**Files:**
- Create: `src/main.py`
- Create: `src/orchestrator.py`

- [ ] **Step 1: Implement `src/orchestrator.py`**

```python
from src.helpers import *

def run_compliance_check(data_dict, rule_map):
    all_pass = True
    results = []
    
    for field, rules in rule_map.items():
        if field not in data_dict:
            results.append(f"INVALID: Field '{field}' is missing in data.")
            all_pass = False
            continue
            
        value = data_dict[field]
        for rule_str in rules:
            # Simple dynamic call parser for functions like check_range(0, 100)
            try:
                if '(' in rule_str:
                    func_name, args_str = rule_str.split('(', 1)
                    args_str = args_str.rstrip(')')
                    # Parse args, handle quotes
                    args = [eval(arg.strip()) for arg in args_str.split(',')]
                    func = globals()[func_name]
                    is_valid, msg = func(value, *args)
                else:
                    func = globals()[rule_str]
                    is_valid, msg = func(value)
                
                if not is_valid:
                    results.append(f"INVALID: Field '{field}' failed '{rule_str}' (Value: '{value}'). Reason: {msg}")
                    all_pass = False
            except Exception as e:
                results.append(f"ERROR: Could not execute rule '{rule_str}' on field '{field}': {e}")
                all_pass = False
                
    return all_pass, results
```

- [ ] **Step 2: Implement `src/main.py`**

```python
import os
from src.parser import parse_dummy_file
from src.llm_service import translate_rules
from src.orchestrator import run_compliance_check

def main():
    dummy_file = "dummy.md"
    rules_file = "rules.md"
    
    if not os.path.exists(dummy_file) or not os.path.exists(rules_file):
        print("Error: dummy.md or rules.md not found.")
        return

    print("--- 1. Parsing Data ---")
    data = parse_dummy_file(dummy_file)
    print(f"Data found: {data}")

    print("\n--- 2. Translating Rules via LLM ---")
    with open(rules_file, 'r', encoding='utf-8') as f:
        rules_text = f.read()
    
    rule_map = translate_rules(rules_text)
    if not rule_map:
        print("Failed to translate rules.")
        return
    print(f"Rule Map: {rule_map}")

    print("\n--- 3. Running Compliance Check ---")
    success, reports = run_compliance_check(data, rule_map)
    
    if success:
        print("RESULT: SUCCESS")
    else:
        print("RESULT: FAILED")
        for report in reports:
            print(report)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run full integration test**

Run: `python src/main.py`
Expected: Output showing SUCCESS or INVALID based on `dummy.md` and `rules.md`.

- [ ] **Step 4: Commit**

```bash
git add src/orchestrator.py src/main.py
git commit -m "feat: implement orchestrator and main entry point"
```
