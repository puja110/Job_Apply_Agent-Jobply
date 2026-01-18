"""
View jobs from database with scores and rankings
"""
import asyncio
import argparse
from datetime import datetime
from typing import Optional

from database.connection import Database


async def view_jobs(
    limit: int = 10, 
    platform: Optional[str] = None,
    min_score: Optional[float] = None,
    show_unscored: bool = False
):
    """
    View jobs from database with optional filters
    
    Args:
        limit: Number of jobs to display
        platform: Filter by platform (e.g., 'jsearch')
        min_score: Minimum overall score to display
        show_unscored: If True, show jobs without scores
    """
    db = Database()
    await db.connect()
    
    # Build query based on filters
    conditions = []
    params = []
    param_counter = 1
    
    if platform:
        conditions.append(f"j.platform = ${param_counter}")
        params.append(platform)
        param_counter += 1
    
    if min_score is not None:
        conditions.append(f"js.total_score >= ${param_counter}")
        params.append(min_score)
        param_counter += 1
    
    where_clause = " AND " + " AND ".join(conditions) if conditions else ""
    
    # Choose query based on whether to show unscored jobs
    if show_unscored:
        query = f"""
            SELECT 
                j.id, j.title, j.company, j.location, j.location_type,
                j.employment_type, j.salary_min, j.salary_max, 
                j.salary_currency, j.salary_period, j.description,
                j.platform, j.platform_url, j.posted_date, j.skills,
                js.total_score, js.skill_match_score, js.salary_score,
                js.location_score, js.company_score, js.success_probability_score,
                js.score_explanation
            FROM jobs j
            LEFT JOIN job_scores js ON j.id = js.job_id
            WHERE 1=1 {where_clause}
            ORDER BY 
                CASE WHEN js.total_score IS NOT NULL 
                     THEN js.total_score 
                     ELSE 0 
                END DESC,
                j.processed_at DESC
            LIMIT ${param_counter}
        """
    else:
        # Only show scored jobs
        query = f"""
            SELECT 
                j.id, j.title, j.company, j.location, j.location_type,
                j.employment_type, j.salary_min, j.salary_max, 
                j.salary_currency, j.salary_period, j.description,
                j.platform, j.platform_url, j.posted_date, j.skills,
                js.total_score, js.skill_match_score, js.salary_score,
                js.location_score, js.company_score, js.success_probability_score,
                js.score_explanation
            FROM jobs j
            INNER JOIN job_scores js ON j.id = js.job_id
            WHERE 1=1 {where_clause}
            ORDER BY js.total_score DESC, j.processed_at DESC
            LIMIT ${param_counter}
        """
    
    params.append(limit)
    jobs = await db.fetch(query, *params)
    
    # Display results
    print("\n" + "="*80)
    if jobs:
        scored_count = sum(1 for j in jobs if j['total_score'] is not None)
        print(f"FOUND {len(jobs)} JOBS ({scored_count} scored)")
    else:
        print(f"FOUND 0 JOBS")
    print("="*80)
    
    if not jobs:
        print("\nNo jobs found in database.")
        print("Run: python main.py to search for jobs first.")
        print("Then: python -m orchestrators.job_scorer to score them.")
        await db.disconnect()
        return
    
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}] ", end="")
        
        # Score badge
        if job['total_score'] is not None:
            score = job['total_score']
            if score >= 80:
                badge = f"🟢 {score:.1f}"
            elif score >= 60:
                badge = f"🟡 {score:.1f}"
            else:
                badge = f"🔴 {score:.1f}"
            print(f"{badge}/100 - ", end="")
        else:
            print("⚪ NOT SCORED - ", end="")
        
        # Job title and company
        print(f"{job['title']} at {job['company']}")
        print(f"{'─'*80}")
        
        # Location and type
        location_display = job['location'] or "Unknown"
        if job['location_type']:
            location_display += f" ({job['location_type']})"
        print(f"Location:     {location_display}")
        
        if job['employment_type']:
            print(f"Type:         {job['employment_type']}")
        
        # Salary
        if job['salary_min'] and job['salary_max']:
            currency = job['salary_currency'] or 'USD'
            period = job['salary_period'] or 'year'
            print(f"Salary:       {currency} ${job['salary_min']:,} - ${job['salary_max']:,} per {period}")
        
        # Score breakdown (if available)
        if job['total_score'] is not None:
            print(f"\nScore Breakdown:")
            print(f"  Skills:      {job['skill_match_score']:.1f}/100")
            print(f"  Salary:      {job['salary_score']:.1f}/100")
            print(f"  Location:    {job['location_score']:.1f}/100")
            print(f"  Company:     {job['company_score']:.1f}/100")
            print(f"  Success:     {job['success_probability_score']:.1f}/100")
            
            if job['score_explanation']:
                print(f"\n  {job['score_explanation']}")
        
        # Skills
        if job['skills']:
            # Handle JSONB skills
            skills = job['skills']
            if isinstance(skills, str):
                import json
                try:
                    skills = json.loads(skills)
                except:
                    skills = []
            
            if isinstance(skills, list) and skills:
                print(f"\nSkills:       {', '.join(skills[:7])}")
                if len(skills) > 7:
                    print(f"              + {len(skills) - 7} more skills")
        
        # URLs
        print(f"\nPlatform:     {job['platform'] or 'Unknown'}")
        print(f"Posted:       {job['posted_date'] or 'Unknown'}")
        if job['platform_url']:
            url_display = job['platform_url'][:70] + "..." if len(job['platform_url']) > 70 else job['platform_url']
            print(f"Apply URL:    {url_display}")
        
        # Description preview
        if job['description']:
            desc = job['description'][:300].replace('\n', ' ').replace('\r', '')
            print(f"\nDescription:")
            print(f"  {desc}...")
        
        print(f"{'='*80}")
    
    await db.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='View jobs from database with scores')
    parser.add_argument('--limit', type=int, default=10, 
                       help='Number of jobs to display (default: 10)')
    parser.add_argument('--platform', type=str, 
                       help='Filter by platform (e.g., jsearch)')
    parser.add_argument('--min-score', type=float, 
                       help='Minimum overall score (0-100)')
    parser.add_argument('--show-unscored', action='store_true',
                       help='Include jobs without scores')
    
    args = parser.parse_args()
    
    asyncio.run(view_jobs(
        limit=args.limit,
        platform=args.platform,
        min_score=args.min_score,
        show_unscored=args.show_unscored
    ))