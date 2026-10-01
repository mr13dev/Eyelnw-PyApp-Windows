"""
Configuration settings for Eyelnw vehicle detection system.
"""

from dataclasses import dataclass, field
from pathlib import Path
import os
import torch


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure runtime directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def get_optimal_device() -> str:
    """Safely determines if CUDA is supported by hardware kernels, otherwise falls back to CPU."""
    if not torch.cuda.is_available():
        return "cpu"
    try:
        # Verify kernel compatibility by running a tiny test allocation
        test_tensor = torch.zeros(1, device="cuda")
        del test_tensor
        return "cuda"
    except Exception:
        return "cpu"


@dataclass
class ScanConfig:
    """Settings controlling video scan and detection."""
    # Model parameters
    model_size: str = "n"  # 'n' (nano), 's' (small), 'm' (medium)
    device: str = field(default_factory=get_optimal_device)
    vehicle_classes: list[int] = field(default_factory=lambda: [2, 3, 5, 7])  # car, motorcycle, bus, truck
    detection_conf: float = 0.30

    # Matching weights
    weight_color: float = 0.25
    weight_feature: float = 0.25
    weight_deep: float = 0.40
    weight_ocr: float = 0.10

    # Threshold for reporting a match
    match_threshold: float = 0.60

    # Video scan parameters
    frame_skip: int = 15  # analyze every N frames (approx 2 times/sec at 30 fps)
    adaptive_skip: bool = True  # adjust skip based on video FPS

    # Grouping & Reporting
    group_interval_seconds: float = 5.0  # detections within N seconds grouped together
    enable_clip_cutting: bool = False     # whether to cut short video clips
    clip_padding_before: float = 4.0     # clip start padding in seconds
    clip_padding_after: float = 4.0      # clip end padding in seconds

    # Optional OCR
    enable_ocr: bool = True

    # Paths
    models_dir: Path = MODELS_DIR
    output_dir: Path = OUTPUT_DIR
    assets_dir: Path = ASSETS_DIR


DEFAULT_CONFIG = ScanConfig()
