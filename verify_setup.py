#!/usr/bin/env python3
"""
Verification script to check all components are working.
"""
import asyncio
import sys
from services.database import db
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def verify_database():
    """Verify PostgreSQL connection and schema."""
    try:
        await db.connect()
        
        # Check tables exist
        tables = await db.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        table_names = [t['table_name'] for t in tables]
        required_tables = ['raw_jobs', 'jobs', 'job_searches', 'rate_limits']
        
        for table in required_tables:
            if table in table_names:
                logger.info(f"Table '{table}' exists")
            else:
                logger.error(f"Table '{table}' missing!")
                return False
        
        await db.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

async def verify_redis():
    """Verify Redis connection."""
    try:
        import redis.asyncio as aioredis
        
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test set/get
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        
        if value == "test_value":
            logger.info("Redis connection working")
            await redis_client.delete("test_key")
            await redis_client.close()
            return True
        else:
            logger.error("Redis test failed")
            return False
            
    except Exception as e:
        logger.error(f"Redis verification failed: {e}")
        return False

async def main():
    """Run all verifications."""
    logger.info("Starting setup verification...\n")
    
    # Check configuration
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}\n")
    
    # Run checks
    db_ok = await verify_database()
    redis_ok = await verify_redis()
    
    # Summary
    logger.info("\n" + "="*50)
    if db_ok and redis_ok:
        logger.info("All systems operational!")
        logger.info("="*50)
        return 0
    else:
        logger.error("Some systems failed verification")
        logger.error("="*50)
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))