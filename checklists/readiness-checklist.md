# Readiness Checklist - Analytics Service (B5)

Danh sách kiểm tra 6 điểm chuẩn để xác minh tính sẵn sàng của hệ thống cục bộ:

- [ ] **1. Môi trường (Environment Variables):** File `.env` đã được tạo từ `.env.example` và các biến bảo mật (POSTGRES_PASSWORD, AUTH_TOKEN) đã được cập nhật đúng.
- [ ] **2. Cơ sở dữ liệu (Database):** Dịch vụ `db` (TimescaleDB) đã khởi động thành công và vượt qua trạng thái `service_healthy`.
- [ ] **3. API Service:** Dịch vụ `api` (FastAPI) đã được build thành công, endpoint `/health` trả về kết nối CSDL hợp lệ.
- [ ] **4. Worker (Data Worker):** Dịch vụ `data-worker` đang chạy và có thể kết nối tới cơ sở dữ liệu chung.
- [ ] **5. Mạng nội bộ (Network):** Mạng `team-internal` đã được tạo và cả 3 dịch vụ đều nằm chung trên một dải mạng.
- [ ] **6. Cổng (Ports):** Cổng `8000` (hoặc cấu hình từ biến APP_PORT) trên máy chủ không bị xung đột và sẵn sàng nhận request.
