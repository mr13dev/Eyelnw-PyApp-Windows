"""
Main Application Window for Eyelnw.
Coordinates the GUI panels and connects them to the backend scanning engine.
"""

from pathlib import Path
import threading
import time
from tkinter import messagebox
import customtkinter as ctk

from core.color_analyzer import ColorAnalyzer
from core.detector import VehicleDetector
from core.feature_extractor import FeatureExtractor
from core.matcher import VehicleMatcher
from core.ocr_reader import PlateReader
from core.target_loader import TargetLoader
from core.video_scanner import VideoScanner
from gui.result_panel import ResultPanel
from gui.scan_panel import ScanPanel
from gui.target_panel import TargetPanel
from gui.video_panel import VideoPanel
from report.generator import ReportGenerator
from utils.config import ScanConfig
from utils.logger import logger
from utils.settings import SettingsManager


class EyelnwApp(ctk.CTk):
    """Primary GUI Application class for Eyelnw."""

    def __init__(self):
        super().__init__()

        # Window Appearance & Setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("🔍 Eyelnw — ระบบตรวจจับรถจากคลิป CCTV")
        self.geometry("1100x880")
        self.minsize(960, 720)

        icon_path = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Settings manager
        self.settings = SettingsManager()

        # Scanning state & active scanner instance
        self.active_scanner: VideoScanner | None = None
        self.active_report_generator: ReportGenerator | None = None
        self.scan_thread: threading.Thread | None = None

        self._build_layout()

    def _build_layout(self):
        # App Header Banner
        header_banner = ctk.CTkFrame(self, fg_color="#161b22", corner_radius=0, height=65)
        header_banner.pack(fill="x")
        header_banner.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            header_banner,
            text="🔍 Eyelnw",
            font=("Outfit", 22, "bold"),
            text_color="#58a6ff"
        )
        title_lbl.pack(side="left", padx=(20, 10))

        sub_lbl = ctk.CTkLabel(
            header_banner,
            text="ระบบ AI ค้นหารถที่ถูกขโมยจากคลิป CCTV อัตโนมัติ",
            font=("Sarabun", 13),
            text_color="#8b949e"
        )
        sub_lbl.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            header_banner,
            text="v1.0.0-beta • Windows 11",
            font=("Outfit", 11),
            text_color="#6e7681"
        )
        ver_lbl.pack(side="right", padx=20)

        # Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10, fg_color="#0d1117")
        self.tabview.pack(fill="both", expand=True, padx=16, pady=12)

        self.tab_scan = self.tabview.add("🔍 ค้นหารถเป้าหมาย")
        self.tab_results = self.tabview.add("📋 ผลการค้นหา")
        self.tab_help = self.tabview.add("ℹ️ คู่มือการใช้งาน")

        # Build Tab 1: Scan Tab (Target + Video + Scan controls in a scrollable view)
        self._build_scan_tab()

        # Build Tab 2: Results Tab
        self._build_results_tab()

        # Build Tab 3: Help Tab
        self._build_help_tab()

    def _build_scan_tab(self):
        scroll_container = ctk.CTkScrollableFrame(self.tab_scan, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=4, pady=4)

        # 1. Target Panel
        self.target_panel = TargetPanel(scroll_container)
        self.target_panel.pack(fill="x", pady=(0, 14))

        # 2. Video Panel
        self.video_panel = VideoPanel(scroll_container)
        self.video_panel.pack(fill="x", pady=(0, 14))

        # 3. Scan & Settings Panel
        self.scan_panel = ScanPanel(
            scroll_container,
            on_start_scan=self.start_scan_pipeline,
            on_pause_scan=self.pause_scan,
            on_resume_scan=self.resume_scan,
            on_cancel_scan=self.cancel_scan,
            on_abort_clips=self.abort_clip_cutting,
            settings=self.settings
        )
        self.scan_panel.pack(fill="x", pady=(0, 14))

    def _build_results_tab(self):
        self.result_panel = ResultPanel(self.tab_results)
        self.result_panel.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_help_tab(self):
        help_frame = ctk.CTkScrollableFrame(self.tab_help, fg_color="#161b22", corner_radius=12)
        help_frame.pack(fill="both", expand=True, padx=12, pady=12)

        guide_text = (
            "📌 คำแนะนำการใช้งาน Eyelnw ให้ได้ผลลัพธ์แม่นยำสูงสุด\n\n"
            "1. การเลือกรูปรถเป้าหมาย (Target Input):\n"
            "   • ใช้รูปรถ 3-10 รูปที่มีมุมมองหลากหลาย (หน้ารถ, ข้างรถ, ท้ายรถ, และมุมสูงเฉียง)\n"
            "   • หากมีภาพจากมุมกล้องสูงคล้ายมุม CCTV จะช่วยเพิ่มความแม่นยำอย่างยิ่ง\n"
            "   • ระบุข้อมูลเพิ่มเติม เช่น ป้ายทะเบียน หรือ ยี่ห้อรถ เพื่อเพิ่มเกณฑ์การคัดกรอง\n\n"
            "2. การตั้งค่าการค้นหา (Settings):\n"
            "   • เกณฑ์ความเชื่อมั่น (Threshold): แนะนำเริ่มต้นที่ 60% (0.60)\n"
            "   • ความเร็วสแกน: โหมด 'สมดุล' สแกนประมาณ 2 ครั้งต่อวินาที ช่วยลดเวลาประมวลผลคลิปยาวได้หลายเท่า\n"
            "   • หากเครื่องมี GPU NVIDIA ระบบจะเปิดใช้งาน CUDA อัตโนมัติเพื่อความเร็วสูงสุด\n\n"
            "3. ผลลัพธ์และการนำไปใช้ (Output & Report):\n"
            "   • รายงานผลจะถูกบันทึกเป็นเว็บหน้าเดียว (HTML) พร้อมภาพตัดและคลิปวิดีโอสั้นช่วงที่ตรวจพบ\n"
            "   • สามารถคลิกปุ่ม 'เปิดรายงาน HTML' หรือ 'เปิดโฟลเดอร์ผลลัพธ์' เพื่อส่งต่อเบาะแสให้เจ้าหน้าที่ตำรวจ\n\n"
            "⚠️ ข้อควรทราบทางกฎหมาย:\n"
            "   • ผลลัพธ์จากโปรแกรมจัดทำขึ้นเพื่อเป็นเบาะแสเบื้องต้นในการสืบสวนเท่านั้น\n"
        )

        lbl = ctk.CTkLabel(
            help_frame,
            text=guide_text,
            font=("Sarabun", 14),
            justify="left",
            text_color="#e6edf3",
            anchor="w",
            padx=20,
            pady=20
        )
        lbl.pack(fill="both", expand=True)

    def start_scan_pipeline(self, scan_params: dict):
        """Validates inputs and starts detection in a worker thread."""
        target_data = self.target_panel.get_data()
        video_paths = self.video_panel.get_videos()

        if not target_data["image_paths"]:
            messagebox.showwarning("แจ้งเตือน", "กรุณาแนบรูปรถเป้าหมายอย่างน้อย 1 รูป ก่อนเริ่มค้นหา")
            self.scan_panel.finish_scan()
            return

        if not video_paths:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกไฟล์วิดีโอ CCTV อย่างน้อย 1 ไฟล์")
            self.scan_panel.finish_scan()
            return

        if "📋 ผลการค้นหา" in self.tabview._segmented_button._buttons_dict:
            self.tabview._segmented_button._buttons_dict["📋 ผลการค้นหา"].configure(
                text="📋 ผลการค้นหา"
            )

        self.scan_thread = threading.Thread(
            target=self._run_scan_thread,
            args=(target_data, video_paths, scan_params),
            daemon=True
        )
        self.scan_thread.start()

    def _run_scan_thread(self, target_data: dict, video_paths: list[Path], scan_params: dict):
        """Worker thread for AI loading, scanning, and report generation."""
        start_time = time.time()
        try:
            self._update_progress_safe(0, 100, 0, 0, 0, "กำลังโหลดโมเดล AI และวิเคราะห์รูปรถเป้าหมาย...")

            # 1. Initialize AI subsystems
            color_analyzer = ColorAnalyzer()
            feature_extractor = FeatureExtractor()
            plate_reader = PlateReader()
            target_loader = TargetLoader(color_analyzer, feature_extractor)

            # 2. Build target profile
            target_profile = target_loader.build_profile(
                image_paths=target_data["image_paths"],
                plate_number=target_data["plate_number"],
                car_color=target_data["car_color"],
                car_brand=target_data["car_brand"],
                car_model=target_data["car_model"]
            )

            # 3. Initialize detector & matcher
            enable_clips = scan_params.get("enable_clip_cutting", True)
            config = ScanConfig(
                model_size=scan_params.get("model_size", "n"),
                match_threshold=scan_params.get("threshold", 0.60),
                frame_skip=scan_params.get("frame_skip", 15),
                enable_clip_cutting=enable_clips
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

            self.active_scanner = VideoScanner(detector, matcher, config)

            all_matched_events = []
            total_vids = len(video_paths)

            for i, vid_path in enumerate(video_paths):
                prefix_status = f"[{i + 1}/{total_vids}] "

                def progress_cb(cur_f, tot_f, cur_t, tot_t, matches, status_txt):
                    self._update_progress_safe(
                        cur_f, tot_f, cur_t, tot_t,
                        len(all_matched_events) + matches,
                        f"{prefix_status}{status_txt}"
                    )

                events = self.active_scanner.scan_video(vid_path, progress_callback=progress_cb)
                all_matched_events.extend(events)

            # 4. Generate Reports and Clips
            post_msg = "กำลังตัดคลิปสั้นและสร้างรายงาน HTML..." if enable_clips else "กำลังบันทึกภาพถ่ายและสร้างรายงาน HTML..."
            self._update_progress_safe(100, 100, 0, 0, len(all_matched_events), post_msg)
            duration = time.time() - start_time
            self.active_report_generator = ReportGenerator()

            def clip_progress_cb(current, total, group_id):
                self._update_clip_progress_safe(current, total, group_id)

            report_path, folder_path = self.active_report_generator.generate_report(
                target=target_profile,
                events=all_matched_events,
                scanned_videos=video_paths,
                scan_duration_sec=duration,
                enable_clip_cutting=enable_clips,
                clip_progress_callback=clip_progress_cb
            )

            # 5. Notify UI on completion
            self.after(0, lambda: self._on_scan_completed(all_matched_events, report_path, folder_path))

        except Exception as e:
            logger.exception("Error during scanning pipeline:")
            self.after(0, lambda err=e: self._on_scan_error(err))
        finally:
            self.active_report_generator = None
            self.after(0, self.scan_panel.finish_scan)

    def _update_progress_safe(self, cur_f, tot_f, cur_t, tot_t, matches, txt):
        self.after(0, lambda: self.scan_panel.update_progress(cur_f, tot_f, cur_t, tot_t, matches, txt))

    def _update_clip_progress_safe(self, current: int, total: int, group_id: int):
        self.after(0, lambda: self.scan_panel.update_clip_progress(current, total, group_id))

    def _on_scan_completed(self, events: list, report_path: Path, folder_path: Path):
        self.result_panel.set_results(events, report_path, folder_path)
        self.tabview.set("📋 ผลการค้นหา")
        if "📋 ผลการค้นหา" in self.tabview._segmented_button._buttons_dict:
            self.tabview._segmented_button._buttons_dict["📋 ผลการค้นหา"].configure(
                text=f"📋 ผลการค้นหา ({len(events)})"
            )
        messagebox.showinfo(
            "การสแกนเสร็จสิ้น",
            f"การค้นหาเสร็จสมบูรณ์!\nพบเหตุการณ์ที่ตรงกับรถเป้าหมายทั้งหมด {len(events)} ครั้ง\nสร้างรายงาน HTML เรียบร้อยแล้ว"
        )

    def _on_scan_error(self, error: Exception):
        messagebox.showerror("เกิดข้อผิดพลาด", f"เกิดข้อผิดพลาดในการประมวลผล:\n{str(error)}")

    def pause_scan(self):
        if self.active_scanner:
            self.active_scanner.pause()

    def resume_scan(self):
        if self.active_scanner:
            self.active_scanner.resume()

    def cancel_scan(self):
        if self.active_scanner:
            self.active_scanner.cancel()

    def abort_clip_cutting(self):
        """Signals the active report generator to abort cutting further video clips."""
        if self.active_report_generator:
            self.active_report_generator.abort_clip_cutting()
