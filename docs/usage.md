# Usage Guide

This guide explains how to use the Theme Evolution System through the modern Streamlit web interface.

## Quick Start

1. **Start the system**
2. **Access the Streamlit UI**
3. **Generate and process data**
4. **View interactive results**

```bash
docker-compose up
# Open http://localhost:8501 in your browser
```

## Streamlit UI Overview

The Streamlit interface provides a modern, interactive way to use the Theme Evolution System:

### 🎛️ Control Panel (Sidebar)
- **🎯 Generate Random Question**: Creates a random survey question
- **📝 Generate 100 Responses**: Creates synthetic responses for the current question
- **⚡ Process New Batch**: Processes the latest batch with theme extraction
- **🗑️ Clear All Data**: Resets all data and starts fresh

### 📊 Main Dashboard
- **Real-time metrics**: Total responses, themes found, batches processed
- **Interactive tabs**: Dashboard, Themes, Responses, Analysis
- **Visual analytics**: Charts, graphs, and data tables

## Step-by-Step Usage

### 1. Generate a Survey Question

Click the **🎯 Generate Random Question** button in the sidebar to create a random survey question. Examples:
- "What are your biggest challenges with remote work?"
- "How do you stay motivated during difficult projects?"
- "What tools do you find most helpful for productivity?"

### 2. Generate Synthetic Responses

Click the **📝 Generate 100 Responses** button to create 100 synthetic responses for the current question. The system will:
- Generate diverse, realistic responses
- Simulate different perspectives and experiences
- Create responses of varying lengths and complexity

### 3. Process the Batch

Click the **⚡ Process New Batch** button to:
- Extract themes from the responses
- Highlight contributing keywords
- Assign responses to themes
- Update existing themes if applicable

### 4. Explore Results

Navigate through the different tabs to explore your results:

#### 📊 Dashboard Tab
- **Theme Distribution**: Pie chart showing response distribution by theme
- **Theme Confidence**: Bar chart showing confidence scores
- **Recent Themes**: List of the latest themes with details

#### 🎯 Themes Tab
- **Theme Selection**: Dropdown to select specific themes
- **Theme Details**: Name, description, confidence, keywords
- **Assigned Responses**: Responses assigned to the selected theme
- **Keyword Analysis**: Highlighted keywords with importance scores

#### 📝 Responses Tab
- **Response Statistics**: Average length, total count, assignment rate
- **Length Distribution**: Histogram of response lengths
- **Recent Responses**: List of the latest responses with details

#### 🔍 Analysis Tab
- **Theme Evolution**: Line chart showing theme confidence over time
- **Keyword Analysis**: Bar chart of top keywords across all themes
- **Similarity Analysis**: Histogram of similarity scores

## Advanced Features

### Batch Processing Workflow

1. **Generate Question**: Start with a new survey question
2. **Generate Responses**: Create 100 synthetic responses
3. **Process Batch**: Extract themes and keywords
4. **Repeat**: Generate more responses for the same question
5. **Theme Evolution**: Watch themes evolve as new data arrives

### Real-time Monitoring

The dashboard provides real-time updates:
- **Processing Status**: Live updates during batch processing
- **Progress Indicators**: Visual feedback for long operations
- **Error Handling**: Clear error messages and recovery options

### Data Management

- **Session State**: All data persists during your session
- **Clear Data**: Reset everything to start fresh
- **Export Options**: Download results as JSON or CSV

## UI Features

### Modern Design
- **Gradient Headers**: Beautiful gradient text effects
- **Card Layouts**: Clean, organized information display
- **Interactive Charts**: Plotly-powered visualizations
- **Responsive Design**: Works on desktop and mobile

### User Experience
- **One-Click Operations**: Simple button-based workflow
- **Visual Feedback**: Progress bars, success messages, warnings
- **Intuitive Navigation**: Clear tab structure and organization
- **No Logs Needed**: All information displayed in the UI

### Performance
- **Real-time Updates**: Live data refresh
- **Efficient Processing**: Optimized batch operations
- **Memory Management**: Smart data handling
- **Error Recovery**: Graceful error handling

## Troubleshooting

### Common Issues

#### UI Not Loading
- Check that Docker Compose is running: `docker-compose ps`
- Verify Streamlit service is up: `docker-compose logs streamlit`
- Try refreshing the browser

#### Processing Errors
- Check Ollama service: `docker-compose logs ollama`
- Verify database connection: `docker-compose logs postgres`
- Clear data and try again

#### Performance Issues
- Reduce batch size in configuration
- Check system resources
- Restart services: `docker-compose restart`

### Debug Mode

Enable debug logging by setting environment variables:
```bash
export LOG_LEVEL=DEBUG
docker-compose up
```

### Reset Everything

If you encounter persistent issues:
```bash
docker-compose down -v
docker-compose up
```

## Best Practices

### 1. Workflow Optimization
- Generate questions that are specific and focused
- Process batches regularly to see theme evolution
- Use the analysis tab to understand patterns

### 2. Data Management
- Clear data between different experiments
- Monitor processing metrics for performance
- Export results for external analysis

### 3. Theme Analysis
- Focus on high-confidence themes
- Review keyword highlights for insights
- Track theme evolution over multiple batches

## Integration

### API Access
The system also provides programmatic access:
```python
from src.theme_processor import ThemeProcessor
processor = ThemeProcessor()
result = processor.process_batch(batch_data)
```

### Database Queries
Direct database access for advanced analysis:
```python
from src.database import DatabaseManager
db = DatabaseManager()
themes = db.get_all_themes()
```

### Data Generation Options
- **Streamlit UI**: Interactive, on-demand generation
- **Programmatic**: Custom data generation via Python API

### Testing and Benchmarking
All testing is done through the Streamlit UI:
- Generate multiple questions and responses
- Process batches to test theme evolution
- Use the analysis tab to monitor performance
- Test with different question types and response patterns

## Next Steps

1. **Experiment**: Try different questions and response patterns
2. **Analyze**: Use the analysis tab to understand theme evolution
3. **Scale**: Process larger datasets to see system performance
4. **Customize**: Modify configuration for your specific needs

The Streamlit UI makes the Theme Evolution System accessible to users of all technical levels while providing powerful analysis capabilities for advanced users.