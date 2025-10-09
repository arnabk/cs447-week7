# Project Proposal

## Project Title
News Article Clustering and Summarization with Incremental Updates

## Team Members
- **Yihui Yu** (netID: yihuiy2)
- **Arnab Karmakar** (netID: arnabk3)

## Project Keywords
#clustering #summarization #incremental-learning #news-analysis #nlp

## Project Description

This project addresses the challenge of processing and organizing large volumes of news articles by developing an intelligent system that can automatically cluster related articles and generate meaningful summaries. The system will handle the dynamic nature of news streams by supporting incremental updates, allowing new articles to be integrated into existing clusters without requiring complete re-processing.

Our approach implements and compares multiple clustering algorithms (HDBSCAN, DBSCAN, K-means, and Deep Learning methods) to identify semantically similar articles, followed by various summarization techniques using Transformer-based models (BART, T5) and graph-based methods (TextRank). We will conduct comprehensive performance comparisons across all algorithm combinations to determine the most effective approach for different scenarios. The system will be implemented as a scalable REST API using FastAPI, with Docker containerization for easy deployment.

We will evaluate the effectiveness of our approach using comprehensive metrics: clustering quality (Silhouette Score, Adjusted Rand Index, Davies-Bouldin Index), summarization quality (ROUGE scores, BLEU scores, semantic similarity), and system performance (response time, memory usage, scalability). The system will be tested with real-world news data from multiple sources (NewsAPI, Guardian, Reuters) and demonstrated through a comparative analysis interface showing algorithm performance across different scenarios.

The project aims to provide detailed performance comparisons across all implemented algorithms, identifying the best approach for different use cases (real-time vs. batch processing, different article volumes, varying topic domains). Success will be demonstrated through comprehensive benchmarking, algorithm comparison reports, and a working prototype that showcases the strengths and weaknesses of each approach.
