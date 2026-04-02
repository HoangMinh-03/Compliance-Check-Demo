# Compliance Checker Demo - Technical Documentation (v2.6.0)

Hệ thống kiểm tra tuân thủ (Compliance Checking) tiên tiến sử dụng LLM để dịch quy tắc ngôn ngữ tự nhiên thành kế hoạch thực thi (Execution Plan) có cấu trúc, hỗ trợ phê duyệt trực quan và thực thi logic phức tạp.

## 1. Cấu trúc thư mục (Detailed Architecture)

```text
D:\katalyst\compliance_checker_demo\
├── Dockerfile           # Đóng gói Backend Python 3.13-slim
├── docker-compose.yml   # Cấu hình container, volumes và environment
├── Luật.txt             # File chứa các quy tắc demo
├── VanbanA.txt          # File chứa dữ liệu văn bản demo
├── main_app/            # Frontend SPA (TailwindCSS + Vanilla JS)
│   ├── index.html       # Giao diện chính
│   ├── index_script.js  # Logic UI & Auto-Seeding Demo
│   └── style.css        # Styling
├── src/
│   ├── main.py          # Entry point FastAPI
│   ├── api/routes.py    # Các API endpoints chính
│   ├── core/
│   │   ├── helpers.py      # Thư viện hàm kiểm tra (Registry)
│   │   └── orchestrator.py # Engine thực thi & Smart Injection
│   └── services/llm_service.py # Gateway LLM
└── storage/             # Lưu trữ kế hoạch (Persistent Volume)
```

## 2. Các cơ chế xử lý cốt lõi (Core Mechanisms)

### 2.1. Dịch quy tắc 2 bước (Two-step Rule Translation)
Quá trình dịch được chia làm 2 giai đoạn LLM:
1.  **Extraction:** Trích xuất logic kiểm tra chính.
2.  **Dependency Completion:** Tự động tìm và thêm các biến phụ thuộc (ví dụ: "Ngày sinh" phục vụ `calculate_age`).

### 2.2. Orchestrator Engine 2.0 (Smart Injection & Resolution)
- **Refined Smart Injection:** Cơ chế tiêm dữ liệu thông minh dựa trên chữ ký hàm:
    - **Validation Helpers:** Tự động chèn giá trị trường (`value`) nếu người dùng truyền thiếu tham số (kể cả tham số có mặc định). Ví dụ: `check_date_format('%d-%m-%Y')` -> `check_date_format(value, '%d-%m-%Y')`.
    - **Pure/Logic Helpers:** Chỉ chèn `value` nếu thiếu tham số **bắt buộc**. Giúp tránh lỗi khi gọi các hàm so sánh như `check_date_before(Ngày ký, Ngày hết hạn)`.
- **Recursive Resolution:** Xử lý các lời gọi hàm lồng nhau vô hạn (VD: `calculate_age(extract_year(Ngày sinh))`).
- **Robust Argument Splitting:** Xử lý chính xác các biểu thức phức tạp có chứa dấu phẩy bên trong chuỗi hoặc hàm con bằng cách theo dõi độ sâu ngoặc và dấu nháy.

### 2.3. Giao diện & Auto-Seeding (Demo Ready)
- **Auto-Seeding:** Hệ thống tự động nạp nội dung từ `Luật.txt` và `VanbanA.txt` vào giao diện khi tải trang, cho phép chạy thử ngay lập tức.
- **Granular Testing:** Cho phép "Chạy thử" từng khối quy tắc riêng lẻ trong bước phê duyệt.
- **Single-Field Regeneration:** Tạo lại logic cho duy nhất một trường nếu LLM dịch chưa chính xác.

## 3. Triển khai & Vận hành (Deployment)

### 3.1. Chạy với Docker (Backend)
Hệ thống hỗ trợ chạy trong Container mạng nội bộ công ty:
```bash
docker compose up --build -d
```
- **Hot-reload:** Code máy thật được mount vào container, sửa code là nhận ngay.
- **Persistence:** Thư mục `storage/` được gắn vào máy thật để lưu trữ dữ liệu vĩnh viễn.

### 3.2. Biến môi trường
Cần file `.env` chứa:
- `OPENAI_API_KEY`: Key API của công ty.
- `PORT`: Cổng chạy ứng dụng (mặc định 8000).

## 4. Thư viện Hàm Helper (Registry)

- **Validation:** `check_numeric`, `check_range`, `check_email`, `check_date_format`, `check_date_before`, `check_date_after`, `check_cccd_vn`, v.v.
- **Logic/Pure:** `check_if`, `calculate_age`, `extract_year`, `date_diff`, `is_empty`, `check_logic_equal`.
- **Math:** `add`, `subtract`, `multiply`, `divide`.

## 5. Ghi chú Bảo mật & Nội bộ
- Hệ thống được thiết kế chạy trong **Network nội bộ công ty**.
- File `.env` chứa API Key nhạy cảm nên được bảo vệ, không đẩy lên repo công khai.
- Toàn bộ dữ liệu demo nằm tại thư mục gốc (`Luật.txt`, `VanbanA.txt`).
