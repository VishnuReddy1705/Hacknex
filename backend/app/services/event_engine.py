import math
import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.database.session import EventModel, EntityModel

def format_ts(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 10))
    if ms > 0:
        return f"{m:02d}:{s:02d}.{ms}"
    return f"{m:02d}:{s:02d}"

def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

class EventEngine:
    def __init__(
        self,
        db: Session,
        video_id: str,
        fps: float,
        width: int,
        height: int,
        stationary_disp_thresh: float = 30.0,
        unattended_time_thresh: float = 4.0, # seconds
        loiter_time_thresh: float = 8.0, # seconds
    ):
        self.db = db
        self.video_id = video_id
        self.fps = fps
        self.width = width
        self.height = height
        self.stationary_disp_thresh = stationary_disp_thresh
        self.unattended_time_thresh = unattended_time_thresh
        self.loiter_time_thresh = loiter_time_thresh

    def process_and_index(self, raw_tracks: Dict[str, Dict[str, Any]]):
        """
        raw_tracks structure:
        {
           entity_id: {
               "track_id": int,
               "class_name": str,
               "first_seen": float,
               "last_seen": float,
               "confidence": float,
               "history": [
                   {"frame": int, "timestamp": float, "bbox": [x1, y1, x2, y2], "center": (cx, cy), "conf": float}
               ]
           }
        }
        """
        extracted_events: List[EventModel] = []
        entity_models: List[EntityModel] = []

        # 1. Index All Entities into SQLite
        for ent_id, ent_info in raw_tracks.items():
            hist = ent_info["history"]
            if not hist:
                continue

            first_seen = hist[0]["timestamp"]
            last_seen = hist[-1]["timestamp"]
            duration = round(max(0.0, last_seen - first_seen), 2)
            avg_conf = sum(h["conf"] for h in hist) / len(hist)

            entity_model = EntityModel(
                entity_id=ent_id,
                video_id=self.video_id,
                track_id=ent_info["track_id"],
                class_name=ent_info["class_name"],
                first_seen=first_seen,
                last_seen=last_seen,
                duration=duration,
                confidence=round(avg_conf, 2),
                event_count=0,
                trajectory=[
                    {
                        "frame": h["frame"],
                        "timestamp": h["timestamp"],
                        "bbox": h["bbox"],
                        "confidence": h["conf"]
                    } for h in hist[::max(1, len(hist)//50)] # sample up to 50 points
                ]
            )
            entity_models.append(entity_model)

        # Commit entities first
        for em in entity_models:
            self.db.merge(em)
        self.db.commit()

        # 2. Extract Discrete Events
        # A. Presence: ENTER & EXIT
        for ent_id, ent_info in raw_tracks.items():
            hist = ent_info["history"]
            if not hist:
                continue

            first = hist[0]
            last = hist[-1]
            c_name = ent_info["class_name"].capitalize()
            readable_name = ent_id.replace("_", " ").title()

            # Entry / Appearance
            is_person = "person" in ent_info["class_name"].lower()
            entry_type = "PERSON_ENTERED" if is_person else "OBJECT_APPEARED"
            entry_desc = f"{readable_name} entered monitored area at {format_ts(first['timestamp'])}" if is_person else f"{readable_name} appeared at {format_ts(first['timestamp'])}"

            extracted_events.append(EventModel(
                event_id=f"ev_entry_{ent_id}",
                video_id=self.video_id,
                type=entry_type,
                entity_id=ent_id,
                start_time=first["timestamp"],
                end_time=first["timestamp"],
                frame_start=first["frame"],
                frame_end=first["frame"],
                confidence=first["conf"],
                description=entry_desc
            ))

            # Exit / Disappearance (if track ends before end of video)
            total_video_time = last["timestamp"]
            # If entity exits before the video finishes
            if last["frame"] > first["frame"] + int(self.fps * 2): # seen for > 2 sec
                exit_type = "PERSON_EXITED" if is_person else "OBJECT_DISAPPEARED"
                exit_desc = f"{readable_name} exited monitored area at {format_ts(last['timestamp'])}" if is_person else f"{readable_name} cleared from view at {format_ts(last['timestamp'])}"

                extracted_events.append(EventModel(
                    event_id=f"ev_exit_{ent_id}",
                    video_id=self.video_id,
                    type=exit_type,
                    entity_id=ent_id,
                    start_time=last["timestamp"],
                    end_time=last["timestamp"],
                    frame_start=last["frame"],
                    frame_end=last["frame"],
                    confidence=last["conf"],
                    description=exit_desc
                ))

            # Loitering (Person remains in small bounding radius for long time)
            if is_person and len(hist) > int(self.fps * self.loiter_time_thresh):
                centers = [h["center"] for h in hist]
                min_x = min(c[0] for c in centers)
                max_x = max(c[0] for c in centers)
                min_y = min(c[1] for c in centers)
                max_y = max(c[1] for c in centers)
                span = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2)
                if span < 120.0: # stayed within 120px radius
                    loiter_duration = round(last["timestamp"] - first["timestamp"], 1)
                    extracted_events.append(EventModel(
                        event_id=f"ev_loiter_{ent_id}",
                        video_id=self.video_id,
                        type="LOITERING",
                        entity_id=ent_id,
                        start_time=first["timestamp"],
                        end_time=last["timestamp"],
                        frame_start=first["frame"],
                        frame_end=last["frame"],
                        confidence=round(avg_conf, 2),
                        description=f"{readable_name} loitered in area for {loiter_duration}s from {format_ts(first['timestamp'])} to {format_ts(last['timestamp'])}"
                    ))

        # B. Stationary Objects and Unattended Baggage Detection
        objects = {k: v for k, v in raw_tracks.items() if not "person" in v["class_name"].lower()}
        people = {k: v for k, v in raw_tracks.items() if "person" in v["class_name"].lower()}

        for obj_id, obj_info in objects.items():
            hist = obj_info["history"]
            if len(hist) < int(self.fps * 2): # ignore flicker
                continue

            # Check if object is stationary
            first_pt = hist[0]["center"]
            displacements = [calculate_distance(first_pt, h["center"]) for h in hist]
            max_disp = max(displacements)

            if max_disp <= self.stationary_disp_thresh:
                # Object is stationary!
                start_stat = hist[0]["timestamp"]
                end_stat = hist[-1]["timestamp"]
                stat_duration = round(end_stat - start_stat, 1)

                extracted_events.append(EventModel(
                    event_id=f"ev_stat_{obj_id}",
                    video_id=self.video_id,
                    type="OBJECT_STATIONARY",
                    entity_id=obj_id,
                    start_time=start_stat,
                    end_time=end_stat,
                    frame_start=hist[0]["frame"],
                    frame_end=hist[-1]["frame"],
                    confidence=round(obj_info["confidence"], 2),
                    description=f"{obj_id.replace('_', ' ').title()} remained stationary for {stat_duration}s ({format_ts(start_stat)} to {format_ts(end_stat)})"
                ))

                # Check for Abandonment / Unattended event
                # Look for a person who was close at the beginning and then moved far away
                associated_carrier = None
                carrier_left_time = None

                for p_id, p_info in people.items():
                    p_hist = p_info["history"]
                    # Find person frame near object appearance
                    near_start = [ph for ph in p_hist if abs(ph["timestamp"] - start_stat) < 2.0]
                    if near_start:
                        closest_start = min(near_start, key=lambda ph: calculate_distance(ph["center"], first_pt))
                        if calculate_distance(closest_start["center"], first_pt) < 160.0:
                            # This person brought / was with the object!
                            associated_carrier = p_id
                            # Now find when this person walked away (> 200px)
                            later_pts = [ph for ph in p_hist if ph["timestamp"] >= closest_start["timestamp"]]
                            for lpt in later_pts:
                                if calculate_distance(lpt["center"], first_pt) > 180.0:
                                    carrier_left_time = lpt["timestamp"]
                                    break
                            break

                unattended_start = carrier_left_time if carrier_left_time else start_stat + 2.0
                if end_stat - unattended_start >= self.unattended_time_thresh:
                    unattended_dur = round(end_stat - unattended_start, 1)
                    extracted_events.append(EventModel(
                        event_id=f"ev_unattended_{obj_id}",
                        video_id=self.video_id,
                        type="OBJECT_LEFT_UNATTENDED",
                        entity_id=obj_id,
                        related_entity_id=associated_carrier,
                        start_time=unattended_start,
                        end_time=end_stat,
                        frame_start=int(unattended_start * self.fps),
                        frame_end=hist[-1]["frame"],
                        confidence=0.92,
                        description=f"{obj_id.replace('_', ' ').title()} was left unattended at {format_ts(unattended_start)}" + (f" by {associated_carrier.replace('_', ' ').title()}" if associated_carrier else "")
                    ))

                # Check if someone subsequently picked it up or interacted
                for p_id, p_info in people.items():
                    if p_id == associated_carrier:
                        continue
                    p_hist = p_info["history"]
                    # Check if person arrived near the end of object's stationary track
                    near_end = [ph for ph in p_hist if abs(ph["timestamp"] - end_stat) < 2.0]
                    if near_end:
                        closest_end = min(near_end, key=lambda ph: calculate_distance(ph["center"], hist[-1]["center"]))
                        if calculate_distance(closest_end["center"], hist[-1]["center"]) < 160.0:
                            # Person interacted / picked up!
                            pickup_time = closest_end["timestamp"]
                            extracted_events.append(EventModel(
                                event_id=f"ev_pickup_{obj_id}_{p_id}",
                                video_id=self.video_id,
                                type="OBJECT_PICKED_UP",
                                entity_id=obj_id,
                                related_entity_id=p_id,
                                start_time=pickup_time,
                                end_time=pickup_time,
                                frame_start=closest_end["frame"],
                                frame_end=closest_end["frame"],
                                confidence=0.90,
                                description=f"{p_id.replace('_', ' ').title()} picked up / interacted with {obj_id.replace('_', ' ').title()} at {format_ts(pickup_time)}"
                            ))
                            break

        # C. Store all events into Database
        extracted_events.sort(key=lambda x: x.start_time)
        for ev in extracted_events:
            self.db.merge(ev)
        
        # Update entity event counts
        for em in entity_models:
            c = sum(1 for e in extracted_events if e.entity_id == em.entity_id or e.related_entity_id == em.entity_id)
            em.event_count = c
            self.db.merge(em)

        self.db.commit()
        return extracted_events
