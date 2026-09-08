from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./wisense.db"
    jwt_secret: str = "change-this-to-a-random-string-at-least-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    model_path: str = "./models/movement_model.pkl"
    scaler_path: str = "./models/scaler.pkl"
    cors_origins: str = "http://localhost:5173"
    data_source: str = "simulation"
    simulator_device_id: str = "SIMULATOR-001"
    simulator_sample_rate: int = 100
    simulator_subcarriers: int = 64
    simulator_noise_level: float = 0.05
    simulator_movement_intensity: float = 1.0
    train_auto_generate: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
