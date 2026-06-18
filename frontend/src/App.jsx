import React from 'react';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <div className="bg-bg-base text-text-base font-sans min-h-screen flex flex-col justify-between relative overflow-x-hidden transition-colors duration-300">
      {/* Top Background Glow Effects */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-cyan-500/5 dark:bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute top-10 right-1/4 w-96 h-96 bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none"></div>

      {/* Main dashboard content */}
      <main className="flex-grow flex items-center justify-center py-6">
        <Dashboard />
      </main>

      {/* Control Center Footer */}
      <footer className="p-6 text-center border-t border-border-base bg-card-base/30 text-xs text-text-muted w-full z-10 transition-colors duration-300">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row justify-between items-center gap-3">
          <p>© 2026 Smart Campus Operations Center. Bản quyền thuộc về Nhóm B5 - Analytics Service.</p>
          <div className="flex items-center gap-4 font-mono text-[10px]">
            <span>FastAPI 0.100+</span>
            <span>•</span>
            <span>TimescaleDB 15</span>
            <span>•</span>
            <span>ReactJS + Vite</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
