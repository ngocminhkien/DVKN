# Hướng dẫn khởi chạy Analytics Service (B5)

Tài liệu này hướng dẫn cách sao chép mã nguồn, thiết lập môi trường và chạy dự án bằng Docker Compose & Makefile.

## 1. Sao chép mã nguồn (Clone)
Mở terminal và chạy lệnh sau để tải dự án về máy:
```bash
git clone <URL_KHO_LUU_TRU>
cd DVKN
```

## 2. Thiết lập biến môi trường
Tạo một bản sao của file mẫu `.env.example` và đổi tên thành `.env`:
```bash
cp .env.example .env
```
Mở file `.env` và cập nhật các thông số bảo mật phù hợp với môi trường cục bộ của bạn.

## 3. Khởi chạy bằng Makefile
Dự án sử dụng `Makefile` để đơn giản hóa các lệnh Docker. Bạn có thể sử dụng các phím tắt sau (đảm bảo bạn đã cài đặt `make` trên máy):

- **Khởi động hệ thống:**
  ```bash
  make compose-up
  ```
  Lệnh này sẽ chạy `docker compose up --build -d` để build và chạy 3 dịch vụ nền.

- **Xem nhật ký (logs):**
  ```bash
  make logs
  ```
  Để theo dõi trạng thái hoạt động của các dịch vụ.

- **Dừng hệ thống:**
  ```bash
  make compose-down
  ```
  Lệnh này sẽ dừng các container và xóa các volume cục bộ.

- **Chạy kiểm thử với Newman:**
  ```bash
  make test-compose
  ```
  (Lưu ý: Bạn cần có cấu hình collection và environment trong thư mục `postman/` trước khi chạy lệnh này).
