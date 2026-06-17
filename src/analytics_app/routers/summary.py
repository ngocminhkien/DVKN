from fastapi import APIRouter, HTTPException
import psycopg2
import os

router = APIRouter(tags=["Dashboard Analytics"])

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

@router.get("/analytics/summary/fire-alarms")
def get_fire_alarms_summary():
    """Đếm tổng số sự kiện báo cháy đã xảy ra"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    
    try:
        cursor = conn.cursor()
        # Đếm số lượng log FIRE_ALARM
        cursor.execute("SELECT COUNT(*) FROM campus_logs WHERE log_type = 'FIRE_ALARM';")
        count = cursor.fetchone()[0]
        cursor.close()
        
        return {
            "metric": "Tổng số vụ báo cháy",
            "total_alarms": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/analytics/summary/temperature")
def get_temperature_summary():
    """Lấy nhiệt độ trung bình của từng thiết bị IoT (từ dữ liệu B1)"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    
    try:
        cursor = conn.cursor()
        # Tính nhiệt độ trung bình theo từng device_id
        query = """
            SELECT device_id, AVG(temperature_c) as avg_temp 
            FROM sensor_events 
            WHERE temperature_c IS NOT NULL 
            GROUP BY device_id;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        
        result = [{"device_id": row[0], "average_temperature": round(row[1], 2)} for row in rows]
        
        return {
            "metric": "Nhiệt độ trung bình theo khu vực",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()