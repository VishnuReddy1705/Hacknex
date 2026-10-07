from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.database import Event, EventRelationship
from backend.app.models.answer import EvidenceItem
from backend.app.utils.timestamps import seconds_to_timestamp

class EvidenceRetriever:
    def __init__(self, db: Session, video_id: str):
        self.db = db
        self.video_id = video_id
        self.events: List[Event] = db.query(Event).filter(
            Event.video_id == video_id
        ).order_by(Event.start_time.asc()).all()

    def retrieve(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        relation = parsed_query.get("relation")
        target_event = parsed_query.get("target_event")
        target_obj = parsed_query.get("target_object")

        # 1. FIRST EVENT
        if parsed_query.get("is_first"):
            if not self.events:
                return {"evidence": [], "anchor": None, "results": []}
            ev = self.events[0]
            return {
                "evidence": [self._to_evidence(ev)],
                "anchor": ev,
                "results": [ev]
            }

        # 2. LAST EVENT
        if parsed_query.get("is_last") and not relation in ("BEFORE", "AFTER", "IMMEDIATELY_BEFORE"):
            if not self.events:
                return {"evidence": [], "anchor": None, "results": []}
            ev = self.events[-1]
            return {
                "evidence": [self._to_evidence(ev)],
                "anchor": ev,
                "results": [ev]
            }

        # 3. COUNT
        if parsed_query.get("is_count"):
            matched = self._filter_events(target_event, target_obj)
            return {
                "evidence": [self._to_evidence(e) for e in matched],
                "anchor": None,
                "results": matched
            }

        # 4. DURATION
        if parsed_query.get("is_duration"):
            matched = self._filter_events(target_event, target_obj)
            return {
                "evidence": [self._to_evidence(e) for e in matched],
                "anchor": None,
                "results": matched
            }

        # 5. BETWEEN
        if relation == "BETWEEN" and parsed_query.get("time_range"):
            t_min, t_max = parsed_query["time_range"]
            matched = [e for e in self.events if t_min <= e.start_time <= t_max]
            return {
                "evidence": [self._to_evidence(e) for e in matched],
                "anchor": None,
                "results": matched
            }

        # 6. BEFORE / IMMEDIATELY_BEFORE
        if relation in ("BEFORE", "IMMEDIATELY_BEFORE"):
            anchor = self._find_anchor(parsed_query)
            if not anchor:
                return {"evidence": [], "anchor": None, "results": []}

            immediate = (relation == "IMMEDIATELY_BEFORE")
            if immediate:
                # Use graph table for IMMEDIATELY_BEFORE
                rel = self.db.query(EventRelationship).filter(
                    EventRelationship.video_id == self.video_id,
                    EventRelationship.target_event_id == anchor.id,
                    EventRelationship.relationship == "IMMEDIATELY_BEFORE"
                ).first()
                if rel:
                    prev = self._get_by_id(rel.source_event_id)
                    results = [prev] if prev else []
                else:
                    priors = [e for e in self.events if e.start_time < anchor.start_time and e.id != anchor.id]
                    results = [priors[-1]] if priors else []
            else:
                results = [e for e in self.events if e.start_time < anchor.start_time and e.id != anchor.id]

            evidence = [self._to_evidence(r) for r in results] + [self._to_evidence(anchor)]
            return {
                "evidence": evidence,
                "anchor": anchor,
                "results": results
            }

        # 7. AFTER / IMMEDIATELY_AFTER
        if relation in ("AFTER", "IMMEDIATELY_AFTER"):
            anchor = self._find_anchor(parsed_query)
            if not anchor:
                return {"evidence": [], "anchor": None, "results": []}

            immediate = (relation == "IMMEDIATELY_AFTER")
            if immediate:
                rel = self.db.query(EventRelationship).filter(
                    EventRelationship.video_id == self.video_id,
                    EventRelationship.source_event_id == anchor.id,
                    EventRelationship.relationship == "IMMEDIATELY_BEFORE"
                ).first()
                if rel:
                    nxt = self._get_by_id(rel.target_event_id)
                    results = [nxt] if nxt else []
                else:
                    subs = [e for e in self.events if e.start_time > anchor.start_time and e.id != anchor.id]
                    results = [subs[0]] if subs else []
            else:
                subs = [e for e in self.events if e.start_time > anchor.start_time and e.id != anchor.id]
                # If question asked "who entered", filter for entry
                if parsed_query.get("is_who") or "enter" in parsed_query.get("raw_question", "").lower():
                    entry_subs = [e for e in subs if "enter" in e.event_type.lower() or "enter" in e.description.lower()]
                    results = entry_subs if entry_subs else subs
                else:
                    results = subs

            evidence = [self._to_evidence(anchor)] + [self._to_evidence(r) for r in results[:2]]
            return {
                "evidence": evidence,
                "anchor": anchor,
                "results": results
            }

        # Default fallback: keyword matching
        words = parsed_query.get("raw_question", "").lower().split()
        matched = []
        for e in self.events:
            if any(w in e.description.lower() for w in words if len(w) > 3):
                matched.append(e)

        return {
            "evidence": [self._to_evidence(e) for e in matched],
            "anchor": None,
            "results": matched
        }

    def _find_anchor(self, parsed: Dict[str, Any]) -> Optional[Event]:
        target_event = parsed.get("target_event")
        target_obj = parsed.get("target_object")

        # Specific event/object checks
        if parsed.get("is_last") and self.events:
            return self.events[-1]
        if parsed.get("is_first") and self.events:
            return self.events[0]

        # Prioritize matching BOTH target_event AND target_obj
        if target_event and target_obj:
            for e in self.events:
                desc_l = e.description.lower()
                ev_type_l = e.event_type.lower()
                if (target_event.lower() in desc_l or target_event.lower() in ev_type_l) and (target_obj.lower() in desc_l or (e.object_id and target_obj.lower() in e.object_id.lower())):
                    return e

        # Match by target_event
        if target_event:
            for e in self.events:
                desc_l = e.description.lower()
                if target_event.lower() in desc_l or target_event.lower() in e.event_type.lower():
                    return e

        # Match by target_obj
        if target_obj:
            for e in self.events:
                desc_l = e.description.lower()
                if target_obj.lower() in desc_l or (e.object_id and target_obj.lower() in e.object_id.lower()):
                    return e
        
        # Fallback to last event or first event
        return self.events[-1] if self.events else None

    def _filter_events(self, target_event: Optional[str], target_obj: Optional[str]) -> List[Event]:
        res = []
        for e in self.events:
            desc_l = e.description.lower()
            matches_ev = not target_event or (target_event.lower() in desc_l or target_event.lower() in e.event_type.lower())
            matches_obj = not target_obj or (target_obj.lower() in desc_l or (e.object_id and target_obj.lower() in e.object_id.lower()))
            if matches_ev and matches_obj:
                res.append(e)
        return res

    def _get_by_id(self, eid: str) -> Optional[Event]:
        for e in self.events:
            if e.id == eid:
                return e
        return None

    def _to_evidence(self, e: Event) -> EvidenceItem:
        return EvidenceItem(
            timestamp=seconds_to_timestamp(e.start_time),
            timestamp_seconds=e.start_time,
            description=e.description,
            event_id=e.id,
            object_id=e.object_id
        )
