# Testing Guide

This guide explains how to test the Theme Evolution System, including unit tests, integration tests, and end-to-end testing.

## Test Structure

```
tests/
├── __init__.py
├── test_models.py              # Pydantic model tests
├── test_embedding_service.py   # Embedding service tests
├── test_integration.py         # End-to-end integration tests
└── test_*.py                   # Additional component tests
```

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements.txt

# Ensure test database is available
docker-compose up -d postgres
```

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::TestSurveyResponse::test_create_survey_response
```

### Test Coverage

```bash
# Run with coverage
pytest --cov=src tests/

# Generate coverage report
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html
```

### Test Configuration

The `pytest.ini` file configures test execution:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    slow: marks tests as slow running
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

#### Model Tests (`test_models.py`)

```python
def test_create_survey_response():
    """Test creating a survey response."""
    response = SurveyResponse(
        batch_id=1,
        question="What are your challenges?",
        response_text="API integration issues"
    )
    
    assert response.batch_id == 1
    assert response.question == "What are your challenges?"
    assert response.response_text == "API integration issues"
```

#### Embedding Service Tests (`test_embedding_service.py`)

```python
def test_get_embedding_success():
    """Test successful embedding generation."""
    # Mock Ollama response
    mock_response = {'embedding': [0.1, 0.2, 0.3]}
    mock_ollama_client.return_value.embeddings.return_value = mock_response
    
    result = embedding_service.get_embedding("test text")
    assert result == [0.1, 0.2, 0.3]
```

### 2. Integration Tests

Test component interactions.

#### End-to-End Tests (`test_integration.py`)

```python
def test_theme_processor_initialization():
    """Test theme processor initialization."""
    processor = ThemeProcessor(mock_config)
    
    # Verify all components were initialized
    assert processor.db_manager is not None
    assert processor.embedding_service is not None
    assert processor.theme_extractor is not None
```

### 3. Performance Tests

Test system performance and scalability.

```python
@pytest.mark.slow
def test_large_batch_processing():
    """Test processing large batches."""
    # Create large batch
    large_batch = create_large_batch(1000)  # 1000 responses
    
    start_time = time.time()
    result = processor.process_batch(large_batch)
    processing_time = time.time() - start_time
    
    assert processing_time < 60  # Should complete within 60 seconds
    assert result.themes_created > 0
```

## Test Data

### Synthetic Test Data

The system includes synthetic data generation for testing:

```python
# Generate test data through Streamlit UI
# Access http://localhost:8501 and use the UI to generate test data

# Load test data
from src.utils import load_batch_data
test_batches = load_batch_data("data/test_batches.json")
```

### Test Fixtures

```python
@pytest.fixture
def sample_batch_data():
    """Sample batch data for testing."""
    return BatchData(
        batch_id=1,
        question="What are your biggest challenges?",
        responses=[
            "API integration issues",
            "Lack of documentation",
            "Version compatibility problems"
        ]
    )

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        },
        'ollama': {
            'base_url': 'http://localhost:11434',
            'generation_model': 'llama3.1',
            'embedding_model': 'nomic-embed-text'
        }
    }
```

## Mocking and Stubbing

### Ollama Mocking

```python
@patch('src.theme_extractor.ollama.Client')
def test_theme_extraction(mock_ollama_client):
    """Test theme extraction with mocked Ollama."""
    # Mock Ollama response
    mock_response = {
        'response': '[{"name": "API Challenges", "description": "API-related issues"}]'
    }
    mock_ollama_client.return_value.generate.return_value = mock_response
    
    # Test theme extraction
    themes = extractor.extract_themes_from_batch(question, responses, batch_id)
    assert len(themes) == 1
    assert themes[0].name == "API Challenges"
```

### Database Mocking

```python
@patch('src.database.psycopg2.connect')
def test_database_operations(mock_connect):
    """Test database operations with mocked connection."""
    # Mock database connection
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn
    
    # Test database operations
    db_manager = DatabaseManager(config)
    assert db_manager.test_connection() is True
```

## Test Environment Setup

### Docker Test Environment

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  postgres-test:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: test_theme_evolution
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    volumes:
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/schema.sql
```

### Test Database Setup

```python
@pytest.fixture(scope="session")
def test_database():
    """Set up test database."""
    # Start test database
    subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"])
    
    # Wait for database to be ready
    time.sleep(5)
    
    yield
    
    # Cleanup
    subprocess.run(["docker-compose", "-f", "docker-compose.test.yml", "down", "-v"])
```

## Test Scenarios

### 1. Basic Functionality Tests

```python
def test_survey_response_creation():
    """Test creating survey responses."""
    response = SurveyResponse(
        batch_id=1,
        question="Test question",
        response_text="Test response"
    )
    assert response.batch_id == 1

def test_theme_creation():
    """Test creating themes."""
    theme = Theme(
        name="Test Theme",
        description="Test description",
        created_at_batch=1
    )
    assert theme.name == "Test Theme"
```

### 2. Integration Tests

```python
def test_theme_extraction_workflow():
    """Test complete theme extraction workflow."""
    # Create test batch
    batch = BatchData(
        batch_id=1,
        question="What are your challenges?",
        responses=["API issues", "Documentation problems"]
    )
    
    # Process batch
    result = processor.process_batch(batch)
    
    # Verify results
    assert result.batch_id == 1
    assert result.themes_created > 0
    assert result.processing_time_seconds > 0
```

### 3. Error Handling Tests

```python
def test_invalid_embedding_handling():
    """Test handling of invalid embeddings."""
    # Test with empty text
    embedding = embedding_service.get_embedding("")
    assert embedding == [0.0] * 768
    
    # Test with None
    embedding = embedding_service.get_embedding(None)
    assert embedding == [0.0] * 768

def test_database_connection_failure():
    """Test handling of database connection failures."""
    with patch('src.database.psycopg2.connect', side_effect=Exception("Connection failed")):
        db_manager = DatabaseManager(config)
        assert db_manager.test_connection() is False
```

### 4. Performance Tests

```python
@pytest.mark.slow
def test_batch_processing_performance():
    """Test batch processing performance."""
    # Create large batch
    large_batch = create_large_batch(100)
    
    start_time = time.time()
    result = processor.process_batch(large_batch)
    processing_time = time.time() - start_time
    
    # Performance assertions
    assert processing_time < 30  # Should complete within 30 seconds
    assert result.processing_time_seconds < 30
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_theme_evolution
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest --cov=src tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Best Practices

### 1. Test Isolation

```python
def test_theme_processing():
    """Test theme processing in isolation."""
    # Use fresh instances for each test
    processor = ThemeProcessor(config)
    batch = create_test_batch()
    
    result = processor.process_batch(batch)
    assert result is not None
```

### 2. Test Data Management

```python
@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test."""
    # Clean up test data
    db_manager.clear_test_data()
    yield
    # Clean up after test
    db_manager.clear_test_data()
```

### 3. Assertion Clarity

```python
def test_theme_creation():
    """Test theme creation with clear assertions."""
    theme = create_test_theme()
    
    # Clear, specific assertions
    assert theme.name == "Test Theme"
    assert theme.description is not None
    assert theme.created_at_batch == 1
    assert theme.status == "active"
```

### 4. Error Testing

```python
def test_invalid_input_handling():
    """Test handling of invalid inputs."""
    with pytest.raises(ValueError, match="Invalid confidence score"):
        ThemeAssignment(
            response_id=1,
            theme_id=1,
            confidence_score=1.5,  # Invalid score > 1
            highlighted_keywords=[],
            assigned_at_batch=1
        )
```

## Debugging Tests

### Verbose Output

```bash
# Run with verbose output
pytest -v -s

# Run specific test with debug output
pytest -v -s tests/test_models.py::TestSurveyResponse::test_create_survey_response
```

### Test Debugging

```python
def test_debug_example():
    """Example of debugging test failures."""
    result = processor.process_batch(batch)
    
    # Debug output
    print(f"Result: {result}")
    print(f"Themes created: {result.themes_created}")
    
    # Assert with helpful message
    assert result.themes_created > 0, f"No themes created. Result: {result}"
```

### Test Logging

```python
import logging

def test_with_logging():
    """Test with logging enabled."""
    logging.basicConfig(level=logging.DEBUG)
    
    result = processor.process_batch(batch)
    assert result is not None
```

## Coverage Goals

### Target Coverage

- **Unit Tests**: 90%+ coverage for core modules
- **Integration Tests**: 80%+ coverage for workflows
- **Error Handling**: 100% coverage for error paths

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term tests/

# View HTML report
open htmlcov/index.html
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */venv/*
    */env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```
