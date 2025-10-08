"""
Transformer-based summarization for news articles
"""

import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,
    pipeline
)
from typing import List, Dict, Any, Optional
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class TransformerSummarizer:
    """
    Transformer-based summarization using pre-trained models
    """
    
    def __init__(self, 
                 model_name: str = "facebook/bart-large-cnn",
                 max_length: int = 1024,
                 min_length: int = 50,
                 device: str = "auto"):
        """
        Initialize transformer summarizer
        
        Args:
            model_name: HuggingFace model name
            max_length: Maximum input length
            min_length: Minimum summary length
            device: Device to use ('auto', 'cpu', 'cuda')
        """
        self.model_name = model_name
        self.max_length = max_length
        self.min_length = min_length
        
        # Set device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Using device: {self.device}")
        
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.to(self.device)
        
        # Create summarization pipeline
        self.summarizer = pipeline(
            "summarization",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if self.device == "cuda" else -1
        )
        
        # Initialize sentence transformer for similarity
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def summarize_single_article(self, 
                                text: str, 
                                max_length: Optional[int] = None,
                                min_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Summarize a single article
        
        Args:
            text: Article text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            Dictionary with summary and metadata
        """
        try:
            # Truncate text if too long
            if len(text) > self.max_length:
                text = text[:self.max_length]
            
            # Generate summary
            summary = self.summarizer(
                text,
                max_length=max_length or self.max_length // 4,
                min_length=min_length or self.min_length,
                do_sample=False
            )
            
            summary_text = summary[0]['summary_text']
            
            # Calculate compression ratio
            compression_ratio = len(summary_text) / len(text)
            
            return {
                'summary': summary_text,
                'compression_ratio': compression_ratio,
                'original_length': len(text),
                'summary_length': len(summary_text),
                'model': self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error summarizing article: {str(e)}")
            return {
                'summary': "Error generating summary",
                'compression_ratio': 0.0,
                'original_length': len(text),
                'summary_length': 0,
                'model': self.model_name,
                'error': str(e)
            }
    
    def summarize_cluster(self, 
                         articles: List[Dict[str, Any]], 
                         method: str = "combined") -> Dict[str, Any]:
        """
        Summarize a cluster of articles
        
        Args:
            articles: List of article dictionaries
            method: Summarization method ('combined', 'representative', 'hierarchical')
            
        Returns:
            Dictionary with cluster summary and metadata
        """
        try:
            if not articles:
                return {
                    'summary': "No articles to summarize",
                    'key_points': [],
                    'confidence': 0.0,
                    'method': method
                }
            
            if method == "combined":
                return self._summarize_combined(articles)
            elif method == "representative":
                return self._summarize_representative(articles)
            elif method == "hierarchical":
                return self._summarize_hierarchical(articles)
            else:
                raise ValueError(f"Unknown summarization method: {method}")
                
        except Exception as e:
            logger.error(f"Error summarizing cluster: {str(e)}")
            return {
                'summary': "Error generating cluster summary",
                'key_points': [],
                'confidence': 0.0,
                'method': method,
                'error': str(e)
            }
    
    def _summarize_combined(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine all articles and summarize as one document
        """
        # Combine all article texts
        combined_text = "\n\n".join([
            f"{article.get('title', '')}\n{article.get('content', '')}"
            for article in articles
        ])
        
        # Truncate if too long
        if len(combined_text) > self.max_length:
            combined_text = combined_text[:self.max_length]
        
        # Generate summary
        summary_result = self.summarize_single_article(combined_text)
        
        # Extract key points from individual articles
        key_points = []
        for article in articles[:5]:  # Limit to first 5 articles
            if 'title' in article:
                key_points.append(article['title'])
        
        return {
            'summary': summary_result['summary'],
            'key_points': key_points,
            'confidence': 0.8,
            'method': 'combined',
            'n_articles': len(articles)
        }
    
    def _summarize_representative(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find most representative article and summarize it
        """
        if len(articles) == 1:
            article = articles[0]
            summary_result = self.summarize_single_article(
                f"{article.get('title', '')}\n{article.get('content', '')}"
            )
            return {
                'summary': summary_result['summary'],
                'key_points': [article.get('title', '')],
                'confidence': 0.9,
                'method': 'representative',
                'n_articles': 1
            }
        
        # Find most representative article using sentence embeddings
        article_texts = [
            f"{article.get('title', '')}\n{article.get('content', '')}"
            for article in articles
        ]
        
        # Calculate embeddings
        embeddings = self.sentence_model.encode(article_texts)
        
        # Find centroid
        centroid = np.mean(embeddings, axis=0)
        
        # Find most similar article to centroid
        similarities = np.dot(embeddings, centroid) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(centroid)
        )
        
        most_representative_idx = np.argmax(similarities)
        representative_article = articles[most_representative_idx]
        
        # Summarize representative article
        summary_result = self.summarize_single_article(
            f"{representative_article.get('title', '')}\n{representative_article.get('content', '')}"
        )
        
        return {
            'summary': summary_result['summary'],
            'key_points': [representative_article.get('title', '')],
            'confidence': 0.7,
            'method': 'representative',
            'n_articles': len(articles)
        }
    
    def _summarize_hierarchical(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Hierarchical summarization: summarize groups, then combine
        """
        if len(articles) <= 3:
            return self._summarize_combined(articles)
        
        # Group articles by similarity
        article_texts = [
            f"{article.get('title', '')}\n{article.get('content', '')}"
            for article in articles
        ]
        
        # Calculate pairwise similarities
        embeddings = self.sentence_model.encode(article_texts)
        similarities = np.dot(embeddings, embeddings.T)
        
        # Simple grouping based on similarity threshold
        groups = []
        used_indices = set()
        
        for i, article in enumerate(articles):
            if i in used_indices:
                continue
                
            group = [articles[i]]
            used_indices.add(i)
            
            for j, other_article in enumerate(articles[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                if similarities[i, j] > 0.7:  # Similarity threshold
                    group.append(other_article)
                    used_indices.add(j)
            
            groups.append(group)
        
        # Summarize each group
        group_summaries = []
        all_key_points = []
        
        for group in groups:
            if len(group) == 1:
                summary_result = self.summarize_single_article(
                    f"{group[0].get('title', '')}\n{group[0].get('content', '')}"
                )
                group_summaries.append(summary_result['summary'])
                all_key_points.append(group[0].get('title', ''))
            else:
                combined_text = "\n\n".join([
                    f"{article.get('title', '')}\n{article.get('content', '')}"
                    for article in group
                ])
                summary_result = self.summarize_single_article(combined_text)
                group_summaries.append(summary_result['summary'])
                all_key_points.extend([article.get('title', '') for article in group[:2]])
        
        # Combine group summaries
        final_summary = "\n\n".join(group_summaries)
        
        return {
            'summary': final_summary,
            'key_points': all_key_points[:5],  # Limit key points
            'confidence': 0.75,
            'method': 'hierarchical',
            'n_articles': len(articles),
            'n_groups': len(groups)
        }
    
    def get_summary_quality_score(self, summary: str, original_text: str) -> float:
        """
        Calculate quality score for summary
        
        Args:
            summary: Generated summary
            original_text: Original text
            
        Returns:
            Quality score between 0 and 1
        """
        try:
            # Calculate compression ratio
            compression_ratio = len(summary) / len(original_text)
            
            # Ideal compression ratio is between 0.1 and 0.3
            if 0.1 <= compression_ratio <= 0.3:
                compression_score = 1.0
            else:
                compression_score = max(0.0, 1.0 - abs(compression_ratio - 0.2) * 2)
            
            # Calculate semantic similarity
            summary_embedding = self.sentence_model.encode([summary])
            original_embedding = self.sentence_model.encode([original_text])
            
            similarity = np.dot(summary_embedding[0], original_embedding[0]) / (
                np.linalg.norm(summary_embedding[0]) * np.linalg.norm(original_embedding[0])
            )
            
            # Combine scores
            quality_score = (compression_score * 0.3 + similarity * 0.7)
            
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {str(e)}")
            return 0.0
