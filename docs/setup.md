# Setup Guide

This guide will help you set up the Theme Evolution System on your local machine.

## Prerequisites

### Required Software

1. **Docker** (version 20.10+)
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Verify installation: `docker --version`

2. **Docker Compose** (version 2.0+)
   - Usually included with Docker Desktop
   - Verify installation: `docker-compose --version`

3. **Git**
   - [Install Git](https://git-scm.com/downloads)
   - Verify installation: `git --version`

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB free space
- **CPU**: 4+ cores recommended
- **OS**: Linux, macOS, or Windows with WSL2

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd theme-evolution-system
```

### 2. Start Services

```bash
docker-compose up
```

This will automatically:
- Download and set up PostgreSQL with pgvector extension
- Download Ollama and required models (Llama 3.1, nomic-embed-text)
- Set up database schema
- Launch Streamlit UI at http://localhost:8501
- Create host directories: `data/`, `outputs/`, `logs/`

### 3. Access the Streamlit UI

Open your browser and navigate to:
```
http://localhost:8501
```

The Streamlit UI provides:
- 🎯 Generate random survey questions
- 📝 Generate 100 synthetic responses
- ⚡ Process batches with theme extraction
- 📊 Interactive dashboards and visualizations
- 🔍 Theme analysis and keyword highlighting

### 4. Verify Installation

Check that all services are running:

```bash
docker-compose ps
```

You should see all services with "Up" status.

### 5. Volume Structure

The system creates the following host directories:

```
project-root/
├── data/           # Input data, synthetic responses
├── outputs/        # Processing results, exports
└── logs/           # Application logs
```

**Volume Benefits:**
- **Data Persistence**: All data survives container restarts
- **Easy Access**: Files accessible from host system
- **Backup Friendly**: Simple to backup and restore
- **Development**: Easy to inspect and modify data

## Troubleshooting

### Common Issues

#### 1. Docker Not Running
```
Error: Cannot connect to the Docker daemon
```
**Solution**: Start Docker Desktop or Docker daemon

#### 2. Port Conflicts
```
Error: Port 5432 is already in use
```
**Solution**: Stop existing PostgreSQL service or change port in docker-compose.yml

#### 3. Out of Memory
```
Error: Container killed due to OOM
```
**Solution**: Increase Docker memory limit to 8GB+ in Docker Desktop settings

#### 4. Ollama Model Not Found
```
Error: Model llama3.1 not found
```
**Solution**: The model will be downloaded automatically on first use. Wait for download to complete.

### Service Health Checks

Check individual service health:

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check Ollama
curl http://localhost:11434/api/tags

# Check application logs
docker-compose logs app
```

### Reset Everything

If you need to start fresh:

```bash
# Stop and remove all containers
docker-compose down -v

# Remove all data volumes
docker volume prune

# Restart setup
docker-compose up
```

## Development Setup

For development work:

### 1. Install Python Dependencies Locally

```bash
pip install -r requirements.txt
```

### 2. Set Up Local Database

```bash
# Install PostgreSQL with pgvector
# Ubuntu/Debian:
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-16-pgvector

# macOS:
brew install postgresql
brew install pgvector
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=src tests/
```

### 4. Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Production Deployment

For production deployment:

### 1. Environment Variables

Set production environment variables:

```bash
export DB_PASSWORD=<secure-password>
export OLLAMA_BASE_URL=http://ollama:11434
export LOG_LEVEL=WARNING
```

### 2. Resource Limits

Update docker-compose.yml with production resource limits:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### 3. Data Persistence

Ensure data volumes are properly configured:

```yaml
volumes:
  postgres_data:
    driver: local
  ollama_data:
    driver: local
```

### 4. Monitoring

Add monitoring and logging:

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Next Steps

Once setup is complete:

1. Read the [Usage Guide](usage.md) to learn how to use the system
2. Explore the [Architecture](architecture.md) to understand the system design
3. Check the [API Reference](api_reference.md) for detailed documentation
4. Run the demo to see the system in action
