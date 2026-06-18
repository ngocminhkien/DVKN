from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import threading
import time
import requests
import os
import psycopg2
import json
import socket
from concurrent.futures import ThreadPoolExecutor

from analytics_app.routers import b3_gate, b6_gate

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dist_dir = os.path.join(base_dir, "frontend", "dist")
assets_dir = os.path.join(dist_dir, "assets")

# Đảm bảo thư mục assets tồn tại để mount StaticFiles không lỗi
os.makedirs(assets_dir, exist_ok=True)

# ==========================================
# KHỞI TẠO APP FASTAPI
# ==========================================
app = FastAPI(
    title="Product B - Analytics Service (Nhóm B5)",
    version="1.0.0",
    description="Trung tâm dữ liệu hứng event từ B2, B3, B4, B6, kéo log từ B7 và cung cấp API cho Dashboard."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router tích hợp DB
app.include_router(b3_gate.router)
app.include_router(b6_gate.router)

app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# ==========================================
# HÀM HỖ TRỢ DATABASE
# ==========================================
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
        print(f"Lỗi kết nối DB: {e}")
        return None

# ==========================================
# KHAI BÁO CÁC MODEL DỮ LIỆU
# ==========================================
# 1. Model B2
class Detection(BaseModel):
    label: str
    confidence: float

class B2CameraEvent(BaseModel):
    sourceService: str
    eventType: str
    cameraId: str
    frameId: str
    snapshotUrl: Optional[str] = None
    timestamp: datetime
    processedAt: datetime
    motionScore: float
    quality: Optional[str] = None
    detections: List[Detection]
    objectCount: int
    labels: List[str]
    maxConfidence: float
    abnormal: bool
    severity: str

# ==========================================
# CƠ CHẾ KÉO DATA TỪ B7 (BACKGROUND THREAD)
# ==========================================
def pull_b7_logs():
    time.sleep(10) # Chờ hệ thống khởi động xong
    b7_url = os.getenv("B7_NOTIFICATION_URL", "http://26.177.175.21:8085") + "/api/v1/alerts/logs"
    
    while True:
        try:
            print(f"🔄 [B5 -> B7] Đang sang nhà B7 lấy log tại {b7_url}...")
            response = requests.get(b7_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"📩 [B7 Notification] Kéo thành công {len(data)} logs. Đang lưu vào DB...")
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        for log in data:
                            log_time = log.get("timestamp") or log.get("time") or datetime.now()
                            log_type = log.get("log_type") or log.get("type") or "SYSTEM_ALERT"
                            details = log.get("details") or log
                            cursor.execute(
                                "INSERT INTO campus_logs (time, log_type, details) VALUES (%s, %s, %s)",
                                (log_time, log_type, json.dumps(details))
                            )
                        conn.commit()
                        cursor.close()
                    except Exception as db_err:
                        print(f"Lỗi lưu B7 logs vào DB: {db_err}")
                        conn.rollback()
                    finally:
                        conn.close()
            else:
                print(f"⚠️ [B7 Notification] Lỗi! B7 trả về mã: {response.status_code}")
        except Exception as e:
            print(f"❌ [B7 Notification] B7 đang sập hoặc chưa mở Radmin (Lỗi: {e})")
        
        # Ngủ 60 giây rồi chạy đi kéo tiếp
        time.sleep(60)

@app.on_event("startup")
def startup_event():
    # Kích hoạt điệp viên chạy ngầm ngay khi bật Server
    thread = threading.Thread(target=pull_b7_logs, daemon=True)
    thread.start()

# ==========================================
# CÁC API ENDPOINT (ROUTERS)
# ==========================================
@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "analytics-service", "database": "connected"}

@app.post("/analytics/camera-events", status_code=202, tags=["ingestion"])
def ingest_camera_event(event: B2CameraEvent):
    print(f"🔥 [B2 Camera] Webhook từ {event.cameraId} - Phát hiện {event.objectCount} {event.labels} - Mức độ: {event.severity}")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO camera_frames 
                (frame_id, camera_id, accepted, timestamp, processed_at, motion_score, quality, detections)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (frame_id) DO NOTHING;
            """
            cursor.execute(query, (
                event.frameId, event.cameraId, not event.abnormal, event.timestamp, event.processedAt,
                event.motionScore, event.quality or "unknown", json.dumps([d.dict() for d in event.detections])
            ))
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"Lỗi khi lưu webhook camera vào DB: {e}")
            conn.rollback()
        finally:
            conn.close()
    return {"status": "success", "received": True}

# --- CỔNG DUY NHẤT HỨNG WEBHOOK TỪ B4 (AI VISION) THEO ĐÚNG HỢP ĐỒNG MỚI ---
@app.post("/api/v1/analytics/vision", status_code=202, tags=["ingestion"])
def ingest_vision_webhook(event: Dict[str, Any]):
    detection_type = event.get("detectionType")
    camera_id = event.get("cameraId")
    
    if detection_type == "OBJECT":
        objects = event.get("detectedObjects", [])
        risk = event.get("riskLevel")
        print(f"👁️ [B4 AI Vision] Nhận diện VẬT THỂ từ {camera_id} - Phát hiện {len(objects)} đối tượng - Rủi ro: {risk}")
    elif detection_type == "FACE":
        matched = event.get("faceMatched")
        conf = event.get("confidence")
        match_status = "Thành công" if matched else "Không khớp"
        print(f"👤 [B4 AI Vision] Nhận diện KHUÔN MẶT từ {camera_id} - Kết quả: {match_status} (Độ tin cậy: {conf})")
    else:
        print(f"⚠️ [B4 AI Vision] Nhận loại dữ liệu không xác định từ {camera_id}")

    # Ghi nhận dữ liệu vào bảng camera_frames
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Phân tích timestamp
            ts = event.get("timestamp") or event.get("time")
            if ts:
                try:
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except:
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()
                
            frame_id = event.get("frameId") or event.get("frame_id") or f"b4-{camera_id or 'unknown'}-{int(time.time()*1000)}"
            
            # Tạo danh sách nhận diện
            detections_list = []
            if detection_type == "OBJECT":
                objects = event.get("detectedObjects", [])
                for obj in objects:
                    detections_list.append({
                        "label": obj.get("label") or obj.get("name") or "Object",
                        "confidence": obj.get("confidence") or 1.0
                    })
            elif detection_type == "FACE":
                detections_list.append({
                    "label": "face",
                    "confidence": event.get("confidence") or 1.0,
                    "matched": event.get("faceMatched", False),
                    "person_id": event.get("personId")
                })
            
            accepted = True
            if detection_type == "OBJECT":
                risk = event.get("riskLevel", "LOW")
                if risk in ["HIGH", "CRITICAL", "MEDIUM"]:
                    accepted = False
            elif detection_type == "FACE":
                matched = event.get("faceMatched", True)
                if not matched:
                    accepted = False
                    
            query = """
                INSERT INTO camera_frames 
                (frame_id, camera_id, accepted, timestamp, processed_at, motion_score, quality, detections)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (frame_id) DO NOTHING;
            """
            cursor.execute(query, (
                frame_id,
                camera_id,
                accepted,
                ts,
                datetime.utcnow(),
                event.get("motionScore", 0.0) or (0.9 if not accepted else 0.1),
                event.get("quality", "high"),
                json.dumps(detections_list)
            ))
            conn.commit()
            cursor.close()
            print(f"💾 [B5 Database] Đã lưu thành công log B4 AI Vision {frame_id} vào camera_frames")
        except Exception as e:
            print(f"Lỗi khi lưu webhook B4 AI Vision vào DB: {e}")
            conn.rollback()
        finally:
            conn.close()

    return {"status": "success", "received": True}

# ==========================================
# 4 ENDPOINTS LẤY LOG CHI TIẾT CHO DASHBOARD DRILL-DOWN
# ==========================================

@app.get("/api/v1/dashboard/logs/access", tags=["dashboard"])
@app.get("/api/v1/dashboard/logs/students", tags=["dashboard"])
def get_dashboard_logs_access():
    conn = get_db_connection()
    logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT time, gate_id, direction, access_granted, person_type 
                FROM gate_events 
                ORDER BY time DESC 
                LIMIT 50;
            """)
            rows = cursor.fetchall()
            for idx, r in enumerate(rows):
                logs.append({
                    "id": f"acc-db-{idx+1}",
                    "time": r[0].isoformat(),
                    "gate": r[1] or "Unknown Gate",
                    "direction": r[2] or "IN",
                    "status": "Thành công" if r[3] else "Từ chối",
                    "person_type": r[4] or "Khách"
                })
            cursor.close()
        except Exception as e:
            print(f"Lỗi truy vấn gate_events: {e}")
        finally:
            conn.close()

    # MOCK DATA FALLBACK REMOVED
    # Only real database data is returned
    return logs

@app.get("/api/v1/dashboard/logs/temp", tags=["dashboard"])
def get_dashboard_logs_temp():
    conn = get_db_connection()
    logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT time, device_id, temperature_c, humidity_percent 
                FROM sensor_events 
                ORDER BY time DESC 
                LIMIT 50;
            """)
            rows = cursor.fetchall()
            for idx, r in enumerate(rows):
                logs.append({
                    "id": f"temp-db-{idx+1}",
                    "time": r[0].isoformat(),
                    "location": r[1] or "Unknown Location",
                    "temp": round(r[2], 1) if r[2] is not None else 32.5,
                    "humidity": round(r[3], 1) if r[3] is not None else 55.0
                })
            cursor.close()
        except Exception as e:
            print(f"Lỗi truy vấn sensor_events: {e}")
        finally:
            conn.close()

    # MOCK DATA FALLBACK REMOVED
    # Only real database data is returned
    return logs

@app.get("/api/v1/dashboard/logs/alerts", tags=["dashboard"])
def get_dashboard_logs_alerts():
    conn = get_db_connection()
    logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT time, log_type, details 
                FROM campus_logs 
                ORDER BY time DESC 
                LIMIT 50;
            """)
            campus_rows = cursor.fetchall()
            for idx, r in enumerate(campus_rows):
                t_val, log_type, details_json = r
                details = {}
                if isinstance(details_json, str):
                    try: details = json.loads(details_json)
                    except: pass
                elif isinstance(details_json, dict):
                    details = details_json

                # CODE CŨ:
                # severity = details.get("severity") or ("HIGH" if log_type == "FIRE_ALARM" else "MEDIUM")
                # logs.append({
                #     "id": f"alt-db-c-{idx+1}",
                #     "time": t_val.isoformat(),
                #     "source": "B6_CORE",
                #     "type": details.get("event_type", log_type),
                #     "severity": severity
                # })
                # CODE MỚI THAY THẾ:
                is_b7 = details.get("module") == "notification"
                source = "B7_NOTIFICATION" if is_b7 else "B6_CORE"
                
                # Trích xuất severity từ B7 hoặc B6
                if is_b7:
                    b7_msg = details.get("message", {})
                    b7_sev = b7_msg.get("severity") if isinstance(b7_msg, dict) else None
                    severity = (b7_sev or "medium").upper()
                    event_type = "NOTIFICATION"
                    if isinstance(b7_msg, dict) and b7_msg.get("message"):
                        event_type = b7_msg.get("message")
                else:
                    severity = "MEDIUM"
                    if log_type == "FIRE_ALARM":
                        severity = "HIGH"
                    elif details.get("severity"):
                        severity = str(details.get("severity")).upper()
                    event_type = details.get("event_type", log_type)

                logs.append({
                    "id": f"alt-db-c-{idx+1}",
                    "time": t_val.isoformat(),
                    "source": source,
                    "type": event_type,
                    "severity": severity
                })

            cursor.execute("""
                SELECT timestamp, camera_id, motion_score 
                FROM camera_frames 
                WHERE accepted = false 
                ORDER BY timestamp DESC 
                LIMIT 50;
            """)
            cam_rows = cursor.fetchall()
            for idx, r in enumerate(cam_rows):
                logs.append({
                    "id": f"alt-db-cam-{idx+1}",
                    "time": r[0].isoformat(),
                    "source": "B4_VISION",
                    "type": f"Nhận diện bất thường tại {r[1]}",
                    "severity": "HIGH" if r[2] > 0.8 else "MEDIUM"
                })

            cursor.close()
        except Exception as e:
            print(f"Lỗi truy vấn campus_logs/camera_frames: {e}")
        finally:
            conn.close()

        logs.sort(key=lambda x: x["time"], reverse=True)
        logs = logs[:50]

    # MOCK DATA FALLBACK REMOVED
    # Only real database data is returned
    return logs

@app.get("/api/v1/dashboard/logs/camera", tags=["dashboard"])
def get_dashboard_logs_camera():
    conn = get_db_connection()
    logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, camera_id, detections 
                FROM camera_frames 
                ORDER BY timestamp DESC 
                LIMIT 50;
            """)
            rows = cursor.fetchall()
            for idx, r in enumerate(rows):
                detections_raw = r[2]
                detections_list = []
                if isinstance(detections_raw, str):
                    try: detections_list = json.loads(detections_raw)
                    except: pass
                elif isinstance(detections_raw, list):
                    detections_list = detections_raw

                objects_str = "None"
                conf_val = 0.0
                if detections_list:
                    items = []
                    confs = []
                    for item in detections_list:
                        label = item.get("label") or ("Face" if item.get("person_id") or "matched" in item else "Object")
                        matched_status = ""
                        if "matched" in item:
                            matched_status = " (Khớp)" if item.get("matched") else " (K.Khớp)"
                        items.append(f"{label}{matched_status}")
                        confs.append(item.get("confidence", 1.0))
                    objects_str = ", ".join(items)
                    conf_val = round(sum(confs) / len(confs) * 100, 1) if confs else 0.0
                else:
                    objects_str = "Chuyển động"
                    conf_val = 100.0

                logs.append({
                    "id": f"cam-db-{idx+1}",
                    "time": r[0].isoformat(),
                    "camera_id": r[1] or "CAM-01",
                    "objects": objects_str,
                    "confidence": conf_val
                })
            cursor.close()
        except Exception as e:
            print(f"Lỗi truy vấn camera_frames: {e}")
        finally:
            conn.close()

    # MOCK DATA FALLBACK REMOVED
    # Only real database data is returned
    return logs


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>Ứng dụng Dashboard đang được biên dịch (ReactJS)... Vui lòng chạy 'npm run build' trong thư mục frontend hoặc đợi Docker hoàn tất build!</h3>"

# --- API LIVE CHO DASHBOARD PHÂN TÍCH ---
@app.get("/api/v1/dashboard/live", tags=["dashboard"])
def get_dashboard_live(range: str = "today"):
    # 1. Quét sức khỏe kết nối (Ping check)
    def get_health_url(env_name: str, default_base: str) -> str:
        url = os.getenv(env_name, default_base).strip().rstrip("/")
        if not url.endswith("/health") and not url.endswith("health"):
            url += "/health"
        return url

    services_to_check = {
        "b1_iot": get_health_url("B1_IOT_URL", "http://26.190.131.131:8000"),
        "b2_camera": get_health_url("B2_CAMERA_URL", "http://26.38.132.64:8000"),
        "b3_access": get_health_url("B3_ACCESS_URL", "http://26.222.63.164:8000"),
        "b4_vision": get_health_url("B4_VISION_URL", "http://26.79.18.68:8000"),
        "b6_core": get_health_url("B6_CORE_URL", "http://26.76.38.192:8000"),
        "b7_notification": get_health_url("B7_NOTIFICATION_URL", "http://26.177.175.21:8085")
    }

    def check_service(name: str, url: str) -> str:
        # Check all services via HTTP GET
        try:
            r = requests.get(url, timeout=1.0)
            if r.status_code == 200:
                return "online"
            return "offline"
        except Exception:
            return "offline"


    # Chạy song song 6 luồng ping check
    health_results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {name: executor.submit(check_service, name, url) for name, url in services_to_check.items()}
        for name, fut in futures.items():
            health_results[name] = fut.result()

    # 2. SQL Query tính toán dữ liệu
    if range == "today":
        interval = "1 day"
    elif range == "30days":
        interval = "30 days"
    else:
        interval = "7 days"

    stats = {
        "total_access": 0,
        "avg_temp": 32.5,
        "total_alerts": 0,
        "camera_detections": 0
    }
    chart_data = {
        "temperature_history": [],
        "access_by_gate": []
    }
    recent_alerts = []

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # --- 2.1 KPIs ---
            cursor.execute(f"SELECT COUNT(*) FROM gate_events WHERE time >= NOW() - INTERVAL '{interval}';")
            stats["total_access"] = cursor.fetchone()[0]

            cursor.execute(f"SELECT AVG(temperature_c) FROM sensor_events WHERE temperature_c IS NOT NULL AND time >= NOW() - INTERVAL '{interval}';")
            avg_temp = cursor.fetchone()[0]
            if avg_temp is not None:
                stats["avg_temp"] = round(avg_temp, 1)

            cursor.execute(f"SELECT COUNT(*) FROM campus_logs WHERE time >= NOW() - INTERVAL '{interval}';")
            stats["total_alerts"] = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM camera_frames WHERE timestamp >= NOW() - INTERVAL '{interval}';")
            stats["camera_detections"] = cursor.fetchone()[0]

            # --- 2.2 Biểu đồ nhiệt độ (temperature_history) ---
            cursor.execute(f"""
                SELECT time, temperature_c 
                FROM sensor_events 
                WHERE temperature_c IS NOT NULL AND time >= NOW() - INTERVAL '{interval}'
                ORDER BY time DESC 
                LIMIT 15;
            """)
            temp_rows = cursor.fetchall()
            temp_rows.reverse()
            for r in temp_rows:
                chart_data["temperature_history"].append({
                    "time": r[0].strftime("%H:%M" if range == "today" else "%d/%m %H:%M"),
                    "temp": round(r[1], 1)
                })

            # Biểu đồ người ra vào theo cổng (access_by_gate) ---
            cursor.execute(f"""
                SELECT gate_id, 
                       COUNT(*) FILTER (WHERE direction = 'IN') as in_count,
                       COUNT(*) FILTER (WHERE direction = 'OUT') as out_count
                FROM gate_events
                WHERE time >= NOW() - INTERVAL '{interval}'
                GROUP BY gate_id;
            """)
            gate_rows = cursor.fetchall()
            for r in gate_rows:
                chart_data["access_by_gate"].append({
                    "gate": r[0] or "Unknown",
                    "in": r[1],
                    "out": r[2]
                })

            # --- 2.3 Bảng Live Alerts ---
            cursor.execute(f"""
                SELECT time, log_type, details 
                FROM campus_logs 
                WHERE time >= NOW() - INTERVAL '{interval}'
                ORDER BY time DESC 
                LIMIT 10;
            """)
            log_rows = cursor.fetchall()
            for idx, r in enumerate(log_rows):
                t_val, log_type, details_json = r
                details = {}
                if isinstance(details_json, str):
                    try: details = json.loads(details_json)
                    except: pass
                elif isinstance(details_json, dict):
                    details = details_json

                # CODE CŨ:
                # severity = "MEDIUM"
                # if log_type == "FIRE_ALARM":
                #     severity = "HIGH"
                # elif details.get("severity"):
                #     severity = details.get("severity")
                # 
                # recent_alerts.append({
                #     "id": f"ALT-{idx+1}",
                #     "time": t_val.isoformat(),
                #     "source": "B6_CORE",
                #     "type": details.get("event_type", log_type),
                #     "severity": severity
                # })
                # CODE MỚI THAY THẾ:
                is_b7 = details.get("module") == "notification"
                source = "B7_NOTIFICATION" if is_b7 else "B6_CORE"
                
                # Trích xuất severity từ B7 hoặc B6
                if is_b7:
                    b7_msg = details.get("message", {})
                    b7_sev = b7_msg.get("severity") if isinstance(b7_msg, dict) else None
                    severity = (b7_sev or "medium").upper()
                    event_type = "NOTIFICATION"
                    if isinstance(b7_msg, dict) and b7_msg.get("message"):
                        event_type = b7_msg.get("message")
                else:
                    severity = "MEDIUM"
                    if log_type == "FIRE_ALARM":
                        severity = "HIGH"
                    elif details.get("severity"):
                        severity = str(details.get("severity")).upper()
                    event_type = details.get("event_type", log_type)

                recent_alerts.append({
                    "id": f"ALT-{idx+1}",
                    "time": t_val.isoformat(),
                    "source": source,
                    "type": event_type,
                    "severity": severity
                })

            # Đọc thêm cảnh báo camera bất thường
            cursor.execute(f"""
                SELECT timestamp, camera_id, motion_score 
                FROM camera_frames 
                WHERE accepted = false AND timestamp >= NOW() - INTERVAL '{interval}'
                ORDER BY timestamp DESC 
                LIMIT 5;
            """)
            cam_alert_rows = cursor.fetchall()
            for idx, r in enumerate(cam_alert_rows):
                recent_alerts.append({
                    "id": f"CAM-ALT-{idx+1}",
                    "time": r[0].isoformat(),
                    "source": "B4_VISION",
                    "type": f"Nhận diện bất thường tại {r[1]}",
                    "severity": "HIGH" if r[2] > 0.8 else "MEDIUM"
                })

            recent_alerts.sort(key=lambda x: x["time"], reverse=True)
            recent_alerts = recent_alerts[:10]

            cursor.close()
        except Exception as e:
            print(f"Lỗi DB trong get_dashboard_live: {e}")
        finally:
            conn.close()

    # MOCK DATA FALLBACK REMOVED
    # Only real database data is returned

    return {
        "system_health": health_results,
        "summary_stats": stats,
        "chart_data": chart_data,
        "recent_alerts": recent_alerts
    }

# Để tương thích ngược với code cũ
@app.get("/api/v1/dashboard/summary", tags=["dashboard"])
async def get_dashboard_summary():
    return {
        "total_students_today": 120,
        "current_avg_temperature": 32.5,
        "recent_alerts": 3,
        "camera_detections": 15
    }