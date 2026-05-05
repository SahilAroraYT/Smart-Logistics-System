import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Smart Logistics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "sqlite:///./smart_logistics.db",
    )

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-use-os-urandom"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Demo mode (bypasses auth for local testing)
    DEMO_MODE: bool = False

    # OSRM
    OSRM_BASE_URL: str = "http://router.project-osrm.org"

    # Model paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    MODEL_PATH: str = str(PROJECT_ROOT / "models" / "delivery_failure_model_v2.pkl")
    ENCODER_PATH: str = str(PROJECT_ROOT / "models" / "label_encoders_v2.pkl")
    DATA_PATH: str = str(PROJECT_ROOT / "data" / "logistics_dataset_v3.csv")

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
