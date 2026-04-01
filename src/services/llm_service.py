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
    Sử dụng LLM 2 bước để dịch rules văn bản sang Execution Plan (JSON).
    Bước 1: Trích xuất logic kiểm tra chính.
    Bước 2: Bổ sung các trường phụ thuộc (variables) bị thiếu.
    """
    helpers_list = registry.get_llm_metadata()

    # --- BƯỚC 1: TRÍCH XUẤT LOGIC CHÍNH ---
    step1_system_prompt = (
        "Bạn là một Chuyên gia Logic học.\n"
        "Nhiệm vụ: Phân tích quy tắc văn bản và chuyển đổi thành Execution Plan (JSON).\n"
        "\n"
        "=== QUY TẮC QUAN TRỌNG ===\n"
        "1. Tên trường (keys) phải lấy TRỰC TIẾP từ văn bản quy tắc.\n"
        "2. TUYỆT ĐỐI KHÔNG sử dụng cú pháp Python (if, else, and, or, not).\n"
        "3. TUYỆT ĐỐI KHÔNG dùng toán tử so sánh (<, >, ==, !=, <=, >=). Thay vào đó, hãy sử dụng các hàm helper tương ứng như check_logic_greater, check_logic_equal, check_logic_smaller.\n"
        "4. CHỈ sử dụng các hàm helper được cung cấp trong danh sách.\n"
        "5. Cấu trúc JSON: {\"tên_trường\": [\"helper_1\", \"helper_2(args)\", ...]}\n"
        "\n"
        "=== HƯỚNG DẪN LOGIC ===\n"
        "- Hàm Validation (vd: check_numeric, check_range): Hệ thống tự động truyền giá trị của trường hiện tại vào tham số đầu tiên.\n"
        "- Hàm Logic/Pure (vd: calculate_age, check_logic_greater, is_empty): Không tự động nhận giá trị trường. Bạn phải truyền tham số rõ ràng.\n"
        "- Điều kiện (check_if): Dùng 'check_if(điều_kiện, kết_quả_nếu_đúng)'. \n"
        "  Ví dụ: \"check_if(is_empty(Chữ ký), check_not_empty)\"\n"
        "  Ví dụ khoảng cách ngày: \"check_date_min_distance(Ngày ký, 12, 'months')\"\n"
        "\n"
        "Yêu cầu: Output JSON trong thẻ <output>."
    )

    user_prompt = f"""  
        <helper_functions>
        {helpers_list}
        </helper_functions>

        <rules_text>
        {rules_text}
        </rules_text>

        Yêu cầu:
        Dựa trên rules_text, hãy tạo Execution Plan.

        Lưu ý quan trọng:
        - So sánh trường A với một số: check_logic_greater(Trường A, 100)
        - So sánh trường A với trường B: check_logic_greater(Trường A, Trường B)
        - Kiểm tra có điều kiện: check_if(is_empty(Trường A), check_not_empty)

        Ví dụ:
        Rules:
        1. Tuổi phải từ 18 đến 60.
        2. Nếu Số tiền lớn hơn 500 triệu thì phải có Người phê duyệt.
        3. Ngày kết thúc phải sau Ngày bắt đầu.

        JSON:
        {{
            "Tuổi": ["check_numeric", "check_range(18, 60)"],
            "Người phê duyệt": ["check_if(check_logic_greater(Số tiền, 500000000), check_not_empty)"],
            "Ngày kết thúc": ["check_date_after(Ngày kết thúc, Ngày bắt đầu)"],
        }}

        KJSON (trong thẻ <output>):"""


    try:
        response1 = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": step1_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        content1 = clean_json_content(response1.choices[0].message.content.strip())
        if not content1: return None
        initial_plan = json.loads(initial_plan_str := content1)
        logger.info(f"Step 1 - Initial Plan: {initial_plan_str}")
    except Exception as e:
        logger.error(f"Lỗi Bước 1 (Translate): {e}")
        return None

    # --- BƯỚC 2: BƯỚC BỔ SUNG BIẾN PHỤ THUỘC (DEPENDENCIES) ---
    step2_system_prompt = (
        "Bạn là một Kỹ sư Kiểm thử Dữ liệu.\n"
        "Nhiệm vụ: Rà soát Execution Plan và bổ sung các trường dữ liệu bị thiếu.\n"
        "\n"
        "QUY TẮC:\n"
        "1. Duyệt qua TẤT CẢ các hàm trong Plan hiện tại. Nếu một Tên Trường xuất hiện như một tham số bên trong một hàm (ví dụ: 'Ngày sinh' trong calculate_age(Ngày sinh), hoặc 'Chữ ký' trong is_empty(Chữ ký)) nhưng Tên Trường đó chưa có trong danh sách Keys của JSON bạn PHẢI, kiểm tra lại một lần nữa xem nó có chắc chắn không nằm trong các trường đã được quy định không, nếu không thêm nó vào làm Key mới với list rỗng [] (Tên trường phải được giữ nguyên vẹn y như trong hàm).\n"
        "2. Đảm bảo mọi biến số cần thiết cho logic đều được liệt kê làm key để hệ thống thực hiện ánh xạ.\n"
        "3. KHÔNG thay đổi logic của các trường đã có.\n"
        "4. Trả về Execution Plan hoàn thiện dưới dạng JSON trong thẻ <output>."
    )

    try:
        response2 = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": step2_system_prompt},
                {"role": "user", "content": f"Original Rules:\n{rules_text}\n\nInitial Plan:\n{json.dumps(initial_plan, ensure_ascii=False, indent=2)}\n\nHoàn thiện Plan và trả về JSON trong thẻ <output>:"}
            ],
            temperature=0.0
        )
        content2 = clean_json_content(response2.choices[0].message.content.strip())
        if not content2: return initial_plan
        final_plan = json.loads(content2)
        logger.info(f"Step 2 - Final Plan: {json.dumps(final_plan, ensure_ascii=False)}")
        return final_plan
    except Exception as e:
        logger.error(f"Lỗi Bước 2 (Completion): {e}")
        return initial_plan

async def translate_single_field_logic(field_name: str, full_rules_text: str) -> Optional[List[str]]:
    """
    Sử dụng LLM để chỉ dịch/tạo lại logic cho MỘT trường cụ thể dựa trên toàn bộ văn bản luật.
    """
    helpers_list = registry.get_llm_metadata()
    
    system_prompt = (
        "Bạn là một Chuyên gia Logic học và Kỹ sư Kiểm thử Dữ liệu.\n"
        f"Nhiệm vụ: Phân tích quy tắc văn bản và chỉ trích xuất các hàm kiểm tra cho trường '{field_name}'.\n"
        "\n"
        "=== QUY TẮC QUAN TRỌNG ===\n"
        "1. CHỈ trả về danh sách các hàm helper (JSON array) cho trường được yêu cầu.\n"
        "2. TUYỆT ĐỐI KHÔNG sử dụng cú pháp Python (if, else, and, or, not).\n"
        "3. TUYỆT ĐỐI KHÔNG dùng toán tử so sánh (<, >, ==, !=, <=, >=). Thay vào đó, hãy sử dụng các hàm helper tương ứng như check_logic_greater, check_logic_equal, check_logic_smaller.\n"
        "4. CHỈ sử dụng các hàm helper được cung cấp trong danh sách.\n"
        "\n"
        "=== HƯỚNG DẪN LOGIC ===\n"
        "- Hàm Validation (vd: check_numeric, check_range): Hệ thống tự động truyền giá trị của trường hiện tại vào tham số đầu tiên. Bạn chỉ cần điền các tham số còn lại.\n"
        "- Hàm Logic/Pure (vd: calculate_age, check_logic_greater, is_empty): Không tự động nhận giá trị trường. Bạn phải truyền tham số rõ ràng.\n"
        "- Điều kiện (check_if): Dùng 'check_if(điều_kiện, kết_quả_nếu_đúng)'. \n"
        "  Ví dụ: \"check_if(is_empty(Chữ ký), check_not_empty)\"\n"
        "  Ví dụ khoảng cách ngày: \"check_date_min_distance(Ngày ký, 12, 'months')\"\n"
        "\n"
        "Yêu cầu: Output JSON ARRAY trong thẻ <output>."
    )
    
    user_prompt = f"""
<helper_functions>
{helpers_list}
</helper_functions>

<full_rules_text>
{full_rules_text}
</full_rules_text>

Trường cần tạo logic: {field_name}

Yêu cầu:
Dựa trên full_rules_text, hãy trích xuất và tạo các hàm kiểm tra cho trường '{field_name}'.
Lưu ý: Nếu quy tắc của trường này phụ thuộc vào giá trị của một trường khác, hãy sử dụng Tên Trường đó làm tham số trong hàm logic.

Ví dụ:
Rules: "Nếu Tuổi dưới 18 thì phải có Người giám hộ"
Field: "Người giám hộ"
Output: ["check_if(check_logic_smaller(Tuổi, 18), check_not_empty)"]

Hãy trả về danh sách hàm (JSON array) trong thẻ <output>:"""

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        content = clean_json_content(response.choices[0].message.content.strip())
        if not content: return None
        return json.loads(content)
    except Exception as e:
        logger.error(f"Lỗi regenerate logic cho trường {field_name}: {e}")
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
        "2. Nếu không tìm thấy trường tương ứng trực tiếp, bạn có thể sử dụng các hàm toán học để tính toán giá trị.\n"
        "3. CÁC HÀM TOÁN HỌC HỖ TRỢ: add(a, b), subtract(a, b), multiply(a, b), divide(a, b).\n"
        "   Ví dụ: \"Lãi suất\": \"divide(Tiền lời, Tiền gửi)\"\n"
        "4. Nếu không tìm thấy trường tương ứng rõ ràng và không thể tính toán, hãy để giá trị là \"\".\n"
        "5. CHỈ trả về JSON trong thẻ <output>."
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

async def generate_plan_metadata(execution_plan: Dict[str, List[Any]]) -> Optional[Dict[str, Dict[str, str]]]:
    """
    Sử dụng LLM để tạo description và sample data cho từng trường trong Execution Plan.
    Trả về JSON: {"tên_trường": {"description": "...", "sample_value": "..."}}
    """
    helpers_list = registry.get_llm_metadata()
    
    system_prompt = (
        "Bạn là một Chuyên gia Kỹ thuật và Kiểm thử Dữ liệu.\n"
        "Nhiệm vụ: Dựa trên Execution Plan (JSON), hãy tạo mô tả (description) bằng tiếng Việt và một giá trị mẫu (sample_value) hợp lệ cho từng trường.\n"
        "QUY TẮC:\n"
        "1. Description: Giải thích ngắn gọn các quy tắc đang được áp dụng cho trường đó (ví dụ: 'Kiểm tra tuổi phải trên 18 và là số'). Nếu trường đó không có quy tắc nào ([]), hãy giải thích rằng đây là trường dữ liệu đầu vào cần thiết cho các logic kiểm tra khác.\n"
        "2. Sample Value: Phải là một giá trị (string) THỎA MÃN tất cả các hàm helper trong list của trường đó (nếu có).\n"
        "3. Trả về JSON object trong thẻ <output>.\n"
        "Cấu trúc: {\"tên_trường\": {\"description\": \"...\", \"sample_value\": \"...\"}}"
    )

    user_prompt = f"""
<helper_metadata>
{helpers_list}
</helper_metadata>

<execution_plan>
{json.dumps(execution_plan, ensure_ascii=False, indent=2)}
</execution_plan>

Hãy tạo metadata và trả về JSON trong thẻ <output>:"""

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
        logger.error(f"Lỗi tạo metadata cho plan: {e}")
        return None
