# Phân tích Ranh giới Dịch vụ (Service Boundary) - Analytics B5

## 1. Vai trò của Service
Analytics Service (B5) đóng vai trò là điểm cuối (Consumer cuối cùng) trong luồng dữ liệu của Smart Campus Operations Platform. Nhiệm vụ cốt lõi là thu thập, lưu trữ, và phân tích các luồng sự kiện từ toàn bộ hệ thống để phục vụ việc trích xuất báo cáo, thống kê metric.

## 2. Ranh giới dữ liệu (Data Boundary)
* **Dữ liệu sở hữu (Data Owner):** B5 sở hữu dữ liệu thống kê tổng hợp (Aggregated Metrics), lịch sử báo cáo, và dữ liệu chuỗi thời gian (Time-series data) của toàn hệ thống.
* **Dữ liệu vay mượn (Data Borrower):** B5 không sở hữu thông tin chi tiết của người dùng (Sinh viên/Nhân viên) hay cấu hình thiết bị IoT gốc, mà chỉ lưu trữ các ID tham chiếu (ví dụ: `device_id`, `student_id`) kèm theo sự kiện.

## 3. Bản đồ Tương tác (Upstream / Downstream)

| Loại tương tác | Tên Service (Nhóm) | Giao thức | Mô tả tích hợp |
| :--- | :--- | :--- | :--- |
| **Upstream** (Hút data về) | **IoT Ingestion (B1)** | MQTT (Subscribe) | Worker của B5 chạy ngầm, subscribe topic của B1 để kéo dữ liệu nhiệt độ, độ ẩm. |
| **Upstream** (Hút data về) | **Camera Stream (B2)** | REST API (GET) | Worker của B5 định kỳ gọi API `/frames/latest` của B2 để kéo lịch sử nhận diện. |
| **Upstream** (Hút data về) | **Notification (B7)** | REST API (GET) | B5 chạy ngầm định kỳ gọi `/notifications/logs` (hoặc `/api/v1/alerts/logs`) của B7 để kéo log lịch sử thông báo. |
| **Upstream** (Nhận data đẩy tới) | **Access Gate (B3)** | REST API (POST) | B3 chủ động gọi API `/api/v1/ingest/access` của B5 mỗi khi có sự kiện quẹt thẻ. |
| **Upstream** (Nhận data đẩy tới) | **AI Vision (B4)** | REST API (POST) | B4 chủ động gọi Webhook `/api/v1/analytics/vision` để đẩy kết quả nhận diện vật thể/khuôn mặt về B5. |
| **Upstream** (Nhận data đẩy tới) | **Core Business (B6)** | REST API (POST) | B6 chủ động gọi API `/analytics/export` của B5 để xuất báo cáo cảnh báo tập trung. |
| **Downstream** (Cung cấp data) | **Admin Dashboard / End-User** | REST API (GET) | B5 cung cấp các API (ví dụ: tổng lượt ra vào, nhiệt độ trung bình) để hệ thống Dashboard hiển thị biểu đồ. |