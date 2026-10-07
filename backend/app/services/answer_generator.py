from typing import Dict, Any, List
from backend.app.models.answer import AskResponse, EvidenceItem
from backend.app.utils.timestamps import seconds_to_timestamp, format_duration_str

class AnswerGenerator:
    def __init__(self):
        pass

    def generate(self, parsed_query: Dict[str, Any], retrieved: Dict[str, Any]) -> AskResponse:
        results = retrieved.get("results", [])
        anchor = retrieved.get("anchor")
        evidence = retrieved.get("evidence", [])
        relation = parsed_query.get("relation")

        if not results and not anchor:
            return AskResponse(
                answer="Insufficient evidence in the analyzed video to answer this question with certainty.",
                timestamps=[],
                evidence=[],
                confidence=0.0,
                structured_query=parsed_query
            )

        # 1. COUNT
        if parsed_query.get("is_count"):
            count = len(results)
            ts_list = [seconds_to_timestamp(e.start_time) for e in results]
            tgt = parsed_query.get("target_object") or parsed_query.get("target_event") or "event"
            if count == 0:
                answer = f"The {tgt} occurred 0 times in this video."
            elif count == 1:
                answer = f"The {tgt} occurred 1 time, at {ts_list[0]}."
            else:
                answer = f"The {tgt} stopped {count} times, at {', '.join(ts_list[:4])}." if "stop" in parsed_query.get("raw_question", "").lower() else f"The {tgt} occurred {count} times, at {', '.join(ts_list[:4])}."
            return AskResponse(
                answer=answer,
                timestamps=ts_list,
                evidence=evidence,
                confidence=0.95,
                structured_query=parsed_query
            )

        # 2. DURATION
        if parsed_query.get("is_duration"):
            if results:
                e = results[0]
                dur_str = format_duration_str(e.duration or (e.end_time - e.start_time))
                t1 = seconds_to_timestamp(e.start_time)
                t2 = seconds_to_timestamp(e.end_time)
                answer = f"{e.description} for {dur_str}, from {t1} to {t2}."
                return AskResponse(
                    answer=answer,
                    timestamps=[t1, t2],
                    evidence=evidence,
                    confidence=e.confidence,
                    structured_query=parsed_query
                )

        # 3. FIRST
        if parsed_query.get("is_first"):
            e = results[0]
            t = seconds_to_timestamp(e.start_time)
            answer = f"The first recorded event was {e.description} at {t}."
            return AskResponse(
                answer=answer,
                timestamps=[t],
                evidence=evidence,
                confidence=e.confidence,
                structured_query=parsed_query
            )

        # 4. LAST
        if parsed_query.get("is_last"):
            e = results[0]
            t = seconds_to_timestamp(e.start_time)
            answer = f"The last recorded event was {e.description} at {t}."
            return AskResponse(
                answer=answer,
                timestamps=[t],
                evidence=evidence,
                confidence=e.confidence,
                structured_query=parsed_query
            )

        # 5. IMMEDIATELY_BEFORE / BEFORE
        if relation in ("IMMEDIATELY_BEFORE", "BEFORE"):
            if results and anchor:
                prev = results[-1] if relation == "BEFORE" else results[0]
                t_prev = seconds_to_timestamp(prev.start_time)
                t_anc = seconds_to_timestamp(anchor.start_time)
                delta = round(anchor.start_time - prev.start_time, 1)

                prefix = "Immediately before" if relation == "IMMEDIATELY_BEFORE" else "Before"
                answer = f"{prefix} {anchor.description} at {t_anc}, {prev.description} occurred at {t_prev} ({delta}s prior)."
                return AskResponse(
                    answer=answer,
                    timestamps=[t_prev, t_anc],
                    evidence=evidence,
                    confidence=min(prev.confidence, anchor.confidence),
                    structured_query=parsed_query,
                    graph_relation={
                        "source": prev.description,
                        "relation": relation,
                        "target": anchor.description,
                        "time_difference": delta
                    }
                )

        # 6. AFTER / IMMEDIATELY_AFTER
        if relation in ("AFTER", "IMMEDIATELY_AFTER"):
            if results and anchor:
                nxt = results[0]
                t_nxt = seconds_to_timestamp(nxt.start_time)
                t_anc = seconds_to_timestamp(anchor.start_time)
                delta = round(nxt.start_time - anchor.start_time, 1)

                answer = f"{nxt.description} at {t_nxt}, approximately {delta} seconds after {anchor.description} at {t_anc}."
                return AskResponse(
                    answer=answer,
                    timestamps=[t_anc, t_nxt],
                    evidence=evidence,
                    confidence=min(nxt.confidence, anchor.confidence),
                    structured_query=parsed_query,
                    graph_relation={
                        "source": anchor.description,
                        "relation": relation,
                        "target": nxt.description,
                        "time_difference": delta
                    }
                )

        # 7. BETWEEN
        if relation == "BETWEEN" and results:
            ts_list = [seconds_to_timestamp(e.start_time) for e in results]
            descs = "; ".join([f"{e.description} at {seconds_to_timestamp(e.start_time)}" for e in results[:3]])
            answer = f"Between the specified times, {len(results)} event(s) took place: {descs}."
            return AskResponse(
                answer=answer,
                timestamps=ts_list,
                evidence=evidence,
                confidence=0.92,
                structured_query=parsed_query
            )

        # Fallback
        if results:
            e = results[0]
            t = seconds_to_timestamp(e.start_time)
            answer = f"At {t}, {e.description} occurred."
            return AskResponse(
                answer=answer,
                timestamps=[t],
                evidence=evidence,
                confidence=e.confidence,
                structured_query=parsed_query
            )

        return AskResponse(
            answer="Insufficient evidence in the analyzed video to answer this question.",
            timestamps=[],
            evidence=[],
            confidence=0.0,
            structured_query=parsed_query
        )
