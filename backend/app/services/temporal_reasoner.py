import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database.session import EventModel, EntityModel
from backend.app.schemas.query import QueryResponse, TemporalEvidenceItem, TemporalRelationStep

def format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 10))
    if ms > 0:
        return f"{m:02d}:{s:02d}.{ms}"
    return f"{m:02d}:{s:02d}"

class TemporalReasoner:
    def __init__(self, db: Session, video_id: str):
        self.db = db
        self.video_id = video_id
        self.events: List[EventModel] = db.query(EventModel).filter(
            EventModel.video_id == video_id
        ).order_by(EventModel.start_time.asc()).all()
        self.entities: List[EntityModel] = db.query(EntityModel).filter(
            EntityModel.video_id == video_id
        ).order_by(EntityModel.first_seen.asc()).all()

    def query(self, user_question: str) -> QueryResponse:
        q = user_question.strip().lower()
        reasoning_trace = []

        if not self.events and not self.entities:
            return QueryResponse(
                query=user_question,
                answer="No events or entities have been indexed for this video yet. Please run video analysis first.",
                timestamp_start=None,
                timestamp_end=None,
                relevant_entities=[],
                confidence=0.0,
                evidence=[],
                temporal_relation=None,
                reasoning_trace=["Database contains 0 events and 0 entities."]
            )

        # 1. "FIRST EVENT" / "WHAT HAPPENED FIRST" / "FIRST THING"
        if "first" in q and ("event" in q or "happened" in q or "occurred" in q or "thing" in q):
            reasoning_trace.append("Detected query intent: FIRST_EVENT")
            ev = self.events[0]
            answer = f"The first recorded event was '{ev.description}' at {format_timestamp(ev.start_time)}."
            evidence = [
                TemporalEvidenceItem(
                    timestamp=ev.start_time,
                    label=f"{format_timestamp(ev.start_time)} {ev.description}",
                    event_id=ev.event_id,
                    entity_id=ev.entity_id,
                    description=ev.description
                )
            ]
            return QueryResponse(
                query=user_question,
                answer=answer,
                timestamp_start=ev.start_time,
                timestamp_end=ev.end_time,
                relevant_entities=[ev.entity_id],
                confidence=ev.confidence,
                evidence=evidence,
                reasoning_trace=reasoning_trace
            )

        # 2. "LAST EVENT" / "FINAL EVENT" / "WHAT HAPPENED LAST"
        if ("last" in q or "final" in q) and ("event" in q or "happened" in q or "occurred" in q) and not ("before" in q or "after" in q):
            reasoning_trace.append("Detected query intent: LAST_EVENT")
            ev = self.events[-1]
            answer = f"The last recorded event was '{ev.description}' at {format_timestamp(ev.start_time)}."
            evidence = [
                TemporalEvidenceItem(
                    timestamp=ev.start_time,
                    label=f"{format_timestamp(ev.start_time)} {ev.description}",
                    event_id=ev.event_id,
                    entity_id=ev.entity_id,
                    description=ev.description
                )
            ]
            return QueryResponse(
                query=user_question,
                answer=answer,
                timestamp_start=ev.start_time,
                timestamp_end=ev.end_time,
                relevant_entities=[ev.entity_id],
                confidence=ev.confidence,
                evidence=evidence,
                reasoning_trace=reasoning_trace
            )

        # 3. "SHOW FULL SEQUENCE" / "COMPLETE SEQUENCE" / "TIMELINE" / "SUMMARY"
        if ("sequence" in q or "all events" in q or "timeline" in q or "summary" in q or "what happened" == q.rstrip('?')):
            reasoning_trace.append("Detected query intent: FULL_SEQUENCE")
            count = len(self.events)
            evidence = [
                TemporalEvidenceItem(
                    timestamp=e.start_time,
                    label=f"{format_timestamp(e.start_time)} {e.description}",
                    event_id=e.event_id,
                    entity_id=e.entity_id,
                    description=e.description
                ) for e in self.events
            ]
            answer = f"The video contains {count} sequential events from {format_timestamp(self.events[0].start_time)} to {format_timestamp(self.events[-1].end_time)}."
            return QueryResponse(
                query=user_question,
                answer=answer,
                timestamp_start=self.events[0].start_time,
                timestamp_end=self.events[-1].end_time,
                relevant_entities=list({e.entity_id for e in self.events}),
                confidence=1.0,
                evidence=evidence,
                reasoning_trace=reasoning_trace
            )

        # 4. "HOW LONG WAS ... UNATTENDED / STATIONARY" / DURATION OF OBJECT
        if "how long" in q and ("unattended" in q or "stationary" in q or "bag" in q or "backpack" in q or "object" in q):
            reasoning_trace.append("Detected query intent: HOW_LONG_UNATTENDED")
            unattended_evs = [e for e in self.events if e.type in ("OBJECT_LEFT_UNATTENDED", "OBJECT_STATIONARY")]
            if unattended_evs:
                ev = unattended_evs[0]
                duration = round(ev.end_time - ev.start_time, 1)
                
                # Check if pickup event happened
                pickup_evs = [e for e in self.events if e.type == "OBJECT_PICKED_UP" and e.start_time >= ev.start_time]
                resolved_by = f"until it was picked up at {format_timestamp(pickup_evs[0].start_time)}" if pickup_evs else f"until {format_timestamp(ev.end_time)}"

                answer = f"{ev.entity_id} remained unattended for {duration} seconds, from {format_timestamp(ev.start_time)} {resolved_by}."
                evidence = [
                    TemporalEvidenceItem(
                        timestamp=ev.start_time,
                        label=f"{format_timestamp(ev.start_time)} {ev.description}",
                        event_id=ev.event_id,
                        entity_id=ev.entity_id,
                        description=ev.description
                    )
                ]
                if pickup_evs:
                    evidence.append(
                        TemporalEvidenceItem(
                            timestamp=pickup_evs[0].start_time,
                            label=f"{format_timestamp(pickup_evs[0].start_time)} {pickup_evs[0].description}",
                            event_id=pickup_evs[0].event_id,
                            entity_id=pickup_evs[0].entity_id,
                            description=pickup_evs[0].description
                        )
                    )
                return QueryResponse(
                    query=user_question,
                    answer=answer,
                    timestamp_start=ev.start_time,
                    timestamp_end=pickup_evs[0].start_time if pickup_evs else ev.end_time,
                    relevant_entities=[ev.entity_id] + ([pickup_evs[0].entity_id] if pickup_evs else []),
                    confidence=ev.confidence,
                    evidence=evidence,
                    temporal_relation=TemporalRelationStep(
                        from_event="Object unattended",
                        to_event="Object picked up / cleared",
                        delta_seconds=duration,
                        relation="duration"
                    ) if pickup_evs else None,
                    reasoning_trace=reasoning_trace
                )

        # 5. "HOW MANY PEOPLE" / "HOW MANY"
        if "how many people" in q or ("how many" in q and "person" in q):
            reasoning_trace.append("Detected query intent: COUNT_PEOPLE")
            people = [ent for ent in self.entities if "person" in ent.class_name.lower()]
            p_ids = [p.entity_id for p in people]
            entry_evs = [e for e in self.events if e.type in ("PERSON_ENTERED", "ZONE_ENTRY") and "person" in e.entity_id.lower()]
            evidence = [
                TemporalEvidenceItem(
                    timestamp=e.start_time,
                    label=f"{format_timestamp(e.start_time)} {e.description}",
                    event_id=e.event_id,
                    entity_id=e.entity_id,
                    description=e.description
                ) for e in entry_evs
            ]
            answer = f"A total of {len(people)} unique individuals were tracked in the video ({', '.join(p_ids)})."
            return QueryResponse(
                query=user_question,
                answer=answer,
                timestamp_start=entry_evs[0].start_time if entry_evs else None,
                timestamp_end=entry_evs[-1].end_time if entry_evs else None,
                relevant_entities=p_ids,
                confidence=1.0,
                evidence=evidence,
                reasoning_trace=reasoning_trace
            )

        # 6. "WHAT HAPPENED BEFORE ..." / "WHO ENTERED BEFORE ..."
        if "before" in q:
            reasoning_trace.append("Detected query intent: BEFORE_RELATION")
            # Find the anchor event/entity mentioned
            target_ev = self._find_matching_anchor_event(q)
            if target_ev:
                cutoff = target_ev.start_time
                prior_events = [e for e in self.events if e.event_id != target_ev.event_id and (e.end_time <= cutoff or e.start_time < cutoff)]
                if prior_events:
                    immediate_prev = prior_events[-1]
                    delta = round(cutoff - immediate_prev.start_time, 1)
                    answer = f"Immediately before {target_ev.description} at {format_timestamp(cutoff)}, {immediate_prev.description} occurred at {format_timestamp(immediate_prev.start_time)} ({delta}s prior)."
                    evidence = [
                        TemporalEvidenceItem(
                            timestamp=immediate_prev.start_time,
                            label=f"{format_timestamp(immediate_prev.start_time)} {immediate_prev.description}",
                            event_id=immediate_prev.event_id,
                            entity_id=immediate_prev.entity_id,
                            description=immediate_prev.description
                        ),
                        TemporalEvidenceItem(
                            timestamp=target_ev.start_time,
                            label=f"{format_timestamp(target_ev.start_time)} {target_ev.description}",
                            event_id=target_ev.event_id,
                            entity_id=target_ev.entity_id,
                            description=target_ev.description
                        )
                    ]
                    return QueryResponse(
                        query=user_question,
                        answer=answer,
                        timestamp_start=immediate_prev.start_time,
                        timestamp_end=target_ev.start_time,
                        relevant_entities=[immediate_prev.entity_id, target_ev.entity_id],
                        confidence=min(immediate_prev.confidence, target_ev.confidence),
                        evidence=evidence,
                        temporal_relation=TemporalRelationStep(
                            from_event=immediate_prev.description,
                            to_event=target_ev.description,
                            delta_seconds=delta,
                            relation="before"
                        ),
                        reasoning_trace=reasoning_trace
                    )
                else:
                    return QueryResponse(
                        query=user_question,
                        answer=f"No recorded events occurred prior to {target_ev.description} at {format_timestamp(target_ev.start_time)}.",
                        timestamp_start=target_ev.start_time,
                        timestamp_end=target_ev.start_time,
                        relevant_entities=[target_ev.entity_id],
                        confidence=1.0,
                        evidence=[],
                        reasoning_trace=reasoning_trace
                    )

        # 7. "WHO ENTERED AFTER ..." / "WHAT HAPPENED AFTER ..."
        if "after" in q:
            reasoning_trace.append("Detected query intent: AFTER_RELATION")
            target_ev = self._find_matching_anchor_event(q)
            if target_ev:
                cutoff = target_ev.start_time
                subsequent_events = [e for e in self.events if e.start_time > cutoff and e.event_id != target_ev.event_id]
                if subsequent_events:
                    # Filter for 'who entered' if asking who
                    if "who" in q or "enter" in q:
                        entry_subs = [e for e in subsequent_events if e.type in ("PERSON_ENTERED", "ZONE_ENTRY")]
                        if entry_subs:
                            next_ev = entry_subs[0]
                        else:
                            next_ev = subsequent_events[0]
                    else:
                        next_ev = subsequent_events[0]

                    delta = round(next_ev.start_time - cutoff, 1)
                    answer = f"{next_ev.entity_id} ({next_ev.description}) at {format_timestamp(next_ev.start_time)}, approximately {delta} seconds after {target_ev.description} at {format_timestamp(cutoff)}."
                    evidence = [
                        TemporalEvidenceItem(
                            timestamp=target_ev.start_time,
                            label=f"{format_timestamp(target_ev.start_time)} {target_ev.description}",
                            event_id=target_ev.event_id,
                            entity_id=target_ev.entity_id,
                            description=target_ev.description
                        ),
                        TemporalEvidenceItem(
                            timestamp=next_ev.start_time,
                            label=f"{format_timestamp(next_ev.start_time)} {next_ev.description}",
                            event_id=next_ev.event_id,
                            entity_id=next_ev.entity_id,
                            description=next_ev.description
                        )
                    ]
                    return QueryResponse(
                        query=user_question,
                        answer=answer,
                        timestamp_start=target_ev.start_time,
                        timestamp_end=next_ev.start_time,
                        relevant_entities=[target_ev.entity_id, next_ev.entity_id],
                        confidence=min(target_ev.confidence, next_ev.confidence),
                        evidence=evidence,
                        temporal_relation=TemporalRelationStep(
                            from_event=target_ev.description,
                            to_event=next_ev.description,
                            delta_seconds=delta,
                            relation="after"
                        ),
                        reasoning_trace=reasoning_trace
                    )

        # 8. "BETWEEN ... AND ..."
        if "between" in q and "and" in q:
            reasoning_trace.append("Detected query intent: BETWEEN_RELATION")
            # Extract two anchors
            # Try to find two matching events
            matched_events = []
            for ev in self.events:
                e_desc = ev.description.lower()
                e_ent = ev.entity_id.lower()
                if (e_ent in q or any(w in e_desc for w in ["enter", "exit", "leave", "truck", "bag", "unattended", "pickup"])):
                    matched_events.append(ev)
            
            if len(matched_events) >= 2:
                ev1 = matched_events[0]
                ev2 = matched_events[-1]
                t_min, t_max = min(ev1.start_time, ev2.start_time), max(ev1.start_time, ev2.start_time)
                in_between = [e for e in self.events if t_min < e.start_time < t_max]
                if in_between:
                    mid_descriptions = "; ".join([f"{e.description} at {format_timestamp(e.start_time)}" for e in in_between])
                    answer = f"Between {format_timestamp(t_min)} and {format_timestamp(t_max)}, {len(in_between)} event(s) took place: {mid_descriptions}."
                    evidence = [
                        TemporalEvidenceItem(
                            timestamp=e.start_time,
                            label=f"{format_timestamp(e.start_time)} {e.description}",
                            event_id=e.event_id,
                            entity_id=e.entity_id,
                            description=e.description
                        ) for e in in_between
                    ]
                    return QueryResponse(
                        query=user_question,
                        answer=answer,
                        timestamp_start=t_min,
                        timestamp_end=t_max,
                        relevant_entities=[e.entity_id for e in in_between],
                        confidence=1.0,
                        evidence=evidence,
                        reasoning_trace=reasoning_trace
                    )

        # 9. "WHEN DID ... ENTER/LEAVE/APPEAR"
        if "when" in q:
            reasoning_trace.append("Detected query intent: WHEN_QUERY")
            target_ev = self._find_matching_anchor_event(q)
            if target_ev:
                answer = f"{target_ev.description} occurred at {format_timestamp(target_ev.start_time)}."
                evidence = [
                    TemporalEvidenceItem(
                        timestamp=target_ev.start_time,
                        label=f"{format_timestamp(target_ev.start_time)} {target_ev.description}",
                        event_id=target_ev.event_id,
                        entity_id=target_ev.entity_id,
                        description=target_ev.description
                    )
                ]
                return QueryResponse(
                    query=user_question,
                    answer=answer,
                    timestamp_start=target_ev.start_time,
                    timestamp_end=target_ev.end_time,
                    relevant_entities=[target_ev.entity_id],
                    confidence=target_ev.confidence,
                    evidence=evidence,
                    reasoning_trace=reasoning_trace
                )

        # Fallback keyword match over events
        reasoning_trace.append("Falling back to semantic keyword retrieval")
        candidates = []
        for ev in self.events:
            score = 0
            words = q.replace("?", "").split()
            for w in words:
                if len(w) > 3 and (w in ev.description.lower() or w in ev.type.lower() or w in ev.entity_id.lower()):
                    score += 1
            if score > 0:
                candidates.append((score, ev))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_ev = candidates[0][1]
            answer = f"At {format_timestamp(best_ev.start_time)}, {best_ev.description} was observed."
            evidence = [
                TemporalEvidenceItem(
                    timestamp=best_ev.start_time,
                    label=f"{format_timestamp(best_ev.start_time)} {best_ev.description}",
                    event_id=best_ev.event_id,
                    entity_id=best_ev.entity_id,
                    description=best_ev.description
                )
            ]
            return QueryResponse(
                query=user_question,
                answer=answer,
                timestamp_start=best_ev.start_time,
                timestamp_end=best_ev.end_time,
                relevant_entities=[best_ev.entity_id],
                confidence=best_ev.confidence,
                evidence=evidence,
                reasoning_trace=reasoning_trace
            )

        return QueryResponse(
            query=user_question,
            answer="Insufficient evidence in the analyzed video to answer this question with high certainty.",
            timestamp_start=None,
            timestamp_end=None,
            relevant_entities=[],
            confidence=0.0,
            evidence=[],
            reasoning_trace=reasoning_trace + ["No matching temporal patterns or event entities discovered."]
        )

    def _find_matching_anchor_event(self, q: str) -> Optional[EventModel]:
        # Check if anchor is specifically "last event" or "final event"
        if ("last event" in q or "final event" in q or "final exit" in q) and self.events:
            return self.events[-1]
        if "first event" in q and self.events:
            return self.events[0]

        # Check for specific entity references like "person 1", "person 2", "person #1", "truck", "bag", "backpack"
        # Check for event types: "enter", "exit", "left", "abandon", "unattended", "pickup", "alarm"
        for ev in self.events:
            desc_l = ev.description.lower()
            ent_l = ev.entity_id.lower().replace("_", " ").replace("#", "")
            
            # Match person #2 / person 2
            m = re.search(r"person\s*#?(\d+)", q)
            if m:
                target_p = f"person_{m.group(1)}"
                if target_p == ev.entity_id.lower() or f"person #{m.group(1)}" in desc_l.lower():
                    if "enter" in q and ("enter" in desc_l or ev.type in ("PERSON_ENTERED", "ZONE_ENTRY")):
                        return ev
                    if ("exit" in q or "leave" in q or "left" in q) and ("exit" in desc_l or ev.type in ("PERSON_EXITED", "ZONE_EXIT")):
                        return ev
                    if not any(k in q for k in ["enter", "exit", "leave"]):
                        return ev

            # Match truck / vehicle
            if "truck" in q or "vehicle" in q:
                if "truck" in desc_l or "truck" in ent_l:
                    return ev

            # Match backpack / bag
            if "backpack" in q or "bag" in q:
                if "unattended" in q or "abandon" in q:
                    if ev.type == "OBJECT_LEFT_UNATTENDED" or "unattended" in desc_l:
                        return ev
                if "pick" in q:
                    if ev.type == "OBJECT_PICKED_UP" or "pick" in desc_l:
                        return ev
                if "bag" in desc_l or "backpack" in desc_l:
                    return ev

            # Match alarm
            if "alarm" in q and "alarm" in desc_l:
                return ev

        # Fallback: find any event that has a word match
        for ev in self.events:
            desc_words = set(ev.description.lower().split())
            if any(w in desc_words for w in ["unattended", "entered", "exited", "truck", "picked"]):
                if any(w in q for w in ["unattended", "entered", "exited", "truck", "picked"]):
                    return ev

        return self.events[0] if self.events else None
