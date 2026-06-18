import React, { useEffect, useRef, useState } from 'react';
import { X, RefreshCw } from 'lucide-react';

export default function LogDetailsModal({ isOpen, onClose, category, logs, loading, onRefresh }) {
  const prevLogsRef = useRef(null);
  const [flashId, setFlashId] = useState(null);

  // Esc Key Listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Flash Highlight detection when new logs arrive
  useEffect(() => {
    if (isOpen && logs && logs.length > 0) {
      if (prevLogsRef.current && prevLogsRef.current.length > 0) {
        const firstPrev = prevLogsRef.current[0];
        const firstCurr = logs[0];
        // If a new log has been prepended or is different
        if (firstPrev.id !== firstCurr.id) {
          setFlashId(firstCurr.id);
          const timer = setTimeout(() => setFlashId(null), 1500);
          return () => clearTimeout(timer);
        }
      }
      prevLogsRef.current = logs;
    } else if (!isOpen) {
      prevLogsRef.current = null;
    }
  }, [logs, isOpen]);

  if (!isOpen) return null;

  // Title translation
  const titles = {
    students: "Chi tiết Lượt ra vào (Access Logs)",
    temp: "Chi tiết Cảm biến Nhiệt độ (IoT Logs)",
    alerts: "Chi tiết Cảnh báo hệ thống (Alert Logs)",
    camera: "Chi tiết Nhận diện Camera (Vision Logs)"
  };

  // Render headers and cells depending on category
  const renderTableContent = () => {
    if (loading && (!logs || logs.length === 0)) {
      return (
        <tr className="border-b border-border-base/30 text-xs font-semibold text-text-muted">
          <td colSpan="4" className="py-20 text-center">
            <div className="flex flex-col items-center gap-3">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <span className="text-sm">Đang tải dữ liệu thực tế từ Database...</span>
            </div>
          </td>
        </tr>
      );
    }

    if (!logs || logs.length === 0) {
      return (
        <tr className="border-b border-border-base/30 text-xs font-semibold text-text-muted">
          <td colSpan="4" className="py-20 text-center text-sm">
            Không tìm thấy bản ghi log nào.
          </td>
        </tr>
      );
    }

    return logs.map((log) => {
      const isFlashed = log.id === flashId;
      const formattedTime = new Date(log.time).toLocaleTimeString('vi-VN') + ' ' + new Date(log.time).toLocaleDateString('vi-VN');

      switch (category) {
        case 'students':
          return (
            <tr 
              key={log.id} 
              className={`border-b border-border-base/30 hover:bg-slate-800/40 transition-colors duration-200 ${isFlashed ? 'animate-highlight-flash' : ''}`}
            >
              <td className="py-3 px-4 text-text-muted font-mono text-[11px]">{formattedTime}</td>
              <td className="py-3 px-4 font-semibold text-text-base">{log.gate}</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${log.direction === 'IN' ? 'bg-indigo-500/10 text-indigo-400' : 'bg-amber-500/10 text-amber-400'}`}>
                  {log.direction}
                </span>
              </td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${log.status === 'Thành công' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400 animate-pulse'}`}>
                  {log.status}
                </span>
              </td>
            </tr>
          );
        case 'temp':
          return (
            <tr 
              key={log.id} 
              className={`border-b border-border-base/30 hover:bg-slate-800/40 transition-colors duration-200 ${isFlashed ? 'animate-highlight-flash' : ''}`}
            >
              <td className="py-3 px-4 text-text-muted font-mono text-[11px]">{formattedTime}</td>
              <td className="py-3 px-4 font-semibold text-text-base">{log.location}</td>
              <td className="py-3 px-4 font-mono text-amber-400 font-bold">{log.temp}°C</td>
              <td className="py-3 px-4 font-mono text-cyan-400">{log.humidity}%</td>
            </tr>
          );
        case 'alerts':
          const isHigh = log.severity === 'HIGH';
          const isMedium = log.severity === 'MEDIUM';
          return (
            <tr 
              key={log.id} 
              className={`border-b border-border-base/30 hover:bg-slate-800/40 transition-colors duration-200 ${isFlashed ? 'animate-highlight-flash' : ''}`}
            >
              <td className="py-3 px-4 text-text-muted font-mono text-[11px]">{formattedTime}</td>
              <td className="py-3 px-4">
                <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 font-mono text-[10px] text-text-base">
                  {log.source}
                </span>
              </td>
              <td className="py-3 px-4 font-semibold text-text-base">{log.type}</td>
              <td className="py-3 px-4">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  isHigh ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                  isMedium ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                  'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                }`}>
                  {log.severity}
                </span>
              </td>
            </tr>
          );
        case 'camera':
          return (
            <tr 
              key={log.id} 
              className={`border-b border-border-base/30 hover:bg-slate-800/40 transition-colors duration-200 ${isFlashed ? 'animate-highlight-flash' : ''}`}
            >
              <td className="py-3 px-4 text-text-muted font-mono text-[11px]">{formattedTime}</td>
              <td className="py-3 px-4 font-semibold text-text-base">{log.camera_id}</td>
              <td className="py-3 px-4 text-purple-400 font-semibold">{log.objects}</td>
              <td className="py-3 px-4 font-mono font-bold text-cyan-400">{log.confidence}%</td>
            </tr>
          );
        default:
          return null;
      }
    });
  };

  const getHeaders = () => {
    switch (category) {
      case 'students':
        return ["Thời gian", "Cổng", "Chiều", "Trạng thái"];
      case 'temp':
        return ["Thời gian", "Vị trí", "Nhiệt độ", "Độ ẩm"];
      case 'alerts':
        return ["Thời gian", "Nguồn", "Phân loại", "Mức độ rủi ro"];
      case 'camera':
        return ["Thời gian", "Camera ID", "Nhận diện", "Độ tin cậy"];
      default:
        return [];
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      <style>{`
        @keyframes highlightFlash {
          0% { background-color: rgba(6, 182, 212, 0.4); }
          100% { background-color: transparent; }
        }
        .animate-highlight-flash {
          animation: highlightFlash 1.5s ease-out;
        }
        @keyframes slideOverIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        .animate-slide-over {
          animation: slideOverIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>

      {/* Slide-over Content Container */}
      <div className="relative w-full max-w-2xl h-full bg-slate-950 border-l border-cyan-500/20 shadow-[0_0_50px_rgba(6,182,212,0.15)] flex flex-col z-10 animate-slide-over">
        {/* Top Glow bar */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-cyan-500 to-purple-500"></div>

        {/* Modal Header */}
        <div className="p-6 border-b border-border-base/30 flex justify-between items-center bg-slate-900/40">
          <div className="space-y-1">
            <h3 className="text-lg font-bold tracking-tight text-white uppercase flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse"></span>
              {titles[category] || "Chi tiết nhật ký"}
            </h3>
            <p className="text-xs text-text-muted">Nhật ký 50 sự kiện mới nhất ghi nhận thời gian thực từ Database</p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={onRefresh}
              disabled={loading}
              title="Làm mới log"
              className="p-2.5 rounded-xl border border-slate-800 text-text-muted hover:text-white hover:border-cyan-500/50 hover:bg-slate-900 active:scale-95 transition-all cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
            <button 
              onClick={onClose}
              title="Đóng cửa sổ (Esc)"
              className="p-2.5 rounded-xl border border-slate-800 text-text-muted hover:text-white hover:border-rose-500/50 hover:bg-slate-900 active:scale-95 transition-all cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Table Body */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-border-base/50 text-xs font-bold text-text-muted uppercase bg-slate-900/10">
                {getHeaders().map((h, i) => (
                  <th key={i} className="py-3 px-4">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border-base/10 text-xs font-medium text-text-base">
              {renderTableContent()}
            </tbody>
          </table>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-border-base/30 bg-slate-950/90 text-right flex justify-between items-center">
          <div className="flex items-center gap-1.5 text-[10px] text-text-muted font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping"></span>
            <span>Đồng bộ tự động mỗi 5 giây</span>
          </div>
          <button 
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-xs font-bold text-text-base transition-all active:scale-95 cursor-pointer shadow-lg hover:shadow-cyan-500/5"
          >
            Đóng bảng
          </button>
        </div>
      </div>
    </div>
  );
}
