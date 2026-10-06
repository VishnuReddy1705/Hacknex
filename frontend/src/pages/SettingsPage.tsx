import React from 'react';
import { Sliders, Cpu, Database, ShieldCheck, Terminal, HardDrive } from 'lucide-react';

interface SettingsPageProps {
  systemHealth?: {
    gpu_available: boolean;
    device: string;
    version: string;
  } | null;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ systemHealth }) => {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">System & Pipeline Configuration</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Temporal reasoning thresholds, computer vision inference parameters, and engine status.
        </p>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-600" />
            <span>Event Extraction Engine Thresholds</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Configurable physical parameters for spatial zone crossings and unattended object classification.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1">
            <div className="font-semibold text-slate-800">Stationary Movement Threshold</div>
            <div className="text-slate-500 text-[11px]">Displacement &le; 25.0 pixels over time window</div>
            <span className="inline-block mt-1 font-mono font-bold text-indigo-600">25 px</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1">
            <div className="font-semibold text-slate-800">Unattended Object Threshold</div>
            <div className="text-slate-500 text-[11px]">Proximity separation &ge; 150 px for duration &ge; 5s</div>
            <span className="inline-block mt-1 font-mono font-bold text-indigo-600">5.0 seconds</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1">
            <div className="font-semibold text-slate-800">YOLO Detection Confidence</div>
            <div className="text-slate-500 text-[11px]">Minimum confidence cutoff for bounding box extraction</div>
            <span className="inline-block mt-1 font-mono font-bold text-indigo-600">0.35 conf</span>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 space-y-1">
            <div className="font-semibold text-slate-800">Frame Sampling Stride</div>
            <div className="text-slate-500 text-[11px]">Process every N frames (preserves exact second timecodes)</div>
            <span className="inline-block mt-1 font-mono font-bold text-indigo-600">Stride = 2</span>
          </div>
        </div>
      </div>

      {/* Hardware & Storage Environment */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
        <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-600" />
          <span>Execution Environment</span>
        </h2>

        <div className="divide-y divide-slate-100 text-xs">
          <div className="flex justify-between py-2.5">
            <span className="text-slate-500">Inference Hardware</span>
            <span className="font-semibold text-slate-800">
              {systemHealth?.gpu_available ? 'NVIDIA GeForce RTX 4050 Laptop GPU' : 'Host CPU'}
            </span>
          </div>
          <div className="flex justify-between py-2.5">
            <span className="text-slate-500">Acceleration Backend</span>
            <span className="font-semibold text-slate-800 font-mono">
              {systemHealth?.device.toUpperCase()}
            </span>
          </div>
          <div className="flex justify-between py-2.5">
            <span className="text-slate-500">Tracking Engine</span>
            <span className="font-semibold text-slate-800">ByteTrack (Kalman Filter + Hungarian Algorithm)</span>
          </div>
          <div className="flex justify-between py-2.5">
            <span className="text-slate-500">Storage Backend</span>
            <span className="font-semibold text-slate-800">SQLite (Indexed relational tables)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
