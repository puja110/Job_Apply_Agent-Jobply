# """
# CLI Tool: Batch PDF Resume Generation
# Generate PDF resumes for all scored jobs
# """
# import asyncio
# import sys
# import os
# from pathlib import Path
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from database.connection import Database
# from services.pdf_generator import PDFGenerator, ResumePDFService
# from services.resume_tailoring import ResumeTailoringService
# from models.resume import BaseResume, WorkExperience, Education, Project
# from models.user_profile import UserProfile
# from models.job import Job
# from models.generated_resume import GeneratedResumeRepository, GeneratedResumeCreate
# from repositories.job_repository import JobRepository
# from repositories.user_profile_repository import UserProfileRepository

# import logging
# from rich.console import Console
# from rich.table import Table
# from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
# from rich.panel import Panel
# from typing import List, Tuple

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# console = Console()


# def create_sample_base_resume() -> BaseResume:
#     """Create sample base resume (replace with actual user data)"""
    
#     return BaseResume(
#         full_name="Puja Shrestha",
#         email="puja@example.com",
#         phone="+1 (555) 123-4567",
#         location="Barrie, Ontario, Canada",
#         linkedin="linkedin.com/in/pujashrestha",
#         github="github.com/pujashrestha",
        
#         summary="""Experienced software engineer with 3+ years of expertise in machine learning, 
#         artificial intelligence, and full-stack development. Proven track record of building 
#         scalable AI systems and delivering high-impact solutions. Passionate about leveraging 
#         cutting-edge technology to solve real-world problems.""",
        
#         technical_skills={
#             "programming_languages": ["Python", "JavaScript", "TypeScript", "SQL"],
#             "ai_ml_frameworks": ["PyTorch", "TensorFlow", "scikit-learn", "Hugging Face"],
#             "llm_frameworks": ["LangChain", "LlamaIndex", "OpenAI API", "Anthropic Claude"],
#             "ai_techniques": ["Machine Learning", "Deep Learning", "NLP", "RAG", "AI Agents"],
#             "web_frameworks": ["Angular.js", "Node.js", "FastAPI", "Flask"],
#             "databases": ["PostgreSQL", "MongoDB", "Redis"],
#             "cloud_devops": ["AWS", "Docker", "Git"],
#             "soft_skills": ["Problem Solving", "Communication", "Leadership", "Architecture Design"]
#         },
        
#         work_experience=[
#             WorkExperience(
#                 company="Tech Innovations Inc.",
#                 position="AI/ML Engineer",
#                 location="Toronto, ON",
#                 start_date="Jan 2022",
#                 end_date=None,
#                 description="Leading development of AI-powered solutions for enterprise clients",
#                 achievements=[
#                     "Built and deployed 5+ production ML models serving 100K+ daily users",
#                     "Reduced model inference time by 60% through optimization and caching strategies",
#                     "Implemented RAG system that improved customer support response accuracy by 40%",
#                     "Led team of 3 engineers in developing multi-agent AI application framework"
#                 ],
#                 technologies=["Python", "PyTorch", "LangChain", "PostgreSQL", "AWS"]
#             ),
#             WorkExperience(
#                 company="Digital Solutions Corp",
#                 position="Full Stack Developer",
#                 location="Remote",
#                 start_date="Jun 2020",
#                 end_date="Dec 2021",
#                 description="Developed scalable web applications and APIs for SaaS products",
#                 achievements=[
#                     "Architected microservices backend handling 1M+ API requests daily",
#                     "Built real-time analytics dashboard using Angular and Node.js",
#                     "Improved application performance by 45% through database optimization",
#                     "Mentored junior developers on best practices and code reviews"
#                 ],
#                 technologies=["JavaScript", "Node.js", "Angular", "MongoDB", "Docker"]
#             ),
#             WorkExperience(
#                 company="StartupXYZ",
#                 position="Software Engineer Intern",
#                 location="Vancouver, BC",
#                 start_date="May 2019",
#                 end_date="Aug 2019",
#                 description="Contributed to development of mobile and web applications",
#                 achievements=[
#                     "Developed REST APIs for mobile app with 10K+ downloads",
#                     "Implemented automated testing suite improving code coverage to 85%",
#                     "Collaborated with cross-functional teams in Agile environment"
#                 ],
#                 technologies=["Python", "Flask", "PostgreSQL", "Git"]
#             )
#         ],
        
#         education=[
#             Education(
#                 institution="University of Toronto",
#                 degree="Bachelor of Science",
#                 field_of_study="Computer Science",
#                 location="Toronto, ON",
#                 graduation_date="May 2020",
#                 gpa=3.8,
#                 honors=["Dean's List", "Graduated with Distinction"],
#                 relevant_coursework=[
#                     "Machine Learning", "Artificial Intelligence", "Database Systems",
#                     "Software Engineering", "Algorithms and Data Structures"
#                 ]
#             )
#         ],
        
#         projects=[
#             Project(
#                 name="Multi-Agent Job Application System",
#                 description="AI-powered system that automates job search, scoring, and application tailoring",
#                 technologies=["Python", "LangChain", "PostgreSQL", "OpenAI", "FastAPI"],
#                 achievements=[
#                     "Implemented semantic job matching with 80% accuracy using sentence transformers",
#                     "Built ATS-optimized resume generation achieving 100% compatibility scores",
#                     "Automated job discovery across 3+ platforms with rate limiting and caching"
#                 ],
#                 date="2024 - Present"
#             ),
#             Project(
#                 name="Intelligent Document Q&A System",
#                 description="RAG-based system for answering questions from large document collections",
#                 technologies=["Python", "LlamaIndex", "ChromaDB", "OpenAI", "Streamlit"],
#                 achievements=[
#                     "Processed 10,000+ documents with 95% retrieval accuracy",
#                     "Reduced query response time to under 2 seconds using vector caching",
#                     "Built interactive UI with conversation history and source citations"
#                 ],
#                 date="2023"
#             ),
#             Project(
#                 name="Real-time Sentiment Analysis Dashboard",
#                 description="Web application for analyzing social media sentiment in real-time",
#                 technologies=["Python", "TensorFlow", "Kafka", "React", "PostgreSQL"],
#                 achievements=[
#                     "Trained LSTM model achieving 88% sentiment classification accuracy",
#                     "Processed 50K+ messages per minute with <100ms latency",
#                     "Visualized sentiment trends with interactive charts and filters"
#                 ],
#                 date="2022"
#             )
#         ],
        
#         certifications=[]
#     )


# async def generate_pdfs_for_all_jobs(
#     user_profile_id: str,
#     min_score: float = 60.0,
#     output_dir: str = "generated_resumes",
#     store_in_db: bool = True
# ):
#     """
#     Generate PDF resumes for all scored jobs above threshold
    
#     Args:
#         user_profile_id: User profile ID
#         min_score: Minimum job score threshold
#         output_dir: Directory to save PDFs
#         store_in_db: Whether to store metadata in database
#     """
#     console.print("\n[bold cyan]🚀 Starting Batch PDF Generation[/bold cyan]\n")
    
#     # Initialize services
#     db = Database()
#     await db.connect()
    
#     try:
#         # Initialize repositories
#         job_repo = JobRepository(db)
#         user_profile_repo = UserProfileRepository(db)
#         resume_repo = GeneratedResumeRepository(db)
        
#         # Initialize services
#         tailoring_service = ResumeTailoringService()
#         pdf_service = ResumePDFService()
        
#         # Load user profile
#         user_profile = await user_profile_repo.get_by_id(user_profile_id)
#         if not user_profile:
#             console.print(f"[red] User profile not found: {user_profile_id}[/red]")
#             return
        
#         console.print(f"[green]✓[/green] Loaded profile: {user_profile.name}")
        
#         # Get all scored jobs above threshold
#         jobs = await job_repo.get_scored_jobs(min_score=min_score)
        
#         if not jobs:
#             console.print(f"[yellow]⚠ No jobs found with score >= {min_score}[/yellow]")
#             return
        
#         console.print(f"[green]✓[/green] Found {len(jobs)} jobs with score >= {min_score}\n")
        
#         # Create base resume
#         base_resume = create_sample_base_resume()
        
#         # Create output directory
#         Path(output_dir).mkdir(parents=True, exist_ok=True)
        
#         # Process each job with progress bar
#         results = []
#         failed = []
        
#         with Progress(
#             SpinnerColumn(),
#             TextColumn("[progress.description]{task.description}"),
#             BarColumn(),
#             TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
#             console=console
#         ) as progress:
            
#             task = progress.add_task(
#                 "[cyan]Generating PDFs...",
#                 total=len(jobs)
#             )
            
#             for job in jobs:
#                 try:
#                     # Tailor resume
#                     tailored_resume = await tailoring_service.tailor_resume(
#                         base_resume=base_resume,
#                         job=job,
#                         user_profile=user_profile
#                     )
                    
#                     # Calculate ATS score
#                     ats_result = tailoring_service.calculate_ats_score(
#                         tailored_resume=tailored_resume,
#                         job=job
#                     )
                    
#                     # Generate PDF
#                     pdf_bytes, filepath = await pdf_service.generate_and_store(
#                         resume=tailored_resume,
#                         job_id=str(job.id),
#                         output_dir=output_dir
#                     )
                    
#                     # Store in database if enabled
#                     if store_in_db:
#                         resume_create = GeneratedResumeCreate(
#                             user_profile_id=user_profile.id,
#                             job_id=job.id,
#                             filename=os.path.basename(filepath),
#                             file_path=filepath,
#                             file_size_bytes=len(pdf_bytes),
#                             resume_data=tailored_resume.dict(),
#                             ats_score=ats_result.ats_score,
#                             keyword_match_rate=ats_result.keyword_match_rate,
#                             matched_keywords=ats_result.matched_keywords,
#                             missing_keywords=ats_result.missing_keywords
#                         )
                        
#                         await resume_repo.create(resume_create)
                    
#                     results.append({
#                         'job': job,
#                         'filepath': filepath,
#                         'ats_score': ats_result.ats_score,
#                         'file_size': len(pdf_bytes)
#                     })
                    
#                 except Exception as e:
#                     logger.error(f"Failed to generate PDF for job {job.id}: {e}")
#                     failed.append((job, str(e)))
                
#                 progress.advance(task)
        
#         # Display results
#         console.print("\n[bold green] PDF Generation Complete![/bold green]\n")
        
#         # Success table
#         if results:
#             table = Table(title="Generated Resumes", show_header=True, header_style="bold magenta")
#             table.add_column("Job Title", style="cyan", width=40)
#             table.add_column("Company", style="green", width=20)
#             table.add_column("ATS Score", justify="right", style="yellow")
#             table.add_column("File Size", justify="right", style="blue")
#             table.add_column("Status", justify="center")
            
#             for result in results:
#                 job = result['job']
#                 ats_score = result['ats_score']
#                 file_size_kb = result['file_size'] / 1024
                
#                 # Color code ATS score
#                 if ats_score >= 80:
#                     score_style = "bold green"
#                     status = "✅"
#                 elif ats_score >= 60:
#                     score_style = "yellow"
#                     status = "✓"
#                 else:
#                     score_style = "red"
#                     status = "⚠"
                
#                 table.add_row(
#                     job.title[:40],
#                     job.company[:20] if job.company else "N/A",
#                     f"[{score_style}]{ats_score:.1f}/100[/{score_style}]",
#                     f"{file_size_kb:.1f} KB",
#                     status
#                 )
            
#             console.print(table)
        
#         # Failure table
#         if failed:
#             console.print("\n[bold red]Failed Generations:[/bold red]")
#             fail_table = Table(show_header=True, header_style="bold red")
#             fail_table.add_column("Job Title", style="cyan")
#             fail_table.add_column("Error", style="red")
            
#             for job, error in failed:
#                 fail_table.add_row(job.title[:50], error[:80])
            
#             console.print(fail_table)
        
#         # Summary statistics
#         if results:
#             avg_ats = sum(r['ats_score'] for r in results) / len(results)
#             total_size_mb = sum(r['file_size'] for r in results) / (1024 * 1024)
            
#             summary = Panel(
#                 f"""[bold cyan]Summary Statistics[/bold cyan]
                
# ✓ Successfully Generated: {len(results)}/{len(jobs)} resumes
# Failed: {len(failed)} resumes
# Average ATS Score: {avg_ats:.1f}/100
# Total Size: {total_size_mb:.2f} MB
# Output Directory: {output_dir}
#                 """,
#                 title="Generation Summary",
#                 border_style="green"
#             )
            
#             console.print("\n", summary)
        
#         # Get database statistics if stored
#         if store_in_db and results:
#             stats = await resume_repo.get_statistics(user_profile.id)
            
#             db_stats = Panel(
#                 f"""[bold cyan]Database Statistics[/bold cyan]
                
# Total Resumes Stored: {stats['total_resumes']}
# Average ATS Score: {stats['avg_ats_score']:.1f}/100
# Max ATS Score: {stats['max_ats_score']:.1f}/100
# Total Storage: {stats['total_size_mb']:.2f} MB
#                 """,
#                 title="Database Stats",
#                 border_style="blue"
#             )
            
#             console.print("\n", db_stats)
    
#     finally:
#         await db.disconnect()


# async def main():
#     """Main CLI entry point"""
#     import argparse
    
#     parser = argparse.ArgumentParser(description="Generate PDF resumes for scored jobs")
#     parser.add_argument(
#         "--user-id",
#         required=True,
#         help="User profile ID"
#     )
#     parser.add_argument(
#         "--min-score",
#         type=float,
#         default=60.0,
#         help="Minimum job score threshold (default: 60.0)"
#     )
#     parser.add_argument(
#         "--output-dir",
#         default="generated_resumes",
#         help="Output directory for PDFs (default: generated_resumes)"
#     )
#     parser.add_argument(
#         "--no-db",
#         action="store_true",
#         help="Don't store metadata in database"
#     )
    
#     args = parser.parse_args()
    
#     await generate_pdfs_for_all_jobs(
#         user_profile_id=args.user_id,
#         min_score=args.min_score,
#         output_dir=args.output_dir,
#         store_in_db=not args.no_db
#     )


# if __name__ == "__main__":
#     asyncio.run(main())