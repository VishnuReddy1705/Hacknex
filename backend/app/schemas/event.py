from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TemporalEventSchema(BaseModel):
    event_id: str
    video_id: str
    type: str
    entity_id: str
    related_entity_id: Optional[str] = None
    start_time: float
    end_time: float
    frame_start: int
    frame_end: int
    confidence: float
    description: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class EventFilterQuery(BaseModel):
    category: Optional[str] = None # 'all', 'people', 'objects', 'zones', 'anomalies'
    min_confidence: Optional[float] = 0.0
