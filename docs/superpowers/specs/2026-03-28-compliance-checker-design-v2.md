# Compliance Checker Design Specification (v2)

## 1. Overview
The **Compliance Checker** is a feasibility demonstration for using Large Language Models (LLMs) to automate legal and regulatory compliance checks. It translates natural language rules into executable validation logic, which is then applied to semi-structured data. This version is optimized for local LLM usage (Ollama/Qwen) and Vietnamese language rules.

## 2. Architecture
The system follows a modular "Translator & Orchestrator" pattern:
- **Parser**: Extracts data from `dummy.md`.
- **LLM Translator**: Interprets natural language rules from `rules.md` and maps them to a library of validation functions.
- **Helper Library**: A collection of reusable Python functions for atomic data validation.
- **Orchestrator**: The central engine that executes the mapped validation logic and reports results.

## 3. Component Breakdown

### 3.1 Data Parser (`src/parser.py`)
- **Input**: `dummy.md` (Format: `Field: Value`).
- **Output**: Python Dictionary.
- **Logic**: Reads file line by line, splits by the first colon (`:`), and strips whitespace.

### 3.2 Helper Library (`src/helpers.py`)
Atomic validation functions returning `(bool, str)` where `str` is an error message if `bool` is `False`.
- `check_not_empty(value)`: True if value is not empty/whitespace.
- `check_numeric(value)`: True if value can be converted to a number.
- `check_range(value, min_val, max_val)`: True if numeric value is within [min, max].
- `check_date_format(value, format="%d-%m-%Y")`: True if date matches format.
- `check_alphabetical(value)`: True if value contains only letters/spaces.

### 3.3 LLM Translator (`src/llm_service.py`)
- **Input**: Contents of `rules.md`.
- **Mechanism**: Calls local LLM API (`LLM_URL` in `.env`, e.g., Ollama) using `requests`.
- **Prompt Strategy**:
    - Focus on Vietnamese language rules.
    - Provide a list of available helper functions with signatures and descriptions.
    - Request a strictly formatted JSON output mapping Vietnamese field names to helper calls.
- **Example Output**:
  ```json
  {
    "Tuổi": ["check_not_empty", "check_numeric", "check_range(0, 100)"],
    "Năm sinh": ["check_not_empty", "check_date_format('%d-%m-%Y')"]
  }
  ```

### 3.4 Orchestrator (`src/main.py`)
- **Workflow**:
    1. Parse `dummy.md` into `data_dict`.
    2. Read `rules.md` and send to `llm_service` to get `rule_map`.
    3. Iterate through `rule_map`:
        - For each field, dynamically call the listed helper functions from `helpers.py` using the value from `data_dict`.
        - Handle missing fields in `data_dict` by reporting `FIELD_MISSING`.
    4. Console Output:
        - `SUCCESS` if all rules pass.
        - `INVALID: Field '[Field]' failed '[Helper]' (Value: [Value])` if any fail.

## 4. Implementation Details
- **Language**: Python 3.x
- **Configuration**: `LLM_URL` and `LLM_MODEL` stored in `.env`.
- **Dependencies**: `python-dotenv`, `requests`.

## 5. Error Handling
- **LLM Failure**: If the local LLM returns malformed JSON, the service will log the raw output and error out (optionally retry).
- **Direct Sending**: Rules are sent directly to the LLM without pre-validation of content (as requested).
