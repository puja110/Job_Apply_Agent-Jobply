-- Database schema extension for storing generated PDF resumes
-- SQL Migration for PDF storage

-- Table for storing generated resumes
CREATE TABLE IF NOT EXISTS generated_resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_profile_id UUID NOT NULL REFERENCES user_profile(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    
    -- PDF metadata
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    
    -- Resume content (JSON)
    resume_data JSONB NOT NULL,
    
    -- ATS scores
    ats_score FLOAT,
    keyword_match_rate FLOAT,
    matched_keywords TEXT[],
    missing_keywords TEXT[],
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Optional: Store PDF binary data directly in database
    pdf_data BYTEA,
    
    -- Unique constraint: one resume per user-job combination
    CONSTRAINT unique_user_job_resume UNIQUE(user_profile_id, job_id)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_generated_resumes_user_profile 
    ON generated_resumes(user_profile_id);

CREATE INDEX IF NOT EXISTS idx_generated_resumes_job 
    ON generated_resumes(job_id);

CREATE INDEX IF NOT EXISTS idx_generated_resumes_created_at 
    ON generated_resumes(created_at DESC);

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_generated_resumes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at on row updates
CREATE TRIGGER trigger_update_generated_resumes_updated_at
    BEFORE UPDATE ON generated_resumes
    FOR EACH ROW
    EXECUTE FUNCTION update_generated_resumes_updated_at();