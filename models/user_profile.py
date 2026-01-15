# models/user_profile.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class RemotePreference(str, Enum):
    REMOTE_ONLY = "remote_only"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    FLEXIBLE = "flexible"

class CompanySize(str, Enum):
    STARTUP = "startup"  # <50 employees
    SMALL = "small"      # 50-200
    MID = "mid"          # 200-1000
    LARGE = "large"      # 1000-5000
    ENTERPRISE = "enterprise"  # 5000+

class UserProfile(BaseModel):
    id: Optional[str] = None
    
    # Basic info
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    
    # Skills and experience
    skills: List[str] = Field(default_factory=list)
    years_of_experience: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    
    # Job preferences
    target_salary_min: Optional[int] = None
    target_salary_max: Optional[int] = None
    target_salary_currency: str = "USD"
    preferred_location: Optional[str] = None
    remote_preference: RemotePreference = RemotePreference.FLEXIBLE
    willing_to_relocate: bool = False
    
    # Additional preferences
    preferred_company_sizes: List[CompanySize] = Field(default_factory=list)
    preferred_industries: List[str] = Field(default_factory=list)
    
    # Resume
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    @validator('skills')
    def normalize_skills(cls, v):
        """Normalize skill names."""
        return [skill.strip().title() for skill in v if skill.strip()]
    
    @validator('years_of_experience')
    def validate_experience(cls, v):
        """Validate years of experience."""
        if v is not None and (v < 0 or v > 50):
            raise ValueError("Years of experience must be between 0 and 50")
        return v
    
    class Config:
        use_enum_values = True


class JobScore(BaseModel):
    id: Optional[str] = None
    job_id: str
    user_profile_id: str
    
    # Overall score
    total_score: float  # 0-100
    rank: Optional[int] = None
    
    # Component scores
    skill_match_score: Optional[float] = None
    salary_score: Optional[float] = None
    location_score: Optional[float] = None
    company_score: Optional[float] = None
    success_probability_score: Optional[float] = None
    
    # Details
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    skill_similarity: Optional[float] = None
    
    # Explanation
    score_explanation: Optional[str] = None
    match_highlights: List[str] = Field(default_factory=list)
    
    # Metadata
    scored_at: Optional[datetime] = None
    scoring_version: str = "v1.0"