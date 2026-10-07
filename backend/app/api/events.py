from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db, Event, EventRelationship
from backend.app.models.event import EventResponse, EventRelationshipResponse, TimelineResponse

router = APIRouter(prefix="/videos", tags=["Events & Timeline"])

@router.get("/{video_id}/events", response_model=List[EventResponse])
def get_video_events(video_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.video_id == video_id).order_by(Event.start_time.asc()).all()
    return [
        EventResponse(
            id=e.id,
            video_id=e.video_id,
            object_id=e.object_id,
            related_object_id=e.related_object_id,
            event_type=e.event_type,
            start_time=e.start_time,
            end_time=e.end_time,
            duration=e.duration,
            confidence=e.confidence,
            description=e.description,
            metadata=e.meta
        ) for e in events
    ]

@router.get("/{video_id}/timeline", response_model=TimelineResponse)
def get_video_timeline(video_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.video_id == video_id).order_by(Event.start_time.asc()).all()
    rels = db.query(EventRelationship).filter(EventRelationship.video_id == video_id).all()

    ev_models = [
        EventResponse(
            id=e.id,
            video_id=e.video_id,
            object_id=e.object_id,
            related_object_id=e.related_object_id,
            event_type=e.event_type,
            start_time=e.start_time,
            end_time=e.end_time,
            duration=e.duration,
            confidence=e.confidence,
            description=e.description,
            metadata=e.meta
        ) for e in events
    ]

    rel_models = [
        EventRelationshipResponse(
            id=r.id,
            video_id=r.video_id,
            source_event_id=r.source_event_id,
            relationship=r.relationship,
            target_event_id=r.target_event_id,
            time_difference=r.time_difference
        ) for r in rels
    ]

    return TimelineResponse(
        video_id=video_id,
        total_events=len(ev_models),
        events=ev_models,
        relationships=rel_models
    )
