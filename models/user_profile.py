# models/user_profile.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class RemotePreference(str, Enum):
    """Remote work preference options"""
    REMOTE_ONLY = "remote_only"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    FLEXIBLE = "flexible"


class ExperienceLevel(str, Enum):
    """Experience level options"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"


class UserProfile(BaseModel):
    """User profile with skills, preferences, and job search criteria"""

    # Basic info
    id: Optional[UUID] = None
    name: str
    email: str

    # Skills and experience
    skills: List[str]
    years_of_experience: Optional[int] = None
    experience_level: Optional[str] = None  # 'junior', 'mid', 'senior', 'lead'
    
    # Job preferences
    target_salary_min: Optional[int] = None
    target_salary_max: Optional[int] = None
    target_salary_currency: str = 'USD'
    
    preferred_location: Optional[str] = None
    remote_preference: Optional[str] = None  # 'remote_only', 'hybrid', 'onsite', 'flexible'
    willing_to_relocate: bool = False
    
    # Additional preferences
    preferred_company_sizes: Optional[List[str]] = None
    preferred_industries: Optional[List[str]] = None
    
    # Resume
    resume_path: Optional[str] = None
    resume_text: Optional[str] = None
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    # Validators (Pydantic v2 style)
    @field_validator('skills')
    @classmethod
    def normalize_skills(cls, v):
        """Normalize skill names."""
        return [skill.strip().title() for skill in v if skill.strip()]
    
    @field_validator('years_of_experience')
    @classmethod
    def validate_experience(cls, v):
        """Validate years of experience."""
        if v is not None and (v < 0 or v > 50):
            raise ValueError("Years of experience must be between 0 and 50")
        return v
    
    # Helper methods
    def matches_location(self, job_location: Optional[str], job_location_type: Optional[str]) -> bool:
        """Check if job location matches user preferences"""
        if not job_location_type:
            return True
        
        location_type_lower = job_location_type.lower()
        
        if self.remote_preference == 'remote_only':
            return 'remote' in location_type_lower
        
        if self.remote_preference == 'hybrid':
            return 'hybrid' in location_type_lower or 'remote' in location_type_lower
        
        if self.remote_preference == 'onsite':
            if 'onsite' in location_type_lower or 'on-site' in location_type_lower:
                return True
            if self.preferred_location and job_location:
                return self.preferred_location.lower() in job_location.lower()
        
        if self.remote_preference == 'flexible':
            return True
        
        if self.preferred_location and job_location:
            return self.preferred_location.lower() in job_location.lower()
        
        return True
    
    def get_skill_set(self) -> set:
        """Get skills as a set for easy comparison"""
        return {skill.lower().strip() for skill in self.skills}
    
    def salary_in_range(self, salary_min: Optional[int], salary_max: Optional[int]) -> bool:
        """Check if job salary overlaps with target salary range"""
        if not salary_min and not salary_max:
            return True
        
        if not self.target_salary_min and not self.target_salary_max:
            return True
        
        job_range = (salary_min or 0, salary_max or float('inf'))
        user_range = (self.target_salary_min or 0, self.target_salary_max or float('inf'))
        
        return job_range[0] <= user_range[1] and job_range[1] >= user_range[0]
    
    class Config:
        use_enum_values = True