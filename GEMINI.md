# Compliance Checker Demo - Technical Documentation (v2.5.2)

Hệ thống kiểm tra tuân thủ (Compliance Checking) tiên tiến sử dụng LLM để dịch quy tắc ngôn ngữ tự nhiên thành kế hoạch thực thi (Execution Plan) có cấu trúc, hỗ trợ phê duyệt trực quan và thực thi logic phức tạp.

## 1. Cấu trúc thư mục (Detailed Architecture)

```text
src/
├── api/
│   └── routes.py    # Endpoint chính:
│                    # - /generate-plan: Dịch luật 2 bước (Extraction & Dependency)
│                    # - /generate-plan-metadata: Gen description & sample data
│                    # - /regenerate-field-logic: Tạo lại logic cho duy nhất 1 trường
│                    # - /execute: Thực thi toàn bộ hoặc một phần kế hoạch
├── core/
│   ├── helpers.py   # Registry quản lý 3 loại hàm: Validation, Logic/Pure, Math
│   └── orchestrator.py # Engine cốt lõi: xử lý đệ quy, inject giá trị, resolve biến
├── services/
│   └── llm_service.py # Gateway LLM với các prompt được tối ưu hóa cho logic học
├── utils/
│   └── file_processor.py # Trích xuất text đa định dạng (docx, md, txt)
└── main.py          # Entry point FastAPI

main_app/            # Frontend SPA (TailwindCSS + Vanilla JS)
├── index.html       # Layout khối (Block-based UI) cho Approval Modal
├── index_script.js  # Quản lý state, rendering động và chạy thử (granular testing)
└── style.css        # Hiệu ứng UI/UX
```

## 2. Các cơ chế xử lý cốt lõi (Core Mechanisms)

### 2.1. Dịch quy tắc 2 bước (Two-step Rule Translation)
Để giảm thiểu sai sót và bỏ lỡ biến, quá trình dịch được chia làm 2 giai đoạn LLM:
1.  **Extraction:** Trích xuất logic kiểm tra chính cho các trường xuất hiện trực tiếp trong luật.
2.  **Dependency Completion:** Rà soát lại toàn bộ Plan để tìm các biến phụ thuộc (ví dụ: "Ngày sinh" trong `calculate_age(Ngày sinh)`) và tự động thêm chúng vào danh sách mapping với rule rỗng `[]`.

### 2.2. Orchestrator Engine (Smart Execution)
- **Recursive Resolution:** Hàm `resolve_arg` có khả năng giải quyết các lời gọi hàm lồng nhau vô hạn (ví dụ: `calculate_age(extract_year(Ngày sinh, '%d-%m-%Y'))`).
- **Smart Injection:** Tự động chèn giá trị hiện tại của trường (`value`) vào tham số đầu tiên của hàm nếu số lượng đối số cung cấp ít hơn số lượng tham số **bắt buộc** của hàm đó (kiểm tra qua `inspect.signature`).
- **Robust Argument Splitting:** Hàm `split_args` sử dụng cơ chế theo dõi độ sâu ngoặc (parenthesis depth) và trạng thái nháy (quote state) để xử lý chính xác các biểu thức phức tạp có chứa dấu phẩy bên trong chuỗi hoặc hàm con.
- **Fuzzy Matching:** Tự động chuẩn hóa tên trường (lowercase, strip whitespace) để khớp dữ liệu giữa "Không gian Luật" và "Không gian Dữ liệu thực tế".

### 2.3. Giao diện Phê duyệt Khối (Block-based UI)
- **Granular Rendering:** Mỗi trường trong kế hoạch được hiển thị thành một khối độc lập với đầy đủ: Tên trường, Danh sách hàm, Mô tả tiếng Việt, và Input dữ liệu mẫu.
- **Granular Testing:** Khi nhấn "Chạy thử", hệ thống thu thập dữ liệu mẫu từ **tất cả** các khối khác để gửi lên server, đảm bảo các logic liên trường (cross-field) vẫn hoạt động chính xác ngay trong bước phê duyệt.
- **Single-Field Regeneration:** Cho phép gọi LLM để tạo lại logic cho duy nhất một trường nếu kết quả ban đầu không chính xác, giúp giữ nguyên các chỉnh sửa thủ công ở các trường khác.

## 3. Thư viện Hàm Helper (Registry)

Hàm được phân loại rõ ràng trong `helpers.py`:
- **Validation (Trả về `Tuple[bool, str]`):** `check_numeric`, `check_range`, `check_email`, `check_not_empty`, `check_date_min_distance`, v.v.
- **Logic/Pure (Trả về giá trị hoặc `bool`):**
    - `check_if(cond, result)`: Thực thi `result` chỉ khi `cond` đúng.
    - `is_empty(val)`, `check_logic_not(val)`.
    - `calculate_age(birth)`, `extract_year(date, format)`.
- **Math (Hỗ trợ tính toán trong Mapping):** `add`, `subtract`, `multiply`, `divide`.

## 4. Hướng dẫn vận hành & Kiểm thử

### Khởi chạy:
```bash
python src/main.py
```

### Chạy kiểm thử:
```bash
# Thiết lập PYTHONPATH để nhận diện module src
$env:PYTHONPATH="."
pytest tests/test_nested_logic_v2.py
pytest tests/test_v252_nested_crossfield.py
```

## 5. Ghi chú cho phát triển tiếp theo
- **Dependency Fields:** Các trường phụ thuộc (không có luật riêng) được styled màu xanh dương nhạt trong UI và gán rule `[]` để đảm bảo được trích xuất và ánh xạ đầy đủ.
- **Smart Injection Nuance:** Cần lưu ý rằng Smart Injection chỉ kích hoạt khi thiếu tham số **bắt buộc**. Nếu hàm có tham số optional (có giá trị mặc định), hệ thống sẽ không tự chèn thêm trừ khi được yêu cầu rõ ràng trong logic.
- **Prompt Synchronization:** Khi cập nhật logic dịch thuật, hãy cập nhật cả `translate_rules` (prompt 2 bước) và `translate_single_field_logic` (prompt đơn lẻ) để đảm bảo tính nhất quán.
- **Robustness:** Luôn ưu tiên dùng `is_empty(Field)` thay vì `check_not_empty(Field)` khi viết điều kiện bên trong `check_if` để đảm bảo giá trị trả về là boolean thuần túy.
