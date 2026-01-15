-- migrations/002_scoring_system.sql

-- User profile table
CREATE TABLE user_profile (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic info
    name VARCHAR(255),
    email VARCHAR(255),
    
    -- Skills and experience
    skills JSONB NOT NULL, -- ['Python', 'React', 'AWS', ...]
    years_of_experience INTEGER,
    experience_level VARCHAR(50), -- 'junior', 'mid', 'senior', 'lead'
    
    -- Job preferences
    target_salary_min INTEGER,
    target_salary_max INTEGER,
    target_salary_currency VARCHAR(3) DEFAULT 'USD',
    preferred_location VARCHAR(255),
    remote_preference VARCHAR(50), -- 'remote_only', 'hybrid', 'onsite', 'flexible'
    willing_to_relocate BOOLEAN DEFAULT FALSE,
    
    -- Additional preferences
    preferred_company_sizes JSONB, -- ['startup', 'mid', 'enterprise']
    preferred_industries JSONB, -- ['fintech', 'healthcare', 'saas']
    
    -- Resume
    resume_path VARCHAR(500),
    resume_text TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Only one active profile at a time for single-user MVP
CREATE UNIQUE INDEX idx_user_profile_active ON user_profile(is_active) WHERE is_active = TRUE;

-- Job scores table
CREATE TABLE job_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    user_profile_id UUID REFERENCES user_profile(id) ON DELETE CASCADE,
    
    -- Overall score
    total_score DECIMAL(5,2) NOT NULL, -- 0-100
    rank INTEGER,
    
    -- Component scores (all 0-100)
    skill_match_score DECIMAL(5,2),
    salary_score DECIMAL(5,2),
    location_score DECIMAL(5,2),
    company_score DECIMAL(5,2),
    success_probability_score DECIMAL(5,2),
    
    -- Detailed breakdown
    matched_skills JSONB, -- Skills that match
    missing_skills JSONB, -- Skills required but not present
    skill_similarity DECIMAL(5,4), -- Cosine similarity
    
    -- Explanation
    score_explanation TEXT,
    match_highlights JSONB, -- Key reasons for the score
    
    -- Metadata
    scored_at TIMESTAMP DEFAULT NOW(),
    scoring_version VARCHAR(50) DEFAULT 'v1.0',
    
    CONSTRAINT unique_job_user_score UNIQUE (job_id, user_profile_id)
);

CREATE INDEX idx_job_scores_job_id ON job_scores(job_id);
CREATE INDEX idx_job_scores_user_profile_id ON job_scores(user_profile_id);
CREATE INDEX idx_job_scores_total_score ON job_scores(total_score DESC);
CREATE INDEX idx_job_scores_rank ON job_scores(rank);

-- Job embeddings table (for semantic search)
CREATE TABLE job_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- Embedding vector (we'll store as JSONB for now, can upgrade to pgvector later)
    embedding JSONB NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2',
    embedding_dimension INTEGER DEFAULT 384,
    
    -- Text that was embedded
    embedded_text TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_job_embedding UNIQUE (job_id)
);

CREATE INDEX idx_job_embeddings_job_id ON job_embeddings(job_id);