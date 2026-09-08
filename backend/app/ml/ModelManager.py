import os
import json
import logging
import joblib
import numpy as np
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages ML model and scaler persistence."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        scaler_path: Optional[str] = None,
    ):
        self.model_path = model_path or settings.model_path
        self.scaler_path = scaler_path or settings.scaler_path
        self.model: Optional[Any] = None
        self.scaler: Optional[Any] = None
        self.metadata: dict = {
            "classes": [],
            "feature_names": [],
            "n_features": 0,
            "model_type": "",
            "metrics": {},
            "normalization_params": {},
            "is_default": False,
        }

    def save(self, model, scaler, metadata: dict):
        """Save model, scaler, and metadata to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(model, self.model_path)
        joblib.dump(scaler, self.scaler_path)
        self.metadata.update(metadata)
        meta_path = self.model_path.replace(".pkl", "_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        self.model = model
        self.scaler = scaler
        logger.info(f"Model saved to {self.model_path}")

    def load(self) -> bool:
        """Load model, scaler, and metadata from disk."""
        if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
            logger.warning("Model files not found")
            return False
        try:
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
            meta_path = self.model_path.replace(".pkl", "_metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r") as f:
                    self.metadata = json.load(f)
            logger.info(f"Model loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def model_exists(self) -> bool:
        return os.path.exists(self.model_path) and os.path.exists(self.scaler_path)

    def get_classes(self) -> list[str]:
        return self.metadata.get("classes", [])

    @property
    def is_loaded(self) -> bool:
        return self.model is not None and self.scaler is not None