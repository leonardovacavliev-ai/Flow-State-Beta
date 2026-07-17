-- Phase 4: ESP Management Database Schema
-- Purpose: Store ESP metadata and document links in PostgreSQL
-- Replaces: Filesystem docs/ folders and CSV files

-- ESPs Table
-- Stores ESP definitions (name, display name, status)
CREATE TABLE IF NOT EXISTS esps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,           -- URL-safe name (e.g., 'klaviyo', 'dotdigital')
    display_name VARCHAR(200) NOT NULL,          -- Human-readable name (e.g., 'Klaviyo', 'DotDigital')
    description TEXT,                            -- Optional description
    status VARCHAR(20) DEFAULT 'active',         -- 'active', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ESP Documents Table
-- Stores URLs and crawl metadata for each ESP
CREATE TABLE IF NOT EXISTS esp_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    esp_id UUID NOT NULL REFERENCES esps(id) ON DELETE CASCADE,
    url TEXT NOT NULL,                           -- Source URL to crawl
    filename VARCHAR(500),                       -- Saved filename in docs/
    content_hash VARCHAR(64),                    -- SHA-256 hash for change detection
    crawl_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'completed', 'failed'
    last_crawled_at TIMESTAMP,
    error_message TEXT,                          -- If crawl failed
    vector_ids JSONB,                            -- Array of vector DB chunk IDs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(esp_id, url)                          -- Prevent duplicate URLs per ESP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_esps_name ON esps(name);
CREATE INDEX IF NOT EXISTS idx_esps_status ON esps(status);
CREATE INDEX IF NOT EXISTS idx_esp_docs_esp_id ON esp_documents(esp_id);
CREATE INDEX IF NOT EXISTS idx_esp_docs_status ON esp_documents(crawl_status);
CREATE INDEX IF NOT EXISTS idx_esp_docs_url ON esp_documents(url);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
DROP TRIGGER IF EXISTS update_esps_updated_at ON esps;
CREATE TRIGGER update_esps_updated_at
    BEFORE UPDATE ON esps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_esp_documents_updated_at ON esp_documents;
CREATE TRIGGER update_esp_documents_updated_at
    BEFORE UPDATE ON esp_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE esps IS 'Email Service Providers configured in the system';
COMMENT ON TABLE esp_documents IS 'Documentation URLs for each ESP with crawl metadata';
COMMENT ON COLUMN esps.name IS 'URL-safe identifier (lowercase, no spaces)';
COMMENT ON COLUMN esps.display_name IS 'Human-readable name shown in UI';
COMMENT ON COLUMN esp_documents.vector_ids IS 'Array of vector database chunk IDs (JSON)';
COMMENT ON COLUMN esp_documents.content_hash IS 'SHA-256 hash of crawled content for change detection';
