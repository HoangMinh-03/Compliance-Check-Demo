import asyncio
import os
import json
import logging
import sys
from src.services.llm_service import translate_rules, generate_plan_metadata

# Đảm bảo in được tiếng Việt trên Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Cấu hình logging
logging.basicConfig(level=logging.INFO)

async def test_full_flow():
    rules_text = """
    Trường 'khách hàng' có giá trị 'Ưu tiên' khi:
    (Số dư tài khoản > 1000000000 VÀ Tổng chi tiêu tháng > 100000000) 
    HOẶC (date_diff(Ngày tham gia, get_current_date(), 'years') > 10).
    """
    
    print("\n--- [PHASE 1 & 2] Translate Rules & Dependency Completion ---")
    plan = await translate_rules(rules_text)
    print(json.dumps(plan, indent=4, ensure_ascii=False))
    
    print("\n--- [PHASE 3] Generate Metadata ---")
    metadata = await generate_plan_metadata(plan)
    print(json.dumps(metadata, indent=4, ensure_ascii=False))
    
    if metadata:
        print("\n✅ Thành công: Metadata đã được tạo.")
        for field, meta in metadata.items():
            print(f"Field: {field}")
            print(f"  - Desc: {meta.get('description')}")
            print(f"  - Sample: {meta.get('sample_value')}")
    else:
        print("\n❌ Thất bại: Metadata KHÔNG được tạo.")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
