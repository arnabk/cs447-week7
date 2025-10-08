"""
HDBSCAN clustering implementation for news articles
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.metrics import silhouette_score, adjusted_rand_score
import hdbscan
import logging

logger = logging.getLogger(__name__)

class HDBSCANClusterer:
    """
    HDBSCAN-based clustering for news articles
    """
    
    def __init__(self, 
                 min_cluster_size: int = 5,
                 min_samples: int = 3,
                 metric: str = 'euclidean',
                 cluster_selection_epsilon: float = 0.0):
        """
        Initialize HDBSCAN clusterer
        
        Args:
            min_cluster_size: Minimum size of clusters
            min_samples: Minimum number of samples in a neighborhood
            metric: Distance metric to use
            cluster_selection_epsilon: Distance threshold for cluster selection
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.metric = metric
        self.cluster_selection_epsilon = cluster_selection_epsilon
        
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric=metric,
            cluster_selection_epsilon=cluster_selection_epsilon
        )
        
        self.is_fitted = False
        self.labels_ = None
        self.cluster_persistence_ = None
        
    def fit(self, embeddings: np.ndarray) -> 'HDBSCANClusterer':
        """
        Fit the clusterer to the data
        
        Args:
            embeddings: Article embeddings array
            
        Returns:
            Self
        """
        logger.info(f"Fitting HDBSCAN with {len(embeddings)} articles")
        
        self.clusterer.fit(embeddings)
        self.labels_ = self.clusterer.labels_
        self.cluster_persistence_ = self.clusterer.cluster_persistence_
        self.is_fitted = True
        
        n_clusters = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        n_noise = list(self.labels_).count(-1)
        
        logger.info(f"Found {n_clusters} clusters and {n_noise} noise points")
        
        return self
    
    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Predict cluster labels for new data
        
        Args:
            embeddings: New article embeddings
            
        Returns:
            Cluster labels
        """
        if not self.is_fitted:
            raise ValueError("Clusterer must be fitted before prediction")
        
        return self.clusterer.fit_predict(embeddings)
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about the clusters
        
        Returns:
            Dictionary with cluster information
        """
        if not self.is_fitted:
            raise ValueError("Clusterer must be fitted before getting cluster info")
        
        unique_labels = set(self.labels_)
        cluster_info = {}
        
        for label in unique_labels:
            if label == -1:  # Noise points
                continue
                
            cluster_mask = self.labels_ == label
            cluster_size = np.sum(cluster_mask)
            
            cluster_info[label] = {
                'size': cluster_size,
                'persistence': self.cluster_persistence_[label] if label in self.cluster_persistence_ else 0.0
            }
        
        return cluster_info
    
    def evaluate_clustering(self, embeddings: np.ndarray, true_labels: np.ndarray = None) -> Dict[str, float]:
        """
        Evaluate clustering quality
        
        Args:
            embeddings: Article embeddings
            true_labels: True cluster labels (optional)
            
        Returns:
            Dictionary with evaluation metrics
        """
        if not self.is_fitted:
            raise ValueError("Clusterer must be fitted before evaluation")
        
        metrics = {}
        
        # Silhouette score
        if len(set(self.labels_)) > 1:
            metrics['silhouette_score'] = silhouette_score(embeddings, self.labels_)
        else:
            metrics['silhouette_score'] = 0.0
        
        # Adjusted Rand Index (if true labels provided)
        if true_labels is not None:
            metrics['adjusted_rand_index'] = adjusted_rand_score(true_labels, self.labels_)
        
        # Number of clusters
        n_clusters = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        metrics['n_clusters'] = n_clusters
        
        # Number of noise points
        n_noise = list(self.labels_).count(-1)
        metrics['n_noise'] = n_noise
        metrics['noise_ratio'] = n_noise / len(self.labels_)
        
        return metrics
    
    def get_cluster_centers(self, embeddings: np.ndarray) -> Dict[int, np.ndarray]:
        """
        Get cluster centers (mean of embeddings in each cluster)
        
        Args:
            embeddings: Article embeddings
            
        Returns:
            Dictionary mapping cluster_id to center coordinates
        """
        if not self.is_fitted:
            raise ValueError("Clusterer must be fitted before getting cluster centers")
        
        cluster_centers = {}
        unique_labels = set(self.labels_)
        
        for label in unique_labels:
            if label == -1:  # Skip noise points
                continue
                
            cluster_mask = self.labels_ == label
            cluster_embeddings = embeddings[cluster_mask]
            center = np.mean(cluster_embeddings, axis=0)
            cluster_centers[label] = center
        
        return cluster_centers
    
    def get_outliers(self) -> List[int]:
        """
        Get indices of outlier/noise points
        
        Returns:
            List of indices for outlier points
        """
        if not self.is_fitted:
            raise ValueError("Clusterer must be fitted before getting outliers")
        
        return [i for i, label in enumerate(self.labels_) if label == -1]
    
    def update_parameters(self, **kwargs):
        """
        Update clustering parameters
        
        Args:
            **kwargs: New parameter values
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Recreate clusterer with new parameters
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            cluster_selection_epsilon=self.cluster_selection_epsilon
        )
        
        self.is_fitted = False
        self.labels_ = None
        self.cluster_persistence_ = None
