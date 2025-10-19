"""
Pydantic models for the theme evolution system.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SurveyResponse(BaseModel):
    """Represents a single survey response."""
    id: Optional[int] = None
    batch_id: int
    question: str
    response_text: str
    embedding: Optional[List[float]] = None
    processed_at: Optional[datetime] = None


class Theme(BaseModel):
    """Represents an extracted theme."""
    id: Optional[int] = None
    name: str
    description: str
    embedding: Optional[List[float]] = None
    created_at_batch: int
    last_updated_batch: Optional[int] = None
    status: str = "active"
    parent_theme_id: Optional[int] = None
    response_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class HighlightedKeyword(BaseModel):
    """Represents a highlighted keyword with its contribution score."""
    keyword: str
    score: float
    positions: Optional[List[int]] = None


class ThemeAssignment(BaseModel):
    """Represents the assignment of a response to a theme."""
    id: Optional[int] = None
    response_id: int
    theme_id: int
    confidence_score: float = Field(ge=0, le=1)
    highlighted_keywords: List[HighlightedKeyword]
    assigned_at_batch: int
    last_updated_batch: Optional[int] = None


class ThemeEvolution(BaseModel):
    """Represents a change to a theme."""
    id: Optional[int] = None
    batch_id: int
    action: str  # created, updated, merged, split, deleted
    theme_id: int
    related_theme_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    affected_response_count: int = 0
    created_at: Optional[datetime] = None


class BatchMetadata(BaseModel):
    """Represents metadata about a processed batch."""
    batch_id: int
    question: str
    total_responses: int
    new_themes_count: int = 0
    updated_themes_count: int = 0
    deleted_themes_count: int = 0
    processing_time_seconds: Optional[float] = None
    processed_at: Optional[datetime] = None


class EmbeddingCache(BaseModel):
    """Represents a cached embedding."""
    id: Optional[int] = None
    text_hash: str
    embedding: List[float]
    model_name: str = "nomic-embed-text"
    created_at: Optional[datetime] = None


class ProcessingResult(BaseModel):
    """Output format for batch processing results."""
    batch_id: int
    question: str
    new_themes: List[Dict[str, Any]] = []
    updated_themes: List[Dict[str, Any]] = []
    deleted_themes: List[Dict[str, Any]] = []
    processing_time_seconds: float
    total_responses: int
    themes_created: int
    themes_updated: int
    themes_deleted: int


class BatchData(BaseModel):
    """Represents a batch of survey responses."""
    batch_id: int
    question: str
    responses: List[str]
