import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from src.services.llm_service import translate_rules
from src.core.orchestrator import run_compliance_check

logger = logging.getLogger(__name__)

router = APIRouter()

class ComplianceRequest(BaseModel):
    content: str  # Rules từ frontend
    data: Dict[str, str]  # Dữ liệu từ frontend

@router.post("/check")
async def check_compliance(req: ComplianceRequest):
    try:
        logger.info(f"Received request. Rules length: {len(req.content)}")
        
        # 1. Translate rules using LLM
        available_fields = list(req.data.keys())
        execution_plan = await translate_rules(req.content, available_fields=available_fields)
        
        if not execution_plan:
            return {
                "success": False,
                "error": "Không thể dịch quy tắc. Vui lòng kiểm tra lại văn bản quy tắc.",
                "details": []
            }

        logger.info(f"Execution Plan: {execution_plan}")

        # 2. Run compliance check
        is_all_valid, results = run_compliance_check(req.data, execution_plan)

        return {
            "success": True,
            "is_valid": is_all_valid,
            "execution_plan": execution_plan,
            "results": results
        }

    except Exception as e:
        logger.exception("Error in check_compliance route")
        raise HTTPException(status_code=500, detail=str(e))
