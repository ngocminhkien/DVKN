# Multi-stage build cho ứng dụng FastAPI
FROM python:3.11-slim as builder

WORKDIR /app

# Cài đặt các thư viện cần thiết để biên dịch psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Cài đặt các gói Python
RUN pip install --user fastapi uvicorn psycopg2-binary

# Stage runtime
FROM python:3.11-slim

WORKDIR /app

ENV SERVICE_NAME=analytics-service
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

# Copy các gói đã cài đặt từ builder
COPY --from=builder /root/.local /root/.local

# Đảm bảo các script trong .local có thể chạy được
ENV PATH=/root/.local/bin:$PATH

# Copy mã nguồn
COPY src /app/src

# Healthcheck một dòng theo yêu cầu
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" || exit 1

# Khởi chạy ứng dụng
CMD ["sh", "-c", "uvicorn analytics_app.main:app --app-dir src --host ${APP_HOST} --port ${APP_PORT}"]
