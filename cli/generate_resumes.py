"""
Pydantic models for generated resumes
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TailoredResumeData(BaseModel):
    """Resume content structure"""
    contact_info: dict
    professional_summary: str
    experience: List[dict]
    education: List[dict]
    skills: List[str]
    certifications: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    keywords_injected: List[str] = Field(default_factory=list)


class ATSScores(BaseModel):
    """ATS scoring metrics"""
    overall_score: float = Field(ge=0, le=100)
    keyword_match_rate: float = Field(ge=0, le=100)
    matched_keywords: List[str]
    missing_keywords: List[str]
    formatting_score: float = Field(ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)


class GeneratedResumeCreate(BaseModel):
    """Schema for creating a new generated resume"""
    user_profile_id: UUID
    job_id: UUID
    filename: str
    file_path: str
    file_size_bytes: int
    resume_data: TailoredResumeData
    ats_score: Optional[float] = None
    keyword_match_rate: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None
    pdf_data: Optional[bytes] = None


class GeneratedResumeUpdate(BaseModel):
    """Schema for updating an existing resume"""
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    resume_data: Optional[TailoredResumeData] = None
    ats_score: Optional[float] = None
    keyword_match_rate: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None
    pdf_data: Optional[bytes] = None


class GeneratedResume(BaseModel):
    """Complete generated resume model"""
    id: UUID
    user_profile_id: UUID
    job_id: UUID
    filename: str
    file_path: str
    file_size_bytes: int
    resume_data: TailoredResumeData
    ats_score: Optional[float] = None
    keyword_match_rate: Optional[float] = None
    matched_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    pdf_data: Optional[bytes] = None

    class Config:
        from_attributes = True