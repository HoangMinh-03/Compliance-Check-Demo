# Compliance Checker Demo - Technical Documentation (v1.5)

Dự án này là một hệ thống kiểm tra tuân thủ (Compliance Checking) sử dụng LLM để dịch các quy tắc ngôn ngữ tự nhiên thành kế hoạch thực thi (Execution Plan) dưới dạng JSON, sau đó chạy các hàm kiểm tra Python tương ứng.

## 1. Cấu trúc thư mục (Modular Architecture)

```text
src/
├── api/             # Giao diện lập trình ứng dụng
│   └── routes.py    # Định nghĩa endpoint /check (nhận rules và data từ frontend)
├── core/            # Nhân cốt lõi của hệ thống
│   ├── helpers.py   # Thư viện các hàm xác thực (Validation Helpers) & Registry
│   └── orchestrator.py # Bộ thực thi logic (Execution Engine)
├── services/        # Tích hợp dịch vụ bên ngoài
│   └── llm_service.py # Giao tiếp với LLM (Ollama/vLLM) để dịch quy tắc
├── utils/           # Tiện ích bổ sung
│   └── parser.py    # (Legacy) Đọc dữ liệu từ file .md
└── main.py          # Entry point chính, khởi chạy FastAPI server
```

## 2. Hệ thống Helper Registry (`src/core/helpers.py`)

Sử dụng Decorator Pattern để quản lý các hàm xác thực:
- `@registry.register(description="...")`: Đăng ký một hàm xác thực thông thường.
- `@registry.register(is_pure=True, description="...")`: Đăng ký một hàm logic/biến đổi (không tự động nhận giá trị trường hiện tại làm đối số đầu tiên).

**Các nhóm hàm chính:**
- **Xác thực cơ bản:** `check_not_empty`, `check_numeric`, `check_alphabetical`, `check_length`, `check_regex`.
- **Định dạng đặc biệt:** `check_email`, `check_visa`, `check_mastercard`, `check_swift_bic`, `check_currency_format`.
- **Logic & Thời gian:** `calculate_age`, `extract_year`, `check_logic_equal/greater/smaller`.
- **Điều kiện (If-Then):** `check_if(condition, helper_result)`.

## 3. Bộ thực thi Orchestrator (`src/core/orchestrator.py`)

Orchestrator có khả năng xử lý thông minh các kế hoạch thực thi từ LLM:
- **Auto-injection (Chèn đối số tự động):** Nếu LLM gọi một hàm mà thiếu tham số (ví dụ: `check_range(0, 100)` thay vì `check_range(value, 0, 100)`), Orchestrator sẽ tự động dùng `inspect` để chèn giá trị của trường hiện tại vào vị trí đầu tiên.
- **Nested Functions (Hàm lồng nhau):** Hỗ trợ các lời gọi hàm phức tạp như `check_logic_equal(calculate_age(extract_year(Ngày sinh, '%d-%m-%Y')))`.
- **Flexible JSON:** Xử lý được cả hai định dạng JSON mà LLM hay trả về (Dict hoặc List các Object).
- **Percentage Handling:** Tự động chuyển đổi chuỗi có dấu `%` (ví dụ: "20%") thành giá trị float (0.2) để so sánh logic chính xác.

## 4. Dịch vụ LLM (`src/services/llm_service.py`)

Prompt đã được tối ưu hóa cho các mô hình nhỏ và tiếng Việt:
- **Strict Context:** Chỉ tạo quy tắc cho các trường được nhắc đến trực tiếp.
- **No Python Syntax:** Cấm tuyệt đối LLM sử dụng cú pháp `if/else` hoặc index `[0]`.
- **If-Then Logic:** Yêu cầu LLM sử dụng hàm `check_if` để xử lý các quy tắc điều kiện.
- **Metadata-driven:** Danh sách helpers gửi cho LLM được sinh ra tự động từ Registry để đảm bảo độ chính xác của tham số.

## 5. Hướng dẫn vận hành

### Khởi chạy API Server:
```bash
python src/main.py
```
API sẽ lắng nghe tại cổng `8000`. Endpoint chính: `POST /check`.

### Chạy Tests:
Hệ thống sử dụng `pytest` để bao phủ toàn bộ logic:
```bash
pytest
```
Các file test quan trọng:
- `tests/test_helpers.py`: Kiểm tra từng hàm xác thực.
- `tests/test_orchestrator.py`: Kiểm tra logic thực thi và chèn đối số.
- `tests/test_compliance_levels.py`: Kiểm tra 10 cấp độ khó của quy tắc tuân thủ.

## 6. Lưu ý cho Session Gemini tiếp theo
- Khi thêm helper mới, luôn sử dụng `@registry.register` kèm theo `description`.
- Nếu Orchestrator gặp lỗi `TypeError` về số lượng đối số, hãy kiểm tra lại logic `inspect` trong `orchestrator.py`.
- Dữ liệu Frontend gửi lên phải là một JSON Object chứa `content` (rules văn bản) và `data` (dict các trường dữ liệu).
