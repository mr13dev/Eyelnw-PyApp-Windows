"""
Result presentation panel for Eyelnw GUI.
Displays detected events, confidence badges, screenshots, and report launch buttons.
"""

import os
from pathlib import Path
import subprocess
import webbrowser
import customtkinter as ctk
from PIL import Image

from core.video_scanner import MatchGroup
from utils.helpers import cv2_to_pil


class ResultEventCard(ctk.CTkFrame):
    """Card displaying a single matched event cluster."""

    def __init__(self, master, event: MatchGroup, **kwargs):
        super().__init__(master, corner_radius=10, fg_color="#1e242c", **kwargs)
        self.event = event

        self._build_card()

    def _build_card(self):
        # 2-column layout: left = image, right = details
        self.grid_columnconfigure(1, weight=1)

        # Left Column: Image preview
        left_box = ctk.CTkFrame(self, fg_color="transparent")
        left_box.grid(row=0, column=0, padx=12, pady=12, sticky="nw")

        try:
            pil_img = cv2_to_pil(self.event.best_detection.annotated_frame)
            pil_img.thumbnail((220, 140))
            self.ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(220, 140))
            lbl_img = ctk.CTkLabel(left_box, image=self.ctk_img, text="")
            lbl_img.pack()
        except Exception:
            lbl_img = ctk.CTkLabel(left_box, text="📸 ภาพตรวจพบ", width=220, height=140, fg_color="#0d1117")
            lbl_img.pack()

        # Right Column: Details & actions
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.grid(row=0, column=1, padx=(0, 12), pady=12, sticky="nsew")

        # Top title row: Event # + Confidence pill
        top_row = ctk.CTkFrame(right_box, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 6))

        title = ctk.CTkLabel(
            top_row,
            text=f"#{self.event.group_id}  📹 {self.event.video_path.name}",
            font=("Sarabun", 14, "bold"),
            text_color="#58a6ff"
        )
        title.pack(side="left")

        conf = self.event.peak_confidence
        conf_pct = int(round(conf * 100))
        if conf >= 0.80:
            badge_color = "#238636"
            badge_txt = f"{conf_pct}% ความมั่นใจสูง"
        elif conf >= 0.65:
            badge_color = "#9e6a03"
            badge_txt = f"{conf_pct}% ปานกลาง"
        else:
            badge_color = "#8957e5"
            badge_txt = f"{conf_pct}% ความเชื่อมั่น"

        pill = ctk.CTkLabel(
            top_row,
            text=badge_txt,
            fg_color=badge_color,
            text_color="#ffffff",
            font=("Sarabun", 11, "bold"),
            corner_radius=12,
            padx=10,
            pady=2
        )
        pill.pack(side="right")

        # Timestamp & motion row
        meta_row = ctk.CTkLabel(
            right_box,
            text=f"⏱ เวลาในคลิป: {self.event.best_detection.timestamp_str} ({self.event.start_time:.1f}s - {self.event.end_time:.1f}s)",
            font=("Sarabun", 12),
            text_color="#e6edf3",
            anchor="w"
        )
        meta_row.pack(fill="x", pady=(0, 4))

        # Attributes grid
        attr_frame = ctk.CTkFrame(right_box, fg_color="#0d1117", corner_radius=6)
        attr_frame.pack(fill="x", pady=(0, 8), padx=0)

        attr_text = (
            f"🧭 ทิศทาง: {self.event.direction}   •   "
            f"🎨 สี: {self.event.best_detection.match_result.detected_color}   •   "
            f"📝 ทะเบียน: {self.event.best_detection.match_result.detected_plate or 'ไม่ชัดเจน'}"
        )
        lbl_attrs = ctk.CTkLabel(attr_frame, text=attr_text, font=("Sarabun", 11), text_color="#8b949e", padx=8, pady=4)
        lbl_attrs.pack(anchor="w")

        # Action buttons row
        btn_row = ctk.CTkFrame(right_box, fg_color="transparent")
        btn_row.pack(fill="x")

        if self.event.clip_path and self.event.clip_path.exists():
            btn_play = ctk.CTkButton(
                btn_row,
                text="▶ ดูคลิปสั้น",
                command=self._on_play_clip,
                font=("Sarabun", 11, "bold"),
                fg_color="#238636",
                hover_color="#2ea043",
                height=28,
                width=100
            )
            btn_play.pack(side="left", padx=(0, 8))

        if self.event.screenshot_path and self.event.screenshot_path.exists():
            btn_shot = ctk.CTkButton(
                btn_row,
                text="📸 เปิดภาพขนาดเต็ม",
                command=self._on_view_screenshot,
                font=("Sarabun", 11),
                fg_color="#21262d",
                hover_color="#30363d",
                height=28,
                width=120
            )
            btn_shot.pack(side="left")

    def _on_play_clip(self):
        if self.event.clip_path and self.event.clip_path.exists():
            os.startfile(str(self.event.clip_path))

    def _on_view_screenshot(self):
        if self.event.screenshot_path and self.event.screenshot_path.exists():
            os.startfile(str(self.event.screenshot_path))


class ResultPanel(ctk.CTkFrame):
    """Panel displaying detection results, filtering options, and report launchers."""

    def __init__(self, master, on_reset_callback=None, **kwargs):
        super().__init__(master, corner_radius=12, fg_color="#161b22", **kwargs)

        self.on_reset_callback = on_reset_callback
        self.events: list[MatchGroup] = []
        self.report_html_path: Path | None = None
        self.scan_folder_path: Path | None = None

        self._build_ui()

    def _build_ui(self):
        # Header
        top_header = ctk.CTkFrame(self, fg_color="transparent")
        top_header.pack(fill="x", padx=16, pady=(16, 8))

        self.lbl_header = ctk.CTkLabel(
            top_header,
            text="📋 ผลการค้นหารถเป้าหมาย",
            font=("Sarabun", 18, "bold"),
            anchor="w"
        )
        self.lbl_header.pack(side="left")

        # Global action buttons
        self.btn_open_report = ctk.CTkButton(
            top_header,
            text="📄 เปิดรายงาน HTML",
            command=self._on_open_report,
            font=("Sarabun", 12, "bold"),
            fg_color="#2f81f7",
            hover_color="#1a73e8",
            height=32,
            state="disabled"
        )
        self.btn_open_report.pack(side="right", padx=(8, 0))

        self.btn_open_folder = ctk.CTkButton(
            top_header,
            text="📁 เปิดโฟลเดอร์ผลลัพธ์",
            command=self._on_open_folder,
            font=("Sarabun", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            height=32,
            state="disabled"
        )
        self.btn_open_folder.pack(side="right")

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=8)
        filter_bar.pack(fill="x", padx=16, pady=(0, 12))

        lbl_filter = ctk.CTkLabel(filter_bar, text="กรองความมั่นใจ:", font=("Sarabun", 12))
        lbl_filter.pack(side="left", padx=(12, 8), pady=8)

        self.combo_filter = ctk.CTkComboBox(
            filter_bar,
            values=["ทั้งหมด", "≥ 60%", "≥ 70%", "≥ 80%"],
            width=120,
            command=self._on_filter_changed,
            font=("Sarabun", 12)
        )
        self.combo_filter.set("ทั้งหมด")
        self.combo_filter.pack(side="left", pady=8)

        lbl_sort = ctk.CTkLabel(filter_bar, text="เรียงตาม:", font=("Sarabun", 12))
        lbl_sort.pack(side="left", padx=(20, 8), pady=8)

        self.combo_sort = ctk.CTkComboBox(
            filter_bar,
            values=["ช่วงเวลาในคลิป", "ความมั่นใจสูงสุด"],
            width=150,
            command=self._on_filter_changed,
            font=("Sarabun", 12)
        )
        self.combo_sort.set("ช่วงเวลาในคลิป")
        self.combo_sort.pack(side="left", pady=8)

        self.lbl_stats = ctk.CTkLabel(
            filter_bar,
            text="ยังไม่มีผลลัพธ์",
            font=("Sarabun", 12, "bold"),
            text_color="#58a6ff"
        )
        self.lbl_stats.pack(side="right", padx=14, pady=8)

        # Scrollable events area
        self.scroll_events = ctk.CTkScrollableFrame(
            self,
            fg_color="#0d1117",
            corner_radius=8
        )
        self.scroll_events.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Initial placeholder
        self.placeholder_lbl = ctk.CTkLabel(
            self.scroll_events,
            text="ผลลัพธ์จะปรากฏที่นี่เมื่อการสแกนเสร็จสิ้น",
            font=("Sarabun", 14),
            text_color="#8b949e"
        )
        self.placeholder_lbl.pack(pady=40)

    def set_results(self, events: list[MatchGroup], report_html_path: Path, scan_folder_path: Path):
        """Populates the result panel with scan output."""
        self.events = events
        self.report_html_path = report_html_path
        self.scan_folder_path = scan_folder_path

        self.btn_open_report.configure(state="normal")
        self.btn_open_folder.configure(state="normal")

        self._refresh_events_list()

    def _on_filter_changed(self, _=None):
        self._refresh_events_list()

    def _refresh_events_list(self):
        for w in self.scroll_events.winfo_children():
            w.destroy()

        if not self.events:
            empty_lbl = ctk.CTkLabel(
                self.scroll_events,
                text="ไม่พบรถที่ตรงกับเกณฑ์ที่กำหนดในการสแกนนี้",
                font=("Sarabun", 14),
                text_color="#8b949e"
            )
            empty_lbl.pack(pady=40)
            self.lbl_stats.configure(text="พบ 0 ครั้ง")
            return

        filter_val = self.combo_filter.get()
        min_conf = 0.0
        if "60%" in filter_val:
            min_conf = 0.60
        elif "70%" in filter_val:
            min_conf = 0.70
        elif "80%" in filter_val:
            min_conf = 0.80

        filtered = [e for e in self.events if e.peak_confidence >= min_conf]

        # Sorting
        sort_val = self.combo_sort.get()
        if "ความมั่นใจ" in sort_val:
            filtered.sort(key=lambda e: e.peak_confidence, reverse=True)
        else:
            filtered.sort(key=lambda e: (str(e.video_path), e.start_time))

        self.lbl_stats.configure(text=f"แสดง {len(filtered)} / {len(self.events)} ครั้ง")

        for event in filtered:
            card = ResultEventCard(self.scroll_events, event=event)
            card.pack(fill="x", padx=4, pady=6)

    def _on_open_report(self):
        if self.report_html_path and self.report_html_path.exists():
            webbrowser.open(self.report_html_path.as_uri())

    def _on_open_folder(self):
        if self.scan_folder_path and self.scan_folder_path.exists():
            os.startfile(str(self.scan_folder_path))
