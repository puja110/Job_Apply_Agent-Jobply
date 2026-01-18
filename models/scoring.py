# models/scoring.py
"""
Job Scoring Models
Contains models for job scoring, ranking, and match quality
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ScoringWeights(BaseModel):
    """Configurable weights for different scoring components"""
    
    skill_match: float = 0.40  # 40% - Most important
    salary: float = 0.20       # 20%
    location: float = 0.15     # 15%
    company: float = 0.10      # 10%
    success_prob: float = 0.15 # 15%
    
    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = (
            self.skill_match + 
            self.salary + 
            self.location + 
            self.company + 
            self.success_prob
        )
        return abs(total - 1.0) < 0.01  # Allow small floating point errors


class ScoringConfig(BaseModel):
    """Configuration for the scoring engine"""
    
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    
    # Skill matching config
    use_semantic_matching: bool = True
    semantic_similarity_threshold: float = 0.6  # Minimum similarity to consider a match
    
    # Salary scoring config
    salary_weight_factor: float = 1.0  # How much to penalize salary mismatches
    
    # Location scoring config
    remote_bonus: float = 10.0  # Bonus points for remote jobs if user prefers remote
    
    # Company scoring config
    preferred_company_bonus: float = 20.0  # Bonus for preferred companies
    
    # Success probability config
    experience_level_mismatch_penalty: float = 15.0
    
    class Config:
        arbitrary_types_allowed = True


class JobScore(BaseModel):
    """
    Complete job scoring model
    Stores both the internal representation (for code) and database representation
    """
    
    # IDs
    id: Optional[UUID] = None
    job_id: UUID
    user_profile_id: UUID
    
    # Overall score
    overall_score: float = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    total_score: Optional[float] = None  # Alias for DB compatibility
    rank: Optional[int] = None
    
    # Component scores (0-100 each)
    skill_score: float = Field(0, ge=0, le=100, description="Skill match score")
    skill_match_score: Optional[float] = None  # Alias for DB
    
    salary_score: float = Field(0, ge=0, le=100, description="Salary match score")
    
    location_score: float = Field(0, ge=0, le=100, description="Location match score")
    
    company_score: float = Field(0, ge=0, le=100, description="Company preference score")
    
    success_score: float = Field(0, ge=0, le=100, description="Success probability score")
    success_probability_score: Optional[float] = None  # Alias for DB
    
    # Details
    matched_skills: List[str] = Field(default_factory=list, description="Skills that match job requirements")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills user doesn't have")
    skill_similarity: Optional[float] = Field(None, description="Semantic similarity score (0-1)")
    
    # Explanation
    explanation: Optional[str] = Field(None, description="Human-readable score explanation")
    score_explanation: Optional[str] = None  # Alias for DB
    match_highlights: List[str] = Field(default_factory=list, description="Key match highlights")
    
    # Metadata
    scored_at: Optional[datetime] = None
    scoring_version: str = "v1.0"
    
    # Job reference (for convenience)
    job: Optional['Job'] = None  # Forward reference
    
    def __init__(self, **data):
        """Initialize with automatic alias handling"""
        super().__init__(**data)
        
        # Sync aliases for DB compatibility
        if self.overall_score and not self.total_score:
            self.total_score = self.overall_score
        if self.total_score and not self.overall_score:
            self.overall_score = self.total_score
            
        if self.skill_score and not self.skill_match_score:
            self.skill_match_score = self.skill_score
        if self.skill_match_score and not self.skill_score:
            self.skill_score = self.skill_match_score
            
        if self.success_score and not self.success_probability_score:
            self.success_probability_score = self.success_score
        if self.success_probability_score and not self.success_score:
            self.success_score = self.success_probability_score
            
        if self.explanation and not self.score_explanation:
            self.score_explanation = self.explanation
        if self.score_explanation and not self.explanation:
            self.explanation = self.score_explanation
    
    def get_score_breakdown(self) -> Dict[str, float]:
        """Get a dictionary of all component scores"""
        return {
            'overall': self.overall_score,
            'skill': self.skill_score,
            'salary': self.salary_score,
            'location': self.location_score,
            'company': self.company_score,
            'success': self.success_score
        }
    
    def get_badge(self) -> str:
        """Get a color-coded badge based on score"""
        if self.overall_score >= 80:
            return "🟢"  # Green - Excellent match
        elif self.overall_score >= 60:
            return "🟡"  # Yellow - Good match
        elif self.overall_score >= 40:
            return "🟠"  # Orange - Fair match
        else:
            return "🔴"  # Red - Poor match
    
    def is_strong_match(self) -> bool:
        """Check if this is a strong match (>= 70)"""
        return self.overall_score >= 70
    
    def __str__(self) -> str:
        """String representation"""
        return f"JobScore(job_id={self.job_id}, score={self.overall_score:.1f})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ScoreExplanation(BaseModel):
    """Detailed explanation of how a score was calculated"""
    
    overall_score: float
    components: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Detailed breakdown of each scoring component"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommendations for the user"
    )
    
    def add_component(self, name: str, score: float, reason: str, details: Dict = None):
        """Add a scoring component explanation"""
        self.components[name] = {
            'score': score,
            'reason': reason,
            'details': details or {}
        }
    
    def add_recommendation(self, recommendation: str):
        """Add a recommendation"""
        self.recommendations.append(recommendation)
    
    def to_text(self) -> str:
        """Convert to readable text explanation"""
        lines = [f"Overall Score: {self.overall_score:.1f}/100\n"]
        
        for name, data in self.components.items():
            lines.append(f"{name.title()}: {data['score']:.1f}/100")
            lines.append(f"  {data['reason']}")
        
        if self.recommendations:
            lines.append("\nRecommendations:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")
        
        return "\n".join(lines)


# Forward reference resolution
from models.job import Job
JobScore.model_rebuild()