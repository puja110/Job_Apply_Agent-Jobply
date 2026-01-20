"""
Repository for generated resumes database operations
"""
from typing import Optional, List
from uuid import UUID
import asyncpg
import json

from models.generated_resume import (
    GeneratedResume,
    GeneratedResumeCreate,
    GeneratedResumeUpdate,
    TailoredResumeData
)


class ResumeRepository:
    """Database operations for generated resumes"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool
    
    async def create(self, resume: GeneratedResumeCreate) -> GeneratedResume:
        """Create a new generated resume"""
        query = """
            INSERT INTO generated_resumes (
                user_profile_id, job_id, filename, file_path, file_size_bytes,
                resume_data, ats_score, keyword_match_rate, matched_keywords,
                missing_keywords, pdf_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING *
        """
        
        resume_data_json = resume.resume_data.model_dump_json()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                resume.user_profile_id,
                resume.job_id,
                resume.filename,
                resume.file_path,
                resume.file_size_bytes,
                resume_data_json,
                resume.ats_score,
                resume.keyword_match_rate,
                resume.matched_keywords,
                resume.missing_keywords,
                resume.pdf_data
            )
            return self._row_to_model(row)
    
    async def get_by_id(self, resume_id: UUID) -> Optional[GeneratedResume]:
        """Get resume by ID"""
        query = "SELECT * FROM generated_resumes WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, resume_id)
            return self._row_to_model(row) if row else None
    
    async def get_by_user_and_job(
        self,
        user_profile_id: UUID,
        job_id: UUID
    ) -> Optional[GeneratedResume]:
        """Get resume for a specific user and job"""
        query = """
            SELECT * FROM generated_resumes 
            WHERE user_profile_id = $1 AND job_id = $2
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_profile_id, job_id)
            return self._row_to_model(row) if row else None
    
    async def list_by_user(
        self,
        user_profile_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[GeneratedResume]:
        """List all resumes for a user"""
        query = """
            SELECT * FROM generated_resumes 
            WHERE user_profile_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_profile_id, limit, offset)
            return [self._row_to_model(row) for row in rows]
    
    async def list_by_job(
        self,
        job_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[GeneratedResume]:
        """List all resumes for a specific job"""
        query = """
            SELECT * FROM generated_resumes 
            WHERE job_id = $1
            ORDER BY created_at DESC
            LIMIT $2 OFFSET $3
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, job_id, limit, offset)
            return [self._row_to_model(row) for row in rows]
    
    async def update(
        self,
        resume_id: UUID,
        updates: GeneratedResumeUpdate
    ) -> Optional[GeneratedResume]:
        """Update a generated resume"""
        # Build dynamic update query based on provided fields
        update_fields = []
        params = []
        param_count = 1
        
        update_dict = updates.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            if field == 'resume_data' and value is not None:
                value = value.model_dump_json()
            update_fields.append(f"{field} = ${param_count}")
            params.append(value)
            param_count += 1
        
        if not update_fields:
            return await self.get_by_id(resume_id)
        
        params.append(resume_id)
        query = f"""
            UPDATE generated_resumes 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            return self._row_to_model(row) if row else None
    
    async def delete(self, resume_id: UUID) -> bool:
        """Delete a generated resume"""
        query = "DELETE FROM generated_resumes WHERE id = $1 RETURNING id"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, resume_id)
            return row is not None
    
    async def get_statistics(self, user_profile_id: UUID) -> dict:
        """Get statistics for user's generated resumes"""
        query = """
            SELECT 
                COUNT(*) as total_resumes,
                AVG(ats_score) as avg_ats_score,
                AVG(keyword_match_rate) as avg_keyword_match,
                AVG(file_size_bytes) as avg_file_size,
                MIN(created_at) as first_generated,
                MAX(created_at) as last_generated
            FROM generated_resumes
            WHERE user_profile_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_profile_id)
            return {
                'total_resumes': row['total_resumes'],
                'avg_ats_score': float(row['avg_ats_score']) if row['avg_ats_score'] else 0,
                'avg_keyword_match': float(row['avg_keyword_match']) if row['avg_keyword_match'] else 0,
                'avg_file_size_kb': round(row['avg_file_size'] / 1024, 2) if row['avg_file_size'] else 0,
                'first_generated': row['first_generated'],
                'last_generated': row['last_generated']
            }
    
    async def get_top_scored_resumes(
        self,
        user_profile_id: UUID,
        limit: int = 10
    ) -> List[GeneratedResume]:
        """Get top-scored resumes by ATS score"""
        query = """
            SELECT * FROM generated_resumes 
            WHERE user_profile_id = $1 AND ats_score IS NOT NULL
            ORDER BY ats_score DESC, created_at DESC
            LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_profile_id, limit)
            return [self._row_to_model(row) for row in rows]
    
    def _row_to_model(self, row: asyncpg.Record) -> GeneratedResume:
        """Convert database row to GeneratedResume model"""
        resume_data = TailoredResumeData.model_validate_json(row['resume_data'])
        
        return GeneratedResume(
            id=row['id'],
            user_profile_id=row['user_profile_id'],
            job_id=row['job_id'],
            filename=row['filename'],
            file_path=row['file_path'],
            file_size_bytes=row['file_size_bytes'],
            resume_data=resume_data,
            ats_score=row['ats_score'],
            keyword_match_rate=row['keyword_match_rate'],
            matched_keywords=row['matched_keywords'],
            missing_keywords=row['missing_keywords'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            pdf_data=row['pdf_data']
        )