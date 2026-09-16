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


# --- Pydantic Models ---

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


# NEW: Model to accept data from ESP32
class SignalData(BaseModel):
    device_id: str  # The ESP32 must send this ID
    value: float    # The sensor reading


# --- Routes ---

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
        
    # Update status from sensing service if applicable
    if device.device_id == sensing_service.current_device_id:
        device.status = "online" if sensing_service.is_running else "offline"
        device.last_seen = datetime.utcnow() if sensing_service.is_running else device.last_seen
        
    return DeviceResponse.model_validate(device)


# NEW: Endpoint to receive data from ESP32
@router.post("/signal")
async def receive_signal(
    data: SignalData,
    session: AsyncSession = Depends(get_session)
):
    """
    Receives signal data from an ESP32 device.
    Updates the device status to 'online' and logs the reading.
    """
    # 1. Find the device by the ID sent by the ESP32
    result = await session.execute(
        select(Device).where(Device.device_id == data.device_id)
    )
    device = result.scalar_one_or_none()

    # 2. Check if device exists
    if not device:
        logger.warning(f"Received signal from unknown device: {data.device_id}")
        raise HTTPException(status_code=404, detail="Device not registered")

    # 3. Update device state (it's online now!)
    device.status = "online"
    device.last_seen = datetime.utcnow()
    
    # 4. (Optional) Process the data
    # You can pass 'data.value' to your sensing_service or ML inference model here.
    # Example: await sensing_service.process_raw_signal(device.id, data.value)
    
    logger.info(f"Received signal from {device.device_id}: {data.value}")

    # 5. Save changes
    await session.commit()
    
    return {"status": "success", "message": "Data received"}