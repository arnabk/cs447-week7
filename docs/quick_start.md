# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/arnabk/news-clustering-project.git
cd news-clustering-project

# Copy environment file
cp env.example .env
# Edit .env with your API keys
```

### 2. Run with Docker
```bash
# Start all services
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. Run Locally (Development)
```bash
# Start database and Redis
docker-compose up -d db redis

# Run the application (requires Python 3.9+)
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Access API documentation
open http://localhost:8000/docs
```

## 📊 Test the System

### 1. Collect News Articles
```python
from src.data_collection.news_collector import NewsCollector

# Initialize collector
collector = NewsCollector({
    'newsapi': 'your_api_key_here'
})

# Collect articles
articles = collector.collect_from_newsapi(query='technology', page_size=50)
print(f"Collected {len(articles)} articles")
```

### 2. Cluster Articles
```python
from src.clustering.hdbscan_clusterer import HDBSCANClusterer
from sentence_transformers import SentenceTransformer

# Generate embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([article.content for article in articles])

# Cluster articles
clusterer = HDBSCANClusterer(min_cluster_size=3)
clusterer.fit(embeddings)

# Get cluster results
clusters = clusterer.get_cluster_info()
print(f"Found {len(clusters)} clusters")
```

### 3. Summarize Clusters
```python
from src.summarization.transformer_summarizer import TransformerSummarizer

# Initialize summarizer
summarizer = TransformerSummarizer()

# Summarize a cluster
cluster_articles = [articles[i] for i in range(5)]  # Example cluster
summary = summarizer.summarize_cluster(cluster_articles)
print(f"Summary: {summary['summary']}")
```

## 🔧 API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Cluster Articles
```bash
curl -X POST "http://localhost:8000/cluster" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "id": "1",
        "title": "AI News",
        "content": "Artificial intelligence is advancing...",
        "source": "TechNews",
        "published_at": "2024-01-01T00:00:00Z",
        "url": "https://example.com/ai-news"
      }
    ],
    "algorithm": "hdbscan"
  }'
```

### Summarize Articles
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [
      {
        "id": "1",
        "title": "AI News",
        "content": "Artificial intelligence is advancing...",
        "source": "TechNews",
        "published_at": "2024-01-01T00:00:00Z",
        "url": "https://example.com/ai-news"
      }
    ],
    "method": "transformer"
  }'
```

## 📈 Monitor Performance

### Check System Status
```bash
# Docker services
docker-compose ps

# Application logs
docker-compose logs -f app

# Database connection
docker-compose exec db psql -U postgres -d news_clustering -c "SELECT COUNT(*) FROM articles;"
```

### Performance Metrics
- **Clustering Accuracy**: > 80%
- **Summarization Quality**: ROUGE > 0.7
- **Response Time**: < 5 seconds
- **Memory Usage**: < 2GB

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Issues
```bash
# Check environment variables
cat .env

# Verify API keys are set
echo $NEWS_API_KEY
```

#### 2. Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 3. Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready

# Reset database
docker-compose down -v
docker-compose up -d
```

#### 4. Memory Issues
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop -> Settings -> Resources -> Memory
```

## 📚 Next Steps

### 1. Explore the Codebase
- **Data Collection**: `src/data_collection/`
- **Clustering**: `src/clustering/`
- **Summarization**: `src/summarization/`
- **API**: `src/api/`

### 2. Customize Configuration
- Edit `src/api/main.py` for API settings
- Modify `src/clustering/hdbscan_clusterer.py` for clustering parameters
- Update `src/summarization/transformer_summarizer.py` for summarization settings

### 3. Add Your Own Features
- Implement new clustering algorithms
- Add custom summarization methods
- Create new API endpoints
- Integrate additional data sources

## 🎯 Development Workflow

### Daily Development
1. **Morning**: Pull latest changes, start assigned tasks
2. **Collaboration Time (9 PM MST)**: Review code, integrate changes, plan next day
3. **Evening**: Commit changes, create pull requests

### Weekly Milestones
- **Week 1**: Basic system setup and data collection
- **Week 2**: Clustering implementation
- **Week 3**: Summarization system
- **Week 4**: API development
- **Week 5**: System integration
- **Week 6**: Performance optimization
- **Week 7**: Final deployment and documentation

## 📞 Support

### Documentation
- **README.md**: Project overview
- **TASK_BREAKDOWN.md**: Detailed task division
- **COLLABORATION_GUIDE.md**: Team collaboration guide
- **API Documentation**: http://localhost:8000/docs

### Team Communication
- **GitHub Issues**: Technical discussions
- **Pull Requests**: Code review
- **Collaboration Time**: 9 PM - 12 AM MST (Mon, Wed, Fri)

### Getting Help
1. Check existing documentation
2. Search GitHub issues
3. Ask during collaboration time
4. Create new issue if needed

Happy coding! 🚀
