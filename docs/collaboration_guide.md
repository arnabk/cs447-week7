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

### 2. Collaboration Time (9 PM - 12 AM MST)
```bash
# Review pull requests
# Test integrated changes
# Plan next day's work
# Update project documentation
```

### 3. Weekly Integration
```bash
# Merge feature branches to develop
# Test full system integration
# Deploy to staging environment
# Update project status
```

## 📊 Progress Tracking

### Task Status
- [ ] **Not Started**: Task not yet begun
- [🔄] **In Progress**: Currently working on
- [✅] **Completed**: Finished and tested
- [❌] **Blocked**: Cannot proceed due to dependencies

### Weekly Milestones
- **Week 1**: Project setup and data collection
- **Week 2**: Basic clustering implementation
- **Week 3**: Advanced clustering and evaluation
- **Week 4**: Summarization system
- **Week 5**: API development
- **Week 6**: System integration
- **Week 7**: Final deployment and documentation

## 📋 Task Division Strategy

### Yihui Yu (yihuiy2) - Backend/ML Specialist
**Primary Focus Areas:**
- **Clustering Algorithms**: HDBSCAN, Deep Learning approaches
- **Summarization**: Transformer-based methods (BART, T5)
- **API Development**: FastAPI, REST endpoints
- **Deployment**: Docker, containerization

**Key Responsibilities:**
- Advanced ML model implementation
- API architecture and development
- System performance optimization
- Production deployment

### Arnab Karmakar (arnabk3) - Data/ML Specialist
**Primary Focus Areas:**
- **Data Pipeline**: Collection, preprocessing, storage
- **Traditional ML**: DBSCAN, K-means, baseline methods
- **Graph Methods**: TextRank, graph-based summarization
- **Documentation**: Reports, user guides, API docs

**Key Responsibilities:**
- Data collection and preprocessing
- Baseline algorithm implementation
- System monitoring and logging
- Comprehensive documentation

## 🤝 Collaboration Protocol

### Daily Standup (9:00 PM MST)
**Questions to Answer:**
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers or issues?
4. Next steps for collaboration

### Weekly Review (Friday 11:00 PM MST)
**Agenda:**
- Review completed tasks
- Plan next week's priorities
- Address technical challenges
- Update project timeline

### Code Review Process
- All code must be reviewed before merging
- Use pull requests for all changes
- Test all functionality before integration
- Document all new features
