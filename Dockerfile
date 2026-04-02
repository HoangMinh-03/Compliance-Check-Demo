# Sử dụng Python 3.13 slim làm base image
FROM python:3.13-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Thiết lập biến môi trường để Python không tạo file .pyc và log output ngay lập tức
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt các thư viện hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements.txt và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Lưu ý: Trong môi trường Dev, chúng ta sẽ mount code thông qua docker-compose 
# nên không cần COPY code vào đây để tận dụng hot-reload.
# Tuy nhiên, vẫn COPY để đảm bảo Docker có thể chạy độc lập nếu cần.
COPY . .

# Expose cổng 8000 cho FastAPI
EXPOSE 8000

# Lệnh khởi chạy ứng dụng với chế độ auto-reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
