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

async def translate_rules(rules_text: str) -> Optional[Dict[str, List[Any]]]:
    """
    Sử dụng LLM để dịch rules văn bản sang Execution Plan (JSON).
    Tên trường (keys) được trích xuất trực tiếp từ văn bản quy tắc.
    """
    helpers_list = registry.get_llm_metadata()

    system_prompt = (
        "Bạn là một Chuyên gia Logic học và Kỹ sư Kiểm thử Dữ liệu.\n"
        "Nhiệm vụ: Phân tích quy tắc văn bản và chuyển đổi thành Execution Plan (JSON).\n"
        "\n"
        "QUY TẮC:\n"
        "1. Tên trường (keys trong JSON) phải lấy TRỰC TIẾP từ <rules_text>.\n"
        "2. TUYỆT ĐỐI KHÔNG sử dụng cú pháp Python (if, else, ...).\n"
        "3. CHỈ sử dụng các hàm helper được cung cấp.\n"
        "4. Logic điều kiện dùng: 'check_if(condition, helper_result)'.\n"
        "\n"
        "Yêu cầu: Output JSON trong thẻ <output>.\n"
        "Cấu trúc: {\"tên_trường_từ_luật\": [\"function_name(args)\", ...]}"
    )

    user_prompt = f"""
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

async def extract_data_from_text(text: str, fields: List[str]) -> Optional[Dict[str, str]]:
    """
    Nhiệm vụ: Chỉ trích xuất giá trị cho các trường dữ liệu từ văn bản thô.
    Không chứa logic kiểm tra hay lập kế hoạch.
    """
    system_prompt = (
        "Bạn là một Chuyên gia Trích xuất Dữ liệu Văn bản.\n"
        "Nhiệm vụ: Đọc văn bản thô và tìm giá trị tương ứng cho danh sách các trường được yêu cầu.\n"
        "QUY TẮC:\n"
        "1. Trả về JSON object: {\"tên_trường\": \"giá_trị\"}.\n"
        "2. Nếu không tìm thấy thông tin cho một trường, hãy để giá trị là \"\".\n"
        "3. Giữ nguyên định dạng gốc của dữ liệu (ví dụ: ngày tháng, số tiền).\n"
        "4. CHỈ trả về JSON trong thẻ <output>."
    )
    
    user_prompt = f"""
<fields_to_find>
{', '.join(fields)}
</fields_to_find>

<document_text>
{text}
</document_text>

Trích xuất dữ liệu và trả về JSON trong thẻ <output>:"""

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
        cleaned = clean_json_content(content)
        if not cleaned: return None
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Lỗi trích xuất dữ liệu: {e}")
        return None

async def translate_rule_for_field(rule_text: str, field_name: str, selected_helpers: List[str]) -> Optional[List[Dict[str, Any]]]:
    """Dịch lẻ từng field (giữ lại để hỗ trợ Update v1.5 tương lai)"""
    return None

async def map_data_to_plan(required_fields: List[str], data_keys: List[str]) -> Optional[Dict[str, str]]:
    """
    Nhiệm vụ: Ánh xạ danh sách 'trường yêu cầu' (từ luật) sang 'trường dữ liệu thực tế' (từ file).
    Trả về JSON object: {"trường_yêu_cầu": "trường_thực_tế"}.
    """
    system_prompt = (
        "Bạn là một Chuyên gia Ánh xạ Dữ liệu.\n"
        "Nhiệm vụ: Ánh xạ danh sách 'trường yêu cầu' (từ luật) sang 'trường dữ liệu thực tế' (từ file).\n"
        "QUY TẮC:\n"
        "1. Trả về JSON object: {\"trường_yêu_cầu\": \"trường_thực_tế\"}.\n"
        "2. Nếu không tìm thấy trường tương ứng rõ ràng, hãy để giá trị là \"\".\n"
        "3. CHỈ trả về JSON trong thẻ <output>."
    )
    
    user_prompt = f"""
<required_fields>
{', '.join(required_fields)}
</required_fields>

<available_data_keys>
{', '.join(data_keys)}
</available_data_keys>

Hãy thực hiện ánh xạ và trả về JSON trong thẻ <output>:"""

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
        cleaned = clean_json_content(content)
        if not cleaned: return None
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Lỗi ánh xạ dữ liệu: {e}")
        return None

async def generate_calculation_logic(target_field: str, data_keys: List[str], instruction: str) -> Optional[str]:
    """
    Sử dụng LLM để tạo ra một lời gọi hàm helper nhằm tính toán giá trị cho một trường.
    Ví dụ: "Tính tuổi từ năm_sinh" -> "calculate_age(năm_sinh)"
    """
    helpers_list = registry.get_llm_metadata()
    
    system_prompt = (
        "Bạn là một Chuyên gia Logic Dữ liệu.\n"
        "Nhiệm vụ: Tạo MỘT lời gọi hàm helper duy nhất để tính toán giá trị cho trường yêu cầu.\n"
        "QUY TẮC:\n"
        "1. CHỈ sử dụng các hàm helper được cung cấp.\n"
        "2. Sử dụng tên trường từ danh sách <available_data_keys>.\n"
        "3. Output CHỈ là chuỗi lời gọi hàm, không giải thích.\n"
        "Ví dụ: calculate_age(extract_year(ngay_sinh))\n"
        "Nếu không thể tạo logic, trả về 'ERROR'."
    )
    
    user_prompt = f"""
Trường mục tiêu: {target_field}
Dữ liệu có sẵn: {', '.join(data_keys)}
Yêu cầu của người dùng: {instruction}

Helper functions:
{helpers_list}

Logic tính toán:"""

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Lỗi tạo logic tính toán: {e}")
        return None
