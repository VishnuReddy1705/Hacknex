import os
import cv2
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal, Video, TrackedObject, ObjectTrack, Event
from backend.app.services.tracker import ObjectTracker
from backend.app.services.event_detector import EventDetector
from backend.app.services.temporal_engine import TemporalReasoningEngine
from backend.app.utils.timestamps import seconds_to_timestamp

def run_video_pipeline(video_id: str):
    db: Session = SessionLocal()
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        db.close()
        return

    try:
        video_path = os.path.join(settings.UPLOAD_DIR, video.filename)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")

        # Stage 1: Reading Video
        video.status = "reading_video"
        video.current_stage_label = "Initializing video stream and AI model"
        video.progress_pct = 5.0
        db.commit()

        cap = cv2.VideoCapture(video_path)
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Configurable frame sampling stride:
        # e.g. If video is 30 FPS and PROCESS_FPS is 5, stride = 6 (processes 5 frames/sec)
        target_fps = settings.PROCESS_FPS
        stride = max(1, int(round(fps / target_fps))) if target_fps > 0 else 1

        annotated_filename = f"{video_id}_annotated.mp4"
        annotated_path = os.path.join(settings.PROCESSED_DIR, annotated_filename)

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(annotated_path, fourcc, fps / stride, (width, height))

        tracker = ObjectTracker()

        # Stage 2 & 3: Detection and Tracking
        video.status = "detecting_and_tracking"
        video.current_stage_label = f"Tracking entities (sampling @ {target_fps} FPS)"
        db.commit()

        objects_data: Dict[str, Dict[str, Any]] = {}
        frame_idx = 0
        processed_frames = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % stride != 0:
                continue

            processed_frames += 1
            # Exact original video timestamp preserved!
            timestamp = round(frame_idx / fps, 2)

            # Run tracking
            tracks = tracker.track_frame(frame, persist=True)
            annotated_frame = frame.copy()

            for trk in tracks:
                obj_id = trk["object_id"]
                track_id = trk["track_id"]
                cls_name = trk["class_name"]
                conf = trk["confidence"]
                x1, y1, x2, y2 = trk["bbox"]
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0

                label = f"{cls_name.capitalize()} {obj_id}"

                if obj_id not in objects_data:
                    objects_data[obj_id] = {
                        "track_id": track_id,
                        "class_name": cls_name,
                        "label": label,
                        "confidence": conf,
                        "history": []
                    }

                objects_data[obj_id]["history"].append({
                    "frame": frame_idx,
                    "timestamp": timestamp,
                    "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                    "center": (cx, cy),
                    "conf": round(conf, 2)
                })

                # Draw bounding box on annotated frame
                color = (79, 70, 229) if "person" in cls_name.lower() else (234, 88, 12)
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                txt = f"{obj_id} ({int(conf*100)}%)"
                cv2.putText(annotated_frame, txt, (int(x1), max(15, int(y1) - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Draw timecode overlay
            cv2.putText(annotated_frame, f"ChronosAI | {seconds_to_timestamp(timestamp)}", (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            out_writer.write(annotated_frame)

            if processed_frames % 20 == 0:
                pct = min(85.0, 10.0 + (frame_idx / max(1, total_frames)) * 75.0)
                video.progress_pct = round(pct, 1)
                video.current_frame = frame_idx
                video.current_stage_label = f"Processed {frame_idx}/{total_frames} frames ({seconds_to_timestamp(timestamp)})"
                db.commit()

        cap.release()
        out_writer.release()

        # Stage 4: Store Tracked Objects & Tracks
        video.status = "extracting_events"
        video.current_stage_label = "Converting trajectories into temporal events"
        video.progress_pct = 88.0
        db.commit()

        for obj_id, info in objects_data.items():
            hist = info["history"]
            if not hist:
                continue
            first_t = hist[0]["timestamp"]
            last_t = hist[-1]["timestamp"]
            dur = round(max(0.0, last_t - first_t), 2)
            avg_conf = sum(h["conf"] for h in hist) / len(hist)

            tracked_obj = TrackedObject(
                id=obj_id,
                video_id=video_id,
                track_id=info["track_id"],
                class_name=info["class_name"],
                label=info["label"],
                first_seen=first_t,
                last_seen=last_t,
                duration=dur,
                confidence=round(avg_conf, 2)
            )
            db.merge(tracked_obj)

            # Store sampled track points
            for pt in hist[::max(1, len(hist)//30)]:
                b = pt["bbox"]
                tr = ObjectTrack(
                    video_id=video_id,
                    object_id=obj_id,
                    frame_number=pt["frame"],
                    timestamp=pt["timestamp"],
                    bbox_x1=b[0],
                    bbox_y1=b[1],
                    bbox_x2=b[2],
                    bbox_y2=b[3],
                    confidence=pt["conf"]
                )
                db.add(tr)

        db.commit()

        # Stage 5: Event Detection
        detector = EventDetector(fps=fps, width=width, height=height)
        events_list = detector.detect_events_from_tracks(objects_data)

        for ev_data in events_list:
            ev = Event(
                id=ev_data["id"],
                video_id=video_id,
                object_id=ev_data["object_id"],
                related_object_id=ev_data.get("related_object_id"),
                event_type=ev_data["event_type"],
                start_time=ev_data["start_time"],
                end_time=ev_data["end_time"],
                duration=ev_data["duration"],
                confidence=ev_data["confidence"],
                description=ev_data["description"]
            )
            ev.meta = ev_data.get("metadata", {})
            db.merge(ev)

        db.commit()

        # Stage 6: Build Temporal Event Graph
        video.status = "indexing_temporal_graph"
        video.current_stage_label = "Constructing Temporal Event Graph"
        video.progress_pct = 95.0
        db.commit()

        engine = TemporalReasoningEngine(db=db, video_id=video_id)
        engine.build_event_graph()

        # Complete!
        video.status = "ready"
        video.progress_pct = 100.0
        video.current_stage_label = "Temporal event graph complete & query ready"
        video.current_frame = total_frames
        video.has_annotated_video = os.path.exists(annotated_path)
        db.commit()

    except Exception as e:
        db.rollback()
        video.status = "failed"
        video.error_message = str(e)
        video.current_stage_label = f"Processing failed: {str(e)}"
        db.commit()
    finally:
        db.close()
