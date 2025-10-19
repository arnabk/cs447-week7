"""
Database layer for PostgreSQL operations with pgvector support.
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple
import os

from models import (
    SurveyResponse, Theme, ThemeAssignment, ThemeEvolution, 
    BatchMetadata, EmbeddingCache
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and operation manager."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_config = config['database']
        
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"host={self.db_config['host']} "
            f"port={self.db_config['port']} "
            f"dbname={self.db_config['database']} "
            f"user={self.db_config['user']} "
            f"password={self.db_config['password']}"
        )
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager."""
        conn = None
        try:
            conn = psycopg2.connect(self.get_connection_string())
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # Survey Response Operations
    def save_response(self, response: SurveyResponse) -> int:
        """Save a survey response and return its ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO survey_responses (batch_id, question, response_text, embedding)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (response.batch_id, response.question, response.response_text, response.embedding)
                )
                response_id = cursor.fetchone()[0]
                conn.commit()
                return response_id
    
    def get_responses_by_batch(self, batch_id: int) -> List[SurveyResponse]:
        """Get all responses for a batch."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM survey_responses WHERE batch_id = %s ORDER BY id",
                    (batch_id,)
                )
                rows = cursor.fetchall()
                responses = []
                for row in rows:
                    # Fix embedding field if it's a string
                    if 'embedding' in row and row['embedding'] is not None:
                        if isinstance(row['embedding'], str):
                            import ast
                            row['embedding'] = ast.literal_eval(row['embedding'])
                    responses.append(SurveyResponse(**row))
                return responses
    
    def get_response_by_id(self, response_id: int) -> Optional[SurveyResponse]:
        """Get a response by ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM survey_responses WHERE id = %s",
                    (response_id,)
                )
                row = cursor.fetchone()
                if row:
                    # Fix embedding field if it's a string
                    if 'embedding' in row and row['embedding'] is not None:
                        if isinstance(row['embedding'], str):
                            import ast
                            row['embedding'] = ast.literal_eval(row['embedding'])
                    return SurveyResponse(**row)
                return None
    
    # Theme Operations
    def save_theme(self, theme: Theme) -> int:
        """Save a theme and return its ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO extracted_themes 
                    (name, description, embedding, created_at_batch, last_updated_batch, 
                     status, parent_theme_id, response_count, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (theme.name, theme.description, theme.embedding, theme.created_at_batch,
                     theme.last_updated_batch, theme.status, theme.parent_theme_id, 
                     theme.response_count, theme.metadata)
                )
                theme_id = cursor.fetchone()[0]
                conn.commit()
                return theme_id
    
    def get_all_themes(self, status: str = "active") -> List[Theme]:
        """Get all themes with given status."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM extracted_themes WHERE status = %s ORDER BY id",
                    (status,)
                )
                rows = cursor.fetchall()
                return [Theme(**row) for row in rows]
    
    def get_theme_by_id(self, theme_id: int) -> Optional[Theme]:
        """Get a theme by ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM extracted_themes WHERE id = %s",
                    (theme_id,)
                )
                row = cursor.fetchone()
                return Theme(**row) if row else None
    
    def update_theme(self, theme: Theme) -> None:
        """Update an existing theme."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE extracted_themes 
                    SET name = %s, description = %s, embedding = %s, 
                        last_updated_batch = %s, status = %s, response_count = %s, metadata = %s
                    WHERE id = %s
                    """,
                    (theme.name, theme.description, theme.embedding, theme.last_updated_batch,
                     theme.status, theme.response_count, theme.metadata, theme.id)
                )
                conn.commit()
    
    def delete_theme(self, theme_id: int) -> None:
        """Delete a theme (soft delete by setting status to 'deleted')."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE extracted_themes SET status = 'deleted' WHERE id = %s",
                    (theme_id,)
                )
                conn.commit()
    
    # Vector similarity search
    def find_similar_themes(self, embedding: List[float], threshold: float = 0.5, limit: int = 10) -> List[Tuple[Theme, float]]:
        """Find themes similar to the given embedding."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT *, 1 - (embedding <=> %s) as similarity
                    FROM extracted_themes 
                    WHERE status = 'active' AND 1 - (embedding <=> %s) > %s
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (embedding, embedding, threshold, embedding, limit)
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    theme = Theme(**{k: v for k, v in row.items() if k != 'similarity'})
                    similarity = row['similarity']
                    results.append((theme, similarity))
                return results
    
    def find_similar_responses(self, embedding: List[float], threshold: float = 0.5, limit: int = 10) -> List[Tuple[SurveyResponse, float]]:
        """Find responses similar to the given embedding."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT *, 1 - (embedding <=> %s) as similarity
                    FROM survey_responses 
                    WHERE embedding IS NOT NULL AND 1 - (embedding <=> %s) > %s
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (embedding, embedding, threshold, embedding, limit)
                )
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    # Fix embedding field if it's a string
                    if 'embedding' in row and row['embedding'] is not None:
                        if isinstance(row['embedding'], str):
                            import ast
                            row['embedding'] = ast.literal_eval(row['embedding'])
                    response = SurveyResponse(**{k: v for k, v in row.items() if k != 'similarity'})
                    similarity = row['similarity']
                    results.append((response, similarity))
                return results
    
    # Theme Assignment Operations
    def save_theme_assignment(self, assignment: ThemeAssignment) -> int:
        """Save a theme assignment and return its ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO theme_assignments 
                    (response_id, theme_id, confidence_score, highlighted_keywords, 
                     assigned_at_batch, last_updated_batch)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (response_id, theme_id) 
                    DO UPDATE SET 
                        confidence_score = EXCLUDED.confidence_score,
                        highlighted_keywords = EXCLUDED.highlighted_keywords,
                        last_updated_batch = EXCLUDED.assigned_at_batch
                    RETURNING id
                    """,
                    (assignment.response_id, assignment.theme_id, assignment.confidence_score,
                     [kw.dict() for kw in assignment.highlighted_keywords], 
                     assignment.assigned_at_batch, assignment.last_updated_batch)
                )
                assignment_id = cursor.fetchone()[0]
                conn.commit()
                return assignment_id
    
    def get_assignments_by_theme(self, theme_id: int) -> List[ThemeAssignment]:
        """Get all assignments for a theme."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM theme_assignments WHERE theme_id = %s ORDER BY confidence_score DESC",
                    (theme_id,)
                )
                rows = cursor.fetchall()
                assignments = []
                for row in rows:
                    # Convert highlighted_keywords back to HighlightedKeyword objects
                    highlighted_keywords = [
                        HighlightedKeyword(**kw) for kw in row['highlighted_keywords']
                    ]
                    assignment = ThemeAssignment(
                        **{k: v for k, v in row.items() if k != 'highlighted_keywords'},
                        highlighted_keywords=highlighted_keywords
                    )
                    assignments.append(assignment)
                return assignments
    
    def get_assignments_by_response(self, response_id: int) -> List[ThemeAssignment]:
        """Get all assignments for a response."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM theme_assignments WHERE response_id = %s ORDER BY confidence_score DESC",
                    (response_id,)
                )
                rows = cursor.fetchall()
                assignments = []
                for row in rows:
                    highlighted_keywords = [
                        HighlightedKeyword(**kw) for kw in row['highlighted_keywords']
                    ]
                    assignment = ThemeAssignment(
                        **{k: v for k, v in row.items() if k != 'highlighted_keywords'},
                        highlighted_keywords=highlighted_keywords
                    )
                    assignments.append(assignment)
                return assignments
    
    # Theme Evolution Operations
    def save_theme_evolution(self, evolution: ThemeEvolution) -> int:
        """Save a theme evolution record."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO theme_evolution_log 
                    (batch_id, action, theme_id, related_theme_id, details, affected_response_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (evolution.batch_id, evolution.action, evolution.theme_id, 
                     evolution.related_theme_id, evolution.details, evolution.affected_response_count)
                )
                evolution_id = cursor.fetchone()[0]
                conn.commit()
                return evolution_id
    
    def get_evolution_by_batch(self, batch_id: int) -> List[ThemeEvolution]:
        """Get all evolution records for a batch."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM theme_evolution_log WHERE batch_id = %s ORDER BY created_at",
                    (batch_id,)
                )
                rows = cursor.fetchall()
                return [ThemeEvolution(**row) for row in rows]
    
    # Batch Metadata Operations
    def save_batch_metadata(self, metadata: BatchMetadata) -> None:
        """Save batch processing metadata."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO batch_metadata 
                    (batch_id, question, total_responses, new_themes_count, 
                     updated_themes_count, deleted_themes_count, processing_time_seconds)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (batch_id) 
                    DO UPDATE SET 
                        question = EXCLUDED.question,
                        total_responses = EXCLUDED.total_responses,
                        new_themes_count = EXCLUDED.new_themes_count,
                        updated_themes_count = EXCLUDED.updated_themes_count,
                        deleted_themes_count = EXCLUDED.deleted_themes_count,
                        processing_time_seconds = EXCLUDED.processing_time_seconds
                    """,
                    (metadata.batch_id, metadata.question, metadata.total_responses,
                     metadata.new_themes_count, metadata.updated_themes_count, 
                     metadata.deleted_themes_count, metadata.processing_time_seconds)
                )
                conn.commit()
    
    def get_batch_metadata(self, batch_id: int) -> Optional[BatchMetadata]:
        """Get batch metadata by batch ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM batch_metadata WHERE batch_id = %s",
                    (batch_id,)
                )
                row = cursor.fetchone()
                return BatchMetadata(**row) if row else None
    
    # Utility methods
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                stats = {}
                
                # Count themes
                cursor.execute("SELECT COUNT(*) FROM extracted_themes WHERE status = 'active'")
                stats['active_themes'] = cursor.fetchone()[0]
                
                # Count responses
                cursor.execute("SELECT COUNT(*) FROM survey_responses")
                stats['total_responses'] = cursor.fetchone()[0]
                
                # Count assignments
                cursor.execute("SELECT COUNT(*) FROM theme_assignments")
                stats['total_assignments'] = cursor.fetchone()[0]
                
                # Count batches
                cursor.execute("SELECT COUNT(*) FROM batch_metadata")
                stats['total_batches'] = cursor.fetchone()[0]
                
                return stats
