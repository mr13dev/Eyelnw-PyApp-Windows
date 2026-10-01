"""
Reusable CustomTkinter UI components for Eyelnw.
"""

from pathlib import Path
import customtkinter as ctk
from PIL import Image


class ImageThumbnail(ctk.CTkFrame):
    """Thumbnail card representing an added target vehicle image."""

    def __init__(self, master, image_path: Path, on_remove, **kwargs):
        super().__init__(master, corner_radius=8, fg_color="#1e242c", **kwargs)
        self.image_path = image_path
        self.on_remove = on_remove

        # Thumbnail display
        try:
            pil_img = Image.open(str(image_path))
            pil_img.thumbnail((100, 75))
            self.ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 75))
            self.img_label = ctk.CTkLabel(self, image=self.ctk_img, text="")
            self.img_label.pack(padx=6, pady=(6, 2))
        except Exception:
            self.img_label = ctk.CTkLabel(self, text="🖼️ รูปภาพ", width=100, height=75)
            self.img_label.pack(padx=6, pady=(6, 2))

        # Bottom row with filename and delete button
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=6, pady=(0, 6))

        short_name = image_path.name
        if len(short_name) > 12:
            short_name = short_name[:10] + ".."
        name_lbl = ctk.CTkLabel(bottom_frame, text=short_name, font=("Sarabun", 10), text_color="#8b949e")
        name_lbl.pack(side="left")

        del_btn = ctk.CTkButton(
            bottom_frame,
            text="✕",
            width=22,
            height=22,
            fg_color="#f85149",
            hover_color="#da3633",
            font=("Sarabun", 11, "bold"),
            command=lambda: self.on_remove(self.image_path)
        )
        del_btn.pack(side="right")


class VideoListItem(ctk.CTkFrame):
    """Row item representing a selected CCTV video file."""

    def __init__(self, master, video_path: Path, on_remove, **kwargs):
        super().__init__(master, corner_radius=6, fg_color="#1e242c", **kwargs)
        self.video_path = video_path

        # File size calculation
        try:
            size_bytes = video_path.stat().st_size
            if size_bytes >= 1024 * 1024 * 1024:
                size_str = f"{size_bytes / (1024 ** 3):.2f} GB"
            else:
                size_str = f"{size_bytes / (1024 ** 2):.1f} MB"
        except Exception:
            size_str = "ไม่ทราบขนาด"

        # Icon + name
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=12, pady=8)

        name_lbl = ctk.CTkLabel(
            info_frame,
            text=f"📹 {video_path.name}",
            font=("Sarabun", 13, "bold"),
            anchor="w"
        )
        name_lbl.pack(fill="x")

        meta_lbl = ctk.CTkLabel(
            info_frame,
            text=f"ขนาด: {size_str}  •  {str(video_path)}",
            font=("Sarabun", 11),
            text_color="#8b949e",
            anchor="w"
        )
        meta_lbl.pack(fill="x")

        # Delete button
        del_btn = ctk.CTkButton(
            self,
            text="✕ ลบ",
            width=60,
            height=28,
            fg_color="#21262d",
            hover_color="#f85149",
            font=("Sarabun", 11),
            command=lambda: on_remove(self.video_path)
        )
        del_btn.pack(side="right", padx=12, pady=8)
