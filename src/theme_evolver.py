"""
Theme evolution logic for merging, splitting, and updating themes over time.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .models import Theme, SurveyResponse, ThemeAssignment, ThemeEvolution
from .embedding_service import EmbeddingService
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class ThemeEvolver:
    """Handles theme evolution including merging, splitting, and updating."""
    
    def __init__(self, config: Dict[str, Any], embedding_service: EmbeddingService, db_manager: DatabaseManager):
        self.config = config
        self.embedding_service = embedding_service
        self.db_manager = db_manager
        
        # Thresholds
        self.similarity_existing = config['thresholds']['similarity_existing_theme']
        self.similarity_update = config['thresholds']['similarity_update_candidate']
        self.similarity_merge = config['thresholds']['similarity_merge_themes']
        self.split_variance = config['thresholds']['theme_split_variance']
        self.embedding_shift = config['thresholds']['embedding_shift_recompute']
        self.drift_threshold = config['processing']['theme_update_drift_threshold']
        self.min_responses = config['thresholds']['min_responses_per_theme']
    
    def match_to_existing_themes(self, responses: List[SurveyResponse], existing_themes: List[Theme]) -> Dict[str, List[SurveyResponse]]:
        """
        Match responses to existing themes based on similarity.
        
        Args:
            responses: New responses to match
            existing_themes: Current active themes
            
        Returns:
            Dictionary mapping theme_id to matched responses
        """
        matches = {}
        
        for response in responses:
            if not response.embedding:
                logger.warning(f"Response {response.id} has no embedding, skipping")
                continue
            
            best_match = None
            best_similarity = 0.0
            
            for theme in existing_themes:
                if not theme.embedding:
                    continue
                
                similarity = self.embedding_service.cosine_similarity(response.embedding, theme.embedding)
                
                if similarity > best_similarity and similarity > self.similarity_existing:
                    best_similarity = similarity
                    best_match = theme
            
            if best_match:
                theme_id = str(best_match.id)
                if theme_id not in matches:
                    matches[theme_id] = []
                matches[theme_id].append(response)
                logger.debug(f"Matched response {response.id} to theme {best_match.name} (similarity: {best_similarity:.3f})")
            else:
                logger.debug(f"No match found for response {response.id} (best similarity: {best_similarity:.3f})")
        
        return matches
    
    def detect_theme_merges(self, themes: List[Theme]) -> List[Tuple[Theme, Theme, float]]:
        """
        Detect themes that should be merged based on similarity.
        
        Args:
            themes: List of themes to check
            
        Returns:
            List of (theme1, theme2, similarity) tuples for themes to merge
        """
        merge_candidates = []
        
        for i, theme1 in enumerate(themes):
            for theme2 in themes[i+1:]:
                if not theme1.embedding or not theme2.embedding:
                    continue
                
                similarity = self.embedding_service.cosine_similarity(theme1.embedding, theme2.embedding)
                
                if similarity > self.similarity_merge:
                    merge_candidates.append((theme1, theme2, similarity))
                    logger.info(f"Merge candidate: '{theme1.name}' + '{theme2.name}' (similarity: {similarity:.3f})")
        
        # Sort by similarity (highest first)
        merge_candidates.sort(key=lambda x: x[2], reverse=True)
        return merge_candidates
    
    def merge_themes(self, theme1: Theme, theme2: Theme, batch_id: int) -> Theme:
        """
        Merge two themes into one.
        
        Args:
            theme1: First theme to merge
            theme2: Second theme to merge
            batch_id: Current batch ID
            
        Returns:
            Merged theme
        """
        logger.info(f"Merging themes: '{theme1.name}' + '{theme2.name}'")
        
        # Create merged theme
        merged_name = f"{theme1.name} & {theme2.name}"
        merged_description = f"Combined theme covering: {theme1.description} and {theme2.description}"
        
        # Average the embeddings
        if theme1.embedding and theme2.embedding:
            merged_embedding = [
                (a + b) / 2 for a, b in zip(theme1.embedding, theme2.embedding)
            ]
        else:
            merged_embedding = theme1.embedding or theme2.embedding
        
        merged_theme = Theme(
            name=merged_name,
            description=merged_description,
            embedding=merged_embedding,
            created_at_batch=batch_id,
            response_count=theme1.response_count + theme2.response_count,
            metadata={
                'merged_from': [theme1.id, theme2.id],
                'merge_batch': batch_id
            }
        )
        
        # Save merged theme
        merged_theme_id = self.db_manager.save_theme(merged_theme)
        merged_theme.id = merged_theme_id
        
        # Update assignments to point to merged theme
        self._update_assignments_for_merge(theme1.id, theme2.id, merged_theme_id, batch_id)
        
        # Mark original themes as merged
        theme1.status = 'merged'
        theme1.last_updated_batch = batch_id
        theme2.status = 'merged'
        theme2.last_updated_batch = batch_id
        
        self.db_manager.update_theme(theme1)
        self.db_manager.update_theme(theme2)
        
        # Log the merge
        self.db_manager.save_theme_evolution(ThemeEvolution(
            batch_id=batch_id,
            action='merged',
            theme_id=merged_theme_id,
            related_theme_id=theme1.id,
            details={
                'merged_themes': [theme1.id, theme2.id],
                'merged_theme_name': merged_name
            },
            affected_response_count=theme1.response_count + theme2.response_count
        ))
        
        return merged_theme
    
    def detect_theme_splits(self, theme: Theme, assignments: List[ThemeAssignment]) -> Optional[List[Theme]]:
        """
        Detect if a theme should be split based on response clustering.
        
        Args:
            theme: Theme to check for splitting
            assignments: Assignments for this theme
            
        Returns:
            List of new themes if split is needed, None otherwise
        """
        if len(assignments) < 6:  # Need minimum responses for meaningful clustering
            return None
        
        # Get response embeddings
        response_embeddings = []
        response_ids = []
        
        for assignment in assignments:
            response = self.db_manager.get_response_by_id(assignment.response_id)
            if response and response.embedding:
                response_embeddings.append(response.embedding)
                response_ids.append(response.id)
        
        if len(response_embeddings) < 6:
            return None
        
        # Try clustering with k=2
        try:
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(response_embeddings)
            
            # Check if clusters are well-separated
            silhouette_avg = silhouette_score(response_embeddings, cluster_labels)
            
            if silhouette_avg > self.split_variance:
                logger.info(f"Theme '{theme.name}' has good split potential (silhouette: {silhouette_avg:.3f})")
                return self._create_split_themes(theme, assignments, cluster_labels, response_ids)
            else:
                logger.debug(f"Theme '{theme.name}' split rejected (silhouette: {silhouette_avg:.3f})")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to analyze theme split for '{theme.name}': {e}")
            return None
    
    def _create_split_themes(self, original_theme: Theme, assignments: List[ThemeAssignment], 
                           cluster_labels: List[int], response_ids: List[int]) -> List[Theme]:
        """Create new themes from a split."""
        logger.info(f"Splitting theme: '{original_theme.name}'")
        
        # Group assignments by cluster
        cluster_assignments = {0: [], 1: []}
        for i, assignment in enumerate(assignments):
            if i < len(cluster_labels):
                cluster_assignments[cluster_labels[i]].append(assignment)
        
        new_themes = []
        
        for cluster_id, cluster_assignments_list in cluster_assignments.items():
            if len(cluster_assignments_list) < self.min_responses:
                continue
            
            # Create new theme name and description
            new_name = f"{original_theme.name} - Cluster {cluster_id + 1}"
            new_description = f"Sub-theme of {original_theme.name}: {original_theme.description}"
            
            # Calculate new embedding (average of cluster responses)
            cluster_embeddings = []
            for assignment in cluster_assignments_list:
                response = self.db_manager.get_response_by_id(assignment.response_id)
                if response and response.embedding:
                    cluster_embeddings.append(response.embedding)
            
            if cluster_embeddings:
                new_embedding = [
                    sum(emb[i] for emb in cluster_embeddings) / len(cluster_embeddings)
                    for i in range(len(cluster_embeddings[0]))
                ]
            else:
                new_embedding = original_theme.embedding
            
            new_theme = Theme(
                name=new_name,
                description=new_description,
                embedding=new_embedding,
                created_at_batch=original_theme.created_at_batch,
                response_count=len(cluster_assignments_list),
                parent_theme_id=original_theme.id,
                metadata={
                    'split_from': original_theme.id,
                    'cluster_id': cluster_id
                }
            )
            
            new_themes.append(new_theme)
        
        return new_themes
    
    def update_theme_description(self, theme: Theme, new_responses: List[SurveyResponse], 
                                theme_extractor) -> Optional[Theme]:
        """
        Update a theme's description based on new responses.
        
        Args:
            theme: Theme to update
            new_responses: New responses to consider
            theme_extractor: Theme extractor for description updates
            
        Returns:
            Updated theme if changes were made
        """
        if not new_responses:
            return None
        
        # Check if we have enough new responses to warrant an update
        if len(new_responses) < 2:
            return None
        
        # Get current theme assignments to check for drift
        current_assignments = self.db_manager.get_assignments_by_theme(theme.id)
        
        if len(current_assignments) < 5:  # Need some history to detect drift
            return None
        
        # Calculate drift in new responses
        new_response_texts = [r.response_text for r in new_responses]
        drift_score = self._calculate_theme_drift(theme, new_response_texts)
        
        if drift_score < self.drift_threshold:
            logger.debug(f"Theme '{theme.name}' drift score {drift_score:.3f} below threshold")
            return None
        
        logger.info(f"Updating theme '{theme.name}' due to drift (score: {drift_score:.3f})")
        
        # Update description using theme extractor
        try:
            updated_description = theme_extractor.update_theme_description(theme, new_response_texts)
            
            if updated_description != theme.description:
                # Check if embedding needs updating
                old_embedding = theme.embedding
                new_embedding = self.embedding_service.get_embedding(f"{theme.name}: {updated_description}")
                
                embedding_distance = 1 - self.embedding_service.cosine_similarity(old_embedding, new_embedding)
                
                if embedding_distance > self.embedding_shift:
                    logger.info(f"Theme '{theme.name}' embedding shifted significantly ({embedding_distance:.3f})")
                    theme.embedding = new_embedding
                
                theme.description = updated_description
                theme.last_updated_batch = new_responses[0].batch_id
                
                self.db_manager.update_theme(theme)
                
                # Log the update
                self.db_manager.save_theme_evolution(ThemeEvolution(
                    batch_id=new_responses[0].batch_id,
                    action='updated',
                    theme_id=theme.id,
                    details={
                        'old_description': theme.description,
                        'new_description': updated_description,
                        'drift_score': drift_score,
                        'embedding_shift': embedding_distance
                    },
                    affected_response_count=len(new_responses)
                ))
                
                return theme
            else:
                logger.debug(f"Theme '{theme.name}' description unchanged")
                return None
                
        except Exception as e:
            logger.error(f"Failed to update theme '{theme.name}': {e}")
            return None
    
    def _calculate_theme_drift(self, theme: Theme, new_responses: List[str]) -> float:
        """Calculate how much new responses differ from the theme."""
        if not theme.embedding or not new_responses:
            return 0.0
        
        # Get embeddings for new responses
        new_embeddings = []
        for response_text in new_responses:
            embedding = self.embedding_service.get_embedding(response_text)
            new_embeddings.append(embedding)
        
        # Calculate average similarity to theme
        similarities = [
            self.embedding_service.cosine_similarity(emb, theme.embedding)
            for emb in new_embeddings
        ]
        
        avg_similarity = sum(similarities) / len(similarities)
        
        # Drift is inverse of similarity (lower similarity = higher drift)
        return 1.0 - avg_similarity
    
    def apply_retroactive_updates(self, affected_responses: List[SurveyResponse], 
                                 theme_changes: List[Dict[str, Any]], batch_id: int) -> None:
        """
        Apply retroactive updates to historical responses.
        
        Args:
            affected_responses: Responses that need updating
            theme_changes: List of theme changes
            batch_id: Current batch ID
        """
        logger.info(f"Applying retroactive updates to {len(affected_responses)} responses")
        
        for response in affected_responses:
            try:
                # Get current assignments
                current_assignments = self.db_manager.get_assignments_by_response(response.id)
                
                for change in theme_changes:
                    if change['action'] == 'merge':
                        self._update_assignments_for_merge(
                            change['old_theme_id'], 
                            change['related_theme_id'], 
                            change['new_theme_id'], 
                            batch_id
                        )
                    elif change['action'] == 'split':
                        self._update_assignments_for_split(
                            change['old_theme_id'],
                            change['new_theme_ids'],
                            response,
                            batch_id
                        )
                    elif change['action'] == 'update':
                        self._update_assignments_for_theme_update(
                            change['theme_id'],
                            response,
                            batch_id
                        )
                        
            except Exception as e:
                logger.error(f"Failed to update response {response.id}: {e}")
                continue
    
    def _update_assignments_for_merge(self, theme1_id: int, theme2_id: int, 
                                     merged_theme_id: int, batch_id: int) -> None:
        """Update assignments when themes are merged."""
        # This would involve updating database records
        # Implementation depends on specific database operations needed
        pass
    
    def _update_assignments_for_split(self, old_theme_id: int, new_theme_ids: List[int], 
                                    response: SurveyResponse, batch_id: int) -> None:
        """Update assignments when a theme is split."""
        # Implementation for handling theme splits
        pass
    
    def _update_assignments_for_theme_update(self, theme_id: int, response: SurveyResponse, 
                                           batch_id: int) -> None:
        """Update assignments when a theme is updated."""
        # Implementation for handling theme updates
        pass
