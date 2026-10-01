"""
Persistent settings manager using JSON file storage.
บันทึกค่าตั้งค่าของ GUI ลง settings.json เพื่อเก็บไว้ใช้ข้ามเซสชัน
"""

import json
from pathlib import Path
from utils.logger import logger

# ไฟล์ settings จะถูกบันทึกที่ root ของโปรเจกต์
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "settings.json"

# ค่าเริ่มต้นทั้งหมด
DEFAULT_SETTINGS = {
    "model_choice": "YOLOv8n (เร็วมาก / แนะนำ)",
    "match_threshold": 0.60,
    "scan_speed": "สมดุล (2 ครั้ง/วินาที)",
    "enable_clip_cutting": True,
    "target_color": "ทั้งหมด (ตามรูป)",
}


class SettingsManager:
    """Reads and writes user settings to a JSON file."""

    def __init__(self, path: Path = SETTINGS_FILE):
        self.path = path
        self._data: dict = {}
        self.load()

    def load(self):
        """โหลด settings จากไฟล์ ถ้าไม่มีไฟล์หรือไฟล์เสียหายให้ใช้ค่าเริ่มต้น"""
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                if not isinstance(self._data, dict):
                    self._data = dict(DEFAULT_SETTINGS)
                logger.info(f"Settings loaded from {self.path}")
            except Exception as e:
                logger.warning(f"Failed to load settings, using defaults: {e}")
                self._data = dict(DEFAULT_SETTINGS)
        else:
            self._data = dict(DEFAULT_SETTINGS)

    def save(self):
        """บันทึก settings ลงไฟล์"""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.info("Settings saved.")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default=None):
        """อ่านค่า โดย fallback เป็นค่า DEFAULT_SETTINGS ถ้าไม่มี"""
        return self._data.get(key, DEFAULT_SETTINGS.get(key, default))

    def set(self, key: str, value):
        """ตั้งค่าและบันทึกอัตโนมัติ"""
        self._data[key] = value
        self.save()

    def reset_all(self):
        """รีเซ็ตทุกค่ากลับสู่ค่าเริ่มต้น"""
        self._data = dict(DEFAULT_SETTINGS)
        self.save()
        logger.info("All settings have been reset to defaults.")

    def to_dict(self) -> dict:
        """ส่งคืน copy ของ settings ทั้งหมด"""
        merged = dict(DEFAULT_SETTINGS)
        merged.update(self._data)
        return merged
