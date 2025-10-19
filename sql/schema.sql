-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Extracted themes table
CREATE TABLE extracted_themes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    embedding VECTOR(768),  -- nomic-embed-text dimensions
    created_at_batch INTEGER NOT NULL,
    last_updated_batch INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    parent_theme_id INTEGER REFERENCES extracted_themes(id),
    response_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Survey responses table
CREATE TABLE survey_responses (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    response_text TEXT NOT NULL,
    embedding VECTOR(768),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Theme assignments (many-to-many)
CREATE TABLE theme_assignments (
    id SERIAL PRIMARY KEY,
    response_id INTEGER REFERENCES survey_responses(id) ON DELETE CASCADE,
    theme_id INTEGER REFERENCES extracted_themes(id) ON DELETE CASCADE,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    highlighted_keywords JSONB,
    assigned_at_batch INTEGER NOT NULL,
    last_updated_batch INTEGER,
    UNIQUE(response_id, theme_id)
);

-- Theme evolution changelog
CREATE TABLE theme_evolution_log (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    theme_id INTEGER REFERENCES extracted_themes(id),
    related_theme_id INTEGER REFERENCES extracted_themes(id),
    details JSONB,
    affected_response_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Batch processing metadata
CREATE TABLE batch_metadata (
    batch_id INTEGER PRIMARY KEY,
    question TEXT NOT NULL,
    total_responses INTEGER,
    new_themes_count INTEGER DEFAULT 0,
    updated_themes_count INTEGER DEFAULT 0,
    deleted_themes_count INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- Embedding cache for cost optimization
CREATE TABLE embedding_cache (
    id SERIAL PRIMARY KEY,
    text_hash VARCHAR(64) UNIQUE NOT NULL,
    embedding VECTOR(768),
    model_name VARCHAR(100) DEFAULT 'nomic-embed-text',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_themes_embedding ON extracted_themes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_themes_status ON extracted_themes(status);
CREATE INDEX idx_responses_batch ON survey_responses(batch_id);
CREATE INDEX idx_responses_embedding ON survey_responses USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_assignments_response ON theme_assignments(response_id);
CREATE INDEX idx_assignments_theme ON theme_assignments(theme_id);
CREATE INDEX idx_evolution_batch ON theme_evolution_log(batch_id);
CREATE INDEX idx_embedding_cache_hash ON embedding_cache(text_hash);
