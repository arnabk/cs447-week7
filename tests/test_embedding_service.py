"""
Tests for embedding service.
"""

import pytest
from unittest.mock import Mock, patch
from src.embedding_service import EmbeddingService
from src.database import DatabaseManager


class TestEmbeddingService:
    """Test EmbeddingService class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'ollama': {
                'base_url': 'http://localhost:11434',
                'embedding_model': 'nomic-embed-text',
                'embedding_timeout': 30
            },
            'processing': {
                'batch_size': 100
            }
        }
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        return Mock(spec=DatabaseManager)
    
    @pytest.fixture
    def embedding_service(self, mock_config, mock_db_manager):
        """Create embedding service with mocked dependencies."""
        return EmbeddingService(mock_config, mock_db_manager)
    
    def test_get_text_hash(self, embedding_service):
        """Test text hashing."""
        text1 = "Hello world"
        text2 = "Hello world"
        text3 = "Hello universe"
        
        hash1 = embedding_service._get_text_hash(text1)
        hash2 = embedding_service._get_text_hash(text2)
        hash3 = embedding_service._get_text_hash(text3)
        
        assert hash1 == hash2  # Same text should produce same hash
        assert hash1 != hash3  # Different text should produce different hash
        assert len(hash1) == 64  # SHA-256 produces 64 character hex string
    
    @patch('src.embedding_service.ollama.Client')
    def test_get_embedding_success(self, mock_ollama_client, embedding_service):
        """Test successful embedding generation."""
        # Mock Ollama response
        mock_response = {'embedding': [0.1, 0.2, 0.3]}
        mock_ollama_client.return_value.embeddings.return_value = mock_response
        
        # Mock database operations
        embedding_service._get_cached_embedding = Mock(return_value=None)
        embedding_service._cache_embedding = Mock()
        
        result = embedding_service.get_embedding("test text")
        
        assert result == [0.1, 0.2, 0.3]
        mock_ollama_client.return_value.embeddings.assert_called_once()
    
    @patch('src.embedding_service.ollama.Client')
    def test_get_embedding_with_cache(self, mock_ollama_client, embedding_service):
        """Test embedding generation with cache hit."""
        # Mock cache hit
        embedding_service._get_cached_embedding = Mock(return_value=[0.1, 0.2, 0.3])
        
        result = embedding_service.get_embedding("test text")
        
        assert result == [0.1, 0.2, 0.3]
        # Should not call Ollama if cached
        mock_ollama_client.return_value.embeddings.assert_not_called()
    
    def test_get_embedding_empty_text(self, embedding_service):
        """Test embedding generation with empty text."""
        result = embedding_service.get_embedding("")
        
        assert result == [0.0] * 768  # Default embedding size
    
    @patch('src.embedding_service.ollama.Client')
    def test_get_embeddings_batch(self, mock_ollama_client, embedding_service):
        """Test batch embedding generation."""
        texts = ["text1", "text2", "text3"]
        mock_embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        
        mock_response = {'embeddings': mock_embeddings}
        mock_ollama_client.return_value.embeddings.return_value = mock_response
        
        # Mock cache miss
        embedding_service._get_cached_embedding = Mock(return_value=None)
        embedding_service._cache_embedding = Mock()
        
        result = embedding_service.get_embeddings_batch(texts)
        
        assert len(result) == 3
        assert result == mock_embeddings
    
    def test_cosine_similarity(self, embedding_service):
        """Test cosine similarity calculation."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]  # Identical
        emb3 = [0.0, 1.0, 0.0]  # Orthogonal
        emb4 = [-1.0, 0.0, 0.0]  # Opposite
        
        # Identical embeddings should have similarity 1.0
        sim1 = embedding_service.cosine_similarity(emb1, emb2)
        assert abs(sim1 - 1.0) < 0.001
        
        # Orthogonal embeddings should have similarity 0.0
        sim2 = embedding_service.cosine_similarity(emb1, emb3)
        assert abs(sim2 - 0.0) < 0.001
        
        # Opposite embeddings should have similarity -1.0
        sim3 = embedding_service.cosine_similarity(emb1, emb4)
        assert abs(sim3 - (-1.0)) < 0.001
    
    def test_cosine_similarity_empty_embeddings(self, embedding_service):
        """Test cosine similarity with empty embeddings."""
        result = embedding_service.cosine_similarity([], [])
        assert result == 0.0
        
        result = embedding_service.cosine_similarity([1.0, 2.0], [])
        assert result == 0.0
    
    def test_get_cache_stats(self, embedding_service, mock_db_manager):
        """Test cache statistics retrieval."""
        mock_db_manager.get_connection.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            (100,),  # total_cached
            (2,)     # models_count
        ]
        
        stats = embedding_service.get_cache_stats()
        
        assert stats['total_cached'] == 100
        assert stats['models_count'] == 2
    
    def test_clear_cache(self, embedding_service, mock_db_manager):
        """Test cache clearing."""
        embedding_service.clear_cache()
        
        # Verify database operations were called
        mock_db_manager.get_connection.assert_called()
