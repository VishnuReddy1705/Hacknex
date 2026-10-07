from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class EventResponse(BaseModel):
    id: str
    video_id: str
    object_id: Optional[str] = None
    related_object_id: Optional[str] = None
    event_type: str
    start_time: float
    end_time: float
    duration: float
    confidence: float
    description: str
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class EventRelationshipResponse(BaseModel):
    id: int
    video_id: str
    source_event_id: str
    relationship: str
    target_event_id: str
    time_difference: float

    class Config:
        from_attributes = True

class TimelineResponse(BaseModel):
    video_id: str
    total_events: int
    events: List[EventResponse]
    relationships: List[EventRelationshipResponse]
