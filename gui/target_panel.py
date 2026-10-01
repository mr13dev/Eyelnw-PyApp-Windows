"""
Target vehicle input panel for Eyelnw GUI.
Allows uploading multi-angle reference photos and specifying target vehicle attributes.
"""

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

from gui.widgets import ImageThumbnail


class TargetPanel(ctk.CTkFrame):
    """Panel for specifying target vehicle photos and metadata."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=12, fg_color="#161b22", **kwargs)

        self.selected_images: list[Path] = []

        self._build_ui()

    def _build_ui(self):
        # Section Header
        header = ctk.CTkLabel(
            self,
            text="🚗 ขั้นตอนที่ 1: กำหนดรูปรถเป้าหมายที่ตามหา",
            font=("Sarabun", 16, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        sub = ctk.CTkLabel(
            self,
            text="แนบรูปรถหลายๆ มุม (แนะนำ 3-10 รูป เช่น ด้านหน้า ด้านข้าง ด้านหลัง มุมสูงคล้าย CCTV) เพื่อความแม่นยำสูงสุด",
            font=("Sarabun", 12),
            text_color="#8b949e",
            anchor="w"
        )
        sub.pack(fill="x", padx=16, pady=(0, 12))

        # Photo Action Bar
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=16, pady=(0, 8))

        self.btn_add_img = ctk.CTkButton(
            action_bar,
            text="➕ เพิ่มรูปรถ (เลือกหลายรูปได้)",
            command=self._on_add_images,
            font=("Sarabun", 13, "bold"),
            fg_color="#2f81f7",
            hover_color="#1a73e8",
            height=34
        )
        self.btn_add_img.pack(side="left", padx=(0, 10))

        self.btn_clear_imgs = ctk.CTkButton(
            action_bar,
            text="ล้างรูปทั้งหมด",
            command=self._on_clear_images,
            font=("Sarabun", 12),
            fg_color="#21262d",
            hover_color="#30363d",
            height=34
        )
        self.btn_clear_imgs.pack(side="left")

        self.lbl_count = ctk.CTkLabel(
            action_bar,
            text="ยังไม่มีรูปที่แนบ",
            font=("Sarabun", 12),
            text_color="#8b949e"
        )
        self.lbl_count.pack(side="right")

        # Scrollable Thumbnail Grid
        self.scroll_thumbs = ctk.CTkScrollableFrame(
            self,
            orientation="horizontal",
            height=135,
            fg_color="#0d1117",
            corner_radius=8
        )
        self.scroll_thumbs.pack(fill="x", padx=16, pady=(0, 16))

        # Metadata Form Section
        meta_label = ctk.CTkLabel(
            self,
            text="📝 ข้อมูลเพิ่มเติม (ไม่บังคับ แต่ช่วยให้ระบบแม่นยำขึ้น)",
            font=("Sarabun", 14, "bold"),
            anchor="w"
        )
        meta_label.pack(fill="x", padx=16, pady=(0, 8))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=16, pady=(0, 16))

        # Row 1: Plate & Color
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", pady=4)

        lbl_plate = ctk.CTkLabel(row1, text="ป้ายทะเบียน:", width=80, anchor="w", font=("Sarabun", 12))
        lbl_plate.pack(side="left")
        self.entry_plate = ctk.CTkEntry(
            row1,
            placeholder_text="เช่น กข 1234 หรือ 1กก 9999",
            width=200,
            font=("Sarabun", 12)
        )
        self.entry_plate.pack(side="left", padx=(0, 24))

        lbl_color = ctk.CTkLabel(row1, text="สีรถ:", width=50, anchor="w", font=("Sarabun", 12))
        lbl_color.pack(side="left")
        self.combo_color = ctk.CTkComboBox(
            row1,
            values=["ทั้งหมด (ตามรูป)", "ขาว", "ดำ", "เงิน / เทา", "บรอนซ์ทอง", "แดง", "น้ำเงิน / ฟ้า", "เหลือง", "เขียว", "ส้ม / น้ำตาล"],
            width=180,
            font=("Sarabun", 12)
        )
        self.combo_color.set("ทั้งหมด (ตามรูป)")
        self.combo_color.pack(side="left")

        # Row 2: Brand & Model
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", pady=4)

        lbl_brand = ctk.CTkLabel(row2, text="ยี่ห้อรถ:", width=80, anchor="w", font=("Sarabun", 12))
        lbl_brand.pack(side="left")
        self.entry_brand = ctk.CTkEntry(
            row2,
            placeholder_text="เช่น Toyota, Honda, Isuzu",
            width=200,
            font=("Sarabun", 12)
        )
        self.entry_brand.pack(side="left", padx=(0, 24))

        lbl_model = ctk.CTkLabel(row2, text="รุ่นรถ:", width=50, anchor="w", font=("Sarabun", 12))
        lbl_model.pack(side="left")
        self.entry_model = ctk.CTkEntry(
            row2,
            placeholder_text="เช่น Yaris, Civic, D-Max",
            width=180,
            font=("Sarabun", 12)
        )
        self.entry_model.pack(side="left")

    def _on_add_images(self):
        files = filedialog.askopenfilenames(
            title="เลือกรูปรถเป้าหมาย (เลือกได้หลายรูป)",
            filetypes=[
                ("Image Files", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
                ("All Files", "*.*")
            ]
        )
        if not files:
            return

        for f in files:
            p = Path(f)
            if p not in self.selected_images:
                self.selected_images.append(p)

        self._refresh_thumbnails()

    def _on_remove_image(self, path: Path):
        if path in self.selected_images:
            self.selected_images.remove(path)
        self._refresh_thumbnails()

    def _on_clear_images(self):
        self.selected_images.clear()
        self._refresh_thumbnails()

    def _refresh_thumbnails(self):
        for widget in self.scroll_thumbs.winfo_children():
            widget.destroy()

        for path in self.selected_images:
            card = ImageThumbnail(self.scroll_thumbs, image_path=path, on_remove=self._on_remove_image)
            card.pack(side="left", padx=6, pady=4)

        n = len(self.selected_images)
        self.lbl_count.configure(
            text=f"แนบรูปแล้ว {n} รูป" if n > 0 else "ยังไม่มีรูปที่แนบ"
        )

    def get_data(self) -> dict:
        """Returns collected target data."""
        color_val = self.combo_color.get()
        if "ทั้งหมด" in color_val:
            color_val = ""

        return {
            "image_paths": list(self.selected_images),
            "plate_number": self.entry_plate.get().strip(),
            "car_color": color_val,
            "car_brand": self.entry_brand.get().strip(),
            "car_model": self.entry_model.get().strip()
        }
