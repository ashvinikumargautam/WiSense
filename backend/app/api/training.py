import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_session
from app.database.models import TrainingSession, TrainingSample, ModelVersion, User
from app.api.auth import get_current_user
from app.services.sensing_service import sensing_service
from app.ml.training import MLTrainer
from app.ml.ModelManager import ModelManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/training", tags=["training"])


class TrainingStartRequest(BaseModel):
    activity: str


class TrainRequest(BaseModel):
    data_source: str = "simulation"


class TrainingStatusResponse(BaseModel):
    collecting: bool
    activity: str | None
    samples_collected: int
    sessions: list[dict]


class TrainResponse(BaseModel):
    status: str
    results: dict | None = None


class ModelStatusResponse(BaseModel):
    model_exists: bool
    model_loaded: bool
    model_type: str
    classes: list[str]
    is_default: bool
    metrics: dict
    n_features: int
    n_training_samples: int


@router.post("/start")
async def start_collection(
    req: TrainingStartRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not sensing_service.is_running:
        raise HTTPException(status_code=400, detail="Start the simulator first")
    valid_activities = ["NO_MOVEMENT", "MOVEMENT", "WALKING"]
    if req.activity not in valid_activities:
        raise HTTPException(status_code=400, detail=f"Invalid activity. Must be one of: {valid_activities}")
    # Create session record
    ts = TrainingSession(
        user_id=user.id,
        data_source=sensing_service.current_data_source_type,
        activity=req.activity,
        status="collecting",
    )
    session.add(ts)
    await session.commit()
    await session.refresh(ts)
    # Start collecting
    sensing_service.start_training_collection(req.activity)
    # Set simulator to this activity
    sensing_service.set_simulator_activity(req.activity)
    return {"status": "collecting", "session_id": ts.id, "activity": req.activity}


@router.post("/stop")
async def stop_collection(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not sensing_service._collecting_training_data:
        raise HTTPException(status_code=400, detail="Not currently collecting training data")
    activity = sensing_service._training_activity
    samples = sensing_service.stop_training_collection()
    # Update session
    result = await session.execute(
        select(TrainingSession).where(
            TrainingSession.user_id == user.id,
            TrainingSession.activity == activity,
            TrainingSession.status == "collecting",
        )
    )
    ts = result.scalar_one_or_none()
    if ts:
        ts.status = "completed"
        ts.samples_collected = len(samples)
        await session.commit()
        # Store samples
        for s in samples:
            sample = TrainingSample(
                session_id=ts.id,
                activity=s["activity"],
                features_json=json.dumps(s["features"]),
            )
            session.add(sample)
        await session.commit()
    return {"status": "stopped", "activity": activity, "samples_collected": len(samples)}


@router.post("/train", response_model=TrainResponse)
async def train_model(
    req: TrainRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Load all training samples for this user
    result = await session.execute(
        select(TrainingSample).join(TrainingSession).where(TrainingSession.user_id == user.id)
    )
    samples = result.scalars().all()
    if not samples:
        raise HTTPException(status_code=400, detail="No training samples collected yet")
    # Parse features and labels
    X_list = []
    y_list = []
    for s in samples:
        features = json.loads(s.features_json)
        X_list.append(features)
        y_list.append(s.activity)
    import numpy as np
    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list)
    # Check minimum samples per class
    from collections import Counter
    counts = Counter(y)
    for cls, cnt in counts.items():
        if cnt < 10:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough samples for class '{cls}': {cnt} (minimum 10)",
            )
    # Train
    model_manager = ModelManager()
    trainer = MLTrainer(model_manager)
    results = trainer.train(X, y)
    # Save model version record
    mv = ModelVersion(
        user_id=user.id,
        model_path=model_manager.model_path,
        scaler_path=model_manager.scaler_path,
        metrics_json=json.dumps(results.get("models", {})),
        classes=json.dumps(results.get("classes", [])),
        is_active=True,
    )
    session.add(mv)
    # Deactivate previous models
    prev = await session.execute(
        select(ModelVersion).where(ModelVersion.user_id == user.id, ModelVersion.is_active == True)
    )
    for prev_mv in prev.scalars().all():
        prev_mv.is_active = False
    await session.commit()
    # Reload inference model
    sensing_service.inference.load_model()
    if model_manager.is_loaded:
        norm_params = model_manager.metadata.get("normalization_params", {})
        if norm_params:
            sensing_service.preprocessor.set_normalization_params(norm_params)
    return TrainResponse(status="trained", results=results)


@router.post("/generate-default", response_model=TrainResponse)
async def generate_default_model(user: User = Depends(get_current_user)):
    model_manager = ModelManager()
    trainer = MLTrainer(model_manager)
    results = trainer.generate_default_model()
    return TrainResponse(status="trained", results=results)


@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(TrainingSession).where(TrainingSession.user_id == user.id)
    )
    sessions = []
    for ts in result.scalars().all():
        sessions.append({
            "id": ts.id,
            "activity": ts.activity,
            "samples_collected": ts.samples_collected,
            "status": ts.status,
            "created_at": ts.created_at.isoformat() if ts.created_at else None,
        })
    return TrainingStatusResponse(
        collecting=sensing_service._collecting_training_data,
        activity=sensing_service._training_activity,
        samples_collected=len(sensing_service._training_samples),
        sessions=sessions,
    )


@router.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(user: User = Depends(get_current_user)):
    mm = ModelManager()
    loaded = mm.load()
    return ModelStatusResponse(
        model_exists=mm.model_exists(),
        model_loaded=loaded,
        model_type=mm.metadata.get("model_type", ""),
        classes=mm.metadata.get("classes", []),
        is_default=mm.metadata.get("is_default", False),
        metrics=mm.metadata.get("metrics", {}),
        n_features=mm.metadata.get("n_features", 0),
        n_training_samples=mm.metadata.get("n_training_samples", 0),
    )