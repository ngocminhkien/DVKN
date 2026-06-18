# Hợp đồng Giao tiếp MQTT - Nhóm B1 (IoT Ingestion)

## 1. Thông tin kết nối Broker
* **Giao thức:** MQTT
* **Topic Subscribe (B5 lắng nghe):** `campus/sensor/metrics`
* **QoS:** 1 (At least once)

## 2. Cấu trúc Payload (JSON)
Mỗi khi có biến động nhiệt độ/độ ẩm, nhóm B1 sẽ đẩy một bản tin JSON vào Topic trên với định dạng bắt buộc sau:

```json
{
  "device_id": "TEMP-LOBBY-01",
  "location": "Sảnh chính tòa A",
  "temperature": 32.5,
  "humidity": 65.0,
  "timestamp": "2026-06-18T19:30:00Z"
}