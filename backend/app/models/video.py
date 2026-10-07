from pydantic import BaseModel
from typing import Optional, List

class VideoBase(BaseModel):
    filename: str
    original_name: str
    fps: float = 30.0
    width: int = 0
    height: int = 0
    total_frames: int = 0
    duration_seconds: float = 0.0
    status: str = "idle"
    progress_pct: float = 0.0
    current_stage_label: str = "Idle"
    error_message: Optional[str] = None
    has_annotated_video: bool = False

class VideoResponse(VideoBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True

class VideoStatusResponse(BaseModel):
    id: str
    status: str
    progress_pct: float
    current_stage_label: str
    current_frame: int = 0
    total_frames: int = 0
    error_message: Optional[str] = None
