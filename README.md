# Compliance Checker Demo (v2.6.2)

Hệ thống kiểm tra tuân thủ (Compliance Checking) tiên tiến sử dụng Trí tuệ nhân tạo (LLM Agent) để dịch các quy tắc ngôn ngữ tự nhiên thành kế hoạch thực thi logic, hỗ trợ phê duyệt trực quan và đối soát dữ liệu tự động.

---

## 🚀 Tính năng Chính

- **Dịch quy tắc thông minh**: Chuyển đổi luật/quy định từ văn bản thô sang bộ hàm logic (Execution Plan) sử dụng `smolagents`.
- **Tự động bổ sung phụ thuộc**: Agent tự phát hiện các trường dữ liệu cần thiết cho tính toán nhưng chưa được định nghĩa trong luật.
- **Ánh xạ dữ liệu tự động**: Tự động khớp tên trường trong văn bản upload với các quy tắc trong Metadata.
- **Giao diện trực quan**: Cho phép người dùng duyệt, chỉnh sửa và tạo lại logic cho từng trường dữ liệu trước khi thực thi.
- **Thư viện Helper mạnh mẽ**: Hỗ trợ hơn 40 hàm kiểm tra từ cơ bản (số, ngày tháng, email) đến phức tạp (tính tuổi, tính khoảng cách ngày, logic điều kiện).

---

## 🛠 Yêu cầu Hệ thống

- **Python**: 3.12+ (Khuyến nghị 3.13)
- **Cơ sở hạ tầng**: Docker & Docker Compose (Nếu chạy bằng container)
- **API Key**: Cần có API Key của LLM (OpenAI hoặc OpenRouter)

---

## 📦 Hướng dẫn Cài đặt

### 1. Cài đặt trực tiếp (Local)
1. Clone repository về máy.
2. Tạo môi trường ảo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Cài đặt thư viện:
   ```bash
   pip install -r requirements.txt
   ```
4. Cấu hình biến môi trường:
   Tạo file `.env` tại thư mục gốc với nội dung:
   ```env
   LLM_API_BASE=your_api_base_url
   LLM_API_KEY=your_api_key
   LLM_MODEL=your_model_name
   ```

### 2. Chạy bằng Docker
Hệ thống đã sẵn sàng với cấu hình Docker:
```bash
docker-compose up --build -d
```
Hệ thống sẽ chạy tại địa chỉ: `http://localhost:8000`

---

## 📖 Hướng dẫn Sử dụng

1.  **Nhập quy tắc (Step 1)**: Nhập nội dung luật vào ô văn bản hoặc sử dụng nội dung mẫu từ `Luật.txt`. Nhấn "Dịch quy tắc" để Agent tạo ra bản nháp logic.
2.  **Phê duyệt logic (Step 2)**: Kiểm tra các khối logic Agent vừa dịch. Bạn có thể nhấn "Tạo lại" cho từng trường nếu AI dịch chưa chính xác hoặc nhấn "Chạy thử" để kiểm tra với dữ liệu mẫu.
3.  **Tải lên văn bản (Step 3)**: Tải lên tệp văn bản cần đối soát (hỗ trợ .txt, .docx, .pdf). AI sẽ tự động trích xuất text.
4.  **Thực thi kiểm tra (Final Step)**: Nhấn "Kiểm tra tuân thủ". Hệ thống sẽ thực hiện ánh xạ dữ liệu và trả về kết quả đạt/không đạt kèm lý do chi tiết cho từng quy tắc.

---

## 🧪 Chạy Kiểm thử (Testing)

Dự án sử dụng `pytest` và các script kiểm thử agent:
```bash
# Chạy bộ test cho orchestrator
pytest tests/test_orchestrator.py

# Kiểm tra khả năng tự động tìm phụ thuộc của Agent
python -m tests.test_dependency_agent
```

---

## 📂 Cơ cấu Thư mục Chính

- `src/core/`: Chứa registry hàm helper và engine thực thi (Orchestrator).
- `src/services/`: Chứa logic Agent xử lý LLM.
- `src/api/`: Các API endpoints (FastAPI).
- `main_app/`: Frontend Single Page Application (HTML/JS/CSS).
- `storage/`: Lưu trữ các kế hoạch thực thi đã được phê duyệt.

---
*Ghi chú: Hệ thống được thiết kế để kết nối giữa con người và AI, nơi con người đóng vai trò phê duyệt cuối cùng (Human-in-the-loop).*
