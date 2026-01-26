"""
PDF Generator Service for creating ATS-optimized ONE-PAGE resumes
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib import colors

from models.generated_resume import TailoredResumeData, ATSScores


class PDFGenerator:
    """Generate ATS-optimized ONE-PAGE PDF resumes"""
    
    def __init__(self, output_dir: Path = Path("./generated_resumes")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = self._create_styles()
    
    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create custom paragraph styles for ATS optimization - ONE PAGE FORMAT"""
        styles = getSampleStyleSheet()
        
        # Compact ATS-optimized styles for one-page resume
        custom_styles = {
            'CustomTitle': ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,  # Reduced from 16
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=4,  # Reduced from 6
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'ContactInfo': ParagraphStyle(
                'ContactInfo',
                parent=styles['Normal'],
                fontSize=9,  # Reduced from 10
                textColor=colors.HexColor('#333333'),
                alignment=TA_CENTER,
                spaceAfter=8  # Reduced from 12
            ),
            'SectionHeader': ParagraphStyle(
                'SectionHeader',
                parent=styles['Heading2'],
                fontSize=11,  # Reduced from 12
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=3,  # Reduced from 6
                spaceBefore=6,  # Reduced from 12
                fontName='Helvetica-Bold',
                borderWidth=0,
                borderPadding=0,
                borderColor=colors.HexColor('#1a1a1a'),
                borderRadius=None,
                backColor=None
            ),
            'JobTitle': ParagraphStyle(
                'JobTitle',
                parent=styles['Normal'],
                fontSize=10,  # Reduced from 11
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=1,  # Reduced from 2
                fontName='Helvetica-Bold'
            ),
            'Company': ParagraphStyle(
                'Company',
                parent=styles['Normal'],
                fontSize=9,  # Reduced from 10
                textColor=colors.HexColor('#333333'),
                spaceAfter=1,  # Reduced from 2
                fontName='Helvetica-Oblique'
            ),
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=styles['Normal'],
                fontSize=9,  # Reduced from 10
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=4,  # Reduced from 6
                leading=11  # Reduced from 14
            ),
            'BulletPoint': ParagraphStyle(
                'BulletPoint',
                parent=styles['Normal'],
                fontSize=9,  # Reduced from 10
                textColor=colors.HexColor('#1a1a1a'),
                leftIndent=15,  # Reduced from 20
                spaceAfter=2,  # Reduced from 4
                leading=11  # Reduced from 13
            )
        }
        
        return custom_styles
    
    def generate_pdf(
        self,
        resume_data: TailoredResumeData,
        filename: str,
        save_to_disk: bool = True
    ) -> tuple[bytes, Path]:
        """
        Generate ATS-optimized ONE-PAGE PDF resume
        
        Returns:
            Tuple of (pdf_bytes, file_path)
        """
        # Create PDF in memory with REDUCED MARGINS
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,  # Reduced from 0.75
            leftMargin=0.5*inch,   # Reduced from 0.75
            topMargin=0.5*inch,    # Reduced from 0.75
            bottomMargin=0.5*inch  # Reduced from 0.75
        )
        
        # Build content
        story = []
        
        # Header - Contact Information
        story.extend(self._build_header(resume_data.contact_info))
        
        # Professional Summary
        if resume_data.professional_summary:
            story.extend(self._build_summary(resume_data.professional_summary))
        
        # Skills Section
        if resume_data.skills:
            story.extend(self._build_skills(resume_data.skills))
        
        # Experience Section
        if resume_data.experience:
            story.extend(self._build_experience(resume_data.experience))
        
        # Education Section
        if resume_data.education:
            story.extend(self._build_education(resume_data.education))
        
        # Projects (limited to 2 for one-page)
        if resume_data.projects:
            story.extend(self._build_projects(resume_data.projects))
        
        # Certifications
        if resume_data.certifications:
            story.extend(self._build_certifications(resume_data.certifications))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to disk if requested
        file_path = self.output_dir / filename
        if save_to_disk:
            file_path.write_bytes(pdf_bytes)
        
        return pdf_bytes, file_path
    
    def _build_header(self, contact_info: dict) -> List:
        """Build contact information header"""
        elements = []
        
        # Name
        name = contact_info.get('name', '')
        elements.append(Paragraph(name, self.styles['CustomTitle']))
        
        # Contact details in one line
        contact_parts = []
        if email := contact_info.get('email'):
            contact_parts.append(email)
        if phone := contact_info.get('phone'):
            contact_parts.append(phone)
        if location := contact_info.get('location'):
            contact_parts.append(location)
        if linkedin := contact_info.get('linkedin'):
            contact_parts.append(f"LinkedIn: {linkedin}")
        if github := contact_info.get('github'):
            contact_parts.append(f"GitHub: {github}")
        
        contact_line = " | ".join(contact_parts)
        elements.append(Paragraph(contact_line, self.styles['ContactInfo']))
        elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        
        return elements
    
    def _build_summary(self, summary: str) -> List:
        """Build professional summary section"""
        elements = []
        elements.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeader']))
        elements.append(Paragraph(summary, self.styles['BodyText']))
        elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        return elements
    
    def _build_skills(self, skills: List[str]) -> List:
        """Build skills section with ATS keyword optimization"""
        elements = []
        elements.append(Paragraph("SKILLS", self.styles['SectionHeader']))
        
        # Group skills in a clean, parseable format
        skills_text = " • ".join(skills)
        elements.append(Paragraph(skills_text, self.styles['BodyText']))
        elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        
        return elements
    
    def _build_experience(self, experiences: List[dict]) -> List:
        """Build work experience section - LIMITED TO 3 BULLETS PER JOB"""
        elements = []
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles['SectionHeader']))
        
        for exp in experiences:
            exp_elements = []
            
            # Job title
            title = exp.get('title', '')
            exp_elements.append(Paragraph(title, self.styles['JobTitle']))
            
            # Company and dates
            company = exp.get('company', '')
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', 'Present')
            company_line = f"{company} | {start_date} - {end_date}"
            exp_elements.append(Paragraph(company_line, self.styles['Company']))
            
            # Location if available
            if location := exp.get('location'):
                exp_elements.append(Paragraph(location, self.styles['Company']))
            
            # Responsibilities/achievements - LIMITED TO 3 BULLETS
            if responsibilities := exp.get('responsibilities', []):
                for resp in responsibilities[:3]:  # LIMIT TO 3 BULLETS
                    bullet = f"• {resp}"
                    exp_elements.append(Paragraph(bullet, self.styles['BulletPoint']))
            
            exp_elements.append(Spacer(1, 0.08*inch))  # Reduced from 0.15
            
            # Keep experience together
            elements.append(KeepTogether(exp_elements))
        
        return elements
    
    def _build_education(self, education: List[dict]) -> List:
        """Build education section"""
        elements = []
        elements.append(Paragraph("EDUCATION", self.styles['SectionHeader']))
        
        for edu in education:
            edu_elements = []
            
            # Degree
            degree = edu.get('degree', '')
            edu_elements.append(Paragraph(degree, self.styles['JobTitle']))
            
            # Institution and dates
            institution = edu.get('institution', '')
            grad_date = edu.get('graduation_date', '')
            edu_line = f"{institution} | {grad_date}"
            edu_elements.append(Paragraph(edu_line, self.styles['Company']))
            
            # Additional details (GPA, honors, etc.) - COMPACT
            details = []
            if gpa := edu.get('gpa'):
                details.append(f"GPA: {gpa}")
            if honors := edu.get('honors'):
                details.append(honors)
            
            if details:
                edu_elements.append(Paragraph(" | ".join(details), self.styles['BodyText']))
            
            edu_elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
            elements.append(KeepTogether(edu_elements))
        
        return elements
    
    def _build_certifications(self, certifications: List[dict]) -> List:
        """Build certifications section"""
        elements = []
        elements.append(Paragraph("CERTIFICATIONS", self.styles['SectionHeader']))
        
        for cert in certifications:
            cert_name = cert.get('name', '')
            issuer = cert.get('issuer', '')
            date = cert.get('date', '')
            
            cert_line = f"• {cert_name} - {issuer}"
            if date:
                cert_line += f" ({date})"
            
            elements.append(Paragraph(cert_line, self.styles['BulletPoint']))
        
        elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
        return elements
    
    def _build_projects(self, projects: List[dict]) -> List:
        """Build projects section - LIMITED TO 2 PROJECTS"""
        elements = []
        elements.append(Paragraph("PROJECTS", self.styles['SectionHeader']))
        
        for proj in projects[:2]:  # LIMIT TO 2 PROJECTS FOR ONE-PAGE
            proj_elements = []
            
            # Project name
            name = proj.get('name', '')
            proj_elements.append(Paragraph(name, self.styles['JobTitle']))
            
            # Technologies
            if technologies := proj.get('technologies'):
                tech_str = ", ".join(technologies) if isinstance(technologies, list) else technologies
                proj_elements.append(Paragraph(f"Technologies: {tech_str}", self.styles['Company']))
            
            # Description
            if description := proj.get('description'):
                proj_elements.append(Paragraph(description, self.styles['BodyText']))
            
            # Highlights - LIMITED TO 2 HIGHLIGHTS
            if highlights := proj.get('highlights', []):
                for highlight in highlights[:2]:  # LIMIT TO 2 HIGHLIGHTS
                    proj_elements.append(Paragraph(f"• {highlight}", self.styles['BulletPoint']))
            
            proj_elements.append(Spacer(1, 0.05*inch))  # Reduced from 0.1
            elements.append(KeepTogether(proj_elements))
        
        return elements
    
    def calculate_ats_score(
        self,
        resume_data: TailoredResumeData,
        job_keywords: List[str]
    ) -> ATSScores:
        """
        Calculate ATS compatibility scores
        
        Args:
            resume_data: The tailored resume content
            job_keywords: Required keywords from job posting
        
        Returns:
            ATSScores with detailed metrics
        """
        # Extract all text from resume
        resume_text = self._extract_all_text(resume_data).lower()
        
        # Check keyword matches
        matched = []
        missing = []
        
        for keyword in job_keywords:
            if keyword.lower() in resume_text:
                matched.append(keyword)
            else:
                missing.append(keyword)
        
        # Calculate metrics
        keyword_match_rate = (len(matched) / len(job_keywords) * 100) if job_keywords else 0
        
        # Formatting score (ATS-friendly features)
        formatting_score = self._calculate_formatting_score(resume_data)
        
        # Overall score (weighted average)
        overall_score = (keyword_match_rate * 0.7) + (formatting_score * 0.3)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            keyword_match_rate, 
            formatting_score, 
            missing
        )
        
        return ATSScores(
            overall_score=round(overall_score, 2),
            keyword_match_rate=round(keyword_match_rate, 2),
            matched_keywords=matched,
            missing_keywords=missing,
            formatting_score=round(formatting_score, 2),
            recommendations=recommendations
        )
    
    def _extract_all_text(self, resume_data: TailoredResumeData) -> str:
        """Extract all text content from resume for keyword analysis"""
        text_parts = [resume_data.professional_summary]
        
        # Skills
        text_parts.extend(resume_data.skills)
        
        # Experience
        for exp in resume_data.experience:
            text_parts.append(exp.get('title', ''))
            text_parts.append(exp.get('company', ''))
            text_parts.extend(exp.get('responsibilities', []))
        
        # Education
        for edu in resume_data.education:
            text_parts.append(edu.get('degree', ''))
            text_parts.append(edu.get('institution', ''))
        
        # Projects
        if resume_data.projects:
            for proj in resume_data.projects:
                text_parts.append(proj.get('name', ''))
                text_parts.append(proj.get('description', ''))
        
        return " ".join(filter(None, text_parts))
    
    def _calculate_formatting_score(self, resume_data: TailoredResumeData) -> float:
        """Calculate formatting score based on ATS-friendly features"""
        score = 100.0
        
        # Deduct points for missing sections
        if not resume_data.professional_summary:
            score -= 10
        if not resume_data.skills:
            score -= 15
        if not resume_data.experience:
            score -= 20
        if not resume_data.education:
            score -= 10
        
        # Check contact info completeness
        contact = resume_data.contact_info
        required_fields = ['name', 'email', 'phone']
        for field in required_fields:
            if not contact.get(field):
                score -= 5
        
        return max(0.0, score)
    
    def _generate_recommendations(
        self,
        keyword_match_rate: float,
        formatting_score: float,
        missing_keywords: List[str]
    ) -> List[str]:
        """Generate ATS improvement recommendations"""
        recommendations = []
        
        if keyword_match_rate < 70:
            recommendations.append(
                f"Add these missing keywords to improve match rate: {', '.join(missing_keywords[:5])}"
            )
        
        if formatting_score < 90:
            recommendations.append(
                "Ensure all standard sections are present (Summary, Skills, Experience, Education)"
            )
        
        if keyword_match_rate >= 80:
            recommendations.append("Excellent keyword coverage! Resume is well-optimized.")
        
        return recommendations