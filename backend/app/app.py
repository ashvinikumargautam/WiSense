import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.database import init_db
from app.api.auth import verify_token_query
from app.api import auth, devices, sensing, training, history
from app.websocket.manager import ws_manager
from app.services.sensing_service import sensing_service
from wisense.backend.app.ml.ModelManager import ModelManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting WiSense backend...")
    os.makedirs("models", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/datasets", exist_ok=True)
    await init_db()
    if settings.train_auto_generate and not ModelManager().model_exists():
        logger.info("No model found. Generating default model from synthetic data...")
        try:
            from app.ml.training import MLTrainer
            trainer = MLTrainer()
            trainer.generate_default_model()
            logger.info("Default model generated successfully.")
        except Exception as e:
            logger.error(f"Failed to generate default model: {e}")
    sensing_service.inference.load_model()
    if sensing_service.model_manager.is_loaded:
        norm_params = sensing_service.model_manager.metadata.get("normalization_params", {})
        if norm_params:
            sensing_service.preprocessor.set_normalization_params(norm_params)
    yield
    if sensing_service.is_running:
        await sensing_service.stop()
    logger.info("WiSense backend stopped.")


app = FastAPI(
    title="WiSense",
    description="Wi-Fi Human Movement Sensing Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(sensing.router)
app.include_router(training.router)
app.include_router(history.router)


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": "WiSense",
        "version": "1.0.0",
        "model_loaded": sensing_service.inference.is_ready,
        "sensing_running": sensing_service.is_running,
    }


@app.websocket("/ws/sensing")
async def websocket_sensing(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        verify_token_query(token)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token")
        return
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "WiSense WebSocket connected",
            "model_ready": sensing_service.inference.is_ready,
        })
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/device/{device_id}")
async def websocket_device(websocket: WebSocket, device_id: str, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        verify_token_query(token)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token")
        return
    await websocket.accept()
    logger.info(f"ESP32 device {device_id} connected")
    from app.data_sources.esp32 import ESP32CSIDataSource
    esp32_source = None
    if (sensing_service.is_running
            and isinstance(sensing_service.data_source, ESP32CSIDataSource)
            and sensing_service.data_source.device_id == device_id):
        esp32_source = sensing_service.data_source
    try:
        while True:
            data = await websocket.receive_json()
            if esp32_source:
                esp32_source.receive_esp32_data(data)
    except WebSocketDisconnect:
        logger.info(f"ESP32 device {device_id} disconnected")
    except Exception as e:
        logger.error(f"Device WebSocket error: {e}")