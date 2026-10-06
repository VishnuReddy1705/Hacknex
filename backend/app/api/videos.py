import os
import uuid
import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.session import get_db, VideoModel
from backend.app.schemas.video import VideoResponse, VideoStatusResponse
import cv2

router = APIRouter(prefix="/videos", tags=["Videos"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "uploads"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@router.post("/upload", response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")
    
    allowed_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Supported: MP4, AVI, MOV, MKV, WEBM")

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, save_filename)

    # Save file to disk
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Extract real metadata with OpenCV
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Corrupted or unreadable video file")

    fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_seconds = (total_frames / fps) if fps > 0 else 0.0
    cap.release()

    video_record = VideoModel(
        id=video_id,
        filename=save_filename,
        original_name=file.filename,
        fps=round(fps, 2),
        width=width,
        height=height,
        total_frames=total_frames,
        duration_seconds=round(duration_seconds, 2),
        status="idle",
        progress_pct=0.0,
        current_stage_label="Uploaded and ready for analysis",
        current_frame=0,
        created_at=datetime.datetime.utcnow().isoformat(),
        has_annotated_video=False
    )
    db.add(video_record)
    db.commit()
    db.refresh(video_record)

    return video_record

@router.get("", response_model=List[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    videos = db.query(VideoModel).order_by(VideoModel.created_at.desc()).all()
    return videos

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoStatusResponse(
        id=video.id,
        status=video.status,
        progress_pct=video.progress_pct,
        current_stage_label=video.current_stage_label,
        current_frame=video.current_frame,
        total_frames=video.total_frames,
        error_message=video.error_message
    )

@router.post("/{video_id}/process")
def process_video_endpoint(
    video_id: str,
    frame_skip: int = 2,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status in ["detecting_entities", "tracking_entities", "extracting_events"]:
        return {"message": "Video is already being analyzed", "video_id": video.id}

    # Reset video status
    video.status = "reading_video"
    video.progress_pct = 2.0
    video.current_stage_label = "Starting video intelligence pipeline"
    video.error_message = None
    db.commit()

    from backend.app.services.video_processor import run_video_pipeline
    background_tasks.add_task(run_video_pipeline, video_id=video.id, frame_skip=frame_skip)

    return {"message": "Video analysis queued in background", "video_id": video.id}

def stream_file(file_path: str, request: Request):
    """Serve video supporting HTTP 206 Partial Content for precise seeking in HTML5 video players"""
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")

    if not range_header:
        def iterfile():
            with open(file_path, mode="rb") as file_like:
                yield from file_like
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={"Content-Length": str(file_size), "Accept-Ranges": "bytes"}
        )

    # Parse range header (e.g. bytes=0-1000)
    range_str = range_header.replace("bytes=", "")
    parts = range_str.split("-")
    start = int(parts[0]) if parts[0] else 0
    end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    content_length = (end - start) + 1

    def iter_range():
        with open(file_path, "rb") as video:
            video.seek(start)
            bytes_left = content_length
            chunk_size = 1024 * 1024 # 1MB
            while bytes_left > 0:
                read_size = min(chunk_size, bytes_left)
                data = video.read(read_size)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    response = StreamingResponse(
        iter_range(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
        }
    )
    return response

@router.get("/{video_id}/stream")
def stream_video(video_id: str, request: Request, annotated: bool = False, db: Session = Depends(get_db)):
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    target_path = os.path.join(UPLOAD_DIR, video.filename)
    if annotated and video.has_annotated_video:
        annotated_path = os.path.join(PROCESSED_DIR, f"{video.id}_annotated.mp4")
        if os.path.exists(annotated_path):
            target_path = annotated_path

    return stream_file(target_path, request)
