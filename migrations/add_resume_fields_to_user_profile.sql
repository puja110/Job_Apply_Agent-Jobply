-- Migration: Add resume-specific columns to user_profile table
-- This adds fields needed for generating complete PDF resumes

-- Add contact information fields
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS linkedin VARCHAR(255),
ADD COLUMN IF NOT EXISTS github VARCHAR(255),
ADD COLUMN IF NOT EXISTS portfolio_url VARCHAR(255);

-- Add detailed work experience (array of experience objects)
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS experience JSONB DEFAULT '[]'::jsonb;

-- Add education history (array of education objects)
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS education JSONB DEFAULT '[]'::jsonb;

-- Add projects (array of project objects)
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS projects JSONB DEFAULT '[]'::jsonb;

-- Add certifications (array of certification objects)
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS certifications JSONB DEFAULT '[]'::jsonb;

-- Add professional summary/bio
ALTER TABLE user_profile
ADD COLUMN IF NOT EXISTS professional_summary TEXT;

-- Add comments
COMMENT ON COLUMN user_profile.phone IS 'Contact phone number';
COMMENT ON COLUMN user_profile.linkedin IS 'LinkedIn profile URL';
COMMENT ON COLUMN user_profile.github IS 'GitHub profile URL';
COMMENT ON COLUMN user_profile.portfolio_url IS 'Personal portfolio/website URL';
COMMENT ON COLUMN user_profile.experience IS 'Array of work experience objects with title, company, dates, responsibilities';
COMMENT ON COLUMN user_profile.education IS 'Array of education objects with degree, institution, graduation date';
COMMENT ON COLUMN user_profile.projects IS 'Array of project objects with name, description, technologies, highlights';
COMMENT ON COLUMN user_profile.certifications IS 'Array of certification objects with name, issuer, date';
COMMENT ON COLUMN user_profile.professional_summary IS 'Professional summary/bio for resume header';

-- Verify the changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'user_profile'
ORDER BY ordinal_position;