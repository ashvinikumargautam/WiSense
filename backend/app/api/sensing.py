import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.auth import get_current_user
from app.database.models import User
from app.services.sensing_service import sensing_service
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sensing", tags=["sensing"])


class StatusResponse(BaseModel):
    is_running: bool
    data_source: str
    device_id: str
    model_ready: bool
    stats: dict
    simulator_activity: str = ""
    collecting_training: bool = False
    training_activity: str | None = None
    training_samples_collected: int = 0


class CurrentResponse(BaseModel):
    prediction: str
    confidence: float
    data_source: str
    device_id: str
    model_ready: bool


class SimulationStartRequest(BaseModel):
    activity: str = "NO_MOVEMENT"
    noise_level: float | None = None
    movement_intensity: float | None = None


class SimulationActivityRequest(BaseModel):
    activity: str


class SimulationNoiseRequest(BaseModel):
    noise_level: float


class SimulationIntensityRequest(BaseModel):
    intensity: float


@router.get("/status", response_model=StatusResponse)
async def get_status(user: User = Depends(get_current_user)):
    stats = sensing_service.get_stats()
    return StatusResponse(
        is_running=stats["is_running"],
        data_source=stats["data_source"],
        device_id=stats["device_id"],
        model_ready=sensing_service.inference.is_ready,
        stats=stats,
        simulator_activity=stats.get("simulator_activity", ""),
        collecting_training=stats.get("collecting_training", False),
        training_activity=stats.get("training_activity"),
        training_samples_collected=stats.get("training_samples_collected", 0),
    )


@router.get("/current", response_model=CurrentResponse)
async def get_current(user: User = Depends(get_current_user)):
    if not sensing_service.is_running:
        return CurrentResponse(
            prediction="UNKNOWN", confidence=0.0,
            data_source="none", device_id="", model_ready=sensing_service.inference.is_ready,
        )
    pred = sensing_service._last_prediction
    return CurrentResponse(
        prediction=pred["prediction"] if pred else "UNKNOWN",
        confidence=pred["confidence"] if pred else 0.0,
        data_source=sensing_service.current_data_source_type,
        device_id=sensing_service.current_device_id,
        model_ready=sensing_service.inference.is_ready,
    )


@router.post("/simulation/start")
async def start_simulation(req: SimulationStartRequest, user: User = Depends(get_current_user)):
    if sensing_service.is_running:
        await sensing_service.stop()
    sensing_service.set_user_id(user.id)
    await sensing_service.start(source_type="simulation")
    if req.activity:
        sensing_service.set_simulator_activity(req.activity)
    if req.noise_level is not None:
        sensing_service.set_simulator_noise(req.noise_level)
    if req.movement_intensity is not None:
        sensing_service.set_simulator_intensity(req.movement_intensity)
    return {"status": "started", "data_source": "simulation"}


@router.post("/simulation/stop")
async def stop_simulation(user: User = Depends(get_current_user)):
    await sensing_service.stop()
    return {"status": "stopped"}


@router.post("/simulation/activity")
async def set_activity(req: SimulationActivityRequest, user: User = Depends(get_current_user)):
    if not sensing_service.is_running:
        raise HTTPException(status_code=400, detail="Simulation is not running")
    sensing_service.set_simulator_activity(req.activity)
    return {"activity": req.activity}


@router.post("/simulation/noise")
async def set_noise(req: SimulationNoiseRequest, user: User = Depends(get_current_user)):
    sensing_service.set_simulator_noise(req.noise_level)
    return {"noise_level": req.noise_level}


@router.post("/simulation/intensity")
async def set_intensity(req: SimulationIntensityRequest, user: User = Depends(get_current_user)):
    sensing_service.set_simulator_intensity(req.intensity)
    return {"intensity": req.intensity}