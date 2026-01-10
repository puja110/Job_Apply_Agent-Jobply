-- PostgreSQL Schema
-- File: migrations/001_initial_schema.sql

-- Raw jobs table (stores original scraped data)
CREATE TABLE raw_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    url TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    scraped_at TIMESTAMP NOT NULL DEFAULT NOW(),
    content_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT unique_platform_url UNIQUE (platform, url),
    CONSTRAINT unique_content_hash UNIQUE (content_hash)
);

CREATE INDEX idx_raw_jobs_platform ON raw_jobs(platform);
CREATE INDEX idx_raw_jobs_scraped_at ON raw_jobs(scraped_at DESC);
CREATE INDEX idx_raw_jobs_content_hash ON raw_jobs(content_hash);

-- Normalized jobs table (clean, structured data)
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_job_id UUID REFERENCES raw_jobs(id),
    
    -- Core fields
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    location_type VARCHAR(50), -- 'remote', 'hybrid', 'onsite'
    
    -- Job details
    description TEXT NOT NULL,
    requirements TEXT,
    responsibilities TEXT,
    
    -- Compensation
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(3) DEFAULT 'USD',
    salary_period VARCHAR(20), -- 'hourly', 'yearly', 'monthly'
    
    -- Metadata
    employment_type VARCHAR(50), -- 'full-time', 'part-time', 'contract'
    experience_level VARCHAR(50), -- 'entry', 'mid', 'senior', 'lead'
    posted_date TIMESTAMP,
    expires_date TIMESTAMP,
    
    -- Platform info
    platform VARCHAR(50) NOT NULL,
    platform_url TEXT NOT NULL,
    apply_url TEXT,
    
    -- Derived fields
    skills JSONB, -- ['Python', 'React', 'AWS']
    keywords JSONB, -- Extracted keywords
    
    -- Processing
    processed_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'expired', 'filled'
    
    CONSTRAINT unique_platform_url_jobs UNIQUE (platform, platform_url)
);

CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_posted_date ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_skills ON jobs USING GIN (skills);

-- Search logs (track what we've searched for)
CREATE TABLE job_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    search_query VARCHAR(500) NOT NULL,
    location VARCHAR(255),
    platform VARCHAR(50) NOT NULL,
    filters JSONB,
    
    results_count INTEGER,
    new_jobs_count INTEGER,
    
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50), -- 'pending', 'completed', 'failed'
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_job_searches_platform ON job_searches(platform);
CREATE INDEX idx_job_searches_created_at ON job_searches(created_at DESC);

-- Rate limiting tracker
CREATE TABLE rate_limits (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255),
    
    requests_count INTEGER DEFAULT 0,
    window_start TIMESTAMP NOT NULL,
    window_duration_seconds INTEGER NOT NULL,
    
    last_request_at TIMESTAMP,
    
    CONSTRAINT unique_platform_endpoint_window UNIQUE (platform, endpoint, window_start)
);

CREATE INDEX idx_rate_limits_platform ON rate_limits(platform);