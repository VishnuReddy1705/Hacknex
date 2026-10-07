import math
from typing import Dict, List, Any, Tuple
from backend.app.config import settings
from backend.app.utils.timestamps import seconds_to_timestamp

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

class EventDetector:
    def __init__(
        self,
        fps: float,
        width: int,
        height: int,
        stationary_thresh: float = None,
        unattended_thresh: float = None,
        loiter_thresh: float = None
    ):
        self.fps = fps
        self.width = width
        self.height = height
        self.stationary_thresh = stationary_thresh or settings.STATIONARY_DISPLACEMENT_THRESH
        self.unattended_thresh = unattended_thresh or settings.UNATTENDED_TIME_THRESH
        self.loiter_thresh = loiter_thresh or settings.LOITER_TIME_THRESH

    def detect_events_from_tracks(self, objects_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        objects_data structure:
        {
          object_id: {
             "track_id": int,
             "class_name": str,
             "label": str,
             "confidence": float,
             "history": [
                {"frame": int, "timestamp": float, "bbox": [x1, y1, x2, y2], "center": (cx, cy), "conf": float}
             ]
          }
        }
        """
        events = []
        event_counter = 1

        for obj_id, info in objects_data.items():
            hist = info["history"]
            if not hist:
                continue

            first_pt = hist[0]
            last_pt = hist[-1]
            c_name = info["class_name"].lower()
            is_person = "person" in c_name
            label = info["label"]

            # 1. ARRIVAL / APPEARANCE / ENTERED_ZONE
            if is_person:
                events.append({
                    "id": f"E{event_counter:02d}",
                    "object_id": obj_id,
                    "related_object_id": None,
                    "event_type": "ENTERED_ZONE",
                    "start_time": first_pt["timestamp"],
                    "end_time": first_pt["timestamp"],
                    "duration": 0.0,
                    "confidence": first_pt["conf"],
                    "description": f"{label} entered monitored area at {seconds_to_timestamp(first_pt['timestamp'])}",
                    "metadata": {"frame": first_pt["frame"], "zone": "monitored_area"}
                })
            else:
                events.append({
                    "id": f"E{event_counter:02d}",
                    "object_id": obj_id,
                    "related_object_id": None,
                    "event_type": "ARRIVED" if c_name in ("truck", "car", "bus") else "OBJECT_APPEARED",
                    "start_time": first_pt["timestamp"],
                    "end_time": first_pt["timestamp"],
                    "duration": 0.0,
                    "confidence": first_pt["conf"],
                    "description": f"{label} arrived at {seconds_to_timestamp(first_pt['timestamp'])}" if c_name in ("truck", "car", "bus") else f"{label} appeared at {seconds_to_timestamp(first_pt['timestamp'])}",
                    "metadata": {"frame": first_pt["frame"]}
                })
            event_counter += 1

            # 2. DEPARTURE / EXITED_ZONE
            # If track finishes before total video end
            if len(hist) > 5 and (last_pt["timestamp"] - first_pt["timestamp"] > 1.5):
                events.append({
                    "id": f"E{event_counter:02d}",
                    "object_id": obj_id,
                    "related_object_id": None,
                    "event_type": "EXITED_ZONE" if is_person else "DEPARTED",
                    "start_time": last_pt["timestamp"],
                    "end_time": last_pt["timestamp"],
                    "duration": 0.0,
                    "confidence": last_pt["conf"],
                    "description": f"{label} exited at {seconds_to_timestamp(last_pt['timestamp'])}" if is_person else f"{label} departed at {seconds_to_timestamp(last_pt['timestamp'])}",
                    "metadata": {"frame": last_pt["frame"]}
                })
                event_counter += 1

            # 3. STATIONARY / STOPPED
            if len(hist) > 10:
                first_center = hist[0]["center"]
                displacements = [calculate_distance(first_center, h["center"]) for h in hist]
                max_d = max(displacements)
                duration_sec = round(last_pt["timestamp"] - first_pt["timestamp"], 1)

                if max_d <= self.stationary_thresh and duration_sec >= 2.0:
                    events.append({
                        "id": f"E{event_counter:02d}",
                        "object_id": obj_id,
                        "related_object_id": None,
                        "event_type": "STATIONARY",
                        "start_time": first_pt["timestamp"],
                        "end_time": last_pt["timestamp"],
                        "duration": duration_sec,
                        "confidence": round(info["confidence"], 2),
                        "description": f"{label} remained stationary for {duration_sec}s from {seconds_to_timestamp(first_pt['timestamp'])} to {seconds_to_timestamp(last_pt['timestamp'])}",
                        "metadata": {"max_displacement": round(max_d, 1)}
                    })
                    event_counter += 1

            # 4. LOITERING (person stays in bounded region)
            if is_person and len(hist) > 20:
                dur = round(last_pt["timestamp"] - first_pt["timestamp"], 1)
                if dur >= self.loiter_thresh:
                    events.append({
                        "id": f"E{event_counter:02d}",
                        "object_id": obj_id,
                        "related_object_id": None,
                        "event_type": "LOITERING",
                        "start_time": first_pt["timestamp"],
                        "end_time": last_pt["timestamp"],
                        "duration": dur,
                        "confidence": round(info["confidence"], 2),
                        "description": f"{label} loitered in area for {dur}s ({seconds_to_timestamp(first_pt['timestamp'])} to {seconds_to_timestamp(last_pt['timestamp'])})",
                        "metadata": {"duration": dur}
                    })
                    event_counter += 1

        # 5. CROSS-OBJECT INTERACTIONS (e.g. person near truck or bag)
        people = [k for k, v in objects_data.items() if "person" in v["class_name"].lower()]
        others = [k for k, v in objects_data.items() if "person" not in v["class_name"].lower()]

        for p_id in people:
            p_hist = objects_data[p_id]["history"]
            p_label = objects_data[p_id]["label"]
            for o_id in others:
                o_hist = objects_data[o_id]["history"]
                o_label = objects_data[o_id]["label"]

                # Find overlap timeframes
                p_times = {int(h["timestamp"] * 2): h for h in p_hist}
                for oh in o_hist:
                    k = int(oh["timestamp"] * 2)
                    if k in p_times:
                        ph = p_times[k]
                        dist = calculate_distance(ph["center"], oh["center"])
                        if dist < 120.0: # Close proximity interaction
                            t = oh["timestamp"]
                            events.append({
                                "id": f"E{event_counter:02d}",
                                "object_id": p_id,
                                "related_object_id": o_id,
                                "event_type": "INTERACTION",
                                "start_time": t,
                                "end_time": t,
                                "duration": 0.0,
                                "confidence": 0.90,
                                "description": f"{p_label} interacted with {o_label} at {seconds_to_timestamp(t)}",
                                "metadata": {"distance_px": round(dist, 1)}
                            })
                            event_counter += 1
                            break # single interaction event per pair

        events.sort(key=lambda x: x["start_time"])
        return events
