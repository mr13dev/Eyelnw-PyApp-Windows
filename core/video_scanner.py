"""
Video scanner that processes CCTV video footage frame-by-frame with smart frame skipping.
"""

from dataclasses import dataclass, field
from pathlib import Path
import threading
import time
import cv2
import numpy as np

from core.detector import VehicleDetector
from core.matcher import VehicleMatcher, MatchResult
from core.motion_tracker import MotionTracker
from utils.config import ScanConfig
from utils.helpers import format_seconds_to_timestamp, draw_detection_box
from utils.logger import logger


@dataclass
class DetectionRecord:
    """A single matched vehicle occurrence in a specific frame."""
    video_path: Path
    frame_index: int
    timestamp: float
    timestamp_str: str
    bbox: list[int]
    match_result: MatchResult
    class_name: str
    annotated_frame: np.ndarray
    car_crop: np.ndarray


@dataclass
class MatchGroup:
    """A cluster of contiguous detections representing a single vehicle passage."""
    group_id: int
    video_path: Path
    start_time: float
    end_time: float
    best_detection: DetectionRecord
    detections: list[DetectionRecord] = field(default_factory=list)
    direction: str = "ไม่ระบุ"
    clip_path: Path | None = None
    screenshot_path: Path | None = None

    @property
    def peak_confidence(self) -> float:
        return self.best_detection.match_result.combined_score

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)


class VideoScanner:
    """Scans CCTV video files for target vehicle matches."""

    def __init__(
        self,
        detector: VehicleDetector,
        matcher: VehicleMatcher,
        config: ScanConfig | None = None
    ):
        self.detector = detector
        self.matcher = matcher
        self.config = config or ScanConfig()
        self.motion_tracker = MotionTracker()

        # Cancellation & pause synchronization
        self._is_cancelled = False
        self._is_paused = False
        self._pause_cond = threading.Condition()

    def cancel(self):
        """Signals the scanning thread to stop as soon as possible."""
        self._is_cancelled = True
        self.resume()  # Ensure paused scan wakes up to exit

    def pause(self):
        """Pauses the scan loop."""
        with self._pause_cond:
            self._is_paused = True

    def resume(self):
        """Resumes the scan loop."""
        with self._pause_cond:
            self._is_paused = False
            self._pause_cond.notify_all()

    def _check_pause_and_cancel(self) -> bool:
        """Helper to block if paused or return True if cancelled."""
        with self._pause_cond:
            while self._is_paused and not self._is_cancelled:
                self._pause_cond.wait(timeout=0.2)
        return self._is_cancelled

    def scan_video(
        self,
        video_path: str | Path,
        progress_callback=None
    ) -> list[MatchGroup]:
        """
        Scans an individual video file for the target vehicle.

        progress_callback signature:
            callback(
                current_frame: int,
                total_frames: int,
                current_time: float,
                total_time: float,
                matches_found: int,
                status_text: str
            )
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        total_duration = total_frames / fps

        # Compute adaptive skip rate if requested (target ~2 to 3 evaluations per second)
        skip = self.config.frame_skip
        if self.config.adaptive_skip and fps > 0:
            skip = max(1, int(round(fps / 2.0)))

        logger.info(
            f"Scanning '{video_path.name}': {total_frames} frames, "
            f"{fps:.1f} FPS, duration: {format_seconds_to_timestamp(total_duration)}, "
            f"evaluating every {skip} frames"
        )

        detections: list[DetectionRecord] = []
        frame_idx = 0
        self._is_cancelled = False

        try:
            while cap.isOpened():
                if self._check_pause_and_cancel():
                    logger.info("Video scanning was cancelled by user.")
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % skip == 0:
                    current_time = frame_idx / fps
                    time_str = format_seconds_to_timestamp(current_time)

                    # 1. Detect all vehicles in frame
                    detected_vehicles = self.detector.detect(frame)

                    for v in detected_vehicles:
                        crop = v["cropped_image"]
                        # 2. Match each detected vehicle against target
                        match_res = self.matcher.match(
                            crop,
                            threshold=self.config.match_threshold,
                            vehicle_class_id=v["class_id"]
                        )

                        if match_res.is_match:
                            # Build annotated frame
                            annotated = draw_detection_box(
                                frame,
                                v["bbox"],
                                label=f"{self.matcher.target.car_brand or 'รถเป้าหมาย'}",
                                confidence=match_res.combined_score,
                                color=(0, 255, 0)
                            )

                            record = DetectionRecord(
                                video_path=video_path,
                                frame_index=frame_idx,
                                timestamp=current_time,
                                timestamp_str=time_str,
                                bbox=v["bbox"],
                                match_result=match_res,
                                class_name=v["class_name"],
                                annotated_frame=annotated,
                                car_crop=crop
                            )
                            detections.append(record)
                            logger.info(
                                f"Match detected at {time_str} in '{video_path.name}'! "
                                f"Score: {match_res.combined_score * 100:.1f}%, Color: {match_res.detected_color}"
                            )

                    # Update progress UI
                    if progress_callback:
                        progress_callback(
                            frame_idx,
                            total_frames,
                            current_time,
                            total_duration,
                            len(detections),
                            f"กำลังสแกน {video_path.name} ({time_str})"
                        )

                frame_idx += 1

        finally:
            cap.release()

        # Group raw detections into event clusters
        grouped_events = self._cluster_detections(detections, video_path)
        logger.info(f"Scan complete. Found {len(detections)} frame matches clustered into {len(grouped_events)} events.")
        return grouped_events

    def _cluster_detections(
        self,
        detections: list[DetectionRecord],
        video_path: Path
    ) -> list[MatchGroup]:
        """
        Clusters close consecutive detections (within group_interval_seconds)
        into a single MatchGroup event, and computes movement direction.
        """
        if not detections:
            return []

        # Sort detections chronologically
        detections.sort(key=lambda d: d.timestamp)

        groups: list[MatchGroup] = []
        current_cluster: list[DetectionRecord] = [detections[0]]

        for d in detections[1:]:
            last_d = current_cluster[-1]
            if d.timestamp - last_d.timestamp <= self.config.group_interval_seconds:
                current_cluster.append(d)
            else:
                groups.append(self._create_group(len(groups) + 1, current_cluster, video_path))
                current_cluster = [d]

        if current_cluster:
            groups.append(self._create_group(len(groups) + 1, current_cluster, video_path))

        return groups

    def _create_group(
        self,
        group_id: int,
        cluster: list[DetectionRecord],
        video_path: Path
    ) -> MatchGroup:
        """Constructs a MatchGroup from a list of DetectionRecords."""
        # Find detection with highest combined score
        best_det = max(cluster, key=lambda d: d.match_result.combined_score)
        start_time = cluster[0].timestamp
        end_time = cluster[-1].timestamp

        # Direction tracking
        traj_data = [{"timestamp": d.timestamp, "bbox": d.bbox} for d in cluster]
        direction = self.motion_tracker.track_direction(traj_data)

        return MatchGroup(
            group_id=group_id,
            video_path=video_path,
            start_time=start_time,
            end_time=end_time,
            best_detection=best_det,
            detections=cluster,
            direction=direction
        )
