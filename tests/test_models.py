"""
Tests for Pydantic models.
"""

import pytest
from datetime import datetime
from src.models import (
    SurveyResponse, Theme, ThemeAssignment, ThemeEvolution, 
    BatchMetadata, HighlightedKeyword, ProcessingResult, BatchData
)


class TestSurveyResponse:
    """Test SurveyResponse model."""
    
    def test_create_survey_response(self):
        """Test creating a survey response."""
        response = SurveyResponse(
            batch_id=1,
            question="What are your biggest challenges?",
            response_text="Integration issues with APIs"
        )
        
        assert response.batch_id == 1
        assert response.question == "What are your biggest challenges?"
        assert response.response_text == "Integration issues with APIs"
        assert response.embedding is None
        assert response.processed_at is None
    
    def test_survey_response_with_embedding(self):
        """Test survey response with embedding."""
        embedding = [0.1, 0.2, 0.3]
        response = SurveyResponse(
            batch_id=1,
            question="Test question",
            response_text="Test response",
            embedding=embedding
        )
        
        assert response.embedding == embedding


class TestTheme:
    """Test Theme model."""
    
    def test_create_theme(self):
        """Test creating a theme."""
        theme = Theme(
            name="API Integration Challenges",
            description="Issues related to integrating external APIs",
            created_at_batch=1
        )
        
        assert theme.name == "API Integration Challenges"
        assert theme.description == "Issues related to integrating external APIs"
        assert theme.created_at_batch == 1
        assert theme.status == "active"
        assert theme.response_count == 0
    
    def test_theme_with_embedding(self):
        """Test theme with embedding."""
        embedding = [0.1, 0.2, 0.3]
        theme = Theme(
            name="Test Theme",
            description="Test description",
            created_at_batch=1,
            embedding=embedding
        )
        
        assert theme.embedding == embedding


class TestHighlightedKeyword:
    """Test HighlightedKeyword model."""
    
    def test_create_highlighted_keyword(self):
        """Test creating a highlighted keyword."""
        keyword = HighlightedKeyword(
            keyword="API",
            score=0.85,
            positions=[10, 25]
        )
        
        assert keyword.keyword == "API"
        assert keyword.score == 0.85
        assert keyword.positions == [10, 25]
    
    def test_highlighted_keyword_without_positions(self):
        """Test highlighted keyword without positions."""
        keyword = HighlightedKeyword(
            keyword="integration",
            score=0.75
        )
        
        assert keyword.keyword == "integration"
        assert keyword.score == 0.75
        assert keyword.positions is None


class TestThemeAssignment:
    """Test ThemeAssignment model."""
    
    def test_create_theme_assignment(self):
        """Test creating a theme assignment."""
        keywords = [
            HighlightedKeyword(keyword="API", score=0.8),
            HighlightedKeyword(keyword="integration", score=0.6)
        ]
        
        assignment = ThemeAssignment(
            response_id=1,
            theme_id=2,
            confidence_score=0.85,
            highlighted_keywords=keywords,
            assigned_at_batch=1
        )
        
        assert assignment.response_id == 1
        assert assignment.theme_id == 2
        assert assignment.confidence_score == 0.85
        assert len(assignment.highlighted_keywords) == 2
        assert assignment.assigned_at_batch == 1
    
    def test_theme_assignment_confidence_validation(self):
        """Test confidence score validation."""
        # Valid confidence scores
        assignment1 = ThemeAssignment(
            response_id=1, theme_id=1, confidence_score=0.0,
            highlighted_keywords=[], assigned_at_batch=1
        )
        assert assignment1.confidence_score == 0.0
        
        assignment2 = ThemeAssignment(
            response_id=1, theme_id=1, confidence_score=1.0,
            highlighted_keywords=[], assigned_at_batch=1
        )
        assert assignment2.confidence_score == 1.0
        
        # Invalid confidence scores should raise validation error
        with pytest.raises(ValueError):
            ThemeAssignment(
                response_id=1, theme_id=1, confidence_score=-0.1,
                highlighted_keywords=[], assigned_at_batch=1
            )
        
        with pytest.raises(ValueError):
            ThemeAssignment(
                response_id=1, theme_id=1, confidence_score=1.1,
                highlighted_keywords=[], assigned_at_batch=1
            )


class TestBatchData:
    """Test BatchData model."""
    
    def test_create_batch_data(self):
        """Test creating batch data."""
        responses = [
            "Response 1",
            "Response 2",
            "Response 3"
        ]
        
        batch = BatchData(
            batch_id=1,
            question="What are your challenges?",
            responses=responses
        )
        
        assert batch.batch_id == 1
        assert batch.question == "What are your challenges?"
        assert len(batch.responses) == 3
        assert batch.responses == responses


class TestProcessingResult:
    """Test ProcessingResult model."""
    
    def test_create_processing_result(self):
        """Test creating processing result."""
        result = ProcessingResult(
            batch_id=1,
            question="Test question",
            processing_time_seconds=2.5,
            total_responses=5,
            themes_created=2,
            themes_updated=1,
            themes_deleted=0
        )
        
        assert result.batch_id == 1
        assert result.question == "Test question"
        assert result.processing_time_seconds == 2.5
        assert result.total_responses == 5
        assert result.themes_created == 2
        assert result.themes_updated == 1
        assert result.themes_deleted == 0
        assert result.new_themes == []
        assert result.updated_themes == []
        assert result.deleted_themes == []
