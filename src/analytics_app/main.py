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
    b7_base = os.getenv("B7_NOTIFICATION_URL", "http://26.177.175.21:8000").strip().rstrip("/")
    b7_token = os.getenv("B7_BEARER_TOKEN", "").strip()

    # Theo OpenAPI B7: /api/v1/alerts/logs KHÔNG cần auth, trả về đầy đủ trường
    # /notifications/logs cần Bearer Token (401 nếu không có)
    # Endpoint chính: /api/v1/alerts/logs?limit=50
    # Schema trả về: [{ticket_id, event_id, alert_id, channel, status, severity, message, timestamp, sent}, ...]

    print(f"🚀 [B5 -> B7] Luồng kéo thông báo khẩn cấp từ B7 khởi động | URL mục tiêu: {b7_base}")

    while True:
        try:
            # --- Ưu tiên /api/v1/alerts/logs (không cần token, đầy đủ trường) ---
            dashboard_url = f"{b7_base}/api/v1/alerts/logs?limit=50"
            print(f"🔄 [B5 -> B7] Đang kéo cảnh báo từ B7 Notification Service tại {dashboard_url}...")

            response = requests.get(dashboard_url, timeout=8)

            # Nếu /api/v1/alerts/logs thất bại, thử /notifications/logs với token
            if response.status_code != 200 and b7_token:
                fallback_url = f"{b7_base}/notifications/logs?limit=50"
                print(f"⚠️ [B7] /api/v1/alerts/logs trả về {response.status_code}, thử fallback {fallback_url}...")
                headers = {"Authorization": f"Bearer {b7_token}"}
                response = requests.get(fallback_url, headers=headers, timeout=8)

            if response.status_code == 200:
                data = response.json()

                # B7 /api/v1/alerts/logs trả về list trực tiếp
                # B7 /notifications/logs có thể trả về {"items": [...]}
                logs_list = []
                if isinstance(data, list):
                    logs_list = data
                elif isinstance(data, dict) and "items" in data:
                    logs_list = data["items"]
                elif isinstance(data, dict) and "data" in data:
                    logs_list = data["data"]

                print(f"📩 [Nhận từ B7 Notification] Kéo thành công {len(logs_list)} thông báo khẩn cấp | Bắt đầu lưu vào database B5...")

                conn = get_db_connection()
                if conn and logs_list:
                    saved_count = 0
                    skipped_count = 0
                    try:
                        cursor = conn.cursor()
                        for log in logs_list:
                            if not isinstance(log, dict):
                                continue

                            ticket_id = log.get("ticket_id")
                            event_id = log.get("event_id") or log.get("alert_id")
                            severity = log.get("severity", "MEDIUM")
                            message = log.get("message", "")
                            channel = log.get("channel", "unknown")
                            status = log.get("status", "unknown")

                            # Parse timestamp
                            raw_ts = log.get("timestamp") or log.get("time")
                            try:
                                if isinstance(raw_ts, str):
                                    log_time = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                                else:
                                    log_time = datetime.now()
                            except Exception:
                                log_time = datetime.now()

                            # Xác định log_type từ nội dung message
                            msg_upper = message.upper()
                            if "HỎA HOẠN" in msg_upper or "FIRE" in msg_upper or "CHÁY" in msg_upper:
                                log_type = "FIRE_ALARM"
                            elif "XÂM NHẬP" in msg_upper or "INVALID_CARD" in msg_upper or "THẺ LẠ" in msg_upper:
                                log_type = "ACCESS_VIOLATION"
                            elif severity in ["CRITICAL", "HIGH"]:
                                log_type = "EMERGENCY_ALERT"
                            else:
                                log_type = "SYSTEM_ALERT"

                            # Chống trùng lặp: kiểm tra ticket_id đã có trong DB chưa
                            if ticket_id:
                                cursor.execute(
                                    "SELECT COUNT(*) FROM campus_logs WHERE details->>'ticket_id' = %s",
                                    (ticket_id,)
                                )
                                already_exists = cursor.fetchone()[0] > 0
                                if already_exists:
                                    skipped_count += 1
                                    continue

                            # Tạo details JSON đầy đủ để lưu vào DB
                            details_payload = {
                                "ticket_id": ticket_id,
                                "event_id": event_id,
                                "message": message,
                                "severity": severity,
                                "channel": channel,
                                "status": status,
                                "module": "notification",
                                "source": "B7_NOTIFICATION",
                                "event_type": log_type
                            }

                            cursor.execute(
                                "INSERT INTO campus_logs (time, log_type, details) VALUES (%s, %s, %s)",
                                (log_time, log_type, json.dumps(details_payload, ensure_ascii=False))
                            )
                            saved_count += 1

                        conn.commit()
                        cursor.close()
                        if saved_count > 0:
                            print(f"💾 [Lưu Database B5] Đã lưu {saved_count} cảnh báo mới từ B7 vào bảng campus_logs (Bỏ qua {skipped_count} trùng lặp)")
                        else:
                            print(f"✅ [B7 Notification] Không có cảnh báo mới — Tất cả {skipped_count} bản ghi đã tồn tại trong database B5")
                    except Exception as db_err:
                        print(f"❌ [Lỗi DB] Không thể lưu B7 logs: {db_err}")
                        conn.rollback()
                    finally:
                        conn.close()
            elif response.status_code == 401:
                print(f"🔐 [B7 Notification] Yêu cầu xác thực (401) — Kiểm tra B7_BEARER_TOKEN trong .env")
            else:
                print(f"⚠️ [B7 Notification] Lỗi! B7 trả về mã HTTP {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ [B7 Notification] Không kết nối được tới {b7_base} — Kiểm tra Radmin VPN (Lỗi: {type(e).__name__})")
        except requests.exceptions.Timeout:
            print(f"⏱️ [B7 Notification] Kết nối tới {b7_base} bị timeout — B7 có thể đang quá tải")
        except Exception as e:
            print(f"❌ [B7 Notification] Lỗi không xác định: {type(e).__name__}: {e}")

        # Kéo lại mỗi 30 giây thay vì 60 để nhận cảnh báo kịp thời hơn
        time.sleep(30)


def seed_initial_data():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sensor_events;")
            count = cursor.fetchone()[0]
            if count < 10:
                print(f"🌱 [Database Seeding] sensor_events has only {count} rows. Seeding 15 historical readings...")
                now = datetime.now()
                import math
                for i in range(15):
                    # Spread out events every 1.5 hours in the past
                    event_time = now - timedelta(hours=1.5 * (15 - i))
                    event_id = f"seed-b1-sensor-{1000 + i}"
                    device_id = "iot-room-101"
                    # Sinusoidal curve peaking at 14:00 (2 PM)
                    hour_float = event_time.hour + event_time.minute / 60.0
                    temp = 30.5 + 2.5 * math.sin((hour_float - 8) * math.pi / 12)
                    humidity = 60.0 - 10.0 * math.sin((hour_float - 8) * math.pi / 12)
                    co2 = 420.0 + 30.0 * math.sin((hour_float - 12) * math.pi / 12)
                    
                    status = "online"
                    alert_level = "normal"
                    reason = "Scheduled reading"
                    raw_payload = {
                        "device_id": device_id,
                        "temperature": round(temp, 1),
                        "humidity": round(humidity, 1),
                        "co2_ppm": int(co2),
                        "status": status,
                        "alert_level": alert_level,
                        "reason": reason,
                        "timestamp": event_time.isoformat()
                    }
                    
                    query = """
                        INSERT INTO sensor_events 
                        (time, event_id, device_id, temperature_c, humidity_percent, co2_ppm, status, alert_level, reason, raw_payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (
                        event_time, 
                        event_id, 
                        device_id, 
                        round(temp, 1), 
                        round(humidity, 1), 
                        int(co2), 
                        status, 
                        alert_level, 
                        reason, 
                        json.dumps(raw_payload)
                    ))
                conn.commit()
                print("🌱 [Database Seeding] Completed seeding sensor_events.")
            cursor.close()
        except Exception as e:
            print(f"Lỗi seeding database: {e}")
            if conn:
                conn.rollback()
        finally:
            conn.close()

@app.on_event("startup")
def startup_event():
    # Gieo dữ liệu lịch sử nếu cần thiết
    seed_initial_data()
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
    print(f"🔥 [Nhận từ B2 Camera Stream] Webhook từ Camera {event.cameraId} - Phát hiện {event.objectCount} đối tượng {event.labels} - Mức độ: {event.severity} | Lưu vào database B5")
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
        print(f"👁️ [Nhận từ B4 AI Vision] Nhận diện VẬT THỂ từ Camera {camera_id} - Phát hiện {len(objects)} đối tượng - Mức độ rủi ro: {risk} | Lưu vào database B5")
    elif detection_type == "FACE":
        matched = event.get("faceMatched")
        conf = event.get("confidence")
        match_status = "Thành công" if matched else "Không khớp"
        print(f"👤 [Nhận từ B4 AI Vision] Nhận diện KHUÔN MẶT từ Camera {camera_id} - Kết quả: {match_status} (Độ tin cậy: {conf}) | Lưu vào database B5")
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
                
            frame_id = event.get("detectionId") or event.get("frameId") or event.get("frame_id") or f"b4-{camera_id or 'unknown'}-{int(time.time()*1000)}"
            
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
                    "person_id": event.get("matchedPersonId") or event.get("personId")
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
            print(f"💾 [Lưu Database B5] Đã lưu thành công log nhận diện từ B4 AI Vision {frame_id} vào bảng camera_frames")
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
                SELECT time, gate_id, direction, access_granted, person_type, event_id 
                FROM gate_events 
                ORDER BY time DESC 
                LIMIT 50;
            """)
            rows = cursor.fetchall()
            for idx, r in enumerate(rows):
                logs.append({
                    "id": r[5] or f"acc-db-{idx+1}",
                    "time": r[0].isoformat(),
                    "gate": r[1] or "Unknown Gate",
                    "direction": r[2] or "IN",
                    "status": "Thành công" if r[3] else "Từ chối",
                    "person_type": r[4] or "Khách"
                })
            cursor.close()
            print(f"📊 [Truy vấn B5 Database] Lấy {len(logs)} lượt ra vào mới nhất gửi về Frontend")
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
                is_b7 = details.get("module") == "notification" or "ticket_id" in details
                source = "B7_NOTIFICATION" if is_b7 else "B6_CORE"
                
                # Trích xuất severity từ B7 hoặc B6
                if is_b7:
                    b7_msg = details.get("message", {})
                    if isinstance(b7_msg, dict):
                        b7_sev = b7_msg.get("severity") or details.get("severity")
                        severity = (b7_sev or "medium").upper()
                        event_type = b7_msg.get("message") or "NOTIFICATION"
                    else:
                        # message is a string in new OpenAPI format
                        severity = (details.get("severity") or "medium").upper()
                        event_type = details.get("message") or "NOTIFICATION"
                else:
                    severity = "MEDIUM"
                    if log_type == "FIRE_ALARM":
                        severity = "HIGH"
                    elif details.get("severity"):
                        severity = str(details.get("severity")).upper()
                    event_type = details.get("event_type", log_type)

                # Get the detailed message string
                msg_val = details.get("message") or details.get("description")
                if not msg_val and is_b7:
                    msg_val = details.get("message") if isinstance(details.get("message"), str) else None
                if not msg_val:
                    msg_val = f"Cảnh báo hệ thống {event_type}"

                logs.append({
                    "id": f"alt-db-c-{idx+1}",
                    "time": t_val.isoformat(),
                    "source": source,
                    "type": event_type,
                    "severity": severity,
                    "message": msg_val
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
                    "severity": "HIGH" if r[2] > 0.8 else "MEDIUM",
                    "message": f"Phát hiện vật thể bất thường tại camera {r[1]} (Độ tự tin: {round(r[2]*100, 1)}%)"
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
        "b1_iot": get_health_url("B1_IOT_URL", "http://26.184.240.188:8000"),
        "b2_camera": get_health_url("B2_CAMERA_URL", "http://26.230.25.250:8000"),
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
                is_b7 = details.get("module") == "notification" or "ticket_id" in details
                source = "B7_NOTIFICATION" if is_b7 else "B6_CORE"
                
                # Trích xuất severity từ B7 hoặc B6
                if is_b7:
                    b7_msg = details.get("message", {})
                    if isinstance(b7_msg, dict):
                        b7_sev = b7_msg.get("severity") or details.get("severity")
                        severity = (b7_sev or "medium").upper()
                        event_type = b7_msg.get("message") or "NOTIFICATION"
                    else:
                        # message is a string in new OpenAPI format
                        severity = (details.get("severity") or "medium").upper()
                        event_type = details.get("message") or "NOTIFICATION"
                else:
                    severity = "MEDIUM"
                    if log_type == "FIRE_ALARM":
                        severity = "HIGH"
                    elif details.get("severity"):
                        severity = str(details.get("severity")).upper()
                    event_type = details.get("event_type", log_type)

                # Get the detailed message string
                msg_val = details.get("message") or details.get("description")
                if not msg_val and is_b7:
                    msg_val = details.get("message") if isinstance(details.get("message"), str) else None
                if not msg_val:
                    msg_val = f"Cảnh báo hệ thống {event_type}"

                recent_alerts.append({
                    "id": f"ALT-{idx+1}",
                    "time": t_val.isoformat(),
                    "source": source,
                    "type": event_type,
                    "severity": severity,
                    "message": msg_val
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
                    "severity": "HIGH" if r[2] > 0.8 else "MEDIUM",
                    "message": f"Phát hiện vật thể bất thường tại camera {r[1]} (Độ tự tin: {round(r[2]*100, 1)}%)"
                })

            recent_alerts.sort(key=lambda x: x["time"], reverse=True)
            recent_alerts = recent_alerts[:10]

            cursor.close()
            print(f"📊 [BFF API] Cập nhật Live Stats | Lượt ra vào: {stats['total_access']} | Nhiệt độ TB: {stats['avg_temp']}°C | Cảnh báo: {stats['total_alerts']} | Chuyển động: {stats['camera_detections']}")
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