from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db, VideoModel
from backend.app.schemas.query import QueryRequest, QueryResponse
from backend.app.services.temporal_reasoner import TemporalReasoner

router = APIRouter(prefix="/videos", tags=["Temporal Query"])

@router.post("/{video_id}/query", response_model=QueryResponse)
def query_video_events(video_id: str, payload: QueryRequest, db: Session = Depends(get_db)):
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    reasoner = TemporalReasoner(db=db, video_id=video_id)
    response = reasoner.query(payload.query)
    return response
