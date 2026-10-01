"""
HTML and JSON report generator for Eyelnw vehicle detection scans.
"""

from datetime import datetime
import json
from pathlib import Path
try:
    import cv2
except ImportError:
    cv2 = None
from jinja2 import Environment, FileSystemLoader

from core.target_loader import TargetProfile
from core.video_scanner import MatchGroup
from report.clip_cutter import VideoClipCutter
from utils.helpers import format_seconds_to_timestamp
from utils.logger import logger


class ReportGenerator:
    """Generates structured HTML & JSON reports, cuts clips, and saves screenshots."""

    def __init__(self, templates_dir: Path | None = None):
        self.templates_dir = templates_dir or Path(__file__).resolve().parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))
        self.clip_cutter = VideoClipCutter()
        self._abort_clips = False

    def abort_clip_cutting(self):
        """Signals to stop cutting clips immediately. Completed clips and screenshots are kept."""
        self._abort_clips = True
        logger.info("Abort clip cutting requested.")

    def generate_report(
        self,
        target: TargetProfile,
        events: list[MatchGroup],
        scanned_videos: list[Path],
        output_base_dir: Path | None = None,
        scan_duration_sec: float = 0.0,
        enable_clip_cutting: bool = True,
        clip_progress_callback=None
    ) -> tuple[Path, Path]:
        """
        Creates a complete scan report with screenshots, optional clips, and HTML summary.
        Returns (report_html_path, scan_folder_path).
        """
        base_dir = output_base_dir or Path(__file__).resolve().parent.parent / "output"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        scan_folder = base_dir / f"scan_{timestamp_str}"

        screenshots_dir = scan_folder / "screenshots"
        clips_dir = scan_folder / "clips"
        target_dir = scan_folder / "target"
        data_dir = scan_folder / "data"

        for d in [screenshots_dir, clips_dir, target_dir, data_dir]:
            d.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating scan report in: {scan_folder} (Clip cutting: {'ON' if enable_clip_cutting else 'OFF'})")

        # 1. Save target reference images to target/
        target_rel_paths = []
        for i, img in enumerate(target.images):
            target_file = target_dir / f"ref_{i + 1:02d}.jpg"
            cv2.imencode(".jpg", img)[1].tofile(str(target_file))
            target_rel_paths.append(f"target/{target_file.name}")

        # 2. Process events: save screenshots & optionally cut clips
        view_events = []
        highest_conf = 0.0

        for i, event in enumerate(events):
            time_tag = event.best_detection.timestamp_str.replace(":", "")
            shot_name = f"match_{event.group_id:03d}_{time_tag}.jpg"
            shot_path = screenshots_dir / shot_name
            self.clip_cutter.save_screenshot(event.best_detection.annotated_frame, shot_path)
            event.screenshot_path = shot_path

            # Cut short clip if enabled and not aborted
            actual_clip = None
            clip_name = f"clip_{event.group_id:03d}_{time_tag}.mp4"
            if enable_clip_cutting and not self._abort_clips:
                if clip_progress_callback:
                    try:
                        clip_progress_callback(i + 1, len(events), event.group_id)
                    except Exception:
                        pass

                clip_path = clips_dir / clip_name
                actual_clip = self.clip_cutter.cut_clip(
                    source_video=event.video_path,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    output_path=clip_path
                )
            event.clip_path = actual_clip

            highest_conf = max(highest_conf, event.peak_confidence)

            # Dictionary structure for Jinja2 template
            view_events.append({
                "group_id": event.group_id,
                "video_name": event.video_path.name,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "peak_confidence": event.peak_confidence,
                "direction": event.direction,
                "best_detection": event.best_detection,
                "screenshot_rel": f"screenshots/{shot_name}",
                "clip_rel": f"clips/{clip_name}" if actual_clip and actual_clip.exists() else None,
            })

        # 3. Render HTML
        template = self.env.get_template("report_template.html")
        html_content = template.render(
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_matches=len(events),
            total_videos=len(scanned_videos),
            highest_confidence=f"{highest_conf * 100:.1f}",
            scan_duration=format_seconds_to_timestamp(scan_duration_sec),
            target=target,
            target_image_paths=target_rel_paths,
            events=view_events
        )

        report_html_path = scan_folder / "report.html"
        with open(report_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 4. Save JSON structured data
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "target": {
                "plate_number": target.plate_number,
                "car_color": target.car_color or target.dominant_color,
                "car_brand": target.car_brand,
                "car_model": target.car_model,
                "reference_images_count": len(target.images)
            },
            "summary": {
                "total_matches": len(events),
                "total_videos": len(scanned_videos),
                "highest_confidence": highest_conf,
                "scan_duration_sec": scan_duration_sec
            },
            "events": [
                {
                    "group_id": e["group_id"],
                    "video": e["video_name"],
                    "start_time": e["start_time"],
                    "end_time": e["end_time"],
                    "peak_confidence": float(e["peak_confidence"]),
                    "direction": e["direction"],
                    "detected_color": e["best_detection"].match_result.detected_color,
                    "detected_plate": e["best_detection"].match_result.detected_plate,
                    "scores": {
                        "color": float(e["best_detection"].match_result.color_score),
                        "feature": float(e["best_detection"].match_result.feature_score),
                        "deep": float(e["best_detection"].match_result.deep_score),
                        "ocr": float(e["best_detection"].match_result.ocr_score)
                    }
                }
                for e in view_events
            ]
        }

        json_file_path = data_dir / "results.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # 5. Update index.html
        try:
            from report.index_generator import ReportIndexGenerator
            index_gen = ReportIndexGenerator(base_dir, templates_dir=self.templates_dir)
            index_gen.generate_index()
        except Exception as e:
            logger.warning(f"Could not update index.html: {e}")

        # Reset abort flag
        self._abort_clips = False

        logger.info(f"Report generated successfully: {report_html_path}")
        return report_html_path, scan_folder
