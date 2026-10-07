import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db, Video, TrackedObject
from backend.app.models.video import VideoResponse, VideoStatusResponse
from backend.app.models.object import ObjectResponse
from backend.app.utils.video_utils import extract_video_metadata
from backend.app.services.video_processor import run_video_pipeline

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/upload", response_model=VideoResponse)
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing")

    allowed_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Unsupported format {ext}. Allowed: MP4, AVI, MOV, MKV, WEBM")

    video_id = str(uuid.uuid4())
    save_filename = f"{video_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        meta = extract_video_metadata(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Corrupt or unreadable video file: {str(e)}")

    video = Video(
        id=video_id,
        filename=save_filename,
        original_name=file.filename,
        fps=meta["fps"],
        width=meta["width"],
        height=meta["height"],
        total_frames=meta["total_frames"],
        duration_seconds=meta["duration_seconds"],
        status="idle",
        progress_pct=0.0,
        current_stage_label="Uploaded & ready for processing",
        current_frame=0,
        has_annotated_video=False
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video

@router.post("/{video_id}/process")
def process_video(video_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if video.status in ("reading_video", "detecting_and_tracking", "extracting_events", "indexing_temporal_graph"):
        return {"message": "Video is already being processed", "video_id": video.id}

    video.status = "reading_video"
    video.progress_pct = 2.0
    video.current_stage_label = "Starting video processing pipeline"
    video.error_message = None
    db.commit()

    background_tasks.add_task(run_video_pipeline, video_id=video.id)
    return {"message": "Video processing queued", "video_id": video.id}

@router.get("", response_model=List[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    return db.query(Video).order_by(Video.created_at.desc()).all()

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
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

@router.get("/{video_id}/objects", response_model=List[ObjectResponse])
def get_video_objects(video_id: str, db: Session = Depends(get_db)):
    objs = db.query(TrackedObject).filter(TrackedObject.video_id == video_id).order_by(TrackedObject.first_seen.asc()).all()
    res = []
    for o in objs:
        res.append(ObjectResponse(
            id=o.id,
            video_id=o.video_id,
            track_id=o.track_id,
            class_name=o.class_name,
            label=o.label,
            first_seen=o.first_seen,
            last_seen=o.last_seen,
            duration=o.duration,
            confidence=o.confidence,
            trajectory=[]
        ))
    return res

@router.get("/{video_id}/stream")
def stream_video(video_id: str, request: Request, annotated: bool = False, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    target_path = os.path.join(settings.UPLOAD_DIR, video.filename)
    if annotated and video.has_annotated_video:
        annot_path = os.path.join(settings.PROCESSED_DIR, f"{video.id}_annotated.mp4")
        if os.path.exists(annot_path):
            target_path = annot_path

    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = os.path.getsize(target_path)
    range_header = request.headers.get("Range")

    if not range_header:
        def iterfile():
            with open(target_path, "rb") as f:
                yield from f
        return StreamingResponse(iterfile(), media_type="video/mp4", headers={"Content-Length": str(file_size)})

    range_str = range_header.replace("bytes=", "")
    parts = range_str.split("-")
    start = int(parts[0]) if parts[0] else 0
    end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
    content_length = (end - start) + 1

    def iter_range():
        with open(target_path, "rb") as f:
            f.seek(start)
            left = content_length
            chunk = 1024 * 1024
            while left > 0:
                to_read = min(chunk, left)
                data = f.read(to_read)
                if not data:
                    break
                left -= len(data)
                yield data

    return StreamingResponse(
        iter_range(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length)
        }
    )
