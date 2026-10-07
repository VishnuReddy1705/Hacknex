import datetime
import os
from backend.app.config import settings
from backend.app.database import SessionLocal, Video, TrackedObject, Event, init_db
from backend.app.services.temporal_engine import TemporalReasoningEngine

def seed_timesense_demo():
    init_db()
    db = SessionLocal()

    video_id = "timesense_demo_cctv"
    existing = db.query(Video).filter(Video.id == video_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    sample_filename = "sample_cctv.mp4"
    video = Video(
        id=video_id,
        filename=sample_filename,
        original_name="cctv_facility_zone_04.mp4",
        fps=30.0,
        width=1280,
        height=720,
        total_frames=5700, # 190 seconds (3m 10s)
        duration_seconds=190.0,
        status="ready",
        progress_pct=100.0,
        current_stage_label="Temporal event graph indexed & ready",
        current_frame=5700,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        has_annotated_video=False
    )
    db.add(video)
    db.commit()

    # Tracked Objects
    objects = [
        TrackedObject(
            id="truck_1",
            video_id=video_id,
            track_id=1,
            class_name="truck",
            label="Delivery Truck #1",
            first_seen=5.0,
            last_seen=60.0,
            duration=55.0,
            confidence=0.96
        ),
        TrackedObject(
            id="P01",
            video_id=video_id,
            track_id=2,
            class_name="person",
            label="Worker P01",
            first_seen=18.0,
            last_seen=40.0,
            duration=22.0,
            confidence=0.94
        ),
        TrackedObject(
            id="machine_1",
            video_id=video_id,
            track_id=3,
            class_name="machine",
            label="Machinery Unit 1",
            first_seen=0.0,
            last_seen=190.0,
            duration=190.0,
            confidence=0.99
        ),
        TrackedObject(
            id="alarm_system",
            video_id=video_id,
            track_id=4,
            class_name="alarm",
            label="Facility Safety Alarm",
            first_seen=47.0,
            last_seen=60.0,
            duration=13.0,
            confidence=0.98
        )
    ]
    for o in objects:
        db.add(o)
    db.commit()

    # Exact events from Section 18
    events_data = [
        ("E01", "truck_1", None, "OBJECT_APPEARED", 5.0, 5.0, 0.0, 0.95, "Truck appeared in driveway at 00:05"),
        ("E02", "truck_1", None, "ARRIVED", 12.0, 12.0, 0.0, 0.96, "Delivery truck arrived at loading dock at 00:12"),
        ("E03", "P01", "truck_1", "INTERACTION", 20.0, 20.0, 0.0, 0.92, "Worker P01 approached truck at 00:20"),
        ("E04", "P01", None, "ENTERED_ZONE", 27.0, 27.0, 0.0, 0.97, "Worker P01 entered restricted zone at 00:27"),
        ("E05", "P01", None, "EXITED_ZONE", 35.0, 35.0, 0.0, 0.95, "Worker P01 exited restricted zone at 00:35"),
        ("E06", "alarm_system", None, "ALARM", 47.0, 47.0, 0.0, 0.98, "Safety alarm activated at 00:47"),
        ("E07", "machine_1", None, "STARTED", 80.0, 80.0, 0.0, 0.94, "Machine started operation at 01:20"),
        ("E08", "machine_1", None, "STOPPED", 130.0, 130.0, 0.0, 0.96, "Machine stopped at 02:10"),
        ("E09", "machine_1", None, "STARTED", 155.0, 155.0, 0.0, 0.93, "Machine started operation at 02:35"),
        ("E10", "machine_1", None, "STOPPED", 190.0, 190.0, 0.0, 0.96, "Machine stopped at 03:10"),
    ]

    for eid, oid, roid, etype, tstart, tend, dur, conf, desc in events_data:
        ev = Event(
            id=eid,
            video_id=video_id,
            object_id=oid,
            related_object_id=roid,
            event_type=etype,
            start_time=tstart,
            end_time=tend,
            duration=dur,
            confidence=conf,
            description=desc
        )
        db.add(ev)
    db.commit()

    # Construct the Temporal Event Graph
    engine = TemporalReasoningEngine(db=db, video_id=video_id)
    relationships = engine.build_event_graph()
    db.close()
    print(f"TimeSense AI benchmark scenario seeded successfully! ({len(events_data)} events, {len(relationships)} graph edges)")

if __name__ == "__main__":
    seed_timesense_demo()
