# Compliance Checker Design Specification

## 1. Overview
The **Compliance Checker** is a feasibility demonstration for using Large Language Models (LLMs) to automate legal and regulatory compliance checks. It translates natural language rules into executable validation logic, which is then applied to semi-structured data.

## 2. Architecture
The system follows a modular "Translator & Orchestrator" pattern:
- **Parser**: Extracts data from a semi-structured text file (ex: dummy.md).
- **LLM Translator**: Interprets natural language rules and maps them to a library of validation functions.
- **Helper Library**: A collection of reusable Python functions for atomic data validation.
- **Orchestrator**: The central engine that executes the mapped validation logic and reports results.

## 3. Component Breakdown

### 3.1 Data Parser (`src/parser.py`)
- **Input**: A text file (e.g., `dummy.md`) with `Field: Value` format.
- **Output**: A Python dictionary.
- **Logic**: Splits each line by the first colon (`:`) and trims whitespace.

### 3.2 Helper Library (`src/helpers.py`)
Provides atomic validation functions. All functions should return a boolean (True for valid, False for invalid) or a descriptive error message.
- `check_not_empty(value)`: Returns True if value is not empty/whitespace.
- `check_numeric(value)`: Returns True if value can be converted to a number.
- `check_range(value, min_val, max_val)`: Returns True if numeric value is within [min, max].
- `check_date_valid(value, format="%d-%m-%Y")`: Returns True if date matches format.
- `check_alphabetical(value)`: Returns True if value contains only letters/spaces.

### 3.3 LLM Translator (`src/llm_service.py`)
- **Input**: Contents of `rules.md`.
- **Mechanism**: Calls an LLM (OpenAI/Gemini/etc.) with a specific prompt.
- **Prompt Strategy**:
    - List available helper functions and their signatures.
    - Provide the rules text.
    - Request a JSON output mapping field names to a list of helper calls.
- **Example Output**:
  ```json
  {
    "Tuổi": ["check_not_empty", "check_numeric", "check_range(0, 100)"],
    "Năm sinh": ["check_not_empty", "check_date_valid"]
  }
  ```

### 3.4 Orchestrator (`src/main.py`)
- **Workflow**:
    1. Parse `dummy.md` into `data`.
    2. Translate `rules.md` into `rule_map` via LLM.
    3. Iterate through `rule_map`:
        - For each field, execute the corresponding helper functions on the `data` value.
        - Track failures.
    4. Output results to console.
- **Success Criteria**: If all pass, output `SUCCESS`. If any fail, output `INVALID` with field name and failed rule.

## 4. Implementation Details
- **Language**: Python 3.x
- **Configuration**: API key stored in `.env`.
- **Environment**: Basic Python (using `python-dotenv` and `requests` or an LLM SDK).

## 5. Success/Failure Examples (Mockup)
- **Input**: `Tuổi: 105`, **Rule**: `Tuổi 0-100` -> **Output**: `INVALID: Field 'Tuổi' failed 'check_range(0, 100)' (Value: 105)`.
- **Input**: `Họ tên: `, **Rule**: `Không được để trống` -> **Output**: `INVALID: Field 'Họ tên' failed 'check_not_empty' (Value: )`.
