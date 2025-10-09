# Collaboration Guide for Yihui Yu & Arnab Karmakar

## 👥 Team Information
- **Yihui Yu** (netid: yihuiy2, github: Yhuir)
- **Arnab Karmakar** (netid: arnabk3, github: arnabk)

## 🕘 Collaboration Schedule
- **Time**: 9:00 PM - 12:00 AM MST (3 hours daily)
- **Days**: Monday, Wednesday, Friday
- **Total**: 9 hours/week × 7 weeks = 63 hours

## 📁 GitHub Repository Setup

### Repository Structure
```
news-clustering-project/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── src/
│   ├── data_collection/
│   ├── clustering/
│   ├── summarization/
│   ├── evaluation/
│   └── api/
├── docs/
```

### Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch
- **feature/**: Feature branches (e.g., feature/hdbscan-clustering)
- **bugfix/**: Bug fix branches

### Commit Convention
```
type(scope): description

Examples:
feat(clustering): implement HDBSCAN clustering algorithm
fix(api): resolve CORS issue in FastAPI endpoints
docs(readme): update installation instructions
test(clustering): add unit tests for HDBSCAN clusterer
```

## 🔄 Workflow Process

### 1. Daily Development Cycle
```bash
# Morning setup (before 9 PM)
git checkout develop
git pull origin develop

# Work on assigned tasks
git checkout -b feature/your-feature-name
# ... make changes ...
git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature-name

# Create pull request
# Review and merge during collaboration time
```
