from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AskRequest(BaseModel):
    question: str

class EvidenceItem(BaseModel):
    timestamp: str
    timestamp_seconds: float
    description: str
    event_id: Optional[str] = None
    object_id: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    timestamps: List[str]
    evidence: List[EvidenceItem]
    confidence: float = 1.0
    structured_query: Optional[Dict[str, Any]] = None
    graph_relation: Optional[Dict[str, Any]] = None
