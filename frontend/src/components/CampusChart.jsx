import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';

export default function CampusChart({ theme, temperatureHistory = [], accessByGate = [] }) {
  const isDark = theme === 'dark';
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);
  
  const strokeColor = isDark ? '#94a3b8' : '#64748b';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.06)';
  const tooltipBg = isDark ? 'rgba(17, 21, 34, 0.85)' : 'rgba(255, 255, 255, 0.9)';
  const tooltipBorder = isDark ? 'rgba(6, 182, 212, 0.2)' : 'rgba(203, 213, 225, 0.8)';
  const tooltipColor = isDark ? '#e2e8f0' : '#0f172a';

  if (!mounted) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full animate-pulse">
        <div className="bg-card-base border border-border-base p-6 rounded-3xl h-[440px] flex items-center justify-center">
          <p className="text-sm text-text-muted font-medium">Đang tải biểu đồ...</p>
        </div>
        <div className="bg-card-base border border-border-base p-6 rounded-3xl h-[440px] flex items-center justify-center">
          <p className="text-sm text-text-muted font-medium">Đang tải biểu đồ...</p>
        </div>
      </div>
    );
  }

  // Augment temperatureHistory if there's only 1 point to prevent single dot issue
  let displayTempHistory = temperatureHistory;
  if (temperatureHistory && temperatureHistory.length === 1) {
    const singlePoint = temperatureHistory[0];
    displayTempHistory = [
      {
        time: "Trước đó",
        temp: singlePoint.temp
      },
      singlePoint
    ];
  }

  const translateGateName = (gateId) => {
    const mapping = {
      'lab-a101': 'Lab A101',
      'gate-a': 'Cổng A',
      'gate-main': 'Cổng Chính',
    };
    return mapping[gateId] || gateId;
  };

  const displayAccessByGate = (accessByGate || []).map(item => ({
    ...item,
    gateDisplayName: translateGateName(item.gate)
  }));

  const isTempEmpty = !displayTempHistory || displayTempHistory.length === 0;
  const isGateEmpty = !displayAccessByGate || displayAccessByGate.length === 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* Biểu đồ 1: Biến thiên nhiệt độ (Area Chart) */}
      <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden min-w-0 flex flex-col justify-between transition-colors duration-300">
        {/* Glow effect in background */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
        
        <div className="flex justify-between items-center mb-6 flex-wrap gap-2 z-10">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-text-base flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              Lịch sử nhiệt độ môi trường
            </h3>
            <p className="text-xs text-text-muted mt-1">Biểu đồ thể hiện sự biến thiên nhiệt độ trung bình từ cảm biến IoT (B1)</p>
          </div>
        </div>
        
        <div className="h-[320px] w-full relative">
          {isTempEmpty ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center py-10">
                <p className="text-sm text-text-muted font-medium">Không có dữ liệu trong khoảng thời gian này</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={displayTempHistory}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.01}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke={strokeColor} 
                  fontSize={11}
                  tickLine={false} 
                  axisLine={false}
                />
                <YAxis 
                  stroke={strokeColor} 
                  fontSize={11}
                  tickLine={false} 
                  axisLine={false}
                  domain={['dataMin - 2', 'dataMax + 2']}
                  tickFormatter={(value) => `${value}°C`}
                />
                <Tooltip
                  formatter={(value) => [`${value}°C`, 'Nhiệt độ']}
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: '16px',
                    color: tooltipColor,
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)'
                  }}
                  cursor={{ stroke: isDark ? 'rgba(6, 182, 212, 0.1)' : 'rgba(0, 0, 0, 0.05)', strokeWidth: 1 }}
                />
                <Legend 
                  verticalAlign="top" 
                  height={36} 
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{
                    fontSize: '11px',
                    color: strokeColor,
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="temp" 
                  name="Nhiệt độ (°C)" 
                  stroke="#06b6d4" 
                  strokeWidth={3}
                  fill="url(#tempGradient)"
                  activeDot={{ r: 6, fill: '#06b6d4', stroke: '#ffffff', strokeWidth: 2 }}
                  dot={{ r: 5, stroke: '#06b6d4', strokeWidth: 2, fill: isDark ? '#111522' : '#ffffff' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Biểu đồ 2: Lượt ra vào theo cổng (Bar Chart) */}
      <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden min-w-0 flex flex-col justify-between transition-colors duration-300">
        {/* Glow effect in background */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex justify-between items-center mb-6 flex-wrap gap-2 z-10">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-text-base flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
              Lượng người ra vào theo cổng
            </h3>
            <p className="text-xs text-text-muted mt-1">Phân bố lưu lượng truy cập thực tế qua các cổng kiểm soát (B3)</p>
          </div>
        </div>
        
        <div className="h-[320px] w-full relative">
          {isGateEmpty ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center py-10">
                <p className="text-sm text-text-muted font-medium">Không có dữ liệu trong khoảng thời gian này</p>
              </div>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={displayAccessByGate}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="inBarGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22d3ee"/>
                    <stop offset="100%" stopColor="#06b6d4"/>
                  </linearGradient>
                  <linearGradient id="outBarGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8"/>
                    <stop offset="100%" stopColor="#6366f1"/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis 
                  dataKey="gateDisplayName" 
                  stroke={strokeColor} 
                  fontSize={11}
                  tickLine={false} 
                  axisLine={false}
                />
                <YAxis 
                  stroke={strokeColor} 
                  fontSize={11}
                  tickLine={false} 
                  axisLine={false}
                  tickFormatter={(value) => `${value} lượt`}
                />
                <Tooltip
                  formatter={(value, name) => [`${value} lượt`, name]}
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: '16px',
                    color: tooltipColor,
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)'
                  }}
                  cursor={{ fill: isDark ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)' }}
                />
                <Legend 
                  verticalAlign="top" 
                  height={36} 
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{
                    fontSize: '11px',
                    color: strokeColor,
                  }}
                />
                <Bar 
                  dataKey="in" 
                  name="Lượt vào (IN)" 
                  fill="url(#inBarGradient)" 
                  radius={[6, 6, 0, 0]} 
                  maxBarSize={30}
                />
                <Bar 
                  dataKey="out" 
                  name="Lượt ra (OUT)" 
                  fill="url(#outBarGradient)" 
                  radius={[6, 6, 0, 0]} 
                  maxBarSize={30}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
