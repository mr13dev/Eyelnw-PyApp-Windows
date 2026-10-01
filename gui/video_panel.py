"""
CCTV Video selection panel for Eyelnw GUI.
Supports single and batch video file selection with size previews.
"""

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from gui.widgets import VideoListItem


class VideoPanel(ctk.CTkFrame):
    """Panel for selecting and managing CCTV video files to be scanned."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=12, fg_color="#161b22", **kwargs)

        self.selected_videos: list[Path] = []

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self,
            text="📹 ขั้นตอนที่ 2: เลือกไฟล์วิดีโอ CCTV",
            font=("Sarabun", 16, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        sub = ctk.CTkLabel(
            self,
            text="เลือกไฟล์วิดีโอ CCTV ที่ต้องการให้ระบบค้นหา (รองรับหลายไฟล์พร้อมกัน: MP4, AVI, MKV, MOV, FLV)",
            font=("Sarabun", 12),
            text_color="#8b949e",
            anchor="w"
        )
        sub.pack(fill="x", padx=16, pady=(0, 12))

        # Actions
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=16, pady=(0, 8))

        self.btn_add_vid = ctk.CTkButton(
            action_bar,
            text="➕ เพิ่มไฟล์วิดีโอ CCTV (เลือกได้หลายไฟล์)",
            command=self._on_add_videos,
            font=("Sarabun", 13, "bold"),
            fg_color="#238636",
            hover_color="#2ea043",
            height=34
        )
        self.btn_add_vid.pack(side="left", padx=(0, 10))

        self.btn_clear_vids = ctk.CTkButton(
            action_bar,
            text="ล้างรายการทั้งหมด",
            command=self._on_clear_videos,
            font=("Sarabun", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            height=34
        )
        self.btn_clear_vids.pack(side="left")

        self.lbl_summary = ctk.CTkLabel(
            action_bar,
            text="ยังไม่มีไฟล์วิดีโอในรายการ",
            font=("Sarabun", 12),
            text_color="#8b949e"
        )
        self.lbl_summary.pack(side="right")

        # Video List container
        self.scroll_list = ctk.CTkScrollableFrame(
            self,
            height=140,
            fg_color="#0d1117",
            corner_radius=8
        )
        self.scroll_list.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _on_add_videos(self):
        files = filedialog.askopenfilenames(
            title="เลือกไฟล์วิดีโอ CCTV (เลือกได้หลายไฟล์)",
            filetypes=[
                ("Video Files", "*.mp4;*.avi;*.mkv;*.mov;*.flv;*.wmv"),
                ("All Files", "*.*")
            ]
        )
        if not files:
            return

        for f in files:
            p = Path(f)
            if p not in self.selected_videos:
                self.selected_videos.append(p)

        self._refresh_list()

    def _on_remove_video(self, path: Path):
        if path in self.selected_videos:
            self.selected_videos.remove(path)
        self._refresh_list()

    def _on_clear_videos(self):
        self.selected_videos.clear()
        self._refresh_list()

    def _refresh_list(self):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        for vid in self.selected_videos:
            item = VideoListItem(self.scroll_list, video_path=vid, on_remove=self._on_remove_video)
            item.pack(fill="x", padx=4, pady=4)

        n = len(self.selected_videos)
        self.lbl_summary.configure(
            text=f"มีไฟล์วิดีโอทั้งหมด {n} ไฟล์" if n > 0 else "ยังไม่มีไฟล์วิดีโอในรายการ"
        )

    def get_videos(self) -> list[Path]:
        return list(self.selected_videos)
