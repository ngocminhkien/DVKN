import os
import time
import requests
import psycopg2
import json

# Lấy cấu hình IP và Token của B2 từ file .env
B2_API_URL = os.getenv("B2_CAMERA_API_URL", "http://localhost:8000")
B2_TOKEN = os.getenv("B2_BEARER_TOKEN", "")

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
        print(f"[B2 Puller] Lỗi kết nối DB: {e}")
        return None

def pull_camera_data():
    conn = None
    try:
        # Gọi API lấy tối đa 20 frames mới nhất
        url = f"{B2_API_URL}/frames/latest?limit=20"
        headers = {}
        if B2_TOKEN:
            headers["Authorization"] = f"Bearer {B2_TOKEN}"
            
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json().get("items", [])
            if not data:
                return
            
            conn = get_db_connection()
            if not conn: return
            
            cursor = conn.cursor()
            inserted = 0
            
            for frame in data:
                # Dùng ON CONFLICT DO NOTHING để bỏ qua những frame_id đã từng lưu rồi
                query = """
                    INSERT INTO camera_frames 
                    (frame_id, camera_id, accepted, timestamp, processed_at, motion_score, quality, detections)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (frame_id) DO NOTHING;
                """
                cursor.execute(query, (
                    frame["frame_id"], 
                    frame["camera_id"], 
                    frame["accepted"],
                    frame["timestamp"], 
                    frame["processed_at"],
                    frame.get("motion_score", 0.0), 
                    frame.get("quality", "unknown"),
                    json.dumps(frame.get("detections", []))
                ))
                # cursor.rowcount sẽ = 1 nếu insert thành công, = 0 nếu bị trùng
                inserted += cursor.rowcount 
                
            conn.commit()
            cursor.close()
            
            if inserted > 0:
                print(f"[B2 Puller] Vừa kéo và lưu mới {inserted} frames từ Camera B2.")
        else:
            print(f"[B2 Puller] Gọi API thất bại. Status: {response.status_code}")
            
    except Exception as e:
        print(f"[B2 Puller] Lỗi trong quá trình kéo dữ liệu B2: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("[B2 Puller] Khởi động Bot hút data Camera B2...")
    while True:
        pull_camera_data()
        time.sleep(10) # Cứ 10 giây chạy đi lấy data 1 lần