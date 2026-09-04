import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)
from typing import Optional


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: Optional[list] = None,
) -> dict:
    """Compute evaluation metrics for a model."""
    if classes is None:
        classes = sorted(list(set(y_true) | set(y_pred)))

    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=classes).tolist(),
        "classification_report": classification_report(y_true, y_pred, labels=classes, zero_division=0),
        "classes": classes,
    }