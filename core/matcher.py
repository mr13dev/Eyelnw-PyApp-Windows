"""
Multi-criteria vehicle matcher combining color, keypoints, deep embeddings, and OCR.
"""

from dataclasses import dataclass
import cv2
import numpy as np
from core.color_analyzer import ColorAnalyzer
from core.feature_extractor import FeatureExtractor
from core.ocr_reader import PlateReader
from core.target_loader import TargetProfile


@dataclass
class MatchResult:
    """Detailed score breakdown and matching status."""
    combined_score: float
    color_score: float
    feature_score: float
    deep_score: float
    ocr_score: float
    detected_plate: str | None
    detected_color: str
    is_match: bool


class VehicleMatcher:
    """Matches candidate vehicle crops against a TargetProfile."""

    def __init__(
        self,
        target: TargetProfile,
        color_analyzer: ColorAnalyzer | None = None,
        feature_extractor: FeatureExtractor | None = None,
        plate_reader: PlateReader | None = None,
        weights: dict[str, float] | None = None
    ):
        self.target = target
        self.color_analyzer = color_analyzer or ColorAnalyzer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.plate_reader = plate_reader or PlateReader()

        # Configurable weights (Blueprint specifies 25% color, 25% feature, 40% deep, 10% ocr)
        self.weights = weights or {
            "color": 0.25,
            "feature": 0.25,
            "deep": 0.40,
            "ocr": 0.10
        }

        # Initialize ORB & Brute Force Matcher for Hamming distance
        self.orb = cv2.ORB_create(nfeatures=800)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def _match_color(self, candidate_image: np.ndarray) -> tuple[float, str]:
        """Calculates color similarity against target histograms and detects color name."""
        cand_hist = self.color_analyzer.compute_histogram(candidate_image)
        cand_color = self.color_analyzer.get_dominant_color(candidate_image)

        if not self.target.color_histograms:
            return 0.5, cand_color

        scores = [
            self.color_analyzer.compare_colors(cand_hist, ref_hist)
            for ref_hist in self.target.color_histograms
        ]
        # Return best match or average
        best_score = max(scores) if scores else 0.0
        avg_score = float(np.mean(scores)) if scores else 0.0
        # Blend best and avg
        score = 0.6 * best_score + 0.4 * avg_score
        return score, cand_color

    def _match_orb_features(self, candidate_image: np.ndarray) -> float:
        """Calculates ORB keypoint descriptor matching score using Lowe's ratio test."""
        if not self.target.descriptors_list:
            return 0.5

        gray = cv2.cvtColor(candidate_image, cv2.COLOR_BGR2GRAY)
        _, cand_des = self.orb.detectAndCompute(gray, None)

        if cand_des is None or len(cand_des) < 10:
            return 0.1

        ref_match_ratios = []
        for ref_des in self.target.descriptors_list:
            if ref_des is None or len(ref_des) < 10:
                continue

            try:
                matches = self.bf.knnMatch(cand_des, ref_des, k=2)
                # Apply Lowe's ratio test
                good_matches = [
                    m for m, n in matches
                    if len((m, n)) == 2 and m.distance < 0.75 * n.distance
                ]
                ratio = len(good_matches) / max(15, min(len(cand_des), len(ref_des)))
                ref_match_ratios.append(min(1.0, ratio * 2.5))  # Scaled for realistic match ratio
            except Exception:
                continue

        if not ref_match_ratios:
            return 0.2
        return float(max(ref_match_ratios))

    def _match_deep_features(self, candidate_image: np.ndarray) -> float:
        """Calculates deep ResNet50 cosine similarity."""
        if not self.target.embeddings:
            return 0.5

        cand_emb = self.feature_extractor.extract(candidate_image)

        similarities = [
            self.feature_extractor.cosine_similarity(cand_emb, ref_emb)
            for ref_emb in self.target.embeddings
        ]
        best_sim = max(similarities) if similarities else 0.0

        if self.target.avg_embedding is not None:
            avg_sim = self.feature_extractor.cosine_similarity(cand_emb, self.target.avg_embedding)
            return float(0.7 * best_sim + 0.3 * avg_sim)
        return float(best_sim)

    def _match_ocr(self, candidate_image: np.ndarray) -> tuple[float, str | None]:
        """Runs OCR and compares plate numbers."""
        detected_plate = self.plate_reader.read_plate(candidate_image)
        if not self.target.plate_number:
            # If target plate is not provided by user, OCR score is neutral (0.5)
            return 0.5, detected_plate

        if not detected_plate:
            # Plate could not be read
            return 0.3, None

        similarity = self.plate_reader.match_plate(detected_plate, self.target.plate_number)
        return similarity, detected_plate

    def match(self, candidate_image: np.ndarray, threshold: float = 0.60) -> MatchResult:
        """
        Executes complete multi-modal comparison pipeline on candidate vehicle crop.
        """
        if candidate_image is None or candidate_image.size == 0:
            return MatchResult(0.0, 0.0, 0.0, 0.0, 0.0, None, "", False)

        color_score, detected_color = self._match_color(candidate_image)
        feature_score = self._match_orb_features(candidate_image)
        deep_score = self._match_deep_features(candidate_image)
        ocr_score, detected_plate = self._match_ocr(candidate_image)

        # Dynamic weight adjustment if target plate was not provided
        w_color = self.weights["color"]
        w_feat = self.weights["feature"]
        w_deep = self.weights["deep"]
        w_ocr = self.weights["ocr"]

        if not self.target.plate_number:
            # Redistribute OCR weight across deep and color
            total_remaining = w_color + w_feat + w_deep
            w_color = w_color / total_remaining
            w_feat = w_feat / total_remaining
            w_deep = w_deep / total_remaining
            w_ocr = 0.0

        combined = (
            w_color * color_score +
            w_feat * feature_score +
            w_deep * deep_score +
            w_ocr * ocr_score
        )

        # Special bonus: If OCR is a strong match, boost confidence
        if self.target.plate_number and ocr_score >= 0.85:
            combined = max(combined, 0.92)

        combined = max(0.0, min(1.0, float(combined)))
        is_match = combined >= threshold

        return MatchResult(
            combined_score=combined,
            color_score=color_score,
            feature_score=feature_score,
            deep_score=deep_score,
            ocr_score=ocr_score,
            detected_plate=detected_plate,
            detected_color=detected_color,
            is_match=is_match
        )
