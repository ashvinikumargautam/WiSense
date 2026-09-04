import numpy as np
from scipy.stats import skew, kurtosis
from scipy.fft import fft, fftfreq


class FeatureExtractor:
    """Extract features from preprocessed CSI windows.

    Feature categories:
    - Time-domain: mean, std, variance, RMS, min, max, range, median, skewness, kurtosis, ZCR
    - Frequency-domain: dominant frequency, spectral energy, spectral entropy, spectral centroid
    - CSI-specific: subcarrier variance statistics, spatial variation
    """

    def extract(self, data: np.ndarray) -> np.ndarray:
        """Extract feature vector from a preprocessed CSI window.

        Args:
            data: shape (n_samples, n_subcarriers) - preprocessed CSI amplitudes

        Returns:
            features: 1D numpy array of extracted features
        """
        features = []

        # Overall mean amplitude time series
        mean_ts = np.mean(data, axis=1)  # shape: (n_samples,)

        # --- Time-domain features from mean time series ---
        features.append(np.mean(mean_ts))
        features.append(np.std(mean_ts))
        features.append(np.var(mean_ts))
        features.append(np.sqrt(np.mean(mean_ts ** 2)))  # RMS
        features.append(np.min(mean_ts))
        features.append(np.max(mean_ts))
        features.append(np.max(mean_ts) - np.min(mean_ts))  # range
        features.append(np.median(mean_ts))
        if len(mean_ts) > 2:
            features.append(skew(mean_ts))
            features.append(kurtosis(mean_ts))
        else:
            features.extend([0.0, 0.0])
        # Zero crossing rate
        zcr = np.sum(np.diff(np.sign(mean_ts)) != 0) / max(len(mean_ts) - 1, 1)
        features.append(zcr)

        # --- Frequency-domain features from mean time series ---
        n = len(mean_ts)
        if n > 1:
            sample_rate = 100.0  # default
            yf = np.abs(fft(mean_ts))[: n // 2]
            xf = fftfreq(n, 1.0 / sample_rate)[: n // 2]

            # Spectral energy
            spectral_energy = np.sum(yf ** 2) / n
            features.append(spectral_energy)

            # Dominant frequency
            if len(yf) > 0 and np.max(yf) > 0:
                dom_freq_idx = np.argmax(yf[1:]) + 1  # skip DC
                features.append(float(xf[dom_freq_idx]))
            else:
                features.append(0.0)

            # Spectral entropy
            psd = yf ** 2
            psd_sum = np.sum(psd)
            if psd_sum > 0:
                psd_norm = psd / psd_sum
                psd_norm = psd_norm[psd_norm > 0]
                spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm))
                features.append(spectral_entropy)
            else:
                features.append(0.0)

            # Spectral centroid
            if np.sum(yf) > 0:
                spectral_centroid = np.sum(xf * yf) / np.sum(yf)
                features.append(spectral_centroid)
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0, 0.0, 0.0])

        # --- Subcarrier-level statistics ---
        subcarrier_means = np.mean(data, axis=0)  # shape: (n_subcarriers,)
        subcarrier_stds = np.std(data, axis=0)    # shape: (n_subcarriers,)

        features.append(np.mean(subcarrier_means))
        features.append(np.std(subcarrier_means))
        features.append(np.mean(subcarrier_stds))
        features.append(np.std(subcarrier_stds))
        features.append(np.max(subcarrier_stds))
        features.append(np.min(subcarrier_stds))

        # Spatial variance (variance across subcarrier means)
        features.append(np.var(subcarrier_means))

        # Top-5 subcarrier variance sum (most variable subcarriers)
        top5_var = np.sum(np.sort(subcarrier_stds)[-5:])
        features.append(top5_var)

        # Ratio of temporal to spatial variation
        temporal_var = np.mean(np.var(data, axis=0))
        spatial_var = np.var(subcarrier_means)
        if spatial_var > 1e-10:
            features.append(temporal_var / spatial_var)
        else:
            features.append(0.0)

        # Per-subcarrier std statistics (more granular)
        features.append(np.percentile(subcarrier_stds, 25))
        features.append(np.percentile(subcarrier_stds, 75))
        features.append(np.percentile(subcarrier_stds, 50))  # median std

        # Subcarrier correlation structure
        if data.shape[1] > 1 and data.shape[0] > 1:
            corr_matrix = np.corrcoef(data.T)
            # Mean absolute correlation (excluding diagonal)
            n_sub = data.shape[1]
            if n_sub > 1:
                mask = ~np.eye(n_sub, dtype=bool)
                mean_abs_corr = np.mean(np.abs(corr_matrix[mask]))
                features.append(mean_abs_corr)
                # Max absolute correlation
                features.append(np.max(np.abs(corr_matrix[mask])))
            else:
                features.extend([0.0, 0.0])
        else:
            features.extend([0.0, 0.0])

        return np.array(features, dtype=np.float64)

    @property
    def feature_names(self) -> list[str]:
        return [
            "mean_amplitude", "std_amplitude", "var_amplitude", "rms_amplitude",
            "min_amplitude", "max_amplitude", "range_amplitude", "median_amplitude",
            "skewness", "kurtosis", "zero_crossing_rate",
            "spectral_energy", "dominant_frequency", "spectral_entropy", "spectral_centroid",
            "subcarrier_mean_of_means", "subcarrier_std_of_means",
            "subcarrier_mean_of_stds", "subcarrier_std_of_stds",
            "subcarrier_max_std", "subcarrier_min_std",
            "spatial_variance", "top5_subcarrier_variance", "temporal_spatial_ratio",
            "subcarrier_std_q25", "subcarrier_std_q75", "subcarrier_std_median",
            "mean_abs_correlation", "max_abs_correlation",
        ]

    @property
    def n_features(self) -> int:
        return len(self.feature_names)