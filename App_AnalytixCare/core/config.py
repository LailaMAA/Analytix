from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """
    Application Configuration
    """
    APP_NAME: str = "Manufacturing Predictive Intelligent System"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Paths (Attributes)
    DATA_PATH: str = "data/processed/dataset_pretraite.csv"
    MODEL_DIR: str = "models/"
    MLFLOW_TRACKING_URI: str = "mlruns"
    
    # Database
    DATABASE_URL: str = "sqlite:///./Companyx_database.db"
    
    # Secrets
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
