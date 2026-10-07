import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TimeSense AI"
    TAGLINE: str = "Not just what happened — what happened, when, in what order, and for how long."
    VERSION: str = "2.0.0"
    
    # Video & CV Processing
    PROCESS_FPS: int = 5
    YOLO_MODEL: str = "yolov8n.pt"
    TRACKER_TYPE: str = "bytetrack.yaml"
    CONFIDENCE_THRESHOLD: float = 0.35
    STATIONARY_DISPLACEMENT_THRESH: float = 30.0
    UNATTENDED_TIME_THRESH: float = 4.0 # seconds
    LOITER_TIME_THRESH: float = 8.0 # seconds

    # Paths
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "uploads")
    PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
    DATABASE_URL: str = f"sqlite:///{os.path.join(DATA_DIR, 'database', 'timesense.db')}"

    # Vision-Language Model / LLM (Optional)
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_PROVIDER: str = "gemini" # 'gemini', 'openai', 'ollama', or 'none'

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.DATA_DIR, "database"), exist_ok=True)
