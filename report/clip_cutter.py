"""
Clip cutter module that extracts short video clips and screenshots around detected match events.
"""

from pathlib import Path
import cv2
import numpy as np
from utils.logger import logger


class VideoClipCutter:
    """Extracts short clips and screenshots from CCTV video footage."""

    def __init__(self, pad_before: float = 4.0, pad_after: float = 4.0):
        self.pad_before = pad_before
        self.pad_after = pad_after

    def cut_clip(
        self,
        source_video: str | Path,
        start_time: float,
        end_time: float,
        output_path: str | Path
    ) -> Path | None:
        """
        Cuts a short video clip from source_video between (start_time - pad) and (end_time + pad).
        """
        source_video = Path(source_video)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not source_video.exists():
            logger.error(f"Cannot cut clip: source video not found: {source_video}")
            return None

        cap = cv2.VideoCapture(str(source_video))
        if not cap.isOpened():
            logger.error(f"Cannot open video for clipping: {source_video}")
            return None

        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            clip_start_sec = max(0.0, start_time - self.pad_before)
            clip_end_sec = end_time + self.pad_after

            start_frame = int(clip_start_sec * fps)
            end_frame = min(total_frames, int(clip_end_sec * fps))

            if start_frame >= total_frames or start_frame >= end_frame:
                start_frame = max(0, end_frame - int(fps * 3))

            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

            curr_frame = start_frame
            while curr_frame <= end_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
                curr_frame += 1

            out.release()
            logger.info(f"Generated clip: {output_path.name} ({clip_start_sec:.1f}s - {clip_end_sec:.1f}s)")
            return output_path
        except Exception as e:
            logger.error(f"Error while cutting clip '{output_path.name}': {e}")
            return None
        finally:
            cap.release()

    def save_screenshot(self, image: np.ndarray, output_path: str | Path) -> Path | None:
        """Saves a frame / screenshot to disk using unicode-safe cv2 encoding."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            ext = output_path.suffix.lower() or ".jpg"
            success, buffer = cv2.imencode(ext, image)
            if success:
                with open(output_path, "wb") as f:
                    f.write(buffer)
                return output_path
            return None
        except Exception as e:
            logger.error(f"Failed to save screenshot {output_path}: {e}")
            return None
