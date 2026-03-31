import os
import json
import logging
import re
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI
from src.core.helpers import registry

load_dotenv(override=True)
logger = logging.getLogger(__name__)

LLM_URL = os.getenv("LLM_URL")
LLM_MODEL = os.getenv("LLM_MODEL")

client = AsyncOpenAI(base_url=LLM_URL, api_key="sk-no-key-required")

def clean_json_content(content: str) -> str:
    if '<output>' in content and '</output>' in content:
        start = content.find('<output>') + 8
        end = content.find('</output>')
        content = content[start:end].strip()
    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
    if code_block_match: content = code_block_match.group(1).strip()
    return content

async def translate_rules(rules_text: str, available_fields: Optional[List[str]] = None) -> Optional[Dict[str, List[Any]]]:
    """
    Sử dụng LLM để dịch rules văn bản sang Execution Plan (JSON) theo định dạng gốc.
    """
    helpers_list = registry.get_llm_metadata()

    system_prompt = (
        "Bạn là một Chuyên gia Logic học và Kỹ sư Kiểm thử Dữ liệu.\n"
        "Nhiệm vụ của bạn là phân tích các quy tắc văn bản và chuyển đổi chúng thành Execution Plan (JSON).\n"
        "\n"
        "QUY TẮC NGHIÊM NGẶT:\n"
        "1. TUYỆT ĐỐI KHÔNG sử dụng cú pháp Python: 'if', 'else', 'ternary operators', 'index [0]', 'index [1]'.\n"
        "2. CHỈ sử dụng các hàm helper được cung cấp.\n"
        "3. ĐỐI VỚI LOGIC ĐIỀU KIỆN (Nếu-Thì): Sử dụng hàm 'check_if(condition, helper_result)'.\n"
        "   Ví dụ: Nếu tuổi < 18 thì Người giám hộ không được trống:\n"
        "   \"Người giám hộ\": [\"check_if(check_logic_smaller(calculate_age(Ngày sinh), 18), check_not_empty)\"]\n"
        "4. CÁC HÀM TRẢ VỀ TUPLE (is_valid, msg) sẽ được Orchestrator tự động lấy giá trị boolean khi dùng làm tham số cho hàm khác. Bạn KHÔNG cần ghi [0].\n"
        "5. CHỈ tạo quy tắc cho các trường được nhắc đến TRỰC TIẾP trong <rules_text>.\n"
        "\n"
        "Yêu cầu: Output cuối cùng là JSON nằm trong thẻ <output>.\n"
        "Cấu trúc: {\"field_name\": [\"function_name(args)\", ...]}"
    )

    fields_info = f"<available_fields> {', '.join(available_fields)} </available_fields>" if available_fields else ""
    
    user_prompt = f"""
{fields_info}
<helper_functions> 
{helpers_list} 
</helper_functions>
<rules_text> 
{rules_text} 
</rules_text>

Yêu cầu:
Trả về JSON trong thẻ <output>.
Ví dụ: {{"Tuổi": ["check_numeric", "check_range(0, calculate_age(extract_year(Ngày sinh, %Y)))"]}}

JSON:"""

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        logger.info(f"Raw LLM Response: {content}")
        
        cleaned = clean_json_content(content)
        if not cleaned: return None
        
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Lỗi trong LLM Service: {e}")
        return None

async def translate_rule_for_field(rule_text: str, field_name: str, selected_helpers: List[str]) -> Optional[List[Dict[str, Any]]]:
    """Dịch lẻ từng field (giữ lại để hỗ trợ Update v1.5 tương lai)"""
    helpers_info = ""
    for h in selected_helpers:
        helper_func = registry.get_helper(h)
        if helper_func:
            import inspect
            sig = inspect.signature(helper_func)
            desc = registry.metadata.get(h, "")
            helpers_info += f"- {h}{sig}: {desc}\n"
    
    system_prompt = "Bạn là Chuyên gia Logic. Dịch quy tắc thành JSON list các hàm."
    user_prompt = f"Trường: {field_name}\nQuy tắc: {rule_text}\nHelpers:\n{helpers_info}\nOutput JSON list in <output>."

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        cleaned = clean_json_content(content)
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Error field translation: {e}")
        return None
