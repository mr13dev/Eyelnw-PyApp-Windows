"""
Scan control and real-time progress panel for Eyelnw GUI.
"""

import time
import customtkinter as ctk
import torch
from utils.helpers import format_seconds_to_timestamp
from utils.settings import SettingsManager


class ScanPanel(ctk.CTkFrame):
    """Panel for configuring scan parameters, launching detection, and tracking progress."""

    def __init__(
        self,
        master,
        on_start_scan,
        on_pause_scan,
        on_resume_scan,
        on_cancel_scan,
        on_abort_clips=None,
        settings: SettingsManager | None = None,
        **kwargs
    ):
        super().__init__(master, corner_radius=12, fg_color="#161b22", **kwargs)

        self.on_start_scan = on_start_scan
        self.on_pause_scan = on_pause_scan
        self.on_resume_scan = on_resume_scan
        self.on_cancel_scan = on_cancel_scan
        self.on_abort_clips = on_abort_clips
        self.settings = settings or SettingsManager()

        self.is_scanning = False
        self.is_paused = False
        self.scan_start_epoch = 0.0

        self._build_ui()
        self._load_saved_settings()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text="⚙️ ขั้นตอนที่ 3: ตั้งค่าและเริ่มค้นหา",
            font=("Sarabun", 16, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        # Hardware & Speed Settings Row
        settings_frame = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=8)
        settings_frame.pack(fill="x", padx=16, pady=(0, 14))

        # Row 1: Model & Hardware Acceleration badge
        r1 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=10)

        lbl_model = ctk.CTkLabel(r1, text="โมเดลตรวจจับ:", font=("Sarabun", 12))
        lbl_model.pack(side="left", padx=(0, 8))
        self.combo_model = ctk.CTkComboBox(
            r1,
            values=["YOLOv8n (เร็วมาก / แนะนำ)", "YOLOv8s (แม่นยำสูง)", "YOLOv8m (สูงสุด)"],
            width=200,
            font=("Sarabun", 12)
        )
        self.combo_model.set("YOLOv8n (เร็วมาก / แนะนำ)")
        self.combo_model.pack(side="left", padx=(0, 20))

        # Device badge
        cuda_avail = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
        badge_text = f"🚀 GPU: {gpu_name}" if cuda_avail else "💻 CPU Mode"
        badge_color = "#238636" if cuda_avail else "#6e7681"

        self.gpu_badge = ctk.CTkLabel(
            r1,
            text=badge_text,
            fg_color=badge_color,
            text_color="#ffffff",
            corner_radius=6,
            font=("Sarabun", 11, "bold"),
            padx=10,
            pady=4
        )
        self.gpu_badge.pack(side="right")

        # Row 2: Threshold & Speed
        r2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(0, 10))

        lbl_thresh = ctk.CTkLabel(r2, text="เกณฑ์ความเชื่อมั่น (Threshold):", font=("Sarabun", 12))
        lbl_thresh.pack(side="left", padx=(0, 8))
        self.slider_thresh = ctk.CTkSlider(
            r2,
            from_=0.40,
            to=0.85,
            number_of_steps=9,
            width=160,
            command=self._on_thresh_change
        )
        self.slider_thresh.set(0.60)
        self.slider_thresh.pack(side="left", padx=(0, 10))

        self.lbl_thresh_val = ctk.CTkLabel(r2, text="60%", font=("Outfit", 13, "bold"), text_color="#58a6ff", width=40)
        self.lbl_thresh_val.pack(side="left", padx=(0, 30))

        lbl_speed = ctk.CTkLabel(r2, text="ความเร็วสแกน:", font=("Sarabun", 12))
        lbl_speed.pack(side="left", padx=(0, 8))
        self.combo_speed = ctk.CTkComboBox(
            r2,
            values=["สแกนเร็ว (ทุก 1 วินาที)", "สมดุล (2 ครั้ง/วินาที)", "ละเอียด (4 ครั้ง/วินาที)"],
            width=180,
            font=("Sarabun", 12)
        )
        self.combo_speed.set("สมดุล (2 ครั้ง/วินาที)")
        self.combo_speed.pack(side="left")

        # Row 3: Clip cutting switch
        r3 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        r3.pack(fill="x", padx=12, pady=(0, 12))

        self.switch_cut_clips = ctk.CTkSwitch(
            r3,
            text="🎬 ตัดคลิปวิดีโอสั้นอัตโนมัติ (Cut short clips)",
            font=("Sarabun", 12, "bold"),
            onvalue=True,
            offvalue=False,
            progress_color="#2f81f7"
        )
        self.switch_cut_clips.select()  # Default enabled
        self.switch_cut_clips.pack(side="left", padx=(0, 12))

        lbl_switch_hint = ctk.CTkLabel(
            r3,
            text="(หากปิด จะช่วยประหยัดเวลาและพื้นที่จัดเก็บ โดยจะบันทึกเฉพาะภาพถ่ายและรายงาน HTML)",
            font=("Sarabun", 11),
            text_color="#8b949e"
        )
        lbl_switch_hint.pack(side="left")

        self.btn_reset_settings = ctk.CTkButton(
            r3,
            text="🔄 รีเซ็ตค่าเริ่มต้น",
            command=self._on_reset_settings,
            font=("Sarabun", 11),
            fg_color="#21262d",
            hover_color="#30363d",
            height=28,
            width=120
        )
        self.btn_reset_settings.pack(side="right")

        # Big CTA Action Button
        self.btn_start = ctk.CTkButton(
            self,
            text="🔍 เริ่มค้นหารถเป้าหมาย",
            command=self._on_start_clicked,
            font=("Sarabun", 16, "bold"),
            fg_color="#2f81f7",
            hover_color="#1a73e8",
            height=46,
            corner_radius=8
        )
        self.btn_start.pack(fill="x", padx=16, pady=(0, 16))

        # Real-time Progress Container
        self.progress_frame = ctk.CTkFrame(self, fg_color="#0d1117", corner_radius=8)
        self.progress_frame.pack(fill="x", padx=16, pady=(0, 16))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=12, corner_radius=6)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=14, pady=(14, 8))

        # Status text row
        stat_row = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        stat_row.pack(fill="x", padx=14, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(
            stat_row,
            text="พร้อมเริ่มการสแกน",
            font=("Sarabun", 12),
            text_color="#e6edf3",
            anchor="w"
        )
        self.lbl_status.pack(side="left")

        self.lbl_percent = ctk.CTkLabel(
            stat_row,
            text="0%",
            font=("Outfit", 12, "bold"),
            text_color="#58a6ff"
        )
        self.lbl_percent.pack(side="right")

        # Meta counters row
        meta_row = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        meta_row.pack(fill="x", padx=14, pady=(0, 12))

        self.lbl_matches_count = ctk.CTkLabel(
            meta_row,
            text="🎯 พบรถเป้าหมาย: 0 ครั้ง",
            font=("Sarabun", 12, "bold"),
            text_color="#3fb950"
        )
        self.lbl_matches_count.pack(side="left")

        self.lbl_time_eta = ctk.CTkLabel(
            meta_row,
            text="เวลาที่ใช้: 00:00:00",
            font=("Sarabun", 11),
            text_color="#8b949e"
        )
        self.lbl_time_eta.pack(side="right")

        # Control Buttons (Pause / Resume / Cancel / Abort Clips)
        self.ctrl_row = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.ctrl_row.pack(fill="x", padx=14, pady=(0, 14))

        self.btn_pause = ctk.CTkButton(
            self.ctrl_row,
            text="⏸ หยุดชั่วคราว",
            command=self._on_toggle_pause,
            state="disabled",
            fg_color="#21262d",
            hover_color="#30363d",
            font=("Sarabun", 12),
            width=110,
            height=30
        )
        self.btn_pause.pack(side="left", padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            self.ctrl_row,
            text="⏹ ยกเลิกการสแกน",
            command=self._on_cancel,
            state="disabled",
            fg_color="#f85149",
            hover_color="#da3633",
            font=("Sarabun", 12),
            width=120,
            height=30
        )
        self.btn_cancel.pack(side="left")

        self.btn_abort_clips = ctk.CTkButton(
            self.ctrl_row,
            text="⏭ หยุดตัดคลิป",
            command=self._on_abort_clips,
            state="disabled",
            fg_color="#d29922",
            hover_color="#bb8009",
            font=("Sarabun", 12),
            width=120,
            height=30
        )
        self.btn_abort_clips.pack(side="left", padx=(8, 0))

    def _load_saved_settings(self):
        """กู้คืนค่า widget จาก settings.json"""
        self.combo_model.set(self.settings.get("model_choice"))
        thresh = float(self.settings.get("match_threshold", 0.60))
        self.slider_thresh.set(thresh)
        self.combo_speed.set(self.settings.get("scan_speed"))

        if self.settings.get("enable_clip_cutting"):
            self.switch_cut_clips.select()
        else:
            self.switch_cut_clips.deselect()

        self._on_thresh_change(thresh)

    def _save_current_settings(self):
        """บันทึกค่าปัจจุบันทั้งหมดลง settings.json"""
        self.settings.set("model_choice", self.combo_model.get())
        self.settings.set("match_threshold", float(self.slider_thresh.get()))
        self.settings.set("scan_speed", self.combo_speed.get())
        self.settings.set("enable_clip_cutting", bool(self.switch_cut_clips.get()))

    def _on_reset_settings(self):
        """รีเซ็ตทุกค่ากลับสู่ค่าเริ่มต้นและอัปเดต UI"""
        self.settings.reset_all()
        self._load_saved_settings()

    def _on_abort_clips(self):
        """ส่งสัญญาณสั่งหยุดตัดคลิป"""
        self.btn_abort_clips.configure(state="disabled", text="กำลังหยุดตัดคลิป...")
        if self.on_abort_clips:
            self.on_abort_clips()

    def _on_thresh_change(self, value):
        self.lbl_thresh_val.configure(text=f"{int(round(value * 100))}%")

    def _on_start_clicked(self):
        if self.is_scanning:
            return

        self._save_current_settings()

        self.is_scanning = True
        self.is_paused = False
        self.scan_start_epoch = time.time()

        self.btn_start.configure(state="disabled", text="⏳ กำลังประมวลผล...")
        self.btn_pause.configure(state="normal", text="⏸ หยุดชั่วคราว")
        self.btn_cancel.configure(state="normal")
        self.btn_abort_clips.configure(state="disabled", text="⏭ หยุดตัดคลิป")
        self.progress_bar.set(0.0)
        self.lbl_percent.configure(text="0%")

        model_str = self.combo_model.get()
        size_code = "n"
        if "YOLOv8s" in model_str:
            size_code = "s"
        elif "YOLOv8m" in model_str:
            size_code = "m"

        speed_str = self.combo_speed.get()
        skip = 15
        if "เร็ว" in speed_str:
            skip = 25
        elif "ละเอียด" in speed_str:
            skip = 8

        config_params = {
            "model_size": size_code,
            "threshold": float(self.slider_thresh.get()),
            "frame_skip": skip,
            "enable_clip_cutting": bool(self.switch_cut_clips.get())
        }

        self.on_start_scan(config_params)

    def _on_toggle_pause(self):
        if not self.is_scanning:
            return

        if not self.is_paused:
            self.is_paused = True
            self.btn_pause.configure(text="▶ ทำต่อ", fg_color="#238636", hover_color="#2ea043")
            self.on_pause_scan()
        else:
            self.is_paused = False
            self.btn_pause.configure(text="⏸ หยุดชั่วคราว", fg_color="#21262d", hover_color="#30363d")
            self.on_resume_scan()

    def _on_cancel(self):
        self.on_cancel_scan()
        self.lbl_status.configure(text="ยกเลิกการสแกนแล้ว")
        self.finish_scan()

    def update_progress(
        self,
        current_frame: int,
        total_frames: int,
        current_time: float,
        total_time: float,
        matches_found: int,
        status_text: str
    ):
        """Thread-safe UI updater called from worker thread."""
        fraction = max(0.0, min(1.0, current_frame / max(1, total_frames)))
        self.progress_bar.set(fraction)
        self.lbl_percent.configure(text=f"{int(fraction * 100)}%")
        self.lbl_status.configure(text=status_text)
        self.lbl_matches_count.configure(text=f"🎯 พบรถเป้าหมาย: {matches_found} ครั้ง")

        elapsed = time.time() - self.scan_start_epoch
        self.lbl_time_eta.configure(
            text=f"เวลาที่ใช้: {format_seconds_to_timestamp(elapsed)}  (วิดีโอ: {format_seconds_to_timestamp(current_time)} / {format_seconds_to_timestamp(total_time)})"
        )

    def update_clip_progress(self, current: int, total: int, group_id: int):
        """อัปเดต progress สำหรับขั้นตอนตัดคลิป"""
        fraction = max(0.0, min(1.0, current / max(1, total)))
        self.progress_bar.set(fraction)
        self.lbl_percent.configure(text=f"{int(fraction * 100)}%")
        self.lbl_status.configure(text=f"✂️ กำลังตัดคลิป #{group_id} ({current}/{total})")

        if self.btn_abort_clips.cget("state") != "normal":
            self.btn_abort_clips.configure(state="normal", text="⏭ หยุดตัดคลิป")

    def finish_scan(self):
        """Resets controls when scan finishes or stops."""
        self.is_scanning = False
        self.is_paused = False
        self.btn_start.configure(state="normal", text="🔍 เริ่มค้นหารถเป้าหมาย")
        self.btn_pause.configure(state="disabled", text="⏸ หยุดชั่วคราว", fg_color="#21262d")
        self.btn_cancel.configure(state="disabled")
        self.btn_abort_clips.configure(state="disabled", text="⏭ หยุดตัดคลิป")
