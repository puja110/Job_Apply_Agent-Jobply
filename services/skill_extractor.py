"""
Skill Extraction Service
Extracts technical skills from job descriptions using NLP and keyword matching
"""
import re
from typing import List, Set, Dict
import logging

logger = logging.getLogger(__name__)


class SkillExtractor:
    """Extract skills from job descriptions"""
    
    def __init__(self):
        """Initialize with comprehensive skill taxonomy"""
        self.skill_taxonomy = self._build_skill_taxonomy()
        self.skill_patterns = self._build_skill_patterns()
    
    def _build_skill_taxonomy(self) -> Dict[str, List[str]]:
        """
        Build a comprehensive taxonomy of technical skills
        Organized by category for better matching
        """
        return {
            # Programming Languages
            'languages': [
                'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 'Go', 'Golang',
                'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB',
                'Perl', 'Shell', 'Bash', 'PowerShell', 'SQL', 'HTML', 'CSS', 'Dart'
            ],
            
            # Web Frameworks
            'web_frameworks': [
                'React', 'ReactJS', 'React.js', 'Angular', 'AngularJS', 'Angular.js',
                'Vue', 'Vue.js', 'VueJS', 'Next.js', 'NextJS', 'Nuxt', 'Svelte',
                'Django', 'Flask', 'FastAPI', 'Express', 'Express.js', 'Node.js', 'NodeJS',
                'Spring', 'Spring Boot', 'ASP.NET', '.NET', 'Rails', 'Laravel', 'Symfony'
            ],
            
            # AI/ML
            'ai_ml': [
                'Machine Learning', 'ML', 'Deep Learning', 'Neural Networks', 'CNN', 'RNN',
                'Transformer', 'BERT', 'GPT', 'LLM', 'Large Language Model',
                'Natural Language Processing', 'NLP', 'Computer Vision', 'CV',
                'PyTorch', 'TensorFlow', 'Keras', 'Scikit-learn', 'XGBoost', 'LightGBM',
                'Hugging Face', 'OpenAI', 'Langchain', 'LlamaIndex',
                'Reinforcement Learning', 'RL', 'Supervised Learning', 'Unsupervised Learning',
                'Generative AI', 'GenAI', 'Stable Diffusion', 'Diffusion Models',
                'RAG', 'Retrieval Augmented Generation', 'Fine-tuning', 'Prompt Engineering',
                'AI Agents', 'Multi-agent Systems', 'AutoML'
            ],
            
            # Data Science
            'data_science': [
                'Pandas', 'NumPy', 'Matplotlib', 'Seaborn', 'Plotly',
                'Data Analysis', 'Data Visualization', 'Statistical Analysis',
                'A/B Testing', 'Hypothesis Testing', 'Time Series', 'Forecasting',
                'Feature Engineering', 'Data Mining', 'ETL', 'Data Pipeline'
            ],
            
            # Cloud & DevOps
            'cloud_devops': [
                'AWS', 'Amazon Web Services', 'EC2', 'S3', 'Lambda', 'SageMaker',
                'Azure', 'Microsoft Azure', 'GCP', 'Google Cloud', 'Google Cloud Platform',
                'Docker', 'Kubernetes', 'K8s', 'Terraform', 'Ansible', 'Jenkins',
                'CI/CD', 'GitLab CI', 'GitHub Actions', 'CircleCI', 'Travis CI',
                'Microservices', 'Serverless', 'Infrastructure as Code', 'IaC'
            ],
            
            # Databases
            'databases': [
                'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Cassandra',
                'DynamoDB', 'Neo4j', 'Graph Database', 'Vector Database', 'Pinecone', 'Weaviate',
                'Snowflake', 'BigQuery', 'Redshift', 'SQL Server', 'Oracle', 'SQLite'
            ],
            
            # Tools & Platforms
            'tools': [
                'Git', 'GitHub', 'GitLab', 'Bitbucket', 'Jira', 'Confluence',
                'VS Code', 'IntelliJ', 'PyCharm', 'Jupyter', 'Notebook',
                'Postman', 'Swagger', 'GraphQL', 'REST API', 'gRPC',
                'Apache Kafka', 'RabbitMQ', 'Celery', 'Airflow', 'Spark', 'Hadoop'
            ],
            
            # Soft Skills & Methodologies
            'methodologies': [
                'Agile', 'Scrum', 'Kanban', 'SAFe', 'Waterfall',
                'Test-Driven Development', 'TDD', 'Behavior-Driven Development', 'BDD',
                'Pair Programming', 'Code Review', 'System Design', 'Architecture',
                'Leadership', 'Mentoring', 'Communication', 'Collaboration'
            ]
        }
    
    def _build_skill_patterns(self) -> List[re.Pattern]:
        """Build regex patterns for skill extraction"""
        patterns = []
        
        # Flatten all skills from taxonomy
        all_skills = []
        for category_skills in self.skill_taxonomy.values():
            all_skills.extend(category_skills)
        
        # Create patterns for each skill (case-insensitive, word boundaries)
        for skill in all_skills:
            # Escape special regex characters
            escaped_skill = re.escape(skill)
            # Create pattern with word boundaries
            pattern = re.compile(r'\b' + escaped_skill + r'\b', re.IGNORECASE)
            patterns.append((skill, pattern))
        
        return patterns
    
    def extract_skills(self, text: str, max_skills: int = 50) -> List[str]:
        """
        Extract skills from text using pattern matching
        
        Args:
            text: Job description or any text
            max_skills: Maximum number of skills to return
            
        Returns:
            List of extracted skills (deduplicated and normalized)
        """
        if not text:
            return []
        
        found_skills = set()
        
        # Extract using patterns
        for skill, pattern in self.skill_patterns:
            if pattern.search(text):
                found_skills.add(skill)
        
        # Additional patterns for common variations
        found_skills.update(self._extract_additional_patterns(text))
        
        # Normalize and deduplicate
        normalized_skills = self._normalize_skills(found_skills)
        
        # Sort by importance (based on frequency in taxonomy)
        sorted_skills = sorted(normalized_skills, key=lambda s: self._get_skill_priority(s))
        
        return sorted_skills[:max_skills]
    
    def _extract_additional_patterns(self, text: str) -> Set[str]:
        """Extract skills using additional heuristics"""
        found = set()
        
        # Look for "X years of experience with Y" patterns
        experience_pattern = r'(\d+\+?\s*years?\s+(?:of\s+)?(?:experience\s+)?(?:with|in|using)\s+)([A-Za-z][A-Za-z0-9\s\.\+#-]+)'
        matches = re.finditer(experience_pattern, text, re.IGNORECASE)
        for match in matches:
            skill = match.group(2).strip()
            if len(skill) > 2 and len(skill) < 30:
                found.add(skill)
        
        # Look for "proficient in X" patterns
        proficient_pattern = r'(?:proficient|experienced|expert|skilled)\s+(?:in|with)\s+([A-Za-z][A-Za-z0-9\s\.\+#-]+)'
        matches = re.finditer(proficient_pattern, text, re.IGNORECASE)
        for match in matches:
            skill = match.group(1).strip()
            # Take only the first few words
            skill_words = skill.split()[:3]
            skill = ' '.join(skill_words)
            if len(skill) > 2 and len(skill) < 30:
                found.add(skill)
        
        return found
    
    def _normalize_skills(self, skills: Set[str]) -> List[str]:
        """
        Normalize skills to canonical forms
        Example: 'ReactJS', 'React.js' -> 'React'
        """
        normalized = set()
        skill_map = {}
        
        # Build canonical mapping
        for category, category_skills in self.skill_taxonomy.items():
            for skill in category_skills:
                canonical = skill
                # Find the shortest version as canonical
                variations = [s for s in category_skills if skill.lower().replace('.', '').replace(' ', '') in s.lower().replace('.', '').replace(' ', '')]
                if variations:
                    canonical = min(variations, key=len)
                skill_map[skill.lower()] = canonical
        
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in skill_map:
                normalized.add(skill_map[skill_lower])
            else:
                # Keep original if not in map
                normalized.add(skill.title())
        
        return list(normalized)
    
    def _get_skill_priority(self, skill: str) -> int:
        """
        Get priority of skill (lower number = higher priority)
        AI/ML skills get highest priority, then languages, then others
        """
        skill_lower = skill.lower()
        
        # Check each category
        for i, (category, skills) in enumerate(self.skill_taxonomy.items()):
            for taxonomy_skill in skills:
                if skill_lower == taxonomy_skill.lower():
                    # AI/ML highest priority (0), then languages (1), etc.
                    category_priority = {
                        'ai_ml': 0,
                        'languages': 1,
                        'data_science': 2,
                        'web_frameworks': 3,
                        'databases': 4,
                        'cloud_devops': 5,
                        'tools': 6,
                        'methodologies': 7
                    }
                    return category_priority.get(category, 10)
        
        return 100  # Unknown skills go last
    
    def categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """
        Categorize a list of skills
        
        Args:
            skills: List of skills
            
        Returns:
            Dictionary mapping category to list of skills
        """
        categorized = {category: [] for category in self.skill_taxonomy.keys()}
        categorized['other'] = []
        
        for skill in skills:
            skill_lower = skill.lower()
            found = False
            
            for category, category_skills in self.skill_taxonomy.items():
                for taxonomy_skill in category_skills:
                    if skill_lower == taxonomy_skill.lower():
                        categorized[category].append(skill)
                        found = True
                        break
                if found:
                    break
            
            if not found:
                categorized['other'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}


# Singleton instance
_skill_extractor_instance = None

def get_skill_extractor() -> SkillExtractor:
    """Get or create singleton instance"""
    global _skill_extractor_instance
    if _skill_extractor_instance is None:
        _skill_extractor_instance = SkillExtractor()
    return _skill_extractor_instance