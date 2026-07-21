-- Migration: Add async crawl job support
-- Safe to run multiple times (idempotent)

-- Create crawl_jobs table
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    esp_id UUID NOT NULL,
    document_id UUID NOT NULL,

    -- Job metadata
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- Values: 'pending', 'processing', 'completed', 'failed', 'cancelled'
    priority INTEGER NOT NULL DEFAULT 0,
        -- Higher = process first. User-initiated = 10, scheduled = 0

    -- Retry logic
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error tracking
    error_message TEXT,
    error_traceback TEXT,

    -- Worker tracking
    worker_id VARCHAR(100),
        -- Which worker is processing this job

    -- Foreign keys
    CONSTRAINT fk_crawl_jobs_esp FOREIGN KEY (esp_id) REFERENCES esps(id) ON DELETE CASCADE,
    CONSTRAINT fk_crawl_jobs_document FOREIGN KEY (document_id) REFERENCES esp_documents(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_esp ON crawl_jobs(esp_id);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_created ON crawl_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_priority ON crawl_jobs(priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_document ON crawl_jobs(document_id);

-- Add columns to esp_documents (safe if already exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'esp_documents' AND column_name = 'crawl_job_id'
    ) THEN
        ALTER TABLE esp_documents ADD COLUMN crawl_job_id UUID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'esp_documents' AND column_name = 'is_crawling'
    ) THEN
        ALTER TABLE esp_documents ADD COLUMN is_crawling BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Add index for is_crawling queries
CREATE INDEX IF NOT EXISTS idx_esp_documents_is_crawling ON esp_documents(is_crawling) WHERE is_crawling = TRUE;

-- Comments for documentation
COMMENT ON TABLE crawl_jobs IS 'Background job queue for async URL crawling';
COMMENT ON COLUMN crawl_jobs.status IS 'Job status: pending, processing, completed, failed, cancelled';
COMMENT ON COLUMN crawl_jobs.priority IS 'Job priority (higher = process first)';
COMMENT ON COLUMN crawl_jobs.attempts IS 'Number of processing attempts (for retry logic)';
COMMENT ON COLUMN crawl_jobs.worker_id IS 'ID of worker processing this job (for distributed systems)';
