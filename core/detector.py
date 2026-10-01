"""
Vehicle detector using YOLOv8 for detecting cars, trucks, buses, and motorcycles in CCTV frames.
"""

from pathlib import Path
import numpy as np
import torch
from utils.helpers import safe_crop
from utils.logger import logger


class VehicleDetector:
    """Detects vehicles in video frames using YOLOv8."""

    # COCO vehicle classes: 2: car, 3: motorcycle, 5: bus, 7: truck
    DEFAULT_CLASSES = [2, 3, 5, 7]
    CLASS_NAMES = {
        2: "รถเก๋ง/กระบะ (Car)",
        3: "มอเตอร์ไซค์ (Motorcycle)",
        5: "รถบัส (Bus)",
        7: "รถบรรทุก (Truck)"
    }

    def __init__(
        self,
        model_size: str = "n",
        device: str | None = None,
        confidence_thresh: float = 0.30,
        vehicle_classes: list[int] | None = None,
        models_dir: Path | None = None
    ):
        self.model_size = model_size
        self.confidence_thresh = confidence_thresh
        self.vehicle_classes = vehicle_classes or self.DEFAULT_CLASSES

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.models_dir = models_dir or Path(__file__).resolve().parent.parent / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = f"yolov8{self.model_size}.pt"
        self.model_path = self.models_dir / self.model_name

        self.model = None

    def _lazy_init(self):
        """Loads YOLOv8 model upon first call."""
        if self.model is not None:
            return

        from ultralytics import YOLO
        logger.info(f"Loading YOLOv8 ({self.model_name}) on device '{self.device}'...")

        # If model exists in models/ dir, load it, otherwise YOLO will auto-download
        if self.model_path.exists():
            self.model = YOLO(str(self.model_path))
        else:
            self.model = YOLO(self.model_name)
            # Save downloaded weights to models/ folder if created in root
            root_weight = Path(self.model_name)
            if root_weight.exists() and not self.model_path.exists():
                try:
                    root_weight.rename(self.model_path)
                    self.model = YOLO(str(self.model_path))
                except Exception:
                    pass

        self.model.to(self.device)
        logger.info("YOLOv8 initialized successfully.")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Runs object detection on a single video frame.

        Returns a list of dicts:
        [
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": int,
                "class_name": str,
                "cropped_image": np.ndarray
            },
            ...
        ]
        """
        if frame is None or frame.size == 0:
            return []

        self._lazy_init()

        results = self.model.predict(
            source=frame,
            classes=self.vehicle_classes,
            conf=self.confidence_thresh,
            device=self.device,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        first_res = results[0]
        boxes = first_res.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for box in boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            xyxy = [int(v) for v in box.xyxy[0].tolist()]

            # Ensure minimum bounding box size to filter out noise
            w = xyxy[2] - xyxy[0]
            h = xyxy[3] - xyxy[1]
            if w < 24 or h < 24:
                continue

            crop = safe_crop(frame, xyxy)
            if crop.size == 0:
                continue

            detections.append({
                "bbox": xyxy,
                "confidence": conf,
                "class_id": cls_id,
                "class_name": self.CLASS_NAMES.get(cls_id, "ยานพาหนะ (Vehicle)"),
                "cropped_image": crop
            })

        return detections
