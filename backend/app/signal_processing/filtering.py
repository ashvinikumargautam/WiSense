import numpy as np
from scipy.signal import butter, filtfilt, medfilt


def butter_lowpass_filter(
    data: np.ndarray,
    cutoff: float = 10.0,
    sample_rate: float = 100.0,
    order: int = 4,
) -> np.ndarray:
    """Apply Butterworth low-pass filter to each subcarrier."""
    nyquist = 0.5 * sample_rate
    normal_cutoff = min(cutoff / nyquist, 0.99)
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    if data.ndim == 1:
        return filtfilt(b, a, data)
    filtered = np.zeros_like(data)
    for i in range(data.shape[1]):
        filtered[:, i] = filtfilt(b, a, data[:, i])
    return filtered


def hampel_filter(
    data: np.ndarray,
    window_size: int = 7,
    n_sigmas: float = 3.0,
) -> np.ndarray:
    """Remove outliers using Hampel filter.

    Replaces values more than n_sigmas MADs from the median
    with the median of the window.
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)
        squeeze = True
    else:
        squeeze = False
    result = data.copy()
    half_w = window_size // 2
    for col in range(data.shape[1]):
        series = data[:, col]
        for i in range(len(series)):
            start = max(0, i - half_w)
            end = min(len(series), i + half_w + 1)
            window = series[start:end]
            median = np.median(window)
            mad = np.median(np.abs(window - median))
            if mad == 0:
                mad = 1e-10
            if abs(series[i] - median) > n_sigmas * mad:
                result[i, col] = median
    if squeeze:
        return result.squeeze()
    return result


def moving_average(data: np.ndarray, window_size: int = 5) -> np.ndarray:
    """Apply moving average smoothing."""
    if data.ndim == 1:
        kernel = np.ones(window_size) / window_size
        return np.convolve(data, kernel, mode="same")
    result = np.zeros_like(data)
    kernel = np.ones(window_size) / window_size
    for i in range(data.shape[1]):
        result[:, i] = np.convolve(data[:, i], kernel, mode="same")
    return result