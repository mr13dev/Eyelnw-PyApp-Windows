"""
Color analysis and HSV histogram comparison for vehicle matching.
"""

import cv2
import numpy as np


class ColorAnalyzer:
    """Analyzes and compares vehicle color profiles using HSV histograms."""

    def __init__(self, h_bins: int = 30, s_bins: int = 32):
        self.h_bins = h_bins
        self.s_bins = s_bins

    def compute_histogram(self, image: np.ndarray) -> np.ndarray:
        """
        Computes a normalized 2D HSV histogram (Hue & Saturation).
        Ignores extreme dark/light borders when possible.
        """
        if image is None or image.size == 0:
            return np.zeros((self.h_bins, self.s_bins), dtype=np.float32)

        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Focus slightly towards center of vehicle to avoid background contamination
        h, w = image.shape[:2]
        pad_y = max(1, int(h * 0.1))
        pad_x = max(1, int(w * 0.1))
        center_crop = hsv[pad_y:h - pad_y, pad_x:w - pad_x]
        if center_crop.size == 0:
            center_crop = hsv

        hist = cv2.calcHist(
            [center_crop],
            channels=[0, 1],
            mask=None,
            histSize=[self.h_bins, self.s_bins],
            ranges=[0, 180, 0, 256]
        )
        # Normalize histogram
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist.astype(np.float32)

    def compare_colors(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """
        Compares two HSV histograms using Correlation.
        Returns a similarity score between 0.0 and 1.0.
        """
        if hist1 is None or hist2 is None or hist1.size == 0 or hist2.size == 0:
            return 0.0

        # Correlation metric: range [-1, 1], normalize to [0, 1]
        raw_corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        normalized_score = max(0.0, min(1.0, (raw_corr + 1.0) / 2.0))
        return float(normalized_score)

    def get_dominant_color(self, image: np.ndarray) -> str:
        """
        Determines the dominant vehicle color (Thai & English description).
        Uses median/mean HSV values in the vehicle body region.
        """
        if image is None or image.size == 0:
            return "ไม่ระบุ (Unknown)"

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, w = image.shape[:2]
        pad_y = max(1, int(h * 0.15))
        pad_x = max(1, int(w * 0.15))
        roi = hsv[pad_y:h - pad_y, pad_x:w - pad_x]
        if roi.size == 0:
            roi = hsv

        h_mean = np.median(roi[:, :, 0])
        s_mean = np.median(roi[:, :, 1])
        v_mean = np.median(roi[:, :, 2])

        # Classification heuristics
        if v_mean < 45:
            return "ดำ (Black)"
        if s_mean < 40 and v_mean > 190:
            return "ขาว (White)"
        if s_mean < 45:
            return "เงิน/เทา (Silver/Grey)"

        # Hue based classification (0-180 in OpenCV)
        if h_mean < 10 or h_mean >= 170:
            return "แดง (Red)"
        elif 10 <= h_mean < 25:
            return "ส้ม/น้ำตาล (Orange/Brown)"
        elif 25 <= h_mean < 35:
            return "เหลือง (Yellow)"
        elif 35 <= h_mean < 85:
            return "เขียว (Green)"
        elif 85 <= h_mean < 130:
            return "น้ำเงิน/ฟ้า (Blue)"
        elif 130 <= h_mean < 160:
            return "ม่วง (Purple)"
        else:
            return "ชมพู (Pink)"
