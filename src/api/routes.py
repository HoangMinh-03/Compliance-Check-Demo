import logging
import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from src.services.llm_service import translate_rules, extract_data_from_text
from src.core.orchestrator import run_compliance_check
from src.utils.file_processor import extract_text_from_file, save_execution_plan, load_execution_plan, list_saved_plans

logger = logging.getLogger(__name__)

router = APIRouter()

class ComplianceRequest(BaseModel):
    content: str  # Rules từ frontend
    data: Dict[str, str]  # Dữ liệu từ frontend

class GeneratePlanRequest(BaseModel):
    rules: str
    available_fields: List[str]

class ExecutePlanRequest(BaseModel):
    data: Dict[str, str]
    execution_plan: Dict[str, Any]

class SavePlanRequest(BaseModel):
    name: str
    plan: Dict[str, Any]

class ExtractDataRequest(BaseModel):
    text: str
    fields: List[str]

@router.post("/check")
async def check_compliance(req: ComplianceRequest):
    """(Legacy) Thực hiện cả 2 bước: dịch và kiểm tra."""
    try:
        available_fields = list(req.data.keys())
        execution_plan = await translate_rules(req.content, available_fields=available_fields)
        if not execution_plan:
            return {"success": False, "error": "Không thể dịch quy tắc."}
        is_all_valid, results = run_compliance_check(req.data, execution_plan)
        return {"success": True, "is_valid": is_all_valid, "execution_plan": execution_plan, "results": results}
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
    """Chỉ gọi LLM để lấy Execution Plan."""
    try:
        plan = await translate_rules(req.rules, available_fields=req.available_fields)
        if not plan:
            return {"success": False, "error": "Không thể tạo kế hoạch thực thi từ LLM."}
        return {"success": True, "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_plan(req: ExecutePlanRequest):
    """Thực thi kiểm tra tuân thủ dựa trên Execution Plan đã có."""
    try:
        is_all_valid, results = run_compliance_check(req.data, req.execution_plan)
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
