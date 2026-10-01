"""
Unit and integration tests for Eyelnw Phase 2 features:
- Feature 1: Motorcycle tuning (upscale, class weights, skin tone filtering)
- Feature 2: Centralized Report Index generation
- Feature 3: Persistent settings manager
- Feature 4: Abort clip cutting logic
"""

from datetime import datetime
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import numpy as np

# Provide test doubles for vision dependencies if running in minimal test environment
if "cv2" not in sys.modules:
    try:
        import cv2
    except ImportError:
        mock_cv2 = MagicMock()
        mock_cv2.INTER_CUBIC = 2
        mock_cv2.NORM_HAMMING = 4
        mock_cv2.COLOR_BGR2HSV = 40
        mock_cv2.HISTCMP_CORREL = 0
        mock_cv2.cvtColor.side_effect = lambda img, code: img.copy()
        mock_cv2.calcHist.side_effect = lambda images, channels, mask, histSize, ranges: np.zeros((histSize[0], histSize[1]), dtype=np.float32)
        mock_cv2.normalize.side_effect = lambda src, dst, alpha, beta, norm_type: src
        mock_cv2.inRange.side_effect = lambda src, lower, upper: np.zeros(src.shape[:2], dtype=np.uint8)
        mock_cv2.bitwise_not.side_effect = lambda src: np.full_like(src, 255)
        mock_cv2.countNonZero.side_effect = lambda src: int(np.count_nonzero(src))
        def fake_resize(src, dsize, interpolation=None):
            return np.zeros((dsize[1], dsize[0], src.shape[2] if src.ndim > 2 else 1), dtype=src.dtype)
        mock_cv2.resize = fake_resize
        sys.modules["cv2"] = mock_cv2

if "torch" not in sys.modules:
    try:
        import torch
    except ImportError:
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        sys.modules["torch"] = mock_torch

if "torchvision" not in sys.modules:
    try:
        import torchvision
    except ImportError:
        mock_tv = MagicMock()
        sys.modules["torchvision"] = mock_tv
        sys.modules["torchvision.transforms"] = MagicMock()
        sys.modules["torchvision.models"] = MagicMock()

from utils.settings import SettingsManager, DEFAULT_SETTINGS
from report.index_generator import ReportIndexGenerator


class TestPhase2Features(unittest.TestCase):
    """Test suite for Phase 2 components."""

    def setUp(self):
        self.test_dir = BASE_DIR / "tests" / "temp_phase2_test"
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Cleanup temp directory
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ---------------------------------------------------------
    # Feature 3: Persistent Settings Tests
    # ---------------------------------------------------------
    def test_settings_manager_defaults(self):
        settings_file = self.test_dir / "settings_test.json"
        sm = SettingsManager(path=settings_file)
        self.assertEqual(sm.get("model_choice"), DEFAULT_SETTINGS["model_choice"])
        self.assertEqual(sm.get("match_threshold"), 0.60)
        self.assertTrue(sm.get("enable_clip_cutting"))

    def test_settings_manager_save_and_reload(self):
        settings_file = self.test_dir / "settings_test.json"
        sm = SettingsManager(path=settings_file)
        sm.set("model_choice", "YOLOv8s (แม่นยำสูง)")
        sm.set("match_threshold", 0.75)
        sm.set("enable_clip_cutting", False)

        # Reload in a new instance
        sm2 = SettingsManager(path=settings_file)
        self.assertEqual(sm2.get("model_choice"), "YOLOv8s (แม่นยำสูง)")
        self.assertEqual(sm2.get("match_threshold"), 0.75)
        self.assertFalse(sm2.get("enable_clip_cutting"))

    def test_settings_manager_reset(self):
        settings_file = self.test_dir / "settings_test.json"
        sm = SettingsManager(path=settings_file)
        sm.set("match_threshold", 0.85)
        self.assertEqual(sm.get("match_threshold"), 0.85)

        sm.reset_all()
        self.assertEqual(sm.get("match_threshold"), 0.60)

    def test_settings_manager_corrupted_file(self):
        settings_file = self.test_dir / "corrupted_settings.json"
        settings_file.write_text("{invalid json format!@#$", encoding="utf-8")
        sm = SettingsManager(path=settings_file)
        # Should gracefully fall back to defaults
        self.assertEqual(sm.get("match_threshold"), 0.60)

    # ---------------------------------------------------------
    # Feature 2: Report Index Generator Tests
    # ---------------------------------------------------------
    def test_report_index_generation(self):
        output_dir = self.test_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create two simulated scan directories
        scan1 = output_dir / "scan_20261001_100000"
        scan1.mkdir(parents=True, exist_ok=True)
        (scan1 / "report.html").write_text("<html>Report 1</html>", encoding="utf-8")
        (scan1 / "data").mkdir(parents=True, exist_ok=True)
        (scan1 / "data" / "results.json").write_text(json.dumps({
            "timestamp": "2026-10-01T10:00:00",
            "target": {"plate_number": "1กก 9999", "car_brand": "Honda", "car_model": "Wave", "car_color": "ดำ"},
            "summary": {"total_matches": 3, "total_videos": 1, "highest_confidence": 0.88, "scan_duration_sec": 12.5},
            "events": [{"group_id": 1}, {"group_id": 2}, {"group_id": 3}]
        }), encoding="utf-8")

        scan2 = output_dir / "scan_20261001_110000"
        scan2.mkdir(parents=True, exist_ok=True)
        (scan2 / "report.html").write_text("<html>Report 2</html>", encoding="utf-8")
        (scan2 / "data").mkdir(parents=True, exist_ok=True)
        (scan2 / "data" / "results.json").write_text(json.dumps({
            "timestamp": "2026-10-01T11:00:00",
            "target": {"plate_number": "2ขข 1234", "car_brand": "Toyota", "car_model": "Hilux", "car_color": "ขาว"},
            "summary": {"total_matches": 1, "total_videos": 2, "highest_confidence": 0.72, "scan_duration_sec": 45.0},
            "events": [{"group_id": 1}]
        }), encoding="utf-8")

        index_gen = ReportIndexGenerator(output_dir=output_dir)
        reports = index_gen.scan_existing_reports()
        self.assertEqual(len(reports), 2)
        # scan2 is newer timestamp folder, should be first
        self.assertEqual(reports[0]["folder_name"], "scan_20261001_110000")
        self.assertEqual(reports[0]["target"]["car_brand"], "Toyota")
        self.assertEqual(reports[1]["target"]["car_brand"], "Honda")

        # Generate index.html
        index_file = index_gen.generate_index()
        self.assertTrue(index_file.exists())
        content = index_file.read_text(encoding="utf-8")
        self.assertIn("1กก 9999", content)
        self.assertIn("2ขข 1234", content)
        self.assertIn("Honda", content)
        self.assertIn("Toyota", content)
        self.assertIn("scan_20261001_110000/report.html", content)

    # ---------------------------------------------------------
    # Feature 4: Abort Clip Cutting Logic Tests
    # ---------------------------------------------------------
    def test_report_generator_abort_clips(self):
        from report.generator import ReportGenerator

        generator = ReportGenerator()
        self.assertFalse(generator._abort_clips)
        generator.abort_clip_cutting()
        self.assertTrue(generator._abort_clips)

    # ---------------------------------------------------------
    # Feature 1: Motorcycle Tuning & Upscale Tests
    # ---------------------------------------------------------
    def test_matcher_motorcycle_profile_weights(self):
        from core.matcher import VehicleMatcher
        from core.target_loader import TargetProfile

        target = TargetProfile(plate_number="", car_color="ดำ", car_brand="Honda", car_model="Wave")
        target.images = [np.zeros((100, 100, 3), dtype=np.uint8)]
        matcher = VehicleMatcher(target=target)
        self.assertIn("motorcycle", matcher.WEIGHT_PROFILES)
        self.assertIn("car", matcher.WEIGHT_PROFILES)

        # Motorcycle has higher deep weight and lower color/feature weight
        moto_weights = matcher.WEIGHT_PROFILES["motorcycle"]
        car_weights = matcher.WEIGHT_PROFILES["car"]
        self.assertGreater(moto_weights["deep"], car_weights["deep"])
        self.assertLess(moto_weights["color"], car_weights["color"])

    def test_matcher_preprocess_upscale(self):
        from core.matcher import VehicleMatcher
        from core.target_loader import TargetProfile

        target = TargetProfile(plate_number="", car_color="ดำ", car_brand="Honda", car_model="Wave")
        target.images = [np.zeros((100, 100, 3), dtype=np.uint8)]
        matcher = VehicleMatcher(target=target)

        # Very small candidate crop (e.g. far motorcycle 20x30)
        tiny_crop = np.zeros((20, 30, 3), dtype=np.uint8)
        upscaled = matcher._preprocess_candidate(tiny_crop, class_id=3)
        h, w = upscaled.shape[:2]
        self.assertGreaterEqual(h, 112)
        self.assertGreaterEqual(w, 112)

    def test_detector_min_size_and_classes(self):
        from core.detector import VehicleDetector
        detector = VehicleDetector(model_size="n")
        self.assertIn(3, detector.MIN_SIZE)
        # Motorcycle min size is 16x16 vs car 24x24
        self.assertEqual(detector.MIN_SIZE[3], (16, 16))
        self.assertEqual(detector.MIN_SIZE[2], (24, 24))

    def test_color_analyzer_motorcycle_mode(self):
        from core.color_analyzer import ColorAnalyzer
        ca = ColorAnalyzer()
        # Test image with dimensions
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        hist_normal = ca.compute_histogram(dummy_img, is_motorcycle=False)
        hist_moto = ca.compute_histogram(dummy_img, is_motorcycle=True)
        self.assertEqual(hist_normal.shape, (30, 32))
        self.assertEqual(hist_moto.shape, (30, 32))

        col_normal = ca.get_dominant_color(dummy_img, is_motorcycle=False)
        col_moto = ca.get_dominant_color(dummy_img, is_motorcycle=True)
        self.assertEqual(col_normal, "ดำ (Black)")
        self.assertEqual(col_moto, "ดำ (Black)")

    def test_report_generator_abort_and_index_end_to_end(self):
        from report.generator import ReportGenerator
        from core.target_loader import TargetProfile
        from core.video_scanner import MatchGroup, DetectionRecord
        from core.matcher import MatchResult

        output_dir = self.test_dir / "output_e2e"
        output_dir.mkdir(parents=True, exist_ok=True)

        target = TargetProfile(plate_number="1กก 1234", car_color="แดง", car_brand="Honda", car_model="Wave")
        target.images = [np.zeros((100, 100, 3), dtype=np.uint8)]

        # Mock detections and match result
        mr = MatchResult(0.85, 0.8, 0.7, 0.9, 0.5, "1กก 1234", "แดง", True)
        det1 = DetectionRecord(
            video_path=Path("test1.mp4"),
            frame_index=10,
            timestamp=2.0,
            timestamp_str="00:00:02",
            bbox=[10, 10, 50, 50],
            match_result=mr,
            class_name="มอเตอร์ไซค์ (Motorcycle)",
            annotated_frame=np.zeros((100, 100, 3), dtype=np.uint8),
            car_crop=np.zeros((40, 40, 3), dtype=np.uint8)
        )
        group1 = MatchGroup(
            group_id=1,
            video_path=Path("test1.mp4"),
            start_time=1.0,
            end_time=3.0,
            best_detection=det1,
            detections=[det1],
            direction="ซ้ายไปขวา"
        )
        group2 = MatchGroup(
            group_id=2,
            video_path=Path("test1.mp4"),
            start_time=5.0,
            end_time=7.0,
            best_detection=det1,
            detections=[det1],
            direction="ขวาไปซ้าย"
        )

        gen = ReportGenerator()
        # Mock clip cutter
        gen.clip_cutter.cut_clip = MagicMock(return_value=Path("dummy_clip.mp4"))
        gen.clip_cutter.save_screenshot = MagicMock()

        progress_calls = []
        def on_clip_prog(curr, tot, gid):
            progress_calls.append((curr, tot, gid))
            if curr == 1:
                # Abort after first clip!
                gen.abort_clip_cutting()

        rep_path, scan_f = gen.generate_report(
            target=target,
            events=[group1, group2],
            scanned_videos=[Path("test1.mp4")],
            output_base_dir=output_dir,
            scan_duration_sec=5.0,
            enable_clip_cutting=True,
            clip_progress_callback=on_clip_prog
        )

        self.assertTrue(rep_path.exists())
        self.assertTrue((scan_f / "data" / "results.json").exists())

        # Event 1 should have had cut_clip called, Event 2 was aborted so cut_clip not called for it!
        self.assertEqual(gen.clip_cutter.cut_clip.call_count, 1)
        # Screenshots are saved for both events regardless of abort!
        self.assertEqual(gen.clip_cutter.save_screenshot.call_count, 2)

        # Master index.html must have been created automatically in output_dir
        master_index = output_dir / "index.html"
        self.assertTrue(master_index.exists())
        index_html = master_index.read_text(encoding="utf-8")
        self.assertIn("1กก 1234", index_html)
        self.assertIn("Honda", index_html)


if __name__ == "__main__":
    unittest.main()
