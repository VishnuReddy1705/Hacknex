import React, { useState } from 'react';
import { VideoMetadata, TemporalEvent, EntityTrack } from '../types';
import { VideoPlayer } from '../components/VideoPlayer';
import { formatTimestamp, formatDuration } from '../utils/format';
import { 
  Clock, 
  Filter, 
  Layers, 
  Play, 
  Sparkles, 
  Loader2, 
  AlertTriangle,
  User,
  Box,
  MapPin,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

interface VideoAnalysisPageProps {
  activeVideo: VideoMetadata | null;
  events: TemporalEvent[];
  entities: EntityTrack[];
  seekTime: number | null;
  onSeek: (seconds: number) => void;
  onRefreshData: () => void;
}

export const VideoAnalysisPage: React.FC<VideoAnalysisPageProps> = ({
  activeVideo,
  events,
  entities,
  seekTime,
  onSeek,
  onRefreshData,
}) => {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  if (!activeVideo) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center">
        <div className="bg-white border border-slate-200 rounded-xl p-12">
          <p className="text-sm text-slate-500">Please select or upload a video to begin analysis.</p>
        </div>
      </div>
    );
  }

  const handleStartAnalysis = async () => {
    setIsProcessing(true);
    try {
      await api.processVideo(activeVideo.id);
      onRefreshData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  };

  const filteredEvents = events.filter((ev) => {
    if (activeCategory === 'all') return true;
    if (activeCategory === 'people') return ['PERSON_ENTERED', 'PERSON_EXITED', 'LOITERING'].includes(ev.type);
    if (activeCategory === 'objects') return ['OBJECT_APPEARED', 'OBJECT_DISAPPEARED', 'OBJECT_STATIONARY', 'OBJECT_INTERACTION'].includes(ev.type);
    if (activeCategory === 'zones') return ['ZONE_ENTRY', 'ZONE_EXIT'].includes(ev.type);
    if (activeCategory === 'anomalies') return ['OBJECT_LEFT_UNATTENDED', 'LOITERING'].includes(ev.type);
    return true;
  });

  const getEventIcon = (type: string) => {
    if (type.includes('PERSON')) return <User className="w-3.5 h-3.5 text-indigo-600" />;
    if (type.includes('ZONE')) return <MapPin className="w-3.5 h-3.5 text-blue-600" />;
    if (type.includes('UNATTENDED') || type.includes('LOITERING')) return <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
    return <Box className="w-3.5 h-3.5 text-emerald-600" />;
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col p-6 gap-6 overflow-hidden">
      {/* 65 / 35 Workspace Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left: Video Player Workspace (approx 65% ~ 8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-4 overflow-y-auto pr-1">
          <VideoPlayer
            videoId={activeVideo.id}
            hasAnnotated={activeVideo.has_annotated_video}
            seekTime={seekTime}
            onTimeUpdate={(t) => setCurrentTime(t)}
          />

          {/* Under-video metadata & analytics bar */}
          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center justify-between text-xs text-slate-600">
            <div className="flex items-center gap-6">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Resolution</span>
                <span className="font-semibold text-slate-800">{activeVideo.width} &times; {activeVideo.height}</span>
              </div>
              <div className="border-l border-slate-200 pl-6">
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Framerate</span>
                <span className="font-semibold text-slate-800">{activeVideo.fps} FPS</span>
              </div>
              <div className="border-l border-slate-200 pl-6">
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Duration</span>
                <span className="font-semibold text-slate-800">{formatDuration(activeVideo.duration_seconds)}</span>
              </div>
              <div className="border-l border-slate-200 pl-6">
                <span className="text-slate-400 block text-[10px] uppercase font-bold tracking-wider">Tracked Entities</span>
                <span className="font-semibold text-indigo-600">{entities.length} detected</span>
              </div>
            </div>

            {activeVideo.status === 'idle' && (
              <button
                onClick={handleStartAnalysis}
                disabled={isProcessing}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
              >
                {isProcessing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Process Video</span>
              </button>
            )}
          </div>
        </div>

        {/* Right: Event Timeline Panel (approx 35% ~ 4 cols) */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-lg flex flex-col shadow-sm min-h-0 overflow-hidden">
          {/* Header & Filter Row */}
          <div className="p-4 border-b border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-indigo-600" />
                <h2 className="text-sm font-semibold text-slate-900">Event Timeline</h2>
              </div>
              <span className="text-xs font-medium text-slate-400">
                {filteredEvents.length} events
              </span>
            </div>

            {/* Category Filter Chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              {[
                { id: 'all', label: 'All' },
                { id: 'people', label: 'People' },
                { id: 'objects', label: 'Objects' },
                { id: 'zones', label: 'Zones' },
                { id: 'anomalies', label: 'Anomalies' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveCategory(tab.id)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                    activeCategory === tab.id
                      ? 'bg-slate-900 text-white font-semibold'
                      : 'bg-slate-100 hover:bg-slate-200/70 text-slate-600'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scrollable Chronological Events List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {filteredEvents.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                {activeVideo.status === 'idle'
                  ? 'Video is not yet analyzed. Click "Process Video" to extract events.'
                  : 'No events match the selected filter category.'}
              </div>
            ) : (
              filteredEvents.map((ev) => {
                const isNearCurrent = Math.abs(currentTime - ev.start_time) < 1.0;
                return (
                  <div
                    key={ev.event_id}
                    onClick={() => onSeek(ev.start_time)}
                    className={`group p-3 rounded-lg border text-left cursor-pointer transition-all ${
                      isNearCurrent
                        ? 'bg-indigo-50/80 border-indigo-300 ring-1 ring-indigo-200'
                        : 'bg-white hover:bg-slate-50 border-slate-200/80 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 group-hover:bg-indigo-100 text-slate-800 group-hover:text-indigo-900 border border-slate-200">
                          {formatTimestamp(ev.start_time)}
                        </span>
                        <div className="flex items-center gap-1 text-[11px] font-medium text-slate-500">
                          {getEventIcon(ev.type)}
                          <span>{ev.entity_id}</span>
                        </div>
                      </div>

                      <span className="text-[10px] text-slate-400 font-mono">
                        {Math.round(ev.confidence * 100)}% conf
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-slate-800 mt-1.5 group-hover:text-indigo-600 transition-colors">
                      {ev.description}
                    </div>

                    {ev.end_time > ev.start_time && (
                      <div className="mt-1 text-[11px] text-slate-400">
                        Duration: {round(ev.end_time - ev.start_time, 1)}s (until {formatTimestamp(ev.end_time)})
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function round(val: number, decimals: number): number {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals);
}
