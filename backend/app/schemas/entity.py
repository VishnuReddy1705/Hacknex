from pydantic import BaseModel
from typing import Optional, List

class TrajectoryPoint(BaseModel):
    frame: int
    timestamp: float
    bbox: List[float] # [x1, y1, x2, y2]
    confidence: float

class EntityTrackSchema(BaseModel):
    entity_id: str
    video_id: str
    track_id: int
    class_name: str
    first_seen: float
    last_seen: float
    duration: float
    confidence: float
    event_count: int = 0
    trajectory: Optional[List[TrajectoryPoint]] = None

    class Config:
        from_attributes = True
