"""
Eyelnw — AI-powered CCTV Vehicle Detection & Investigation System.
Entry point for GUI and CLI operations.
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.logger import logger


def run_gui():
    """Launches the CustomTkinter graphical user interface."""
    from gui.app import EyelnwApp
    logger.info("Starting Eyelnw Graphical User Interface...")
    app = EyelnwApp()
    app.mainloop()


def run_cli(args):
    """Executes headless scan pipeline from command line arguments."""
    from core.color_analyzer import ColorAnalyzer
    from core.detector import VehicleDetector
    from core.feature_extractor import FeatureExtractor
    from core.matcher import VehicleMatcher
    from core.ocr_reader import PlateReader
    from core.target_loader import TargetLoader
    from core.video_scanner import VideoScanner
    from report.generator import ReportGenerator
    from utils.config import ScanConfig

    logger.info("Running Eyelnw in CLI mode...")

    # Collect target images
    target_path = Path(args.target)
    if target_path.is_dir():
        image_paths = [
            p for p in target_path.iterdir()
            if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]
        ]
    elif target_path.is_file():
        image_paths = [target_path]
    else:
        logger.error(f"Target path does not exist: {target_path}")
        sys.exit(1)

    if not image_paths:
        logger.error("No valid target images found.")
        sys.exit(1)

    video_paths = [Path(v) for v in args.videos]
    for v in video_paths:
        if not v.exists():
            logger.error(f"Video file not found: {v}")
            sys.exit(1)

    logger.info(f"Target images: {len(image_paths)}, Videos: {len(video_paths)}")

    # Initialize AI subsystems
    color_analyzer = ColorAnalyzer()
    feature_extractor = FeatureExtractor()
    plate_reader = PlateReader()
    target_loader = TargetLoader(color_analyzer, feature_extractor)

    target_profile = target_loader.build_profile(
        image_paths=image_paths,
        plate_number=args.plate or "",
        car_color=args.color or "",
        car_brand=args.brand or "",
        car_model=args.model or ""
    )

    config = ScanConfig(
        model_size=args.model_size,
        match_threshold=args.threshold,
        frame_skip=args.skip,
        enable_clip_cutting=not args.no_clips
    )

    detector = VehicleDetector(
        model_size=config.model_size,
        confidence_thresh=config.detection_conf,
        models_dir=config.models_dir
    )
    matcher = VehicleMatcher(
        target=target_profile,
        color_analyzer=color_analyzer,
        feature_extractor=feature_extractor,
        plate_reader=plate_reader
    )

    scanner = VideoScanner(detector, matcher, config)
    all_events = []

    for vid in video_paths:
        events = scanner.scan_video(vid)
        all_events.extend(events)

    generator = ReportGenerator()
    report_file, scan_dir = generator.generate_report(
        target=target_profile,
        events=all_events,
        scanned_videos=video_paths,
        enable_clip_cutting=not args.no_clips
    )

    logger.info(f"Scan completed. Found {len(all_events)} events.")
    logger.info(f"HTML Report: {report_file}")
    logger.info(f"Output Directory: {scan_dir}")


def main():
    parser = argparse.ArgumentParser(description="Eyelnw — CCTV Vehicle Detection System")
    parser.add_argument("--cli", action="store_true", help="Run in CLI headless mode without GUI")
    parser.add_argument("--target", type=str, help="Path to reference vehicle image or directory of images")
    parser.add_argument("--videos", nargs="+", type=str, help="Path to one or more CCTV video files")
    parser.add_argument("--plate", type=str, default="", help="License plate number (optional)")
    parser.add_argument("--color", type=str, default="", help="Car color (optional)")
    parser.add_argument("--brand", type=str, default="", help="Car brand (optional)")
    parser.add_argument("--model", type=str, default="", help="Car model (optional)")
    parser.add_argument("--threshold", type=float, default=0.60, help="Confidence threshold (default 0.60)")
    parser.add_argument("--model-size", type=str, default="n", choices=["n", "s", "m"], help="YOLOv8 model size (n/s/m)")
    parser.add_argument("--skip", type=int, default=15, help="Frame skip rate (default 15)")
    parser.add_argument("--no-clips", action="store_true", help="Disable cutting short video clips")

    args = parser.parse_args()

    if args.cli:
        if not args.target or not args.videos:
            parser.error("--cli mode requires --target and --videos arguments.")
        run_cli(args)
    else:
        run_gui()


if __name__ == "__main__":
    main()
