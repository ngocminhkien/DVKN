from fastapi import FastAPI, HTTPException
import psycopg2
import os

app = FastAPI(title="Analytics Service")

@app.get("/health")
def health_check():
    # Lấy thông tin kết nối từ biến môi trường
    host = os.environ.get("DB_HOST", "db")
    database = os.environ.get("POSTGRES_DB", "analytics_db")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    port = os.environ.get("DB_PORT", "5432")

    try:
        # Cố gắng kết nối tới cơ sở dữ liệu TimescaleDB
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        # Xử lý lỗi nếu kết nối thất bại
        print(f"Lỗi kết nối CSDL: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
