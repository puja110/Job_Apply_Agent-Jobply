# services/skill_matcher.py
from typing import List, Dict, Tuple
from services.embeddings import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class SkillMatcher:
    """Match user skills against job requirements using semantic similarity."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    def match_skills(
        self,
        user_skills: List[str],
        job_skills: List[str],
        threshold: float = 0.5
    ) -> Dict:
        """
        Match user skills against job requirements.
        
        Args:
            user_skills: List of user's skills
            job_skills: List of job's required skills
            threshold: Minimum similarity to consider a match
            
        Returns:
            Dict with matched_skills, missing_skills, and similarity scores
        """
        if not job_skills:
            # If no skills listed, assume all user skills match
            return {
                'matched_skills': user_skills,
                'missing_skills': [],
                'match_percentage': 100.0,
                'skill_details': []
            }
        
        if not user_skills:
            return {
                'matched_skills': [],
                'missing_skills': job_skills,
                'match_percentage': 0.0,
                'skill_details': []
            }
        
        # Generate embeddings for all skills
        user_embeddings = self.embedding_service.generate_embeddings(user_skills)
        job_embeddings = self.embedding_service.generate_embeddings(job_skills)
        
        matched_skills = []
        missing_skills = []
        skill_details = []
        
        # For each job skill, find best matching user skill
        for job_idx, job_skill in enumerate(job_skills):
            job_emb = job_embeddings[job_idx]
            
            # Find most similar user skill
            best_similarity = 0.0
            best_user_skill = None
            
            for user_idx, user_skill in enumerate(user_skills):
                user_emb = user_embeddings[user_idx]
                similarity = self.embedding_service.compute_similarity(user_emb, job_emb)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_user_skill = user_skill
            
            # Record the match
            skill_detail = {
                'job_skill': job_skill,
                'user_skill': best_user_skill,
                'similarity': best_similarity,
                'matched': best_similarity >= threshold
            }
            skill_details.append(skill_detail)
            
            if best_similarity >= threshold:
                matched_skills.append(job_skill)
            else:
                missing_skills.append(job_skill)
        
        # Calculate match percentage
        match_percentage = (len(matched_skills) / len(job_skills)) * 100
        
        return {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_percentage': match_percentage,
            'skill_details': skill_details
        }
    
    def compute_profile_job_similarity(
        self,
        user_profile: Dict,
        job_data: Dict
    ) -> float:
        """
        Compute overall semantic similarity between user profile and job.
        
        Args:
            user_profile: User profile data
            job_data: Job data
            
        Returns:
            Similarity score between 0 and 1
        """
        # Create text representations
        profile_text = self.embedding_service.embed_user_profile(user_profile)
        job_text = self.embedding_service.embed_job_description(job_data)
        
        # Generate embeddings
        profile_emb = self.embedding_service.generate_embedding(profile_text)
        job_emb = self.embedding_service.generate_embedding(job_text)
        
        # Compute similarity
        similarity = self.embedding_service.compute_similarity(profile_emb, job_emb)
        
        return similarity