"""
Main theme processor that orchestrates the entire theme evolution pipeline.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from models import (
    SurveyResponse, Theme, ThemeAssignment, ThemeEvolution, 
    BatchMetadata, ProcessingResult, BatchData
)
from embedding_service import EmbeddingService
from database import DatabaseManager
from theme_extractor import ThemeExtractor
from keyword_highlighter import KeywordHighlighter
from theme_evolver import ThemeEvolver

logger = logging.getLogger(__name__)


class ThemeProcessor:
    """Main processor that orchestrates the theme evolution pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.db_manager = DatabaseManager(config)
        self.embedding_service = EmbeddingService(config, self.db_manager)
        self.theme_extractor = ThemeExtractor(config, self.embedding_service)
        self.keyword_highlighter = KeywordHighlighter(config, self.embedding_service)
        self.theme_evolver = ThemeEvolver(config, self.embedding_service, self.db_manager)
        
        # Processing statistics
        self.stats = {
            'total_batches_processed': 0,
            'total_themes_created': 0,
            'total_themes_merged': 0,
            'total_themes_split': 0,
            'total_themes_updated': 0,
            'total_responses_processed': 0
        }
    
    def process_batch(self, batch_data: BatchData) -> ProcessingResult:
        """
        Process a single batch of survey responses.
        
        Args:
            batch_data: Batch data containing question and responses
            
        Returns:
            Processing result with themes and changes
        """
        start_time = time.time()
        batch_id = batch_data.batch_id
        question = batch_data.question
        responses_text = batch_data.responses
        
        logger.info(f"Processing batch {batch_id}: '{question[:50]}...' with {len(responses_text)} responses")
        
        try:
            # Phase 1: Embed all responses
            logger.info("Phase 1: Embedding responses...")
            response_embeddings = self.embedding_service.get_embeddings_batch(responses_text)
            
            # Create SurveyResponse objects
            survey_responses = []
            for i, (text, embedding) in enumerate(zip(responses_text, response_embeddings)):
                response = SurveyResponse(
                    batch_id=batch_id,
                    question=question,
                    response_text=text,
                    embedding=embedding
                )
                response_id = self.db_manager.save_response(response)
                response.id = response_id
                survey_responses.append(response)
            
            # Phase 2: Get existing themes
            existing_themes = self.db_manager.get_all_themes()
            
            # Phase 3: Match responses to existing themes or create new ones
            logger.info("Phase 3: Matching responses to themes...")
            theme_matches = self.theme_evolver.match_to_existing_themes(survey_responses, existing_themes)
            
            # Phase 4: Process new themes for unmatched responses
            unmatched_responses = []
            for response in survey_responses:
                matched = False
                for theme_id, matched_responses in theme_matches.items():
                    if response in matched_responses:
                        matched = True
                        break
                if not matched:
                    unmatched_responses.append(response)
            
            new_themes = []
            if unmatched_responses:
                logger.info(f"Creating new themes for {len(unmatched_responses)} unmatched responses...")
                unmatched_texts = [r.response_text for r in unmatched_responses]
                new_themes = self.theme_extractor.extract_themes_from_batch(
                    question, unmatched_texts, batch_id
                )
                
                # Save new themes
                for theme in new_themes:
                    theme_id = self.db_manager.save_theme(theme)
                    theme.id = theme_id
                    new_themes.append(theme)
            
            # Phase 5: Detect theme merges
            logger.info("Phase 5: Detecting theme merges...")
            all_themes = existing_themes + new_themes
            merge_candidates = self.theme_evolver.detect_theme_merges(all_themes)
            
            merged_themes = []
            for theme1, theme2, similarity in merge_candidates:
                logger.info(f"Merging themes: '{theme1.name}' + '{theme2.name}' (similarity: {similarity:.3f})")
                merged_theme = self.theme_evolver.merge_themes(theme1, theme2, batch_id)
                merged_themes.append(merged_theme)
            
            # Phase 6: Detect theme splits
            logger.info("Phase 6: Detecting theme splits...")
            split_themes = []
            for theme in all_themes:
                if theme.id and theme.status == 'active':
                    assignments = self.db_manager.get_assignments_by_theme(theme.id)
                    split_candidates = self.theme_evolver.detect_theme_splits(theme, assignments)
                    if split_candidates:
                        split_themes.extend(split_candidates)
                        # Save split themes
                        for split_theme in split_candidates:
                            theme_id = self.db_manager.save_theme(split_theme)
                            split_theme.id = theme_id
                        split_themes.extend(split_candidates)
            
            # Phase 7: Update theme descriptions
            logger.info("Phase 7: Updating theme descriptions...")
            updated_themes = []
            for theme in all_themes:
                if theme.id and theme.status == 'active':
                    # Get new responses for this theme
                    theme_responses = theme_matches.get(str(theme.id), [])
                    if theme_responses:
                        updated_theme = self.theme_evolver.update_theme_description(
                            theme, theme_responses, self.theme_extractor
                        )
                        if updated_theme:
                            updated_themes.append(updated_theme)
            
            # Phase 8: Create theme assignments and highlight keywords
            logger.info("Phase 8: Creating assignments and highlighting keywords...")
            self._create_assignments_and_highlight(survey_responses, all_themes + merged_themes + split_themes)
            
            # Phase 9: Apply retroactive updates
            logger.info("Phase 9: Applying retroactive updates...")
            self._apply_retroactive_updates(batch_id, merged_themes, split_themes, updated_themes)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Save batch metadata
            batch_metadata = BatchMetadata(
                batch_id=batch_id,
                question=question,
                total_responses=len(survey_responses),
                new_themes_count=len(new_themes),
                updated_themes_count=len(updated_themes),
                deleted_themes_count=len(merge_candidates),  # Merged themes are "deleted"
                processing_time_seconds=processing_time
            )
            self.db_manager.save_batch_metadata(batch_metadata)
            
            # Update statistics
            self.stats['total_batches_processed'] += 1
            self.stats['total_themes_created'] += len(new_themes)
            self.stats['total_themes_merged'] += len(merge_candidates)
            self.stats['total_themes_split'] += len(split_themes)
            self.stats['total_themes_updated'] += len(updated_themes)
            self.stats['total_responses_processed'] += len(survey_responses)
            
            # Create processing result
            result = ProcessingResult(
                batch_id=batch_id,
                question=question,
                new_themes=self._format_new_themes(new_themes),
                updated_themes=self._format_updated_themes(updated_themes),
                deleted_themes=self._format_deleted_themes(merge_candidates),
                processing_time_seconds=processing_time,
                total_responses=len(survey_responses),
                themes_created=len(new_themes),
                themes_updated=len(updated_themes),
                themes_deleted=len(merge_candidates)
            )
            
            logger.info(f"Batch {batch_id} processed successfully in {processing_time:.2f}s")
            logger.info(f"Created {len(new_themes)} themes, updated {len(updated_themes)} themes, merged {len(merge_candidates)} themes")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process batch {batch_id}: {e}")
            raise
    
    def _create_assignments_and_highlight(self, responses: List[SurveyResponse], themes: List[Theme]) -> None:
        """Create theme assignments and highlight keywords."""
        for response in responses:
            if not response.embedding:
                continue
            
            # Find best matching theme
            best_theme = None
            best_similarity = 0.0
            
            for theme in themes:
                if not theme.embedding or theme.status != 'active':
                    continue
                
                similarity = self.embedding_service.cosine_similarity(response.embedding, theme.embedding)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_theme = theme
            
            if best_theme and best_similarity > self.config['thresholds']['similarity_existing_theme']:
                # Highlight keywords
                highlighted_keywords = self.keyword_highlighter.highlight_keywords(
                    response.response_text, best_theme.embedding
                )
                
                # Create assignment
                assignment = ThemeAssignment(
                    response_id=response.id,
                    theme_id=best_theme.id,
                    confidence_score=best_similarity,
                    highlighted_keywords=highlighted_keywords,
                    assigned_at_batch=response.batch_id
                )
                
                self.db_manager.save_theme_assignment(assignment)
                logger.debug(f"Assigned response {response.id} to theme '{best_theme.name}' (confidence: {best_similarity:.3f})")
    
    def _apply_retroactive_updates(self, batch_id: int, merged_themes: List[Theme], 
                                  split_themes: List[Theme], updated_themes: List[Theme]) -> None:
        """Apply retroactive updates to historical responses."""
        # This is a simplified version - in practice, you'd need to:
        # 1. Identify affected historical responses
        # 2. Update their assignments
        # 3. Re-highlight keywords if theme embeddings changed significantly
        # 4. Log all changes
        
        if merged_themes or split_themes or updated_themes:
            logger.info(f"Applying retroactive updates for {len(merged_themes)} merged, {len(split_themes)} split, {len(updated_themes)} updated themes")
            # Implementation would go here
            pass
    
    def _format_new_themes(self, themes: List[Theme]) -> List[Dict[str, Any]]:
        """Format new themes for output."""
        formatted = []
        for theme in themes:
            formatted.append({
                'theme_id': theme.id,
                'name': theme.name,
                'description': theme.description,
                'created_at_batch': theme.created_at_batch
            })
        return formatted
    
    def _format_updated_themes(self, themes: List[Theme]) -> List[Dict[str, Any]]:
        """Format updated themes for output."""
        formatted = []
        for theme in themes:
            formatted.append({
                'theme_id': theme.id,
                'name': theme.name,
                'description': theme.description,
                'updated_at_batch': theme.last_updated_batch
            })
        return formatted
    
    def _format_deleted_themes(self, merge_candidates: List) -> List[Dict[str, Any]]:
        """Format deleted/merged themes for output."""
        formatted = []
        for theme1, theme2, similarity in merge_candidates:
            formatted.append({
                'theme_id': theme1.id,
                'name': theme1.name,
                'reason': f"Merged with theme '{theme2.name}' (similarity: {similarity:.3f})",
                'merged_with': theme2.id
            })
        return formatted
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        db_stats = self.db_manager.get_database_stats()
        return {
            **self.stats,
            **db_stats,
            'cache_stats': self.embedding_service.get_cache_stats()
        }
    
    def test_system_health(self) -> Dict[str, bool]:
        """Test all system components."""
        health = {}
        
        # Test database connection
        health['database'] = self.db_manager.test_connection()
        
        # Test Ollama connection
        health['ollama'] = self.theme_extractor.test_connection()
        
        # Test embedding service
        try:
            test_embedding = self.embedding_service.get_embedding("test")
            health['embeddings'] = len(test_embedding) > 0
        except Exception:
            health['embeddings'] = False
        
        return health
    
    def process_multiple_batches(self, batches: List[BatchData]) -> List[ProcessingResult]:
        """Process multiple batches sequentially."""
        results = []
        
        logger.info(f"Processing {len(batches)} batches...")
        
        for i, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {i}/{len(batches)}: {batch.batch_id}")
            try:
                result = self.process_batch(batch)
                results.append(result)
                
                # Log progress
                if i % 10 == 0:
                    stats = self.get_processing_stats()
                    logger.info(f"Progress: {i}/{len(batches)} batches processed. "
                              f"Total themes: {stats['active_themes']}, "
                              f"Total responses: {stats['total_responses']}")
                
            except Exception as e:
                logger.error(f"Failed to process batch {batch.batch_id}: {e}")
                continue
        
        logger.info(f"Completed processing {len(results)}/{len(batches)} batches successfully")
        return results
