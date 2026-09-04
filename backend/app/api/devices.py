import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.database import get_session
from app.database.models import Device, User
from app.api.auth import get_current_user
from app.services.sensing_service import sensing_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/devices", tags=["devices"])


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    device_type: str
    data_source: str
    status: str
    last_seen: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceCreateRequest(BaseModel):
    device_id: str
    device_name: str = ""
    device_type: str = "esp32"
    data_source: str = "esp32"


@router.get("", response_model=list[DeviceResponse])
async def list_devices(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Device).where(Device.user_id == user.id))
    devices = result.scalars().all()
    # Ensure simulator device exists
    sim_result = await session.execute(
        select(Device).where(Device.user_id == user.id, Device.device_id == "SIMULATOR-001")
    )
    if not sim_result.scalar_one_or_none():
        sim_device = Device(
            user_id=user.id,
            device_id="SIMULATOR-001",
            device_name="WiSense Simulator",
            device_type="simulator",
            data_source="simulation",
            status="offline",
        )
        session.add(sim_device)
        await session.commit()
        await session.refresh(sim_device)
        devices.append(sim_device)
    return [DeviceResponse.model_validate(d) for d in devices]


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    req: DeviceCreateRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        select(Device).where(Device.user_id == user.id, Device.device_id == req.device_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device ID already exists")
    device = Device(
        user_id=user.id,
        device_id=req.device_id,
        device_name=req.device_name,
        device_type=req.device_type,
        data_source=req.data_source,
        status="offline",
    )
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Device).where(Device.user_id == user.id, Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if device.device_id == "SIMULATOR-001":
        raise HTTPException(status_code=400, detail="Cannot delete the simulator device")
    await session.delete(device)
    await session.commit()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Device).where(Device.user_id == user.id, Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    # Update status from sensing service
    if device.device_id == sensing_service.current_device_id:
        device.status = "online" if sensing_service.is_running else "offline"
        device.last_seen = datetime.utcnow() if sensing_service.is_running else device.last_seen
    return DeviceResponse.model_validate(device)