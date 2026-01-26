"""
Populate user profile with complete resume data
"""
import asyncio
import json
from uuid import UUID
from database.connection import Database

async def populate_user_profile():
    """Add complete profile data for resume generation"""
    
    db = Database()
    await db.connect()
    
    try:
        user_id = UUID("24e93fba-fe4e-4b2c-a76e-4a48028b9e0b")
        
        # Complete skills list
        skills = [
            "Python", "Machine Learning", "Deep Learning", "NLP", 
            "PyTorch", "TensorFlow", "LLM", "RAG", "AI Agents",
            "FastAPI", "REST APIs", "PostgreSQL", "MongoDB", "Redis",
            "Docker", "Kubernetes", "AWS", "CI/CD", "Git",
            "JavaScript", "TypeScript", "Angular.js", "Node.js", "React",
            "Prompt Engineering", "System Design", "Agile"
        ]
        
        # Work experience
        experience = [
            {
                "title": "Machine Learning Engineer",
                "company": "Tech Innovations Inc.",
                "location": "Toronto, ON (Remote)",
                "start_date": "Jan 2022",
                "end_date": "Present",
                "responsibilities": [
                    "Developed and deployed production-grade LLM applications serving 100K+ users using GPT-4 and Claude API",
                    "Built RAG (Retrieval-Augmented Generation) systems improving answer accuracy by 40% using vector databases",
                    "Designed and implemented multi-agent AI systems for automated workflow orchestration",
                    "Optimized ML model inference reducing latency by 60% through efficient PyTorch optimization",
                    "Led team of 3 junior engineers, conducting code reviews and providing technical mentorship"
                ]
            },
            {
                "title": "AI/ML Developer",
                "company": "DataSoft Solutions",
                "location": "Barrie, ON",
                "start_date": "Jun 2020",
                "end_date": "Dec 2021",
                "responsibilities": [
                    "Developed NLP models for text classification achieving 92% accuracy using TensorFlow and BERT",
                    "Built RESTful APIs with FastAPI for ML model serving handling 1000+ requests/second",
                    "Implemented CI/CD pipelines using Docker and AWS for automated model deployment",
                    "Created data processing pipelines using Python and PostgreSQL for 10M+ records",
                    "Collaborated with cross-functional teams to integrate AI solutions into production systems"
                ]
            },
            {
                "title": "Software Developer Intern",
                "company": "StartupHub Technologies",
                "location": "Remote",
                "start_date": "Jan 2020",
                "end_date": "May 2020",
                "responsibilities": [
                    "Developed web applications using Angular.js and Node.js for client projects",
                    "Implemented RESTful APIs and database schemas using MongoDB and PostgreSQL",
                    "Participated in Agile development cycles and daily stand-ups",
                    "Wrote unit tests achieving 85% code coverage"
                ]
            }
        ]
        
        # Education
        education = [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of Toronto",
                "graduation_date": "2020",
                "location": "Toronto, ON",
                "gpa": "3.8/4.0",
                "honors": "Dean's List (2018-2020)"
            }
        ]
        
        # Projects
        projects = [
            {
                "name": "AI-Powered Job Application Agent",
                "description": "Multi-agent system automating job search, resume tailoring, and application submission",
                "technologies": ["Python", "LangChain", "PostgreSQL", "OpenAI API", "FastAPI"],
                "highlights": [
                    "Implemented semantic job matching using sentence transformers achieving 80% accuracy",
                    "Built automated resume tailoring with ATS optimization (100% compatibility scores)",
                    "Designed scalable PostgreSQL database schema for job and profile management"
                ]
            },
            {
                "name": "RAG-Based Document Q&A System",
                "description": "Enterprise document search and question-answering system using RAG architecture",
                "technologies": ["Python", "LangChain", "ChromaDB", "OpenAI Embeddings", "FastAPI"],
                "highlights": [
                    "Processed 10,000+ PDF documents with 95% retrieval accuracy",
                    "Reduced information retrieval time by 70% compared to manual search",
                    "Deployed on AWS with auto-scaling handling 500+ concurrent users"
                ]
            },
            {
                "name": "Real-time Sentiment Analysis Dashboard",
                "description": "Web application for real-time social media sentiment analysis",
                "technologies": ["Python", "TensorFlow", "React", "WebSocket", "Redis"],
                "highlights": [
                    "Achieved 89% accuracy on sentiment classification using fine-tuned BERT model",
                    "Processed 1000+ tweets per minute with real-time updates",
                    "Built interactive dashboard with React and D3.js for data visualization"
                ]
            }
        ]
        
        # Certifications
        certifications = [
            {
                "name": "AWS Certified Machine Learning - Specialty",
                "issuer": "Amazon Web Services",
                "date": "2023"
            },
            {
                "name": "TensorFlow Developer Certificate",
                "issuer": "Google",
                "date": "2022"
            },
            {
                "name": "Deep Learning Specialization",
                "issuer": "Coursera (deeplearning.ai)",
                "date": "2021"
            }
        ]
        
        # Update query
        update_query = """
            UPDATE user_profile
            SET 
                skills = $1::jsonb,
                experience = $2::jsonb,
                education = $3::jsonb,
                projects = $4::jsonb,
                certifications = $5::jsonb,
                phone = $6,
                linkedin = $7,
                github = $8
            WHERE id = $9
            RETURNING id, name, email;
        """
        
        async with db.pool.acquire() as conn:
            result = await conn.fetchrow(
                update_query,
                json.dumps(skills),
                json.dumps(experience),
                json.dumps(education),
                json.dumps(projects),
                json.dumps(certifications),
                "+1 (647) 555-0123",  # Add phone
                "linkedin.com/in/pujashrestha",  # Add LinkedIn
                "github.com/pujashrestha",  # Add GitHub
                user_id
            )
        
        print("Profile updated successfully!")
        print(f"User: {result['name']}")
        print(f"Email: {result['email']}")
        print(f"\nAdded:")
        print(f"  - {len(skills)} technical skills")
        print(f"  - {len(experience)} work experiences")
        print(f"  - {len(education)} education entries")
        print(f"  - {len(projects)} projects")
        print(f"  - {len(certifications)} certifications")
        print(f"  - Contact: Phone, LinkedIn, GitHub")
        
        print("\nNext steps:")
        print("  1. Delete old resume: rm generated_resumes/resume_mthree_*.pdf")
        print("  2. Delete from database: DELETE FROM generated_resumes;")
        print("  3. Regenerate: python test_real_job.py")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(populate_user_profile())
