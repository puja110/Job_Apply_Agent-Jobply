"""
Test Script: Single PDF Resume Generation
Test the PDF generation service with one job
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Database
from services.pdf_generator import PDFGenerator, ResumePDFService
from services.resume_tailoring import ResumeTailoringService
from models.resume import BaseResume, WorkExperience, Education, Project
from models.user_profile import UserProfile
from models.job import Job
from repositories.job_repository import JobRepository
from repositories.user_profile_repository import UserProfileRepository

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_base_resume() -> BaseResume:
    """Create sample base resume"""
    
    return BaseResume(
        full_name="Puja Shrestha",
        email="puja@example.com",
        phone="+1 (555) 123-4567",
        location="Barrie, Ontario, Canada",
        linkedin="linkedin.com/in/pujashrestha",
        github="github.com/pujashrestha",
        
        summary="""Experienced software engineer with 3+ years of expertise in machine learning, 
        artificial intelligence, and full-stack development. Proven track record of building 
        scalable AI systems and delivering high-impact solutions.""",
        
        technical_skills={
            "programming_languages": ["Python", "JavaScript", "TypeScript", "SQL"],
            "ai_ml_frameworks": ["PyTorch", "TensorFlow", "scikit-learn"],
            "llm_frameworks": ["LangChain", "OpenAI API"],
            "ai_techniques": ["Machine Learning", "Deep Learning", "NLP", "RAG", "AI Agents"],
            "web_frameworks": ["Angular.js", "Node.js", "FastAPI"],
            "databases": ["PostgreSQL", "MongoDB", "Redis"],
            "cloud_devops": ["AWS", "Docker", "Git"]
        },
        
        work_experience=[
            WorkExperience(
                company="Tech Innovations Inc.",
                position="AI/ML Engineer",
                location="Toronto, ON",
                start_date="Jan 2022",
                end_date=None,
                description="Leading development of AI-powered solutions",
                achievements=[
                    "Built and deployed 5+ production ML models serving 100K+ daily users",
                    "Reduced model inference time by 60% through optimization",
                    "Implemented RAG system improving accuracy by 40%",
                    "Led team of 3 engineers in multi-agent framework development"
                ],
                technologies=["Python", "PyTorch", "LangChain", "PostgreSQL", "AWS"]
            ),
            WorkExperience(
                company="Digital Solutions Corp",
                position="Full Stack Developer",
                location="Remote",
                start_date="Jun 2020",
                end_date="Dec 2021",
                description="Developed scalable web applications and APIs",
                achievements=[
                    "Architected microservices backend handling 1M+ API requests daily",
                    "Built real-time analytics dashboard using Angular and Node.js",
                    "Improved application performance by 45% through optimization"
                ],
                technologies=["JavaScript", "Node.js", "Angular", "MongoDB"]
            )
        ],
        
        education=[
            Education(
                institution="University of Toronto",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
                location="Toronto, ON",
                graduation_date="May 2020",
                gpa=3.8,
                honors=["Dean's List", "Graduated with Distinction"],
                relevant_coursework=[
                    "Machine Learning", "Artificial Intelligence", "Database Systems"
                ]
            )
        ],
        
        projects=[
            Project(
                name="Multi-Agent Job Application System",
                description="AI-powered system that automates job search and application",
                technologies=["Python", "LangChain", "PostgreSQL", "OpenAI"],
                achievements=[
                    "Implemented semantic job matching with 80% accuracy",
                    "Built ATS-optimized resume generation with 100% compatibility"
                ],
                date="2024 - Present"
            )
        ],
        
        certifications=[]
    )


async def test_pdf_generation():
    """Test PDF generation for a single job"""
    
    print("\n" + "="*80)
    print(" TEST: PDF Resume Generation")
    print("="*80 + "\n")
    
    # Initialize database
    db = Database()
    await db.connect()
    
    try:
        # Initialize repositories
        job_repo = JobRepository(db)
        user_profile_repo = UserProfileRepository(db)
        
        # Get first user profile
        profiles = await user_profile_repo.list_all(limit=1)
        if not profiles:
            print("No user profiles found. Please create a profile first.")
            return
        
        user_profile = profiles[0]
        print(f"✓ Loaded profile: {user_profile.name}")
        
        # Get highest scored job
        jobs = await job_repo.get_scored_jobs(min_score=0, limit=1)
        if not jobs:
            print("No jobs found. Please run job discovery first.")
            return
        
        job = jobs[0]
        print(f"✓ Loaded job: {job.title} at {job.company}")
        print(f"  Job score: {job.score:.1f}/100")
        print()
        
        # Create base resume
        base_resume = create_sample_base_resume()
        print("✓ Created sample base resume")
        
        # Initialize services
        tailoring_service = ResumeTailoringService()
        pdf_service = ResumePDFService()
        
        # Tailor resume
        print("\n Tailoring resume for job...")
        tailored_resume = await tailoring_service.tailor_resume(
            base_resume=base_resume,
            job=job,
            user_profile=user_profile
        )
        print("✓ Resume tailored successfully")
        
        # Calculate ATS score
        ats_result = tailoring_service.calculate_ats_score(
            tailored_resume=tailored_resume,
            job=job
        )
        
        print(f"\n ATS Optimization Results:")
        print(f"  ATS Score: {ats_result.ats_score:.1f}/100")
        print(f"  Keyword Match Rate: {ats_result.keyword_match_rate*100:.1f}%")
        print(f"  Matched Keywords: {len(ats_result.matched_keywords)}")
        print(f"  Missing Keywords: {len(ats_result.missing_keywords)}")
        
        # Generate PDF
        print("\n Generating PDF...")
        output_dir = "test_resumes"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        pdf_bytes, filepath = await pdf_service.generate_and_store(
            resume=tailored_resume,
            job_id=str(job.id),
            output_dir=output_dir
        )
        
        file_size_kb = len(pdf_bytes) / 1024
        
        print(f"PDF Generated Successfully!")
        print(f"\n File Details:")
        print(f"  Path: {filepath}")
        print(f"  Size: {file_size_kb:.2f} KB")
        print(f"  Pages: 1-2 (estimated)")
        
        # Display resume highlights
        print(f"\n✨ Resume Highlights:")
        print(f"  Professional Summary: {tailored_resume.summary[:100]}...")
        print(f"  Experience Sections: {len(tailored_resume.work_experience)}")
        print(f"  Projects: {len(tailored_resume.projects)}")
        print(f"  Skills Categories: {len(tailored_resume.technical_skills)}")
        
        print("\n" + "="*80)
        print("TEST PASSED - PDF generation successful!")
        print("="*80 + "\n")
        
        print(f"Next steps:")
        print(f"  1. Open the PDF: {filepath}")
        print(f"  2. Verify formatting and content")
        print(f"  3. Run batch generation: python scripts/generate_all_resumes.py")
        print()
        
    except Exception as e:
        print(f"\n TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_pdf_generation())