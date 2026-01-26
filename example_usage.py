"""
Example: Generate Resume PDFs for Jobply

This example demonstrates how to use the PDF generation system.
"""
import asyncio
import asyncpg
from pathlib import Path
from uuid import UUID

from services.resume_service import ResumeService
from models.generated_resume import TailoredResumeData
from services.pdf_generator import PDFGenerator


async def example_single_resume():
    """Example: Generate resume for a single job"""
    print("=" * 60)
    print("Example 1: Generate Single Resume")
    print("=" * 60)
    
    # Connect to database
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='jobply',
        user='pujashrestha'
    )
    
    try:
        # Initialize service
        resume_service = ResumeService(pool, Path('./example_output'))
        
        # Replace with your actual UUIDs
        user_id = UUID('00000000-0000-0000-0000-000000000000')  # Replace!
        job_id = UUID('00000000-0000-0000-0000-000000000000')   # Replace!
        
        print(f"Generating resume for:")
        print(f"  User: {user_id}")
        print(f"  Job: {job_id}")
        
        # Generate resume
        result = await resume_service.generate_resume_for_job(
            user_profile_id=user_id,
            job_id=job_id,
            store_pdf_in_db=False
        )
        
        if result:
            print("\n✅ Success!")
            print(f"   Filename: {result['filename']}")
            print(f"   ATS Score: {result['ats_score']:.1f}%")
            print(f"   Keyword Match: {result['keyword_match_rate']:.1f}%")
            print(f"   Matched Keywords: {', '.join(result['matched_keywords'][:5])}")
            print(f"   Path: {result['file_path']}")
        else:
            print("\n❌ Failed to generate resume")
    
    finally:
        await pool.close()


async def example_batch_generation():
    """Example: Generate resumes for multiple top jobs"""
    print("\n" + "=" * 60)
    print("Example 2: Batch Generate for Top Jobs")
    print("=" * 60)
    
    # Connect to database
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        database='jobply',
        user='pujashrestha'
    )
    
    try:
        # Initialize service
        resume_service = ResumeService(pool, Path('./example_output'))
        
        # Replace with your actual user UUID
        user_id = UUID('00000000-0000-0000-0000-000000000000')  # Replace!
        
        print(f"Generating resumes for user: {user_id}")
        print(f"Min score: 70.0, Limit: 5")
        
        # Generate batch
        results = await resume_service.generate_batch_resumes(
            user_profile_id=user_id,
            min_score=70.0,
            limit=5,
            store_pdf_in_db=False
        )
        
        print(f"\n✅ Generated {len(results)} resumes:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['filename']}")
            print(f"   Job: {result['job_title']} at {result['company']}")
            print(f"   ATS Score: {result['ats_score']:.1f}%")
            print(f"   Keywords: {result['keyword_match_rate']:.1f}%")
            print()
    
    finally:
        await pool.close()


async def example_direct_pdf():
    """Example: Generate PDF directly without database"""
    print("\n" + "=" * 60)
    print("Example 3: Direct PDF Generation (No Database)")
    print("=" * 60)
    
    # Create sample resume data
    sample_data = TailoredResumeData(
        contact_info={
            'name': 'Puja Shrestha',
            'email': 'puja@example.com',
            'phone': '+1 (555) 123-4567',
            'location': 'Barrie, ON, Canada',
            'linkedin': 'linkedin.com/in/pujashrestha',
            'github': 'github.com/pujashrestha'
        },
        professional_summary=(
            "Results-driven AI/ML Engineer with 3 years of experience in developing "
            "and deploying production-grade AI solutions. Specialized in Python, Machine Learning, "
            "Deep Learning, NLP, PyTorch, TensorFlow, and modern LLM frameworks including RAG. "
            "Proven track record of delivering scalable AI agents and intelligent automation systems."
        ),
        skills=[
            'Python', 'Machine Learning', 'Deep Learning', 'NLP', 'PyTorch', 'TensorFlow',
            'LLM', 'RAG', 'AI Agents', 'REST API', 'PostgreSQL', 'Redis', 'Docker',
            'AWS', 'Git', 'Agile'
        ],
        experience=[
            {
                'title': 'AI/ML Engineer',
                'company': 'Tech Company',
                'location': 'Remote',
                'start_date': '2022-01',
                'end_date': 'Present',
                'responsibilities': [
                    'Developed multi-agent AI system for automated job applications, achieving 80% ATS compatibility',
                    'Implemented semantic search using sentence transformers, improving job matching accuracy by 40%',
                    'Built production-grade RAG pipeline with PostgreSQL vector storage and OpenAI GPT-4',
                    'Designed and deployed microservices architecture using FastAPI, Docker, and AWS'
                ]
            },
            {
                'title': 'Software Engineer',
                'company': 'Previous Company',
                'location': 'Toronto, ON',
                'start_date': '2021-06',
                'end_date': '2021-12',
                'responsibilities': [
                    'Developed REST APIs using Python Flask serving 10K+ daily requests',
                    'Implemented data processing pipelines with pandas and NumPy',
                    'Created automated testing suite achieving 90% code coverage'
                ]
            }
        ],
        education=[
            {
                'degree': 'Bachelor of Science in Computer Science',
                'institution': 'University of Example',
                'graduation_date': '2021',
                'gpa': '3.8/4.0',
                'honors': 'Magna Cum Laude'
            }
        ],
        certifications=[
            {
                'name': 'AWS Certified Solutions Architect',
                'issuer': 'Amazon Web Services',
                'date': '2023'
            }
        ],
        projects=[
            {
                'name': 'Jobply - Automated Job Application System',
                'technologies': ['Python', 'PostgreSQL', 'OpenAI', 'Docker', 'React'],
                'description': 'Multi-agent AI system for discovering, scoring, and applying to jobs',
                'highlights': [
                    'Semantic matching with sentence transformers achieving 80% accuracy',
                    'Automated resume tailoring with 100% ATS compatibility',
                    'Scalable architecture handling 1000+ jobs per day'
                ]
            }
        ]
    )
    
    # Initialize PDF generator
    pdf_gen = PDFGenerator(Path('./example_output'))
    
    # Generate PDF
    print("Generating PDF...")
    pdf_bytes, file_path = pdf_gen.generate_pdf(
        resume_data=sample_data,
        filename='sample_resume.pdf',
        save_to_disk=True
    )
    
    # Calculate ATS score
    job_keywords = ['Python', 'Machine Learning', 'NLP', 'PyTorch', 'AWS', 'Docker', 'REST API']
    ats_scores = pdf_gen.calculate_ats_score(sample_data, job_keywords)
    
    print(f"\n✅ PDF Generated!")
    print(f"   File: {file_path}")
    print(f"   Size: {len(pdf_bytes):,} bytes")
    print(f"\n📊 ATS Scores:")
    print(f"   Overall: {ats_scores.overall_score:.1f}%")
    print(f"   Keyword Match: {ats_scores.keyword_match_rate:.1f}%")
    print(f"   Formatting: {ats_scores.formatting_score:.1f}%")
    print(f"   Matched Keywords: {', '.join(ats_scores.matched_keywords)}")
    if ats_scores.missing_keywords:
        print(f"   Missing Keywords: {', '.join(ats_scores.missing_keywords)}")
    print(f"\n💡 Recommendations:")
    for rec in ats_scores.recommendations:
        print(f"   • {rec}")


async def main():
    """Run all examples"""
    print("\n🚀 Jobply PDF Generator - Examples\n")
    
    # Example 3: Direct PDF (no database required)
    await example_direct_pdf()
    
    # Example 1: Single resume (requires database with job data)
    # Uncomment and update UUIDs to run:
    # await example_single_resume()
    
    # Example 2: Batch generation (requires database with job data)
    # Uncomment and update user UUID to run:
    # await example_batch_generation()
    
    print("\n" + "=" * 60)
    print("Examples complete! Check ./example_output/ for generated PDFs")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())