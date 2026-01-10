import pytest
import asyncio
from services.database import Database
from services.rate_limiter import RateLimiter, PlatformRateLimiter
from services.deduplicator import JobDeduplicator
from models.job import RawJob, Job, LocationType, EmploymentType
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_database_connection():
    """Test PostgreSQL connection."""
    db = Database()
    await db.connect()
    
    # Test query
    result = await db.fetchrow("SELECT 1 as test")
    assert result['test'] == 1
    
    await db.disconnect()
    logger.info("✅ Database connection test passed")

@pytest.mark.asyncio
async def test_rate_limiter():
    """Test rate limiter."""
    limiter = RateLimiter(requests_per_minute=60)  # 1 per second
    
    # Should allow first request immediately
    start = asyncio.get_event_loop().time()
    await limiter.acquire()
    elapsed = asyncio.get_event_loop().time() - start
    
    assert elapsed < 0.1  # Should be instant
    
    stats = limiter.get_stats()
    assert stats['requests_last_minute'] == 1
    
    logger.info("✅ Rate limiter test passed")

@pytest.mark.asyncio
async def test_job_model_validation():
    """Test Pydantic models."""
    raw_job = RawJob(
        platform="indeed",
        url="https://indeed.com/job/123",
        raw_data={
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": "Remote",
            "description": "Build amazing software"
        }
    )
    
    assert raw_job.platform == "indeed"
    assert len(raw_job.content_hash) == 64  # SHA256 hash
    
    logger.info("✅ Job model validation test passed")

@pytest.mark.asyncio
async def test_platform_rate_limiter():
    """Test platform-specific rate limiter."""
    limiter = PlatformRateLimiter(settings)
    
    # Test Indeed rate limiter
    await limiter.acquire("indeed")
    stats = limiter.get_stats()
    
    assert "indeed" in stats
    assert stats["indeed"]["requests_last_minute"] == 1
    
    logger.info("✅ Platform rate limiter test passed")

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])