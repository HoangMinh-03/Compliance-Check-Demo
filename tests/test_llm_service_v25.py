import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.llm_service import translate_rules, map_data_to_plan

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_translate_rules_no_fields():
    rules = "Tuổi phải lớn hơn 18"
    plan = await translate_rules(rules)
    assert plan is not None
    # We expect the LLM to identify "Tuổi" as a field from the rule text
    assert any("Tuổi" in k for k in plan.keys())

@pytest.mark.anyio
async def test_map_data_to_plan():
    required_fields = ["Ngày sinh", "Họ tên"]
    data_keys = ["dob", "full_name", "address"]
    mapping = await map_data_to_plan(required_fields, data_keys)
    assert mapping is not None
    # We expect the LLM to map "Ngày sinh" to "dob" and "Họ tên" to "full_name"
    assert mapping.get("Ngày sinh") == "dob"
    assert mapping.get("Họ tên") == "full_name"
