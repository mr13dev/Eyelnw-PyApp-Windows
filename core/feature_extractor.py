"""
Deep feature extractor using pre-trained convolutional neural networks (ResNet50).
"""

import numpy as np
import cv2
import torch
import torchvision.transforms as T
import torchvision.models as models
from utils.logger import logger


class FeatureExtractor:
    """
    Extracts deep visual embeddings from vehicle images using ResNet50.
    Calculates cosine similarity between embedding vectors.
    """

    def __init__(self, device: str | None = None):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = None
        self._transform = None
        logger.info(f"FeatureExtractor configured for device: {self.device}")

    def _lazy_init(self):
        """Initializes model and transforms lazily upon first use."""
        if self.model is not None:
            return

        try:
            logger.info("Loading pre-trained ResNet50 for deep feature extraction...")
            # Load ResNet50 weights
            weights = models.ResNet50_Weights.DEFAULT
            base_model = models.resnet50(weights=weights)

            # Strip the final classification layer, keep the 2048-dim pooling output
            self.model = torch.nn.Sequential(*(list(base_model.children())[:-1]))
            self.model.to(self.device)
            self.model.eval()

            # Transformation pipeline for standard ResNet inputs
            self._transform = T.Compose([
                T.ToPILImage(),
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            logger.info("ResNet50 model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ResNet50 model: {e}")
            raise

    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Extracts a 2048-dimensional normalized embedding vector from a BGR image.
        Returns a 1D float32 numpy array with unit norm.
        """
        if image is None or image.size == 0:
            return np.zeros(2048, dtype=np.float32)

        self._lazy_init()

        try:
            # OpenCV BGR to RGB
            rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            input_tensor = self._transform(rgb_img).unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = self.model(input_tensor)
                features = features.squeeze().cpu().numpy().astype(np.float32)

            # Normalize to unit length (L2 norm)
            norm = np.linalg.norm(features)
            if norm > 1e-6:
                features = features / norm
            return features
        except Exception as e:
            logger.warning(f"Error during deep feature extraction: {e}")
            return np.zeros(2048, dtype=np.float32)

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Computes cosine similarity between two 1D vectors in range [0.0, 1.0].
        """
        if vec1 is None or vec2 is None or vec1.size == 0 or vec2.size == 0:
            return 0.0

        v1 = vec1.flatten()
        v2 = vec2.flatten()
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0

        dot = np.dot(v1, v2) / (norm1 * norm2)
        # Cosine similarity is [-1, 1], normalize to [0, 1]
        sim = max(0.0, min(1.0, float((dot + 1.0) / 2.0)))
        return sim
