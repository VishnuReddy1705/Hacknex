from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.app.database.session import get_db, EventModel
from backend.app.schemas.event import TemporalEventSchema

router = APIRouter(prefix="/videos", tags=["Events"])

@router.get("/{video_id}/events", response_model=List[TemporalEventSchema])
def get_video_events(
    video_id: str,
    category: Optional[str] = Query(None, description="all, people, objects, zones, anomalies"),
    db: Session = Depends(get_db)
):
    query = db.query(EventModel).filter(EventModel.video_id == video_id)

    if category and category.lower() != "all":
        cat = category.lower()
        if cat == "people":
            query = query.filter(EventModel.type.in_(["PERSON_ENTERED", "PERSON_EXITED", "LOITERING"]))
        elif cat == "objects":
            query = query.filter(EventModel.type.in_(["OBJECT_APPEARED", "OBJECT_DISAPPEARED", "OBJECT_STATIONARY", "OBJECT_INTERACTION"]))
        elif cat == "zones":
            query = query.filter(EventModel.type.in_(["ZONE_ENTRY", "ZONE_EXIT"]))
        elif cat == "anomalies":
            query = query.filter(EventModel.type.in_(["OBJECT_LEFT_UNATTENDED", "LOITERING"]))

    events = query.order_by(EventModel.start_time.asc()).all()

    # Convert to response schema
    results = []
    for ev in events:
        results.append(TemporalEventSchema(
            event_id=ev.event_id,
            video_id=ev.video_id,
            type=ev.type,
            entity_id=ev.entity_id,
            related_entity_id=ev.related_entity_id,
            start_time=ev.start_time,
            end_time=ev.end_time,
            frame_start=ev.frame_start,
            frame_end=ev.frame_end,
            confidence=ev.confidence,
            description=ev.description,
            metadata=ev.event_metadata
        ))
    return results

@router.get("/{video_id}/evidence/{event_id}", response_model=TemporalEventSchema)
def get_event_evidence(video_id: str, event_id: str, db: Session = Depends(get_db)):
    event = db.query(EventModel).filter(EventModel.video_id == video_id, EventModel.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event evidence not found")
    
    return TemporalEventSchema(
        event_id=event.event_id,
        video_id=event.video_id,
        type=event.type,
        entity_id=event.entity_id,
        related_entity_id=event.related_entity_id,
        start_time=event.start_time,
        end_time=event.end_time,
        frame_start=event.frame_start,
        frame_end=event.frame_end,
        confidence=event.confidence,
        description=event.description,
        metadata=event.event_metadata
    )
