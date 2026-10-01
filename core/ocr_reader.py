"""
OCR Plate Reader for reading Thai & English license plates from detected vehicles.
"""

from difflib import SequenceMatcher
import re
import cv2
import numpy as np
from utils.logger import logger


class PlateReader:
    """Reads license plate characters and computes string similarity."""

    def __init__(self, languages: list[str] | None = None, gpu: bool = True):
        self.languages = languages or ["th", "en"]
        self.gpu = gpu
        self.reader = None
        self._disabled = False

    def _lazy_init(self):
        """Initializes easyocr reader on first request."""
        if self.reader is not None or self._disabled:
            return

        try:
            import easyocr
            logger.info("Initializing EasyOCR for license plate reading...")
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu, verbose=False)
            logger.info("EasyOCR initialized.")
        except Exception as e:
            logger.warning(f"EasyOCR could not be initialized (OCR will be skipped): {e}")
            self._disabled = True

    def read_plate(self, car_image: np.ndarray) -> str | None:
        """
        Attempts to read license plate text from a cropped vehicle image.
        Focuses predominantly on the lower half/middle section of the car.
        """
        if car_image is None or car_image.size == 0:
            return None

        self._lazy_init()
        if self._disabled or self.reader is None:
            return None

        try:
            h, w = car_image.shape[:2]
            # Plate is typically in lower 60% of vehicle
            plate_roi = car_image[int(h * 0.40):h, :]
            if plate_roi.size == 0:
                plate_roi = car_image

            # Preprocessing: convert to grayscale and contrast enhancement
            gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            results = self.reader.readtext(enhanced, detail=0, paragraph=False)
            if not results:
                return None

            # Clean and combine alphanumeric and Thai characters
            cleaned_tokens = []
            for text in results:
                # Remove punctuation and noisy symbols
                cleaned = re.sub(r'[^\w\u0E00-\u0E7F]', '', text)
                if len(cleaned) >= 2:
                    cleaned_tokens.append(cleaned)

            if cleaned_tokens:
                return " ".join(cleaned_tokens)
            return None
        except Exception as e:
            logger.debug(f"Plate reading exception: {e}")
            return None

    @staticmethod
    def match_plate(detected_plate: str | None, target_plate: str | None) -> float:
        """
        Calculates similarity ratio between target plate and detected plate string.
        Returns a float between 0.0 and 1.0.
        """
        if not detected_plate or not target_plate:
            return 0.0

        # Normalize strings: lowercase and remove spaces/dashes
        clean_det = re.sub(r'[\s\-_\.]', '', detected_plate).lower()
        clean_target = re.sub(r'[\s\-_\.]', '', target_plate).lower()

        if not clean_det or not clean_target:
            return 0.0

        if clean_target in clean_det or clean_det in clean_target:
            return 1.0

        ratio = SequenceMatcher(None, clean_det, clean_target).ratio()
        return float(ratio)
