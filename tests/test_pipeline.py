"""
End-to-end integration test for Eyelnw pipeline.
Generates synthetic reference image and video clip, runs detection & matching, and checks report output.
"""

from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import time
import cv2
import numpy as np

from core.color_analyzer import ColorAnalyzer
from core.detector import VehicleDetector
from core.feature_extractor import FeatureExtractor
from core.matcher import VehicleMatcher
from core.target_loader import TargetLoader
from core.video_scanner import VideoScanner
from report.generator import ReportGenerator
from utils.config import ScanConfig


def create_synthetic_car_image(color_bgr=(240, 240, 240), plate_text="1กก 1234") -> np.ndarray:
    """Creates a synthetic image resembling a car for test purposes."""
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    # Background asphalt road
    img[:] = (60, 60, 60)

    # Car body
    cv2.rectangle(img, (60, 100), (340, 230), color_bgr, -1)
    # Roof / windows
    cv2.rectangle(img, (110, 70), (280, 110), (40, 40, 40), -1)
    # Windshield
    cv2.fillPoly(img, [np.array([[90, 110], [110, 70], [280, 70], [300, 110]], np.int32)], (70, 70, 70))
    # Headlights
    cv2.circle(img, (80, 180), 14, (100, 255, 255), -1)
    cv2.circle(img, (320, 180), 14, (100, 255, 255), -1)
    # Plate box
    cv2.rectangle(img, (150, 185), (250, 215), (255, 255, 255), -1)
    cv2.putText(img, plate_text, (155, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    return img


def create_synthetic_cctv_video(output_video_path: Path, num_frames=60, fps=20):
    """Creates a short synthetic CCTV clip with a car moving from left to right."""
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    car = create_synthetic_car_image(color_bgr=(240, 240, 240))
    car_h, car_w = car.shape[:2]

    for i in range(num_frames):
        # CCTV background (street)
        frame = np.full((height, width, 3), 80, dtype=np.uint8)
        # Road lane markings
        cv2.line(frame, (0, 350), (640, 350), (200, 200, 200), 2)
        cv2.line(frame, (0, 450), (640, 450), (200, 200, 200), 2)

        # Move car horizontally across frame
        x_pos = int(-car_w + (width + car_w * 2) * (i / num_frames))
        y_pos = 180

        # Paste car if in bounds
        c_x1 = max(0, x_pos)
        c_y1 = max(0, y_pos)
        c_x2 = min(width, x_pos + car_w)
        c_y2 = min(height, y_pos + car_h)

        if c_x2 > c_x1 and c_y2 > c_y1:
            crop_w = c_x2 - c_x1
            crop_h = c_y2 - c_y1
            src_x1 = c_x1 - x_pos
            src_y1 = c_y1 - y_pos
            frame[c_y1:c_y2, c_x1:c_x2] = car[src_y1:src_y1 + crop_h, src_x1:src_x1 + crop_w]

        out.write(frame)

    out.release()


def run_pipeline_test():
    print("\n--- Starting Eyelnw Pipeline Integration Test ---")
    test_dir = Path(__file__).resolve().parent / "temp_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create target image
    target_img = create_synthetic_car_image()
    target_path = test_dir / "target_sample.jpg"
    cv2.imwrite(str(target_path), target_img)
    print(f"✅ Generated target image: {target_path}")

    # 2. Create synthetic CCTV video
    video_path = test_dir / "cctv_test_01.mp4"
    create_synthetic_cctv_video(video_path, num_frames=50, fps=20)
    print(f"✅ Generated CCTV test video: {video_path}")

    # 3. TargetLoader & Feature Extraction
    print("Testing TargetLoader & Deep Feature extraction...")
    color_analyzer = ColorAnalyzer()
    feature_extractor = FeatureExtractor()
    loader = TargetLoader(color_analyzer, feature_extractor)
    target_profile = loader.build_profile(
        image_paths=[target_path],
        plate_number="1กก 1234",
        car_color="ขาว",
        car_brand="Toyota",
        car_model="Yaris"
    )
    assert target_profile.is_valid, "TargetProfile should be valid"
    print(f"✅ TargetProfile created. Dominant color: {target_profile.dominant_color}")

    # 4. Color Matching Test
    cand_same = create_synthetic_car_image(color_bgr=(240, 240, 240))
    cand_diff = create_synthetic_car_image(color_bgr=(20, 20, 200))  # red
    hist_same = color_analyzer.compute_histogram(cand_same)
    hist_diff = color_analyzer.compute_histogram(cand_diff)
    score_same = color_analyzer.compare_colors(target_profile.avg_histogram, hist_same)
    score_diff = color_analyzer.compare_colors(target_profile.avg_histogram, hist_diff)
    print(f"✅ Color similarity: Same color={score_same:.2f}, Diff color={score_diff:.2f}")
    assert score_same > score_diff, "Same color score must be higher than different color"

    # 5. ResNet50 Embedding Cosine Similarity Test
    emb_same = feature_extractor.extract(cand_same)
    emb_diff = feature_extractor.extract(cand_diff)
    sim_same = feature_extractor.cosine_similarity(target_profile.avg_embedding, emb_same)
    sim_diff = feature_extractor.cosine_similarity(target_profile.avg_embedding, emb_diff)
    print(f"✅ Deep Feature Cosine Similarity: Same={sim_same:.2f}, Diff={sim_diff:.2f}")

    # 6. Detector Test (YOLOv8 initialization & inference)
    print("Testing YOLOv8 vehicle detector...")
    config = ScanConfig(model_size="n", match_threshold=0.50)
    detector = VehicleDetector(model_size="n")
    # Quick inference on frame
    frame = cv2.imread(str(target_path))
    dets = detector.detect(frame)
    print(f"✅ YOLOv8 detected {len(dets)} vehicles in test frame.")

    # 7. VideoScanner Test
    print("Testing VideoScanner...")
    matcher = VehicleMatcher(target=target_profile, color_analyzer=color_analyzer, feature_extractor=feature_extractor)
    scanner = VideoScanner(detector, matcher, config)
    events = scanner.scan_video(video_path)
    print(f"✅ VideoScanner completed. Found {len(events)} match events.")

    # 8. Report Generator Test
    print("Testing ReportGenerator...")
    generator = ReportGenerator()
    report_file, scan_folder = generator.generate_report(
        target=target_profile,
        events=events,
        scanned_videos=[video_path],
        output_base_dir=test_dir,
        scan_duration_sec=3.5
    )
    assert report_file.exists(), f"Report file must exist: {report_file}"
    print(f"✅ Report HTML created: {report_file}")
    assert (scan_folder / "data" / "results.json").exists(), "results.json must exist"
    print(f"✅ results.json created at: {scan_folder / 'data' / 'results.json'}")

    print("\n🎉 ALL PIPELINE TESTS PASSED SUCCESSFULLY! 🎉\n")


if __name__ == "__main__":
    run_pipeline_test()
