import React, { useState } from 'react';
import { VideoMetadata, EntityTrack, TemporalEvent } from '../types';
import { formatTimestamp, formatDuration } from '../utils/format';
import { Users, Tag, Clock, ArrowRight, PlayCircle, ShieldCheck, Box, User } from 'lucide-react';

interface EntitiesPageProps {
  activeVideo: VideoMetadata | null;
  entities: EntityTrack[];
  events: TemporalEvent[];
  onSeekToTime: (time: number) => void;
  onNavigateToAnalysis: () => void;
}

export const EntitiesPage: React.FC<EntitiesPageProps> = ({
  activeVideo,
  entities,
  events,
  onSeekToTime,
  onNavigateToAnalysis,
}) => {
  const [selectedEntityId, setSelectedEntityId] = useState<string | null>(null);

  if (!activeVideo) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center">
        <div className="bg-white border border-slate-200 rounded-xl p-12">
          <p className="text-sm text-slate-500">Please select or upload a video to inspect detected entities.</p>
        </div>
      </div>
    );
  }

  const selectedEntity = entities.find((e) => e.entity_id === selectedEntityId) || entities[0];
  const selectedEvents = selectedEntity
    ? events.filter(
        (e) => e.entity_id === selectedEntity.entity_id || e.related_entity_id === selectedEntity.entity_id
      )
    : [];

  const handleInspect = (time: number) => {
    onSeekToTime(time);
    onNavigateToAnalysis();
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Entity Explorer</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Persistent track identities maintained across frames for <span className="font-semibold text-slate-700">{activeVideo.original_name}</span>
          </p>
        </div>

        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
          {entities.length} Unique Entities
        </span>
      </div>

      {entities.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center text-xs text-slate-400">
          No tracked entities available. Process the video to extract entity tracks.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Entity List */}
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-900">Tracked Entities Table</h2>
              <span className="text-xs text-slate-400">ByteTrack Persistent IDs</span>
            </div>

            <div className="divide-y divide-slate-100">
              {entities.map((ent) => {
                const isSelected = selectedEntity?.entity_id === ent.entity_id;
                const isPerson = ent.class_name.toLowerCase().includes('person');

                return (
                  <div
                    key={ent.entity_id}
                    onClick={() => setSelectedEntityId(ent.entity_id)}
                    className={`p-4 flex items-center justify-between cursor-pointer transition-colors ${
                      isSelected ? 'bg-indigo-50/60' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                          isPerson ? 'bg-indigo-100 text-indigo-700' : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {isPerson ? <User className="w-4 h-4" /> : <Box className="w-4 h-4" />}
                      </div>

                      <div>
                        <div className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                          <span>{ent.entity_id}</span>
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200 uppercase">
                            {ent.class_name}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          Seen {formatTimestamp(ent.first_seen)} &rarr; {formatTimestamp(ent.last_seen)} &bull; {formatDuration(ent.duration)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleInspect(ent.first_seen);
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono font-bold bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors shadow-2xs"
                      >
                        <PlayCircle className="w-3.5 h-3.5 text-indigo-600" />
                        <span>{formatTimestamp(ent.first_seen)}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Entity Details Panel */}
          {selectedEntity && (
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase">
                    {selectedEntity.class_name}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Track ID #{selectedEntity.track_id}</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">{selectedEntity.entity_id}</h3>
              </div>

              {/* Metrics */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">First Observed:</span>
                  <button
                    onClick={() => handleInspect(selectedEntity.first_seen)}
                    className="font-mono font-bold text-indigo-600 hover:underline"
                  >
                    {formatTimestamp(selectedEntity.first_seen)}
                  </button>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Last Observed:</span>
                  <button
                    onClick={() => handleInspect(selectedEntity.last_seen)}
                    className="font-mono font-bold text-indigo-600 hover:underline"
                  >
                    {formatTimestamp(selectedEntity.last_seen)}
                  </button>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Total Duration:</span>
                  <span className="font-semibold text-slate-800">{formatDuration(selectedEntity.duration)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-50">
                  <span className="text-slate-500">Tracking Confidence:</span>
                  <span className="font-semibold text-slate-800">{Math.round(selectedEntity.confidence * 100)}%</span>
                </div>
              </div>

              {/* Associated Events */}
              <div className="space-y-2 pt-2">
                <div className="text-xs font-semibold text-slate-900">
                  Associated Events ({selectedEvents.length})
                </div>

                {selectedEvents.length === 0 ? (
                  <p className="text-xs text-slate-400">No discrete events associated with this entity.</p>
                ) : (
                  <div className="space-y-2">
                    {selectedEvents.map((ev) => (
                      <div
                        key={ev.event_id}
                        onClick={() => handleInspect(ev.start_time)}
                        className="p-2.5 rounded-lg border border-slate-200/80 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all cursor-pointer text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono font-bold text-slate-700">{formatTimestamp(ev.start_time)}</span>
                          <span className="text-[10px] text-indigo-600 font-semibold">Jump &rarr;</span>
                        </div>
                        <div className="text-slate-800 font-medium mt-1">{ev.description}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
