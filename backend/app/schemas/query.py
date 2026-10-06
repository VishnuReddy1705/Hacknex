from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    query: str

class TemporalEvidenceItem(BaseModel):
    timestamp: float
    label: str
    event_id: Optional[str] = None
    entity_id: Optional[str] = None
    description: str

class TemporalRelationStep(BaseModel):
    from_event: str
    to_event: str
    delta_seconds: float
    relation: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    relevant_entities: List[str] = []
    confidence: float = 1.0
    evidence: List[TemporalEvidenceItem] = []
    temporal_relation: Optional[TemporalRelationStep] = None
    reasoning_trace: List[str] = []
