import React, { useState } from 'react';
import { VideoMetadata, TemporalEvent } from '../types';
import { formatTimestamp, formatDuration } from '../utils/format';
import { Clock, Search, Filter, ShieldCheck, Tag, ArrowRight, PlayCircle } from 'lucide-react';
import { VideoPlayer } from '../components/VideoPlayer';
import { EntityTrack } from '../types';

interface EventTimelinePageProps {
  activeVideo: VideoMetadata | null;
  events: TemporalEvent[];
  entities?: EntityTrack[];
  seekTime: number | { time: number; nonce: number } | null;
  onSeekToTime: (time: number) => void;
  onNavigateToAnalysis: () => void;
}

export const EventTimelinePage: React.FC<EventTimelinePageProps> = ({
  activeVideo,
  events,
  entities = [],
  seekTime,
  onSeekToTime,
  onNavigateToAnalysis,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');

  if (!activeVideo) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center">
        <div className="bg-white border border-slate-200 rounded-xl p-12">
          <p className="text-sm text-slate-500">Please select or upload a video to inspect its temporal timeline.</p>
        </div>
      </div>
    );
  }

  const filteredEvents = events.filter((ev) => {
    const matchesSearch =
      ev.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ev.entity_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ev.type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = selectedType === 'ALL' || ev.type === selectedType;

    return matchesSearch && matchesType;
  });

  const eventTypes = Array.from(new Set(events.map((e) => e.type)));

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      {/* Title & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Structured Temporal Index</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Indexed event stream for <span className="font-semibold text-slate-700">{activeVideo.original_name}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
            {events.length} Events Total
          </span>
          <button
            onClick={onNavigateToAnalysis}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
          >
            <span>Open Video View</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search events by entity, action, or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 focus:bg-white border border-slate-200 rounded-md outline-none focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-1.5 outline-none text-slate-700 cursor-pointer"
          >
            <option value="ALL">All Event Types</option>
            {eventTypes.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Side-by-Side 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Events Stream List (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          {filteredEvents.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-lg p-12 text-center text-xs text-slate-400">
              No events match the criteria or video has not been processed.
            </div>
          ) : (
            filteredEvents.map((ev, index) => (
              <div
                key={ev.event_id}
                onClick={() => onSeekToTime(ev.start_time)}
                className="bg-white border border-slate-200 rounded-lg p-4 shadow-2xs hover:border-indigo-300 hover:bg-slate-50/50 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-4">
                  {/* Index Pill & Timecode */}
                  <div className="flex flex-col items-center">
                    <span className="text-[10px] font-bold text-slate-400">#{index + 1}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSeekToTime(ev.start_time);
                      }}
                      className="mt-1 inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono font-bold bg-slate-100 hover:bg-indigo-50 text-slate-800 hover:text-indigo-900 border border-slate-200 transition-colors cursor-pointer"
                    >
                      <PlayCircle className="w-3.5 h-3.5 text-indigo-600" />
                      <span>{formatTimestamp(ev.start_time)}</span>
                    </button>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {ev.type}
                      </span>
                      <span className="text-xs font-medium text-slate-500 flex items-center gap-1">
                        <Tag className="w-3 h-3 text-slate-400" />
                        {ev.entity_id}
                      </span>
                      {ev.related_entity_id && (
                        <span className="text-xs text-slate-400">
                          &rarr; {ev.related_entity_id}
                        </span>
                      )}
                    </div>

                    <div className="text-sm font-semibold text-slate-900">
                      {ev.description}
                    </div>

                    <div className="text-[11px] text-slate-400 flex items-center gap-4">
                      <span>Frames: {ev.frame_start} &ndash; {ev.frame_end}</span>
                      {ev.end_time > ev.start_time && (
                        <span>Duration: {round(ev.end_time - ev.start_time, 1)}s</span>
                      )}
                      <span>Confidence: {Math.round(ev.confidence * 100)}%</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold text-indigo-600 hover:text-indigo-700 bg-indigo-50/70 border border-indigo-200 transition-colors">
                    <PlayCircle className="w-3.5 h-3.5" />
                    <span>Play &rarr;</span>
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Column: Live Sticky Video Player (5 cols) */}
        <div className="lg:col-span-5 sticky top-6 space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <PlayCircle className="w-4 h-4 text-indigo-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Timeline Synchronized Player</h3>
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
              Click any event in the timeline on the left to seek & auto-play the video at that exact moment.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

function round(val: number, decimals: number): number {
  return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals);
}
