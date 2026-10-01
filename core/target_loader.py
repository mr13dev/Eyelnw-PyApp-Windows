"""
Target vehicle loader and profile builder for Eyelnw.
Handles multi-angle reference photos and creates consolidated feature profiles.
"""

from pathlib import Path
import cv2
import numpy as np
from core.color_analyzer import ColorAnalyzer
from core.feature_extractor import FeatureExtractor
from utils.logger import logger


class TargetProfile:
    """Consolidated representation of target vehicle features across multiple angles."""

    def __init__(
        self,
        plate_number: str = "",
        car_color: str = "",
        car_brand: str = "",
        car_model: str = ""
    ):
        self.plate_number = plate_number.strip().upper()
        self.car_color = car_color.strip()
        self.car_brand = car_brand.strip()
        self.car_model = car_model.strip()

        self.image_paths: list[Path] = []
        self.images: list[np.ndarray] = []
        self.color_histograms: list[np.ndarray] = []
        self.avg_histogram: np.ndarray | None = None
        self.descriptors_list: list[np.ndarray] = []
        self.embeddings: list[np.ndarray] = []
        self.avg_embedding: np.ndarray | None = None
        self.dominant_color: str = ""

    @property
    def is_valid(self) -> bool:
        """Returns True if at least one reference photo has been loaded."""
        return len(self.images) > 0


class TargetLoader:
    """Loads reference vehicle images and computes combined target profile."""

    def __init__(self, color_analyzer: ColorAnalyzer | None = None, feature_extractor: FeatureExtractor | None = None):
        self.color_analyzer = color_analyzer or ColorAnalyzer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        # Initialize ORB detector
        self.orb = cv2.ORB_create(nfeatures=1000)

    def build_profile(
        self,
        image_paths: list[str | Path],
        plate_number: str = "",
        car_color: str = "",
        car_brand: str = "",
        car_model: str = ""
    ) -> TargetProfile:
        """
        Loads all provided target vehicle images and extracts:
        - HSV Color Histograms & Average Histogram
        - ORB feature descriptors
        - Deep feature embeddings & Average Embedding
        - Dominant color detection
        """
        profile = TargetProfile(
            plate_number=plate_number,
            car_color=car_color,
            car_brand=car_brand,
            car_model=car_model
        )

        loaded_hists = []
        loaded_embeddings = []

        for p in image_paths:
            path_obj = Path(p)
            if not path_obj.exists():
                logger.warning(f"Target image not found: {p}")
                continue

            # Read image using cv2 with unicode-safe handling for Windows paths
            img_bytes = np.fromfile(str(path_obj), dtype=np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
            if img is None:
                logger.warning(f"Could not decode target image: {p}")
                continue

            profile.image_paths.append(path_obj)
            profile.images.append(img)

            # 1. Color histogram
            hist = self.color_analyzer.compute_histogram(img)
            profile.color_histograms.append(hist)
            loaded_hists.append(hist)

            # 2. ORB Descriptors
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, des = self.orb.detectAndCompute(gray, None)
            if des is not None:
                profile.descriptors_list.append(des)

            # 3. Deep Feature Embedding
            emb = self.feature_extractor.extract(img)
            profile.embeddings.append(emb)
            loaded_embeddings.append(emb)

        if not profile.images:
            raise ValueError("No valid reference images could be loaded.")

        # Compute average color histogram
        if loaded_hists:
            profile.avg_histogram = np.mean(loaded_hists, axis=0).astype(np.float32)

        # Compute average deep embedding
        if loaded_embeddings:
            avg_emb = np.mean(loaded_embeddings, axis=0).astype(np.float32)
            norm = np.linalg.norm(avg_emb)
            if norm > 1e-6:
                avg_emb = avg_emb / norm
            profile.avg_embedding = avg_emb

        # Determine dominant color from first image or avg
        profile.dominant_color = self.color_analyzer.get_dominant_color(profile.images[0])

        logger.info(
            f"TargetProfile successfully created with {len(profile.images)} images. "
            f"Dominant color: {profile.dominant_color}"
        )
        return profile
