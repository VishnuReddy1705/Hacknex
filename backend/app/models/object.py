from pydantic import BaseModel
from typing import Optional, List

class TrackPoint(BaseModel):
    frame_number: int
    timestamp: float
    bbox: List[float]
    confidence: float

class ObjectResponse(BaseModel):
    id: str
    video_id: str
    track_id: int
    class_name: str
    label: str
    first_seen: float
    last_seen: float
    duration: float
    confidence: float
    trajectory: Optional[List[TrackPoint]] = []

    class Config:
        from_attributes = True
