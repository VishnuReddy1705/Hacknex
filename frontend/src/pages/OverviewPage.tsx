import React, { useState } from 'react';
import { VideoMetadata, TemporalEvent, EntityTrack } from '../types';
import { formatDuration, formatTimestamp } from '../utils/format';
import { 
  Play, 
  Users, 
  Box, 
  Clock, 
  CheckCircle2, 
  ArrowRight, 
  Cpu, 
  Activity,
  Layers,
  Sparkles,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';

interface OverviewPageProps {
  activeVideo: VideoMetadata | null;
  events: TemporalEvent[];
  entities: EntityTrack[];
  onNavigateToAnalysis: () => void;
  onNavigateToAsk: () => void;
  onSeekToTime: (time: number) => void;
  onRefreshData: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  activeVideo,
  events,
  entities,
  onNavigateToAnalysis,
  onNavigateToAsk,
  onSeekToTime,
  onRefreshData,
}) => {
  const [isTriggering, setIsTriggering] = useState(false);

  if (!activeVideo) {
    return (
      <div className="p-8 max-w-5xl mx-auto">
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center">
          <div className="w-12 h-12 mx-auto rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-3">
            <Clock className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-slate-800">No Video Selected</h2>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload a video using the top bar or file selector to inspect detections, events, and temporal timeline.
          </p>
        </div>
      </div>
    );
  }

  const peopleCount = entities.filter((e) => e.class_name.toLowerCase().includes('person')).length;
  const objectCount = entities.filter((e) => !e.class_name.toLowerCase().includes('person')).length;

  const handleStartAnalysis = async () => {
    setIsTriggering(true);
    try {
      await api.processVideo(activeVideo.id);
      onRefreshData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsTriggering(false);
    }
  };

  const pipelineStages = [
    { label: 'Video Ingestion & Metadata', desc: 'FPS, resolution & duration', done: true },
    { label: 'YOLOv8 Detection', desc: 'Spatial bounding boxes & classes', done: activeVideo.status === 'ready' },
    { label: 'ByteTrack Multi-Object Tracking', desc: 'Persistent identity preservation', done: activeVideo.status === 'ready' },
    { label: 'Temporal Event Extraction', desc: 'Zone crossings, handoffs & states', done: activeVideo.status === 'ready' },
    { label: 'SQLite Temporal Memory', desc: 'Timestamped relational index', done: activeVideo.status === 'ready' },
    { label: 'Reasoning Engine', desc: 'Deterministic queries & grounding', done: activeVideo.status === 'ready' },
  ];

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Page Title & Quick Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Intelligence Overview</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Temporal audit summary for <span className="font-semibold text-slate-700">{activeVideo.original_name}</span>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeVideo.status === 'idle' && (
            <button
              onClick={handleStartAnalysis}
              disabled={isTriggering}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-md text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
            >
              {isTriggering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Start Video Analysis</span>
            </button>
          )}

          <button
            onClick={onNavigateToAnalysis}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
          >
            <Play className="w-3.5 h-3.5 text-indigo-600" />
            <span>Open Player</span>
          </button>

          <button
            onClick={onNavigateToAsk}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-white transition-colors"
          >
            <span>Ask Questions</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Tracked Entities</span>
            <Layers className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{entities.length}</div>
          <div className="mt-1 text-[11px] text-slate-400">Unique persistent tracks</div>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Detected Events</span>
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{events.length}</div>
          <div className="mt-1 text-[11px] text-slate-400">Timestamp-grounded occurrences</div>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Tracked People</span>
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{peopleCount}</div>
          <div className="mt-1 text-[11px] text-slate-400">Identities maintained across occlusion</div>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Tracked Objects</span>
            <Box className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{objectCount}</div>
          <div className="mt-1 text-[11px] text-slate-400">Bags, vehicles & static assets</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Significant Events */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">Recent Significant Events</h2>
              <p className="text-xs text-slate-500">Chronological event transitions identified by CV engine</p>
            </div>
            <button
              onClick={onNavigateToAnalysis}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View full timeline</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {events.length === 0 ? (
            <div className="py-10 text-center text-slate-400 text-xs">
              {activeVideo.status === 'idle'
                ? 'Video has not been processed yet. Click "Start Video Analysis" above.'
                : 'No significant events detected in this segment.'}
            </div>
          ) : (
            <div className="space-y-2.5">
              {events.slice(0, 6).map((ev) => (
                <div
                  key={ev.event_id}
                  onClick={() => {
                    onSeekToTime(ev.start_time);
                    onNavigateToAnalysis();
                  }}
                  className="flex items-center justify-between p-2.5 rounded-md hover:bg-slate-50 border border-transparent hover:border-slate-200 transition-colors cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 group-hover:bg-indigo-50 text-slate-700 group-hover:text-indigo-800 border border-slate-200">
                      {formatTimestamp(ev.start_time)}
                    </span>
                    <div>
                      <div className="text-xs font-semibold text-slate-900 group-hover:text-indigo-600">
                        {ev.description}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Type: {ev.type} &bull; Entity: {ev.entity_id}
                      </div>
                    </div>
                  </div>

                  <span className="text-[11px] font-semibold text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    Seek &rarr;
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Processing Pipeline Status */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h2 className="text-sm font-semibold text-slate-900">Intelligence Pipeline</h2>
            <p className="text-xs text-slate-500">Autonomous processing stages</p>
          </div>

          <div className="space-y-3">
            {pipelineStages.map((stage, idx) => (
              <div key={idx} className="flex items-start gap-3 text-xs">
                <div className="mt-0.5">
                  {stage.done ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : activeVideo.status !== 'idle' && idx === 1 ? (
                    <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-slate-300" />
                  )}
                </div>
                <div>
                  <div className={`font-semibold ${stage.done ? 'text-slate-800' : 'text-slate-400'}`}>
                    {stage.label}
                  </div>
                  <div className="text-[11px] text-slate-400">{stage.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
            <div className="flex justify-between">
              <span>Resolution:</span>
              <span className="font-semibold text-slate-700">{activeVideo.width} &times; {activeVideo.height}</span>
            </div>
            <div className="flex justify-between">
              <span>Duration:</span>
              <span className="font-semibold text-slate-700">{formatDuration(activeVideo.duration_seconds)}</span>
            </div>
            <div className="flex justify-between">
              <span>Framerate:</span>
              <span className="font-semibold text-slate-700">{activeVideo.fps} FPS ({activeVideo.total_frames} frames)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
