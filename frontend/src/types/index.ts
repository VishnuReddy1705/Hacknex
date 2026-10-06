export type VideoProcessingStage = 
  | 'idle'
  | 'uploading'
  | 'reading_video'
  | 'detecting_entities'
  | 'tracking_entities'
  | 'extracting_events'
  | 'indexing_temporal'
  | 'ready'
  | 'failed';

export interface VideoMetadata {
  id: string;
  filename: string;
  original_name: string;
  fps: number;
  width: number;
  height: number;
  total_frames: number;
  duration_seconds: number;
  status: VideoProcessingStage;
  progress_pct: number;
  current_stage_label: string;
  error_message?: string;
  created_at: string;
  has_annotated_video: boolean;
}

export type EventType =
  | 'PERSON_ENTERED'
  | 'PERSON_EXITED'
  | 'OBJECT_APPEARED'
  | 'OBJECT_DISAPPEARED'
  | 'ZONE_ENTRY'
  | 'ZONE_EXIT'
  | 'OBJECT_STATIONARY'
  | 'OBJECT_INTERACTION'
  | 'OBJECT_LEFT_UNATTENDED'
  | 'OBJECT_PICKED_UP'
  | 'LOITERING';

export interface TemporalEvent {
  event_id: string;
  video_id: string;
  type: EventType;
  entity_id: string;
  related_entity_id?: string | null;
  start_time: number;
  end_time: number;
  frame_start: number;
  frame_end: number;
  confidence: number;
  description: string;
  metadata?: Record<string, any>;
}

export interface EntityTrajectoryPoint {
  frame: number;
  timestamp: number;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;
}

export interface EntityTrack {
  entity_id: string;
  track_id: number;
  class_name: string;
  first_seen: number;
  last_seen: number;
  duration: number;
  confidence: number;
  event_count: number;
  trajectory?: EntityTrajectoryPoint[];
}

export interface TemporalEvidenceItem {
  timestamp: number;
  label: string;
  event_id?: string;
  entity_id?: string;
  description: string;
}

export interface TemporalRelationStep {
  from_event: string;
  to_event: string;
  delta_seconds: number;
  relation: string; // 'before', 'after', 'during'
}

export interface QueryResponse {
  query: string;
  answer: string;
  timestamp_start: number | null;
  timestamp_end: number | null;
  relevant_entities: string[];
  confidence: number;
  evidence: TemporalEvidenceItem[];
  temporal_relation?: TemporalRelationStep | null;
  reasoning_trace?: string[];
}
