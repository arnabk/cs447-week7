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
# Start database
docker-compose up -d db

# Run Jupyter notebooks (requires Python 3.9+)
pip install -r requirements.txt
jupyter lab

# Access Jupyter interface
open http://localhost:8888
```

## 📊 Test the System

### 1. Collect News Articles
```python
from src.data_collection.news_collector import NewsCollector

# Initialize collector with free sources
collector = NewsCollector({
    'rss_feeds': [
        'https://www.bbc.com/news/rss.xml',
        'http://feeds.reuters.com/reuters/technologyNews',
        'http://rss.cnn.com/rss/edition_technology.rss'
    ]
})

# Collect articles from RSS feeds
articles = collector.collect_from_rss_feeds()
print(f"Collected {len(articles)} articles")

# Or load from free datasets
articles = collector.load_from_dataset('uci_news_aggregator')
print(f"Loaded {len(articles)} articles from dataset")
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

## 🔧 Algorithm Testing

### Test Clustering Algorithms
```python
# Test different clustering algorithms
from src.clustering.hdbscan_clusterer import HDBSCANClusterer
from src.clustering.dbscan_clusterer import DBSCANClusterer

# Compare clustering results
hdbscan_results = HDBSCANClusterer().fit(embeddings)
dbscan_results = DBSCANClusterer().fit(embeddings)

print(f"HDBSCAN found {len(hdbscan_results.clusters)} clusters")
print(f"DBSCAN found {len(dbscan_results.clusters)} clusters")
```

### Test Summarization Algorithms
```python
# Test different summarization methods
from src.summarization.transformer_summarizer import TransformerSummarizer
from src.summarization.textrank_summarizer import TextRankSummarizer

# Compare summarization results
transformer_summary = TransformerSummarizer().summarize(articles)
textrank_summary = TextRankSummarizer().summarize(articles)

print(f"Transformer summary: {transformer_summary}")
print(f"TextRank summary: {textrank_summary}")
```

## 📈 Monitor Performance

### Check System Status
```bash
# Docker services
docker-compose ps

# Database connection
docker-compose exec db psql -U postgres -d news_clustering -c "SELECT COUNT(*) FROM articles;"

# Jupyter notebook status
jupyter notebook list
```

### Performance Metrics
- **Clustering Accuracy**: > 80%
- **Summarization Quality**: ROUGE > 0.7
- **Processing Time**: < 5 seconds per batch
- **Memory Usage**: < 2GB

## 🐛 Troubleshooting

### Common Issues

#### 1. RSS Feed Issues
```bash
# Check RSS feed availability
curl -I https://www.bbc.com/news/rss.xml

# Test RSS feed parsing
python -c "import feedparser; print(feedparser.parse('https://www.bbc.com/news/rss.xml').status)"
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
- **Evaluation**: `src/evaluation/`
- **Notebooks**: `notebooks/`

### 2. Customize Configuration
- Modify `src/clustering/hdbscan_clusterer.py` for clustering parameters
- Update `src/summarization/transformer_summarizer.py` for summarization settings
- Edit `notebooks/` for analysis and experimentation

### 3. Add Your Own Features
- Implement new clustering algorithms
- Add custom summarization methods
- Create new evaluation metrics
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
- **Week 4**: Algorithm comparison framework
- **Week 5**: System integration
- **Week 6**: Performance optimization
- **Week 7**: Final deployment and documentation

## 📞 Support

### Documentation
- **README.md**: Project overview
- **TASK_BREAKDOWN.md**: Detailed task division
- **COLLABORATION_GUIDE.md**: Team collaboration guide
- **Jupyter Notebooks**: Interactive analysis and experimentation

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
