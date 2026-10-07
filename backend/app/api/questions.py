import json
import uuid
import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db, Video, Question, Answer
from backend.app.models.answer import AskRequest, AskResponse
from backend.app.services.question_parser import QuestionParser
from backend.app.services.evidence_retriever import EvidenceRetriever
from backend.app.services.answer_generator import AnswerGenerator
from backend.app.services.vlm_service import VLMService

router = APIRouter(prefix="/videos", tags=["Question Answering"])

parser = QuestionParser()
generator = AnswerGenerator()
vlm = VLMService()

@router.post("/{video_id}/ask", response_model=AskResponse)
def ask_video(video_id: str, payload: AskRequest, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # 1. Parse question into structured temporal query
    parsed = parser.parse(payload.question)

    # 2. Retrieve relevant evidence from SQLite temporal graph
    retriever = EvidenceRetriever(db=db, video_id=video_id)
    retrieved = retriever.retrieve(parsed)

    # 3. Generate initial timestamp-grounded answer deterministically
    deterministic_response = generator.generate(parsed, retrieved)

    # 4. Optional VLM/LLM enhancement if API key exists
    if vlm.is_available:
        enhanced = vlm.verify_or_synthesize(
            question=payload.question,
            structured_evidence=[e.dict() for e in deterministic_response.evidence],
            fallback_answer=deterministic_response.answer
        )
        final_answer_text = enhanced["answer"]
    else:
        final_answer_text = deterministic_response.answer

    response = AskResponse(
        answer=final_answer_text,
        timestamps=deterministic_response.timestamps,
        evidence=deterministic_response.evidence,
        confidence=deterministic_response.confidence,
        structured_query=parsed,
        graph_relation=deterministic_response.graph_relation
    )

    # 5. Persist question & answer in database
    q_id = str(uuid.uuid4())
    question_record = Question(
        id=q_id,
        video_id=video_id,
        question_text=payload.question,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    db.add(question_record)

    answer_record = Answer(
        id=str(uuid.uuid4()),
        question_id=q_id,
        answer_text=response.answer,
        confidence=response.confidence,
        timestamps_json=json.dumps(response.timestamps),
        evidence_json=json.dumps([e.dict() for e in response.evidence]),
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )
    db.add(answer_record)
    db.commit()

    return response
