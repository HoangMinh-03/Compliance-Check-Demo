# Compliance Checker Demo - Technical Documentation (v2.0)

Dự án này là một hệ thống kiểm tra tuân thủ (Compliance Checking) sử dụng LLM để dịch các quy tắc ngôn ngữ tự nhiên thành kế hoạch thực thi (Execution Plan) dưới dạng JSON, sau đó cho phép người dùng phê duyệt/chỉnh sửa trước khi chạy các hàm kiểm tra Python tương ứng.

## 1. Cấu trúc thư mục (Modular Architecture)

```text
src/
├── api/             # Giao diện lập trình ứng dụng (FastAPI)
│   └── routes.py    # Định nghĩa các endpoint: /check, /upload, /generate-plan, /execute, /plans, /extract-data
├── core/            # Nhân cốt lõi của hệ thống
│   ├── helpers.py   # Thư viện các hàm xác thực (Validation Helpers) & Registry
│   └── orchestrator.py # Bộ thực thi logic (Execution Engine)
├── services/        # Tích hợp dịch vụ bên ngoài
│   └── llm_service.py # Giao tiếp với LLM (Ollama/vLLM) để dịch quy tắc và trích xuất dữ liệu
├── utils/           # Tiện ích bổ sung
│   ├── file_processor.py # Xử lý trích xuất text (docx, md, txt) và quản lý file JSON plans
│   └── parser.py    # (Legacy) Đọc dữ liệu từ file .md
└── main.py          # Entry point chính, khởi chạy FastAPI server

storage/
└── plans/           # Thư mục lưu trữ các Kế hoạch thực thi (Execution Plans) đã lưu

main_app/            # Giao diện người dùng (Frontend)
├── index.html       # Single Page Application sử dụng TailwindCSS
└── style.css        # Tùy chỉnh giao diện dark mode và hiệu ứng
```

## 2. Quy trình Thực thi 2 bước (Two-step Workflow)

Thay vì thực hiện "Black-box compliance", v2.0 tách biệt quá trình:
1.  **Dịch quy tắc (Translation):** LLM nhận `rules` và `available_fields` để tạo ra một Kế hoạch thực thi JSON.
2.  **Phê duyệt (Approval):** Người dùng xem xét JSON, có thể chỉnh sửa trực tiếp trên giao diện để đảm bảo tính chính xác của logic.
3.  **Thực thi (Execution):** Orchestrator chạy kế hoạch đã được phê duyệt trên dữ liệu thực tế.

## 3. Các tính năng đã hoàn thiện (v2.0 Final)

### Quản lý Trường dữ liệu linh hoạt (Dynamic Data Management)
- **Tự động sinh trường:** Tự động tạo các trường dữ liệu khi upload file JSON hoặc trích xuất từ văn bản thô (Smart Extraction).
- **Thêm/Xóa thủ công:** Người dùng có thể thêm các trường mới hoặc xóa các trường không cần thiết trực tiếp trên giao diện.
- **Tùy chỉnh Key-Value:** Cho phép chỉnh sửa cả tên trường và giá trị trước khi thực hiện kiểm tra.

### Trích xuất dữ liệu thông minh (Smart Extraction)
Hệ thống nhận văn bản thô (hợp đồng, văn bản quy phạm) và tự động điền giá trị vào các trường dữ liệu mục tiêu bằng LLM.

### Quản lý file (File Handling)
- **Hỗ trợ định dạng:** Trích xuất text từ `.txt`, `.md`, và `.docx`.
- **Lưu trữ Kế hoạch:** Cho phép lưu các Execution Plan đã tinh chỉnh xuống `storage/plans/` để tái sử dụng.

## 4. Hệ thống Helper Registry (`src/core/helpers.py`)

Sử dụng Decorator Pattern để quản lý các hàm xác thực:
- `@registry.register(description="...")`: Đăng ký một hàm xác thực thông thường.
- `@registry.register(is_pure=True, description="...")`: Đăng ký một hàm logic/biến đổi.

## 5. Hướng dẫn vận hành

### Khởi chạy API Server:
```bash
python src/main.py
```
API lắng nghe tại cổng `8000`. Truy cập `main_app/index.html` để sử dụng UI.

### Chạy Tests:
```bash
pytest
```

## 6. Lộ trình phát triển v2.5 (Roadmap)
- **Hỗ trợ .PDF:** Tích hợp thư viện xử lý file PDF để trích xuất nội dung.
- **Batch Processing:** Kiểm tra tuân thủ cho nhiều file dữ liệu cùng lúc dựa trên 1 Kế hoạch mẫu.
- **Export Results:** Xuất kết quả kiểm tra ra file Excel/PDF kèm theo minh chứng (evidence).
- **Cải thiện Editor:** Thêm Syntax Highlighting cho trình chỉnh sửa JSON Plan.

## 7. Lưu ý cho Session Gemini tiếp theo
- Khi thêm helper mới, luôn cập nhật registry kèm description.
- Giao diện hiện tại đã hỗ trợ thêm/xóa trường, cần lưu ý logic index khi thao tác hàng loạt.
