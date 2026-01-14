# main.py
import asyncio
import sys
from services.database import db
from services.rate_limiter import PlatformRateLimiter
from services.deduplicator import JobDeduplicator
from agents.jsearch_agent import JSearchAgent
from models.search import JobSearchParams
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_jsearch():
    """Test Indeed agent with a sample search."""
    
    # Initialize database
    await db.connect()
    
    # Initialize services
    rate_limiter = PlatformRateLimiter(settings)
    deduplicator = JobDeduplicator(db)
    
    # Initialize Indeed agent
    jsearch_agent = JSearchAgent(
        rate_limiter=rate_limiter.limiters['indeed'],
        deduplicator=deduplicator,
        db_pool=db
    )
    
    try:
        # Define search parameters
        search_params = JobSearchParams(
            query="AI Engineer",
            location="Canada",
            platform="jsearch",
            remote_only=False,
            posted_within_days=1,
            max_results=20
        )
        
        logger.info(f"Starting job search: {search_params.query}")
        logger.info("="*60)
        
        # Execute search
        result = await jsearch_agent.search_and_store(search_params)
        
        # Display results
        logger.info("="*60)
        logger.info(f"Search Status: {result.status.value}")
        logger.info(f"Total Results: {result.results_count}")
        logger.info(f"New Jobs: {result.new_jobs_count}")
        logger.info(f"Duplicates: {result.duplicate_jobs_count}")
        logger.info(f"Duration: {(result.completed_at - result.started_at).total_seconds():.2f}s")

        if result.error_message:
            logger.error(f"Error: {result.error_message}")
        
        # Fetch and display some jobs from database
        jobs = await db.fetch("""
            SELECT id, title, company, location, posted_date, platform_url 
            FROM jobs 
            WHERE platform = 'jsearch'
            ORDER BY posted_date DESC 
            LIMIT 10
        """)
        
        logger.info("\n" + "="*60)
        logger.info("Sample Jobs Stored:")
        logger.info("="*60)
        for job in jobs:
            logger.info(f"✓ {job['title']} at {job['company']} ({job['location']})")
            logger.info(f"  URL: {job['platform_url']}\n")
        
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return 1
    
    finally:
        await jsearch_agent.close()
        await db.disconnect()
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(test_jsearch()))