# System Architecture

This document describes the architecture and design of the Theme Evolution System.

## Overview

The Theme Evolution System solves the critical challenge of **large-scale batch processing that exceeds LLM context windows**. It processes survey responses in intelligent chunks, maintains theme consistency across batches, and evolves themes over time using vector-based similarity matching and incremental processing.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Theme Evolution System                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │   Survey    │  │   Theme     │  │  Keyword    │  │  Theme  │ │
│  │  Responses  │  │ Extractor   │  │ Highlighter │  │ Evolver │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│         │                │                │              │      │
│         ▼                ▼                ▼              ▼      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Theme Processor (Orchestrator)                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Data Layer                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ PostgreSQL  │  │   Ollama    │  │   Embedding Cache   │ │ │
│  │  │ + pgvector  │  │ (Llama 3.1) │  │                     │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Theme Processor (Orchestrator)

**File**: `src/theme_processor.py`

The main orchestrator that coordinates all other components:

- **Responsibilities**:
  - Manages the complete processing pipeline
  - Coordinates between all components
  - Handles batch processing workflow
  - Manages error handling and logging

- **Key Methods**:
  - `process_batch()`: Process a single batch of responses
  - `process_multiple_batches()`: Process multiple batches
  - `test_system_health()`: Health check for all components

### 2. Theme Extractor

**File**: `src/theme_extractor.py`

Extracts themes from survey responses using Ollama/Llama:

- **Responsibilities**:
  - Generate themes from response batches
  - Update theme descriptions based on new data
  - Handle LLM communication and response parsing

- **Key Methods**:
  - `extract_themes_from_batch()`: Extract themes from responses
  - `update_theme_description()`: Update existing theme descriptions

### 3. Keyword Highlighter

**File**: `src/keyword_highlighter.py`

Identifies keywords that contribute to theme assignment:

- **Responsibilities**:
  - Extract n-grams (unigrams, bigrams, trigrams)
  - Calculate keyword contribution scores
  - Highlight relevant words/phrases

- **Key Methods**:
  - `highlight_keywords()`: Highlight keywords for a response-theme pair
  - `extract_phrases()`: Extract n-grams from text

### 4. Theme Evolver

**File**: `src/theme_evolver.py`

Handles theme evolution over time:

- **Responsibilities**:
  - Match responses to existing themes
  - Detect theme merges and splits
  - Update theme descriptions
  - Apply retroactive updates

- **Key Methods**:
  - `match_to_existing_themes()`: Match responses to themes
  - `detect_theme_merges()`: Find themes to merge
  - `detect_theme_splits()`: Find themes to split
  - `update_theme_description()`: Update theme descriptions

### 5. Embedding Service

**File**: `src/embedding_service.py`

Manages embeddings and similarity calculations:

- **Responsibilities**:
  - Generate embeddings using Ollama
  - Cache embeddings for efficiency
  - Calculate cosine similarity
  - Batch processing for performance

- **Key Methods**:
  - `get_embedding()`: Get embedding for text
  - `get_embeddings_batch()`: Batch embedding generation
  - `cosine_similarity()`: Calculate similarity between embeddings

### 6. Database Manager

**File**: `src/database.py`

Handles all database operations:

- **Responsibilities**:
  - CRUD operations for all entities
  - Vector similarity searches
  - Transaction management
  - Connection pooling

- **Key Methods**:
  - `save_response()`: Save survey response
  - `save_theme()`: Save theme
  - `find_similar_themes()`: Vector similarity search
  - `save_theme_assignment()`: Save response-theme mapping

## Data Flow

### 1. Large-Scale Batch Processing Flow

```
Large Dataset → Context-Aware Chunking → Batch Processing → Vector Similarity Matching → Theme Evolution → Retroactive Updates
```

**Key Innovation**: Breaks down datasets that exceed LLM context windows into manageable chunks while maintaining semantic coherence.

### 2. Context Window Management

```
Dataset Size > Context Limit → Intelligent Batching → LLM Processing → Vector Storage → Incremental Processing
```

**Technical Challenge**: Process millions of responses that cannot fit into single LLM calls while maintaining theme consistency.

### 3. Theme Evolution Across Batches

```
Batch 1 → Theme Creation → Vector Storage → Batch 2 → Similarity Matching → Theme Updates → Retroactive Processing
```

**State Management**: Maintain theme consistency across batches using vector embeddings and database persistence.

## Database Schema

### Core Tables

1. **survey_responses**: Stores survey responses with embeddings
2. **extracted_themes**: Stores themes with embeddings and metadata
3. **theme_assignments**: Maps responses to themes with confidence scores
4. **theme_evolution_log**: Tracks theme changes over time
5. **batch_metadata**: Stores processing metadata for each batch
6. **embedding_cache**: Caches embeddings for performance

### Vector Operations

- Uses pgvector extension for efficient similarity search
- IVFFlat indexes for fast vector queries
- Cosine similarity for theme matching

## Configuration

### Key Configuration Parameters

```yaml
thresholds:
  similarity_existing_theme: 0.75    # Match to existing theme
  similarity_update_candidate: 0.50  # Consider for theme update
  similarity_merge_themes: 0.85     # Merge themes threshold
  theme_split_variance: 0.40        # Split theme threshold
  keyword_contribution: 0.05        # Minimum keyword contribution

processing:
  batch_size: 100                   # Embedding batch size
  max_keywords_per_response: 10     # Max keywords per response
  theme_update_drift_threshold: 0.20 # Theme update threshold
```

## Performance Considerations

### 1. Embedding Caching

- All embeddings are cached in the database
- SHA-256 hashing for cache keys
- Significant cost savings for repeated text

### 2. Batch Processing

- Embeddings generated in batches of 100
- Database operations batched for efficiency
- Parallel processing where possible

### 3. Vector Search Optimization

- IVFFlat indexes for fast similarity search
- Connection pooling for database access
- Efficient query patterns

### 4. Memory Management

- Streaming for large responses
- Lazy loading of embeddings
- Garbage collection optimization

## Scalability

### Horizontal Scaling

- Stateless application design
- Database connection pooling
- Container orchestration ready

### Vertical Scaling

- Configurable batch sizes
- Memory-efficient processing
- Optimized algorithms

### Data Volume Handling

- Efficient vector operations
- Incremental processing
- Retroactive updates only when necessary

## Security Considerations

### 1. Data Privacy

- Local processing with Ollama
- No external API calls
- Data stays within your infrastructure

### 2. Database Security

- Connection encryption
- Access control
- Audit logging

### 3. Container Security

- Minimal base images
- Non-root user execution
- Resource limits

## Monitoring and Observability

### 1. Logging

- Structured logging with timestamps
- Component-level logging
- Error tracking and alerting

### 2. Metrics

- Processing time per batch
- Theme creation/update rates
- Cache hit rates
- Database performance

### 3. Health Checks

- Component health monitoring
- Database connectivity
- Ollama service status
- Embedding service health

## Error Handling

### 1. Graceful Degradation

- Continue processing on non-critical errors
- Fallback mechanisms for failed components
- Retry logic for transient failures

### 2. Error Recovery

- Transaction rollback on failures
- State consistency maintenance
- Data integrity preservation

### 3. Monitoring

- Error rate tracking
- Performance degradation detection
- Alerting on critical failures
