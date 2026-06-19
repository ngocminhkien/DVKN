# 📊 Nhóm B5 — Analytics Service (Product B)
## Phân tích đầy đủ Yêu cầu Báo cáo & Nộp bài theo Đề bài FIT4110

> **Học phần**: Dịch vụ kết nối và Công nghệ nền tảng  
> **Nhóm**: B5 | **Sản phẩm**: Product B  
> **Service phụ trách**: Analytics Service — *Xây dựng dịch vụ tổng hợp và phân tích dữ liệu*

---

## 1. Vai trò của B5 trong hệ thống

B5 là **trung tâm dữ liệu phân tích** của Product B. Service này chịu trách nhiệm:

- **Thu thập** dữ liệu từ nhiều nguồn: IoT, Camera, Access Gate, Core Business
- **Tổng hợp** metric và chỉ số vận hành theo thời gian thực
- **Cung cấp** báo cáo dạng JSON và endpoint phục vụ Dashboard
- **Hiển thị** tổng quan trạng thái toàn hệ thống cho người vận hành

```
IoT (B1) ──────────────┐
Camera (B2) ────────────┤
AI Vision (B4) ─────────┼──▶  B5 Analytics ──▶ Dashboard / Báo cáo
Access Gate (B3) ───────┤                       Metric / JSON API
Core Business (B6) ─────┘
Notification (B7) ──────┘  ← B5 kéo log mỗi 3 giây
```

---

## 2. Nhiệm vụ chính phải thực hiện

Theo đề bài (mục 6.5.2), B5 **bắt buộc** phải xây dựng service có khả năng:

| # | Nhiệm vụ | Ghi chú |
|---|----------|---------|
| 1 | **Nhận hoặc lấy dữ liệu** từ IoT, Camera, Access Gate và Core Business | Qua Webhook POST hoặc MQTT hoặc Pull |
| 2 | **Tổng hợp metric** từ dữ liệu thu thập được | Tính tổng, trung bình, đếm theo khoảng thời gian |
| 3 | **Trả về báo cáo dạng JSON** | Endpoint REST API chuẩn |
| 4 | **Cung cấp endpoint phục vụ Dashboard** | Giao diện UI hiển thị số liệu trực tiếp |

---

## 3. Các Metric bắt buộc phải thống kê

Theo đề bài (mục 6.5.3), các metric cần có:

| Metric | Mô tả | Nguồn dữ liệu |
|--------|-------|---------------|
| 🚪 **Số lượt ra/vào theo giờ** | Đếm lượt quẹt thẻ vào/ra theo từng khung giờ | B3 Access Gate |
| 🌡️ **Nhiệt độ trung bình theo phòng/khu vực** | Tính trung bình nhiệt độ cảm biến | B1 IoT Ingestion |
| 🚨 **Số cảnh báo trong ngày** | Đếm tổng alert (hỏa hoạn, xâm nhập, v.v.) | B6 Core Business, B7 Notification |
| 📷 **Số lần phát hiện chuyển động** | Đếm camera frame có motion | B2 Camera / B4 AI Vision |
| ⚠️ **Số event bất thường** | Đếm các sự kiện bị từ chối hoặc bất thường | B3, B4, B6 |

**Đầu ra JSON mẫu theo đề bài:**
```json
{
  "date": "2026-05-02",
  "total_access": 120,
  "total_alerts": 5,
  "avg_temperature": 30.8
}
```

---

## 4. Service cần kết nối (bắt buộc theo đề bài)

| Service | Mục đích kết nối | Phương thức | Trạng thái |
|---------|-----------------|-------------|-----------|
| **B1 IoT Ingestion** | Lấy dữ liệu cảm biến (nhiệt độ, độ ẩm, CO₂) | MQTT Subscribe | ✅ Đang kết nối |
| **B2 Camera Stream** | Lấy dữ liệu camera event | Webhook POST `/analytics/camera-events` | ✅ Đang nhận |
| **B3 Access Gate** | Lấy dữ liệu lượt ra/vào | Webhook POST `/api/v1/ingest/access` | ✅ Đang nhận |
| **B4 AI Vision** | Lấy dữ liệu phát hiện đối tượng/khuôn mặt | Webhook POST `/api/v1/analytics/vision` | ✅ Đang nhận |
| **B6 Core Business** | Lấy dữ liệu cảnh báo/quyết định nghiệp vụ | Webhook POST `/analytics/export` | ✅ Đang nhận |
| **B7 Notification** | Lấy log thông báo khẩn cấp đã gửi | HTTP GET Pull mỗi 30 giây | ✅ Đang kéo |

> 💡 **Lưu ý**: Đề bài yêu cầu kết nối **ít nhất một service khác**. B5 đã kết nối **tất cả 6 service** trong Product B.

---

## 5. Log minh chứng kết nối thực tế

Khi báo cáo, B5 sẽ trình bày log console của container để chứng minh kết nối thực tế:

```text
# B1 IoT Ingestion (qua MQTT)
💾 [Nhận từ B1 IoT Ingestion] Thiết bị iot-room-101 | Nhiệt độ: 30.5°C | Độ ẩm: 62.0% | Lưu thành công vào database B5

# B2 Camera Stream (Webhook)
🔥 [Nhận từ B2 Camera Stream] Webhook từ Camera CAM-001 - Phát hiện 2 đối tượng ['person'] - Mức độ: MEDIUM | Lưu vào database B5

# B3 Access Gate (Webhook)
🚪 [Nhận từ B3 Access Gate] Sự kiện quẹt thẻ tại cổng lab-a101 | Chiều: IN | Trạng thái: Cho phép | Lưu vào database B5

# B4 AI Vision (Webhook)
👁️ [Nhận từ B4 AI Vision] Nhận diện VẬT THỂ từ Camera CAM-001 - Phát hiện 3 đối tượng - Mức độ rủi ro: LOW | Lưu vào database B5

# B6 Core Business (Webhook)
📦 [Nhận từ B6 Core Business] Webhook xuất báo cáo chứa 5 bản ghi cảnh báo | Lưu vào database B5

# B7 Notification (Pull)
🔄 [B5 -> B7] Đang kéo cảnh báo từ B7 Notification Service tại http://26.177.175.21:8000/api/v1/alerts/logs?limit=50...
📩 [Nhận từ B7 Notification] Kéo thành công 50 thông báo khẩn cấp | Bắt đầu lưu vào database B5...
💾 [Lưu Database B5] Đã lưu 50 cảnh báo mới từ B7 vào bảng campus_logs (Bỏ qua 0 trùng lặp)

# Dashboard API phục vụ Frontend
📊 [BFF API] Cập nhật Live Stats | Lượt ra vào: 590 | Nhiệt độ TB: 30.5°C | Cảnh báo: 53 | Chuyển động: 10
```

---

## 6. Artefact bắt buộc phải nộp

### 6.1 File kỹ thuật trong repo

| File/Thư mục | Bắt buộc | Vị trí | Trạng thái |
|-------------|----------|--------|-----------|
| `README.md` | ✅ | Root | Cần kiểm tra đủ 10 mục |
| `openapi.yaml` | ✅ | Root | ✅ Có |
| `service_boundary.md` | ✅ | Root | ✅ Có |
| `Dockerfile` | ✅ | Root | ✅ Có |
| `docker-compose.yml` | ✅ | Root | ✅ Có |
| `.env.example` | ✅ | Root | ✅ Có |
| `RUN_COMPOSE.md` | ✅ | Root | ✅ Có |
| `postman/collections/` | ✅ | postman/ | ✅ Có |
| `requirements.txt` | ✅ | Root | ✅ Có |

### 6.2 Minh chứng vận hành

| Minh chứng | Bắt buộc | Ghi chú |
|-----------|----------|---------|
| Log container chạy thành công | ✅ | `docker logs analytics-api` |
| Screenshot Dashboard hiển thị metric | ✅ | Chụp màn hình UI |
| Test report Postman/Newman | ✅ | Kết quả newman đã chạy: **4 requests, 8 assertions, 0 failed** |
| Minh chứng kết nối với service khác | ✅ | Log nhận webhook từ B3, B6, B7... |
| Video demo ngắn 2–3 phút | ✅ | **Cần quay trước buổi bảo vệ** |

---

## 7. Kết quả kiểm thử Postman (Newman)

Đã chạy thành công bộ test tích hợp:

```
B5 Analytics API Tests (Full Coverage)

→ 1. Health Check (Happy Path)
  GET http://localhost:8000/health [200 OK, 43ms]
  √  Mã trạng thái là 200 OK
  √  Database đã kết nối

→ 2. B3 Access Gate - Dữ liệu chuẩn (Happy Path)
  POST http://localhost:8000/api/v1/ingest/access [202 Accepted, 88ms]
  √  Mã trạng thái là 202 Accepted
  √  Báo cáo nhận thành công

→ 3. B3 Access Gate - Thiếu trường bắt buộc (Negative Case)
  POST http://localhost:8000/api/v1/ingest/access [422 Unprocessable Entity, 6ms]
  √  Mã trạng thái là 422 Unprocessable Entity
  √  Hệ thống báo lỗi thiếu dữ liệu

→ 4. B6 Export - Dữ liệu chuẩn (Happy Path)
  POST http://localhost:8000/analytics/export [201 Created, 102ms]
  √  Mã trạng thái là thành công (201 Created)
  √  Lưu thành công dữ liệu từ B6

Tổng kết:
  - Requests:   4 executed / 0 failed
  - Assertions: 8 passed   / 0 failed
  - Thời gian:  557ms tổng (avg 59ms/request)
```

---

## 8. Yêu cầu README.md (10 mục bắt buộc)

Theo đề bài (mục 7), `README.md` phải có đủ **10 mục** sau:

- [x] **1. Tên service** — Analytics Service (Nhóm B5, Product B)
- [x] **2. Vai trò** trong hệ thống Smart Campus
- [x] **3. Thành viên nhóm** và phân vai
- [x] **4. Công nghệ sử dụng** — Python, FastAPI, TimescaleDB, Docker, React
- [x] **5. Cách chạy local** — Hướng dẫn từng bước
- [x] **6. Cách chạy bằng Docker** — `docker compose up --build`
- [x] **7. Danh sách endpoint chính** — Tất cả REST API endpoints
- [x] **8. Service upstream/downstream** — Ai gọi B5, B5 gọi ai
- [x] **9. Link Postman Collection** hoặc hướng dẫn chạy test
- [ ] **10. Minh chứng demo** — **Cần thêm link video hoặc screenshot**

---

## 9. Tiêu chí chấm điểm (Trọng số)

| Tiêu chí | Trọng số | Yêu cầu để đạt điểm tốt |
|----------|----------|------------------------|
| 🗺️ **Phân tích service boundary** | 10% | Sơ đồ rõ, xác định đủ input/output/upstream/downstream |
| 📄 **Hợp đồng API (OpenAPI)** | 20% | `openapi.yaml` rõ ràng, có schema, example, error model, auth |
| 🧪 **Kiểm thử tích hợp (Postman)** | 15% | Happy path + Negative + Auth + Boundary, có report |
| 🐳 **Công nghệ nền tảng (Docker)** | 20% | Dockerfile + Compose + .env + healthcheck + chạy từ repo sạch |
| 🔗 **Kết nối liên service** | 20% | Bắt tay với ít nhất 1 service khác, có minh chứng end-to-end |
| 🎤 **Trình bày và bảo vệ** | 15% | Giải thích được quyết định kiến trúc, trả lời phản biện |

**Tổng: 100%**

---

## 10. Rubric chi tiết — Điều kiện đạt từng mức

### Service Boundary (10%)
| Mức | Yêu cầu |
|-----|---------|
| ✅ **Tốt** | Sơ đồ rõ, xác định đủ input/output/upstream/downstream/data owner |
| ⚠️ **Đạt** | Có sơ đồ nhưng còn thiếu một số quan hệ |
| ❌ **Chưa đạt** | Sơ đồ mơ hồ, service bị cô lập |

### OpenAPI Contract (20%)
| Mức | Yêu cầu |
|-----|---------|
| ✅ **Tốt** | Có schema, status code, example, error model, auth |
| ⚠️ **Đạt** | Có endpoint chính nhưng thiếu example hoặc error model |
| ❌ **Chưa đạt** | Không có openapi.yaml hoặc spec sai nhiều |

### Testing (15%)
| Mức | Yêu cầu |
|-----|---------|
| ✅ **Tốt** | Có happy path, negative, auth, boundary, có report |
| ⚠️ **Đạt** | Có test cơ bản nhưng chưa đủ phủ lỗi |
| ❌ **Chưa đạt** | Không có test hoặc chỉ test thủ công bằng trình duyệt |

### Docker/Compose (20%)
| Mức | Yêu cầu |
|-----|---------|
| ✅ **Tốt** | Chạy được từ repo sạch, có env, healthcheck, compose |
| ⚠️ **Đạt** | Có Dockerfile nhưng hướng dẫn còn thiếu |
| ❌ **Chưa đạt** | Không chạy được bằng Docker |

### Integration (20%)
| Mức | Yêu cầu |
|-----|---------|
| ✅ **Tốt** | Kết nối được với ít nhất 1 service khác, có log/screenshot/video end-to-end |
| ⚠️ **Đạt** | Có mô phỏng kết nối nhưng chưa ổn định |
| ❌ **Chưa đạt** | Service chạy đơn lẻ, không kết nối được |

---

## 11. Demo Pack cuối kỳ — Checklist đầy đủ

Theo mục 11 của đề bài, **Demo Pack** phải có đầy đủ:

- [x] `README.md` mô tả service (đủ 10 mục)
- [x] **Service Boundary Diagram** (`service_boundary.md`)
- [x] `openapi.yaml` đầy đủ
- [ ] **Endpoint Catalog** — Cần tạo file `docs/endpoint_catalog.md`
- [x] **Postman Collection** (`postman/collections/b5_analytics_test.json`)
- [x] **Test report Newman** — 8 assertions, 0 failed ✅
- [x] **Source code** (GitHub repo)
- [x] `Dockerfile`
- [x] `.env.example`
- [x] `docker-compose.yml`
- [x] **Log service chạy thành công** (docker logs)
- [x] **Minh chứng kết nối với service khác** (log B3, B6, B7)
- [ ] **Slide kiến trúc** — Cần chuẩn bị
- [ ] **Video demo 2–3 phút** — Cần quay

---

## 12. Những điểm cần đặc biệt chú ý khi báo cáo

### 12.1 Câu hỏi phản biện giảng viên hay hỏi

> **"Tại sao dùng TimescaleDB thay vì PostgreSQL thường?"**

→ TimescaleDB là extension của PostgreSQL tối ưu cho dữ liệu time-series (sensor, log theo thời gian). Hỗ trợ **hypertable** cho phép phân mảnh tự động theo thời gian, truy vấn theo khoảng thời gian hiệu quả hơn.

---

> **"Nếu B7 offline thì sao? Dữ liệu có mất không?"**

→ B5 dùng cơ chế **pull-based** mỗi 30 giây. Nếu B7 offline, B5 log rõ nguyên nhân (`ConnectionError` / `Timeout`) và thử lại sau 30 giây. Khi B7 online trở lại, B5 kéo đủ log mới nhất. Dữ liệu không mất vì B7 giữ log ở phía mình.

---

> **"Service boundary của B5 là gì — B5 có phát sinh cảnh báo không?"**

→ B5 **không phát sinh cảnh báo**. B5 chỉ **tổng hợp và hiển thị**. B5 là **consumer thuần túy** đối với B1/B2/B3/B4/B6. Việc phát cảnh báo là trách nhiệm của B6 (Core Business) và B7 (Notification).

---

> **"Làm sao chứng minh B5 kết nối được với các service khác?"**

→ Demo trực tiếp bằng cách:
1. Mở Dashboard tại `http://localhost:5173/`
2. Xem bộ đếm "Lượt ra vào" tăng real-time khi B3 gửi webhook
3. Xem bộ đếm "Cảnh báo" tăng khi B6/B7 gửi dữ liệu
4. Show `docker logs analytics-api` — thấy log nhận từng nhóm

---

## 13. Công nghệ sử dụng (cho Slide kiến trúc)

| Lớp | Công nghệ |
|-----|-----------|
| **Backend API** | Python 3.11 + FastAPI + Uvicorn |
| **Database** | TimescaleDB (PostgreSQL 15 + TimescaleDB extension) |
| **Message Queue** | MQTT (kết nối với Broker của B1) |
| **Frontend** | React + Vite + Recharts + TailwindCSS |
| **Container** | Docker + Docker Compose (multi-stage build) |
| **API Design** | OpenAPI 3.1 (openapi.yaml) |
| **Testing** | Postman + Newman |
| **VPN** | Radmin VPN (kết nối các nhóm trong mạng nội bộ) |

---

## 14. Tóm tắt trạng thái hiện tại của B5

| Hạng mục | Trạng thái | Ghi chú |
|----------|-----------|---------|
| FastAPI backend với 10+ REST endpoints | ✅ Hoàn thành | Chạy ổn định |
| TimescaleDB với 4 bảng | ✅ Hoàn thành | sensor_events, gate_events, camera_frames, campus_logs |
| Dashboard React.js realtime (3 giây/lần) | ✅ Hoàn thành | http://localhost:5173 |
| Nhận webhook từ B2, B3, B4, B6 | ✅ Đang nhận live | Log xác nhận |
| MQTT từ B1 | ✅ Hoạt động | mqtt_subscriber.py |
| Pull thông báo từ B7 mỗi 30 giây | ✅ Hoạt động | Kéo được 50 bản ghi |
| Dockerfile + docker-compose.yml | ✅ Hoàn thành | Multi-stage build |
| openapi.yaml | ✅ Có | Cần cập nhật thêm endpoint mới |
| Postman Test + Newman Report | ✅ Pass 100% | 8/8 assertions |
| Video demo | ❌ Chưa có | **Cần quay trước buổi bảo vệ** |
| Slide kiến trúc | ❌ Chưa có | **Cần chuẩn bị** |
| Endpoint Catalog | ❌ Chưa có | **Cần tạo file** |
