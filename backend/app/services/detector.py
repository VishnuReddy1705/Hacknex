import torch
from ultralytics import YOLO
from typing import List, Dict, Any
from backend.app.config import settings

# Common surveillance & industrial classes:
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck, 24: backpack, 26: handbag, 28: suitcase, 56: chair
DEFAULT_TARGET_CLASSES = [0, 1, 2, 3, 5, 7, 24, 26, 28, 56]

class ObjectDetector:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.YOLO_MODEL
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(self.model_name)

    def detect(self, frame) -> List[Dict[str, Any]]:
        results = self.model(
            frame,
            device=self.device,
            classes=DEFAULT_TARGET_CLASSES,
            conf=settings.CONFIDENCE_THRESHOLD,
            verbose=False
        )
        detections = []
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self.model.names.get(cls_id, "object")
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                detections.append({
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": xyxy
                })
        return detections
