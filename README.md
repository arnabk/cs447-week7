# News Article Clustering and Summarization

Intelligent system for clustering news articles and generating summaries with incremental updates.

## Team
- **Yihui Yu** (yihuiy2, github: Yhuir)
- **Arnab Karmakar** (arnabk3, github: arnabk)

## Quick Start
```bash
# Clone and run
git clone <repository>
cd news-clustering-project
docker-compose up

# Access API
curl http://localhost:8000/health
```

## Documentation
- [project proposal](docs/project_proposal.md) - One-page project proposal
- [algorithm comparison](docs/algorithm_comparison.md) - Comprehensive algorithm analysis
- [task breakdown](docs/task_breakdown.md) - Week-by-week tasks
- [project summary](docs/project_summary.md) - Technical overview
- [collaboration guide](docs/collaboration_guide.md) - Team protocols
- [quick start](docs/quick_start.md) - Setup guide

## Features
- **Multi-Algorithm Comparison**: HDBSCAN, DBSCAN, Spectral, Deep Learning, Mean Shift
- **Advanced Summarization**: BART, T5, TextRank, LexRank
- **Performance Benchmarking**: Comprehensive evaluation across all algorithms
- **Incremental Updates**: Handle new articles without full re-clustering
- **REST API**: FastAPI with algorithm selection
- **Docker Deployment**: Complete containerization
