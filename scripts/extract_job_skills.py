"""
Extract and update skills for all jobs in database
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Database
from services.skill_extractor import get_skill_extractor
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract_and_update_skills():
    """Extract skills from job descriptions and update database"""
    
    db = Database()
    await db.connect()
    
    skill_extractor = get_skill_extractor()
    
    try:
        # Fetch all jobs
        jobs = await db.fetch("""
            SELECT id, title, description, skills
            FROM jobs
            ORDER BY processed_at DESC
        """)
        
        logger.info(f"Found {len(jobs)} jobs to process")
        
        updated_count = 0
        
        for job in jobs:
            # Extract skills from title + description
            text = f"{job['title']}. {job['description'] or ''}"
            extracted_skills = skill_extractor.extract_skills(text, max_skills=30)
            
            if not extracted_skills:
                logger.warning(f"No skills extracted for job {job['id']}")
                continue
            
            # Update job with extracted skills
            await db.execute("""
                UPDATE jobs
                SET skills = $1
                WHERE id = $2
            """, json.dumps(extracted_skills), job['id'])
            
            updated_count += 1
            logger.info(f"Updated job {job['id']}: {job['title']}")
            logger.info(f"  Extracted {len(extracted_skills)} skills: {', '.join(extracted_skills[:10])}")
            if len(extracted_skills) > 10:
                logger.info(f"  ... and {len(extracted_skills) - 10} more")
        
        logger.info(f"\n Successfully updated {updated_count}/{len(jobs)} jobs")
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(extract_and_update_skills())