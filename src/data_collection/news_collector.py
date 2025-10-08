"""
News article data collection from various sources
"""

import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Article data structure"""
    id: str
    title: str
    content: str
    source: str
    published_at: str
    url: str
    author: Optional[str] = None
    category: Optional[str] = None

class NewsCollector:
    """
    Collect news articles from various sources
    """
    
    def __init__(self, api_keys: Dict[str, str] = None):
        """
        Initialize news collector
        
        Args:
            api_keys: Dictionary of API keys for different sources
        """
        self.api_keys = api_keys or {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'News Clustering Bot 1.0'
        })
        
    def collect_from_newsapi(self, 
                           query: str = None,
                           sources: List[str] = None,
                           language: str = 'en',
                           sort_by: str = 'publishedAt',
                           page_size: int = 100) -> List[Article]:
        """
        Collect articles from NewsAPI
        
        Args:
            query: Search query
            sources: List of source IDs
            language: Language code
            sort_by: Sort order
            page_size: Number of articles per page
            
        Returns:
            List of Article objects
        """
        if 'newsapi' not in self.api_keys:
            logger.warning("NewsAPI key not provided")
            return []
        
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': self.api_keys['newsapi'],
                'language': language,
                'sortBy': sort_by,
                'pageSize': min(page_size, 100)  # NewsAPI limit
            }
            
            if query:
                params['q'] = query
            if sources:
                params['sources'] = ','.join(sources)
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('articles', []):
                article = Article(
                    id=f"newsapi_{hash(item['url'])}",
                    title=item.get('title', ''),
                    content=item.get('content', '') or item.get('description', ''),
                    source=item.get('source', {}).get('name', 'Unknown'),
                    published_at=item.get('publishedAt', ''),
                    url=item.get('url', ''),
                    author=item.get('author')
                )
                articles.append(article)
            
            logger.info(f"Collected {len(articles)} articles from NewsAPI")
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting from NewsAPI: {str(e)}")
            return []
    
    def collect_from_guardian(self, 
                            query: str = None,
                            section: str = None,
                            page_size: int = 50) -> List[Article]:
        """
        Collect articles from Guardian API
        
        Args:
            query: Search query
            section: News section
            page_size: Number of articles
            
        Returns:
            List of Article objects
        """
        if 'guardian' not in self.api_keys:
            logger.warning("Guardian API key not provided")
            return []
        
        try:
            url = "https://content.guardianapis.com/search"
            params = {
                'api-key': self.api_keys['guardian'],
                'page-size': min(page_size, 50),  # Guardian limit
                'show-fields': 'headline,body,byline,publication-date'
            }
            
            if query:
                params['q'] = query
            if section:
                params['section'] = section
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for item in data.get('response', {}).get('results', []):
                fields = item.get('fields', {})
                article = Article(
                    id=f"guardian_{item['id']}",
                    title=fields.get('headline', ''),
                    content=fields.get('body', ''),
                    source='The Guardian',
                    published_at=fields.get('publication-date', ''),
                    url=item.get('webUrl', ''),
                    author=fields.get('byline', '')
                )
                articles.append(article)
            
            logger.info(f"Collected {len(articles)} articles from Guardian")
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting from Guardian: {str(e)}")
            return []
    
    def collect_from_reuters(self, 
                           query: str = None,
                           category: str = None,
                           limit: int = 50) -> List[Article]:
        """
        Collect articles from Reuters (using RSS feed)
        
        Args:
            query: Search query
            category: News category
            limit: Number of articles
            
        Returns:
            List of Article objects
        """
        try:
            import feedparser
            
            # Reuters RSS feeds
            rss_feeds = {
                'world': 'http://feeds.reuters.com/reuters/worldNews',
                'business': 'http://feeds.reuters.com/reuters/businessNews',
                'technology': 'http://feeds.reuters.com/reuters/technologyNews',
                'sports': 'http://feeds.reuters.com/reuters/sportsNews'
            }
            
            feed_url = rss_feeds.get(category, rss_feeds['world'])
            feed = feedparser.parse(feed_url)
            
            articles = []
            for entry in feed.entries[:limit]:
                # Extract content from summary or description
                content = entry.get('summary', '') or entry.get('description', '')
                
                article = Article(
                    id=f"reuters_{hash(entry.link)}",
                    title=entry.get('title', ''),
                    content=content,
                    source='Reuters',
                    published_at=entry.get('published', ''),
                    url=entry.get('link', ''),
                    category=category
                )
                articles.append(article)
            
            logger.info(f"Collected {len(articles)} articles from Reuters")
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting from Reuters: {str(e)}")
            return []
    
    def collect_from_multiple_sources(self, 
                                    sources: List[str] = None,
                                    query: str = None,
                                    max_articles: int = 200) -> List[Article]:
        """
        Collect articles from multiple sources
        
        Args:
            sources: List of source names
            query: Search query
            max_articles: Maximum number of articles
            
        Returns:
            List of Article objects
        """
        if sources is None:
            sources = ['newsapi', 'guardian', 'reuters']
        
        all_articles = []
        
        for source in sources:
            try:
                if source == 'newsapi':
                    articles = self.collect_from_newsapi(query=query)
                elif source == 'guardian':
                    articles = self.collect_from_guardian(query=query)
                elif source == 'reuters':
                    articles = self.collect_from_reuters(query=query)
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue
                
                all_articles.extend(articles)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting from {source}: {str(e)}")
                continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        # Limit to max_articles
        unique_articles = unique_articles[:max_articles]
        
        logger.info(f"Collected {len(unique_articles)} unique articles from {len(sources)} sources")
        return unique_articles
    
    def save_articles(self, articles: List[Article], filename: str):
        """
        Save articles to JSON file
        
        Args:
            articles: List of Article objects
            filename: Output filename
        """
        try:
            data = []
            for article in articles:
                data.append({
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'source': article.source,
                    'published_at': article.published_at,
                    'url': article.url,
                    'author': article.author,
                    'category': article.category
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(articles)} articles to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving articles: {str(e)}")
    
    def load_articles(self, filename: str) -> List[Article]:
        """
        Load articles from JSON file
        
        Args:
            filename: Input filename
            
        Returns:
            List of Article objects
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            articles = []
            for item in data:
                article = Article(
                    id=item['id'],
                    title=item['title'],
                    content=item['content'],
                    source=item['source'],
                    published_at=item['published_at'],
                    url=item['url'],
                    author=item.get('author'),
                    category=item.get('category')
                )
                articles.append(article)
            
            logger.info(f"Loaded {len(articles)} articles from {filename}")
            return articles
            
        except Exception as e:
            logger.error(f"Error loading articles: {str(e)}")
            return []
