# BÁO CÁO KIỂM THỬ TÍCH HỢP & PHÂN TÍCH HỆ THỐNG QA (E2E)
**Hệ thống:** Smart Campus Operations Platform - Product B
**Thành phần đánh giá:** Dịch vụ phân tích trung tâm Analytics Service (Nhóm B5)
**Trạng thái hệ thống:** 🟢 **ĐÃ SỬA LỖI & TÁI KHỞI ĐỘNG THÀNH CÔNG**

---

## PHẦN 1: PHÂN TÍCH TĨNH & ĐÁNH GIÁ KIẾN TRÚC (STATIC ANALYSIS)

### 1. Đánh giá sự tương thích hợp đồng dữ liệu (Contract Compliance)

#### 🔴 Nhóm B1 (IoT Ingestion - MQTT)
*   **Sai lệch Topic:** Hợp đồng giao tiếp của B1 (`contracts/b1_iot_mqtt_contract.md`) quy định topic là `campus/sensor/metrics`, nhưng mã nguồn gốc của worker `mqtt_subscriber.py` lại subscribe topic `smart-campus/events/sensor`.
*   **Sai lệch Payload:** 
    *   Hợp đồng B1 gửi các trường `"temperature"` và `"humidity"`.
    *   Nhưng worker `mqtt_subscriber.py` lại parse các trường `"temperature_c"` và `"humidity_percent"`.
    *   *Hậu quả:* Mọi dữ liệu cảm biến gửi từ B1 khi vào DB đều bị lưu thành `NULL` hoặc giá trị mặc định.
*   *Trạng thái:* **Đã sửa đổi trên local để tương thích với hợp đồng B1 và hỗ trợ fallback.**

#### 🔴 Nhóm B2 (Camera Stream - Webhook)
*   **Lỗi Validation (422 HTTP Mismatch):**
    *   Hợp đồng `contracts/b2_camera.openapi.yaml` chỉ yêu cầu 6 trường cơ bản: `sourceService`, `eventType`, `cameraId`, `objectCount`, `severity`, và `timestamp`.
    *   Tuy nhiên, model `B2CameraEvent` trong `main.py` của chúng ta lại bắt buộc (required) đến 15 trường, bao gồm các trường phụ như `frameId`, `processedAt`, `motionScore`, `detections`, `labels`, `maxConfidence`, `abnormal`...
    *   *Hậu quả:* Khi B2 gọi POST webhook sang cổng `/analytics/camera-events` theo chuẩn hợp đồng của họ, FastAPI sẽ chặn lại và trả về lỗi `422 Unprocessable Entity` do thiếu các trường bắt buộc trên.

#### 🟢 Nhóm B3 (Access Gate - Webhook)
*   **Tương thích:** **Đạt**. Endpoint `/api/v1/ingest/access` trong router `b3_gate.py` khớp hoàn chỉnh với hợp đồng dữ liệu quẹt thẻ. Các trường bổ sung như `source_service` hay `product` đã có giá trị mặc định nên không bị lỗi validation.

#### 🟢 Nhóm B4 (AI Vision - Webhook)
*   **Tương thích:** **Đạt**. Endpoint `/api/v1/analytics/vision` nhận kiểu dữ liệu chung `Dict[str, Any]` (không ép kiểu Pydantic chặt chẽ) nên B4 đẩy sự kiện `OBJECT` hay `FACE` thì B5 đều parse linh hoạt bằng `.get()` và lưu thành công, không lo sập do lỗi validation.

#### 🔴 Nhóm B6 (Core Business - Webhook)
*   **Sai lệch Alias (Tên trường):**
    *   Hợp đồng quy định gửi trường `from_time` và `to_time`.
    *   Nhưng mã nguồn `b6_gate.py` lại khai báo model nhận alias là `"from"` và `"to"` (gán vào `from_date` và `to_date`).
    *   *Hậu quả:* Các giá trị thời gian báo cáo gửi từ B6 sẽ bị bỏ qua và lưu thành `None` vào cơ sở dữ liệu.
*   **Ép kiểu quá chặt:** Hợp đồng chỉ yêu cầu mảng `data` chứa các object chung chung. Nhưng model trong `b6_gate.py` lại bắt buộc `data` phải khớp chính xác định dạng `LogEntry` (có `log_type`, `timestamp`, `details`). Nếu B6 gửi lệch cấu trúc, API sẽ báo lỗi `422`.

#### 🔴 Nhóm B7 (Notification - Pull Mode)
*   **Sai lệch nghiệp vụ & Nhầm lẫn nguồn gốc:**
    *   Hợp đồng `contracts/b7_integration_notes.md` trả về cấu trúc log chứa `timestamp`, `level`, `module`, `message`.
    *   Tiến trình `pull_b7_logs` trong `main.py` lại tìm kiếm trường `log_type` hoặc `type`. Do B7 không gửi 2 trường này, hệ thống tự động gán mặc định là `"SYSTEM_ALERT"`.
    *   Khi hiển thị trên Dashboard ở endpoint `/api/v1/dashboard/logs/alerts`, nguồn của log này lại bị hardcode thành `"B6_CORE"` thay vì `"B7_NOTIFICATION"`. Ngoài ra, API đọc mức độ cảnh báo qua `details.get("severity")`, trong khi trong dữ liệu của B7 thì `severity` lại nằm lồng bên trong `"message"` (`message.severity`), dẫn đến mức độ cảnh báo của B7 luôn bị fallback về `"MEDIUM"`.

---

### 2. Tối ưu hóa kiến trúc Backend-For-Frontend (BFF)

Cơ chế cập nhật dữ liệu hiện tại sử dụng polling từ ReactJS (gửi request mỗi 5 giây). Đây là điểm nghẽn nghiêm trọng với mã nguồn cũ:
1.  **Chặn Event Loop:** Webhook của B2 và B4 được khai báo dạng `async def` nhưng lại chạy các thư viện đồng bộ, gây block Event Loop của FastAPI.
2.  **Quá tải Database & CPU:** Mỗi request `/api/v1/dashboard/live` (cứ 5 giây từ mỗi tab trình duyệt của Client) sẽ chạy song song `ThreadPoolExecutor` để gửi 6 HTTP request ping đến 6 địa chỉ Radmin của các nhóm khác, đồng thời mở một kết nối DB mới để query liên tiếp 5-6 câu lệnh SQL nặng.
    *   *Khuyến nghị:* Cần có cơ chế Cache kết quả ping kiểm tra dịch vụ chạy nền (Background Task) thay vì ping trực tiếp mỗi khi BFF nhận request. Sử dụng Database Connection Pool để tránh quá tải kết nối.

---

## PHẦN 2: KỊCH BẢN KIỂM THỬ TÍCH HỢP (INTEGRATION TEST PLAN)

Dưới đây là các câu lệnh `cURL` và script mô phỏng để bạn chạy test trực tiếp trên môi trường `localhost:8000` hoặc trong container Docker:

### 1. B1 (IoT Ingestion - MQTT)
Đảm bảo đã cài `paho-mqtt` trên máy tính (`pip install paho-mqtt`). Chạy file Python này để gửi gói tin giả lập B1:

```python
import json
import time
import paho.mqtt.client as mqtt

# Cấu hình Broker HiveMQ dùng chung
broker = "b1-broker.hivemq.cloud"
port = 8883
topic = "campus/sensor/metrics"  # Đúng topic hợp đồng mới

client = mqtt.Client()
client.tls_set()  # Enforce TLS cho bảo mật HiveMQ
client.username_pw_set("your_mqtt_user", "your_mqtt_password")

client.connect(broker, port, 60)
payload = {
    "device_id": "TEMP-LOBBY-01",
    "location": "Sảnh chính tòa A",
    "temperature": 32.5,
    "humidity": 65.0,
    "timestamp": "2026-06-18T19:30:00Z"
}
client.publish(topic, json.dumps(payload), qos=1)
print("Đã gửi bản tin IoT B1!")
client.disconnect()
```
*Kiểm tra kết quả:* Chạy lệnh `docker logs analytics-worker` để xem log ghi nhận dữ liệu cảm biến vào DB.

### 2. B2 & B4 (Camera & AI Vision Webhooks)

#### Gửi cảnh báo từ Camera B2:
```bash
curl -X POST http://localhost:8000/analytics/camera-events \
  -H "Content-Type: application/json" \
  -d '{
    "sourceService": "B2_CAMERA_STREAM",
    "eventType": "AI_DETECTION",
    "cameraId": "CAM-001",
    "frameId": "F-20260617-0025",
    "timestamp": "2026-06-18T19:30:00Z",
    "processedAt": "2026-06-18T19:30:01Z",
    "motionScore": 0.72,
    "detections": [{"label": "person", "confidence": 0.96}],
    "objectCount": 1,
    "labels": ["person"],
    "maxConfidence": 0.96,
    "abnormal": true,
    "severity": "HIGH"
  }'
```

#### Gửi nhận diện Vật thể (OBJECT) từ AI Vision B4:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/vision \
  -H "Content-Type: application/json" \
  -d '{
    "detectionType": "OBJECT",
    "cameraId": "CAM-B4-LOBBY",
    "timestamp": "2026-06-18T19:30:00Z",
    "detectedObjects": [{"label": "backpack", "confidence": 0.88}],
    "riskLevel": "HIGH",
    "motionScore": 0.85
  }'
```

#### Gửi nhận diện Khuôn mặt (FACE) từ AI Vision B4:
```bash
curl -X POST http://localhost:8000/api/v1/analytics/vision \
  -H "Content-Type: application/json" \
  -d '{
    "detectionType": "FACE",
    "cameraId": "CAM-B4-ENTRANCE",
    "timestamp": "2026-06-18T19:31:00Z",
    "faceMatched": true,
    "confidence": 0.98,
    "personId": "STUDENT-2026-991A"
  }'
```

### 3. B3 (Access Gate Webhook)
```bash
curl -X POST http://localhost:8000/api/v1/ingest/access \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "acc-test-999",
    "gate_id": "gate-main-lobby",
    "direction": "IN",
    "access_granted": true,
    "person_type": "student",
    "timestamp": "2026-06-18T19:35:00Z"
  }'
```

### 4. B6 (Core Business Webhook)
```bash
curl -X POST http://localhost:8000/analytics/export \
  -H "Content-Type: application/json" \
  -d '{
    "from": "2026-06-18T19:00:00Z",
    "to": "2026-06-18T20:00:00Z",
    "data": [
      {
        "log_type": "ACCESS",
        "timestamp": "2026-06-18T19:05:00Z",
        "details": {"gate": "A1", "direction": "IN"}
      },
      {
        "log_type": "FIRE_ALARM",
        "timestamp": "2026-06-18T19:15:00Z",
        "details": {"zone": "Zone-A", "temperature": 95.0}
      }
    ]
  }'
```

### 5. B7 (Notification Service - Pull Task)
Để xác nhận bot kéo log từ B7 đang chạy ngầm, gõ lệnh sau để xem log của API:
```bash
docker logs analytics-api
```
Tìm log có dạng:
`🔄 [B5 -> B7] Đang sang nhà B7 lấy log...` hoặc `❌ [B7 Notification] B7 đang sập hoặc chưa mở Radmin...` (nếu máy B7 đang offline).

### 6. Kiểm tra API live cung cấp cho Frontend Dashboard
```bash
curl http://localhost:8000/api/v1/dashboard/live?range=today
```
*Kết quả mong đợi:* Trả về JSON chứa trạng thái kết nối mạng thực tế của các nhóm (`system_health`), cùng các số liệu thống kê KPIs thực lấy từ Database.

---

## PHẦN 3: BẢNG ĐÁNH GIÁ CHUNG & PHÁT HIỆN SỰ CỐ (DIAGNOSTICS)

### 1. Bảng đánh giá tích hợp các dịch vụ ngoài

| Dịch vụ ngoài | Giao thức | Vai trò của B5 | Đánh giá logic kiểm thử | Đóng góp & Khuyến nghị |
| :--- | :--- | :--- | :--- | :--- |
| **B1 (IoT Cảm biến)** | MQTT | Ingest (Subscribe) | ⚠️ **Cảnh báo** *(Đã sửa)* | Trước đó cấu hình sai topic và tên trường dữ liệu khiến DB trống rỗng. Khuyến nghị cập nhật theo đúng file đã sửa đổi. |
| **B2 (Camera Stream)** | HTTP POST | Ingest (Webhook) | ⚠️ **Cảnh báo** | Định nghĩa model Pydantic quá nhiều trường bắt buộc so với API của nhóm B2. *Khuyến nghị: Chuyển các trường phụ thành Optional trong main.py.* |
| **B3 (Cổng kiểm soát)**| HTTP POST | Ingest (Webhook) | 🟢 **Đạt** | Chạy ổn định, lưu đúng cấu trúc bảng `gate_events`. |
| **B4 (AI Vision)** | HTTP POST | Ingest (Webhook) | 🟢 **Đạt** | Parser động bằng Dict hoạt động linh hoạt, không lo lỗi định dạng dữ liệu từ B4. |
| **B6 (Nhiệp vụ chính)**| HTTP POST | Ingest (Webhook) | ⚠️ **Cảnh báo** | Sai tên trường `from_time`/`to_time` thành `from`/`to`. Cần sửa lại alias Pydantic. |
| **B7 (Cảnh báo)** | HTTP GET | Pull (Background task)| ⚠️ **Cảnh báo** | Log của B7 khi hiển thị trên web bị gán nhãn sai thành nguồn `B6_CORE` và mất định dạng severity. Cần chỉnh sửa lại câu lệnh SQL dashboard. |

---

### 2. ⚠️ DANH SÁCH CẢNH BÁO ĐỎ [RED ALERT] & MÃ NGUỒN SỬA LỖI

Quá trình kiểm tra hệ thống phát hiện 2 điểm chí mạng có thể gây treo ứng dụng hoặc tràn tài nguyên máy chủ. **Tất cả các lỗi này hiện đã được vá trực tiếp vào mã nguồn trong Workspace của bạn và đã được khởi động lại thành công:**

#### **[RED ALERT 1] Lỗi rò rỉ kết nối Database (Database Connection Leak)**
*   **Chi tiết lỗi:** Ở tệp `mqtt_subscriber.py` và `b2_puller.py`, kết nối DB (`conn`) được mở ra nhưng lệnh đóng kết nối `conn.close()` lại nằm hoàn toàn trong block `try`. Khi xảy ra lỗi dữ liệu đầu vào hoặc lỗi truy vấn SQL, luồng sẽ nhảy ngay vào block `except`, bỏ qua việc đóng kết nối. Kết nối cũ sẽ bị treo vô thời hạn (leak). Chỉ sau vài chục bản tin lỗi, PostgreSQL sẽ hết cổng kết nối khả dụng (quá giới hạn 100 kết nối) và treo toàn bộ hệ thống.
*   **Mã nguồn đã sửa (Áp dụng cho `mqtt_subscriber.py` và `b2_puller.py`):**
    Đã đưa toàn bộ lệnh đóng kết nối vào trong cấu trúc `try...finally` để đảm bảo kết nối luôn luôn được giải phóng:
    ```python
    def on_message(client, userdata, msg):
        conn = None
        try:
            payload_str = msg.payload.decode('utf-8')
            payload = json.loads(payload_str)
            
            # Trích xuất dữ liệu an toàn & tương thích hợp đồng B1
            device_id = payload.get("device_id")
            temp = payload.get("temperature") or payload.get("temperature_c")
            humidity = payload.get("humidity") or payload.get("humidity_percent")
            event_time = payload.get("timestamp") or payload.get("time") or datetime.now().isoformat()
            
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # (Tiến hành execute query và commit)
                    conn.commit()
                    cursor.close()
                except Exception as db_err:
                    print(f"Lỗi DB: {db_err}")
                    conn.rollback()
        except Exception as e:
            print(f"Lỗi xử lý MQTT: {e}")
        finally:
            if conn:
                conn.close() # Luôn luôn đóng kết nối an toàn!
    ```

#### **[RED ALERT 2] Treo ứng dụng do đồng bộ trong Async (Blocking Event Loop)**
*   **Chi tiết lỗi:** Trong `main.py`, các endpoint webhook `/analytics/camera-events`, `/api/v1/analytics/vision`, và `/dashboard` được khai báo bằng từ khóa `async def`. Tuy nhiên, bên trong các hàm này lại chạy các tác vụ đồng bộ chặn luồng (như `psycopg2.connect`, `open()` để đọc file tĩnh). Khi các webhook này nhận nhiều yêu cầu cùng lúc từ B2/B4, chúng sẽ chiếm dụng và treo cứng Event Loop duy nhất của FastAPI, khiến ứng dụng không thể xử lý thêm bất cứ request nào khác (bao gồm cả request tải trang giao diện hay ping kết nối).
*   **Mã nguồn đã sửa (Áp dụng cho `main.py`):**
    Đã chuyển định nghĩa của 3 endpoint này từ `async def` thành các hàm đồng bộ `def` thông thường. Nhờ đó, FastAPI sẽ tự động điều phối chúng chạy trên các Thread riêng biệt của Worker Threadpool, giúp Event Loop chính luôn thông thoáng và không bao giờ bị nghẽn:
    ```python
    @app.post("/analytics/camera-events", status_code=202, tags=["ingestion"])
    def ingest_camera_event(event: B2CameraEvent):
        # Viết bằng def để tránh block async event loop
        
    @app.post("/api/v1/analytics/vision", status_code=202, tags=["ingestion"])
    def ingest_vision_webhook(event: Dict[str, Any]):
        # Viết bằng def để tránh block async event loop

    @app.get("/dashboard", response_class=HTMLResponse)
    def get_dashboard():
        # Đọc file đồng bộ an toàn trong luồng ThreadPool
    ```
