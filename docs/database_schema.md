# Database Schema

This document describes the database schema for the Theme Evolution System.

## Overview

The system uses PostgreSQL with the pgvector extension for efficient vector similarity search. All tables are designed to support the theme evolution workflow with proper indexing and relationships.

## Core Tables

### 1. extracted_themes

Stores the themes extracted from survey responses.

```sql
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
```

**Fields:**
- `id`: Unique theme identifier
- `name`: Theme name (e.g., "API Integration Challenges")
- `description`: Detailed theme description
- `embedding`: Vector embedding for similarity search
- `created_at_batch`: Batch number when theme was first created
- `last_updated_batch`: Batch number when theme was last updated
- `status`: Theme status (active, merged, split, deleted)
- `parent_theme_id`: Reference to parent theme (for splits)
- `response_count`: Number of responses assigned to this theme
- `metadata`: Additional theme metadata (JSON)

### 2. survey_responses

Stores individual survey responses.

```sql
CREATE TABLE survey_responses (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    response_text TEXT NOT NULL,
    embedding VECTOR(768),
    processed_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id`: Unique response identifier
- `batch_id`: Batch number this response belongs to
- `question`: The survey question
- `response_text`: The actual response text
- `embedding`: Vector embedding for similarity search
- `processed_at`: When the response was processed

### 3. theme_assignments

Maps responses to themes with confidence scores and highlighted keywords.

```sql
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
```

**Fields:**
- `id`: Unique assignment identifier
- `response_id`: Reference to survey response
- `theme_id`: Reference to theme
- `confidence_score`: Similarity score (0-1)
- `highlighted_keywords`: JSON array of highlighted keywords with scores
- `assigned_at_batch`: Batch when assignment was made
- `last_updated_batch`: Batch when assignment was last updated

### 4. theme_evolution_log

Tracks all theme changes over time.

```sql
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
```

**Fields:**
- `id`: Unique log entry identifier
- `batch_id`: Batch number when change occurred
- `action`: Type of change (created, updated, merged, split, deleted)
- `theme_id`: Primary theme involved
- `related_theme_id`: Secondary theme (for merges/splits)
- `details`: Additional change details (JSON)
- `affected_response_count`: Number of responses affected

### 5. batch_metadata

Stores processing metadata for each batch.

```sql
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
```

**Fields:**
- `batch_id`: Batch identifier
- `question`: Survey question for this batch
- `total_responses`: Number of responses in batch
- `new_themes_count`: Number of new themes created
- `updated_themes_count`: Number of themes updated
- `deleted_themes_count`: Number of themes deleted/merged
- `processing_time_seconds`: Time taken to process batch
- `processed_at`: When batch was processed

### 6. embedding_cache

Caches embeddings for performance optimization.

```sql
CREATE TABLE embedding_cache (
    id SERIAL PRIMARY KEY,
    text_hash VARCHAR(64) UNIQUE NOT NULL,
    embedding VECTOR(768),
    model_name VARCHAR(100) DEFAULT 'nomic-embed-text',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Fields:**
- `id`: Unique cache entry identifier
- `text_hash`: SHA-256 hash of the text
- `embedding`: Cached embedding vector
- `model_name`: Embedding model used
- `created_at`: When embedding was cached

## Indexes

### Performance Indexes

```sql
-- Vector similarity search indexes
CREATE INDEX idx_themes_embedding ON extracted_themes USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_responses_embedding ON survey_responses USING ivfflat (embedding vector_cosine_ops);

-- Status and batch indexes
CREATE INDEX idx_themes_status ON extracted_themes(status);
CREATE INDEX idx_responses_batch ON survey_responses(batch_id);

-- Assignment indexes
CREATE INDEX idx_assignments_response ON theme_assignments(response_id);
CREATE INDEX idx_assignments_theme ON theme_assignments(theme_id);

-- Evolution log index
CREATE INDEX idx_evolution_batch ON theme_evolution_log(batch_id);

-- Cache index
CREATE INDEX idx_embedding_cache_hash ON embedding_cache(text_hash);
```

## Relationships

### Entity Relationship Diagram

```
survey_responses (1) ←→ (M) theme_assignments (M) ←→ (1) extracted_themes
        ↓                           ↓
   batch_metadata              theme_evolution_log
        ↓
   embedding_cache
```

### Key Relationships

1. **Survey Response → Theme Assignment**: One-to-many
2. **Theme → Theme Assignment**: One-to-many
3. **Theme → Theme Evolution Log**: One-to-many
4. **Batch → Survey Responses**: One-to-many
5. **Batch → Batch Metadata**: One-to-one

## Vector Operations

### Similarity Search

The system uses cosine similarity for theme matching:

```sql
-- Find similar themes
SELECT *, 1 - (embedding <=> %s) as similarity
FROM extracted_themes 
WHERE status = 'active' AND 1 - (embedding <=> %s) > %s
ORDER BY embedding <=> %s
LIMIT %s;

-- Find similar responses
SELECT *, 1 - (embedding <=> %s) as similarity
FROM survey_responses 
WHERE embedding IS NOT NULL AND 1 - (embedding <=> %s) > %s
ORDER BY embedding <=> %s
LIMIT %s;
```

### Distance Operators

- `<=>`: Cosine distance (0 = identical, 2 = opposite)
- `1 - (embedding <=> embedding)`: Cosine similarity (0 = opposite, 1 = identical)

## Data Types

### Vector Dimensions

- **Embedding Size**: 768 dimensions (nomic-embed-text)
- **Vector Type**: `VECTOR(768)`
- **Index Type**: `ivfflat` for fast approximate search

### JSON Fields

- **highlighted_keywords**: Array of keyword objects with scores and positions
- **metadata**: Theme metadata including extraction method, model info
- **details**: Evolution log details including change descriptions

## Performance Considerations

### Query Optimization

1. **Vector Search**: Use IVFFlat indexes for fast similarity search
2. **Batch Queries**: Filter by batch_id for efficient data retrieval
3. **Status Filtering**: Use status indexes for active theme queries
4. **Cache Hits**: Check embedding_cache before generating new embeddings

### Storage Optimization

1. **Embedding Compression**: Consider compression for large datasets
2. **Index Maintenance**: Regular VACUUM and ANALYZE operations
3. **Partitioning**: Consider partitioning by batch_id for very large datasets

## Backup and Recovery

### Backup Strategy

```bash
# Full database backup
pg_dump -h localhost -U postgres theme_evolution > backup.sql

# Schema-only backup
pg_dump -h localhost -U postgres --schema-only theme_evolution > schema.sql

# Data-only backup
pg_dump -h localhost -U postgres --data-only theme_evolution > data.sql
```

### Recovery

```bash
# Restore from backup
psql -h localhost -U postgres theme_evolution < backup.sql
```

## Monitoring

### Key Metrics

1. **Database Size**: Monitor growth of vector embeddings
2. **Query Performance**: Track similarity search times
3. **Cache Hit Rate**: Monitor embedding cache effectiveness
4. **Index Usage**: Ensure indexes are being used effectively

### Health Checks

```sql
-- Check database health
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename IN ('extracted_themes', 'survey_responses');

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public';
```
