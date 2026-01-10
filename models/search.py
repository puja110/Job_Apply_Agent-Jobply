# models/search.py
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from enum import Enum

class SearchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class JobSearchParams(BaseModel):
    """Parameters for job search."""
    query: str
    location: Optional[str] = None
    platform: str
    
    # Filters
    remote_only: bool = False
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    posted_within_days: int = 7
    
    # Pagination
    max_results: int = 50

class JobSearchResult(BaseModel):
    """Result of a job search."""
    search_id: str
    search_params: JobSearchParams
    
    status: SearchStatus
    results_count: int = 0
    new_jobs_count: int = 0
    duplicate_jobs_count: int = 0
    
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None