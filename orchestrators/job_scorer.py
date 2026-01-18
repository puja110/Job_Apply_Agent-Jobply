"""
Job Scoring Orchestrator
Coordinates the job scoring pipeline: fetch jobs, score them, store results
"""
import asyncio
import json
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import logging

from database.connection import Database
from services.scoring_engine import ScoringEngine
from services.embeddings import EmbeddingService
from models.user_profile import UserProfile
from models.job import Job
from models.scoring import JobScore

logger = logging.getLogger(__name__)


class JobScoringOrchestrator:
    """Orchestrates the job scoring workflow"""
    
    def __init__(self, db: Database):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.scoring_engine = ScoringEngine(self.embedding_service)
    
    async def score_all_jobs(
        self, 
        user_profile: UserProfile,
        job_ids: Optional[List[UUID]] = None,
        rescore: bool = False
    ) -> List[JobScore]:
        """
        Score all jobs (or specific job IDs) for a user profile
        
        Args:
            user_profile: User's profile with skills, preferences, etc.
            job_ids: Optional list of specific job IDs to score
            rescore: If True, rescore even if scores already exist
            
        Returns:
            List of JobScore objects
        """
        logger.info(f"Starting job scoring for profile: {user_profile.name}")
        
        # 1. Fetch jobs from database
        jobs = await self._fetch_jobs(job_ids, rescore)
        
        if not jobs:
            logger.warning("No jobs found to score")
            return []
        
        logger.info(f"Found {len(jobs)} jobs to score")
        
        # 2. Score each job
        scored_jobs = []
        for job in jobs:
            try:
                score = await self.scoring_engine.score_job(job, user_profile)
                scored_jobs.append(score)
                logger.debug(f"Scored job {job.id}: {score.overall_score:.2f}")
            except Exception as e:
                logger.error(f"Error scoring job {job.id}: {e}")
                continue
        
        # 3. Store scores in database
        await self._store_scores(scored_jobs, user_profile.id)
        
        # 4. Sort by overall score (descending)
        scored_jobs.sort(key=lambda x: x.overall_score, reverse=True)
        
        logger.info(f"Successfully scored {len(scored_jobs)} jobs")
        return scored_jobs
    
    async def _fetch_jobs(
    self, 
    job_ids: Optional[List[UUID]], 
    rescore: bool
    ) -> List[Job]:
        """Fetch jobs from database that need scoring"""
        
        if job_ids:
            # Score specific jobs
            query = """
                SELECT 
                    j.id, j.title, j.company, j.location, j.location_type,
                    j.employment_type, j.salary_min, j.salary_max, 
                    j.salary_currency, j.salary_period, j.description,
                    j.platform, j.platform_url, j.posted_date, j.skills
                FROM jobs j
                WHERE j.id = ANY($1)
                ORDER BY j.processed_at DESC
            """
            rows = await self.db.fetch(query, job_ids)
        elif rescore:
            # Rescore all jobs
            query = """
                SELECT 
                    j.id, j.title, j.company, j.location, j.location_type,
                    j.employment_type, j.salary_min, j.salary_max, 
                    j.salary_currency, j.salary_period, j.description,
                    j.platform, j.platform_url, j.posted_date, j.skills
                FROM jobs j
                ORDER BY j.processed_at DESC
            """
            rows = await self.db.fetch(query)
        else:
            # Score only unscored jobs
            query = """
                SELECT 
                    j.id, j.title, j.company, j.location, j.location_type,
                    j.employment_type, j.salary_min, j.salary_max, 
                    j.salary_currency, j.salary_period, j.description,
                    j.platform, j.platform_url, j.posted_date, j.skills
                FROM jobs j
                LEFT JOIN job_scores js ON j.id = js.job_id
                WHERE js.id IS NULL
                ORDER BY j.processed_at DESC
            """
            rows = await self.db.fetch(query)
        
        # Convert to Job objects
        jobs = []
        for row in rows:
            try:
                # Parse skills if it's JSONB
                skills = row['skills']
                if isinstance(skills, str):
                    skills = json.loads(skills)
                elif not isinstance(skills, list):
                    skills = []
                
                job = Job(
                    id=str(row['id']),  # Convert UUID to string
                    title=row['title'],
                    company=row['company'],
                    location=row['location'],
                    location_type=row['location_type'],
                    employment_type=row['employment_type'],
                    salary_min=row['salary_min'],
                    salary_max=row['salary_max'],
                    salary_currency=row['salary_currency'],
                    salary_period=row['salary_period'],
                    description=row['description'],
                    platform=row['platform'],  # Added
                    platform_url=row['platform_url'],  # Changed from apply_url
                    apply_url=row['platform_url'],  # Keep for compatibility
                    posted_date=row['posted_date'],
                    skills=skills,
                    source=None
                )
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error converting row to Job: {e}")
                continue
        
        return jobs
    
    async def _store_scores(self, scored_jobs: List[JobScore], profile_id: UUID):
        """Store job scores in database"""
        
        for score in scored_jobs:
            try:
                # Check if score already exists
                existing = await self.db.fetchrow(
                    "SELECT id FROM job_scores WHERE job_id = $1 AND user_profile_id = $2",
                    score.job_id, profile_id
                )
                
                if existing:
                    # Update existing score
                    await self.db.execute("""
                        UPDATE job_scores SET
                            total_score = $1,
                            skill_match_score = $2,
                            salary_score = $3,
                            location_score = $4,
                            company_score = $5,
                            success_probability_score = $6,
                            score_explanation = $7,
                            scored_at = NOW()
                        WHERE job_id = $8 AND user_profile_id = $9
                    """, 
                        score.overall_score,
                        score.skill_score,
                        score.salary_score,
                        score.location_score,
                        score.company_score,
                        score.success_score,
                        score.explanation,
                        score.job_id,
                        profile_id
                    )
                    logger.debug(f"Updated score for job {score.job_id}")
                else:
                    # Insert new score
                    await self.db.execute("""
                        INSERT INTO job_scores (
                            job_id, user_profile_id, total_score,
                            skill_match_score, salary_score, location_score,
                            company_score, success_probability_score, score_explanation
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                        score.job_id,
                        profile_id,
                        score.overall_score,
                        score.skill_score,
                        score.salary_score,
                        score.location_score,
                        score.company_score,
                        score.success_score,
                        score.explanation
                    )
                    logger.debug(f"Inserted score for job {score.job_id}")
                    
            except Exception as e:
                logger.error(f"Error storing score for job {score.job_id}: {e}")
                continue


async def main():
    """Load profile and score jobs"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    db = Database()
    await db.connect()
    
    try:
        # Load the active user profile
        profile_row = await db.fetchrow("""
            SELECT 
                id, name, email, skills, years_of_experience, experience_level,
                target_salary_min, target_salary_max, target_salary_currency,
                preferred_location, remote_preference, willing_to_relocate,
                preferred_company_sizes, preferred_industries
            FROM user_profile
            WHERE is_active = TRUE
            LIMIT 1
        """)
        
        if not profile_row:
            print("No active user profile found. Run: python -m scripts.create_profile")
            return
        
        # Parse JSONB fields
        skills = json.loads(profile_row['skills']) if isinstance(profile_row['skills'], str) else profile_row['skills']
        company_sizes = json.loads(profile_row['preferred_company_sizes']) if isinstance(profile_row['preferred_company_sizes'], str) else profile_row['preferred_company_sizes']
        industries = json.loads(profile_row['preferred_industries']) if isinstance(profile_row['preferred_industries'], str) else profile_row['preferred_industries']
        
        user_profile = UserProfile(
            id=profile_row['id'],
            name=profile_row['name'],
            email=profile_row['email'],
            skills=skills,
            years_of_experience=profile_row['years_of_experience'],
            experience_level=profile_row['experience_level'],
            target_salary_min=profile_row['target_salary_min'],
            target_salary_max=profile_row['target_salary_max'],
            target_salary_currency=profile_row['target_salary_currency'],
            preferred_location=profile_row['preferred_location'],
            remote_preference=profile_row['remote_preference'],
            willing_to_relocate=profile_row['willing_to_relocate'],
            preferred_company_sizes=company_sizes,
            preferred_industries=industries
        )
        
        print(f"\nLoaded profile: {user_profile.name}")
        print(f"   Skills: {len(user_profile.skills)} skills")
        print(f"   Target salary: ${user_profile.target_salary_min:,} - ${user_profile.target_salary_max:,}")
        print(f"   Location preference: {user_profile.preferred_location} ({user_profile.remote_preference})")
        
        # Create orchestrator and score jobs
        orchestrator = JobScoringOrchestrator(db)
        scored_jobs = await orchestrator.score_all_jobs(
            user_profile=user_profile,
            rescore=False  # Only score new jobs
        )
        
        if not scored_jobs:
            print("\nNo jobs to score. Run: python main.py to fetch jobs first.")
            return
        
        # Display top 5
        print("\n" + "="*80)
        print(f"TOP 5 MATCHED JOBS")
        print("="*80)
        
        for i, score in enumerate(scored_jobs[:5], 1):
            print(f"\n{i}. {score.job.title} at {score.job.company}")
            print(f"   Overall Score: {score.overall_score:.1f}/100")
            print(f"   {score.explanation}")
            print(f"   Location: {score.job.location} ({score.job.location_type})")
            if score.job.salary_min and score.job.salary_max:
                print(f"   Salary: ${score.job.salary_min:,} - ${score.job.salary_max:,}")
        
        print("\n" + "="*80)
        print(f"\nScored {len(scored_jobs)} jobs successfully!")
        print(f"   Run: python view_jobs.py to view all ranked jobs")
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())