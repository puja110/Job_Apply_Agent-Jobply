"""
Check table schema and generate resume for real job from database
"""
import asyncio
from uuid import UUID
from database.connection import Database
from services.resume_service import ResumeService
from repositories.resume_repository import ResumeRepository
from services.pdf_generator import PDFGenerator

async def check_schema_and_generate():
    db = Database()
    await db.connect()
    
    try:
        # First, check the jobs table schema
        print("Checking jobs table schema...")
        schema_query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'jobs'
            ORDER BY ordinal_position;
        """
        
        async with db.pool.acquire() as conn:
            columns = await conn.fetch(schema_query)
        
        print("\nJobs table columns:")
        for col in columns:
            print(f"  - {col['column_name']} ({col['data_type']})")
        
        # Your actual user ID
        user_id = UUID("24e93fba-fe4e-4b2c-a76e-4a48028b9e0b")
        print(f"\nUser: Puja Shrestha")
        print(f"ID: {user_id}")
        
        # Get your top scored job with correct column names
        query = """
            SELECT 
                j.id, 
                j.title, 
                j.company, 
                j.location,
                j.description,
                j.skills,
                j.keywords,
                js.total_score,
                js.skill_match_score,
                js.salary_score,
                js.location_score,
                js.matched_skills,
                js.missing_skills
            FROM jobs j
            JOIN job_scores js ON j.id = js.job_id
            WHERE js.user_profile_id = $1
            ORDER BY js.total_score DESC
            LIMIT 1
        """
        
        async with db.pool.acquire() as conn:
            job = await conn.fetchrow(query, user_id)
        
        if not job:
            print("\nNo jobs found!")
            return
        
        print(f"\nTop Job Found:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Total Score: {job['total_score']:.2f}%")
        print(f"  Skill Match: {job['skill_match_score']:.2f}%")
        print(f"  Salary Score: {job['salary_score']:.2f}%")
        print(f"  Location Score: {job['location_score']:.2f}%")
        
        print(f"\nGenerating tailored resume...")
        
        # Generate resume - ResumeService creates its own repository and pdf_generator
        resume_service = ResumeService(db.pool)
        
        result = await resume_service.generate_resume_for_job(
            user_profile_id=user_id,
            job_id=job['id']
        )
        
        print(f"\nResume Generated Successfully!")
        print("=" * 80)
        print(f"File Details:")
        print(f"  Path: {result['file_path']}")
        print(f"  Job: {result['job_title']} at {result['company']}")
        
        print(f"\nATS Scores:")
        print(f"  Overall Score: {result['ats_score']:.1f}%")
        print(f"  Keyword Match: {result['keyword_match_rate']:.1f}%")
        
        print(f"\nMatched Keywords ({len(result['matched_keywords'])}):")
        for i, kw in enumerate(result['matched_keywords'][:15], 1):
            print(f"  {i:2d}. {kw}")
        
        if result['missing_keywords']:
            print(f"\nMissing Keywords ({len(result['missing_keywords'])}):")
            for i, kw in enumerate(result['missing_keywords'][:10], 1):
                print(f"  {i:2d}. {kw}")
        
        print(f"\n" + "=" * 80)
        print(f"Next Steps:")
        print(f"  1. Open and review: {result['file_path']}")
        print(f"  2. Generate for more jobs:")
        print(f"     python cli/generate_resumes.py generate-batch \\")
        print(f"       --user-id {user_id} \\")
        print(f"       --min-score 50 \\")
        print(f"       --limit 10")
        print(f"  3. Check database: SELECT * FROM generated_resumes;")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_schema_and_generate())
