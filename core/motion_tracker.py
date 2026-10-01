"""
Motion tracker to determine direction of vehicle movement from bounding box sequences.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class TrajectoryPoint:
    timestamp: float
    bbox: list[int]  # [x1, y1, x2, y2]

    @property
    def center(self) -> tuple[float, float]:
        cx = (self.bbox[0] + self.bbox[2]) / 2.0
        cy = (self.bbox[1] + self.bbox[3]) / 2.0
        return cx, cy

    @property
    def area(self) -> float:
        w = max(0, self.bbox[2] - self.bbox[0])
        h = max(0, self.bbox[3] - self.bbox[1])
        return float(w * h)


class MotionTracker:
    """Estimates the vehicle's movement direction across a sequence of detections."""

    def track_direction(self, points: list[TrajectoryPoint] | list[dict]) -> str:
        """
        Analyzes a sequence of bounding box detections over time.
        Input can be list of TrajectoryPoint or list of dicts with 'bbox' and 'timestamp'.
        """
        if not points or len(points) < 2:
            return "ไม่สามารถระบุได้ (Single observation)"

        # Standardize items into TrajectoryPoint
        traj_points: list[TrajectoryPoint] = []
        for p in points:
            if isinstance(p, TrajectoryPoint):
                traj_points.append(p)
            elif isinstance(p, dict) and "bbox" in p:
                traj_points.append(TrajectoryPoint(
                    timestamp=p.get("timestamp", 0.0),
                    bbox=p["bbox"]
                ))

        if len(traj_points) < 2:
            return "ไม่สามารถระบุได้ (Single observation)"

        # Sort by timestamp
        traj_points.sort(key=lambda x: x.timestamp)

        p_start = traj_points[0]
        p_end = traj_points[-1]

        c_start_x, c_start_y = p_start.center
        c_end_x, c_end_y = p_end.center

        dx = c_end_x - c_start_x
        dy = c_end_y - c_start_y

        area_start = p_start.area
        area_end = p_end.area
        area_ratio = area_end / max(1.0, area_start)

        distance = np.sqrt(dx ** 2 + dy ** 2)
        avg_w = ((p_start.bbox[2] - p_start.bbox[0]) + (p_end.bbox[2] - p_end.bbox[0])) / 2.0

        # If displacement is negligible relative to vehicle width
        if distance < avg_w * 0.15:
            if area_ratio > 1.35:
                return "มุ่งหน้าเข้ามาหา (Approaching)"
            elif area_ratio < 0.70:
                return "เคลื่อนที่ห่างออกไป (Moving away)"
            return "จอด / ชะลอความเร็ว (Stationary / Slow)"

        # Check primary axis of movement
        if abs(dx) >= abs(dy):
            if dx > 0:
                return "ซ้ายไปขวา (Left to Right)"
            else:
                return "ขวาไปซ้าย (Right to Left)"
        else:
            if dy > 0:
                return "บนลงล่าง / เข้ามาใกล้ (Top to Bottom / Approaching)"
            else:
                return "ล่างขึ้นบน / ถอยห่าง (Bottom to Top / Moving away)"
