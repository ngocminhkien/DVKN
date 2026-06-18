CREATE EXTENSION IF NOT EXISTS timescaledb;
-- Bảng chứa dữ liệu cảm biến IoT (Từ nhóm B1)
CREATE TABLE IF NOT EXISTS sensor_events (
    time TIMESTAMPTZ NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    temperature_c DOUBLE PRECISION,
    humidity_percent DOUBLE PRECISION,
    co2_ppm DOUBLE PRECISION,
    status VARCHAR(50),
    alert_level VARCHAR(50),
    reason VARCHAR(255),
    raw_payload JSONB -- Lưu trữ toàn bộ cục JSON gốc phòng khi cần
);

-- ==========================================
-- Bảng chứa kết quả phân tích Camera (từ B2)
-- ==========================================
CREATE TABLE IF NOT EXISTS camera_frames (
    frame_id VARCHAR(100) PRIMARY KEY,
    camera_id VARCHAR(50),
    accepted BOOLEAN,
    timestamp TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    motion_score FLOAT,
    quality VARCHAR(50),
    detections JSONB -- Lưu mảng nhận diện (người, xe...) dạng JSON
);

-- Chuyển thành siêu bảng (Hypertable) của TimescaleDB để tối ưu truy vấn thời gian
SELECT create_hypertable('sensor_events', 'time', if_not_exists => TRUE);


-- Bảng chứa dữ liệu sự kiện quẹt thẻ và báo cháy (Từ nhóm B6)
CREATE TABLE IF NOT EXISTS campus_logs (
    time TIMESTAMPTZ NOT NULL,
    log_type VARCHAR(50) NOT NULL,
    details JSONB NOT NULL -- Sử dụng JSONB vì bên trong detail của Access và Fire Alarm có các trường khác nhau
);

-- Chuyển thành siêu bảng (Hypertable)
SELECT create_hypertable('campus_logs', 'time', if_not_exists => TRUE);

-- ==========================================
-- Bảng chứa sự kiện quẹt thẻ từ B3 (Access Gate)
-- ==========================================
CREATE TABLE IF NOT EXISTS gate_events (
    time TIMESTAMPTZ NOT NULL,
    event_id VARCHAR(100) NOT NULL,
    gate_id VARCHAR(50),
    direction VARCHAR(10),
    access_granted BOOLEAN,
    person_type VARCHAR(50),
    source_service VARCHAR(50),
    product VARCHAR(50)
);

-- Chuyển thành siêu bảng (Hypertable)
SELECT create_hypertable('gate_events', 'time', if_not_exists => TRUE);