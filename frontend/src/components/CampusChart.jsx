import React from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, BarChart3 } from 'lucide-react';

export default function CampusChart({ theme, temperatureHistory = [], accessByGate = [] }) {
  const isDark = theme === 'dark';
  
  const strokeColor = isDark ? '#94a3b8' : '#64748b';
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.06)';
  const tooltipBg = isDark ? '#111522' : '#ffffff';
  const tooltipBorder = isDark ? '#1e2538' : '#cbd5e1';
  const tooltipColor = isDark ? '#e2e8f0' : '#0f172a';

  const isTempEmpty = !temperatureHistory || temperatureHistory.length === 0;
  const isGateEmpty = !accessByGate || accessByGate.length === 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* Biểu đồ 1: Biến thiên nhiệt độ (Line Chart) */}
      <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden min-w-0 flex flex-col justify-between transition-colors duration-300">
        <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-text-base flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-cyan-400" />
              Lịch sử nhiệt độ môi trường
            </h3>
            <p className="text-xs text-text-muted mt-1">Biểu đồ thể hiện sự biến thiên nhiệt độ trung bình từ cảm biến IoT (B1)</p>
          </div>
        </div>
        
        <div className="h-[320px] w-full flex items-center justify-center relative">
          {isTempEmpty ? (
            <div className="text-center py-10">
              <p className="text-sm text-text-muted font-medium">Không có dữ liệu trong khoảng thời gian này</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <LineChart
                data={temperatureHistory}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
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
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: '12px',
                    color: tooltipColor,
                  }}
                  cursor={{ stroke: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)', strokeWidth: 1 }}
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
                <Line 
                  type="monotone" 
                  dataKey="temp" 
                  name="Nhiệt độ (°C)" 
                  stroke="#06b6d4" 
                  strokeWidth={3}
                  activeDot={{ r: 6, fill: '#06b6d4', strokeWidth: 0 }}
                  dot={{ r: 2, strokeWidth: 0, fill: '#06b6d4' }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Biểu đồ 2: Lượt ra vào theo cổng (Bar Chart) */}
      <div className="bg-card-base border border-border-base p-6 rounded-3xl shadow-2xl relative overflow-hidden min-w-0 flex flex-col justify-between transition-colors duration-300">
        <div className="flex justify-between items-center mb-6 flex-wrap gap-2">
          <div>
            <h3 className="text-lg font-bold tracking-tight text-text-base flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-indigo-400" />
              Lượng người ra vào theo cổng
            </h3>
            <p className="text-xs text-text-muted mt-1">Phân bố lưu lượng truy cập thực tế qua các cổng kiểm soát (B3)</p>
          </div>
        </div>
        
        <div className="h-[320px] w-full flex items-center justify-center relative">
          {isGateEmpty ? (
            <div className="text-center py-10">
              <p className="text-sm text-text-muted font-medium">Không có dữ liệu trong khoảng thời gian này</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <BarChart
                data={accessByGate}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis 
                  dataKey="gate" 
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
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: tooltipBg,
                    borderColor: tooltipBorder,
                    borderRadius: '12px',
                    color: tooltipColor,
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
                  fill="#22d3ee" 
                  radius={[6, 6, 0, 0]} 
                  maxBarSize={30}
                />
                <Bar 
                  dataKey="out" 
                  name="Lượt ra (OUT)" 
                  fill="#6366f1" 
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
