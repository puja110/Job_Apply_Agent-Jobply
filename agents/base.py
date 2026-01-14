# agents/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
import logging
import asyncio
import json  # ADD THIS
from datetime import datetime

from models.job import RawJob, Job
from models.search import JobSearchParams, JobSearchResult, SearchStatus
from services.rate_limiter import RateLimiter
from services.deduplicator import JobDeduplicator
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

class BaseJobAgent(ABC):
    """Abstract base class for job discovery agents."""
    
    def __init__(
        self, 
        platform_name: str,
        rate_limiter: RateLimiter,
        deduplicator: JobDeduplicator,
        db_pool
    ):
        self.platform = platform_name
        self.rate_limiter = rate_limiter
        self.deduplicator = deduplicator
        self.db = db_pool
        
        logger.info(f"Initialized {self.platform} agent")
    
    async def search_and_store(
        self, 
        search_params: JobSearchParams
    ) -> JobSearchResult:
        """
        Main entry point: search for jobs and store results.
        """
        # Create search record
        search_id = await self._create_search_record(search_params)
        
        result = JobSearchResult(
            search_id=search_id,
            search_params=search_params,
            status=SearchStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        try:
            # Perform search
            raw_jobs = await self._search_jobs(search_params)
            result.results_count = len(raw_jobs)
            
            # Process and store jobs
            for idx, raw_job in enumerate(raw_jobs, 1):
                try:
                    # Check for duplicates
                    is_dup, existing_id = await self.deduplicator.is_duplicate(raw_job)
                    
                    if is_dup:
                        result.duplicate_jobs_count += 1
                        logger.debug(f"Job {idx}/{len(raw_jobs)} is duplicate: {raw_job.url}")
                        continue
                    
                    # Store raw job
                    raw_job_id = await self._store_raw_job(raw_job)
                    logger.debug(f"Stored raw job {idx}/{len(raw_jobs)}: {raw_job_id}")
                    
                    # Normalize and store processed job
                    job = await self._normalize_job(raw_job)
                    job.raw_job_id = raw_job_id
                    await self._store_job(job)
                    
                    result.new_jobs_count += 1
                    logger.info(f"Job {idx}/{len(raw_jobs)} inserted: {job.title} at {job.company}")
                    
                except Exception as e:
                    logger.error(
                        f"Error processing job {idx}/{len(raw_jobs)} - {raw_job.url}: {e}",
                        exc_info=True  # This shows full stack trace
                    )
                    # Don't increment any counter for failed jobs
                    continue
            
            result.status = SearchStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            result.status = SearchStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.utcnow()
        
        # Update search record
        await self._update_search_record(result)
        
        return result
    
    @abstractmethod
    async def _search_jobs(
        self, 
        search_params: JobSearchParams
    ) -> List[RawJob]:
        """Platform-specific job search implementation."""
        pass
    
    @abstractmethod
    async def _normalize_job(self, raw_job: RawJob) -> Job:
        """Platform-specific normalization logic."""
        pass
    
    async def _create_search_record(
        self, 
        search_params: JobSearchParams
    ) -> str:
        """Create initial search record in database."""
        # Convert Pydantic model to JSON-compatible dict
        filters = search_params.model_dump(
            exclude={'query', 'location', 'platform'}
        )
        
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO job_searches (
                    search_query, location, platform, filters, 
                    started_at, status
                )
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                RETURNING id
                """,
                search_params.query,
                search_params.location,
                self.platform,
                json.dumps(filters),  # Convert to JSON string
                datetime.utcnow(),
                SearchStatus.PENDING.value
            )
            return str(result['id'])
    
    async def _update_search_record(
        self, 
        result: JobSearchResult
    ) -> None:
        """Update search record with results."""
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE job_searches
                SET results_count = $1,
                    new_jobs_count = $2,
                    completed_at = $3,
                    status = $4,
                    error_message = $5
                WHERE id = $6
                """,
                result.results_count,
                result.new_jobs_count,
                result.completed_at,
                result.status.value,
                result.error_message,
                result.search_id
            )
    
    async def _store_raw_job(self, raw_job: RawJob) -> str:
        """Store raw job data."""
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO raw_jobs (
                    platform, external_id, url, raw_data, 
                    scraped_at, content_hash
                )
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                ON CONFLICT (platform, url) DO UPDATE
                SET raw_data = EXCLUDED.raw_data,
                    scraped_at = EXCLUDED.scraped_at
                RETURNING id
                """,
                raw_job.platform,
                raw_job.external_id,
                str(raw_job.url),
                json.dumps(raw_job.raw_data),  # Convert to JSON string
                raw_job.scraped_at,
                raw_job.content_hash
            )
            return str(result['id'])
    
    async def _store_job(self, job: Job) -> str:
        """Store normalized job."""
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                INSERT INTO jobs (
                    raw_job_id, title, company, location, location_type,
                    description, requirements, responsibilities,
                    salary_min, salary_max, salary_currency, salary_period,
                    employment_type, experience_level, posted_date, expires_date,
                    platform, platform_url, apply_url,
                    skills, keywords, processed_at, status
                )
                VALUES (
                    $1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20::jsonb, $21::jsonb, $22, $23
                )
                ON CONFLICT (platform, platform_url) DO UPDATE
                SET title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    last_updated = NOW()
                RETURNING id
                """,
                job.raw_job_id, job.title, job.company, job.location,
                job.location_type.value if job.location_type else None,
                job.description, job.requirements, job.responsibilities,
                job.salary_min, job.salary_max, job.salary_currency,
                job.salary_period,
                job.employment_type.value if job.employment_type else None,
                job.experience_level.value if job.experience_level else None,
                job.posted_date, job.expires_date,
                job.platform, str(job.platform_url), 
                str(job.apply_url) if job.apply_url else None,
                json.dumps(job.skills),  # Convert list to JSON
                json.dumps(job.keywords),  # Convert list to JSON
                job.processed_at, job.status
            )
            return str(result['id'])