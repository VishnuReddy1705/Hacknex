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

  async processVideo(videoId: string, frameSkip: number = 2): Promise<{ message: string; video_id: string }> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/process?frame_skip=${frameSkip}`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Processing failed to start' }));
      throw new Error(err.detail || 'Failed to start processing');
    }
    return res.json();
  },

  async getEvents(videoId: string, category?: string): Promise<TemporalEvent[]> {
    const url = new URL(`${API_BASE_URL}/videos/${videoId}/events`);
    if (category && category !== 'all') {
      url.searchParams.set('category', category);
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error('Failed to fetch events');
    return res.json();
  },

  async getEntities(videoId: string): Promise<EntityTrack[]> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/entities`);
    if (!res.ok) throw new Error('Failed to fetch entities');
    return res.json();
  },

  async queryVideo(videoId: string, query: string): Promise<QueryResponse> {
    const res = await fetch(`${API_BASE_URL}/videos/${videoId}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Query failed' }));
      throw new Error(err.detail || 'Failed to query video');
    }
    return res.json();
  },

  getVideoStreamUrl(videoId: string, annotated: boolean = false): string {
    return `${API_BASE_URL}/videos/${videoId}/stream?annotated=${annotated}`;
  }
};
