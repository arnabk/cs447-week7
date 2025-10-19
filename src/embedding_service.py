"""
Embedding service for generating and caching embeddings using Ollama.
"""

import hashlib
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
import yaml
import os

from models import EmbeddingCache
from database import DatabaseManager

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and caching embeddings using Ollama."""
    
    def __init__(self, config: Dict[str, Any], db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.ollama_base_url = config['ollama']['base_url']
        self.embedding_model = config['ollama']['embedding_model']
        self.timeout = config['ollama']['embedding_timeout']
        
    def _get_text_hash(self, text: str) -> str:
        """Generate SHA-256 hash for text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for text, using cache if available.
        
        Args:
            text: Text to embed
            use_cache: Whether to check cache first
            
        Returns:
            List of embedding values
        """
        if not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 768  # Default embedding size for nomic-embed-text
            
        text_hash = self._get_text_hash(text)
        
        # Check cache first
        if use_cache:
            cached_embedding = self._get_cached_embedding(text_hash)
            if cached_embedding is not None:
                logger.debug(f"Using cached embedding for text hash: {text_hash[:8]}...")
                return cached_embedding
        
        # Generate new embedding
        logger.debug(f"Generating new embedding for text: {text[:50]}...")
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            embedding = response.json()['embedding']
            
            # Cache the embedding
            if use_cache:
                self._cache_embedding(text_hash, embedding)
                
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to check cache first
            
        Returns:
            List of embedding lists
        """
        embeddings = []
        texts_to_embed = []
        text_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if use_cache:
                text_hash = self._get_text_hash(text)
                cached_embedding = self._get_cached_embedding(text_hash)
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                    continue
            
            texts_to_embed.append(text)
            text_indices.append(i)
            embeddings.append(None)  # Placeholder
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            logger.info(f"Generating embeddings for {len(texts_to_embed)} texts")
            try:
                # Process in smaller batches to avoid timeout
                batch_size = self.config['processing']['batch_size']
                for i in range(0, len(texts_to_embed), batch_size):
                    batch_texts = texts_to_embed[i:i + batch_size]
                    batch_indices = text_indices[i:i + batch_size]
                    
                    # Process each text individually since Ollama doesn't support batch embeddings
                    batch_embeddings = []
                    for text in batch_texts:
                        response = requests.post(
                            f"{self.ollama_base_url}/api/embeddings",
                            json={
                                "model": self.embedding_model,
                                "prompt": text
                            },
                            timeout=self.timeout
                        )
                        response.raise_for_status()
                        
                        embedding = response.json()['embedding']
                        batch_embeddings.append(embedding)
                    
                    # Fill in embeddings and cache them
                    for j, embedding in enumerate(batch_embeddings):
                        original_index = batch_indices[j]
                        embeddings[original_index] = embedding
                        
                        if use_cache:
                            text_hash = self._get_text_hash(texts_to_embed[j])
                            self._cache_embedding(text_hash, embedding)
                            
            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                raise
        
        return embeddings
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity score (0-1)
        """
        if not embedding1 or not embedding2:
            return 0.0
            
        # Convert to numpy arrays and reshape for sklearn
        emb1 = np.array(embedding1).reshape(1, -1)
        emb2 = np.array(embedding2).reshape(1, -1)
        
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)
    
    def _get_cached_embedding(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embedding from database."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT embedding FROM embedding_cache WHERE text_hash = %s",
                        (text_hash,)
                    )
                    result = cursor.fetchone()
                    if result:
                        embedding = result[0]
                        # Ensure embedding is a list of floats
                        if isinstance(embedding, str):
                            # Parse string representation of list
                            import ast
                            embedding = ast.literal_eval(embedding)
                        elif isinstance(embedding, (list, tuple)):
                            embedding = list(embedding)
                        return embedding
            return None
        except Exception as e:
            logger.warning(f"Failed to get cached embedding: {e}")
            return None
    
    def _cache_embedding(self, text_hash: str, embedding: List[float]) -> None:
        """Cache embedding in database."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO embedding_cache (text_hash, embedding, model_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (text_hash) DO NOTHING
                        """,
                        (text_hash, embedding, self.embedding_model)
                    )
                    conn.commit()
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM embedding_cache")
                    conn.commit()
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM embedding_cache")
                    total_cached = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(DISTINCT model_name) FROM embedding_cache")
                    models_count = cursor.fetchone()[0]
                    
                    return {
                        "total_cached": total_cached,
                        "models_count": models_count
                    }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"total_cached": 0, "models_count": 0}
