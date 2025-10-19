"""
Keyword highlighter using similarity-based approach to identify contributing words/phrases.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Set
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

from models import HighlightedKeyword
from embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KeywordHighlighter:
    """Highlights keywords that contribute to theme assignment using similarity-based approach."""
    
    def __init__(self, config: Dict[str, Any], embedding_service: EmbeddingService):
        self.config = config
        self.embedding_service = embedding_service
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        # Load stop words
        self.stop_words = set(stopwords.words('english'))
        # Keep some important words that are often filtered out
        self.stop_words -= {
            'not', 'no', 'but', 'however', 'very', 'too', 'more', 'less',
            'only', 'just', 'also', 'well', 'much', 'many', 'most', 'all'
        }
        
        # Configuration
        self.ngram_config = config['ngrams']
        self.contribution_threshold = config['thresholds']['keyword_contribution']
        self.max_keywords = config['processing']['max_keywords_per_response']
    
    def highlight_keywords(self, response_text: str, theme_embedding: List[float]) -> List[HighlightedKeyword]:
        """
        Highlight keywords that contribute to theme assignment.
        
        Args:
            response_text: Text of the response
            theme_embedding: Embedding of the theme
            
        Returns:
            List of highlighted keywords with scores
        """
        if not response_text.strip():
            return []
        
        logger.debug(f"Highlighting keywords for text: {response_text[:50]}...")
        
        # Extract phrases (n-grams)
        phrases = self._extract_phrases(response_text)
        
        if not phrases:
            return []
        
        # Get base embedding for the full response
        base_embedding = self.embedding_service.get_embedding(response_text)
        base_similarity = self.embedding_service.cosine_similarity(base_embedding, theme_embedding)
        
        # Calculate contribution for each phrase
        contributions = []
        for phrase in phrases:
            try:
                contribution_score = self._calculate_contribution(
                    response_text, phrase, base_embedding, theme_embedding, base_similarity
                )
                
                if contribution_score > self.contribution_threshold:
                    # Find positions of the phrase in the text
                    positions = self._find_phrase_positions(response_text, phrase)
                    
                    contributions.append(HighlightedKeyword(
                        keyword=phrase,
                        score=contribution_score,
                        positions=positions
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to calculate contribution for phrase '{phrase}': {e}")
                continue
        
        # Sort by contribution score and limit results
        contributions.sort(key=lambda x: x.score, reverse=True)
        return contributions[:self.max_keywords]
    
    def _extract_phrases(self, text: str) -> List[str]:
        """
        Extract n-grams (unigrams, bigrams, trigrams) from text.
        
        Args:
            text: Input text
            
        Returns:
            List of phrases
        """
        # Tokenize and clean
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalnum()]  # Remove punctuation
        
        phrases = []
        
        # Unigrams (single words)
        if self.ngram_config['use_unigrams']:
            unigrams = [
                w for w in words 
                if w not in self.stop_words 
                and len(w) >= self.ngram_config['min_word_length']
            ]
            phrases.extend(unigrams)
        
        # Bigrams (2-word phrases)
        if self.ngram_config['use_bigrams']:
            bigrams = []
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                # Skip if both words are stop words
                if not (words[i] in self.stop_words and words[i+1] in self.stop_words):
                    bigrams.append(bigram)
            phrases.extend(bigrams)
        
        # Trigrams (3-word phrases)
        if self.ngram_config['use_trigrams']:
            trigrams = []
            for i in range(len(words) - 2):
                trigram_words = words[i:i+3]
                # Only include if max 1 stop word
                stop_word_count = sum(1 for w in trigram_words if w in self.stop_words)
                if stop_word_count <= self.ngram_config['max_stopwords_in_phrase']:
                    trigram = f"{trigram_words[0]} {trigram_words[1]} {trigram_words[2]}"
                    trigrams.append(trigram)
            phrases.extend(trigrams)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_phrases = []
        for phrase in phrases:
            if phrase not in seen:
                seen.add(phrase)
                unique_phrases.append(phrase)
        
        return unique_phrases
    
    def _calculate_contribution(self, text: str, phrase: str, base_embedding: List[float], 
                               theme_embedding: List[float], base_similarity: float) -> float:
        """
        Calculate how much a phrase contributes to theme similarity.
        
        Args:
            text: Original text
            phrase: Phrase to test
            base_embedding: Embedding of full text
            theme_embedding: Theme embedding
            base_similarity: Similarity between full text and theme
            
        Returns:
            Contribution score
        """
        try:
            # Remove the phrase from the text
            modified_text = self._remove_phrase_from_text(text, phrase)
            
            if not modified_text.strip():
                # If removing the phrase leaves empty text, it's very important
                return 1.0
            
            # Get embedding of modified text
            modified_embedding = self.embedding_service.get_embedding(modified_text)
            modified_similarity = self.embedding_service.cosine_similarity(modified_embedding, theme_embedding)
            
            # Contribution is the difference in similarity
            contribution = base_similarity - modified_similarity
            
            # Ensure non-negative contribution
            return max(0.0, contribution)
            
        except Exception as e:
            logger.warning(f"Failed to calculate contribution for '{phrase}': {e}")
            return 0.0
    
    def _remove_phrase_from_text(self, text: str, phrase: str) -> str:
        """
        Remove a phrase from text, handling word boundaries.
        
        Args:
            text: Original text
            phrase: Phrase to remove
            
        Returns:
            Text with phrase removed
        """
        # Use word boundary regex to avoid partial matches
        pattern = r'\b' + re.escape(phrase) + r'\b'
        modified_text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        modified_text = re.sub(r'\s+', ' ', modified_text).strip()
        
        return modified_text
    
    def _find_phrase_positions(self, text: str, phrase: str) -> List[int]:
        """
        Find all positions where a phrase appears in text.
        
        Args:
            text: Text to search in
            phrase: Phrase to find
            
        Returns:
            List of start positions
        """
        positions = []
        start = 0
        
        while True:
            pos = text.lower().find(phrase.lower(), start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        return positions
    
    def batch_highlight_keywords(self, responses: List[str], theme_embeddings: List[List[float]]) -> List[List[HighlightedKeyword]]:
        """
        Highlight keywords for multiple responses and themes in batch.
        
        Args:
            responses: List of response texts
            theme_embeddings: List of theme embeddings
            
        Returns:
            List of highlighted keywords for each response
        """
        results = []
        
        for i, response in enumerate(responses):
            response_keywords = []
            
            for theme_embedding in theme_embeddings:
                keywords = self.highlight_keywords(response, theme_embedding)
                response_keywords.extend(keywords)
            
            # Remove duplicates and sort by score
            unique_keywords = {}
            for kw in response_keywords:
                if kw.keyword not in unique_keywords or kw.score > unique_keywords[kw.keyword].score:
                    unique_keywords[kw.keyword] = kw
            
            sorted_keywords = sorted(unique_keywords.values(), key=lambda x: x.score, reverse=True)
            results.append(sorted_keywords[:self.max_keywords])
        
        return results
    
    def get_phrase_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get statistics about phrases in text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with phrase statistics
        """
        phrases = self._extract_phrases(text)
        
        return {
            'total_phrases': len(phrases),
            'unigrams': len([p for p in phrases if ' ' not in p]),
            'bigrams': len([p for p in phrases if p.count(' ') == 1]),
            'trigrams': len([p for p in phrases if p.count(' ') == 2]),
            'unique_phrases': len(set(phrases)),
            'avg_phrase_length': sum(len(p.split()) for p in phrases) / len(phrases) if phrases else 0
        }
