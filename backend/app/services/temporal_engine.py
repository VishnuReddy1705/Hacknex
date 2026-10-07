from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.database import Event, EventRelationship

class TemporalReasoningEngine:
    def __init__(self, db: Session, video_id: str):
        self.db = db
        self.video_id = video_id
        self.events: List[Event] = db.query(Event).filter(
            Event.video_id == video_id
        ).order_by(Event.start_time.asc()).all()

    def build_event_graph(self) -> List[EventRelationship]:
        """
        Builds the Object-Aware Temporal Event Graph.
        Populates directed edges representing:
        - BEFORE / AFTER
        - IMMEDIATELY_BEFORE / IMMEDIATELY_AFTER
        - DURING / OVERLAPS
        - STARTS_BEFORE / ENDS_AFTER
        """
        # Clear existing relationships for this video
        self.db.query(EventRelationship).filter(EventRelationship.video_id == self.video_id).delete()

        relationships: List[EventRelationship] = []
        n = len(self.events)

        for i in range(n):
            e_src = self.events[i]
            for j in range(n):
                if i == j:
                    continue
                e_tgt = self.events[j]

                # 1. Temporal Distance (start to start)
                time_diff = round(e_tgt.start_time - e_src.start_time, 2)

                # 2. Sequential & Immediate relations
                if j == i + 1:
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="IMMEDIATELY_BEFORE",
                        target_event_id=e_tgt.id,
                        time_difference=abs(time_diff)
                    ))
                elif j == i - 1:
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="IMMEDIATELY_AFTER",
                        target_event_id=e_tgt.id,
                        time_difference=abs(time_diff)
                    ))

                # 3. BEFORE / AFTER (all strictly ordered pairs)
                if e_src.end_time <= e_tgt.start_time:
                    delta = round(e_tgt.start_time - e_src.end_time, 2)
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="BEFORE",
                        target_event_id=e_tgt.id,
                        time_difference=delta
                    ))
                elif e_src.start_time >= e_tgt.end_time:
                    delta = round(e_src.start_time - e_tgt.end_time, 2)
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="AFTER",
                        target_event_id=e_tgt.id,
                        time_difference=delta
                    ))

                # 4. DURING / OVERLAPS
                if e_src.start_time >= e_tgt.start_time and e_src.end_time <= e_tgt.end_time and (e_tgt.duration > 0):
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="DURING",
                        target_event_id=e_tgt.id,
                        time_difference=0.0
                    ))
                elif (e_src.start_time < e_tgt.end_time and e_src.end_time > e_tgt.start_time):
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="OVERLAPS",
                        target_event_id=e_tgt.id,
                        time_difference=0.0
                    ))

                # 5. STARTS_BEFORE / ENDS_AFTER
                if e_src.start_time < e_tgt.start_time:
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="STARTS_BEFORE",
                        target_event_id=e_tgt.id,
                        time_difference=round(e_tgt.start_time - e_src.start_time, 2)
                    ))
                if e_src.end_time > e_tgt.end_time:
                    relationships.append(EventRelationship(
                        video_id=self.video_id,
                        source_event_id=e_src.id,
                        relationship="ENDS_AFTER",
                        target_event_id=e_tgt.id,
                        time_difference=round(e_src.end_time - e_tgt.end_time, 2)
                    ))

        for rel in relationships:
            self.db.add(rel)
        self.db.commit()
        return relationships

    # Deterministic query resolvers
    def get_events_before(self, target_event_id: str, immediate_only: bool = False) -> List[Event]:
        target = self._get_event_by_id(target_event_id)
        if not target:
            return []
        
        if immediate_only:
            rel = self.db.query(EventRelationship).filter(
                EventRelationship.video_id == self.video_id,
                EventRelationship.target_event_id == target_event_id,
                EventRelationship.relationship == "IMMEDIATELY_BEFORE"
            ).first()
            if rel:
                return [self._get_event_by_id(rel.source_event_id)]
            return []

        prior = [e for e in self.events if e.start_time < target.start_time and e.id != target.id]
        return prior

    def get_events_after(self, target_event_id: str, immediate_only: bool = False) -> List[Event]:
        target = self._get_event_by_id(target_event_id)
        if not target:
            return []

        if immediate_only:
            rel = self.db.query(EventRelationship).filter(
                EventRelationship.video_id == self.video_id,
                EventRelationship.source_event_id == target_event_id,
                EventRelationship.relationship == "IMMEDIATELY_BEFORE"
            ).first()
            if rel:
                return [self._get_event_by_id(rel.target_event_id)]
            return []

        subsequent = [e for e in self.events if e.start_time > target.start_time and e.id != target.id]
        return subsequent

    def get_events_between(self, start_time: float, end_time: float) -> List[Event]:
        return [e for e in self.events if start_time <= e.start_time <= end_time]

    def count_events(self, event_type: str = None, object_id: str = None) -> int:
        query = self.db.query(Event).filter(Event.video_id == self.video_id)
        if event_type:
            query = query.filter(Event.event_type.ilike(f"%{event_type}%"))
        if object_id:
            query = query.filter(Event.object_id.ilike(f"%{object_id}%"))
        return query.count()

    def get_time_difference(self, event_id_1: str, event_id_2: str) -> float:
        e1 = self._get_event_by_id(event_id_1)
        e2 = self._get_event_by_id(event_id_2)
        if not e1 or not e2:
            return 0.0
        return round(abs(e2.start_time - e1.start_time), 2)

    def _get_event_by_id(self, event_id: str) -> Optional[Event]:
        for e in self.events:
            if e.id == event_id:
                return e
        return self.db.query(Event).filter(Event.video_id == self.video_id, Event.id == event_id).first()
