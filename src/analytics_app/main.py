import os
import psycopg2
from fastapi import FastAPI


from analytics_app.routers import b6_gate 
from analytics_app.routers import summary # Thêm dòng này

app = FastAPI(title="Analytics Service (B5) - Smart Campus")

# Nhúng các router vào ứng dụng chính
app.include_router(b6_gate.router)
app.include_router(summary.router) # Thêm dòng này

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