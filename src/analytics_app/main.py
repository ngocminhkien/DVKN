import os
import psycopg2
from fastapi import FastAPI

# Import file router của B6
from analytics_app.routers import b6_gate 

app = FastAPI(title="Analytics Service (B5) - Smart Campus")

# Nhúng router B6 vào ứng dụng chính
app.include_router(b6_gate.router)

@app.get("/health")
def health_check():
    status = {"status": "healthy", "service": "analytics-service"}
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "analytics_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            connect_timeout=3
        )
        status["database"] = "connected"
        conn.close()
    except Exception as e:
        status["database"] = f"error: {str(e)}"
    
    return status