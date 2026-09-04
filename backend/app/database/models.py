from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    device_name = Column(String(200), default="")
    device_type = Column(String(50), default="simulator")
    data_source = Column(String(50), default="simulation")
    token = Column(String(255), default="")
    status = Column(String(20), default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    data_source = Column(String(50), default="simulation")
    activity = Column(String(50), nullable=False)
    duration_seconds = Column(Float, default=0)
    samples_collected = Column(Integer, default=0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, server_default=func.now())


class TrainingSample(Base):
    __tablename__ = "training_samples"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    activity = Column(String(50), nullable=False)
    features_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False)
    prediction = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    rssi = Column(Float, nullable=True)
    data_source = Column(String(50), default="simulation")
    created_at = Column(DateTime, server_default=func.now(), index=True)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_path = Column(String(500), default="")
    scaler_path = Column(String(500), default="")
    metrics_json = Column(Text, default="{}")
    classes = Column(Text, default="[]")
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())