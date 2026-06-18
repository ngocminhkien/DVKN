# Hợp Đồng Tích Hợp - Nhóm B7 (Notification Service)

## 1. Cơ chế giao tiếp (Pull Mode)
Nhóm B5 (Analytics) sẽ phải cấu hình một Background Task (Cronjob) để định kỳ kéo Log cảnh báo từ máy chủ của nhóm B7.

## 2. API Endpoint cung cấp log
* **Giao thức:** HTTP GET
* **Endpoint:** `http://26.177.175.21:8085/api/v1/alerts/logs`
* **Tham số:** Có thể thêm `limit` (tối đa 100 log/request).

## 3. Cấu trúc Log trả về
```json
[
  {
    "timestamp": "2026-06-17 00:31:02",
    "level": "INFO",
    "module": "notification",
    "message": {
      "alert_id": "ALT-001",
      "severity": "high",
      "message": "Unknown person detected near main gate",
      "target": "security_team",
      "channel": "telegram",
      "status": "delivered"
    }
  }
]