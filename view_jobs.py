# view_jobs.py
import asyncio
import sys
from services.database import db
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def view_jobs(limit=10, platform=None):
    """View jobs from database with detailed formatting."""
    await db.connect()
    
    # Build query
    where_clause = "WHERE j.platform = $1" if platform else ""
    params = [platform] if platform else []
    
    query = f"""
        SELECT 
            j.id,
            j.title, 
            j.company, 
            j.location,
            j.location_type,
            j.employment_type,
            j.salary_min,
            j.salary_max,
            j.salary_currency,
            j.salary_period,
            j.description,
            j.platform_url,
            j.apply_url,
            j.posted_date,
            j.skills,
            j.platform,
            j.processed_at,
            rj.raw_data->>'job_publisher' as source
        FROM jobs j
        LEFT JOIN raw_jobs rj ON j.raw_job_id = rj.id
        {where_clause}
        ORDER BY j.processed_at DESC 
        LIMIT {limit}
    """
    
    jobs = await db.fetch(query, *params) if params else await db.fetch(query)
    
    print("\n" + "="*80)
    print(f"FOUND {len(jobs)} JOBS")
    print("="*80)
    
    if not jobs:
        print("\nNo jobs found in database.")
        print("Run: python main.py to search for jobs first.\n")
        await db.disconnect()
        return
    
    for idx, job in enumerate(jobs, 1):
        print(f"\n{'='*80}")
        print(f"JOB #{idx}")
        print(f"{'='*80}")
        print(f"Title:        {job['title']}")
        print(f"Company:      {job['company']}")
        print(f"Location:     {job['location']} ({job['location_type'] or 'N/A'})")
        print(f"Type:         {job['employment_type'] or 'Not specified'}")
        print(f"Platform:     {job['platform']}")
        
        # Salary info
        if job['salary_min'] and job['salary_max']:
            print(f"Salary:       ${job['salary_min']:,} - ${job['salary_max']:,} {job['salary_currency']}")
            if job['salary_period']:
                print(f"              ({job['salary_period']})")
        elif job['salary_min']:
            print(f"Salary:       ${job['salary_min']:,}+ {job['salary_currency']}")
        else:
            print(f"Salary:       Not disclosed")
        
        # Skills
        if job['skills']:
            skills = job['skills'] if isinstance(job['skills'], list) else []
            if skills:
                print(f"Skills:       {', '.join(skills[:7])}")
                if len(skills) > 7:
                    print(f"              + {len(skills) - 7} more skills")
        
        # URLs
        print(f"Source:       {job['source'] or 'Unknown'}")
        print(f"Posted:       {job['posted_date'] or 'Unknown'}")
        print(f"Scraped:      {job['processed_at']}")
        print(f"Apply URL:    {job['apply_url'][:70]}...")
        
        # Description preview
        if job['description']:
            # Clean and truncate description
            desc = job['description'][:400].replace('\n', ' ').replace('\r', '')
            print(f"\nDescription:")
            print(f"  {desc}...")
        
        print(f"{'='*80}")
    
    await db.disconnect()

if __name__ == "__main__":
    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description='View jobs from database')
    parser.add_argument('--limit', type=int, default=10, help='Number of jobs to display')
    parser.add_argument('--platform', type=str, help='Filter by platform (e.g., jsearch)')
    
    args = parser.parse_args()
    
    asyncio.run(view_jobs(limit=args.limit, platform=args.platform))