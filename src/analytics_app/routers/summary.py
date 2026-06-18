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

def get_interval_sql(range_str: str) -> str:
    if range_str == "today":
        return "1 day"
    elif range_str == "30days":
        return "30 days"
    else:  # mặc định 7days
        return "7 days"

@router.get("/analytics/summary/stats")
def get_dashboard_stats(range: str = "7days"):
    """Lấy thống kê số lượng bản ghi cho dashboard"""
    interval = get_interval_sql(range)
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    try:
        cursor = conn.cursor()
        
        # B1 count
        cursor.execute(f"SELECT COUNT(*) FROM sensor_events WHERE time >= NOW() - INTERVAL '{interval}';")
        b1_count = cursor.fetchone()[0]
        
        # B3 count
        cursor.execute(f"SELECT COUNT(*) FROM gate_events WHERE time >= NOW() - INTERVAL '{interval}';")
        b3_count = cursor.fetchone()[0]
        
        # B6 count
        cursor.execute(f"SELECT COUNT(*) FROM campus_logs WHERE time >= NOW() - INTERVAL '{interval}';")
        b6_count = cursor.fetchone()[0]
        
        # Cảnh báo cháy
        cursor.execute(f"SELECT COUNT(*) FROM campus_logs WHERE log_type = 'FIRE_ALARM' AND time >= NOW() - INTERVAL '{interval}';")
        fire_count = cursor.fetchone()[0]
        
        cursor.close()
        return {
            "b1_sensor_events": b1_count,
            "b3_gate_access": b3_count,
            "b6_batch_export": b6_count,
            "fire_alarms": fire_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/analytics/summary/temperature-history")
def get_temperature_history(range: str = "7days"):
    """Lấy lịch sử nhiệt độ vẽ biểu đồ line chart"""
    interval = get_interval_sql(range)
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    try:
        cursor = conn.cursor()
        query = f"""
            SELECT time, temperature_c 
            FROM sensor_events 
            WHERE temperature_c IS NOT NULL AND time >= NOW() - INTERVAL '{interval}'
            ORDER BY time DESC 
            LIMIT 15;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        
        # Sắp xếp tăng dần theo thời gian
        rows.reverse()
        
        labels = [row[0].strftime("%H:%M:%S" if range == "today" else "%d/%m %H:%M") for row in rows]
        data = [round(row[1], 1) for row in rows]
        return {
            "labels": labels,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/analytics/summary/distribution")
def get_log_distribution(range: str = "7days"):
    """Lấy tỷ lệ phân bố log vẽ biểu đồ tròn"""
    interval = get_interval_sql(range)
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    try:
        cursor = conn.cursor()
        
        # B1 count
        cursor.execute(f"SELECT COUNT(*) FROM sensor_events WHERE time >= NOW() - INTERVAL '{interval}';")
        b1_count = cursor.fetchone()[0]
        
        # B3 count
        cursor.execute(f"SELECT COUNT(*) FROM gate_events WHERE time >= NOW() - INTERVAL '{interval}';")
        b3_count = cursor.fetchone()[0]
        
        # B6 count (loại trừ fire alarm)
        cursor.execute(f"SELECT COUNT(*) FROM campus_logs WHERE log_type != 'FIRE_ALARM' AND time >= NOW() - INTERVAL '{interval}';")
        b6_count = cursor.fetchone()[0]
        
        # Fire count
        cursor.execute(f"SELECT COUNT(*) FROM campus_logs WHERE log_type = 'FIRE_ALARM' AND time >= NOW() - INTERVAL '{interval}';")
        fire_count = cursor.fetchone()[0]
        
        cursor.close()
        return {
            "labels": ['Cảm biến IoT (B1)', 'Quẹt thẻ cổng (B3)', 'Nhật ký xuất (B6)', 'Cảnh báo cháy'],
            "data": [b1_count, b3_count, b6_count, fire_count]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/analytics/summary/recent-logs")
def get_recent_logs():
    """Lấy các log sự kiện gần nhất cho terminal stream"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Lỗi kết nối DB")
    try:
        cursor = conn.cursor()
        
        # Lấy 10 bản ghi từ campus_logs
        cursor.execute("SELECT time, log_type, details FROM campus_logs ORDER BY time DESC LIMIT 10;")
        campus_logs_rows = cursor.fetchall()
        
        # Lấy 10 bản ghi từ gate_events
        cursor.execute("SELECT time, gate_id, direction, access_granted, person_type FROM gate_events ORDER BY time DESC LIMIT 10;")
        gate_events_rows = cursor.fetchall()
        
        # Lấy 10 bản ghi từ sensor_events
        cursor.execute("SELECT time, device_id, temperature_c, co2_ppm, status FROM sensor_events ORDER BY time DESC LIMIT 10;")
        sensor_events_rows = cursor.fetchall()
        
        cursor.close()
        
        logs = []
        for row in campus_logs_rows:
            t, log_type, details = row
            import json
            # details có thể là dict hoặc string json
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except:
                    pass
            logs.append({
                "time": t.isoformat(),
                "source": "B6",
                "type": log_type,
                "message": f"Log nhận từ B6. Chi tiết: {details}"
            })
        for row in gate_events_rows:
            t, gate_id, direction, access_granted, person_type = row
            status_str = "HỢP LỆ" if access_granted else "KHÔNG HỢP LỆ"
            logs.append({
                "time": t.isoformat(),
                "source": "B3",
                "type": "GATE_ACCESS",
                "message": f"Quẹt thẻ tại cổng '{gate_id}' (${direction}) | Đối tượng: {person_type or 'N/A'} | Kết quả: {status_str}"
            })
        for row in sensor_events_rows:
            t, device_id, temp, co2, status = row
            logs.append({
                "time": t.isoformat(),
                "source": "B1",
                "type": "SENSOR_EVENT",
                "message": f"Thiết bị '{device_id}' | Nhiệt độ: {temp or 0.0}°C | CO2: {co2 or 0.0}ppm | Trạng thái: {status}"
            })
        
        # Sắp xếp theo thời gian giảm dần
        logs.sort(key=lambda x: x["time"], reverse=True)
        return logs[:15]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()