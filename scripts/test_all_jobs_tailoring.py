"""
Test Resume Tailoring Across All Jobs
Generate tailored resumes for all scored jobs and analyze results
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Database
from services.resume_tailoring import ResumeTailoringService
from models.resume import BaseResume, WorkExperience, Education, Project
from models.user_profile import UserProfile
from models.job import Job
import json
import logging
from typing import List, Dict

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


def create_sample_base_resume() -> BaseResume:
    """Create a sample base resume for testing"""
    
    return BaseResume(
        full_name="Puja Shrestha",
        email="puja@example.com",
        phone="+1 (555) 123-4567",
        location="Barrie, Ontario, Canada",
        linkedin="linkedin.com/in/pujashrestha",
        github="github.com/pujashrestha",
        
        summary="""Experienced software engineer with strong expertise in machine learning, 
        artificial intelligence, and full-stack development. Proven track record of building 
        scalable AI systems and delivering high-impact solutions. Passionate about leveraging 
        cutting-edge technology to solve real-world problems.""",
        
        technical_skills={
            "Languages": ["Python", "JavaScript", "TypeScript", "SQL"],
            "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "LLM", "RAG", "AI Agents"],
            "Frameworks": ["FastAPI", "React", "Angular.js", "Node.js", "Django", "Flask"],
            "Cloud & DevOps": ["AWS", "Docker", "PostgreSQL", "Redis", "Kubernetes"],
            "Tools": ["Git", "REST APIs", "CI/CD", "Prompt Engineering"]
        },
        
        work_experience=[
            WorkExperience(
                company="Tech Innovations Inc.",
                position="Machine Learning Engineer",
                location="Toronto, ON",
                start_date="Jan 2022",
                end_date="Present",
                description="Lead ML engineer developing AI-powered solutions including LLM applications, RAG systems, and AI agents for enterprise clients",
                achievements=[
                    "Built and deployed 5+ machine learning models serving 100K+ daily users",
                    "Developed AI agents and multi-agent systems for workflow automation",
                    "Implemented RAG pipelines for context-aware LLM applications",
                    "Improved model accuracy by 25% through advanced feature engineering",
                    "Reduced inference latency by 40% using model optimization techniques",
                    "Mentored 3 junior engineers in ML best practices"
                ],
                technologies=["Python", "PyTorch", "TensorFlow", "LLM", "RAG", "AI Agents", "AWS", "Docker", "FastAPI"]
            ),
            WorkExperience(
                company="DataCorp Solutions",
                position="Software Engineer",
                location="Remote",
                start_date="Jun 2020",
                end_date="Dec 2021",
                description="Full-stack engineer building data-intensive web applications and automation solutions",
                achievements=[
                    "Developed RESTful APIs serving 50K+ requests per day",
                    "Designed and implemented PostgreSQL database schemas for high-performance queries",
                    "Built responsive React dashboards for data visualization",
                    "Implemented CI/CD pipelines reducing deployment time by 60%",
                    "Created automation tools using Python and Docker"
                ],
                technologies=["JavaScript", "React", "Node.js", "PostgreSQL", "Python", "AWS", "Docker", "REST APIs"]
            ),
            WorkExperience(
                company="Startup Labs",
                position="Junior Developer",
                location="Barrie, ON",
                start_date="Jan 2019",
                end_date="May 2020",
                description="Software developer working on web applications, automation tools, and generative AI prototypes",
                achievements=[
                    "Developed automation scripts reducing manual work by 70%",
                    "Built internal tools used by 20+ team members daily",
                    "Experimented with generative AI for content creation",
                    "Collaborated with cross-functional teams in Agile environment"
                ],
                technologies=["Python", "Django", "JavaScript", "MongoDB", "Generative AI"]
            )
        ],
        
        education=[
            Education(
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                location="Toronto, ON",
                graduation_date="May 2018",
                gpa=3.7,
                honors=["Dean's List", "Academic Excellence Award"],
                relevant_coursework=[
                    "Machine Learning",
                    "Artificial Intelligence",
                    "Data Structures & Algorithms",
                    "Database Systems"
                ]
            )
        ],
        
        projects=[
            Project(
                name="AI Job Application Assistant",
                description="Multi-agent AI system that automates job searching, resume tailoring, and application tracking using LLMs, RAG, and semantic search",
                technologies=["Python", "LLM", "RAG", "AI Agents", "PostgreSQL", "FastAPI", "OpenAI"],
                achievements=[
                    "Implemented semantic job matching with 85% accuracy",
                    "Automated resume generation for 100+ applications",
                    "Reduced job search time by 80%"
                ],
                date="2024"
            ),
            Project(
                name="Real-time Sentiment Analysis Platform",
                description="Built a scalable system for analyzing social media sentiment using deep learning and transformers",
                technologies=["Python", "PyTorch", "BERT", "NLP", "Redis", "Docker", "AWS"],
                achievements=[
                    "Processed 1M+ tweets per day with 92% accuracy",
                    "Deployed using microservices architecture",
                    "Implemented real-time dashboard for insights"
                ],
                date="2023"
            ),
            Project(
                name="Smart Recommendation Engine",
                description="Collaborative filtering system for personalized product recommendations using machine learning",
                technologies=["Python", "TensorFlow", "Machine Learning", "PostgreSQL", "FastAPI"],
                achievements=[
                    "Increased click-through rate by 35%",
                    "Served 10K+ recommendations per minute"
                ],
                date="2022"
            )
        ],
        
        certifications=[],
        publications=[],
        awards=[],
        volunteer=[]
    )


async def test_all_jobs():
    """Test resume tailoring on all scored jobs"""
    
    db = Database()
    await db.connect()
    
    try:
        # 1. Load user profile
        profile_row = await db.fetchrow("""
            SELECT 
                id, name, email, skills, years_of_experience, experience_level,
                target_salary_min, target_salary_max, target_salary_currency,
                preferred_location, remote_preference, willing_to_relocate,
                preferred_company_sizes, preferred_industries
            FROM user_profile
            WHERE is_active = TRUE
            LIMIT 1
        """)
        
        if not profile_row:
            print("No active user profile found. Run: python -m scripts.create_profile")
            return
        
        # Parse profile
        skills = json.loads(profile_row['skills']) if isinstance(profile_row['skills'], str) else profile_row['skills']
        
        user_profile = UserProfile(
            id=profile_row['id'],
            name=profile_row['name'],
            email=profile_row['email'],
            skills=skills,
            years_of_experience=profile_row['years_of_experience'],
            experience_level=profile_row['experience_level'],
            target_salary_min=profile_row['target_salary_min'],
            target_salary_max=profile_row['target_salary_max'],
            preferred_location=profile_row['preferred_location'],
            remote_preference=profile_row['remote_preference']
        )
        
        print(f"Loaded profile: {user_profile.name}")
        
        # 2. Load all scored jobs
        job_rows = await db.fetch("""
            SELECT 
                j.id, j.title, j.company, j.location, j.location_type,
                j.employment_type, j.salary_min, j.salary_max, 
                j.salary_currency, j.salary_period, j.description,
                j.platform, j.platform_url, j.posted_date, j.skills,
                js.total_score
            FROM jobs j
            INNER JOIN job_scores js ON j.id = js.job_id
            ORDER BY js.total_score DESC
        """)
        
        if not job_rows:
            print("No scored jobs found. Run: python main.py && python -m orchestrators.job_scorer")
            return
        
        print(f"Found {len(job_rows)} scored jobs\n")
        
        # 3. Create base resume
        base_resume = create_sample_base_resume()
        tailoring_service = ResumeTailoringService()
        
        # 4. Test tailoring on each job
        results = []
        
        print("🔄 Testing resume tailoring on all jobs...\n")
        
        for i, job_row in enumerate(job_rows, 1):
            # Parse job
            job_skills = json.loads(job_row['skills']) if isinstance(job_row['skills'], str) else job_row['skills']
            
            job = Job(
                id=str(job_row['id']),
                title=job_row['title'],
                company=job_row['company'],
                location=job_row['location'],
                location_type=job_row['location_type'],
                employment_type=job_row['employment_type'],
                salary_min=job_row['salary_min'],
                salary_max=job_row['salary_max'],
                description=job_row['description'],
                platform=job_row['platform'],
                platform_url=job_row['platform_url'],
                skills=job_skills if isinstance(job_skills, list) else []
            )
            
            # Tailor resume
            tailored_resume = await tailoring_service.tailor_resume(
                base_resume=base_resume,
                job=job,
                user_profile=user_profile
            )
            
            # Analyze ATS
            ats_result = tailoring_service.analyze_ats_compatibility(tailored_resume, job)
            
            results.append({
                'job': job,
                'job_score': job_row['total_score'],
                'tailored_resume': tailored_resume,
                'ats_result': ats_result
            })
            
            # Quick progress indicator
            print(f"[{i}/{len(job_rows)}] {job.title[:50]:<50} | ATS: {ats_result.ats_score:>5.1f}/100 | Keywords: {ats_result.keyword_match_rate*100:>5.1f}%")
        
        # 5. Display summary
        print("\n" + "="*100)
        print("RESUME TAILORING SUMMARY")
        print("="*100)
        
        avg_ats = sum(r['ats_result'].ats_score for r in results) / len(results)
        avg_keyword_match = sum(r['ats_result'].keyword_match_rate for r in results) / len(results)
        
        perfect_ats = sum(1 for r in results if r['ats_result'].ats_score >= 95)
        good_ats = sum(1 for r in results if 80 <= r['ats_result'].ats_score < 95)
        moderate_ats = sum(1 for r in results if 60 <= r['ats_result'].ats_score < 80)
        poor_ats = sum(1 for r in results if r['ats_result'].ats_score < 60)
        
        print(f"\nOverall Statistics:")
        print(f"  Total Jobs:           {len(results)}")
        print(f"  Average ATS Score:    {avg_ats:.1f}/100")
        print(f"  Average Keyword Match: {avg_keyword_match*100:.1f}%")
        print(f"\nATS Score Distribution:")
        print(f"  🟢 Perfect (95-100):  {perfect_ats} jobs")
        print(f"  🟡 Good (80-94):      {good_ats} jobs")
        print(f"  🟠 Moderate (60-79):  {moderate_ats} jobs")
        print(f"  🔴 Poor (<60):        {poor_ats} jobs")
        
        # 6. Show top 3 best matches
        print("\n" + "="*100)
        print("🏆 TOP 3 BEST TAILORED RESUMES")
        print("="*100)
        
        results_sorted = sorted(results, key=lambda x: x['ats_result'].ats_score, reverse=True)
        
        for i, result in enumerate(results_sorted[:3], 1):
            job = result['job']
            tailored = result['tailored_resume']
            ats = result['ats_result']
            
            print(f"\n{i}. {job.title} at {job.company}")
            print(f"   Job Score:     {result['job_score']:.1f}/100")
            print(f"   ATS Score:     {ats.ats_score:.1f}/100")
            print(f"   Keyword Match: {ats.keyword_match_rate*100:.1f}%")
            print(f"   Strategy:      {tailored.tailoring_strategy}")
            print(f"   Summary:       {tailored.tailored_summary[:100]}...")
            print(f"   Top Skills:    {', '.join(tailored.highlighted_skills[:5])}")
            print(f"   Experience:    {len(tailored.relevant_experience)} positions selected")
            print(f"   Projects:      {len(tailored.relevant_projects)} projects selected")
        
        # 7. Show bottom 3 (needs improvement)
        if len(results) > 3:
            print("\n" + "="*100)
            print(" BOTTOM 3 - NEEDS IMPROVEMENT")
            print("="*100)
            
            for i, result in enumerate(results_sorted[-3:], 1):
                job = result['job']
                ats = result['ats_result']
                
                print(f"\n{i}. {job.title} at {job.company}")
                print(f"   ATS Score:        {ats.ats_score:.1f}/100")
                print(f"   Keyword Match:    {ats.keyword_match_rate*100:.1f}%")
                print(f"   Missing Keywords: {', '.join(ats.missing_keywords[:5])}")
                if ats.suggestions:
                    print(f"   Suggestions:      {ats.suggestions[0]}")
        
        # 8. Edge cases and issues
        print("\n" + "="*100)
        print("🔍 EDGE CASES & ISSUES")
        print("="*100)
        
        issues_found = False
        
        # Check for low ATS scores
        low_ats = [r for r in results if r['ats_result'].ats_score < 70]
        if low_ats:
            issues_found = True
            print(f"\n {len(low_ats)} jobs with ATS score < 70:")
            for r in low_ats[:3]:
                print(f"   - {r['job'].title}: {r['ats_result'].ats_score:.1f}/100")
                print(f"     Missing: {', '.join(r['ats_result'].missing_keywords[:3])}")
        
        # Check for jobs with many missing keywords
        many_missing = [r for r in results if len(r['ats_result'].missing_keywords) > 5]
        if many_missing:
            issues_found = True
            print(f"\n {len(many_missing)} jobs with >5 missing keywords:")
            for r in many_missing[:3]:
                print(f"   - {r['job'].title}: {len(r['ats_result'].missing_keywords)} missing")
        
        # Check for jobs with no experience selected
        no_exp = [r for r in results if len(r['tailored_resume'].relevant_experience) == 0]
        if no_exp:
            issues_found = True
            print(f"\n {len(no_exp)} jobs with no relevant experience selected:")
            for r in no_exp:
                print(f"   - {r['job'].title}")
        
        if not issues_found:
            print("\n No significant issues found!")
        
        print("\n" + "="*100)
        print("Resume tailoring test completed!")
        print("="*100)
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_all_jobs())