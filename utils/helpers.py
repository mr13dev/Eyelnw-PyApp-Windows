"""
Helper functions for Eyelnw (timestamps, bounding boxes, file handling).
"""

from pathlib import Path
import re
import cv2
import numpy as np
from PIL import Image


def format_seconds_to_timestamp(seconds: float) -> str:
    """Converts seconds (e.g. 3672.4) into HH:MM:SS format."""
    total_seconds = int(max(0, seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def sanitize_filename(name: str) -> str:
    """Removes invalid characters for file naming across operating systems."""
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()


def safe_crop(image: np.ndarray, bbox: tuple[int, int, int, int] | list[int]) -> np.ndarray:
    """
    Safely crops an image given [x1, y1, x2, y2] bounding box with boundary checks.
    """
    h, w = image.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in bbox]
    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))
    return image[y1:y2, x1:x2].copy()


def draw_detection_box(
    image: np.ndarray,
    bbox: tuple[int, int, int, int] | list[int],
    label: str,
    confidence: float,
    color: tuple[int, int, int] = (0, 255, 0)
) -> np.ndarray:
    """
    Draws a styled bounding box with label and confidence on an image.
    """
    annotated = image.copy()
    x1, y1, x2, y2 = [int(v) for v in bbox]

    # Draw rectangle border
    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

    # Label text
    text = f"{label} {confidence * 100:.1f}%"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.65
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    # Background banner for label
    box_y1 = max(0, y1 - text_h - 10)
    cv2.rectangle(annotated, (x1, box_y1), (x1 + text_w + 10, box_y1 + text_h + 10), color, -1)
    cv2.putText(
        annotated,
        text,
        (x1 + 5, box_y1 + text_h + 3),
        font,
        font_scale,
        (0, 0, 0),
        thickness,
        cv2.LINE_AA
    )
    return annotated


def cv2_to_pil(cv_image: np.ndarray) -> Image.Image:
    """Converts a BGR OpenCV image to a PIL Image."""
    rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Converts a PIL Image to a BGR OpenCV image."""
    rgb = np.array(pil_image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
