# services/deduplicator.py
import hashlib
from difflib import SequenceMatcher
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class JobDeduplicator:
    """Detect duplicate jobs using multiple strategies."""
    
    def __init__(self, db_pool):
        self.db = db_pool
        
    async def is_duplicate(self, raw_job: 'RawJob') -> tuple[bool, Optional[str]]:
        """
        Check if job is duplicate.
        Returns: (is_duplicate, existing_job_id)
        """
        # Strategy 1: Exact URL match
        existing = await self._check_url_duplicate(
            raw_job.platform, 
            str(raw_job.url)
        )
        if existing:
            logger.info(f"Duplicate found by URL: {raw_job.url}")
            return True, existing
        
        # Strategy 2: Content hash match
        existing = await self._check_content_hash_duplicate(
            raw_job.content_hash
        )
        if existing:
            logger.info(f"Duplicate found by content hash: {raw_job.url}")
            return True, existing
        
        # Strategy 3: Fuzzy matching (expensive, only for recent jobs)
        existing = await self._check_fuzzy_duplicate(raw_job)
        if existing:
            logger.info(f"Duplicate found by fuzzy match: {raw_job.url}")
            return True, existing
        
        return False, None
    
    async def _check_url_duplicate(
        self, 
        platform: str, 
        url: str
    ) -> Optional[str]:
        """Check for exact URL match."""
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id FROM raw_jobs 
                WHERE platform = $1 AND url = $2
                LIMIT 1
                """,
                platform, url
            )
            return result['id'] if result else None
    
    async def _check_content_hash_duplicate(
        self, 
        content_hash: str
    ) -> Optional[str]:
        """Check for content hash match."""
        async with self.db.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT id FROM raw_jobs 
                WHERE content_hash = $1
                LIMIT 1
                """,
                content_hash
            )
            return result['id'] if result else None
    
    async def _check_fuzzy_duplicate(
        self, 
        raw_job: 'RawJob',
        similarity_threshold: float = 0.90
    ) -> Optional[str]:
        """
        Check for fuzzy duplicates among recent jobs.
        Only compare against jobs from last 7 days to limit overhead.
        """
        title = raw_job.raw_data.get('title', '').lower()
        company = raw_job.raw_data.get('company', '').lower()
        
        if not title or not company:
            return None
        
        async with self.db.acquire() as conn:
            # Get recent jobs from same company
            recent_jobs = await conn.fetch(
                """
                SELECT id, raw_data FROM raw_jobs
                WHERE platform = $1
                  AND raw_data->>'company' ILIKE $2
                  AND scraped_at > NOW() - INTERVAL '7 days'
                LIMIT 50
                """,
                raw_job.platform,
                f"%{company}%"
            )
            
            for job in recent_jobs:
                existing_title = job['raw_data'].get('title', '').lower()
                similarity = SequenceMatcher(
                    None, 
                    title, 
                    existing_title
                ).ratio()
                
                if similarity >= similarity_threshold:
                    logger.debug(
                        f"Fuzzy match: {similarity:.2f} - "
                        f"'{title}' vs '{existing_title}'"
                    )
                    return job['id']
        
        return None