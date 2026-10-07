import React, { useState } from 'react';
import { VideoMetadata, QueryResponse } from '../types';
import { api } from '../services/api';
import { formatTimestamp } from '../utils/format';
import { 
  MessageSquareText, 
  Send, 
  Sparkles, 
  PlayCircle, 
  ShieldCheck, 
  ArrowRight, 
  Clock, 
  Layers,
  HelpCircle,
  Loader2
} from 'lucide-react';
import { VideoPlayer } from '../components/VideoPlayer';
import { EntityTrack } from '../types';

interface AskVideoPageProps {
  activeVideo: VideoMetadata | null;
  entities?: EntityTrack[];
  seekTime: number | { time: number; nonce: number } | null;
  onSeekToTime: (time: number) => void;
  onNavigateToAnalysis: () => void;
}

export const AskVideoPage: React.FC<AskVideoPageProps> = ({
  activeVideo,
  entities = [],
  seekTime,
  onSeekToTime,
  onNavigateToAnalysis,
}) => {
  const [queryInput, setQueryInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null);
  const [history, setHistory] = useState<QueryResponse[]>([]);

  const suggestions = [
    'What happened first?',
    'Who entered after Person 1?',
    'How long was the backpack unattended?',
    'What happened before the last event?',
    'How many people were tracked?',
    'Show the full sequence.',
  ];

  const handleAsk = async (text: string) => {
    if (!activeVideo || !text.trim() || isLoading) return;

    setIsLoading(true);
    try {
      const res = await api.queryVideo(activeVideo.id, text.trim());
      setCurrentResponse(res);
      setHistory((prev) => [res, ...prev]);
      setQueryInput('');
      if (res.timestamp_start !== null && res.timestamp_start !== undefined) {
        onSeekToTime(res.timestamp_start);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSeek = (time: number) => {
    onSeekToTime(time);
  };

  if (!activeVideo) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center">
        <div className="bg-white border border-slate-200 rounded-xl p-12">
          <p className="text-sm text-slate-500">Please select or upload a video to ask temporal questions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Ask this video</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Temporal reasoning and timestamp-grounded question answering with live side-by-side video playback.
          </p>
        </div>
        <button
          onClick={onNavigateToAnalysis}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-2xs transition-colors"
        >
          <span>Full Analysis View</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Side-by-Side 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Q&A, Suggestions & Verified Responses (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Suggestion Chips */}
          <div className="space-y-1.5">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle className="w-3 h-3" />
              <span>Recommended Queries</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((chip) => (
                <button
                  key={chip}
                  onClick={() => handleAsk(chip)}
                  className="px-3 py-1.5 rounded-full text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 hover:border-slate-300 shadow-2xs transition-all text-left"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAsk(queryInput);
            }}
            className="relative bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all"
          >
            <textarea
              rows={2}
              placeholder="e.g. What happened between Person 1 entering and leaving? How long was the bag untouched?"
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleAsk(queryInput);
                }
              }}
              className="w-full px-4 py-3 text-sm text-slate-900 outline-none resize-none placeholder:text-slate-400"
            />

            <div className="bg-slate-50 px-4 py-2 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Grounded via Temporal Event Graph
              </span>
              <button
                type="submit"
                disabled={!queryInput.trim() || isLoading}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 text-white transition-colors cursor-pointer"
              >
                {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                <span>Ask</span>
              </button>
            </div>
          </form>

          {/* Latest Answer Display */}
          {currentResponse && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4 animate-in fade-in duration-200">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded">
                    Verified Response
                  </span>
                  <h2 className="text-sm font-semibold text-slate-700 mt-1">
                    Q: &ldquo;{currentResponse.query}&rdquo;
                  </h2>
                </div>

                {currentResponse.timestamp_start !== null && (
                  <button
                    onClick={() => handleSeek(currentResponse.timestamp_start!)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-100 hover:bg-indigo-50 text-slate-800 hover:text-indigo-900 border border-slate-200 text-xs font-mono font-bold transition-colors cursor-pointer"
                  >
                    <PlayCircle className="w-3.5 h-3.5 text-indigo-600" />
                    <span>Seek to {formatTimestamp(currentResponse.timestamp_start)}</span>
                  </button>
                )}
              </div>

              {/* Natural Language Answer Box */}
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200/80 text-sm font-medium text-slate-900 leading-relaxed">
                {currentResponse.answer}
              </div>

              {/* Temporal Relation Flow (when available) */}
              {currentResponse.temporal_relation && (
                <div className="p-3.5 rounded-lg bg-indigo-50/60 border border-indigo-100 space-y-2">
                  <div className="text-[11px] font-semibold text-indigo-900 uppercase tracking-wider">
                    Temporal Transition Flow
                  </div>
                  <div className="flex items-center gap-3 text-xs font-medium text-slate-800 flex-wrap">
                    <span className="bg-white px-2.5 py-1 rounded border border-indigo-200 shadow-2xs">
                      {currentResponse.temporal_relation.from_event}
                    </span>
                    <span className="text-indigo-600 font-bold font-mono">
                      &darr; +{currentResponse.temporal_relation.delta_seconds}s
                    </span>
                    <span className="bg-white px-2.5 py-1 rounded border border-indigo-200 shadow-2xs">
                      {currentResponse.temporal_relation.to_event}
                    </span>
                  </div>
                </div>
              )}

              {/* Evidence Grid */}
              {currentResponse.evidence.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Supporting Visual Evidence ({currentResponse.evidence.length})</span>
                  </div>
                  <div className="grid grid-cols-1 gap-2">
                    {currentResponse.evidence.map((ev, i) => (
                      <div
                        key={i}
                        onClick={() => handleSeek(ev.timestamp)}
                        className="p-3 bg-slate-50 hover:bg-indigo-50/60 border border-slate-200 hover:border-indigo-300 rounded-lg transition-colors cursor-pointer flex items-center justify-between"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-100 px-1.5 py-0.5 rounded">
                              {formatTimestamp(ev.timestamp)}
                            </span>
                            <span className="text-xs font-semibold text-slate-800">{ev.label}</span>
                          </div>
                          <p className="text-xs text-slate-600 mt-1">{ev.description}</p>
                        </div>
                        <PlayCircle className="w-4 h-4 text-indigo-600 shrink-0 ml-3" />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reasoning trace disclosure */}
              {currentResponse.reasoning_trace && currentResponse.reasoning_trace.length > 0 && (
                <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400 font-mono">
                  <span className="font-semibold text-slate-500">Reasoning trace: </span>
                  {currentResponse.reasoning_trace.join(' &rarr; ')}
                </div>
              )}
            </div>
          )}

          {/* History Log */}
          {history.length > 1 && (
            <div className="space-y-3 pt-3 border-t border-slate-200">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Previous Queries</h3>
              <div className="space-y-2">
                {history.slice(1).map((h, i) => (
                  <div
                    key={i}
                    onClick={() => {
                      setCurrentResponse(h);
                      if (h.timestamp_start !== null) handleSeek(h.timestamp_start);
                    }}
                    className="p-3 bg-white border border-slate-200 rounded-lg text-xs hover:border-slate-300 transition-colors cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <span className="font-semibold text-slate-800">{h.query}</span>
                      <p className="text-slate-500 line-clamp-1 mt-0.5">{h.answer}</p>
                    </div>
                    <span className="text-indigo-600 font-semibold shrink-0 ml-4">Play &rarr;</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Video Player Sticky Side-by-Side (5 cols) */}
        <div className="lg:col-span-5 sticky top-6 space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <PlayCircle className="w-4 h-4 text-indigo-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Live Video Evidence</h3>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">
                {activeVideo.original_name}
              </span>
            </div>

            <VideoPlayer
              videoId={activeVideo.id}
              hasAnnotated={activeVideo.has_annotated_video}
              seekTime={seekTime}
              entities={entities}
              videoWidth={activeVideo.width}
              videoHeight={activeVideo.height}
              onTimeUpdate={() => {}}
            />

            <p className="text-[11px] text-slate-500 mt-3 text-center">
              Clicking any answer timestamp, evidence card, or timeline event automatically seeks & plays the video here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
