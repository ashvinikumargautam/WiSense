import numpy as np
import logging
from typing import Optional
from app.ModelManager import ModelManager
from app.signal_processing.preprocessing import SignalPreprocessor
from app.signal_processing.features import FeatureExtractor

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.45


class MLInference:
    """Real-time ML inference for movement classification."""

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.preprocessor = SignalPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self._loaded = False

    def load_model(self) -> bool:
        """Load model from disk."""
        success = self.model_manager.load()
        if success:
            norm_params = self.model_manager.metadata.get("normalization_params", {})
            if norm_params:
                self.preprocessor.set_normalization_params(norm_params)
            self._loaded = True
            logger.info("Inference model loaded successfully")
        else:
            self._loaded = False
            logger.warning("No model available for inference")
        return success

    @property
    def is_ready(self) -> bool:
        return self._loaded and self.model_manager.is_loaded

    def predict(self, csi_window: np.ndarray) -> dict:
        """Predict movement class from a CSI window.

        Args:
            csi_window: shape (n_samples, n_subcarriers) - raw or complex CSI

        Returns:
            dict with prediction, confidence, class_probabilities
        """
        if not self.is_ready:
            return {
                "prediction": "UNKNOWN",
                "confidence": 0.0,
                "probabilities": {},
                "model_ready": False,
            }

        try:
            # Preprocess
            processed = self.preprocessor.process(csi_window)

            # Extract features
            features = self.feature_extractor.extract(processed).reshape(1, -1)

            # Scale
            features_scaled = self.model_manager.scaler.transform(features)

            # Predict
            model = self.model_manager.model
            prediction = model.predict(features_scaled)[0]
            classes = self.model_manager.get_classes()

            # Get probabilities
            probabilities = {}
            confidence = 0.0
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(features_scaled)[0]
                for i, cls in enumerate(model.classes_):
                    probabilities[cls] = round(float(probs[i]), 4)
                confidence = float(np.max(probs))
            else:
                confidence = 1.0
                for cls in classes:
                    probabilities[cls] = 1.0 if cls == prediction else 0.0

            # Apply confidence threshold
            if confidence < CONFIDENCE_THRESHOLD:
                prediction = "UNKNOWN"

            return {
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "probabilities": probabilities,
                "model_ready": True,
            }
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return {
                "prediction": "UNKNOWN",
                "confidence": 0.0,
                "probabilities": {},
                "model_ready": False,
                "error": str(e),
            }