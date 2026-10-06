import datetime
import os
from backend.app.database.session import SessionLocal, VideoModel, EventModel, EntityModel, init_db

def seed_demo_benchmark():
    init_db()
    db = SessionLocal()

    video_id = "warehouse_demo_01"
    existing = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    sample_filename = "sample_cctv.mp4"
    
    video = VideoModel(
        id=video_id,
        filename=sample_filename,
        original_name="warehouse_cctv_zone_b.mp4",
        fps=30.0,
        width=1280,
        height=720,
        total_frames=3600,
        duration_seconds=120.0,
        status="ready",
        progress_pct=100.0,
        current_stage_label="Temporal reasoning index complete",
        current_frame=3600,
        created_at=datetime.datetime.utcnow().isoformat(),
        has_annotated_video=False
    )
    db.add(video)
    db.commit()

    # Entities
    entities = [
        EntityModel(
            entity_id="person_1",
            video_id=video_id,
            track_id=1,
            class_name="person",
            first_seen=12.0,
            last_seen=53.0,
            duration=41.0,
            confidence=0.96,
            event_count=4,
            trajectory=[
                {"frame": 360, "timestamp": 12.0, "bbox": [120, 150, 240, 520], "confidence": 0.95},
                {"frame": 1050, "timestamp": 35.0, "bbox": [450, 210, 560, 540], "confidence": 0.97},
                {"frame": 1590, "timestamp": 53.0, "bbox": [880, 200, 990, 530], "confidence": 0.94},
            ]
        ),
        EntityModel(
            entity_id="backpack_1",
            video_id=video_id,
            track_id=2,
            class_name="backpack",
            first_seen=35.0,
            last_seen=105.0,
            duration=70.0,
            confidence=0.92,
            event_count=3,
            trajectory=[
                {"frame": 1050, "timestamp": 35.0, "bbox": [470, 480, 530, 550], "confidence": 0.91},
                {"frame": 2400, "timestamp": 80.0, "bbox": [470, 480, 530, 550], "confidence": 0.94},
                {"frame": 3150, "timestamp": 105.0, "bbox": [470, 480, 530, 550], "confidence": 0.90},
            ]
        ),
        EntityModel(
            entity_id="person_2",
            video_id=video_id,
            track_id=3,
            class_name="person",
            first_seen=81.0,
            last_seen=115.0,
            duration=34.0,
            confidence=0.95,
            event_count=3,
            trajectory=[
                {"frame": 2430, "timestamp": 81.0, "bbox": [920, 190, 1030, 530], "confidence": 0.95},
                {"frame": 3150, "timestamp": 105.0, "bbox": [480, 220, 590, 540], "confidence": 0.96},
                {"frame": 3450, "timestamp": 115.0, "bbox": [100, 180, 210, 510], "confidence": 0.94},
            ]
        ),
    ]
    for ent in entities:
        db.add(ent)
    db.commit()

    # Events
    events = [
        EventModel(
            event_id="ev_01",
            video_id=video_id,
            type="PERSON_ENTERED",
            entity_id="person_1",
            start_time=12.0,
            end_time=12.0,
            frame_start=360,
            frame_end=360,
            confidence=0.96,
            description="Person #1 entered monitored area at 00:12"
        ),
        EventModel(
            event_id="ev_02",
            video_id=video_id,
            type="OBJECT_APPEARED",
            entity_id="backpack_1",
            start_time=35.0,
            end_time=35.0,
            frame_start=1050,
            frame_end=1050,
            confidence=0.91,
            description="Backpack #1 appeared at 00:35"
        ),
        EventModel(
            event_id="ev_03",
            video_id=video_id,
            type="OBJECT_LEFT_UNATTENDED",
            entity_id="backpack_1",
            related_entity_id="person_1",
            start_time=47.0,
            end_time=105.0,
            frame_start=1410,
            frame_end=3150,
            confidence=0.94,
            description="Backpack #1 was left unattended at 00:47 by Person #1"
        ),
        EventModel(
            event_id="ev_04",
            video_id=video_id,
            type="PERSON_EXITED",
            entity_id="person_1",
            start_time=53.0,
            end_time=53.0,
            frame_start=1590,
            frame_end=1590,
            confidence=0.95,
            description="Person #1 exited monitored area at 00:53"
        ),
        EventModel(
            event_id="ev_05",
            video_id=video_id,
            type="PERSON_ENTERED",
            entity_id="person_2",
            start_time=81.0,
            end_time=81.0,
            frame_start=2430,
            frame_end=2430,
            confidence=0.95,
            description="Person #2 entered monitored area at 01:21"
        ),
        EventModel(
            event_id="ev_06",
            video_id=video_id,
            type="OBJECT_PICKED_UP",
            entity_id="backpack_1",
            related_entity_id="person_2",
            start_time=105.0,
            end_time=105.0,
            frame_start=3150,
            frame_end=3150,
            confidence=0.93,
            description="Person #2 picked up / interacted with Backpack #1 at 01:45"
        ),
        EventModel(
            event_id="ev_07",
            video_id=video_id,
            type="PERSON_EXITED",
            entity_id="person_2",
            start_time=115.0,
            end_time=115.0,
            frame_start=3450,
            frame_end=3450,
            confidence=0.94,
            description="Person #2 exited monitored area at 01:55"
        )
    ]
    for ev in events:
        db.add(ev)
    db.commit()
    db.close()
    print("Benchmark warehouse scenario seeded successfully into SQLite database!")

if __name__ == "__main__":
    seed_demo_benchmark()
