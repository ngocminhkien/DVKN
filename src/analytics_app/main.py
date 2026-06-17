import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from analytics_app.routers import b6_gate 
from analytics_app.routers import summary
from analytics_app.routers import b3_gate

app = FastAPI(title="Analytics Service (B5) - Smart Campus")

# Nhúng các router vào ứng dụng chính
app.include_router(b6_gate.router)
app.include_router(summary.router)
app.include_router(b3_gate.router)

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

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    # Lấy đường dẫn thư mục hiện tại của file main.py
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "dashboard.html")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()