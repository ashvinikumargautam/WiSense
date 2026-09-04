import asyncio
import numpy as np
from typing import Optional, Callable
from app.data_sources.base import BaseDataSource, CSISample
from app.config import settings


class SimulatorDataSource(BaseDataSource):
    """Generates realistic CSI-like signals for different human activities.

    Signal characteristics by activity:
    - NO_MOVEMENT: Stable amplitudes, very low temporal variance, no periodic structure
    - MOVEMENT: Random amplitude fluctuations, medium variance, no clear periodicity
    - WALKING: Periodic amplitude modulation at ~1.5 Hz (step frequency),
      moderate variance, frequency-domain peak near 1-2 Hz
    """

    ACTIVITIES = ["NO_MOVEMENT", "MOVEMENT", "WALKING"]

    def __init__(
        self,
        device_id: Optional[str] = None,
        n_subcarriers: Optional[int] = None,
        sample_rate: Optional[int] = None,
        noise_level: Optional[float] = None,
        movement_intensity: Optional[float] = None,
    ):
        super().__init__(
            device_id=device_id or settings.simulator_device_id,
            n_subcarriers=n_subcarriers or settings.simulator_subcarriers,
        )
        self.sample_rate = sample_rate or settings.simulator_sample_rate
        self.noise_level = noise_level or settings.simulator_noise_level
        self.movement_intensity = movement_intensity or settings.simulator_movement_intensity
        self.current_activity: str = "NO_MOVEMENT"
        self._base_profile: Optional[np.ndarray] = None
        self._time_offset: float = 0.0
        self._phase_offsets: Optional[np.ndarray] = None
        self._subcarrier_gains: Optional[np.ndarray] = None
        self._on_activity_change: Optional[Callable] = None
        self._generate_base_profile()

    @property
    def data_source_type(self) -> str:
        return "simulation"

    def _generate_base_profile(self):
        """Generate a realistic base CSI amplitude profile across subcarriers."""
        np.random.seed(42)
        n = self.n_subcarriers
        # Real CSI has a characteristic frequency-selective fading pattern
        freq_indices = np.arange(n)
        # Simulate multipath with a few dominant paths
        base = np.ones(n) * 2.0
        # Add frequency-selective fading (sinusoidal pattern from multipath)
        base += 0.5 * np.sin(2 * np.pi * freq_indices / n * 3 + 0.5)
        base += 0.3 * np.sin(2 * np.pi * freq_indices / n * 7 + 1.2)
        base += 0.2 * np.cos(2 * np.pi * freq_indices / n * 11 + 2.1)
        # Ensure positive amplitudes
        base = np.abs(base) + 0.5
        self._base_profile = base
        # Random phase offsets per subcarrier (for complex signal)
        self._phase_offsets = np.random.uniform(0, 2 * np.pi, n)
        # Per-subcarrier gain variation (some subcarriers are inherently weaker)
        self._subcarrier_gains = np.random.uniform(0.7, 1.3, n)
        self._time_offset = 0.0

    def set_activity(self, activity: str):
        if activity in self.ACTIVITIES:
            self.current_activity = activity

    def set_noise_level(self, level: float):
        self.noise_level = max(0.0, min(1.0, level))

    def set_movement_intensity(self, intensity: float):
        self.movement_intensity = max(0.1, min(3.0, intensity))

    async def start(self):
        self._running = True
        self._time_offset = 0.0

    async def stop(self):
        self._running = False

    def _generate_no_movement(self, t: float) -> np.ndarray:
        """Very stable signal with only measurement noise."""
        noise = np.random.randn(self.n_subcarriers) * self.noise_level * 0.15
        # Tiny thermal drift
        drift = 0.01 * np.sin(2 * np.pi * 0.05 * t) * np.ones(self.n_subcarriers)
        amplitudes = self._base_profile * self._subcarrier_gains + noise + drift
        return amplitudes

    def _generate_movement(self, t: float) -> np.ndarray:
        """Random body movements - no clear periodicity, higher variance."""
        intensity = self.movement_intensity
        # Random fluctuation that changes slowly (body sway, arm movement)
        slow_random = 0.3 * intensity * np.sin(
            2 * np.pi * np.random.uniform(0.2, 0.8) * t
            + np.random.uniform(0, 2 * np.pi, self.n_subcarriers)
        )
        # Faster random component
        fast_random = 0.15 * intensity * np.sin(
            2 * np.pi * np.random.uniform(2.0, 5.0) * t
            + np.random.uniform(0, 2 * np.pi, self.n_subcarriers)
        )
        # Burst-like random fluctuations (sudden movements)
        burst = np.zeros(self.n_subcarriers)
        if np.random.random() < 0.05:
            burst = np.random.randn(self.n_subcarriers) * 0.4 * intensity
        # Noise floor
        noise = np.random.randn(self.n_subcarriers) * self.noise_level * 0.5
        amplitudes = self._base_profile * self._subcarrier_gains + slow_random + fast_random + burst + noise
        return amplitudes

    def _generate_walking(self, t: float) -> np.ndarray:
        """Walking - clear periodic pattern at step frequency (~1.5 Hz)."""
        intensity = self.movement_intensity
        step_freq = 1.5  # Hz - typical walking step frequency
        # Primary step modulation - sinusoidal at step frequency
        step_modulation = 0.4 * intensity * np.sin(
            2 * np.pi * step_freq * t + self._phase_offsets * 0.3
        )
        # Harmonic content (body bounce, arm swing at 2x step freq)
        harmonic = 0.15 * intensity * np.sin(
            2 * np.pi * step_freq * 2 * t + self._phase_offsets * 0.5 + 0.7
        )
        # Subcarrier-dependent phase (simulates different path lengths per subcarrier)
        spatial_variation = 0.1 * intensity * np.sin(
            2 * np.pi * step_freq * t
            + np.linspace(0, np.pi, self.n_subcarriers)
        )
        # Slight random gait variation (not perfectly periodic)
        gait_jitter = 0.05 * intensity * np.sin(
            2 * np.pi * (step_freq + np.random.uniform(-0.1, 0.1)) * t
        )
        # Noise
        noise = np.random.randn(self.n_subcarriers) * self.noise_level * 0.3
        amplitudes = (
            self._base_profile * self._subcarrier_gains
            + step_modulation
            + harmonic
            + spatial_variation
            + gait_jitter
            + noise
        )
        return amplitudes

    def _generate_csi(self, t: float) -> np.ndarray:
        """Generate CSI amplitudes based on current activity."""
        if self.current_activity == "NO_MOVEMENT":
            amplitudes = self._generate_no_movement(t)
        elif self.current_activity == "MOVEMENT":
            amplitudes = self._generate_movement(t)
        elif self.current_activity == "WALKING":
            amplitudes = self._generate_walking(t)
        else:
            amplitudes = self._generate_no_movement(t)
        return amplitudes

    async def get_sample(self) -> Optional[CSISample]:
        if not self._running:
            return None
        t = self._time_offset
        amplitudes = self._generate_csi(t)
        # Convert to complex CSI (add random phase)
        phases = self._phase_offsets + np.random.randn(self.n_subcarriers) * 0.1
        csi_complex = amplitudes * np.exp(1j * phases)
        # RSSI varies slightly with activity
        rssi_base = -45.0
        if self.current_activity == "MOVEMENT":
            rssi = rssi_base + np.random.uniform(-3, 3)
        elif self.current_activity == "WALKING":
            rssi = rssi_base + np.random.uniform(-5, 2)
        else:
            rssi = rssi_base + np.random.uniform(-1, 1)
        sample = self._make_sample(csi_complex, rssi=rssi)
        self._time_offset += 1.0 / self.sample_rate
        return sample

    def generate_dataset_samples(
        self,
        activity: str,
        n_windows: int = 200,
        window_size: int = 100,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate a batch of labeled CSI windows for training.

        Returns:
            windows: shape (n_windows, window_size, n_subcarriers)
            labels: shape (n_windows,)
        """
        saved_activity = self.current_activity
        self.current_activity = activity
        windows = np.zeros((n_windows, window_size, self.n_subcarriers))
        for w in range(n_windows):
            t_start = w * window_size / self.sample_rate
            for s in range(window_size):
                t = t_start + s / self.sample_rate
                windows[w, s] = self._generate_csi(t)
        labels = np.full(n_windows, activity)
        self.current_activity = saved_activity
        return windows, labels