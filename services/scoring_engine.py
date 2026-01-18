# services/scoring_engine.py
from typing import Dict, Optional
from services.skill_matcher import SkillMatcher
from models.scoring import ScoringWeights, ScoringConfig
from models.user_profile import RemotePreference
import logging

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Calculate job scores based on multiple factors."""
    
    def __init__(
        self, 
        skill_matcher: SkillMatcher,
        config: Optional[ScoringConfig] = None
    ):
        self.skill_matcher = skill_matcher
        self.config = config or ScoringConfig()
        self.config.weights.validate_weights()
    
    def score_job(
        self,
        job_data: Dict,
        user_profile: Dict
    ) -> Dict:
        """
        Calculate comprehensive score for a job.
        
        Args:
            job_data: Job information
            user_profile: User profile information
            
        Returns:
            Dict with total_score and component scores
        """
        # Component scores (all 0-100)
        skill_score = self._score_skills(job_data, user_profile)
        salary_score = self._score_salary(job_data, user_profile)
        location_score = self._score_location(job_data, user_profile)
        company_score = self._score_company(job_data, user_profile)
        success_score = self._score_success_probability(job_data, user_profile)
        
        # Calculate weighted total
        weights = self.config.weights
        total_score = (
            skill_score * weights.skill_match +
            salary_score * weights.salary +
            location_score * weights.location +
            company_score * weights.company +
            success_score * weights.success_probability
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            skill_score, salary_score, location_score, 
            company_score, success_score, job_data
        )
        
        return {
            'total_score': round(total_score, 2),
            'skill_match_score': round(skill_score, 2),
            'salary_score': round(salary_score, 2),
            'location_score': round(location_score, 2),
            'company_score': round(company_score, 2),
            'success_probability_score': round(success_score, 2),
            'score_explanation': explanation
        }
    
    def _score_skills(self, job_data: Dict, user_profile: Dict) -> float:
        """Score skill match (0-100)."""
        user_skills = user_profile.get('skills', [])
        job_skills = job_data.get('skills', [])
        
        if not job_skills:
            # If no skills specified, use semantic similarity
            similarity = self.skill_matcher.compute_profile_job_similarity(
                user_profile, job_data
            )
            return similarity * 100
        
        # Match specific skills
        match_result = self.skill_matcher.match_skills(user_skills, job_skills)
        
        # Base score on match percentage
        base_score = match_result['match_percentage']
        
        # Bonus for overall profile similarity
        similarity = self.skill_matcher.compute_profile_job_similarity(
            user_profile, job_data
        )
        similarity_bonus = similarity * 20  # Up to 20 bonus points
        
        final_score = min(100, base_score + similarity_bonus)
        return final_score
    
    def _score_salary(self, job_data: Dict, user_profile: Dict) -> float:
        """Score salary alignment (0-100)."""
        job_min = job_data.get('salary_min')
        job_max = job_data.get('salary_max')
        user_min = user_profile.get('target_salary_min')
        user_max = user_profile.get('target_salary_max')
        
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
    
    def _score_location(self, job_data: Dict, user_profile: Dict) -> float:
        """Score location match (0-100)."""
        job_location = job_data.get('location', '').lower()
        job_location_type = job_data.get('location_type', '').lower()
        user_location = user_profile.get('preferred_location', '').lower()
        remote_pref = user_profile.get('remote_preference', 'flexible').lower()
        willing_to_relocate = user_profile.get('willing_to_relocate', False)
        
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
    
    def _score_company(self, job_data: Dict, user_profile: Dict) -> float:
        """Score company match (0-100)."""
        # For now, neutral score
        # Can be enhanced with company data from external APIs
        return 50.0
    
    def _score_success_probability(self, job_data: Dict, user_profile: Dict) -> float:
        """Score likelihood of success (0-100)."""
        user_experience = user_profile.get('years_of_experience', 0)
        user_level = user_profile.get('experience_level', 'mid').lower()
        job_title = job_data.get('title', '').lower()
        
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
        success_score: float,
        job_data: Dict
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