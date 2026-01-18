"""
Create/update user profile for job scoring
"""
import sys
import os
import json  # Add this import

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from database.connection import Database


async def create_profile():
    db = Database()
    await db.connect()
    
    # Your profile data
    profile_data = {
        'name': 'Puja Shrestha',
        'email': 'puja@example.com',  # Update with your email
        'skills': [
            "Python", "Machine Learning", "Deep Learning",
            "Natural Language Processing", "PyTorch", "TensorFlow",
            "LLM", "RAG", "AI Agents", "FastAPI", "PostgreSQL",
            "Docker", "AWS", "REST APIs", "JavaScript", "Angular.js"
        ],
        'years_of_experience': 3,
        'experience_level': 'mid',  # 'junior', 'mid', 'senior', 'lead'
        'target_salary_min': 100000,
        'target_salary_max': 150000,
        'target_salary_currency': 'USD',
        'preferred_location': 'Remote',
        'remote_preference': 'remote_only',  # 'remote_only', 'hybrid', 'onsite', 'flexible'
        'willing_to_relocate': False,
        'preferred_company_sizes': ['startup', 'mid', 'enterprise'],
        'preferred_industries': ['AI', 'ML', 'SaaS', 'Tech']
    }
    
    # Check if profile exists
    existing = await db.fetchrow(
        "SELECT id FROM user_profile WHERE email = $1",
        profile_data['email']
    )
    
    if existing:
        print(f"Profile already exists with ID: {existing['id']}")
        print("Updating profile...")
        
        await db.execute("""
            UPDATE user_profile SET
                name = $1,
                skills = $2::jsonb,
                years_of_experience = $3,
                experience_level = $4,
                target_salary_min = $5,
                target_salary_max = $6,
                target_salary_currency = $7,
                preferred_location = $8,
                remote_preference = $9,
                willing_to_relocate = $10,
                preferred_company_sizes = $11::jsonb,
                preferred_industries = $12::jsonb,
                updated_at = NOW()
            WHERE email = $13
        """,
            profile_data['name'],
            json.dumps(profile_data['skills']),  # Convert to JSON string
            profile_data['years_of_experience'],
            profile_data['experience_level'],
            profile_data['target_salary_min'],
            profile_data['target_salary_max'],
            profile_data['target_salary_currency'],
            profile_data['preferred_location'],
            profile_data['remote_preference'],
            profile_data['willing_to_relocate'],
            json.dumps(profile_data['preferred_company_sizes']),  # Convert to JSON string
            json.dumps(profile_data['preferred_industries']),  # Convert to JSON string
            profile_data['email']
        )
        print("Profile updated!")
    else:
        print("Creating new profile...")
        
        profile_id = await db.fetchval("""
            INSERT INTO user_profile (
                name, email, skills, years_of_experience, experience_level,
                target_salary_min, target_salary_max, target_salary_currency,
                preferred_location, remote_preference, willing_to_relocate,
                preferred_company_sizes, preferred_industries
            ) VALUES ($1, $2, $3::jsonb, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13::jsonb)
            RETURNING id
        """,
            profile_data['name'],
            profile_data['email'],
            json.dumps(profile_data['skills']),  # Convert to JSON string
            profile_data['years_of_experience'],
            profile_data['experience_level'],
            profile_data['target_salary_min'],
            profile_data['target_salary_max'],
            profile_data['target_salary_currency'],
            profile_data['preferred_location'],
            profile_data['remote_preference'],
            profile_data['willing_to_relocate'],
            json.dumps(profile_data['preferred_company_sizes']),  # Convert to JSON string
            json.dumps(profile_data['preferred_industries'])  # Convert to JSON string
        )
        print(f"Profile created with ID: {profile_id}")
    
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(create_profile())