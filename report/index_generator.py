"""
Index generator for compiling an overview HTML page of all scan reports.
"""

from datetime import datetime
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from utils.helpers import format_seconds_to_timestamp
from utils.logger import logger


class ReportIndexGenerator:
    """Scans the output directory and generates an index.html listing all scan reports."""

    def __init__(self, output_dir: Path, templates_dir: Path | None = None):
        self.output_dir = output_dir
        self.index_path = output_dir / "index.html"
        self.templates_dir = templates_dir or Path(__file__).resolve().parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def scan_existing_reports(self) -> list[dict]:
        """
        Scans output/ looking for scan_* folders that contain report.html and data/results.json.
        Returns a list of report summary dictionaries sorted with newest first.
        """
        reports = []
        if not self.output_dir.exists():
            return reports

        for scan_dir in sorted(self.output_dir.glob("scan_*"), reverse=True):
            if not scan_dir.is_dir():
                continue

            report_html = scan_dir / "report.html"
            results_json = scan_dir / "data" / "results.json"

            if not report_html.exists():
                continue

            report_item = {
                "folder_name": scan_dir.name,
                "report_path": str(report_html),
                "relative_path": f"{scan_dir.name}/report.html",
                "timestamp_display": scan_dir.name.replace("scan_", ""),
                "target": {},
                "summary": {},
                "matches_count": 0,
                "highest_confidence": 0.0,
                "total_videos": 0,
                "duration_display": "-"
            }

            if results_json.exists():
                try:
                    data = json.loads(results_json.read_text(encoding="utf-8"))
                    report_item["target"] = data.get("target", {})
                    summary = data.get("summary", {})
                    report_item["summary"] = summary
                    report_item["matches_count"] = summary.get("total_matches", len(data.get("events", [])))
                    report_item["highest_confidence"] = float(summary.get("highest_confidence", 0.0))
                    report_item["total_videos"] = summary.get("total_videos", 1)
                    duration_sec = summary.get("scan_duration_sec", 0.0)
                    report_item["duration_display"] = format_seconds_to_timestamp(duration_sec)

                    raw_ts = data.get("timestamp")
                    if raw_ts:
                        try:
                            dt = datetime.fromisoformat(raw_ts)
                            report_item["timestamp_display"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            report_item["timestamp_display"] = raw_ts
                except Exception as e:
                    logger.warning(f"Error parsing {results_json}: {e}")

            reports.append(report_item)

        return reports

    def generate_index(self) -> Path:
        """Renders and writes index.html into output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        reports = self.scan_existing_reports()

        template = self.env.get_template("index_template.html")
        html = template.render(
            updated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_reports=len(reports),
            reports=reports
        )

        with open(self.index_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Report index updated with {len(reports)} reports: {self.index_path}")
        return self.index_path
