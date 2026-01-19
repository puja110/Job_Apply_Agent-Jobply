"""
Resume Models
Data models for resume generation and tailoring
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


class ResumeFormat(str, Enum):
    """Resume output formats"""
    LATEX = "latex"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class WorkExperience(BaseModel):
    """Work experience entry"""
    company: str
    position: str
    location: Optional[str] = None
    start_date: str  # e.g., "Jan 2020"
    end_date: Optional[str] = None  # None for current job
    description: str
    achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """Education entry"""
    institution: str
    degree: str
    field_of_study: str
    location: Optional[str] = None
    graduation_date: str
    gpa: Optional[float] = None
    honors: List[str] = Field(default_factory=list)
    relevant_coursework: List[str] = Field(default_factory=list)


class Project(BaseModel):
    """Project entry"""
    name: str
    description: str
    technologies: List[str]
    url: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    date: Optional[str] = None


class Certification(BaseModel):
    """Certification entry"""
    name: str
    issuer: str
    date: str
    credential_id: Optional[str] = None
    url: Optional[str] = None


class BaseResume(BaseModel):
    """Base resume template with all user information"""
    
    # Personal Information
    full_name: str
    email: str
    phone: Optional[str] = None
    location: str
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    
    # Professional Summary
    summary: str
    
    # Skills (categorized)
    technical_skills: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Categorized skills: {'Languages': [...], 'Frameworks': [...], ...}"
    )
    
    # Experience
    work_experience: List[WorkExperience] = Field(default_factory=list)
    
    # Education
    education: List[Education] = Field(default_factory=list)
    
    # Projects
    projects: List[Project] = Field(default_factory=list)
    
    # Certifications
    certifications: List[Certification] = Field(default_factory=list)
    
    # Additional Sections
    publications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    volunteer: List[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    """Resume tailored for a specific job"""
    
    id: Optional[UUID] = None
    user_profile_id: UUID
    job_id: UUID
    base_resume_id: Optional[UUID] = None
    
    # Tailored Content
    tailored_summary: str
    highlighted_skills: List[str]
    relevant_experience: List[WorkExperience]
    relevant_projects: List[Project]
    keywords_included: List[str]
    
    # Metadata
    match_score: Optional[float] = None
    tailoring_strategy: str = Field(
        default="",
        description="Strategy used for tailoring (e.g., 'emphasize ML experience')"
    )
    
    # Output
    latex_content: Optional[str] = None
    markdown_content: Optional[str] = None
    pdf_path: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ResumeTailoringRequest(BaseModel):
    """Request for resume tailoring"""
    
    job_id: UUID
    user_profile_id: UUID
    base_resume: BaseResume
    
    # Tailoring Options
    format: ResumeFormat = ResumeFormat.PDF
    max_length: int = Field(default=1, description="Max pages")
    emphasize_skills: List[str] = Field(default_factory=list)
    include_sections: List[str] = Field(
        default_factory=lambda: ["summary", "experience", "education", "skills", "projects"]
    )


class ATSOptimizationResult(BaseModel):
    """Results of ATS optimization analysis"""
    
    ats_score: float = Field(..., ge=0, le=100, description="ATS compatibility score")
    keyword_match_rate: float = Field(..., ge=0, le=1)
    matched_keywords: List[str]
    missing_keywords: List[str]
    suggestions: List[str]
    warnings: List[str] = Field(default_factory=list)