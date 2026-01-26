"""
Resume Tailoring Service
Uses LLM to tailor resumes for specific job postings
"""
import logging
from typing import List, Dict, Optional
import re

from models.resume import (
    BaseResume, TailoredResume, WorkExperience, Project,
    ResumeTailoringRequest, ATSOptimizationResult
)
from models.job import Job
from models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class ResumeTailoringService:
    """Service for tailoring resumes to specific jobs"""
    
    def __init__(self):
        """Initialize the resume tailoring service"""
        self.max_summary_length = 150  # words
        self.max_bullets_per_job = 4
    
    async def tailor_resume(
        self,
        base_resume: BaseResume,
        job: Job,
        user_profile: UserProfile
    ) -> TailoredResume:
        """
        Tailor a resume for a specific job
        
        Args:
            base_resume: User's base resume
            job: Job to tailor for
            user_profile: User's profile
            
        Returns:
            Tailored resume
        """
        logger.info(f"Tailoring resume for job: {job.title} at {job.company}")
        
        # 1. Analyze job requirements
        job_keywords = self._extract_job_keywords(job)
        required_skills = set(s.lower() for s in job.skills)
        
        # 2. Tailor professional summary
        tailored_summary = self._tailor_summary(
            base_resume.summary,
            job,
            user_profile,
            job_keywords
        )
        
        # 3. Select and optimize work experience
        relevant_experience = self._select_relevant_experience(
            base_resume.work_experience,
            job,
            required_skills
        )
        
        # 4. Select relevant projects
        relevant_projects = self._select_relevant_projects(
            base_resume.projects,
            job,
            required_skills
        )
        
        # 5. Highlight matching skills
        highlighted_skills = self._highlight_skills(
            base_resume.technical_skills,
            required_skills,
            job_keywords
        )
        
        # 6. Identify keywords to include
        keywords_included = self._identify_keywords(
            tailored_summary,
            relevant_experience,
            relevant_projects,
            job_keywords
        )
        
        # 7. Create tailored resume
        tailored_resume = TailoredResume(
            user_profile_id=user_profile.id,
            job_id=job.id,
            tailored_summary=tailored_summary,
            highlighted_skills=highlighted_skills,
            relevant_experience=relevant_experience,
            relevant_projects=relevant_projects,
            keywords_included=keywords_included,
            tailoring_strategy=self._generate_strategy(job, required_skills)
        )
        
        return tailored_resume
    
    def _extract_job_keywords(self, job: Job) -> List[str]:
        """Extract important keywords from job description"""
        keywords = set()
        
        # Add job title keywords
        title_words = job.title.lower().split()
        keywords.update(w for w in title_words if len(w) > 3)
        
        # Add skills
        keywords.update(s.lower() for s in job.skills)
        
        # Extract from description using common patterns
        description = job.description.lower() if job.description else ""
        
        # Pattern: "experience with X"
        experience_pattern = r'experience\s+(?:with|in|using)\s+([a-z][a-z0-9\s\.\+#-]+)'
        for match in re.finditer(experience_pattern, description):
            keyword = match.group(1).strip().split()[0]  # First word
            if len(keyword) > 2:
                keywords.add(keyword)
        
        # Pattern: "proficient in X"
        proficient_pattern = r'(?:proficient|expert|skilled)\s+(?:in|with)\s+([a-z][a-z0-9\s\.\+#-]+)'
        for match in re.finditer(proficient_pattern, description):
            keyword = match.group(1).strip().split()[0]
            if len(keyword) > 2:
                keywords.add(keyword)
        
        return list(keywords)[:50]  # Top 50 keywords
    
    def _tailor_summary(
        self,
        base_summary: str,
        job: Job,
        user_profile: UserProfile,
        job_keywords: List[str]
    ) -> str:
        """
        Tailor the professional summary for the job
        """
        # Extract key info
        years_exp = user_profile.years_of_experience or 3
        level = user_profile.experience_level or "mid"
        top_skills = user_profile.skills[:5]
        
        # Get top 3 job skills that match user skills
        user_skills_lower = set(s.lower() for s in user_profile.skills)
        matched_job_skills = []
        for skill in job.skills[:5]:  # Top 5 job skills
            if skill.lower() in user_skills_lower or any(us.lower() in skill.lower() for us in user_profile.skills):
                matched_job_skills.append(skill)
        
        # If no direct matches, use job skills anyway (important for ATS)
        if not matched_job_skills and job.skills:
            matched_job_skills = job.skills[:2]
        
        # Match job type
        job_title_lower = job.title.lower()
        job_type = "engineer"
        if "solutions" in job_title_lower:
            job_type = "solutions engineer"
        elif "data" in job_title_lower:
            job_type = "data professional"
        elif "ml" in job_title_lower or "machine learning" in job_title_lower:
            job_type = "machine learning engineer"
        elif "ai" in job_title_lower:
            job_type = "AI engineer"
        
        # Build tailored summary
        summary_parts = []
        
        # Opening with level
        if level == "senior" or years_exp >= 5:
            summary_parts.append(f"Senior {job_type} with {years_exp}+ years of experience")
        elif level == "mid" or years_exp >= 2:
            summary_parts.append(f"Experienced {job_type} with {years_exp}+ years")
        else:
            summary_parts.append(f"Motivated {job_type}")
        
        # IMPORTANT: Include matched job skills for ATS
        if matched_job_skills:
            skills_str = ", ".join(matched_job_skills[:3])
            summary_parts.append(f"specializing in {skills_str}")
        elif top_skills:
            skills_str = ", ".join(top_skills[:3])
            summary_parts.append(f"with expertise in {skills_str}")
        
        # Add specific accomplishment keyword
        summary_parts.append("Proven track record of delivering scalable solutions")
        
        # Company/domain alignment
        if job.company:
            summary_parts.append(f"Seeking to contribute to {job.company}'s mission")
        
        # Job-specific value proposition (include keywords)
        if "ai" in job_title_lower or "ml" in job_title_lower:
            summary_parts.append("by building intelligent AI-powered systems")
        elif "solutions" in job_title_lower:
            summary_parts.append("by designing and implementing customer-focused solutions")
        elif "data" in job_title_lower:
            summary_parts.append("by leveraging data to drive insights and decisions")
        else:
            summary_parts.append("by delivering high-quality technical solutions")
        
        tailored_summary = " ".join(summary_parts) + "."

        required_skills = set(s.lower() for s in job.skills)
        tailored_summary = self._inject_soft_skills_into_summary(
            tailored_summary,
            job,
            required_skills,
            user_profile.skills
        )
        
        return tailored_summary
    
    def _select_relevant_experience(
        self,
        all_experience: List[WorkExperience],
        job: Job,
        required_skills: set
    ) -> List[WorkExperience]:
        """Select and optimize most relevant work experience"""
        
        scored_experience = []
        
        for exp in all_experience:
            # Score based on relevance
            score = 0
            
            # Technology overlap
            exp_tech = set(t.lower() for t in exp.technologies)
            tech_overlap = len(exp_tech.intersection(required_skills))
            score += tech_overlap * 10
            
            # Description keyword matches
            desc_lower = exp.description.lower()
            for skill in required_skills:
                if skill in desc_lower:
                    score += 5
            
            # Recent experience gets higher score
            if exp.end_date is None or exp.end_date.lower() == "present":
                score += 20
            
            scored_experience.append((score, exp))
        
        # Sort by score and take top experiences
        scored_experience.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 3-4 most relevant
        return [exp for _, exp in scored_experience[:4]]
    
    def _select_relevant_projects(
        self,
        all_projects: List[Project],
        job: Job,
        required_skills: set
    ) -> List[Project]:
        """Select most relevant projects"""
        
        scored_projects = []
        
        for project in all_projects:
            score = 0
            
            # Technology match
            proj_tech = set(t.lower() for t in project.technologies)
            tech_overlap = len(proj_tech.intersection(required_skills))
            score += tech_overlap * 15
            
            # Description keywords
            desc_lower = project.description.lower()
            job_title_words = set(job.title.lower().split())
            for word in job_title_words:
                if len(word) > 3 and word in desc_lower:
                    score += 5
            
            scored_projects.append((score, project))
        
        # Sort and return top 2-3
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        return [proj for _, proj in scored_projects[:3]]
    
    def _highlight_skills(
        self,
        all_skills: Dict[str, List[str]],
        required_skills: set,
        job_keywords: List[str]
    ) -> List[str]:
        """Select and order skills to highlight"""
        
        highlighted = []
        all_user_skills = []
        
        # Flatten all skills
        for category, skills in all_skills.items():
            all_user_skills.extend(skills)
        
        # First: Add matching required skills
        for skill in all_user_skills:
            if skill.lower() in required_skills:
                highlighted.append(skill)
        
        # Second: Add skills matching job keywords
        for skill in all_user_skills:
            skill_lower = skill.lower()
            if skill not in highlighted and any(kw in skill_lower for kw in job_keywords):
                highlighted.append(skill)
        
        # Third: Add remaining important skills
        for skill in all_user_skills:
            if skill not in highlighted and len(highlighted) < 15:
                highlighted.append(skill)
        
        return highlighted[:15]  # Max 15 skills
    
    def _identify_keywords(
        self,
        summary: str,
        experience: List[WorkExperience],
        projects: List[Project],
        job_keywords: List[str]
    ) -> List[str]:
        """Identify which job keywords are included in the tailored resume"""
        
        # Combine all text
        all_text = summary.lower()
        for exp in experience:
            all_text += " " + exp.description.lower()
            all_text += " " + " ".join(exp.achievements).lower()
        for proj in projects:
            all_text += " " + proj.description.lower()
        
        # Check which keywords are present
        included = []
        for keyword in job_keywords:
            if keyword.lower() in all_text:
                included.append(keyword)
        
        return included
    
    def _generate_strategy(self, job: Job, required_skills: set) -> str:
        """Generate a description of the tailoring strategy used"""
        strategies = []
        
        if "senior" in job.title.lower():
            strategies.append("Emphasized senior-level experience and leadership")
        
        if "ai" in job.title.lower() or "ml" in job.title.lower():
            strategies.append("Highlighted AI/ML projects and expertise")
        
        if required_skills:
            top_skills = list(required_skills)[:3]
            strategies.append(f"Focused on: {', '.join(top_skills)}")
        
        return " | ".join(strategies) if strategies else "Standard tailoring"
    
    def analyze_ats_compatibility(
        self,
        tailored_resume: TailoredResume,
        job: Job
    ) -> ATSOptimizationResult:
        """
        Analyze how well the resume will perform in ATS systems
        
        Args:
            tailored_resume: The tailored resume
            job: The job posting
            
        Returns:
            ATS optimization analysis
        """
        job_keywords = set(s.lower() for s in job.skills)
        resume_keywords = set(s.lower() for s in tailored_resume.keywords_included)
        
        # Calculate match rate
        if job_keywords:
            matched = job_keywords.intersection(resume_keywords)
            match_rate = len(matched) / len(job_keywords)
        else:
            match_rate = 0.5
        
        # Calculate ATS score (0-100)
        ats_score = match_rate * 100
        
        # Boost for good formatting (assuming good format)
        ats_score = min(100, ats_score + 10)
        
        # Identify missing keywords
        missing = job_keywords - resume_keywords
        
        # Generate suggestions
        suggestions = []
        if match_rate < 0.7:
            suggestions.append(f"Add these missing keywords: {', '.join(list(missing)[:5])}")
        if len(tailored_resume.tailored_summary.split()) < 50:
            suggestions.append("Consider expanding your professional summary")
        
        return ATSOptimizationResult(
            ats_score=ats_score,
            keyword_match_rate=match_rate,
            matched_keywords=list(matched) if job_keywords else [],
            missing_keywords=list(missing)[:10],
            suggestions=suggestions
        )
    
    def _inject_soft_skills_into_summary(
        self,
        base_summary: str,
        job: Job,
        required_skills: set,
        user_skills: List[str]
    ) -> str:
        """
        Inject soft skills into the summary if they're required by the job
        
        Args:
            base_summary: Base summary text
            job: Job posting
            required_skills: Required skills from job
            user_skills: All user skills (including soft skills)
            
        Returns:
            Summary with soft skills incorporated
        """
        # Common soft skills to look for
        soft_skill_keywords = {
            'leadership': ['leadership', 'lead', 'mentor', 'mentoring', 'team lead'],
            'communication': ['communication', 'collaborate', 'collaboration', 'stakeholder'],
            'architecture': ['architecture', 'system design', 'design', 'architect'],
            'agile': ['agile', 'scrum', 'sprint']
        }
        
        # Flatten user skills for checking
        user_skills_lower = set(s.lower() for s in user_skills)
        
        # Check which soft skills are required and user has
        soft_skills_to_add = []
        for skill_category, keywords in soft_skill_keywords.items():
            # Check if job requires this skill
            job_requires = any(kw in ' '.join(required_skills).lower() for kw in keywords)
            # Check if user has this skill
            user_has = any(kw in user_skills_lower for kw in keywords)
            
            if job_requires and user_has:
                # Add the most appropriate term
                if 'leadership' in keywords and user_has:
                    soft_skills_to_add.append('leadership')
                elif 'communication' in keywords and user_has:
                    soft_skills_to_add.append('strong communication')
                elif 'architecture' in keywords and user_has:
                    soft_skills_to_add.append('system architecture')
                elif 'agile' in keywords and user_has:
                    soft_skills_to_add.append('Agile methodologies')
        
        # Inject soft skills into summary
        if soft_skills_to_add:
            # Add after the first sentence
            sentences = base_summary.split('.')
            if len(sentences) > 1:
                soft_skills_phrase = f"Demonstrated expertise in {', '.join(soft_skills_to_add)}."
                sentences.insert(1, soft_skills_phrase)
                return '.'.join(sentences)
        
        return base_summary