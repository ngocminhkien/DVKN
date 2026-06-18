import React from 'react';

export default function StatCard({ title, value, type, icon: Icon, description, onClick }) {
  // Xác định màu sắc động và hiệu ứng dựa trên giá trị và loại thẻ
  let cardClass = "bg-card-base hover:bg-card-base/90 border border-border-base hover:border-indigo-500/50 glow-blue";
  let iconContainerClass = "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:bg-indigo-500 group-hover:text-card-base";
  let descClass = "text-emerald-500";
  let displayVal = value !== undefined && value !== null ? value.toLocaleString('vi-VN') : '--';
  let descText = description;

  if (type === 'temp') {
    const temp = Number(value) || 0;
    displayVal = value !== undefined && value !== null ? `${temp.toFixed(1)}°C` : '--';
    
    if (temp > 35) {
      // Báo đỏ nếu nhiệt độ vượt quá 35 độ C
      cardClass = "bg-card-base hover:bg-card-base/90 border border-rose-500/50 glow-red animate-pulse";
      iconContainerClass = "bg-rose-500/20 text-rose-500 border border-rose-500/30 group-hover:bg-rose-500 group-hover:text-card-base";
      descClass = "text-rose-500 font-bold";
      descText = "⚠️ CẢNH BÁO QUÁ NHIỆT (>35°C)";
    } else {
      cardClass = "bg-card-base hover:bg-card-base/90 border border-border-base hover:border-amber-500/50 glow-amber";
      iconContainerClass = "bg-amber-500/10 text-amber-400 border border-amber-500/20 group-hover:bg-amber-500 group-hover:text-card-base";
      descClass = "text-amber-500";
    }
  } else if (type === 'alerts') {
    const alertsCount = Number(value) || 0;
    if (alertsCount > 0) {
      cardClass = "bg-card-base hover:bg-card-base/90 border border-rose-500/70 glow-red animate-pulse";
      iconContainerClass = "bg-rose-500/20 text-rose-500 border border-rose-500/30 group-hover:bg-rose-500 group-hover:text-card-base";
      descClass = "text-rose-500 font-semibold";
    } else {
      cardClass = "bg-card-base hover:bg-card-base/90 border border-border-base hover:border-rose-500/50 glow-red";
      iconContainerClass = "bg-rose-500/10 text-rose-400 border border-rose-500/20 group-hover:bg-rose-500 group-hover:text-card-base";
      descClass = "text-rose-400";
    }
  } else if (type === 'camera') {
    cardClass = "bg-card-base hover:bg-card-base/90 border border-border-base hover:border-purple-500/50 glow-purple";
    iconContainerClass = "bg-purple-500/10 text-purple-400 border border-purple-500/20 group-hover:bg-purple-500 group-hover:text-card-base";
    descClass = "text-purple-500";
  }

  return (
    <div 
      onClick={onClick}
      className={`p-5 rounded-3xl transition-all duration-300 transform hover:-translate-y-1 hover:scale-[1.02] active:scale-[0.98] shadow-lg group relative overflow-hidden cursor-pointer select-none ${cardClass}`}
    >
      {/* Background soft glow decoration */}
      <div className="absolute -right-3 -top-3 w-16 h-16 bg-white/3 rounded-full group-hover:scale-150 transition-all duration-500"></div>
      
      <div className="flex justify-between items-start">
        <div>
          <span className="text-xs font-bold text-text-muted uppercase tracking-wider block">
            {title}
          </span>
          <span className="text-4xl font-black tracking-tight text-text-base mt-3 block">
            {displayVal}
          </span>
        </div>
        <div className={`p-3 rounded-2xl transition-all duration-300 shadow-md ${iconContainerClass}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className={`mt-4 flex items-center gap-1.5 text-[11px] ${descClass}`}>
        <span>{descText}</span>
      </div>
    </div>
  );
}
