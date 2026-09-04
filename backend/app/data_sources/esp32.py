import asyncio
import json
import logging
from typing import Optional
from app.data_sources.base import BaseDataSource, CSISample
import numpy as np

logger = logging.getLogger(__name__)


class ESP32CSIDataSource(BaseDataSource):
    """Receives real CSI data from an ESP32 device over WebSocket.

    The ESP32 connects to WS /ws/device/{device_id} and sends CSI packets.
    This data source reads from a queue that the device WebSocket endpoint writes to.
    """

    def __init__(self, device_id: str, n_subcarriers: int = 64):
        super().__init__(device_id=device_id, n_subcarriers=n_subcarriers)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._timeout = 2.0

    @property
    def data_source_type(self) -> str:
        return "esp32"

    async def start(self):
        self._running = True
        self._sequence = 0
        logger.info(f"ESP32 data source started for device {self.device_id}")

    async def stop(self):
        self._running = False
        logger.info(f"ESP32 data source stopped for device {self.device_id}")

    def receive_esp32_data(self, raw_data: dict):
        """Called by the device WebSocket endpoint when ESP32 sends data.

        Expected format:
        {
            "timestamp": 1720000000,
            "sequence": 123,
            "rssi": -45,
            "channel": 6,
            "csi": [[re, im], [re, im], ...]
        }
        """
        if self._queue.full():
            # Drop oldest sample if queue is full
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        self._queue.put_nowait(raw_data)

    async def get_sample(self) -> Optional[CSISample]:
        if not self._running:
            return None
        try:
            raw = await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        except asyncio.TimeoutError:
            return None
        try:
            csi_list = raw.get("csi", [])
            n = min(len(csi_list), self.n_subcarriers)
            csi_complex = np.zeros(self.n_subcarriers, dtype=complex)
            for i in range(n):
                if isinstance(csi_list[i], list) and len(csi_list[i]) >= 2:
                    csi_complex[i] = complex(csi_list[i][0], csi_list[i][1])
                elif isinstance(csi_list[i], (int, float)):
                    csi_complex[i] = complex(csi_list[i], 0)
            return CSISample(
                device_id=self.device_id,
                timestamp=raw.get("timestamp", 0),
                sequence=raw.get("sequence", self._sequence + 1),
                rssi=raw.get("rssi", -50.0),
                channel=raw.get("channel", 6),
                csi=csi_complex,
            )
        except Exception as e:
            logger.error(f"Error parsing ESP32 CSI data: {e}")
            return None