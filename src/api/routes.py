import logging
import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from src.services.llm_service import translate_rules, extract_data_from_text, map_data_to_plan
from src.core.orchestrator import run_compliance_check
from src.utils.file_processor import extract_text_from_file, save_execution_plan, load_execution_plan, list_saved_plans

logger = logging.getLogger(__name__)

router = APIRouter()

class ComplianceRequest(BaseModel):
    content: str  # Rules từ frontend
    data: Dict[str, str]  # Dữ liệu từ frontend

class GeneratePlanRequest(BaseModel):
    rules: str

class GenerateMappingRequest(BaseModel):
    required_fields: List[str]
    data_keys: List[str]

class GenerateCalculationRequest(BaseModel):
    target_field: str
    data_keys: List[str]
    instruction: str

class ExecutePlanRequest(BaseModel):
    data: Dict[str, str]
    execution_plan: Dict[str, Any]
    mapping: Optional[Dict[str, str]] = None

class SavePlanRequest(BaseModel):
    name: str
    plan: Dict[str, Any]

class ExtractDataRequest(BaseModel):
    text: str
    fields: List[str]

class GenerateMetadataRequest(BaseModel):
    execution_plan: Dict[str, List[Any]]

class RegenerateLogicRequest(BaseModel):
    field_name: str
    rules_text: str

@router.post("/check")
# ... (existing check_compliance) ...
async def check_compliance(req: ComplianceRequest):
    """(Legacy) Thực hiện cả 2 bước: dịch và kiểm tra."""
    try:
        execution_plan = await translate_rules(req.content)
        if not execution_plan:
            return {"success": False, "error": "Không thể dịch quy tắc."}
        
        # Mapping logic for legacy check
        required_fields = list(execution_plan.keys())
        data_keys = list(req.data.keys())
        mapping = await map_data_to_plan(required_fields, data_keys)
        
        is_all_valid, results = run_compliance_check(req.data, execution_plan, mapping=mapping)
        return {"success": True, "is_valid": is_all_valid, "execution_plan": execution_plan, "results": results, "mapping": mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload file và trích xuất nội dung text."""
    temp_dir = "temp_uploads"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    temp_path = os.path.join(temp_dir, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        content = extract_text_from_file(temp_path, file.filename)
        if content is None:
            return {"success": False, "error": "Không thể trích xuất text từ file này."}
        return {"success": True, "content": content}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/generate-plan")
async def generate_plan(req: GeneratePlanRequest):
    """Chỉ gọi LLM để lấy Execution Plan (Rule-First)."""
    try:
        plan = await translate_rules(req.rules)
        if not plan:
            return {"success": False, "error": "Không thể tạo kế hoạch thực thi từ LLM."}
        return {"success": True, "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-mapping")
async def generate_mapping(req: GenerateMappingRequest):
    """Gọi LLM để thực hiện ánh xạ giữa Plan Fields và Data Keys."""
    try:
        mapping = await map_data_to_plan(req.required_fields, req.data_keys)
        if mapping is None:
            return {"success": False, "error": "Không thể tạo ánh xạ dữ liệu."}
        return {"success": True, "mapping": mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-calculation")
async def generate_calculation(req: GenerateCalculationRequest):
    """Gọi LLM để tạo logic tính toán cho một trường cụ thể."""
    try:
        from src.services.llm_service import generate_calculation_logic
        logic = await generate_calculation_logic(req.target_field, req.data_keys, req.instruction)
        if logic is None or logic == "ERROR":
            return {"success": False, "error": "Không thể tạo logic tính toán."}
        return {"success": True, "logic": logic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_plan(req: ExecutePlanRequest):
    """Thực thi kiểm tra tuân thủ dựa trên Execution Plan và Mapping."""
    try:
        is_all_valid, results = run_compliance_check(req.data, req.execution_plan, mapping=req.mapping)
        return {"success": True, "is_valid": is_all_valid, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def get_plans():
    """Lấy danh sách các kế hoạch đã lưu."""
    return {"success": True, "plans": list_saved_plans()}

@router.post("/plans/save")
async def save_plan(req: SavePlanRequest):
    """Lưu kế hoạch thực thi xuống file JSON."""
    try:
        save_execution_plan(req.name, req.plan)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans/{name}")
async def load_plan_api(name: str):
    """Tải một kế hoạch thực thi cụ thể."""
    plan = load_execution_plan(name)
    if plan is None:
        return {"success": False, "error": "Không tìm thấy kế hoạch này."}
    return {"success": True, "plan": plan}

@router.post("/extract-data")
async def extract_data_api(req: ExtractDataRequest):
    """Trích xuất dữ liệu từ văn bản thô dựa trên danh sách trường."""
    try:
        data = await extract_data_from_text(req.text, req.fields)
        if data is None:
            return {"success": False, "error": "Không thể trích xuất dữ liệu từ văn bản."}
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.post("/generate-plan-metadata")
async def generate_plan_metadata_api(req: GenerateMetadataRequest):
    """Tạo description và sample data cho từng trường trong plan."""
    try:
        from src.services.llm_service import generate_plan_metadata
        metadata = await generate_plan_metadata(req.execution_plan)
        if metadata is None:
            return {"success": False, "error": "Không thể tạo metadata cho kế hoạch."}
        return {"success": True, "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/regenerate-field-logic")
async def regenerate_field_logic_api(req: RegenerateLogicRequest):
    """Tạo lại logic cho một trường cụ thể."""
    try:
        from src.services.llm_service import translate_single_field_logic
        new_rules = await translate_single_field_logic(req.field_name, req.rules_text)
        if new_rules is None:
            return {"success": False, "error": "Không thể tạo lại logic cho trường này."}
        return {"success": True, "rules": new_rules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

