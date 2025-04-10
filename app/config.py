import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Lynk AI"
    MONGO_URI: str = os.getenv("MONGODB_URI")
    
    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_CC: str = os.getenv("SMTP_CC")
    SMTP_USERNAME: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASS")
    SMTP_FROM: str = os.getenv("SMTP_FROM")
    
    class Config:
        env_file = ".env"

settings = Settings()
