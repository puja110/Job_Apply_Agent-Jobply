# agents/jsearch_agent.py
import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
import logging
import os

from agents.base import BaseJobAgent
from models.job import RawJob, Job, LocationType, EmploymentType
from models.search import JobSearchParams
from config.settings import settings

logger = logging.getLogger(__name__)

class JSearchAgent(BaseJobAgent):
    """Job search via JSearch API (RapidAPI) - aggregates Indeed, LinkedIn, etc."""
    
    API_URL = "https://jsearch.p.rapidapi.com/search"
    
    def __init__(self, rate_limiter, deduplicator, db_pool):
        super().__init__("jsearch", rate_limiter, deduplicator, db_pool)
        
        # Get API key from environment
        self.api_key = settings.RAPIDAPI_KEY
        if not self.api_key:
            raise ValueError(
                "RAPIDAPI_KEY not found in .env file. "
                "Please add: RAPIDAPI_KEY=your_key_here"
            )
        
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
        )
        
        logger.info("JSearch API agent initialized")
    
    async def _search_jobs(self, search_params: JobSearchParams) -> List[RawJob]:
        """Search using JSearch API."""
        logger.info(f"Searching JSearch API: {search_params.query} in {search_params.location}")
        
        await self.rate_limiter.acquire()
        
        # Build query string
        query_parts = [search_params.query]
        if search_params.location:
            query_parts.append(f"in {search_params.location}")
        
        query = " ".join(query_parts)
        
        # API parameters
        params = {
            "query": query,
            "page": "1",
            "num_pages": "1",  # Start with 1 page (10 results)
        }
        
        # Date filter
        date_map = {
            1: "today",
            3: "3days",
            7: "week",
            14: "week",  # No 2-week option, use week
            30: "month",
        }
        params["date_posted"] = date_map.get(search_params.posted_within_days, "week")
        
        # Remote filter
        if search_params.remote_only:
            params["remote_jobs_only"] = "true"
        
        # Employment type filter
        if search_params.employment_type:
            params["employment_types"] = search_params.employment_type.upper()
        
        logger.info(f"API Request: {self.API_URL} with params: {params}")
        
        try:
            response = await self.client.get(self.API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'OK':
                logger.error(f"API returned non-OK status: {data}")
                return []
            
            raw_jobs = []
            job_results = data.get('data', [])
            
            logger.info(f"API returned {len(job_results)} jobs")
            
            for idx, job_data in enumerate(job_results, 1):
                try:
                    # Log first job for debugging
                    if idx == 1:
                        logger.debug(f"Sample job data: {job_data}")
                    
                    # Build job URL (prefer apply link, fallback to Google link)
                    job_url = (
                        job_data.get('job_apply_link') or 
                        job_data.get('job_google_link') or
                        f"https://www.google.com/search?q={job_data.get('job_id')}"
                    )
                    
                    raw_job = RawJob(
                        platform="jsearch",
                        external_id=job_data.get('job_id'),
                        url=job_url,
                        raw_data={
                            'job_key': job_data.get('job_id'),
                            'title': job_data.get('job_title'),
                            'company': job_data.get('employer_name'),
                            'company_type': job_data.get('employer_company_type'),
                            'location': self._format_location(job_data),
                            'description': job_data.get('job_description'),
                            'snippet': (job_data.get('job_description') or '')[:500],
                            'posted_date': job_data.get('job_posted_at_datetime_utc'),
                            'url': job_url,
                            'apply_url': job_data.get('job_apply_link'),
                            'employment_type': job_data.get('job_employment_type'),
                            'is_remote': job_data.get('job_is_remote'),
                            'salary_min': job_data.get('job_min_salary'),
                            'salary_max': job_data.get('job_max_salary'),
                            'salary_currency': job_data.get('job_salary_currency'),
                            'salary_period': job_data.get('job_salary_period'),
                            'required_experience': job_data.get('job_required_experience'),
                            'required_skills': job_data.get('job_required_skills'),
                            'benefits': job_data.get('job_benefits'),
                            'job_publisher': job_data.get('job_publisher'),  # Indeed, LinkedIn, etc.
                        }
                    )
                    raw_jobs.append(raw_job)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse job {idx}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(raw_jobs)} jobs")
            return raw_jobs[:search_params.max_results]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"API HTTP error: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return []
    
    def _format_location(self, job_data: dict) -> str:
        """Format location from job data."""
        city = job_data.get('job_city')
        state = job_data.get('job_state')
        country = job_data.get('job_country')
        
        parts = [p for p in [city, state, country] if p]
        return ', '.join(parts) if parts else 'Remote'
    
    async def _normalize_job(self, raw_job: RawJob) -> Job:
        """Convert RawJob to normalized Job."""
        raw_data = raw_job.raw_data
        
        # Determine location type
        if raw_data.get('is_remote'):
            location_type = LocationType.REMOTE
        elif raw_data.get('location', '').lower() == 'remote':
            location_type = LocationType.REMOTE
        else:
            location_type = LocationType.ONSITE
        
        # Parse employment type
        emp_type_str = raw_data.get('employment_type', '').upper()
        emp_type_map = {
            'FULLTIME': EmploymentType.FULL_TIME,
            'PARTTIME': EmploymentType.PART_TIME,
            'CONTRACTOR': EmploymentType.CONTRACT,
            'INTERN': EmploymentType.INTERNSHIP,
        }
        employment_type = emp_type_map.get(emp_type_str)
        
        # Parse posted date - convert to naive UTC datetime
        posted_date = None
        if raw_data.get('posted_date'):
            try:
                # Parse ISO format datetime
                dt = datetime.fromisoformat(
                    raw_data['posted_date'].replace('Z', '+00:00')
                )
                # Convert to naive UTC (remove timezone info)
                if dt.tzinfo is not None:
                    # Convert to UTC then remove timezone
                    posted_date = dt.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    posted_date = dt
            except Exception as e:
                logger.debug(f"Failed to parse posted_date: {raw_data.get('posted_date')} - {e}")
                pass
        
        # Extract skills
        skills = raw_data.get('required_skills') or []
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        
        # Ensure salary_currency is always a string
        salary_currency = raw_data.get('salary_currency')
        if not salary_currency:
            salary_currency = 'USD'
        
        return Job(
            raw_job_id=None,
            title=raw_data['title'],
            company=raw_data['company'],
            location=raw_data.get('location'),
            location_type=location_type,
            description=raw_data.get('description', ''),
            salary_min=raw_data.get('salary_min'),
            salary_max=raw_data.get('salary_max'),
            salary_currency=salary_currency,
            salary_period=raw_data.get('salary_period'),
            employment_type=employment_type,
            posted_date=posted_date,  # Now timezone-naive
            platform='jsearch',
            platform_url=raw_data['url'],
            apply_url=raw_data.get('apply_url') or raw_data['url'],
            skills=skills[:20],
        )
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
        logger.info("JSearch API client closed")