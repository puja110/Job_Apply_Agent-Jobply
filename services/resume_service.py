"""
Resume Service - Integrates PDF generation with database operations
"""
from pathlib import Path
from typing import List, Optional, Dict
from uuid import UUID
import asyncpg
import json
from datetime import datetime

from services.pdf_generator import PDFGenerator
from repositories.resume_repository import ResumeRepository
from models.generated_resume import (
    TailoredResumeData,
    GeneratedResumeCreate,
    GeneratedResume
)


class ResumeService:
    """High-level service for resume generation and management"""
    
    def __init__(self, db_pool: asyncpg.Pool, output_dir: Path = Path("./generated_resumes")):
        self.pool = db_pool
        self.repository = ResumeRepository(db_pool)
        self.pdf_generator = PDFGenerator(output_dir)
        self.output_dir = output_dir
    
    async def generate_resume_for_job(
        self,
        user_profile_id: UUID,
        job_id: UUID,
        store_pdf_in_db: bool = False
    ) -> Optional[Dict]:
        """
        Generate tailored resume for a specific job
        
        Args:
            user_profile_id: User's profile UUID
            job_id: Target job UUID
            store_pdf_in_db: Whether to store PDF bytes in database
            
        Returns:
            Dictionary with resume details or None if failed
        """
        # Check if resume already exists
        existing = await self.repository.get_by_user_and_job(user_profile_id, job_id)
        if existing:
            print(f"Resume already exists for this job: {existing.filename}")
            return self._resume_to_dict(existing)
        
        # Fetch job and user profile data
        job_data = await self._fetch_job(job_id)
        if not job_data:
            print(f"Job {job_id} not found")
            return None
        
        user_profile = await self._fetch_user_profile(user_profile_id)
        if not user_profile:
            print(f"User profile {user_profile_id} not found")
            return None
        
        # Tailor resume to job
        resume_data = await self._tailor_resume(user_profile, job_data)
        
        # Extract job keywords for ATS scoring
        job_keywords = self._extract_job_keywords(job_data)
        
        # Calculate ATS scores
        ats_scores = self.pdf_generator.calculate_ats_score(resume_data, job_keywords)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company = job_data.get('company', 'Unknown').replace(' ', '_')
        filename = f"resume_{company}_{timestamp}.pdf"
        
        # Generate PDF
        pdf_bytes, file_path = self.pdf_generator.generate_pdf(
            resume_data=resume_data,
            filename=filename,
            save_to_disk=True
        )
        
        # Prepare database entry
        resume_create = GeneratedResumeCreate(
            user_profile_id=user_profile_id,
            job_id=job_id,
            filename=filename,
            file_path=str(file_path),
            file_size_bytes=len(pdf_bytes),
            resume_data=resume_data,
            ats_score=ats_scores.overall_score,
            keyword_match_rate=ats_scores.keyword_match_rate,
            matched_keywords=ats_scores.matched_keywords,
            missing_keywords=ats_scores.missing_keywords,
            pdf_data=pdf_bytes if store_pdf_in_db else None
        )
        
        # Save to database
        generated_resume = await self.repository.create(resume_create)
        
        return self._resume_to_dict(generated_resume, job_data)
    
    async def generate_batch_resumes(
        self,
        user_profile_id: UUID,
        min_score: float = 70.0,
        limit: int = 10,
        store_pdf_in_db: bool = False
    ) -> List[Dict]:
        """
        Generate resumes for top-scored jobs
        
        Args:
            user_profile_id: User's profile UUID
            min_score: Minimum job match score threshold
            limit: Maximum number of resumes to generate
            store_pdf_in_db: Whether to store PDF bytes in database
            
        Returns:
            List of generated resume details
        """
        # Fetch top-scored jobs
        top_jobs = await self._fetch_top_jobs(user_profile_id, min_score, limit)
        
        if not top_jobs:
            print(f"No jobs found with score >= {min_score}")
            return []
        
        print(f"Found {len(top_jobs)} jobs to process")
        
        # Generate resumes for each job
        results = []
        for job_data in top_jobs:
            job_id = job_data['id']
            
            print(f"Generating resume for: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            result = await self.generate_resume_for_job(
                user_profile_id=user_profile_id,
                job_id=job_id,
                store_pdf_in_db=store_pdf_in_db
            )
            
            if result:
                results.append(result)
        
        return results
    
    async def _fetch_job(self, job_id: UUID) -> Optional[Dict]:
        """Fetch job details from database"""
        query = """
            SELECT 
                j.id, j.title, j.company, j.location, j.description,
                j.requirements, j.salary_min, j.salary_max,
                js.total_score, js.skill_match_score
            FROM jobs j
            LEFT JOIN job_scores js ON j.id = js.job_id
            WHERE j.id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, job_id)
            if row:
                return dict(row)
            return None
    
    async def _fetch_user_profile(self, user_profile_id: UUID) -> Optional[Dict]:
        """Fetch user profile from database"""
        query = "SELECT * FROM user_profile WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_profile_id)
            if row:
                return dict(row)
            return None
    
    async def _fetch_top_jobs(
        self,
        user_profile_id: UUID,
        min_score: float,
        limit: int
    ) -> List[Dict]:
        """Fetch top-scored jobs for user"""
        query = """
            SELECT 
                j.id, j.title, j.company, j.location, j.description,
                j.requirements, j.salary_min, j.salary_max,
                js.total_score, js.skill_match_score
            FROM jobs j
            INNER JOIN job_scores js ON j.id = js.job_id
            WHERE js.user_profile_id = $1 AND js.total_score >= $2
            ORDER BY js.total_score DESC, js.skill_match_score DESC
            LIMIT $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_profile_id, min_score, limit)
            return [dict(row) for row in rows]
    
    async def _tailor_resume(
        self,
        user_profile: Dict,
        job_data: Dict
    ) -> TailoredResumeData:
        """
        Tailor resume content to match job requirements
        
        This is a simplified version. In production, you'd use an LLM
        to intelligently tailor the content.
        """
        # Extract user data - parse JSON fields if they're strings
        skills = user_profile.get('skills', [])
        if isinstance(skills, str):
            skills = json.loads(skills)
        
        experience = user_profile.get('experience', [])
        if isinstance(experience, str):
            experience = json.loads(experience)
        
        education = user_profile.get('education', [])
        if isinstance(education, str):
            education = json.loads(education)
        
        # Parse certifications and projects
        certifications = user_profile.get('certifications', [])
        if isinstance(certifications, str):
            certifications = json.loads(certifications)
        
        projects = user_profile.get('projects', [])
        if isinstance(projects, str):
            projects = json.loads(projects)
        
        # Create contact info
        contact_info = {
            'name': user_profile.get('name', 'Puja Shrestha'),
            'email': user_profile.get('email', 'puja@example.com'),
            'phone': user_profile.get('phone', ''),
            'location': user_profile.get('preferred_location', 'Barrie, ON, Canada'),
            'linkedin': user_profile.get('linkedin', ''),
            'github': user_profile.get('github', '')
        }
        
        # Generate tailored professional summary
        job_title = job_data.get('title', 'Software Engineer')
        professional_summary = f"Results-driven AI/ML Engineer with 3 years of experience in {job_title.lower()} and related fields. Specialized in Python, Machine Learning, Deep Learning, NLP, and AI Agents. Proven track record of delivering production-grade AI solutions using PyTorch, TensorFlow, and modern LLM frameworks. Seeking to leverage expertise in a remote {job_title} role."
        
        # Extract job keywords and inject into skills
        job_keywords = self._extract_job_keywords(job_data)
        enhanced_skills = list(set(skills + [kw for kw in job_keywords if kw.lower() not in [s.lower() for s in skills]]))
        
        return TailoredResumeData(
            contact_info=contact_info,
            professional_summary=professional_summary,
            experience=experience or [],
            education=education or [],
            skills=enhanced_skills,
            certifications=certifications or [],
            projects=projects or [],
            keywords_injected=job_keywords
        )
    
    def _extract_job_keywords(self, job_data: Dict) -> List[str]:
        """Extract important keywords from job posting"""
        keywords = []
        
        # Extract from requirements
        requirements = job_data.get('requirements', '')
        if requirements:
            # Simple keyword extraction (in production, use NLP)
            common_tech = [
                'Python', 'PyTorch', 'TensorFlow', 'Machine Learning', 'Deep Learning',
                'NLP', 'LLM', 'AI', 'AWS', 'Docker', 'Kubernetes', 'REST API',
                'PostgreSQL', 'Redis', 'Git', 'CI/CD', 'Agile', 'RAG'
            ]
            
            requirements_lower = requirements.lower()
            for tech in common_tech:
                if tech.lower() in requirements_lower:
                    keywords.append(tech)
        
        # Extract from description
        description = job_data.get('description', '')
        if 'remote' in description.lower():
            keywords.append('Remote Work')
        
        return list(set(keywords))
    
    def _resume_to_dict(self, resume: GeneratedResume, job_data: Optional[Dict] = None) -> Dict:
        """Convert GeneratedResume to dictionary for CLI output"""
        return {
            'id': str(resume.id),
            'filename': resume.filename,
            'file_path': resume.file_path,
            'ats_score': resume.ats_score or 0.0,
            'keyword_match_rate': resume.keyword_match_rate or 0.0,
            'matched_keywords': resume.matched_keywords or [],
            'missing_keywords': resume.missing_keywords or [],
            'created_at': resume.created_at.isoformat(),
            'job_title': job_data.get('title', 'Unknown') if job_data else 'Unknown',
            'company': job_data.get('company', 'Unknown') if job_data else 'Unknown'
        }