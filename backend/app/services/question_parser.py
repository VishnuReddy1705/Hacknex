import re
from typing import Dict, Any, Optional
from backend.app.utils.timestamps import timestamp_to_seconds

class QuestionParser:
    def __init__(self):
        pass

    def parse(self, question: str) -> Dict[str, Any]:
        q = question.strip().lower()
        
        parsed: Dict[str, Any] = {
            "raw_question": question,
            "target_event": None,
            "relation": None,
            "target_object": None,
            "is_count": False,
            "is_duration": False,
            "is_first": False,
            "is_last": False,
            "is_who": "who" in q,
            "time_range": None
        }

        # 1. COUNT intent
        if "how many times" in q or "how many" in q or "count" in q:
            parsed["is_count"] = True
            parsed["relation"] = "COUNT"

        # 2. DURATION intent
        elif "how long" in q or "duration" in q or "how much time" in q:
            parsed["is_duration"] = True
            parsed["relation"] = "DURATION"

        # 3. FIRST / LAST
        elif "first" in q:
            parsed["is_first"] = True
            parsed["relation"] = "FIRST"
        elif "last" in q or "final" in q:
            parsed["is_last"] = True
            parsed["relation"] = "LAST"

        # 4. IMMEDIATELY BEFORE / AFTER
        elif "immediately before" in q or "right before" in q or "just before" in q:
            parsed["relation"] = "IMMEDIATELY_BEFORE"
        elif "immediately after" in q or "right after" in q or "just after" in q:
            parsed["relation"] = "IMMEDIATELY_AFTER"

        # 5. BEFORE / AFTER
        elif "before" in q:
            parsed["relation"] = "BEFORE"
        elif "after" in q:
            parsed["relation"] = "AFTER"

        # 6. BETWEEN
        elif "between" in q:
            parsed["relation"] = "BETWEEN"
            # Look for timestamps in question like 00:20 and 01:00
            m = re.findall(r"(\d{1,2}:\d{2})", q)
            if len(m) >= 2:
                parsed["time_range"] = (timestamp_to_seconds(m[0]), timestamp_to_seconds(m[1]))

        # Extract Target Object
        # Matches: "person p01", "p07", "worker p01", "truck", "machine", "bag", "backpack"
        p_match = re.search(r"\b(p\d{1,2}|person\s*#?\d+|worker\s*p?\d+)\b", q)
        if p_match:
            parsed["target_object"] = p_match.group(1).replace(" ", "_")
        elif "truck" in q:
            parsed["target_object"] = "truck"
        elif "machine" in q:
            parsed["target_object"] = "machine"
        elif "backpack" in q or "bag" in q:
            parsed["target_object"] = "backpack"

        # Extract Target Event
        if "alarm" in q:
            parsed["target_event"] = "ALARM"
        elif "stop" in q:
            parsed["target_event"] = "STOPPED"
        elif "start" in q:
            parsed["target_event"] = "STARTED"
        elif "enter" in q or "entered" in q or "arrival" in q or "arrive" in q:
            parsed["target_event"] = "ARRIVED" if ("truck" in q or "car" in q) else "ENTERED_ZONE"
        elif "exit" in q or "leave" in q or "left" in q:
            parsed["target_event"] = "EXITED_ZONE"
        elif "unattended" in q:
            parsed["target_event"] = "OBJECT_LEFT_UNATTENDED"
        elif "pick" in q:
            parsed["target_event"] = "OBJECT_PICKED_UP"

        return parsed
