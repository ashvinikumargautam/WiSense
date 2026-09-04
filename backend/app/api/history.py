import logging
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_session
from app.database.models import Detection, User
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/history", tags=["history"])


class DetectionResponse(BaseModel):
    id: int
    device_id: str
    prediction: str
    confidence: float
    rssi: float | None
    data_source: str
    created_at: str

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    detections: list[DetectionResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=HistoryResponse)
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    prediction: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    query = select(Detection).where(Detection.user_id == user.id)
    if prediction:
        query = query.where(Detection.prediction == prediction)

    count_subq = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_subq)).scalar() or 0

    query = (
        query
        .order_by(desc(Detection.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(query)
    dets = result.scalars().all()

    return HistoryResponse(
        detections=[
            DetectionResponse(
                id=d.id,
                device_id=d.device_id,
                prediction=d.prediction,
                confidence=d.confidence,
                rssi=d.rssi,
                data_source=d.data_source,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
            for d in dets
        ],
        total=total,
        page=page,
        page_size=page_size,
    )