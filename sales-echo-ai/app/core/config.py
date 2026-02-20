"""
Core Configuration Settings
Loads environment variables and provides app-wide configuration.
"""

from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional


# Load environment variables from both project root `.env`
# and `docs/.env` (where API keys may be stored).
BASE_DIR = Path(__file__).resolve().parents[2]

# Load docs/.env first (fallback), then root .env to override if both exist
load_dotenv(BASE_DIR / "docs" / ".env")
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str
    
    # AI Providers
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # CRM Integration
    hubspot_access_token: Optional[str] = None
    
    # Application
    environment: str = "development"
    debug: bool = True
    
    # Optional: Redis
    redis_url: Optional[str] = None
    
    # Optional: AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: Optional[str] = None
    
    # Development Only: Standardized org_id for testing (DEV_ONLY_WARNING)
    # MUST be removed before production - replace with Auth middleware
    # This ensures consistent org_id across upload and fetch operations during development
    dev_org_id: Optional[str] = None
    stable_org_id: Optional[str] = None  # Deprecated: Use dev_org_id instead
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
