import React from 'react';
import { formatTimestamp } from '../utils/format';
import { PlayCircle, ShieldCheck, Tag } from 'lucide-react';
import { TemporalEvidenceItem } from '../types';

interface EvidenceCardProps {
  evidence: TemporalEvidenceItem;
  onSeek: (seconds: number) => void;
  isActive?: boolean;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  evidence,
  onSeek,
  isActive = false,
}) => {
  return (
    <div
      onClick={() => onSeek(evidence.timestamp)}
      className={`group p-3 rounded-lg border text-left cursor-pointer transition-all ${
        isActive
          ? 'bg-indigo-50/70 border-indigo-300 ring-1 ring-indigo-200'
          : 'bg-white hover:bg-slate-50 border-slate-200 hover:border-slate-300'
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-bold bg-slate-100 group-hover:bg-indigo-100 text-slate-800 group-hover:text-indigo-900 border border-slate-200 group-hover:border-indigo-200 transition-colors"
        >
          <PlayCircle className="w-3.5 h-3.5 text-indigo-600" />
          <span>{formatTimestamp(evidence.timestamp)}</span>
        </button>

        {evidence.entity_id && (
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500 bg-slate-50 border border-slate-200 px-1.5 py-0.5 rounded">
            <Tag className="w-3 h-3 text-slate-400" />
            {evidence.entity_id}
          </span>
        )}
      </div>

      <div className="text-xs text-slate-800 font-medium mt-1.5 line-clamp-2">
        {evidence.description}
      </div>

      <div className="mt-2 pt-1.5 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
        <span className="flex items-center gap-1">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          Verified Visual Evidence
        </span>
        <span className="text-indigo-600 font-semibold group-hover:underline">Jump to frame &rarr;</span>
      </div>
    </div>
  );
};
