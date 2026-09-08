import asyncio
import logging
import time
import json
import numpy as np
from typing import Optional
from app.data_sources.base import BaseDataSource, CSISample
from app.data_sources.simulator import SimulatorDataSource
from app.data_sources.esp32 import ESP32CSIDataSource
from app.signal_processing.preprocessing import SignalPreprocessor
from app.signal_processing.features import FeatureExtractor
from app.ml.inference import MLInference
from app.ml.ModelManager import ModelManager
from app.websocket.manager import ws_manager
from app.config import settings
from app.database.database import async_session
from app.database.models import Detection

logger = logging.getLogger(__name__)


class SignalBuffer:
    def __init__(self, window_size: int = 100, hop_size: int = 50, n_subcarriers: int = 64):
        self.window_size = window_size
        self.hop_size = hop_size
        self.n_subcarriers = n_subcarriers
        self.buffer = np.zeros((window_size, n_subcarriers), dtype=np.float64)
        self.sample_count = 0
        self._fill_index = 0
        self._filled = False

    def reset(self):
        self.buffer.fill(0)
        self.sample_count = 0
        self._fill_index = 0
        self._filled = False

    def add_sample(self, amplitudes: np.ndarray) -> Optional[np.ndarray]:
        self.buffer[self._fill_index] = amplitudes
        self._fill_index = (self._fill_index + 1) % self.window_size
        self.sample_count += 1
        if not self._filled and self._fill_index == 0:
            self._filled = True
        if self._filled and self.sample_count % self.hop_size == 0:
            return np.roll(self.buffer, -self._fill_index, axis=0).copy()
        return None

    @property
    def is_ready(self) -> bool:
        return self._filled


class SensingService:
    def __init__(self):
        self.data_source: Optional[BaseDataSource] = None
        self.signal_buffer: SignalBuffer = SignalBuffer(
            window_size=100,
            hop_size=50,
            n_subcarriers=settings.simulator_subcarriers,
        )
        self.preprocessor = SignalPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self.model_manager = ModelManager()
        self.inference = MLInference(self.model_manager)
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._collecting_training_data = False
        self._training_activity: Optional[str] = None
        self._training_samples: list = []
        self._current_user_id: Optional[int] = None
        self._stats = {
            "total_samples": 0,
            "total_predictions": 0,
            "start_time": None,
            "packets_per_second": 0,
        }
        self._recent_sample_times: list = []
        self._last_prediction: Optional[dict] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_data_source_type(self) -> str:
        if self.data_source:
            return self.data_source.data_source_type
        return "none"

    @property
    def current_device_id(self) -> str:
        if self.data_source:
            return self.data_source.device_id
        return ""

    @property
    def current_activity(self) -> str:
        if isinstance(self.data_source, SimulatorDataSource):
            return self.data_source.current_activity
        return "N/A"

    def set_user_id(self, user_id: int):
        self._current_user_id = user_id

    def set_simulator_activity(self, activity: str):
        if isinstance(self.data_source, SimulatorDataSource):
            self.data_source.set_activity(activity)

    def set_simulator_noise(self, level: float):
        if isinstance(self.data_source, SimulatorDataSource):
            self.data_source.set_noise_level(level)

    def set_simulator_intensity(self, intensity: float):
        if isinstance(self.data_source, SimulatorDataSource):
            self.data_source.set_movement_intensity(intensity)

    async def start(self, source_type: str = "simulation", device_id: Optional[str] = None):
        if self._running:
            await self.stop()
        if source_type == "simulation":
            self.data_source = SimulatorDataSource(device_id=device_id)
        elif source_type == "esp32":
            self.data_source = ESP32CSIDataSource(device_id=device_id or "ESP32-001")
        else:
            raise ValueError(f"Unknown data source type: {source_type}")
        if not self.inference.is_ready:
            self.inference.load_model()
        if self.model_manager.is_loaded:
            norm_params = self.model_manager.metadata.get("normalization_params", {})
            if norm_params:
                self.preprocessor.set_normalization_params(norm_params)
        await self.data_source.start()
        self._running = True
        self._stats["start_time"] = time.time()
        self._stats["total_samples"] = 0
        self._stats["total_predictions"] = 0
        self._recent_sample_times = []
        self._last_prediction = None
        self._task = asyncio.create_task(self._processing_loop())
        logger.info(f"Sensing service started with {source_type} source")

    async def stop(self):
        self._running = False
        if self.data_source:
            await self.data_source.stop()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.signal_buffer.reset()
        self.data_source = None
        logger.info("Sensing service stopped")

    async def _save_detection(self, device_id: str, prediction: str, confidence: float, rssi: float, data_source: str):
        """Persist detection to database without blocking the event loop."""
        if not self._current_user_id:
            return
        try:
            async with async_session() as session:
                detection = Detection(
                    user_id=self._current_user_id,
                    device_id=device_id,
                    prediction=prediction,
                    confidence=confidence,
                    rssi=rssi,
                    data_source=data_source,
                )
                session.add(detection)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to save detection: {e}")

    async def _processing_loop(self):
        sample_interval = 1.0 / settings.simulator_sample_rate
        save_counter = 0
        while self._running and self.data_source:
            try:
                sample = await self.data_source.get_sample()
                if sample is None:
                    await asyncio.sleep(sample_interval)
                    continue
                amplitudes = sample.get_amplitudes()
                self._stats["total_samples"] += 1
                now = time.time()
                self._recent_sample_times.append(now)
                self._recent_sample_times = [t for t in self._recent_sample_times if now - t < 1.0]
                self._stats["packets_per_second"] = len(self._recent_sample_times)

                window = self.signal_buffer.add_sample(amplitudes)

                if window is not None:
                    try:
                        processed = self.preprocessor.process(window)
                        features = self.feature_extractor.extract(processed)
                        result = self.inference.predict(window)
                        self._stats["total_predictions"] += 1
                        self._last_prediction = result

                        if self._collecting_training_data and self._training_activity:
                            self._training_samples.append({
                                "activity": self._training_activity,
                                "features": features.tolist(),
                            })

                        signal_subset = amplitudes[:min(len(amplitudes), 64)].tolist()

                        message = {
                            "type": "sensing_update",
                            "timestamp": sample.timestamp,
                            "device_id": sample.device_id,
                            "prediction": result["prediction"],
                            "confidence": result["confidence"],
                            "probabilities": result.get("probabilities", {}),
                            "signal": signal_subset,
                            "rssi": sample.rssi,
                            "data_source": self.data_source.data_source_type,
                            "model_ready": result.get("model_ready", False),
                            "stats": {
                                "total_samples": self._stats["total_samples"],
                                "total_predictions": self._stats["total_predictions"],
                                "packets_per_second": self._stats["packets_per_second"],
                            },
                        }
                        await ws_manager.broadcast(message)

                        # Save every 2nd prediction to DB (avoid flooding)
                        save_counter += 1
                        if save_counter % 2 == 0:
                            asyncio.create_task(self._save_detection(
                                device_id=sample.device_id,
                                prediction=result["prediction"],
                                confidence=result["confidence"],
                                rssi=sample.rssi,
                                data_source=self.data_source.data_source_type,
                            ))

                    except Exception as e:
                        logger.error(f"Processing error: {e}")

                await asyncio.sleep(sample_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Processing loop error: {e}")
                await asyncio.sleep(0.1)

    def start_training_collection(self, activity: str):
        self._collecting_training_data = True
        self._training_activity = activity
        self._training_samples = []

    def stop_training_collection(self) -> list:
        self._collecting_training_data = False
        samples = self._training_samples.copy()
        self._training_activity = None
        self._training_samples = []
        return samples

    def get_stats(self) -> dict:
        elapsed = 0
        if self._stats["start_time"]:
            elapsed = time.time() - self._stats["start_time"]
        return {
            **self._stats,
            "elapsed_seconds": round(elapsed, 1),
            "is_running": self._running,
            "data_source": self.current_data_source_type,
            "device_id": self.current_device_id,
            "simulator_activity": self.current_activity,
            "collecting_training": self._collecting_training_data,
            "training_activity": self._training_activity,
            "training_samples_collected": len(self._training_samples),
        }


sensing_service = SensingService()