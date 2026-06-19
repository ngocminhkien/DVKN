# TÀI LIỆU HỢP ĐỒNG API HỘI TÍCH (API CONTRACTS) — NHÓM B4 (AI VISION SERVICE)

Tài liệu này định nghĩa chính thức các giao tiếp dữ liệu giữa **Nhóm B4 (AI Vision Service)** với các nhóm liên quan trong dự án Smart Campus:
*   **Nhóm B2 (Camera Stream)**: Consumer gọi vào API của B4.
*   **Nhóm B5 (Analytics Service)**: Consumer nhận Webhook (bất đồng bộ) từ B4 để phục vụ thống kê.
*   **Nhóm B6 (Core Business Service)**: Consumer nhận Webhook (bất đồng bộ) từ B4 để đưa ra các quyết định nghiệp vụ (báo động, xử lý cửa ra vào).

---

## 📌 THÔNG TIN CHUNG B4
*   **Tên Service**: `ai-vision-service`
*   **Địa chỉ host triển khai (Radmin VPN)**: `http://26.79.18.68:8000` (hoặc `http://localhost:8000` chạy local)
*   **Cơ chế xác thực**: Sử dụng Bearer Token cho các API mà B4 cung cấp.
    *   Header: `Authorization: Bearer local-dev-token`
*   **Định dạng dữ liệu**: `application/json`

---

## 1. HỢP ĐỒNG GIỮA B2 (CAMERA STREAM) VÀ B4 (AI VISION)

B2 sẽ gọi lên B4 khi phát hiện chuyển động hoặc khi cần nhận diện khuôn mặt tại các cổng kiểm soát.

### 1.1 API Phân tích vật thể (Object Detection)
*   **Endpoint**: `POST /vision/detect`
*   **Headers**:
    ```http
    Authorization: Bearer local-dev-token
    Content-Type: application/json
    ```

#### Request Payload (`DetectRequest`)
```json
{
  "cameraId": "CAM-001",
  "imageRef": "http://26.38.132.64:8000/snapshots/CAM-001/F-001.jpg",
  "timestamp": "2026-06-17T16:20:00Z",
  "motionConfidence": 0.95
}
```
*Chi tiết các trường:*
*   `cameraId` (Bắt buộc): Chuỗi mã định danh camera, định dạng `^CAM-[0-9]{3}$` (Ví dụ: `CAM-001`).
*   `imageRef` (Bắt buộc): Đường dẫn URI của ảnh (hỗ trợ `http://`, `https://`, `s3://`).
*   `timestamp` (Bắt buộc): Định dạng ISO 8601 của thời điểm chụp ảnh.
*   `motionConfidence` (Không bắt buộc): Độ tin cậy chuyển động phát hiện được ở biên (từ `0.0` đến `1.0`).

#### Response Payload (`ObjectDetectionResult`) - `201 Created`
```json
{
  "detectionId": "58c3db08-b80c-4fa2-bf42-01bb8d9600e1",
  "cameraId": "CAM-001",
  "detectionType": "OBJECT",
  "detectedObjects": [
    {
      "label": "PERSON",
      "confidence": 0.98,
      "boundingBox": {
        "x": 120,
        "y": 240,
        "width": 80,
        "height": 180
      }
    }
  ],
  "riskLevel": "LOW",
  "modelVersion": "yolov8x-coco-v2.1",
  "timestamp": "2026-06-17T16:20:02Z"
}
```
*Chi tiết các trường:*
*   `detectionId`: UUID định danh cho phiên nhận diện này.
*   `detectionType`: Luôn là `"OBJECT"`.
*   `detectedObjects`: Danh sách vật thể phát hiện được:
    *   `label`: Nhãn vật thể, bao gồm: `PERSON`, `VEHICLE`, `FIRE`, `SMOKE`, `BAG`, `OTHER`.
    *   `confidence`: Độ tin cậy của mô hình AI (`0.0` - `1.0`).
    *   `boundingBox`: Tọa độ khung nhận diện (`x`, `y` là góc trên bên trái, `width` là chiều rộng, `height` là chiều cao).
*   `riskLevel`: Mức độ rủi ro sơ bộ do AI phân tích (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
*   `modelVersion`: Phiên bản model AI đã xử lý.

---

### 1.2 API Đối sánh khuôn mặt (Face Matching)
*   **Endpoint**: `POST /vision/face-match`
*   **Headers**:
    ```http
    Authorization: Bearer local-dev-token
    Content-Type: application/json
    ```

#### Request Payload (`FaceMatchRequest`)
```json
{
  "cameraId": "CAM-002",
  "imageRef": "http://26.38.132.64:8000/snapshots/CAM-002/F-002.jpg",
  "timestamp": "2026-06-17T16:21:00Z"
}
```

#### Response Payload (`FaceMatchResult`) - `201 Created`
```json
{
  "detectionId": "ac8ea6c7-3117-48f8-b391-6677f52ee823",
  "cameraId": "CAM-002",
  "detectionType": "FACE",
  "faceMatched": true,
  "matchedPersonId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2eeee",
  "confidence": 0.92,
  "status": "success",
  "isLive": true,
  "riskLevel": "LOW",
  "modelVersion": "facenet-v3.0",
  "timestamp": "2026-06-17T16:21:02Z",
  "suggestions": null
}
```
*Chi tiết các trường:*
*   `faceMatched`: `true` nếu nhận diện đúng người đã đăng ký trong cơ sở dữ liệu, ngược lại `false`.
*   `matchedPersonId`: UUID của người được nhận diện (nếu khớp), hoặc `null` nếu không khớp.
*   `status`: Trạng thái đối sánh (`success`, `low_confidence`, `no_face_detected`).
*   `isLive`: Kiểm tra chống giả mạo khuôn mặt (chụp qua màn hình điện thoại/giấy).
*   `suggestions`: Danh sách các gợi ý người có độ tương đồng gần nhất (nếu độ tin cậy thấp).

---

## 2. HỢP ĐỒNG WEBHOOK BẤT ĐỒNG BỘ: B4 GỬI KẾT QUẢ CHO B5 VÀ B6

Sau khi B4 phân tích xong hình ảnh (từ B2 gửi tới), B4 sẽ **không tự quyết định việc tạo cảnh báo**, mà sẽ đẩy **toàn bộ dữ liệu kết quả phân tích** sang cho **B5 (Analytics)** phục vụ thống kê và **B6 (Core Business)** phục vụ quyết định nghiệp vụ.

### 🔴 QUY ĐỊNH CHO B5 & B6:
Hiện tại trong cấu hình hệ thống, URL nhận tin của B5 và B6 đang trỏ tạm về endpoint `/health` (chỉ nhận phương thức `GET`).
Để tích hợp thành công, **B5 và B6 bắt buộc phải cung cấp một API dạng POST** để nhận dữ liệu từ B4 gửi sang.

*   **URL mẫu cần xây dựng**:
    *   B6 (Core Business): `POST http://<B6_IP>:<B6_PORT>/api/v1/webhook/vision`
    *   B5 (Analytics): `POST http://<B5_IP>:<B5_PORT>/api/v1/analytics/vision`
*   Khi có các URL chính thức này, B4 sẽ cập nhật vào file cấu hình hệ thống `.env` của mình:
    ```bash
    CORE_SERVICE_URL=http://26.177.175.21:8000/api/v1/webhook/vision
    ANALYTICS_SERVICE_URL=http://26.21.187.230:8000/api/v1/analytics/vision
    ```

---

### 2.1 Payload Webhook dạng Phân tích vật thể (OBJECT)
B4 sẽ gửi payload này qua HTTP POST tới B5 và B6:

```json
{
  "detectionId": "58c3db08-b80c-4fa2-bf42-01bb8d9600e1",
  "cameraId": "CAM-001",
  "detectionType": "OBJECT",
  "detectedObjects": [
    {
      "label": "PERSON",
      "confidence": 0.98,
      "boundingBox": {
        "x": 120,
        "y": 240,
        "width": 80,
        "height": 180
      }
    }
  ],
  "riskLevel": "LOW",
  "modelVersion": "yolov8x-coco-v2.1",
  "timestamp": "2026-06-17T16:20:02Z",
  "originalRequest": {
    "cameraId": "CAM-001",
    "imageRef": "http://26.38.132.64:8000/snapshots/CAM-001/F-001.jpg",
    "timestamp": "2026-06-17T16:20:00Z",
    "motionConfidence": 0.95
  }
}
```
*Lưu ý:* Trường `originalRequest` đính kèm chính là payload nguyên bản mà nhóm B2 đã gửi cho B4. Điều này giúp nhóm B5, B6 nắm được chính xác đường dẫn ảnh gốc `imageRef` để hiển thị trên dashboard của mình, cũng như timestamp gốc của camera.

---

### 2.2 Payload Webhook dạng Đối sánh khuôn mặt (FACE)
B4 sẽ gửi payload này qua HTTP POST tới B5 và B6:

```json
{
  "detectionId": "ac8ea6c7-3117-48f8-b391-6677f52ee823",
  "cameraId": "CAM-002",
  "detectionType": "FACE",
  "faceMatched": true,
  "matchedPersonId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2eeee",
  "confidence": 0.92,
  "status": "success",
  "isLive": true,
  "riskLevel": "LOW",
  "modelVersion": "facenet-v3.0",
  "timestamp": "2026-06-17T16:21:02Z",
  "suggestions": null,
  "originalRequest": {
    "cameraId": "CAM-002",
    "imageRef": "http://26.38.132.64:8000/snapshots/CAM-002/F-002.jpg",
    "timestamp": "2026-06-17T16:21:00Z"
  }
}
```

---

## 3. CÁC MÃ LỖI PHẢN HỒI CHUẨN (PROBLEM DETAILS - RFC 7807)
Nếu xảy ra lỗi, B4 sẽ trả về mã lỗi theo định dạng RFC 7807 để các nhóm tiện xử lý:

### 3.1 Sai định dạng Request (400 Bad Request)
```json
{
  "type": "about:blank",
  "title": "Bad Request",
  "status": 400,
  "detail": "Trường imageRef không đúng định dạng URI",
  "instance": "/vision/detect"
}
```

### 3.2 Lỗi phân tích hình ảnh từ AI (422 Unprocessable Entity)
Trả về khi không thể tải hoặc xử lý hình ảnh được chỉ định bởi `imageRef`:
```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Không thể xử lý ảnh từ imageRef cung cấp (Lỗi AI: Connection Refused)",
  "instance": "/vision/detect"
}
```

### 3.3 Chưa xác thực hoặc Token sai (401 Unauthorized)
```json
{
  "type": "about:blank",
  "title": "Unauthorized",
  "status": 401,
  "detail": "Missing or invalid credentials",
  "instance": "/vision/detect"
}
```
