# API Reference

This document provides detailed API documentation for all modules in the Theme Evolution System.

## Core Modules

### ThemeProcessor

Main orchestrator that coordinates all components.

```python
from src.theme_processor import ThemeProcessor

processor = ThemeProcessor(config)
```

#### Methods

**`process_batch(batch_data: BatchData) -> ProcessingResult`**

Processes a single batch of survey responses.

```python
result = processor.process_batch(batch_data)
print(f"Created {result.themes_created} themes")
print(f"Processing time: {result.processing_time_seconds:.2f}s")
```

**`process_multiple_batches(batches: List[BatchData]) -> List[ProcessingResult]`**

Processes multiple batches sequentially.

```python
results = processor.process_multiple_batches(batches)
```

**`test_system_health() -> Dict[str, bool]`**

Tests all system components.

```python
health = processor.test_system_health()
# Returns: {'database': True, 'ollama': True, 'embeddings': True}
```

**`get_processing_stats() -> Dict[str, Any]`**

Gets processing statistics.

```python
stats = processor.get_processing_stats()
print(f"Total batches: {stats['total_batches_processed']}")
print(f"Active themes: {stats['active_themes']}")
```

### EmbeddingService

Manages embeddings and similarity calculations.

```python
from src.embedding_service import EmbeddingService

embedding_service = EmbeddingService(config, db_manager)
```

#### Methods

**`get_embedding(text: str, use_cache: bool = True) -> List[float]`**

Gets embedding for text, using cache if available.

```python
embedding = embedding_service.get_embedding("Sample text")
# Returns: [0.1, 0.2, 0.3, ...] (768 dimensions)
```

**`get_embeddings_batch(texts: List[str], use_cache: bool = True) -> List[List[float]]`**

Gets embeddings for multiple texts in batch.

```python
embeddings = embedding_service.get_embeddings_batch(["text1", "text2", "text3"])
# Returns: [[0.1, 0.2, ...], [0.3, 0.4, ...], [0.5, 0.6, ...]]
```

**`cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float`**

Calculates cosine similarity between two embeddings.

```python
similarity = embedding_service.cosine_similarity(emb1, emb2)
# Returns: 0.85 (similarity score 0-1)
```

**`get_cache_stats() -> Dict[str, int]`**

Gets cache statistics.

```python
stats = embedding_service.get_cache_stats()
# Returns: {'total_cached': 1000, 'models_count': 1}
```

**`clear_cache() -> None`**

Clears all cached embeddings.

```python
embedding_service.clear_cache()
```

### ThemeExtractor

Extracts themes from survey responses using Ollama/Llama.

```python
from src.theme_extractor import ThemeExtractor

extractor = ThemeExtractor(config, embedding_service)
```

#### Methods

**`extract_themes_from_batch(question: str, responses: List[str], batch_id: int) -> List[Theme]`**

Extracts themes from a batch of responses.

```python
themes = extractor.extract_themes_from_batch(
    question="What are your challenges?",
    responses=["Response 1", "Response 2"],
    batch_id=1
)
# Returns: [Theme(name="Challenges", description="..."), ...]
```

**`update_theme_description(theme: Theme, new_responses: List[str]) -> str`**

Updates a theme's description based on new responses.

```python
updated_description = extractor.update_theme_description(theme, new_responses)
```

**`test_connection() -> bool`**

Tests connection to Ollama.

```python
is_connected = extractor.test_connection()
```

### KeywordHighlighter

Highlights keywords that contribute to theme assignment.

```python
from src.keyword_highlighter import KeywordHighlighter

highlighter = KeywordHighlighter(config, embedding_service)
```

#### Methods

**`highlight_keywords(response_text: str, theme_embedding: List[float]) -> List[HighlightedKeyword]`**

Highlights keywords that contribute to theme assignment.

```python
keywords = highlighter.highlight_keywords(
    response_text="API integration challenges",
    theme_embedding=[0.1, 0.2, 0.3, ...]
)
# Returns: [HighlightedKeyword(keyword="API", score=0.12), ...]
```

**`extract_phrases(text: str) -> List[str]`**

Extracts n-grams (unigrams, bigrams, trigrams) from text.

```python
phrases = highlighter.extract_phrases("API integration challenges")
# Returns: ["API", "integration", "challenges", "API integration", ...]
```

**`batch_highlight_keywords(responses: List[str], theme_embeddings: List[List[float]]) -> List[List[HighlightedKeyword]]`**

Highlights keywords for multiple responses and themes.

```python
all_keywords = highlighter.batch_highlight_keywords(responses, theme_embeddings)
```

**`get_phrase_statistics(text: str) -> Dict[str, Any]`**

Gets statistics about phrases in text.

```python
stats = highlighter.get_phrase_statistics("Sample text")
# Returns: {'total_phrases': 10, 'unigrams': 5, 'bigrams': 3, ...}
```

### ThemeEvolver

Handles theme evolution including merging, splitting, and updating.

```python
from src.theme_evolver import ThemeEvolver

evolver = ThemeEvolver(config, embedding_service, db_manager)
```

#### Methods

**`match_to_existing_themes(responses: List[SurveyResponse], existing_themes: List[Theme]) -> Dict[str, List[SurveyResponse]]`**

Matches responses to existing themes based on similarity.

```python
matches = evolver.match_to_existing_themes(responses, themes)
# Returns: {'1': [response1, response2], '2': [response3]}
```

**`detect_theme_merges(themes: List[Theme]) -> List[Tuple[Theme, Theme, float]]`**

Detects themes that should be merged based on similarity.

```python
merge_candidates = evolver.detect_theme_merges(themes)
# Returns: [(theme1, theme2, 0.87), (theme3, theme4, 0.91)]
```

**`merge_themes(theme1: Theme, theme2: Theme, batch_id: int) -> Theme`**

Merges two themes into one.

```python
merged_theme = evolver.merge_themes(theme1, theme2, batch_id)
```

**`detect_theme_splits(theme: Theme, assignments: List[ThemeAssignment]) -> Optional[List[Theme]]`**

Detects if a theme should be split based on response clustering.

```python
split_themes = evolver.detect_theme_splits(theme, assignments)
# Returns: [new_theme1, new_theme2] or None
```

**`update_theme_description(theme: Theme, new_responses: List[SurveyResponse], theme_extractor) -> Optional[Theme]`**

Updates a theme's description based on new responses.

```python
updated_theme = evolver.update_theme_description(theme, new_responses, extractor)
```

### DatabaseManager

Handles all database operations.

```python
from src.database import DatabaseManager

db_manager = DatabaseManager(config)
```

#### Methods

**`test_connection() -> bool`**

Tests database connection.

```python
is_connected = db_manager.test_connection()
```

**Survey Response Operations:**

```python
# Save response
response_id = db_manager.save_response(response)

# Get responses by batch
responses = db_manager.get_responses_by_batch(batch_id)

# Get response by ID
response = db_manager.get_response_by_id(response_id)
```

**Theme Operations:**

```python
# Save theme
theme_id = db_manager.save_theme(theme)

# Get all themes
themes = db_manager.get_all_themes(status="active")

# Get theme by ID
theme = db_manager.get_theme_by_id(theme_id)

# Update theme
db_manager.update_theme(theme)

# Delete theme (soft delete)
db_manager.delete_theme(theme_id)
```

**Vector Similarity Search:**

```python
# Find similar themes
similar_themes = db_manager.find_similar_themes(
    embedding=[0.1, 0.2, 0.3],
    threshold=0.7,
    limit=5
)

# Find similar responses
similar_responses = db_manager.find_similar_responses(
    embedding=[0.1, 0.2, 0.3],
    threshold=0.7,
    limit=5
)
```

**Theme Assignment Operations:**

```python
# Save assignment
assignment_id = db_manager.save_theme_assignment(assignment)

# Get assignments by theme
assignments = db_manager.get_assignments_by_theme(theme_id)

# Get assignments by response
assignments = db_manager.get_assignments_by_response(response_id)
```

**Theme Evolution Operations:**

```python
# Save evolution record
evolution_id = db_manager.save_theme_evolution(evolution)

# Get evolution by batch
evolutions = db_manager.get_evolution_by_batch(batch_id)
```

**Batch Metadata Operations:**

```python
# Save batch metadata
db_manager.save_batch_metadata(metadata)

# Get batch metadata
metadata = db_manager.get_batch_metadata(batch_id)
```

**Utility Methods:**

```python
# Get database statistics
stats = db_manager.get_database_stats()
# Returns: {'active_themes': 50, 'total_responses': 1000, ...}
```

## Data Models

### SurveyResponse

```python
from src.models import SurveyResponse

response = SurveyResponse(
    batch_id=1,
    question="What are your challenges?",
    response_text="API integration issues",
    embedding=[0.1, 0.2, 0.3, ...]  # Optional
)
```

### Theme

```python
from src.models import Theme

theme = Theme(
    name="API Integration Challenges",
    description="Challenges related to API integration",
    embedding=[0.1, 0.2, 0.3, ...],  # Optional
    created_at_batch=1
)
```

### ThemeAssignment

```python
from src.models import ThemeAssignment, HighlightedKeyword

keywords = [
    HighlightedKeyword(keyword="API", score=0.12, positions=[10, 25]),
    HighlightedKeyword(keyword="integration", score=0.08, positions=[15])
]

assignment = ThemeAssignment(
    response_id=1,
    theme_id=2,
    confidence_score=0.85,
    highlighted_keywords=keywords,
    assigned_at_batch=1
)
```

### BatchData

```python
from src.models import BatchData

batch = BatchData(
    batch_id=1,
    question="What are your challenges?",
    responses=["Response 1", "Response 2", "Response 3"]
)
```

### ProcessingResult

```python
from src.models import ProcessingResult

result = ProcessingResult(
    batch_id=1,
    question="What are your challenges?",
    processing_time_seconds=2.5,
    total_responses=8,
    themes_created=2,
    themes_updated=1,
    themes_deleted=0
)
```

## Utility Functions

### Configuration Loading

```python
from src.utils import load_config

config = load_config("config.yaml")
```

### Logging Setup

```python
from src.utils import setup_logging

setup_logging("INFO")  # DEBUG, INFO, WARNING, ERROR
```

### Data Loading

```python
from src.utils import load_batch_data, save_processing_results

# Load batch data
batches = load_batch_data("data/batches.json")

# Save results
save_processing_results(results, "outputs/results.json")
```

### Output Directory Creation

```python
from src.utils import create_output_directory

create_output_directory("outputs")
```

### Processing Summary

```python
from src.utils import format_processing_summary

summary = format_processing_summary(results)
print(summary)
```

## Error Handling

### Common Exceptions

```python
try:
    result = processor.process_batch(batch)
except Exception as e:
    print(f"Processing failed: {e}")
    # Handle error appropriately
```

### Health Checks

```python
# Check system health before processing
health = processor.test_system_health()
if not all(health.values()):
    print("System not healthy, check components")
    return
```

## Configuration

### Configuration File (config.yaml)

```yaml
database:
  host: postgres
  port: 5432
  database: theme_evolution
  user: postgres
  password: postgres

ollama:
  base_url: http://ollama:11434
  generation_model: llama3.1
  embedding_model: nomic-embed-text
  generation_timeout: 120
  embedding_timeout: 30

thresholds:
  similarity_existing_theme: 0.75
  similarity_update_candidate: 0.50
  similarity_merge_themes: 0.85
  theme_split_variance: 0.40
  embedding_shift_recompute: 0.15
  keyword_contribution: 0.05
  min_responses_per_theme: 2

processing:
  batch_size: 100
  max_keywords_per_response: 10
  theme_update_drift_threshold: 0.20

ngrams:
  use_unigrams: true
  use_bigrams: true
  use_trigrams: true
  min_word_length: 3
  max_stopwords_in_phrase: 1
```

## Examples

### Complete Processing Example

```python
from src.theme_processor import ThemeProcessor
from src.utils import load_config, load_batch_data

# Load configuration
config = load_config()

# Initialize processor
processor = ThemeProcessor(config)

# Load data
batches = load_batch_data("data/batches.json")

# Process batches
results = []
for batch in batches:
    try:
        result = processor.process_batch(batch)
        results.append(result)
        print(f"Batch {batch.batch_id}: {result.themes_created} themes created")
    except Exception as e:
        print(f"Failed to process batch {batch.batch_id}: {e}")

# Save results
from src.utils import save_processing_results
save_processing_results(results, "outputs/results.json")
```

### Custom Theme Processing

```python
# Custom theme extractor
class CustomThemeExtractor(ThemeExtractor):
    def extract_themes_from_batch(self, question, responses, batch_id):
        themes = super().extract_themes_from_batch(question, responses, batch_id)
        # Custom post-processing
        for theme in themes:
            if "challenge" in theme.name.lower():
                theme.name = f"Challenge: {theme.name}"
        return themes

# Use custom extractor
processor.theme_extractor = CustomThemeExtractor(config, processor.embedding_service)
```
