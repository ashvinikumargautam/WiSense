from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import time


@dataclass
class CSISample:
    device_id: str
    timestamp: float
    sequence: int
    rssi: float
    channel: int
    csi: np.ndarray  # shape: (n_subcarriers,) complex amplitudes

    def get_amplitudes(self) -> np.ndarray:
        return np.abs(self.csi)

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "rssi": self.rssi,
            "channel": self.channel,
            "csi_amplitude": self.get_amplitudes().tolist(),
        }


class BaseDataSource(ABC):
    def __init__(self, device_id: str, n_subcarriers: int = 64):
        self.device_id = device_id
        self.n_subcarriers = n_subcarriers
        self._running: bool = False
        self._sequence: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def data_source_type(self) -> str:
        return "unknown"

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def get_sample(self) -> Optional[CSISample]:
        pass

    def _make_sample(self, csi_complex: np.ndarray, rssi: float = -45.0, channel: int = 6) -> CSISample:
        self._sequence += 1
        return CSISample(
            device_id=self.device_id,
            timestamp=time.time(),
            sequence=self._sequence,
            rssi=rssi,
            channel=channel,
            csi=csi_complex,
        )