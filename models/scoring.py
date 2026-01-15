# models/scoring.py
from pydantic import BaseModel
from typing import Dict

class ScoringWeights(BaseModel):
    """Configurable weights for different scoring components."""
    skill_match: float = 0.40      # 40%
    salary: float = 0.20            # 20%
    location: float = 0.15          # 15%
    company: float = 0.15           # 15%
    success_probability: float = 0.10  # 10%
    
    def validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = (
            self.skill_match + 
            self.salary + 
            self.location + 
            self.company + 
            self.success_probability
        )
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return True

class ScoringConfig(BaseModel):
    """Configuration for the scoring system."""
    weights: ScoringWeights = ScoringWeights()
    
    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Thresholds
    min_skill_similarity: float = 0.3  # Below this = poor match
    excellent_skill_similarity: float = 0.7  # Above this = excellent match
    
    # Salary scoring
    salary_importance: str = "high"  # 'low', 'medium', 'high'
    
    # Location scoring
    location_importance: str = "medium"