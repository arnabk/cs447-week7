# Project Proposal

**Project Title:** Theme Evolution System for Survey Response Analysis

**Team Members:** Arnab Karmakar (arnabk3)

**Project Coordinator:** Arnab Karmakar (arnabk3)

## Project Description

This project aims to develop an intelligent theme evolution system that processes survey responses in batches, automatically extracts themes, highlights contributing keywords, and intelligently evolves themes over time using local LLM processing.

### 1. What is the new tool or new function that you'd like to develop?

A scalable theme extraction and evolution system that:
- **Processes survey responses in batches** with automatic theme identification
- **Highlights keywords** that contribute to theme assignment using similarity-based analysis
- **Evolves themes intelligently** over time through merging, splitting, and updating
- **Applies retroactive updates** to historical data when themes change
- **Provides comprehensive analytics** on theme evolution and response patterns

### 2. Why do we need it? What pain point does it address?

**Critical Technical Challenge:**
- **LLM Context Window Limitations**: Even advanced LLMs (Gemini with 1M+ context) cannot handle several million survey responses
- **Large-Scale Batch Processing**: Survey datasets with several million responses exceed even the largest context windows
- **Memory Constraints**: Processing entire datasets at once causes memory overflow and performance degradation
- **Incremental Processing**: Need to process data in manageable chunks while maintaining theme consistency
- **State Management**: Themes must evolve across batches without losing historical context

**Our Solution Addresses:**
- **Intelligent Batching**: Process datasets with several million responses in optimal chunks
- **Incremental Theme Evolution**: Maintain theme consistency across massive datasets
- **Vector-Based Similarity**: Use embeddings for efficient theme matching without full context
- **Retroactive Updates**: Update historical themes when new patterns emerge
- **Scalable Architecture**: Handle datasets of any size through intelligent chunking

### 3. How is this different from existing tools?

**Existing Tools Limitations:**
- **Single-shot LLM analysis** (ChatGPT, Claude, Gemini) cannot handle several million responses even with 1M+ context windows
- **Static analysis tools** (NVivo, Atlas.ti) require manual coding and don't scale to several million responses
- **Basic clustering** (K-means, LDA) don't provide semantic understanding or evolution
- **Survey platforms** (SurveyMonkey, Qualtrics) only provide basic analytics, no theme evolution
- **Cloud APIs** (AWS Comprehend, Google NLP) lack incremental processing and theme evolution

**Our Innovation:**
- **Intelligent batching** that maintains semantic coherence across chunks
- **Vector-based theme evolution** using embeddings for efficient similarity matching
- **Incremental processing** that scales to several million responses
- **Retroactive updates** that maintain historical consistency across batches
- **Scalable architecture** for large-scale theme analysis

### 4. How do you plan to build your tool?

**Core Technical Solution:**
- **Intelligent Batching**: Process responses in optimal chunks that fit LLM context windows
- **Vector-Based Similarity**: Use embeddings to match responses to themes without full context
- **Incremental Processing**: Maintain theme state across batches using database persistence
- **Retroactive Updates**: Update historical themes when new patterns emerge

**Architecture:**
- **Batch Processor**: Orchestrates chunking and processing workflow
- **Theme Extractor**: LLM integration for theme generation within context limits
- **Vector Database**: PostgreSQL + pgvector for efficient similarity search
- **Theme Evolver**: Merge/split/update logic with retroactive processing
- **Embedding Service**: Batch embedding generation and caching

**Key Technical Innovations:**
1. **Context-Aware Chunking**: Optimal batch sizes based on LLM context limits
2. **Vector Similarity Matching**: Efficient theme assignment without full context
3. **Incremental State Management**: Database-driven theme evolution across batches
4. **Retroactive Processing**: Update historical data when themes change
5. **Scalable Embedding Pipeline**: Batch processing for millions of responses

### 5. How do you plan to evaluate your tool?

**Core Technical Metrics:**
- **Context Window Utilization**: Optimal batch sizes that maximize LLM context usage
- **Processing Scalability**: Performance with datasets exceeding LLM context limits
- **Memory Efficiency**: Processing large datasets without memory overflow
- **Theme Consistency**: Coherence across batches and evolution patterns
- **Vector Similarity Accuracy**: Embedding-based theme matching precision

**Large-Scale Processing Tests:**
- **Context Limit Testing**: Datasets with several million responses that exceed even Gemini's 1M+ context windows
- **Batch Processing Performance**: Throughput with 100+ batches, 1000+ responses
- **Memory Usage**: Processing datasets of varying sizes without overflow
- **Theme Evolution**: Consistency across several million responses
- **Retroactive Updates**: Historical theme updates without data loss

**UI-Based Testing:**
- **Interactive Data Generation**: Generate diverse survey questions and responses through Streamlit UI
- **Variable Response Testing**: Create 100+ responses with different patterns and themes
- **Batch Processing Validation**: Test theme extraction and evolution across multiple batches
- **Real-time Performance Monitoring**: Monitor processing time and memory usage through UI
- **Theme Evolution Analysis**: Track how themes change and merge across different question types

### 6. How do you plan to divide the work among team members?

**Solo Project Structure:**
- **Phase 1**: Core system architecture and database design
- **Phase 2**: LLM integration and theme extraction logic
- **Phase 3**: Keyword highlighting and similarity algorithms
- **Phase 4**: Theme evolution and retroactive update logic
- **Phase 5**: Testing, documentation, and deployment setup

**Project Code + Documentation Submission Link**: To be completed later

**Project Presentation Submission Link**: To be completed later

**Project Report**: To be completed later
