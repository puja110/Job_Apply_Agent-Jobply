# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/job_discovery"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RapidAPI
    RAPIDAPI_KEY: Optional[str] = None
    
    # Rate Limiting (requests per minute)
    INDEED_RATE_LIMIT: int = 6
    LINKEDIN_RATE_LIMIT: int = 10
    GLASSDOOR_RATE_LIMIT: int = 10
    JSEARCH_RATE_LIMIT: int = 10
    
    # Scraping
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # seconds
    
    # User Agent rotation
    USER_AGENTS: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # AWS (for future use)
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()