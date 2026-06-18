import React from 'react';
import { Cpu, Sun, Moon } from 'lucide-react';

export default function Header({ apiStatus, lastUpdated, theme, onToggleTheme, timeRange, onChangeTimeRange }) {
  return (
    <header className="bg-card-base/80 backdrop-blur-md border border-border-base p-5 rounded-3xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-2xl relative overflow-hidden">
      {/* Decorative vertical gradient bar */}
      <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-cyan-400 to-indigo-600"></div>

      <div className="flex items-center gap-4 pl-2">
        <div className="bg-gradient-to-tr from-cyan-500/20 to-indigo-500/20 text-cyan-400 p-3.5 rounded-2xl border border-cyan-500/30">
          <Cpu className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">
            Smart Campus Operations Platform
          </h1>
          <p className="text-xs text-text-muted font-medium tracking-widest uppercase flex items-center gap-1.5 mt-1">
            <span className="h-2 w-2 rounded-full bg-indigo-500 animate-ping"></span>
            Product B — Analytics Dashboard
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 self-stretch md:self-auto justify-end">
        {/* Time Filter Select */}
        <select
          value={timeRange}
          onChange={(e) => onChangeTimeRange(e.target.value)}
          className="bg-bg-base border border-border-base rounded-2xl px-3 py-1.5 text-xs font-bold text-text-base focus:outline-none focus:ring-1 focus:ring-cyan-500 cursor-pointer transition-all duration-300 hover:border-cyan-500/50"
        >
          <option value="today">Hôm nay</option>
          <option value="7days">7 ngày qua</option>
          <option value="30days">30 ngày qua</option>
        </select>

        <div className="flex items-center gap-2 px-3.5 py-1.5 bg-bg-base border border-border-base rounded-2xl text-xs font-bold text-text-base">
          <span className={`h-2.5 w-2.5 rounded-full animate-pulse ${
            apiStatus === 'connected' ? 'bg-emerald-500' :
            apiStatus === 'loading' ? 'bg-amber-500' : 'bg-rose-500'
          }`}></span>
          BFF API Status:{' '}
          <span className={`ml-1 ${
            apiStatus === 'connected' ? 'text-emerald-400' :
            apiStatus === 'loading' ? 'text-amber-400' : 'text-rose-500'
          }`}>
            {apiStatus === 'connected' ? 'Kết nối' :
             apiStatus === 'loading' ? 'Đang tải' : 'Lỗi API'}
          </span>
        </div>
        
        {/* Toggle Theme Button */}
        <button
          onClick={onToggleTheme}
          className="p-2.5 rounded-2xl bg-bg-base hover:bg-border-base text-text-muted hover:text-text-base transition-all border border-border-base cursor-pointer"
          title="Đổi giao diện Sáng/Tối"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-500" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-500" />
          )}
        </button>

        <div className="text-[10px] text-text-muted font-mono pl-1">
          Cập nhật: {lastUpdated || '--:--:--'}
        </div>
      </div>
    </header>
  );
}
