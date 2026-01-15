# cli/create_profile.py
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import db
from models.user_profile import UserProfile, ExperienceLevel, RemotePreference, CompanySize
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)

async def create_user_profile():
    """Interactive CLI to create user profile."""
    print("\n" + "="*80)
    print("CREATE YOUR JOB SEARCH PROFILE")
    print("="*80 + "\n")
    
    # Basic info
    name = input("Your name: ").strip()
    email = input("Your email (optional): ").strip() or None
    
    # Skills
    print("\nEnter your skills (comma-separated):")
    print("Example: Python, React, AWS, Machine Learning, Docker")
    skills_input = input("Skills: ").strip()
    skills = [s.strip() for s in skills_input.split(',') if s.strip()]
    
    # Experience
    years = input("\nYears of professional experience: ").strip()
    years_of_experience = int(years) if years else None
    
    print("\nExperience level:")
    for i, level in enumerate(ExperienceLevel, 1):
        print(f"  {i}. {level.value}")
    exp_choice = input("Choose (1-5): ").strip()
    experience_level = list(ExperienceLevel)[int(exp_choice) - 1] if exp_choice else None
    
    # Salary expectations
    print("\nSalary expectations (USD):")
    min_salary = input("  Minimum: $").strip()
    max_salary = input("  Maximum: $").strip()
    target_salary_min = int(min_salary) if min_salary else None
    target_salary_max = int(max_salary) if max_salary else None
    
    # Location preferences
    print("\nLocation preferences:")
    preferred_location = input("  Preferred location (e.g., 'New York' or 'Remote'): ").strip() or None
    
    print("\nRemote work preference:")
    for i, pref in enumerate(RemotePreference, 1):
        print(f"  {i}. {pref.value}")
    remote_choice = input("Choose (1-4): ").strip()
    remote_preference = list(RemotePreference)[int(remote_choice) - 1] if remote_choice else RemotePreference.FLEXIBLE
    
    relocate = input("\nWilling to relocate? (y/n): ").strip().lower()
    willing_to_relocate = relocate == 'y'
    
    # Company size preferences
    print("\nPreferred company sizes (comma-separated numbers):")
    for i, size in enumerate(CompanySize, 1):
        print(f"  {i}. {size.value}")
    size_choice = input("Choose (e.g., '1,3,4'): ").strip()
    preferred_company_sizes = []
    if size_choice:
        indices = [int(i.strip()) - 1 for i in size_choice.split(',') if i.strip().isdigit()]
        preferred_company_sizes = [list(CompanySize)[i] for i in indices if i < len(CompanySize)]
    
    # Industries
    print("\nPreferred industries (comma-separated):")
    print("Example: fintech, healthcare, saas, ai, edtech")
    industries_input = input("Industries: ").strip()
    preferred_industries = [i.strip() for i in industries_input.split(',') if i.strip()]
    
    # Create profile
    profile = UserProfile(
        name=name,
        email=email,
        skills=skills,
        years_of_experience=years_of_experience,
        experience_level=experience_level,
        target_salary_min=target_salary_min,
        target_salary_max=target_salary_max,
        preferred_location=preferred_location,
        remote_preference=remote_preference,
        willing_to_relocate=willing_to_relocate,
        preferred_company_sizes=preferred_company_sizes,
        preferred_industries=preferred_industries,
    )
    
    # Display summary
    print("\n" + "="*80)
    print("PROFILE SUMMARY")
    print("="*80)
    print(f"Name: {profile.name}")
    print(f"Email: {profile.email or 'Not provided'}")
    print(f"Skills ({len(profile.skills)}): {', '.join(profile.skills)}")
    print(f"Experience: {profile.years_of_experience} years ({profile.experience_level})")
    print(f"Salary Range: ${profile.target_salary_min:,} - ${profile.target_salary_max:,}" if profile.target_salary_min else "Salary: Not specified")
    print(f"Location: {profile.preferred_location or 'Flexible'}")
    print(f"Remote Preference: {profile.remote_preference}")
    print(f"Willing to Relocate: {'Yes' if profile.willing_to_relocate else 'No'}")
    if preferred_company_sizes:
        print(f"Company Sizes: {', '.join([s.value for s in preferred_company_sizes])}")
    if preferred_industries:
        print(f"Industries: {', '.join(preferred_industries)}")
    print("="*80)
    
    confirm = input("\nSave this profile? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Profile not saved.")
        return
    
    # Save to database
    await db.connect()
    
    try:
        # Deactivate any existing active profiles
        await db.execute(
            "UPDATE user_profile SET is_active = FALSE WHERE is_active = TRUE"
        )
        
        # Insert new profile
        result = await db.fetchrow(
            """
            INSERT INTO user_profile (
                name, email, skills, years_of_experience, experience_level,
                target_salary_min, target_salary_max, target_salary_currency,
                preferred_location, remote_preference, willing_to_relocate,
                preferred_company_sizes, preferred_industries, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
            """,
            profile.name,
            profile.email,
            json.dumps(profile.skills),
            profile.years_of_experience,
            profile.experience_level,
            profile.target_salary_min,
            profile.target_salary_max,
            profile.target_salary_currency,
            profile.preferred_location,
            profile.remote_preference,
            profile.willing_to_relocate,
            json.dumps(profile.preferred_company_sizes),
            json.dumps(profile.preferred_industries),
            True
        )
        
        profile_id = result['id']
        logger.info(f"Profile saved successfully! ID: {profile_id}")
        print(f"\nProfile created successfully! ID: {profile_id}")
        
    except Exception as e:
        logger.error(f"Failed to save profile: {e}", exc_info=True)
        print(f"\nError saving profile: {e}")
    
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(create_user_profile())