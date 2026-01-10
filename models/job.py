# models/job.py
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import hashlib
import json

class LocationType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"

class EmploymentType(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class RawJob(BaseModel):
    """Raw job data as scraped from platform."""
    platform: str
    external_id: Optional[str] = None
    url: HttpUrl
    raw_data: dict
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def content_hash(self) -> str:
        """Generate content hash for deduplication."""
        # Normalize data for consistent hashing
        normalized = {
            "title": self.raw_data.get("title", "").lower().strip(),
            "company": self.raw_data.get("company", "").lower().strip(),
            "location": self.raw_data.get("location", "").lower().strip(),
            "description": self.raw_data.get("description", "")[:500],  # First 500 chars
        }
        content = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

class Job(BaseModel):
    """Normalized job data."""
    id: Optional[str] = None
    raw_job_id: Optional[str] = None
    
    # Core fields
    title: str
    company: str
    location: Optional[str] = None
    location_type: Optional[LocationType] = None
    
    # Job details
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    
    # Compensation
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    salary_period: Optional[str] = None
    
    # Metadata
    employment_type: Optional[EmploymentType] = None
    experience_level: Optional[ExperienceLevel] = None
    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    
    # Platform info
    platform: str
    platform_url: HttpUrl
    apply_url: Optional[HttpUrl] = None
    
    # Derived fields
    skills: List[str] = []
    keywords: List[str] = []
    
    # Processing
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"
    
    @validator('title', 'company', 'description')
    def clean_text(cls, v):
        """Remove extra whitespace and normalize."""
        if v:
            return ' '.join(v.split())
        return v
    
    @validator('location_type', pre=True)
    def parse_location_type(cls, v):
        """Infer location type from description."""
        if not v:
            return None
        v_lower = str(v).lower()
        if 'remote' in v_lower:
            return LocationType.REMOTE
        elif 'hybrid' in v_lower:
            return LocationType.HYBRID
        else:
            return LocationType.ONSITE