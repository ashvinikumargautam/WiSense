import numpy as np
from typing import Optional
from app.signal_processing.filtering import hampel_filter, butter_lowpass_filter, moving_average
from app.config import settings


class SignalPreprocessor:
    """Full CSI signal preprocessing pipeline.

    Pipeline:
    1. Amplitude extraction from complex CSI
    2. Outlier removal (Hampel filter)
    3. Low-pass Butterworth filter
    4. Moving average smoothing
    5. Standardization (per-subcarrier z-score)
    """

    def __init__(
        self,
        sample_rate: int = None,
        cutoff_freq: float = 10.0,
        hampel_window: int = 7,
        hampel_sigmas: float = 3.0,
        ma_window: int = 5,
    ):
        self.sample_rate = sample_rate or settings.simulator_sample_rate
        self.cutoff_freq = cutoff_freq
        self.hampel_window = hampel_window
        self.hampel_sigmas = hampel_sigmas
        self.ma_window = ma_window
        self._means: Optional[np.ndarray] = None
        self._stds: Optional[np.ndarray] = None
        self._fitted: bool = False

    def fit(self, data: np.ndarray):
        """Compute normalization statistics from training data."""
        self._means = np.mean(data, axis=0)
        self._stds = np.std(data, axis=0)
        self._stds[self._stds < 1e-10] = 1e-10
        self._fitted = True
        return self

    def get_normalization_params(self) -> dict:
        if not self._fitted:
            return {}
        return {
            "means": self._means.tolist(),
            "stds": self._stds.tolist(),
        }

    def set_normalization_params(self, params: dict):
        if params.get("means") and params.get("stds"):
            self._means = np.array(params["means"])
            self._stds = np.array(params["stds"])
            self._fitted = True

    def process(self, raw_csi: np.ndarray) -> np.ndarray:
        """Process a CSI window.

        Args:
            raw_csi: shape (n_samples, n_subcarriers) - complex or real amplitudes

        Returns:
            processed: shape (n_samples, n_subcarriers) - cleaned, normalized amplitudes
        """
        # Step 1: Amplitude extraction (handle complex input)
        if np.iscomplexobj(raw_csi):
            data = np.abs(raw_csi)
        else:
            data = raw_csi.copy().astype(np.float64)

        # Validate
        if data.ndim != 2 or data.shape[0] < 3 or data.shape[1] < 3:
            raise ValueError(f"Invalid CSI shape: {data.shape}")

        # Step 2: Outlier removal
        data = hampel_filter(data, window_size=self.hampel_window, n_sigmas=self.hampel_sigmas)

        # Step 3: Low-pass filter
        data = butter_lowpass_filter(data, cutoff=self.cutoff_freq, sample_rate=self.sample_rate)

        # Step 4: Moving average
        data = moving_average(data, window_size=self.ma_window)

        # Step 5: Normalization
        if self._fitted and self._means is not None:
            data = (data - self._means) / self._stds
        else:
            # Online normalization using window statistics
            w_mean = np.mean(data, axis=0)
            w_std = np.std(data, axis=0)
            w_std[w_std < 1e-10] = 1e-10
            data = (data - w_mean) / w_std

        return data