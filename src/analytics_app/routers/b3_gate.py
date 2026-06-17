from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import psycopg2
import os

router = APIRouter(tags=["B3 Access Gate Integration"])

# 1. Pydantic Model hứng đúng chuẩn hợp đồng B3
class B3AccessEvent(BaseModel):
    event_id: str
    gate_id: str
    direction: str
    access_granted: bool
    person_type: Optional[str] = None
    timestamp: datetime
    source_service: str = "access-gate-b3"
    product: str = "product-b"

# 2. Hàm kết nối Database
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "analytics_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            port=5432
        )
    except Exception as e:
        print(f"Lỗi DB B3: {e}")
        return None

# 3. Endpoint hứng dữ liệu
@router.post("/api/v1/ingest/access", status_code=202) # Trả về 202 Accepted như hợp đồng yêu cầu
async def receive_b3_access_event(event: B3AccessEvent, response: Response):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB hệ thống")
    
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO gate_events 
            (time, event_id, gate_id, direction, access_granted, person_type, source_service, product)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            event.timestamp, event.event_id, event.gate_id, event.direction,
            event.access_granted, event.person_type, event.source_service, event.product
        ))
        conn.commit()
        cursor.close()
        
        # Trả về JSON đúng yêu cầu hợp đồng B3
        return {
            "received": True,
            "event_id": event.event_id
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi lưu data B3: {str(e)}")
    finally:
        if conn:
            conn.close()