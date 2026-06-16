import os
import json
import time
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime

# ==========================================
# Cấu hình MQTT & Database từ file .env
# ==========================================
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC = "smart-campus/events/sensor"

def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("POSTGRES_DB", "analytics_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
    except Exception as e:
        print(f"[DB Error] Không thể kết nối DB: {e}")
        return None

# ==========================================
# Các hàm sự kiện (Callbacks) của MQTT
# ==========================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Đã kết nối MQTT Broker ({MQTT_BROKER}).")
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Đã đăng ký hóng tin tại topic: {MQTT_TOPIC}")
    else:
        print(f"❌ Kết nối MQTT thất bại, mã lỗi: {rc}")

def on_message(client, userdata, msg):
    try:
        # 1. Đọc tin nhắn B1 gửi tới
        payload_str = msg.payload.decode('utf-8')
        payload = json.loads(payload_str)
        
        # 2. XÓA BẪY CỦA GIẢNG VIÊN (QUAN TRỌNG!)
        if "scenario_hint_for_teacher" in payload:
            del payload["scenario_hint_for_teacher"]
            print("🛡️ Đã phát hiện và gỡ bỏ 'scenario_hint_for_teacher'.")

        # 3. Trích xuất thông số
        event_time = payload.get("timestamp", datetime.now().isoformat())
        event_id = payload.get("event_id")
        device_id = payload.get("device_id")
        temp = payload.get("temperature_c")
        humidity = payload.get("humidity_percent")
        co2 = payload.get("co2_ppm")
        status = payload.get("status")
        alert_level = payload.get("alert_level")
        reason = payload.get("reason")
        
        # 4. Nhét vào TimescaleDB
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO sensor_events 
                (time, event_id, device_id, temperature_c, humidity_percent, co2_ppm, status, alert_level, reason, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (event_time, event_id, device_id, temp, humidity, co2, status, alert_level, reason, json.dumps(payload)))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"💾 LƯU THÀNH CÔNG: Thiết bị {device_id} | Trạng thái: {status}")

    except Exception as e:
        print(f"⚠️ Lỗi khi xử lý bản tin MQTT: {e}")

# ==========================================
# Khởi động MQTT Client
# ==========================================
client = mqtt.Client()

if MQTT_USER and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

if MQTT_PORT == 8883:
    client.tls_set() # Kích hoạt mã hóa bảo mật TLS cho HiveMQ

client.on_connect = on_connect
client.on_message = on_message

# Thử kết nối mãi mãi (Phòng khi mạng rớt hoặc Broker sập)
while True:
    try:
        print(f"🔄 Đang kết nối tới {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        break
    except Exception as e:
        print(f"Kết nối lỗi: {e}. Sẽ thử lại sau 5 giây...")
        time.sleep(5)

# Bật vòng lặp vĩnh cửu để lắng nghe data B1
client.loop_forever()