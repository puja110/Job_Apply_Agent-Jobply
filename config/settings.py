# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database - Individual fields
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "jobply"
    
    # Database - URL format (for compatibility)
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JSearch API (RapidAPI)
    JSEARCH_API_KEY: str = ""
    JSEARCH_API_HOST: str = "jsearch.p.rapidapi.com"
    
    # RapidAPI (legacy)
    # RAPIDAPI_KEY: Optional[str] = None
    
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
    
    def get_database_url(self) -> str:
        """Generate DATABASE_URL from individual components if not set"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        password_part = f":{self.DB_PASSWORD}" if self.DB_PASSWORD else ""
        return f"postgresql://{self.DB_USER}{password_part}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env

settings = Settings()