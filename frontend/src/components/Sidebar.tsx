import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  Clock, 
  MessageSquareText, 
  Users, 
  Settings, 
  Cpu,
  Layers,
  ShieldCheck
} from 'lucide-react';

export type NavTab = 'overview' | 'analysis' | 'timeline' | 'ask' | 'entities' | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  systemHealth?: {
    gpu_available: boolean;
    device: string;
    version: string;
  } | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  systemHealth,
}) => {
  const navItems = [
    { id: 'overview' as NavTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'analysis' as NavTab, label: 'Video Analysis', icon: Video },
    { id: 'timeline' as NavTab, label: 'Event Timeline', icon: Clock },
    { id: 'ask' as NavTab, label: 'Ask Video', icon: MessageSquareText },
    { id: 'entities' as NavTab, label: 'Entities', icon: Users },
    { id: 'settings' as NavTab, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between h-screen shrink-0 select-none">
      <div>
        {/* Product Brand */}
        <div className="h-16 flex items-center px-6 border-b border-slate-100 gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-slate-900 text-sm tracking-tight flex items-center gap-1.5">
              ChronosAI
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100">PS02</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium leading-tight mt-0.5">Temporal Reasoning Engine</div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-slate-100 text-slate-900 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status Footprint */}
      <div className="p-4 m-3 rounded-lg bg-slate-50 border border-slate-200/70 space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            Inference Engine
          </span>
          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${
            systemHealth?.gpu_available 
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
              : 'bg-blue-50 text-blue-700 border border-blue-200'
          }`}>
            {systemHealth?.gpu_available ? 'CUDA / GPU' : 'CPU Active'}
          </span>
        </div>
        <div className="text-[11px] text-slate-500 space-y-0.5">
          <div className="flex justify-between">
            <span>Model:</span>
            <span className="font-medium text-slate-700">YOLOv8 + ByteTrack</span>
          </div>
          <div className="flex justify-between">
            <span>Memory:</span>
            <span className="font-medium text-slate-700">SQLite Temporal DB</span>
          </div>
        </div>
        <div className="pt-1.5 border-t border-slate-200/80 flex items-center gap-1.5 text-[10px] text-slate-400">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          <span>Deterministic Grounding</span>
        </div>
      </div>
    </aside>
  );
};
