from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.session import get_db, EntityModel
from backend.app.schemas.entity import EntityTrackSchema

router = APIRouter(prefix="/videos", tags=["Entities"])

@router.get("/{video_id}/entities", response_model=List[EntityTrackSchema])
def get_video_entities(video_id: str, db: Session = Depends(get_db)):
    entities = db.query(EntityModel).filter(EntityModel.video_id == video_id).order_by(EntityModel.first_seen.asc()).all()
    results = []
    for ent in entities:
        results.append(EntityTrackSchema(
            entity_id=ent.entity_id,
            video_id=ent.video_id,
            track_id=ent.track_id,
            class_name=ent.class_name,
            first_seen=ent.first_seen,
            last_seen=ent.last_seen,
            duration=ent.duration,
            confidence=ent.confidence,
            event_count=ent.event_count,
            trajectory=ent.trajectory
        ))
    return results

@router.get("/{video_id}/entities/{entity_id}", response_model=EntityTrackSchema)
def get_entity_detail(video_id: str, entity_id: str, db: Session = Depends(get_db)):
    ent = db.query(EntityModel).filter(EntityModel.video_id == video_id, EntityModel.entity_id == entity_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return EntityTrackSchema(
        entity_id=ent.entity_id,
        video_id=ent.video_id,
        track_id=ent.track_id,
        class_name=ent.class_name,
        first_seen=ent.first_seen,
        last_seen=ent.last_seen,
        duration=ent.duration,
        confidence=ent.confidence,
        event_count=ent.event_count,
        trajectory=ent.trajectory
    )
