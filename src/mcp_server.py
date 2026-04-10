import os
import sys
import io
import json
import logging
import asyncio
import contextlib
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# --- CẤU HÌNH LOGGING ---
# Ép toàn bộ log hệ thống ra stderr để không làm hỏng luồng JSON-RPC của MCP
logging.basicConfig(
    level=logging.ERROR,
    stream=sys.stderr,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_server")

# Load môi trường
load_dotenv(override=True)

# Khởi tạo FastMCP
# Lưu ý: FastMCP sẽ tự động quản lý stdio khi chạy mcp.run()
mcp = FastMCP(
    "ComplianceEngine",
    dependencies=["smolagents", "openai", "python-dotenv"]
)

# Import các thành phần lõi
from src.core.helpers import registry
from src.services.llm_service import (
    translate_rules, 
    extract_data_from_text, 
    translate_single_field_logic, 
    map_data_to_plan
)
from src.core.orchestrator import run_compliance_check

# ==========================================
# 1. Đăng ký các hàm Helper từ Registry
# ==========================================

def create_mcp_tool(name: str, func: callable, description: str):
    """Tạo một wrapper cho hàm helper để tương thích với MCP tool."""
    async def tool_wrapper(*args, **kwargs):
        # Chuyển hướng stdout nội bộ để tránh log rác từ thư viện bẻ lái luồng dữ liệu
        with contextlib.redirect_stdout(sys.stderr):
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
    
    tool_wrapper.__doc__ = description
    return mcp.tool(name=f"helper_{name}")(tool_wrapper)

# Đăng ký tự động toàn bộ helper
for name, func in registry.helpers.items():
    desc = registry.metadata.get(name, "Hàm hỗ trợ kiểm tra tuân thủ.")
    create_mcp_tool(name, func, desc)

# ==========================================
# 2. Đăng ký các Công cụ Dịch vụ (High-level Tools)
# ==========================================

@mcp.tool()
async def translate_compliance_rules(rules_text: str) -> Dict[str, Any]:
    """
    Dịch các quy định nghiệp vụ bằng ngôn ngữ tự nhiên thành một Kế hoạch thực thi (Execution Plan).
    """
    with contextlib.redirect_stdout(sys.stderr):
        print(f"--- Đang phân tích quy tắc: {len(rules_text)} ký tự ---", file=sys.stderr)
        plan = await translate_rules(rules_text)
        return {"execution_plan": plan} if plan else {"error": "Không thể dịch quy tắc."}

@mcp.tool()
async def translate_field_logic(field_name: str, rules_text: str) -> Dict[str, Any]:
    """
    Dịch lại logic cho duy nhất một trường dữ liệu dựa trên văn bản quy tắc.
    Hữu ích khi chỉ cần cập nhật một phần nhỏ của kế hoạch.
    """
    with contextlib.redirect_stdout(sys.stderr):
        logic = await translate_single_field_logic(field_name, rules_text)
        return {"field_name": field_name, "logic": logic} if logic else {"error": f"Không thể dịch logic cho trường {field_name}."}

@mcp.tool()
async def extract_data(text: str, fields: List[str]) -> Dict[str, str]:
    """
    Trích xuất các giá trị dữ liệu thô từ một đoạn văn bản (Van ban).
    """
    with contextlib.redirect_stdout(sys.stderr):
        data = await extract_data_from_text(text, fields)
        return data if data else {"error": "Không thể trích xuất dữ liệu."}

@mcp.tool()
async def map_data(required_fields: List[str], extracted_keys: List[str]) -> Dict[str, str]:
    """
    Thực hiện ánh xạ (Mapping) giữa các trường yêu cầu trong luật và các trường thực tế trích xuất được.
    Ví dụ: Khớp 'Số dư' (luật) với 'Account Balance' (văn bản).
    """
    with contextlib.redirect_stdout(sys.stderr):
        mapping = await map_data_to_plan(required_fields, extracted_keys)
        return mapping if mapping else {"error": "Không thể tạo ánh xạ dữ liệu."}

@mcp.tool()
async def execute_check(data: Dict[str, str], execution_plan: Dict[str, Any], mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Thực thi kiểm tra tuân thủ đối với một bộ dữ liệu.
    """
    with contextlib.redirect_stdout(sys.stderr):
        is_valid, results = run_compliance_check(data, execution_plan, mapping=mapping)
        return {
            "is_valid": is_valid,
            "results": results
        }

# --- Cung cấp Resources ---
@mcp.resource("rules://default")
def get_default_rules() -> str:
    """Nội dung các quy tắc kiểm tra tuân thủ mặc định (Luật.txt)."""
    try:
        with open("Luật.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading rules: {e}"

@mcp.resource("document://sample")
def get_sample_document() -> str:
    """Nội dung văn bản mẫu cần đối soát (VanbanA.txt)."""
    try:
        with open("VanbanA.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading document: {e}"

if __name__ == "__main__":
    # RẤT QUAN TRỌNG: Không can thiệp vào sys.stdout trước khi gọi mcp.run()
    # để tránh lỗi "ValueError: I/O operation on closed file"
    mcp.run()
