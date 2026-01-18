# models/job.py
from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from uuid import UUID
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
    url: Union[HttpUrl, str]  # Allow string URLs
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
    id: Optional[Union[str, UUID]] = None  # Accept both string and UUID
    raw_job_id: Optional[Union[str, UUID]] = None
    
    # Core fields
    title: str
    company: str
    location: Optional[str] = None
    location_type: Optional[Union[LocationType, str]] = None  # Accept string too
    
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
    employment_type: Optional[Union[EmploymentType, str]] = None  # Accept string too
    experience_level: Optional[Union[ExperienceLevel, str]] = None
    posted_date: Optional[Union[datetime, str]] = None  # Accept string dates
    expires_date: Optional[Union[datetime, str]] = None
    
    # Platform info
    platform: str
    platform_url: Union[HttpUrl, str]  # Accept string URLs
    apply_url: Optional[Union[HttpUrl, str]] = None
    
    # Derived fields
    skills: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    # Additional fields for compatibility
    source: Optional[str] = None
    
    # Processing
    processed_at: Optional[datetime] = Field(default=None)
    last_updated: Optional[datetime] = None
    status: str = "active"
    
    # Validators (Pydantic v2 style)
    @field_validator('title', 'company', 'description')
    @classmethod
    def clean_text(cls, v):
        """Remove extra whitespace and normalize."""
        if v:
            return ' '.join(v.split())
        return v
    
    @field_validator('location_type', mode='before')
    @classmethod
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
    
    @field_validator('id', 'raw_job_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string if needed."""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    def __init__(self, **data):
        """Initialize with UUID conversion"""
        # Convert UUIDs to strings
        if 'id' in data and isinstance(data['id'], UUID):
            data['id'] = str(data['id'])
        if 'raw_job_id' in data and isinstance(data['raw_job_id'], UUID):
            data['raw_job_id'] = str(data['raw_job_id'])
        
        super().__init__(**data)
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True