import numpy as np
import logging
from typing import Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)
from wisense.backend.app.ml.ModelManager import ModelManager
from app.signal_processing.preprocessing import SignalPreprocessor
from app.signal_processing.features import FeatureExtractor

logger = logging.getLogger(__name__)


class MLTrainer:
    """Train and evaluate movement classification models."""

    def __init__(self, model_manager: Optional[ModelManager] = None):
        self.model_manager = model_manager or ModelManager()
        self.preprocessor = SignalPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self.results: dict = {}

    def extract_features_from_windows(
        self, windows: np.ndarray, fit_preprocessor: bool = True
    ) -> np.ndarray:
        """Extract features from raw CSI windows.

        Args:
            windows: shape (n_windows, n_samples, n_subcarriers)
            fit_preprocessor: if True, fit the preprocessor on this data

        Returns:
            features: shape (n_windows, n_features)
        """
        if fit_preprocessor:
            # Fit preprocessor on all data
            all_samples = windows.reshape(-1, windows.shape[2])
            self.preprocessor.fit(all_samples)

        n_windows = windows.shape[0]
        features = np.zeros((n_windows, self.feature_extractor.n_features))
        for i in range(n_windows):
            processed = self.preprocessor.process(windows[i])
            features[i] = self.feature_extractor.extract(processed)
        return features

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.2,
    ) -> dict:
        """Train multiple classifiers and select the best one.

        Args:
            X: feature matrix (n_samples, n_features)
            y: labels (n_samples,)

        Returns:
            Training results including metrics and confusion matrix
        """
        from sklearn.model_selection import train_test_split

        classes = sorted(list(set(y)))
        logger.info(f"Training with {len(X)} samples, classes: {classes}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=42
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models = {
            "RandomForest": RandomForestClassifier(
                n_estimators=100, max_depth=15, random_state=42, n_jobs=-1
            ),
            # ✅ FIX: Removed multi_class="multinomial" for scikit-learn compatibility
            "LogisticRegression": LogisticRegression(
                max_iter=1000, random_state=42
            ),
            "SVM": SVC(kernel="rbf", C=10, gamma="scale", random_state=42, probability=True),
        }

        best_model = None
        best_name = ""
        best_f1 = 0.0
        all_results = {}

        for name, model in models.items():
            logger.info(f"Training {name}...")
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
            rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
            f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
            cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()

            # Cross-validation
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            cv_results = cross_validate(
                model, X_train_scaled, y_train, cv=cv,
                scoring=["accuracy", "f1_weighted"],
            )

            all_results[name] = {
                "accuracy": round(float(acc), 4),
                "precision": round(float(prec), 4),
                "recall": round(float(rec), 4),
                "f1_score": round(float(f1), 4),
                "confusion_matrix": cm,
                "cv_accuracy_mean": round(float(cv_results["test_accuracy"].mean()), 4),
                "cv_accuracy_std": round(float(cv_results["test_accuracy"].std()), 4),
                "cv_f1_mean": round(float(cv_results["test_f1_weighted"].mean()), 4),
            }

            logger.info(f"  {name}: acc={acc:.4f}, f1={f1:.4f}")

            if f1 > best_f1:
                best_f1 = f1
                best_model = model
                best_name = name

        # Retrain best model on full dataset
        logger.info(f"Best model: {best_name} (F1={best_f1:.4f})")
        X_full_scaled = scaler.fit_transform(X)
        best_model.fit(X_full_scaled, y)

        # Save
        self.model_manager.save(
            model=best_model,
            scaler=scaler,
            metadata={
                "classes": classes,
                "feature_names": self.feature_extractor.feature_names,
                "n_features": self.feature_extractor.n_features,
                "model_type": best_name,
                "metrics": all_results[best_name],
                "all_results": all_results,
                "normalization_params": self.preprocessor.get_normalization_params(),
                "n_training_samples": len(X),
                "is_default": False,
            },
        )

        self.results = {
            "best_model": best_name,
            "best_f1": round(float(best_f1), 4),
            "classes": classes,
            "n_samples": len(X),
            "n_features": X.shape[1],
            "models": all_results,
            "confusion_matrix_labels": classes,
        }

        return self.results

    def generate_default_model(self) -> dict:
        """Generate a default model using synthetic data from the simulator."""
        from app.data_sources.simulator import SimulatorDataSource

        logger.info("Generating default model from synthetic data...")
        simulator = SimulatorDataSource()
        all_windows = []
        all_labels = []

        for activity in SimulatorDataSource.ACTIVITIES:
            windows, labels = simulator.generate_dataset_samples(
                activity=activity, n_windows=200, window_size=100
            )
            all_windows.append(windows)
            all_labels.append(labels)
            logger.info(f"  Generated {len(windows)} windows for {activity}")

        X_windows = np.concatenate(all_windows, axis=0)
        y_labels = np.concatenate(all_labels, axis=0)

        features = self.extract_features_from_windows(X_windows, fit_preprocessor=True)
        results = self.train(features, y_labels)

        # Mark as default
        self.model_manager.metadata["is_default"] = True
        meta_path = self.model_manager.model_path.replace(".pkl", "_metadata.json")
        import json
        with open(meta_path, "w") as f:
            json.dump(self.model_manager.metadata, f, indent=2)

        return results