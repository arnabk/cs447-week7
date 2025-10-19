"""
Integration tests for the theme evolution system.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from src.theme_processor import ThemeProcessor
from src.models import BatchData


class TestThemeEvolutionIntegration:
    """Integration tests for the complete theme evolution system."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'user': 'test_user',
                'password': 'test_password'
            },
            'ollama': {
                'base_url': 'http://localhost:11434',
                'generation_model': 'llama3.1',
                'embedding_model': 'nomic-embed-text',
                'generation_timeout': 120,
                'embedding_timeout': 30
            },
            'thresholds': {
                'similarity_existing_theme': 0.75,
                'similarity_update_candidate': 0.50,
                'similarity_merge_themes': 0.85,
                'theme_split_variance': 0.40,
                'embedding_shift_recompute': 0.15,
                'keyword_contribution': 0.05,
                'min_responses_per_theme': 2
            },
            'processing': {
                'batch_size': 100,
                'max_keywords_per_response': 10,
                'theme_update_drift_threshold': 0.20
            },
            'ngrams': {
                'use_unigrams': True,
                'use_bigrams': True,
                'use_trigrams': True,
                'min_word_length': 3,
                'max_stopwords_in_phrase': 1
            }
        }
    
    @pytest.fixture
    def sample_batch_data(self):
        """Sample batch data for testing."""
        return BatchData(
            batch_id=1,
            question="What are the biggest challenges you face when integrating AI tools into your workflow?",
            responses=[
                "Difficulty aligning AI outputs with specific business logic.",
                "Lack of transparency or explainability in model decisions.",
                "Integration issues between AI APIs and internal platforms.",
                "Rapid changes in APIs leading to unstable production systems.",
                "Sometimes the models work great in demo, but fail silently in real-time use cases.",
                "Cost of running large models at scale is higher than expected.",
                "Privacy restrictions make it hard to use sensitive data for training.",
                "Limited internal expertise to evaluate model quality before deployment."
            ]
        )
    
    @patch('src.theme_processor.DatabaseManager')
    @patch('src.theme_processor.EmbeddingService')
    @patch('src.theme_processor.ThemeExtractor')
    @patch('src.theme_processor.KeywordHighlighter')
    @patch('src.theme_processor.ThemeEvolver')
    def test_theme_processor_initialization(self, mock_evolver, mock_highlighter, 
                                          mock_extractor, mock_embedding, mock_db, mock_config):
        """Test theme processor initialization."""
        processor = ThemeProcessor(mock_config)
        
        # Verify all components were initialized
        mock_db.assert_called_once_with(mock_config)
        mock_embedding.assert_called_once()
        mock_extractor.assert_called_once()
        mock_highlighter.assert_called_once()
        mock_evolver.assert_called_once()
    
    @patch('src.theme_processor.DatabaseManager')
    @patch('src.theme_processor.EmbeddingService')
    @patch('src.theme_processor.ThemeExtractor')
    @patch('src.theme_processor.KeywordHighlighter')
    @patch('src.theme_processor.ThemeEvolver')
    def test_system_health_check(self, mock_evolver, mock_highlighter, 
                                mock_extractor, mock_embedding, mock_db, mock_config):
        """Test system health check."""
        # Mock health check responses
        mock_db.return_value.test_connection.return_value = True
        mock_extractor.return_value.test_connection.return_value = True
        mock_embedding.return_value.get_embedding.return_value = [0.1, 0.2, 0.3]
        
        processor = ThemeProcessor(mock_config)
        health = processor.test_system_health()
        
        assert health['database'] is True
        assert health['ollama'] is True
        assert health['embeddings'] is True
    
    @patch('src.theme_processor.DatabaseManager')
    @patch('src.theme_processor.EmbeddingService')
    @patch('src.theme_processor.ThemeExtractor')
    @patch('src.theme_processor.KeywordHighlighter')
    @patch('src.theme_processor.ThemeEvolver')
    def test_batch_processing_flow(self, mock_evolver, mock_highlighter, 
                                 mock_extractor, mock_embedding, mock_db, mock_config, sample_batch_data):
        """Test complete batch processing flow."""
        # Mock all the dependencies
        mock_db_instance = mock_db.return_value
        mock_embedding_instance = mock_embedding.return_value
        mock_extractor_instance = mock_extractor.return_value
        mock_highlighter_instance = mock_highlighter.return_value
        mock_evolver_instance = mock_evolver.return_value
        
        # Mock database operations
        mock_db_instance.get_all_themes.return_value = []
        mock_db_instance.save_response.return_value = 1
        mock_db_instance.save_theme.return_value = 1
        mock_db_instance.save_batch_metadata.return_value = None
        
        # Mock embedding service
        mock_embedding_instance.get_embeddings_batch.return_value = [[0.1, 0.2, 0.3]] * 8
        
        # Mock theme extractor
        from src.models import Theme
        mock_themes = [
            Theme(
                id=1,
                name="API Integration Challenges",
                description="Challenges with API integration",
                embedding=[0.1, 0.2, 0.3],
                created_at_batch=1
            )
        ]
        mock_extractor_instance.extract_themes_from_batch.return_value = mock_themes
        
        # Mock theme evolver
        mock_evolver_instance.match_to_existing_themes.return_value = {}
        mock_evolver_instance.detect_theme_merges.return_value = []
        mock_evolver_instance.detect_theme_splits.return_value = None
        mock_evolver_instance.update_theme_description.return_value = None
        
        # Mock keyword highlighter
        mock_highlighter_instance.highlight_keywords.return_value = []
        
        # Create processor and process batch
        processor = ThemeProcessor(mock_config)
        result = processor.process_batch(sample_batch_data)
        
        # Verify result structure
        assert result.batch_id == 1
        assert result.total_responses == 8
        assert result.themes_created == 1
        assert result.processing_time_seconds > 0
        
        # Verify all components were called
        mock_embedding_instance.get_embeddings_batch.assert_called_once()
        mock_extractor_instance.extract_themes_from_batch.assert_called_once()
        mock_evolver_instance.match_to_existing_themes.assert_called_once()
        mock_db_instance.save_batch_metadata.assert_called_once()
    
    def test_processing_result_format(self, sample_batch_data):
        """Test processing result format."""
        from src.models import ProcessingResult
        
        result = ProcessingResult(
            batch_id=1,
            question=sample_batch_data.question,
            processing_time_seconds=2.5,
            total_responses=8,
            themes_created=2,
            themes_updated=1,
            themes_deleted=0
        )
        
        # Test serialization
        result_dict = result.dict()
        assert result_dict['batch_id'] == 1
        assert result_dict['total_responses'] == 8
        assert result_dict['themes_created'] == 2
        
        # Test JSON serialization
        json_str = result.json()
        assert '"batch_id": 1' in json_str
        assert '"total_responses": 8' in json_str
    
    def test_multiple_batch_processing(self, mock_config, sample_batch_data):
        """Test processing multiple batches."""
        with patch('src.theme_processor.DatabaseManager'), \
             patch('src.theme_processor.EmbeddingService'), \
             patch('src.theme_processor.ThemeExtractor'), \
             patch('src.theme_processor.KeywordHighlighter'), \
             patch('src.theme_processor.ThemeEvolver'):
            
            processor = ThemeProcessor(mock_config)
            
            # Create multiple batches
            batches = [
                sample_batch_data,
                BatchData(
                    batch_id=2,
                    question="What motivates you to contribute to open-source projects?",
                    responses=[
                        "Building a visible portfolio that helps in career growth.",
                        "Learning from code written by experienced developers.",
                        "Supporting communities that maintain tools I depend on."
                    ]
                )
            ]
            
            # Mock all the necessary methods
            processor.process_batch = Mock(return_value=Mock(dict=Mock(return_value={})))
            
            results = processor.process_multiple_batches(batches)
            
            assert len(results) == 2
            processor.process_batch.assert_called()
    
    def test_statistics_tracking(self, mock_config):
        """Test processing statistics tracking."""
        with patch('src.theme_processor.DatabaseManager'), \
             patch('src.theme_processor.EmbeddingService'), \
             patch('src.theme_processor.ThemeExtractor'), \
             patch('src.theme_processor.KeywordHighlighter'), \
             patch('src.theme_processor.ThemeEvolver'):
            
            processor = ThemeProcessor(mock_config)
            
            # Check initial stats
            stats = processor.get_processing_stats()
            assert stats['total_batches_processed'] == 0
            assert stats['total_themes_created'] == 0
            
            # Simulate processing
            processor.stats['total_batches_processed'] = 5
            processor.stats['total_themes_created'] = 10
            
            stats = processor.get_processing_stats()
            assert stats['total_batches_processed'] == 5
            assert stats['total_themes_created'] == 10
