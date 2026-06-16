from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
import os
import json

# Tạo Router riêng cho B6 để code gọn gàng
router = APIRouter(tags=["B6 Access Gate & Core Integration"])

# ==========================================
# 1. Định nghĩa cấu trúc JSON nhận từ B6
# ==========================================
class LogEntry(BaseModel):
    log_type: str
    timestamp: datetime
    details: Dict[str, Any] # Dùng Dict để chứa cả ACCESS log lẫn FIRE_ALARM log

class ExportPayload(BaseModel):
    from_date: Optional[datetime] = Field(alias="from", default=None)
    to_date: Optional[datetime] = Field(alias="to", default=None)
    data: List[LogEntry]

# ==========================================
# 2. Hàm hỗ trợ kết nối TimescaleDB
# ==========================================
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "analytics_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            port=5432
        )
        return conn
    except Exception as e:
        print(f"Lỗi kết nối DB: {e}")
        return None

# ==========================================
# 3. API Endpoint hứng data
# ==========================================
@router.post("/analytics/export", status_code=201)
async def receive_b6_export(payload: ExportPayload):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối Database nội bộ")
    
    try:
        cursor = conn.cursor()
        # Dùng executemany để insert hàng loạt siêu nhanh
        insert_query = """
            INSERT INTO campus_logs (time, log_type, details)
            VALUES (%s, %s, %s)
        """
        
        # Chuyển đổi dữ liệu Pydantic thành Tuple để nhét vào DB
        records_to_insert = [
            (entry.timestamp, entry.log_type, json.dumps(entry.details))
            for entry in payload.data
        ]
        
        cursor.executemany(insert_query, records_to_insert)
        conn.commit()
        cursor.close()
        
        return {
            "status": "success", 
            "message": f"Đã nhận và lưu thành công {len(records_to_insert)} bản ghi từ B6"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi lưu vào DB: {str(e)}")
    finally:
        if conn:
            conn.close()