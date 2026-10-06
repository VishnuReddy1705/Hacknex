import os
import cv2
import torch
import numpy as np
from typing import Dict, Any
from ultralytics import YOLO
from sqlalchemy.orm import Session

from backend.app.database.session import SessionLocal, VideoModel
from backend.app.services.event_engine import EventEngine

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "uploads"))
PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed"))
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Target surveillance classes in COCO:
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 7: truck, 24: backpack, 26: handbag, 28: suitcase
TARGET_CLASSES = [0, 1, 2, 3, 7, 24, 26, 28]

def run_video_pipeline(video_id: str, frame_skip: int = 2):
    """
    Background worker that runs YOLOv8 + ByteTrack on uploaded video,
    computes frame-exact timestamps, generates annotated playback,
    and runs the EventEngine to populate the SQLite temporal index.
    """
    db: Session = SessionLocal()
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        db.close()
        return

    try:
        video_path = os.path.join(UPLOAD_DIR, video.filename)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file {video_path} not found")

        # Update status
        video.status = "reading_video"
        video.current_stage_label = "Initializing video stream and AI model"
        video.progress_pct = 5.0
        db.commit()

        cap = cv2.VideoCapture(video_path)
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Output annotated video path
        annotated_filename = f"{video_id}_annotated.mp4"
        annotated_path = os.path.join(PROCESSED_DIR, annotated_filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(annotated_path, fourcc, fps / max(1, frame_skip), (width, height))

        # Load YOLO model
        video.status = "detecting_entities"
        video.current_stage_label = "Running YOLOv8 detection & ByteTrack tracking"
        db.commit()

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = YOLO("yolov8n.pt")

        raw_tracks: Dict[str, Dict[str, Any]] = {}
        frame_idx = 0
        processed_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue

            processed_count += 1
            timestamp = round(frame_idx / fps, 2)

            # Run tracking with ByteTrack
            results = model.track(
                frame,
                persist=True,
                classes=TARGET_CLASSES,
                device=device,
                verbose=False,
                conf=0.35
            )

            annotated_frame = frame.copy()

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    # Check if track id is assigned
                    if box.id is None:
                        continue

                    track_id = int(box.id[0])
                    cls_id = int(box.cls[0])
                    cls_name = model.names.get(cls_id, "object")
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    x1, y1, x2, y2 = xyxy
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0

                    entity_id = f"{cls_name}_{track_id}"

                    if entity_id not in raw_tracks:
                        raw_tracks[entity_id] = {
                            "track_id": track_id,
                            "class_name": cls_name,
                            "confidence": conf,
                            "history": []
                        }

                    raw_tracks[entity_id]["history"].append({
                        "frame": frame_idx,
                        "timestamp": timestamp,
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "center": (cx, cy),
                        "conf": round(conf, 2)
                    })

                    # Draw clean bounding box and label onto annotated frame
                    color = (79, 70, 229) if "person" in cls_name else (234, 88, 12) # Indigo for person, orange for objects
                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    
                    label_text = f"{cls_name.upper()} #{track_id} ({int(conf*100)}%)"
                    (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(annotated_frame, (int(x1), int(y1) - th - 6), (int(x1) + tw + 4, int(y1)), color, -1)
                    cv2.putText(annotated_frame, label_text, (int(x1) + 2, int(y1) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # Draw timestamp overlay in top left corner
            ts_str = f"T: {int(timestamp//60):02d}:{int(timestamp%60):02d}.{int((timestamp%1)*10)} | F: {frame_idx}"
            cv2.putText(annotated_frame, ts_str, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(annotated_frame, ts_str, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)

            out_writer.write(annotated_frame)

            # Update progress periodically
            if processed_count % 30 == 0:
                pct = min(85.0, 10.0 + (frame_idx / max(1, total_frames)) * 75.0)
                video.progress_pct = round(pct, 1)
                video.current_frame = frame_idx
                video.current_stage_label = f"Tracking entities (Frame {frame_idx}/{total_frames})"
                db.commit()

        cap.release()
        out_writer.release()

        # Event Extraction Stage
        video.status = "extracting_events"
        video.current_stage_label = "Extracting temporal events & spatial interactions"
        video.progress_pct = 90.0
        db.commit()

        event_engine = EventEngine(
            db=db,
            video_id=video_id,
            fps=fps,
            width=width,
            height=height
        )
        event_engine.process_and_index(raw_tracks)

        # Mark ready
        video.status = "ready"
        video.progress_pct = 100.0
        video.current_stage_label = "Temporal reasoning index complete"
        video.current_frame = total_frames
        video.has_annotated_video = os.path.exists(annotated_path)
        db.commit()

    except Exception as e:
        db.rollback()
        video.status = "failed"
        video.error_message = str(e)
        video.current_stage_label = f"Failed: {str(e)}"
        db.commit()
    finally:
        db.close()
