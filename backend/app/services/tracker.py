import torch
from ultralytics import YOLO
from typing import List, Dict, Any
from backend.app.config import settings

class ObjectTracker:
    def __init__(self, model_name: str = None, tracker_type: str = None):
        self.model_name = model_name or settings.YOLO_MODEL
        self.tracker_type = tracker_type or settings.TRACKER_TYPE
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(self.model_name)

    def track_frame(self, frame, persist: bool = True) -> List[Dict[str, Any]]:
        results = self.model.track(
            frame,
            persist=persist,
            tracker=self.tracker_type,
            device=self.device,
            conf=settings.CONFIDENCE_THRESHOLD,
            verbose=False
        )

        tracks = []
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                if box.id is None:
                    continue
                track_id = int(box.id[0])
                cls_id = int(box.cls[0])
                cls_name = self.model.names.get(cls_id, "object")
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().tolist()

                # Generate clean object identity: e.g. "P01" for person 1, "truck_2", "backpack_3"
                if "person" in cls_name.lower():
                    obj_id = f"P{track_id:02d}"
                else:
                    obj_id = f"{cls_name}_{track_id}"

                tracks.append({
                    "object_id": obj_id,
                    "track_id": track_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": xyxy
                })
        return tracks
