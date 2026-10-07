import { VideoMetadata, TemporalEvent, EntityTrack, QueryResponse, VideoProcessingStage } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async listVideos(): Promise<VideoMetadata[]> {
    const res = await fetch(`${API_BASE_URL}/videos`);
    if (!res.ok) throw new Error('Failed to fetch videos');
    return res.json();
  },

  async getVideo(videoId: string): Promise<VideoMetadata> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}`);
    if (!res.ok) throw new Error('Failed to fetch video');
    return res.json();
  },

  async getVideoStatus(videoId: string): Promise<{
    id: string;
    status: VideoProcessingStage;
    progress_pct: number;
    current_stage_label: string;
    current_frame: number;
    total_frames: number;
    error_message?: string;
  }> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/status`);
    if (!res.ok) throw new Error('Failed to fetch video status');
    return res.json();
  },

  async uploadVideo(file: File): Promise<VideoMetadata> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/videos/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async processVideo(videoId: string): Promise<{ message: string; video_id: string }> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/process`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Processing failed to start' }));
      throw new Error(err.detail || 'Failed to start processing');
    }
    return res.json();
  },

  async getEvents(videoId: string): Promise<TemporalEvent[]> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/events`);
    if (!res.ok) throw new Error('Failed to fetch events');
    const data = await res.json();
    return data.map((d: any) => ({
      event_id: d.id,
      video_id: d.video_id,
      type: d.event_type,
      entity_id: d.object_id || 'scene',
      related_entity_id: d.related_object_id,
      start_time: d.start_time,
      end_time: d.end_time,
      frame_start: Math.round(d.start_time * 30),
      frame_end: Math.round(d.end_time * 30),
      confidence: d.confidence,
      description: d.description,
      metadata: d.metadata
    }));
  },

  async getEntities(videoId: string): Promise<EntityTrack[]> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/objects`);
    if (!res.ok) throw new Error('Failed to fetch objects');
    const data = await res.json();
    return data.map((d: any) => ({
      entity_id: d.id,
      track_id: d.track_id,
      class_name: d.class_name,
      first_seen: d.first_seen,
      last_seen: d.last_seen,
      duration: d.duration,
      confidence: d.confidence,
      event_count: 0,
      trajectory: (d.trajectory || []).map((t: any) => ({
        frame: t.frame_number,
        timestamp: t.timestamp,
        bbox: t.bbox,
        confidence: t.confidence
      }))
    }));
  },

  async askVideo(videoId: string, question: string): Promise<{
    answer: string;
    timestamps: string[];
    evidence: any[];
    confidence: number;
    graph_relation?: any;
  }> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Ask failed' }));
      throw new Error(err.detail || 'Failed to query video');
    }
    return res.json();
  },

  // Backward compatible queryVideo alias mapping to askVideo
  async queryVideo(videoId: string, query: string): Promise<QueryResponse> {
    const askRes = await this.askVideo(videoId, query);
    const firstSec = askRes.evidence && askRes.evidence.length > 0 ? askRes.evidence[0].timestamp_seconds : null;
    const lastSec = askRes.evidence && askRes.evidence.length > 1 ? askRes.evidence[askRes.evidence.length - 1].timestamp_seconds : firstSec;

    return {
      query,
      answer: askRes.answer,
      timestamp_start: firstSec,
      timestamp_end: lastSec,
      relevant_entities: askRes.evidence ? askRes.evidence.map((e: any) => e.object_id).filter(Boolean) : [],
      confidence: askRes.confidence,
      evidence: askRes.evidence ? askRes.evidence.map((e: any) => ({
        timestamp: e.timestamp_seconds,
        label: `${e.timestamp} ${e.description}`,
        event_id: e.event_id,
        entity_id: e.object_id,
        description: e.description
      })) : [],
      temporal_relation: askRes.graph_relation ? {
        from_event: askRes.graph_relation.source,
        to_event: askRes.graph_relation.target,
        delta_seconds: askRes.graph_relation.time_difference,
        relation: askRes.graph_relation.relation
      } : null,
      reasoning_trace: [`Resolved via ChronosAI Temporal Event Graph`]
    };
  },

  async getTimeline(videoId: string) {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  },

  getVideoStreamUrl(videoId: string, annotated: boolean = false): string {
    return `${API_BASE_URL}/videos/${videoId}/stream?annotated=${annotated}`;
  }
};
