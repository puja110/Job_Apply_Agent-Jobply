"""
Test Resume Tailoring Service
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

logging.basicConfig(level=logging.INFO)
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
            "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "LLM"],
            "Frameworks": ["FastAPI", "React", "Angular.js", "Node.js", "Django"],
            "Cloud & DevOps": ["AWS", "Docker", "PostgreSQL", "Redis"],
            "Tools": ["Git", "REST APIs", "CI/CD"]
        },
        
        work_experience=[
            WorkExperience(
                company="Tech Innovations Inc.",
                position="Machine Learning Engineer",
                location="Toronto, ON",
                start_date="Jan 2022",
                end_date="Present",
                description="Lead ML engineer developing AI-powered solutions for enterprise clients",
                achievements=[
                    "Built and deployed 5+ machine learning models serving 100K+ daily users",
                    "Improved model accuracy by 25% through advanced feature engineering",
                    "Reduced inference latency by 40% using model optimization techniques",
                    "Mentored 3 junior engineers in ML best practices"
                ],
                technologies=["Python", "PyTorch", "TensorFlow", "AWS", "Docker", "FastAPI"]
            ),
            WorkExperience(
                company="DataCorp Solutions",
                position="Software Engineer",
                location="Remote",
                start_date="Jun 2020",
                end_date="Dec 2021",
                description="Full-stack engineer building data-intensive web applications",
                achievements=[
                    "Developed RESTful APIs serving 50K+ requests per day",
                    "Designed and implemented PostgreSQL database schemas for high-performance queries",
                    "Built responsive React dashboards for data visualization",
                    "Implemented CI/CD pipelines reducing deployment time by 60%"
                ],
                technologies=["JavaScript", "React", "Node.js", "PostgreSQL", "AWS", "Docker"]
            ),
            WorkExperience(
                company="Startup Labs",
                position="Junior Developer",
                location="Barrie, ON",
                start_date="Jan 2019",
                end_date="May 2020",
                description="Software developer working on web applications and automation tools",
                achievements=[
                    "Developed automation scripts reducing manual work by 70%",
                    "Built internal tools used by 20+ team members daily",
                    "Collaborated with cross-functional teams in Agile environment"
                ],
                technologies=["Python", "Django", "JavaScript", "MongoDB"]
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
                description="Multi-agent AI system that automates job searching, resume tailoring, and application tracking using LLMs and semantic search",
                technologies=["Python", "LLM", "RAG", "PostgreSQL", "FastAPI", "OpenAI"],
                achievements=[
                    "Implemented semantic job matching with 85% accuracy",
                    "Automated resume generation for 100+ applications",
                    "Reduced job search time by 80%"
                ],
                date="2024"
            ),
            Project(
                name="Real-time Sentiment Analysis Platform",
                description="Built a scalable system for analyzing social media sentiment using deep learning",
                technologies=["Python", "PyTorch", "BERT", "Redis", "Docker", "AWS"],
                achievements=[
                    "Processed 1M+ tweets per day with 92% accuracy",
                    "Deployed using microservices architecture",
                    "Implemented real-time dashboard for insights"
                ],
                date="2023"
            ),
            Project(
                name="Smart Recommendation Engine",
                description="Collaborative filtering system for personalized product recommendations",
                technologies=["Python", "TensorFlow", "PostgreSQL", "FastAPI"],
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


async def test_resume_tailoring():
    """Test the resume tailoring service"""
    
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
        
        print(f"\n Loaded profile: {user_profile.name}")
        
        # 2. Load a job with good score
        job_row = await db.fetchrow("""
            SELECT 
                j.id, j.title, j.company, j.location, j.location_type,
                j.employment_type, j.salary_min, j.salary_max, 
                j.salary_currency, j.salary_period, j.description,
                j.platform, j.platform_url, j.posted_date, j.skills
            FROM jobs j
            INNER JOIN job_scores js ON j.id = js.job_id
            ORDER BY js.total_score DESC
            LIMIT 1
        """)
        
        if not job_row:
            print("No scored jobs found. Run: python main.py && python -m orchestrators.job_scorer")
            return
        
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
            salary_currency=job_row['salary_currency'],
            salary_period=job_row['salary_period'],
            description=job_row['description'],
            platform=job_row['platform'],
            platform_url=job_row['platform_url'],
            posted_date=job_row['posted_date'],
            skills=job_skills if isinstance(job_skills, list) else []
        )
        
        print(f"Loaded job: {job.title} at {job.company}")
        print(f"   Required skills: {', '.join(job.skills[:5])}")
        if len(job.skills) > 5:
            print(f"   ... and {len(job.skills) - 5} more")
        
        # 3. Create sample base resume
        print("\n Created sample base resume")
        base_resume = create_sample_base_resume()
        
        # 4. Tailor the resume
        print("\n Tailoring resume...")
        tailoring_service = ResumeTailoringService()
        tailored_resume = await tailoring_service.tailor_resume(
            base_resume=base_resume,
            job=job,
            user_profile=user_profile
        )
        
        # 5. Analyze ATS compatibility
        ats_result = tailoring_service.analyze_ats_compatibility(tailored_resume, job)
        
        # 6. Display results
        print("\n" + "="*80)
        print(" TAILORED RESUME RESULTS")
        print("="*80)
        
        print(f"\n Job: {job.title} at {job.company}")
        print(f"Strategy: {tailored_resume.tailoring_strategy}")
        
        print(f"\n Tailored Summary:")
        print(f"   {tailored_resume.tailored_summary}")
        
        print(f"\n Highlighted Skills ({len(tailored_resume.highlighted_skills)}):")
        print(f"   {', '.join(tailored_resume.highlighted_skills[:10])}")
        if len(tailored_resume.highlighted_skills) > 10:
            print(f"   ... and {len(tailored_resume.highlighted_skills) - 10} more")
        
        print(f"\n💼 Selected Experience ({len(tailored_resume.relevant_experience)} positions):")
        for i, exp in enumerate(tailored_resume.relevant_experience, 1):
            print(f"   {i}. {exp.position} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})")
            print(f"      Technologies: {', '.join(exp.technologies[:5])}")
        
        print(f"\n Selected Projects ({len(tailored_resume.relevant_projects)}):")
        for i, proj in enumerate(tailored_resume.relevant_projects, 1):
            print(f"   {i}. {proj.name}")
            print(f"      Tech: {', '.join(proj.technologies[:5])}")
        
        print(f"\n Keywords Included ({len(tailored_resume.keywords_included)}):")
        print(f"   {', '.join(tailored_resume.keywords_included[:15])}")
        if len(tailored_resume.keywords_included) > 15:
            print(f"   ... and {len(tailored_resume.keywords_included) - 15} more")
        
        print(f"\n ATS COMPATIBILITY ANALYSIS")
        print("="*80)
        print(f"ATS Score:          {ats_result.ats_score:.1f}/100")
        print(f"Keyword Match Rate: {ats_result.keyword_match_rate*100:.1f}%")
        print(f"Matched Keywords:   {len(ats_result.matched_keywords)}")
        print(f"Missing Keywords:   {len(ats_result.missing_keywords)}")
        
        if ats_result.missing_keywords:
            print(f"\n Missing Keywords: {', '.join(ats_result.missing_keywords[:5])}")
        
        if ats_result.suggestions:
            print(f"\n Suggestions:")
            for suggestion in ats_result.suggestions:
                print(f"   - {suggestion}")
        
        print("\n" + "="*80)
        print("Resume tailoring test completed!")
        print("="*80)
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_resume_tailoring())