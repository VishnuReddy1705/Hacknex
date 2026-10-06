import React from 'react';
import { VideoMetadata } from '../types';
import { formatDuration } from '../utils/format';
import { UploadCloud, Film, CheckCircle2, Loader2, AlertCircle, Clock } from 'lucide-react';

interface TopBarProps {
  videos: VideoMetadata[];
  activeVideo: VideoMetadata | null;
  onSelectVideo: (videoId: string) => void;
  onOpenUpload: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  videos,
  activeVideo,
  onSelectVideo,
  onOpenUpload,
}) => {
  const getStatusBadge = () => {
    if (!activeVideo) return null;

    if (activeVideo.status === 'ready') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Indexed & Ready
        </span>
      );
    }
    if (activeVideo.status === 'failed') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200">
          <AlertCircle className="w-3.5 h-3.5" />
          Analysis Failed
        </span>
      );
    }
    if (activeVideo.status !== 'idle') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200 animate-pulse">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          {activeVideo.current_stage_label} ({Math.round(activeVideo.progress_pct)}%)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
        <Clock className="w-3.5 h-3.5 text-slate-500" />
        Uploaded (Pending Analysis)
      </span>
    );
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        {/* Active video indicator / selector */}
        {videos.length > 0 ? (
          <div className="flex items-center gap-2">
            <Film className="w-4 h-4 text-slate-400" />
            <select
              value={activeVideo?.id || ''}
              onChange={(e) => onSelectVideo(e.target.value)}
              className="text-sm font-semibold text-slate-900 bg-transparent hover:bg-slate-50 border border-transparent hover:border-slate-200 rounded px-2 py-1 outline-none transition-colors cursor-pointer"
            >
              {videos.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.original_name}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Film className="w-4 h-4" />
            <span>No video selected</span>
          </div>
        )}

        {/* Status Pill */}
        {getStatusBadge()}

        {/* Duration badge */}
        {activeVideo && activeVideo.duration_seconds > 0 && (
          <span className="text-xs text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded">
            Duration: {formatDuration(activeVideo.duration_seconds)} ({activeVideo.total_frames} frames @ {activeVideo.fps} FPS)
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenUpload}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
        >
          <UploadCloud className="w-4 h-4" />
          <span>Upload Video</span>
        </button>
      </div>
    </header>
  );
};
