import os
import json
import logging
import asyncio
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from smolagents import Tool, CodeAgent, ToolCallingAgent, OpenAIServerModel
from src.core.helpers import registry

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_API_BASE = os.getenv("LLM_API_BASE")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

model = OpenAIServerModel(model_id=LLM_MODEL, api_base=LLM_API_BASE, api_key=LLM_API_KEY)

# ==========================================
# AGENT V2 CORE TOOLS
# ==========================================

class PlanBuilderTool(Tool):
    """Công cụ để đăng ký danh sách các hàm kiểm tra cho một trường dữ liệu (field)."""
    name = "add_rule_plan"
    description = "Đăng ký danh sách các hàm kiểm tra cho một trường dữ liệu (field)."
    inputs = {
        "field_name": {"type": "string", "description": "Tên trường dữ liệu (chính xác từ văn bản)."},
        "helpers": {"type": "array", "items": {"type": "string"}, "description": "Danh sách các chuỗi gọi hàm helper."}
    }
    output_type = "string"
    def __init__(self, accumulated_plan: Dict[str, List[str]]):
        self.accumulated_plan = accumulated_plan
        super().__init__()
    def forward(self, field_name: str, helpers: List[str]) -> str:
        # Tự động sửa lỗi nếu LLM gọi nhầm tên (như add_rule_plan)
        self.accumulated_plan[field_name] = helpers
        return f"Đã thêm quy tắc cho trường '{field_name}'."

class ExtractionTool(Tool):
    """Công cụ để trích xuất dữ liệu hàng loạt."""
    name = "record_extracted_dict"
    description = "Ghi lại TOÀN BỘ các trường tìm được dưới dạng 1 dictionary {tên_trường: giá_trị}."
    inputs = {
        "data_dict": {"type": "object", "description": "Dictionary chứa các cặp {tên: giá_trị}."}
    }
    output_type = "string"
    def __init__(self, storage: Dict[str, str]):
        self.storage = storage
        super().__init__()
    def forward(self, data_dict: dict) -> str:
        self.storage.update(data_dict)
        return f"Đã ghi nhận {len(data_dict)} trường dữ liệu."

class MappingTool(Tool):
    """Công cụ để ánh xạ dữ liệu hàng loạt."""
    name = "record_mapping_dict"
    description = "Ghi lại TOÀN BỘ các ánh xạ dưới dạng 1 dictionary {tên_rules: tên_thực_tế}."
    inputs = {
        "mapping_dict": {"type": "object", "description": "Dictionary ánh xạ logic."}
    }
    output_type = "string"
    def __init__(self, mapping: Dict[str, str]):
        self.mapping = mapping
        super().__init__()
    def forward(self, mapping_dict: dict) -> str:
        self.mapping.update(mapping_dict)
        return f"Đã ghi lại {len(mapping_dict)} ánh xạ."

class MetadataTool(Tool):
    """Công cụ để tạo metadata hàng loạt."""
    name = "record_metadata_dict"
    description = "Ghi lại TOÀN BỘ metadata dưới dạng dictionary {tên: {'description': '...', 'sample_value': '...'}}."
    inputs = {
        "metadata_dict": {"type": "object", "description": "Dictionary chứa thông tin hiển thị UI."}
    }
    output_type = "string"
    def __init__(self, metadata_storage: Dict[str, Dict[str, str]]):
        self.metadata_storage = metadata_storage
        super().__init__()
    def forward(self, metadata_dict: dict) -> str:
        self.metadata_storage.update(metadata_dict)
        return f"Đã ghi lại metadata cho {len(metadata_dict)} trường."

def get_helper_definitions() -> str:
    return registry.get_llm_metadata()

SYNTAX_SPECIFICATION = """
QUY TẮC CÚ PHÁP BẮT BUỘC (STRICT GRAMMAR):
1. ĐỊNH DẠNG: Chỉ sử dụng các lời gọi hàm lồng nhau. VD: func1(func2(arg), arg2).
2. CẤM TOÁN TỬ: Tuyệt đối KHÔNG dùng '>', '<', '==', '!=', 'AND', 'OR', 'NOT', 'if', 'else'.
3. CẤM BỌC HÀM DƯ THỪA: KHÔNG bọc các giá trị trong check_numeric() hay check_not_empty() khi truyền vào các hàm check_logic_... vì các hàm này đã tự xử lý validate.
4. THỜI GIAN: Dùng date_diff('Ngày A', 'Ngày B', 'years') để tính năm/tuổi. KHÔNG tự trừ năm.
5. LOGIC MAPPING:
   - Sử dụng check_logic_greater(v1, v2) thay cho v1 > v2.
   - Sử dụng check_logic_equal(v1, v2) thay cho v1 == v2.
   - Sử dụng check_and/or cho logic kết hợp.
6. TÊN BIẾN & DẤU NHÁY:
   - Tuyệt đối KHÔNG bọc Tên Biến trong dấu nháy. VD: dùng Số nhà, KHÔNG dùng 'Số nhà'.
   - CHỈ dùng dấu nháy cho các Giá trị Hằng số hoặc Kết quả mong muốn. VD: 'VIP', '01-01-2024'.
"""

# ==========================================
# AGENT V2 IMPLEMENTATIONS
# ==========================================

async def translate_rules(rules_text: str) -> Optional[Dict[str, List[Any]]]:
    """Dịch Rules văn bản sang Execution Plan (CodeAgent - High Precision)."""
    accumulated_plan = {}
    builder_tool = PlanBuilderTool(accumulated_plan)
    # CodeAgent tự kiểm tra mã nguồn giúp tạo logic lồng nhau chuẩn xác
    agent = CodeAgent(tools=[builder_tool], model=model, verbosity_level=-1, additional_authorized_imports=[], max_steps=10)
    
    helper_metadata = get_helper_definitions()
    task = f"""Dịch RULES thành Execution Plan. 
LƯU Ý: Mỗi trường dữ liệu (Khách hàng, Lãi suất,...) PHẢI được gọi qua công cụ 'add_rule_plan' RIÊNG BIỆT.
{SYNTAX_SPECIFICATION}

HELPERS:
{helper_metadata}

RULES:
{rules_text}"""
    
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        # Bước 2: Bổ sung các biến phụ thuộc (Dependency Completion)
        if accumulated_plan:
            await complete_plan_dependencies(accumulated_plan)
        return accumulated_plan if accumulated_plan else None
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (translate_rules): {e}")
        return None

async def complete_plan_dependencies(execution_plan: Dict[str, List[Any]]) -> Dict[str, List[Any]]:
    """Giai đoạn 2: Tự động tìm và thêm các biến phụ thuộc ẩn trong công thức."""
    builder_tool = PlanBuilderTool(execution_plan)
    agent = CodeAgent(tools=[builder_tool], model=model, verbosity_level=-1, max_steps=5)
    
    helper_metadata = get_helper_definitions()
    task = f"""Duyệt qua Execution Plan hiện tại và tìm các 'biến phụ thuộc' bị thiếu.
Biến phụ thuộc là các tên trường (VD: 'Ngày tham gia', 'Lương') được truyền vào làm tham số cho các hàm nhưng CHƯA tồn tại trong danh sách các key của Plan.

LƯU Ý:
1. Nếu tìm thấy trường chưa có, hãy gọi công cụ add_rule_plan(tên_trường, []) - truyền list rỗng.
2. KHÔNG thêm các giá trị là chuỗi hằng số (trong dấu nháy), số, hoặc tên hàm helper.
3. Chỉ tập trung vào các định danh trông giống Tên Trường dữ liệu. Tuyệt đối KHÔNG bọc chúng trong dấu nháy.

PHẠM VI KIỂM TRA:
{json.dumps(execution_plan, ensure_ascii=False)}

DANH SÁCH HELPER ĐỂ LOẠI TRỪ:
{helper_metadata}"""
    
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return execution_plan
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (complete_dependencies): {e}")
        return execution_plan

async def translate_single_field_logic(field_name: str, full_rules_text: str) -> Optional[List[str]]:
    """Dịch lại logic lẻ trường (CodeAgent - Accuracy focus)."""
    accumulated_plan = {}
    builder_tool = PlanBuilderTool(accumulated_plan)
    agent = CodeAgent(tools=[builder_tool], model=model, verbosity_level=-1, additional_authorized_imports=[], max_steps=3)
    
    helper_metadata = get_helper_definitions()
    task = f"""Tạo quy tắc cho trường '{field_name}' bằng add_rule_plan.
{SYNTAX_SPECIFICATION}

HELPERS:
{helper_metadata}

RULES:
{full_rules_text}"""
    
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return accumulated_plan.get(field_name)
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (single_field): {e}")
        return None

async def extract_data_from_text(text: str, fields: List[str]) -> Optional[Dict[str, str]]:
    """Trích xuất dữ liệu (CodeAgent - High Precision)."""
    storage = {}
    tool = ExtractionTool(storage)
    agent = CodeAgent(tools=[tool], model=model, verbosity_level=-1, max_steps=10)
    task = f"Trích xuất {fields} từ văn bản bằng record_extracted_dict.\n\nVĂN BẢN:\n{text}"
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return storage
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (extract): {e}")
        return None

async def map_data_to_plan(required_fields: List[str], data_keys: List[str]) -> Optional[Dict[str, str]]:
    """Ánh xạ dữ liệu (CodeAgent - High Precision)."""
    mapping = {}
    tool = MappingTool(mapping)
    agent = CodeAgent(tools=[tool], model=model, verbosity_level=-1, max_steps=10)
    task = f"Ánh xạ {required_fields} sang các trường thực tế {data_keys} bằng record_mapping_dict."
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return mapping
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (mapping): {e}")
        return None

async def generate_plan_metadata(execution_plan: Dict[str, List[Any]]) -> Optional[Dict[str, Dict[str, str]]]:
    """Tạo metadata chi tiết bao gồm mô tả và dữ liệu mẫu (CodeAgent)."""
    storage = {}
    tool = MetadataTool(storage)
    agent = CodeAgent(tools=[tool], model=model, verbosity_level=-1, max_steps=10)
    
    helper_metadata = get_helper_definitions()
    task = f"""Tạo metadata cho Execution Plan sau đây bằng record_metadata_dict.
Đối với MỖI trường trong plan, bạn cần cung cấp:
1. 'description': Giải thích logic kiểm tra của trường đó bằng tiếng Việt một cách dễ hiểu dựa trên các hàm helper được gọi. Nếu trường đó là biến phụ thuộc (không có quy tắc), hãy ghi 'Trường dữ liệu đầu vào'.
2. 'sample_value': Một giá trị mẫu hợp lệ thỏa mãn TẤT CẢ các quy tắc của trường đó (nếu có). 
   - Nếu có check_date_format('%d-%m-%Y'), giá trị phải là '01-01-2024'.
   - Nếu có check_logic_greater(val, 100), giá trị phải lớn hơn 100.
   - Tham chiếu logic hàm từ danh sách HELPERS bên dưới.

HELPERS REFERENCE:
{helper_metadata}

PLAN:
{json.dumps(execution_plan, ensure_ascii=False)}"""
    
    try:
        await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return storage
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (metadata): {e}")
        return None

async def generate_calculation_logic(target_field: str, data_keys: List[str], instruction: str) -> Optional[str]:
    """Tạo logic tính toán sử dụng Agent (Agent-Native)."""
    agent = CodeAgent(tools=[], model=model, verbosity_level=-1)
    helper_metadata = get_helper_definitions()
    task = f"Tạo lời gọi hàm helper để tính toán trường '{target_field}'.\nHD: {instruction}\nKEYS: {data_keys}\nHELPERS:\n{helper_metadata}\nChỉ trả về chuỗi gọi hàm."
    try:
        res = await asyncio.to_thread(lambda: agent.run(task, reset=True))
        return str(res).strip() if res else None
    except Exception as e:
        logger.error(f"Lỗi CodeAgent (calculation): {e}")
        return None
