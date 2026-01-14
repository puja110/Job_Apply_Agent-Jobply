# utils/html_parser.py
from bs4 import BeautifulSoup
from typing import Optional, List
import re
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class IndeedHTMLParser:
    """Parser for Indeed job search results and job detail pages."""
    
    @staticmethod
    def parse_search_results(html: str) -> List[dict]:
        """
        Parse Indeed search results page.
        Returns list of job cards with basic info.
        """
        soup = BeautifulSoup(html, 'lxml')
        jobs = []
        
        # Indeed uses different selectors depending on region/layout
        # Try multiple selectors for robustness
        job_cards = soup.select('div.job_seen_beacon') or \
                   soup.select('td.resultContent') or \
                   soup.select('div.jobsearch-SerpJobCard')
        
        logger.info(f"Found {len(job_cards)} job cards")
        
        for card in job_cards:
            try:
                job_data = IndeedHTMLParser._parse_job_card(card)
                if job_data:
                    jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Failed to parse job card: {e}")
                continue
        
        return jobs
    
    @staticmethod
    def _parse_job_card(card) -> Optional[dict]:
        """Parse individual job card from search results."""
        try:
            # Title and URL
            title_elem = card.select_one('h2.jobTitle a') or \
                        card.select_one('a[data-jk]') or \
                        card.select_one('h2 a')
            
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            job_key = title_elem.get('data-jk') or \
                     re.search(r'/rc/clk\?jk=([a-f0-9]+)', title_elem.get('href', ''))
            
            if not job_key:
                return None
            
            job_key = job_key if isinstance(job_key, str) else job_key.group(1)
            
            # Company
            company_elem = card.select_one('span[data-testid="company-name"]') or \
                          card.select_one('span.companyName') or \
                          card.select_one('span.company')
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Location
            location_elem = card.select_one('div[data-testid="text-location"]') or \
                           card.select_one('div.companyLocation') or \
                           card.select_one('span.location')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Salary (if available)
            salary_elem = card.select_one('div.salary-snippet') or \
                         card.select_one('span.salary-snippet')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            # Job snippet (preview)
            snippet_elem = card.select_one('div.job-snippet') or \
                          card.select_one('div.summary')
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
            
            # Posted date
            date_elem = card.select_one('span.date') or \
                       card.select_one('span[data-testid="myJobsStateDate"]')
            posted_date = IndeedHTMLParser._parse_posted_date(
                date_elem.get_text(strip=True) if date_elem else None
            )
            
            # Build job URL
            job_url = f"https://www.indeed.com/viewjob?jk={job_key}"
            
            return {
                'job_key': job_key,
                'title': title,
                'company': company,
                'location': location,
                'salary': salary,
                'snippet': snippet,
                'posted_date': posted_date,
                'url': job_url
            }
            
        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None
    
    @staticmethod
    def _parse_posted_date(date_text: Optional[str]) -> Optional[datetime]:
        """
        Parse relative date strings like 'Just posted', '2 days ago', etc.
        """
        if not date_text:
            return None
        
        date_text = date_text.lower()
        now = datetime.utcnow()
        
        if 'just posted' in date_text or 'today' in date_text:
            return now
        
        # Match patterns like "2 days ago", "1 hour ago", etc.
        match = re.search(r'(\d+)\s+(minute|hour|day|week|month)s?\s+ago', date_text)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'minute':
                return now - timedelta(minutes=value)
            elif unit == 'hour':
                return now - timedelta(hours=value)
            elif unit == 'day':
                return now - timedelta(days=value)
            elif unit == 'week':
                return now - timedelta(weeks=value)
            elif unit == 'month':
                return now - timedelta(days=value * 30)
        
        return None
    
    @staticmethod
    def parse_job_details(html: str) -> dict:
        """
        Parse full job details page.
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Job title
        title_elem = soup.select_one('h1.jobsearch-JobInfoHeader-title')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Company
        company_elem = soup.select_one('div[data-company-name="true"]') or \
                      soup.select_one('a[data-testid="inlineHeader-companyName"]')
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
        
        # Location
        location_elem = soup.select_one('div[data-testid="inlineHeader-companyLocation"]')
        location = location_elem.get_text(strip=True) if location_elem else None
        
        # Job description
        desc_elem = soup.select_one('div#jobDescriptionText') or \
                   soup.select_one('div.jobsearch-jobDescriptionText')
        description = desc_elem.get_text(separator='\n', strip=True) if desc_elem else ""
        
        # Salary
        salary_elem = soup.select_one('div#salaryInfoAndJobType') or \
                     soup.select_one('span.salary')
        salary = salary_elem.get_text(strip=True) if salary_elem else None
        
        # Job type (full-time, part-time, etc.)
        job_type_elem = soup.select_one('span[data-testid="job-type-text"]')
        job_type = job_type_elem.get_text(strip=True) if job_type_elem else None
        
        return {
            'title': title,
            'company': company,
            'location': location,
            'description': description,
            'salary': salary,
            'job_type': job_type
        }