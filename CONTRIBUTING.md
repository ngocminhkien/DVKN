# 📜 Quy định Quản lý Mã nguồn - Analytics Service (Team B5)

Để đảm bảo hệ thống luôn ổn định, vượt qua các bài kiểm tra tự động và chuẩn bị tốt nhất cho buổi Plug-a-thon, toàn bộ thành viên nhóm bắt buộc tuân thủ quy trình Git dưới đây.

## 🚫 1. Luật "Bất khả xâm phạm" (Protected Branches)
* **Tuyệt đối KHÔNG commit hoặc push code trực tiếp** lên hai nhánh `main` (sản phẩm thực tế) và `dev` (môi trường kiểm thử chung).
* Nhánh `main` và `dev` chỉ được phép nhận code mới thông qua **Pull Request (PR)**.
* Mọi Pull Request phải chờ hệ thống GitHub Actions (CI) chạy test báo "Xanh" mới được phép gộp (Merge).

## 🌿 2. Quy tắc tạo nhánh (Branch Naming)
* Mọi người phải tạo nhánh mới từ nhánh `dev` trước khi bắt đầu viết code.
* Tính năng mới: Đặt tên nhánh bắt đầu bằng `feat/` (Ví dụ: `feat/dashboard-api`).
* Sửa lỗi hệ thống: Đặt tên nhánh bắt đầu bằng `fix/` (Ví dụ: `fix/db-timeout-error`).
* Cập nhật tài liệu: Đặt tên nhánh bắt đầu bằng `docs/` (Ví dụ: `docs/update-run-compose`).

## 📝 3. Quy tắc viết thông điệp (Commit Message)
* Tuân thủ chuẩn Conventional Commits với cú pháp: `loại_thay_đổi: Mô tả ngắn gọn`.
* **feat:** Khi thêm một tính năng mới (Ví dụ: `feat: thêm api tổng hợp dữ liệu camera`).
* **fix:** Khi vá một lỗi hiện có (Ví dụ: `fix: sửa lỗi crash do thiếu biến môi trường DB`).
* **chore:** Khi cập nhật các thiết lập không làm thay đổi logic code (Ví dụ: `chore: cập nhật thư viện requirements`).

## 🔄 4. Quy trình làm việc chuẩn (Workflow Bước-Từng-Bước)
* Bước 1: Kéo code mới nhất từ nhánh `dev` về máy (`git pull origin dev`).
* Bước 2: Tạo nhánh làm việc cá nhân (`git checkout -b feat/ten-tinh-nang`).
* Bước 3: Viết code và tự kiểm tra trên máy bằng lệnh `make compose-up` và `make test-compose`.
* Bước 4: Lưu thay đổi cục bộ (`git add .` và `git commit -m "feat: mô tả"`).
* Bước 5: Đẩy nhánh cá nhân lên kho lưu trữ chung (`git push origin feat/ten-tinh-nang`).
* Bước 6: Lên giao diện GitHub, tạo một **Pull Request** yêu cầu gộp nhánh của bạn vào nhánh `dev`.
* Bước 7: Báo cho Leader (Minh Kiên) hoặc đồng đội vào xem xét code (Code Review) và nhấn Merge.