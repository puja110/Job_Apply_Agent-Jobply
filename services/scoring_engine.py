# services/scoring_engine.py
from typing import Dict, Optional
from services.embeddings import EmbeddingService  # Changed from embedding_service
from models.scoring import ScoringWeights, ScoringConfig
from models.user_profile import UserProfile
from models.job import Job
import logging

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Calculate job scores based on multiple factors."""
    
    def __init__(
        self, 
        embedding_service: EmbeddingService,
        config: Optional[ScoringConfig] = None
    ):
        self.embedding_service = embedding_service
        self.config = config or ScoringConfig()
        self.config.weights.validate_weights()
    
    async def score_job(
        self,
        job: Job,
        user_profile: UserProfile
    ) -> 'JobScore':
        """
        Calculate comprehensive score for a job.
        
        Args:
            job: Job object
            user_profile: UserProfile object
            
        Returns:
            JobScore object
        """
        from models.scoring import JobScore
        
        # Component scores (all 0-100)
        skill_score = await self._score_skills(job, user_profile)
        salary_score = self._score_salary(job, user_profile)
        location_score = self._score_location(job, user_profile)
        company_score = self._score_company(job, user_profile)
        success_score = self._score_success_probability(job, user_profile)
        
        # Calculate weighted total
        weights = self.config.weights
        total_score = (
            skill_score * weights.skill_match +
            salary_score * weights.salary +
            location_score * weights.location +
            company_score * weights.company +
            success_score * weights.success_prob
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            skill_score, salary_score, location_score, 
            company_score, success_score
        )
        
        return JobScore(
            job_id=job.id,
            user_profile_id=user_profile.id,
            overall_score=round(total_score, 2),
            skill_score=round(skill_score, 2),
            salary_score=round(salary_score, 2),
            location_score=round(location_score, 2),
            company_score=round(company_score, 2),
            success_score=round(success_score, 2),
            explanation=explanation,
            job=job
        )
    
    async def _score_skills(self, job: Job, user_profile: UserProfile) -> float:
        """Score skill match (0-100)."""
        user_skills = user_profile.skills or []
        job_skills = job.skills or []
        
        if not job_skills and not job.description:
            return 50.0  # Neutral if no skill info
        
        # Exact match scoring
        user_skills_lower = {s.lower().strip() for s in user_skills}
        job_skills_lower = {s.lower().strip() for s in job_skills}
        
        if job_skills_lower:
            matched_skills = user_skills_lower.intersection(job_skills_lower)
            match_percentage = (len(matched_skills) / len(job_skills_lower)) * 100
        else:
            match_percentage = 50.0
        
        # Semantic similarity using embeddings
        if job.description:
            try:
                user_text = ", ".join(user_skills)
                job_text = f"{job.title}. {job.description[:500]}"
                
                # Use the correct method based on your EmbeddingService
                embeddings = self.embedding_service.encode([user_text, job_text])
                similarity = self.embedding_service.cosine_similarity(
                    embeddings[0], embeddings[1]
                )
                
                semantic_score = max(0, min(100, similarity * 100))
                
                # Combine exact match and semantic similarity
                final_score = (match_percentage * 0.6) + (semantic_score * 0.4)
            except Exception as e:
                logger.warning(f"Semantic matching failed: {e}")
                final_score = match_percentage
        else:
            final_score = match_percentage
        
        return min(100, final_score)
    
    def _score_salary(self, job: Job, user_profile: UserProfile) -> float:
        """Score salary alignment (0-100)."""
        job_min = job.salary_min
        job_max = job.salary_max
        user_min = user_profile.target_salary_min
        user_max = user_profile.target_salary_max
        
        # If no salary data, return neutral score
        if not user_min or not job_min:
            return 50.0
        
        # If job minimum meets or exceeds user minimum
        if job_min >= user_min:
            score = 80.0
            
            # Bonus if within desired range
            if user_max and job_max and job_max <= user_max * 1.2:
                score = 100.0
            # Big bonus if significantly above minimum
            elif job_min >= user_min * 1.5:
                score = 100.0
                
            return score
        
        # If job salary is below expectations
        else:
            # Calculate how much below
            gap_percentage = ((user_min - job_min) / user_min) * 100
            
            if gap_percentage < 10:
                return 60.0  # Close enough
            elif gap_percentage < 20:
                return 40.0  # Somewhat below
            elif gap_percentage < 30:
                return 20.0  # Significantly below
            else:
                return 10.0  # Far below
    
    def _score_location(self, job: Job, user_profile: UserProfile) -> float:
        """Score location match (0-100)."""
        job_location = (job.location or '').lower()
        job_location_type = str(job.location_type).lower() if job.location_type else ''
        user_location = (user_profile.preferred_location or '').lower()
        remote_pref = (user_profile.remote_preference or 'flexible').lower()
        willing_to_relocate = user_profile.willing_to_relocate
        
        # Remote preference matching
        if remote_pref == 'remote_only':
            if job_location_type == 'remote' or 'remote' in job_location:
                return 100.0
            else:
                return 10.0
        
        elif remote_pref == 'onsite':
            if job_location_type == 'onsite':
                # Check location match
                if user_location in job_location or job_location in user_location:
                    return 100.0
                elif willing_to_relocate:
                    return 70.0
                else:
                    return 30.0
            else:
                return 40.0
        
        elif remote_pref == 'hybrid':
            if job_location_type == 'hybrid':
                return 100.0
            elif job_location_type == 'remote':
                return 90.0
            else:
                return 50.0
        
        else:  # flexible
            if job_location_type == 'remote' or 'remote' in job_location:
                return 100.0
            elif user_location in job_location or job_location in user_location:
                return 90.0
            elif willing_to_relocate:
                return 70.0
            else:
                return 60.0
    
    def _score_company(self, job: Job, user_profile: UserProfile) -> float:
        """Score company match (0-100)."""
        # Safely check for preferred_companies attribute
        preferred_companies = getattr(user_profile, 'preferred_companies', None)
        
        if not preferred_companies:
            return 50.0  # Neutral if no preference
        
        company_lower = job.company.lower()
        preferred_lower = [c.lower() for c in preferred_companies]
        
        for preferred in preferred_lower:
            if preferred in company_lower or company_lower in preferred:
                return 100.0
        
        return 50.0
    
    def _score_success_probability(self, job: Job, user_profile: UserProfile) -> float:
        """Score likelihood of success (0-100)."""
        user_experience = user_profile.years_of_experience or 0
        user_level = (user_profile.experience_level or 'mid').lower()
        job_title = job.title.lower()
        
        # Parse seniority from title
        title_seniority = 'mid'  # default
        if any(word in job_title for word in ['senior', 'sr', 'lead', 'principal', 'staff']):
            title_seniority = 'senior'
        elif any(word in job_title for word in ['junior', 'jr', 'entry', 'associate']):
            title_seniority = 'junior'
        
        # Match experience level
        if user_level == title_seniority:
            base_score = 80.0
        elif (user_level == 'senior' and title_seniority == 'mid') or \
             (user_level == 'mid' and title_seniority == 'junior'):
            base_score = 90.0  # Overqualified
        elif (user_level == 'mid' and title_seniority == 'senior'):
            base_score = 60.0  # Slight stretch
        elif (user_level == 'junior' and title_seniority == 'mid'):
            base_score = 50.0  # Moderate stretch
        else:
            base_score = 30.0  # Significant mismatch
        
        # Adjust based on years of experience
        if user_experience >= 5 and title_seniority == 'senior':
            base_score = min(100, base_score + 10)
        elif user_experience < 2 and title_seniority == 'senior':
            base_score = max(20, base_score - 20)
        
        return base_score
    
    def _generate_explanation(
        self,
        skill_score: float,
        salary_score: float,
        location_score: float,
        company_score: float,
        success_score: float
    ) -> str:
        """Generate human-readable explanation of the score."""
        explanations = []
        
        # Skills
        if skill_score >= 80:
            explanations.append("✓ Excellent skill match")
        elif skill_score >= 60:
            explanations.append("~ Good skill alignment")
        else:
            explanations.append("⚠ Limited skill match")
        
        # Salary
        if salary_score >= 80:
            explanations.append("✓ Salary meets expectations")
        elif salary_score >= 50:
            explanations.append("~ Salary is acceptable")
        else:
            explanations.append("⚠ Salary below target")
        
        # Location
        if location_score >= 80:
            explanations.append("✓ Great location fit")
        elif location_score >= 50:
            explanations.append("~ Decent location match")
        else:
            explanations.append("⚠ Location not ideal")
        
        # Success probability
        if success_score >= 80:
            explanations.append("✓ High success probability")
        elif success_score >= 60:
            explanations.append("~ Moderate success chance")
        else:
            explanations.append("⚠ May be challenging")
        
        return " | ".join(explanations)