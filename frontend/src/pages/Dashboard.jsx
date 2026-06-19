import React, { useState, useEffect, useRef } from 'react';
import { Users, Thermometer, AlertTriangle, Camera } from 'lucide-react';
import Header from '../components/Header';
import StatCard from '../components/StatCard';
import CampusChart from '../components/CampusChart';
import LogDetailsModal from '../components/LogDetailsModal';
import { fetchDashboardLive, fetchDashboardLogs } from '../services/apiService';

const serviceNames = {
  b1_iot: 'B1 IoT Cảm biến',
  b2_camera: 'B2 Camera Stream',
  b3_access: 'B3 Cổng kiểm soát',
  b4_vision: 'B4 AI Vision',
  b6_core: 'B6 Nghiệp vụ chính',
  b7_notification: 'B7 Cảnh báo'
};

const translateSource = (src) => {
  const mapping = {
    "B6_CORE": "Nghiệp vụ B6",
    "B7_NOTIFICATION": "Thông báo B7",
    "B4_VISION": "AI Vision B4"
  };
  return mapping[src] || src;
};

const translateType = (type) => {
  const mapping = {
    "FIRE_ALARM": "Báo cháy",
    "ACCESS": "Kiểm soát ra vào",
    "NOTIFICATION": "Thông báo",
    "SYSTEM_ALERT": "Cảnh báo hệ thống"
  };
  if (mapping[type]) return mapping[type];
  if (type && type.toUpperCase().includes("HỎA HOẠN")) return "Báo cháy";
  if (type && type.toUpperCase().includes("TRUY CẬP")) return "Cảnh báo ra vào";
  return type;
};

const SkeletonCard = () => (
  <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden animate-pulse min-h-[140px] flex flex-col justify-between transition-colors duration-300">
    <div className="flex justify-between items-start">
      <div className="space-y-2.5 w-2/3">
        <div className="h-3.5 bg-border-base/50 rounded-md w-full"></div>
        <div className="h-3 bg-border-base/50 rounded-md w-1/2"></div>
      </div>
      <div className="h-10 w-10 bg-border-base/50 rounded-2xl"></div>
    </div>
    <div className="h-8 bg-border-base/50 rounded-lg w-1/3 mt-4"></div>
  </div>
);

export default function Dashboard() {
  const [data, setData] = useState({
    system_health: {
      b1_iot: 'online',
      b2_camera: 'online',
      b3_access: 'online',
      b4_vision: 'online',
      b6_core: 'online',
      b7_notification: 'online'
    },
    summary_stats: {
      total_access: 0,
      avg_temp: 0.0,
      total_alerts: 0,
      camera_detections: 0
    },
    chart_data: {
      temperature_history: [],
      access_by_gate: []
    },
    recent_alerts: []
  });
  const [apiStatus, setApiStatus] = useState('loading'); // 'loading' | 'connected' | 'error'
  const [lastUpdated, setLastUpdated] = useState('');
  const [timeRange, setTimeRange] = useState('today');
  const [b5Offline, setB5Offline] = useState(false);
  const [toasts, setToasts] = useState([]);
  
  // States quản lý drill-down Slide-over logs
  const [activeModal, setActiveModal] = useState(null);
  const [modalLogs, setModalLogs] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);
  const activeModalRef = useRef(null);

  // Sync ref để tránh stale closure trong hàm setInterval
  useEffect(() => {
    activeModalRef.current = activeModal;
  }, [activeModal]);

  // Quản lý theme Sáng/Tối
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');

  const prevHealthRef = useRef({
    b1_iot: 'online',
    b2_camera: 'online',
    b3_access: 'online',
    b4_vision: 'online',
    b6_core: 'online',
    b7_notification: 'online'
  });

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    localStorage.setItem('theme', nextTheme);
  };

  // Đồng bộ class "dark" lên thẻ html
  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.classList.remove('dark');
    } else {
      document.documentElement.classList.add('dark');
    }
  }, [theme]);

  // Hàm tạo Toast thông báo
  const showToast = (message) => {
    const id = Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    setToasts((t) => [...t, { id, message }]);
    setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id));
    }, 4000);
  };

  // Hàm lấy dữ liệu và cập nhật state từ BFF API
  const loadData = async (isFirstLoad = false) => {
    if (isFirstLoad) {
      setApiStatus('loading');
    }
    
    // Gửi song song yêu cầu dữ liệu Dashboard Live và Logs chi tiết (nếu có)
    const promises = [fetchDashboardLive(timeRange)];
    const currentActiveModal = activeModalRef.current;
    if (currentActiveModal) {
      promises.push(fetchDashboardLogs(currentActiveModal));
    }

    try {
      const results = await Promise.all(promises);
      const liveResult = results[0];
      const logsResult = results[1]; // Sẽ nhận về kết quả hoặc undefined

      setData(liveResult);
      if (logsResult) {
        setModalLogs(logsResult);
      }

      setApiStatus('connected');
      setB5Offline(false);
      
      const now = new Date();
      setLastUpdated(now.toLocaleTimeString('vi-VN'));

      // Kiểm tra trạng thái offline của các nhóm khác để báo Toast
      if (liveResult && liveResult.system_health) {
        Object.keys(liveResult.system_health).forEach((key) => {
          const prevStatus = prevHealthRef.current[key];
          const currentStatus = liveResult.system_health[key];
          if (prevStatus === 'online' && currentStatus === 'offline') {
            showToast(`Không lấy được dữ liệu từ nhóm ${key.substring(0, 2).toUpperCase()}`);
          }
        });
        prevHealthRef.current = liveResult.system_health;
      }
    } catch (error) {
      console.error("Lỗi đồng bộ dữ liệu Dashboard:", error);
      setApiStatus('error');
      setB5Offline(true); // Kích hoạt overlay mất kết nối BFF máy chủ
    }
  };

  const handleOpenModal = async (category) => {
    setActiveModal(category);
    setModalLoading(true);
    try {
      const logsResult = await fetchDashboardLogs(category);
      setModalLogs(logsResult);
    } catch (err) {
      console.error("Lỗi khi tải chi tiết logs:", err);
    } finally {
      setModalLoading(false);
    }
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setModalLogs([]);
  };

  const handleRefreshModalLogs = async () => {
    if (!activeModal) return;
    setModalLoading(true);
    try {
      const logsResult = await fetchDashboardLogs(activeModal);
      setModalLogs(logsResult);
    } catch (err) {
      console.error("Lỗi khi làm mới logs:", err);
    } finally {
      setModalLoading(false);
    }
  };

  useEffect(() => {
    // Gọi API lần đầu tiên
    loadData(true);

    // Thiết lập vòng lặp cập nhật mỗi 3 giây
    const interval = setInterval(() => {
      loadData(false);
    }, 3000);

    return () => clearInterval(interval);
  }, [timeRange]); // reload lại luồng polling khi timeRange đổi

  /* ==========================================================================
     MOCK DATA FALLBACK REMOVED & SYSTEM HEALTH RECONFIGURED
     All services are set to 'offline' (Red / Mất kết nối) if the BFF API is unreachable.
     ========================================================================== */
  const systemHealth = (apiStatus === 'error' || !data || !data.system_health) ? {
    b1_iot: 'offline',
    b2_camera: 'offline',
    b3_access: 'offline',
    b4_vision: 'offline',
    b6_core: 'offline',
    b7_notification: 'offline'
  } : data.system_health;


  return (
    <div className="p-6 max-w-[1600px] mx-auto w-full space-y-6 z-10 relative">
      <style>{`
        @keyframes slideIn {
          from { transform: translateY(100px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-slide-in {
          animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>

      {/* Header */}
      <Header 
        apiStatus={apiStatus} 
        lastUpdated={lastUpdated} 
        theme={theme}
        onToggleTheme={toggleTheme}
        timeRange={timeRange}
        onChangeTimeRange={setTimeRange}
      />

      {/* System Health Status Bar */}
      <div className="bg-card-base border border-border-base p-4 rounded-3xl shadow-xl flex flex-wrap gap-4 items-center justify-between transition-colors duration-300">
        <div className="flex items-center gap-2 pl-1">
          <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse"></span>
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">Trạng thái kết nối dịch vụ:</span>
        </div>
        <div className="flex flex-wrap gap-2.5">
          {Object.entries(systemHealth).map(([key, status]) => {
            const isOnline = status === 'online';
            return (
              <div 
                key={key} 
                className={`flex items-center gap-1.5 px-3.5 py-1 rounded-2xl border text-xs font-bold transition-all duration-300 ${
                  isOnline 
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                    : 'bg-rose-500/10 border-rose-500/20 text-rose-400 animate-pulse'
                }`}
              >
                <span className={`h-1.5 w-1.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-rose-400 animate-ping'}`}></span>
                <span>{serviceNames[key] || key}: {isOnline ? 'OK' : 'Mất kết nối'}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Grid chứa 4 thẻ StatCard với Skeleton loading */}
      {apiStatus === 'loading' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <StatCard
            title="Lượt ra vào"
            value={apiStatus === 'error' ? undefined : data?.summary_stats?.total_access}
            type="students"
            icon={Users}
            description="Tích hợp luồng Access Gate (B3)"
            onClick={() => handleOpenModal('students')}
          />
          <StatCard
            title="Nhiệt độ trung bình"
            value={apiStatus === 'error' ? undefined : data?.summary_stats?.avg_temp}
            type="temp"
            icon={Thermometer}
            description="Quét từ cảm biến IoT (B1)"
            onClick={() => handleOpenModal('temp')}
          />
          <StatCard
            title="Cảnh báo bất thường"
            value={apiStatus === 'error' ? undefined : data?.summary_stats?.total_alerts}
            type="alerts"
            icon={AlertTriangle}
            description="Sự kiện khẩn cấp từ B6 Logs"
            onClick={() => handleOpenModal('alerts')}
          />
          <StatCard
            title="Nhận diện Camera"
            value={apiStatus === 'error' ? undefined : data?.summary_stats?.camera_detections}
            type="camera"
            icon={Camera}
            description="Kéo dữ liệu frames từ B2"
            onClick={() => handleOpenModal('camera')}
          />
        </div>
      )}

      {/* Biểu đồ Recharts sử dụng dữ liệu thực */}
      <CampusChart 
        theme={theme} 
        temperatureHistory={data?.chart_data?.temperature_history}
        accessByGate={data?.chart_data?.access_by_gate}
      />

      {/* Bảng Luồng Cảnh báo (Live Alerts Feed) */}
      <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden transition-colors duration-300">
        <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-text-base flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500 animate-pulse" />
              Luồng cảnh báo trực tiếp (Live Alerts Feed)
            </h3>
            <p className="text-xs text-text-muted mt-1">Các cảnh báo an ninh và lỗi thiết bị thời gian thực trong khuôn viên</p>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border-base text-xs font-bold text-text-muted uppercase">
                <th className="py-3 px-4">Mã số</th>
                <th className="py-3 px-4">Thời gian</th>
                <th className="py-3 px-4">Nguồn phát</th>
                <th className="py-3 px-4">Loại sự kiện</th>
                <th className="py-3 px-4">Mức độ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-base/50 text-xs font-medium text-text-base">
              {data?.recent_alerts && data.recent_alerts.length > 0 ? (
                data.recent_alerts.map((alert) => {
                  const isHigh = alert.severity === 'HIGH';
                  const isMedium = alert.severity === 'MEDIUM';
                  return (
                    <tr key={alert.id} className="hover:bg-bg-base/30 transition-colors duration-200">
                       <td className="py-3.5 px-4 font-mono font-bold text-cyan-400">{alert.id}</td>
                      <td className="py-3.5 px-4 text-text-muted">
                        {new Date(alert.time).toLocaleTimeString('vi-VN')} {new Date(alert.time).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-lg bg-bg-base border border-border-base font-mono text-[10px] text-text-base">
                          {translateSource(alert.source)}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-text-base font-semibold">
                        <div>{translateType(alert.type)}</div>
                        {alert.message && (
                          <div className="text-[10px] text-text-muted mt-0.5 font-normal max-w-sm truncate" title={alert.message}>
                            {alert.message}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-lg text-[10px] font-bold tracking-wider uppercase ${
                          isHigh ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                          isMedium ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                        }`}>
                          {alert.severity}
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-text-muted text-sm">
                    Không có cảnh báo nào trong hệ thống
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Full-screen B5 Offline Overlay */}
      {b5Offline && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/85 backdrop-blur-md transition-all duration-300">
          <div className="text-center space-y-4 max-w-md p-6 bg-slate-900/50 rounded-3xl border border-rose-500/20 shadow-2xl">
            <div className="relative flex items-center justify-center">
              <span className="absolute inline-flex h-16 w-16 rounded-full bg-rose-500/20 animate-ping"></span>
              <span className="relative inline-flex rounded-full h-8 w-8 bg-rose-500 flex items-center justify-center font-bold text-white">!</span>
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white uppercase">Mất kết nối BFF</h2>
            <p className="text-sm text-rose-300/80 font-medium animate-pulse">
              🔴 MẤT KẾT NỐI ĐẾN MÁY CHỦ BFF. ĐANG THỬ KẾT NỐI LẠI...
            </p>
          </div>
        </div>
      )}

      {/* Slide-over Panel Chi tiết Log */}
      <LogDetailsModal
        isOpen={activeModal !== null}
        onClose={handleCloseModal}
        category={activeModal}
        logs={modalLogs}
        loading={modalLoading}
        onRefresh={handleRefreshModalLogs}
      />

      {/* Toast Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div 
            key={toast.id} 
            className="bg-slate-950 border border-rose-500/30 text-rose-200 px-4 py-3 rounded-2xl shadow-2xl flex items-center gap-3 animate-slide-in pointer-events-auto"
          >
            <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 animate-bounce" />
            <span className="text-xs font-semibold">{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
