-- Healthcare Provider Database Schema for AI Voice Agent
-- Using PostgreSQL with pgvector for semantic search

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS unaccent; -- For accent-insensitive search

-- Main providers table
CREATE TABLE healthcare_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255), -- For search optimization
    provider_type VARCHAR(50), -- 'hospital', 'clinic', 'pharmacy', 'optical'

    -- Contact information
    phone_primary VARCHAR(50),
    phone_secondary VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),

    -- Location
    address TEXT,
    area VARCHAR(100),
    region VARCHAR(100),
    coordinates POINT, -- For distance calculations

    -- Services and metadata
    specialties TEXT[], -- Array of specialties
    services_description TEXT,

    -- AI/Search optimization
    search_vector tsvector, -- Full-text search
    embedding vector(1536), -- Semantic search embeddings
    search_keywords TEXT[], -- Common search terms

    -- Insurance and operational
    insurance_plans TEXT[], -- Supported insurance plans
    operating_hours JSONB, -- Flexible schedule storage
    is_active BOOLEAN DEFAULT true,
    is_emergency BOOLEAN DEFAULT false,

    -- Metadata
    source_sheet VARCHAR(50), -- Track which Excel sheet
    source_row_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Specialties reference table (for normalization)
CREATE TABLE specialties (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE, -- GP, PED, OBS/GYN, etc.
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50), -- 'primary_care', 'specialty', 'diagnostic'
    description TEXT,
    common_searches TEXT[] -- How users might ask for this
);

-- Provider-specialty junction table
CREATE TABLE provider_specialties (
    provider_id INTEGER REFERENCES healthcare_providers(id),
    specialty_id INTEGER REFERENCES specialties(id),
    is_primary BOOLEAN DEFAULT false,
    PRIMARY KEY (provider_id, specialty_id)
);

-- Areas/locations reference table
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    region VARCHAR(100),
    alternative_names TEXT[], -- Different ways to refer to the area
    coordinates POINT,
    nearby_landmarks TEXT[]
);

-- Search optimization indexes
CREATE INDEX idx_providers_name_trgm ON healthcare_providers USING gin (name gin_trgm_ops);
CREATE INDEX idx_providers_area_trgm ON healthcare_providers USING gin (area gin_trgm_ops);
CREATE INDEX idx_providers_specialties ON healthcare_providers USING gin (specialties);
CREATE INDEX idx_providers_search_vector ON healthcare_providers USING gin (search_vector);
CREATE INDEX idx_providers_embedding ON healthcare_providers USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_providers_location ON healthcare_providers USING gist (coordinates);
CREATE INDEX idx_providers_active ON healthcare_providers (is_active) WHERE is_active = true;

-- Function to update search vector automatically
CREATE OR REPLACE FUNCTION update_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.area, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.specialties, ' '), '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.services_description, '')), 'D');

    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update search vector
CREATE TRIGGER trigger_update_search_vector
    BEFORE INSERT OR UPDATE ON healthcare_providers
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Insert sample specialties
INSERT INTO specialties (code, name, category, common_searches) VALUES
('GP', 'General Practice', 'primary_care', ARRAY['general doctor', 'family doctor', 'primary care']),
('PED', 'Pediatrics', 'specialty', ARRAY['children doctor', 'kids doctor', 'pediatrician']),
('GYN', 'Obstetrics/Gynecology', 'specialty', ARRAY['women health', 'pregnancy', 'gynecologist']),
('ENT', 'Ear Nose Throat', 'specialty', ARRAY['ear doctor', 'throat doctor', 'ENT specialist']),
('OPH', 'Ophthalmology', 'specialty', ARRAY['eye doctor', 'vision', 'eye specialist']),
('PHY', 'Physiotherapy', 'specialty', ARRAY['physio', 'physical therapy', 'rehabilitation']),
('DEN', 'Dental', 'specialty', ARRAY['dentist', 'teeth', 'dental care']),
('PHARM', 'Pharmacy', 'service', ARRAY['pharmacy', 'medication', 'drugs', 'chemist']);

-- Function for AI agent queries with semantic search
CREATE OR REPLACE FUNCTION search_providers(
    query_text TEXT DEFAULT '',
    query_embedding vector(1536) DEFAULT NULL,
    area_filter TEXT DEFAULT NULL,
    specialty_filter TEXT DEFAULT NULL,
    max_results INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE(
    id INTEGER,
    name VARCHAR(255),
    area VARCHAR(100),
    specialties TEXT[],
    phone_primary VARCHAR(50),
    address TEXT,
    similarity_score FLOAT,
    text_rank FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.name,
        p.area,
        p.specialties,
        p.phone_primary,
        p.address,
        CASE
            WHEN query_embedding IS NOT NULL
            THEN 1 - (p.embedding <=> query_embedding)
            ELSE 0.0
        END as similarity_score,
        CASE
            WHEN query_text != ''
            THEN ts_rank_cd(p.search_vector, plainto_tsquery('english', query_text))
            ELSE 0.0
        END as text_rank
    FROM healthcare_providers p
    WHERE p.is_active = true
        AND (area_filter IS NULL OR p.area ILIKE '%' || area_filter || '%')
        AND (specialty_filter IS NULL OR specialty_filter = ANY(p.specialties))
        AND (
            query_text = '' OR
            p.search_vector @@ plainto_tsquery('english', query_text) OR
            p.name ILIKE '%' || query_text || '%'
        )
        AND (
            query_embedding IS NULL OR
            (1 - (p.embedding <=> query_embedding)) > similarity_threshold
        )
    ORDER BY
        GREATEST(similarity_score, text_rank) DESC,
        p.name
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;