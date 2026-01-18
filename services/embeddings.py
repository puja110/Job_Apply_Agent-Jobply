# services/embeddings.py
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Union
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generate and compare text embeddings for semantic matching."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model name. Default is fast and accurate.
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.embedding_dim}")
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """
        Generate embeddings for text(s) - returns numpy arrays.
        Compatible with scoring_engine.py expectations.
        
        Args:
            texts: Single text string or list of texts
            normalize: If True, normalize embeddings to unit length
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        # Filter out empty texts
        valid_texts = [t if t and t.strip() else "" for t in texts]
        embeddings = self.model.encode(
            valid_texts, 
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        
        return embeddings
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings (numpy arrays).
        Compatible with scoring_engine.py expectations.
        
        Args:
            embedding1: First embedding vector (numpy array)
            embedding2: Second embedding vector (numpy array)
            
        Returns:
            Similarity score between -1 and 1 (typically 0 to 1 for normalized embeddings)
        """
        # Handle 1D arrays
        if len(embedding1.shape) == 1:
            embedding1 = embedding1.reshape(1, -1)
        if len(embedding2.shape) == 1:
            embedding2 = embedding2.reshape(1, -1)
        
        # Compute cosine similarity
        similarity = sklearn_cosine_similarity(embedding1, embedding2)[0][0]
        
        return float(similarity)
    
    # Legacy methods (for backward compatibility)
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (legacy method).
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dim
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (legacy method).
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t if t and t.strip() else "" for t in texts]
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def compute_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings (legacy method).
        
        Args:
            embedding1: First embedding vector (list)
            embedding2: Second embedding vector (list)
            
        Returns:
            Similarity score between 0 and 1
        """
        # Convert to numpy arrays
        emb1 = np.array(embedding1).reshape(1, -1)
        emb2 = np.array(embedding2).reshape(1, -1)
        
        # Compute cosine similarity
        similarity = sklearn_cosine_similarity(emb1, emb2)[0][0]
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, similarity))
    
    def find_best_matches(
        self,
        query_embedding: Union[List[float], np.ndarray],
        candidate_embeddings: Union[List[List[float]], np.ndarray],
        top_k: int = 5
    ) -> List[Dict[str, float]]:
        """
        Find top K most similar embeddings.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            top_k: Number of top matches to return
            
        Returns:
            List of dicts with 'index' and 'similarity' keys
        """
        if not len(candidate_embeddings):
            return []
        
        # Convert to numpy if needed
        if isinstance(query_embedding, list):
            query = np.array(query_embedding).reshape(1, -1)
        else:
            query = query_embedding.reshape(1, -1)
        
        if isinstance(candidate_embeddings, list):
            candidates = np.array(candidate_embeddings)
        else:
            candidates = candidate_embeddings
        
        # Compute similarities
        similarities = sklearn_cosine_similarity(query, candidates)[0]
        
        # Get top K indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [
            {
                'index': int(idx),
                'similarity': float(similarities[idx])
            }
            for idx in top_indices
        ]
        
        return results
    
    def embed_job_description(self, job_data: Dict) -> str:
        """
        Create a combined text representation of a job for embedding.
        
        Args:
            job_data: Dictionary with job details
            
        Returns:
            Combined text string
        """
        parts = []
        
        # Title (most important)
        if job_data.get('title'):
            parts.append(f"Job Title: {job_data['title']}")
        
        # Description
        if job_data.get('description'):
            # Take first 500 chars of description
            desc = job_data['description'][:500]
            parts.append(f"Description: {desc}")
        
        # Skills
        if job_data.get('skills'):
            skills = job_data['skills']
            if isinstance(skills, list):
                skills_text = ', '.join(skills)
            else:
                skills_text = str(skills)
            parts.append(f"Required Skills: {skills_text}")
        
        # Company and location
        if job_data.get('company'):
            parts.append(f"Company: {job_data['company']}")
        
        if job_data.get('location'):
            parts.append(f"Location: {job_data['location']}")
        
        return ' | '.join(parts)
    
    def embed_user_profile(self, profile_data: Dict) -> str:
        """
        Create a combined text representation of user profile for embedding.
        
        Args:
            profile_data: Dictionary with profile details
            
        Returns:
            Combined text string
        """
        parts = []
        
        # Skills (most important)
        if profile_data.get('skills'):
            skills = profile_data['skills']
            if isinstance(skills, list):
                skills_text = ', '.join(skills)
            else:
                skills_text = str(skills)
            parts.append(f"Skills: {skills_text}")
        
        # Experience level
        if profile_data.get('experience_level'):
            parts.append(f"Experience Level: {profile_data['experience_level']}")
        
        # Years of experience
        if profile_data.get('years_of_experience'):
            parts.append(f"Years of Experience: {profile_data['years_of_experience']}")
        
        # Preferred industries
        if profile_data.get('preferred_industries'):
            industries = profile_data['preferred_industries']
            if isinstance(industries, list):
                industries_text = ', '.join(industries)
            else:
                industries_text = str(industries)
            parts.append(f"Interested in: {industries_text}")
        
        return ' | '.join(parts)