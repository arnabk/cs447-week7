"""
Theme extractor using Ollama/Llama for identifying themes in survey responses.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import requests
import re

from models import Theme, SurveyResponse
from embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ThemeExtractor:
    """Extracts themes from survey responses using Ollama/Llama."""
    
    def __init__(self, config: Dict[str, Any], embedding_service: EmbeddingService):
        self.config = config
        self.embedding_service = embedding_service
        self.ollama_base_url = config['ollama']['base_url']
        self.generation_model = config['ollama']['generation_model']
        self.timeout = config['ollama']['generation_timeout']
        
    def extract_themes_from_batch(self, question: str, responses: List[str], batch_id: int) -> List[Theme]:
        """
        Extract themes from a batch of responses.
        
        Args:
            question: The survey question
            responses: List of response texts
            batch_id: Batch identifier
            
        Returns:
            List of extracted themes
        """
        logger.info(f"Extracting themes for batch {batch_id} with {len(responses)} responses")
        
        # Format responses for the prompt
        formatted_responses = self._format_responses(responses)
        
        # Create the extraction prompt
        prompt = self._create_extraction_prompt(question, formatted_responses)
        
        try:
            # Call Ollama to extract themes
            logger.debug(f"Calling Ollama with model: {self.generation_model}")
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.generation_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        'temperature': 0.3,  # Lower temperature for more consistent results
                        'top_p': 0.9,
                        'num_predict': 2000
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Parse the response
            themes_data = self._parse_theme_response(response_data['response'])
            
            # Create Theme objects with embeddings
            themes = []
            for i, theme_data in enumerate(themes_data):
                try:
                    # Generate embedding for the theme
                    theme_text = f"{theme_data['name']}: {theme_data['description']}"
                    embedding = self.embedding_service.get_embedding(theme_text)
                    
                    theme = Theme(
                        name=theme_data['name'],
                        description=theme_data['description'],
                        embedding=embedding,
                        created_at_batch=batch_id,
                        response_count=0,  # Will be updated later
                        metadata={
                            'extraction_method': 'ollama_llama',
                            'model': self.generation_model,
                            'batch_id': batch_id
                        }
                    )
                    themes.append(theme)
                    
                except Exception as e:
                    logger.error(f"Failed to create theme {i}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(themes)} themes for batch {batch_id}")
            return themes
            
        except Exception as e:
            logger.error(f"Failed to extract themes for batch {batch_id}: {e}")
            raise
    
    def _format_responses(self, responses: List[str]) -> str:
        """Format responses for the prompt."""
        formatted = []
        for i, response in enumerate(responses, 1):
            formatted.append(f"Response {i}: {response}")
        return "\n".join(formatted)
    
    def _create_extraction_prompt(self, question: str, formatted_responses: str) -> str:
        """Create the prompt for theme extraction."""
        return f"""You are analyzing survey responses to identify high-level themes.

Question: {question}

Responses:
{formatted_responses}

Extract 3-5 high-level themes that capture the main patterns in these responses. Each theme should:
1. Represent a distinct concept or concern
2. Be broad enough to encompass multiple responses
3. Be specific enough to be actionable

For each theme provide:
1. A concise name (3-5 words)
2. A detailed description (1-2 sentences explaining what this theme represents)

Output as JSON array:
[
  {{"name": "Theme Name", "description": "Theme description"}},
  {{"name": "Another Theme", "description": "Another description"}}
]

Focus on identifying the core patterns, not just summarizing individual responses. Look for underlying concerns, motivations, or challenges that multiple people are expressing."""
    
    def _parse_theme_response(self, response_text: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from Ollama.
        
        Args:
            response_text: Raw response from Ollama
            
        Returns:
            List of theme dictionaries
        """
        try:
            # Clean up the response text
            cleaned_text = self._clean_json_response(response_text)
            
            # Try to parse as JSON
            themes_data = json.loads(cleaned_text)
            
            if not isinstance(themes_data, list):
                raise ValueError("Response is not a list")
            
            # Validate theme structure
            validated_themes = []
            for theme in themes_data:
                if isinstance(theme, dict) and 'name' in theme and 'description' in theme:
                    validated_themes.append({
                        'name': str(theme['name']).strip(),
                        'description': str(theme['description']).strip()
                    })
                else:
                    logger.warning(f"Invalid theme structure: {theme}")
            
            if not validated_themes:
                raise ValueError("No valid themes found in response")
            
            return validated_themes
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Failed to parse theme response: {e}")
            raise
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean and extract JSON from the response text."""
        # Remove any text before the first [
        start_idx = response_text.find('[')
        if start_idx == -1:
            raise ValueError("No JSON array found in response")
        
        # Find the last ]
        end_idx = response_text.rfind(']')
        if end_idx == -1:
            raise ValueError("No complete JSON array found in response")
        
        # Extract the JSON part
        json_text = response_text[start_idx:end_idx + 1]
        
        # Clean up common issues
        json_text = json_text.replace('\n', ' ').replace('\r', ' ')
        json_text = re.sub(r'\s+', ' ', json_text)  # Replace multiple spaces with single space
        
        return json_text.strip()
    
    def update_theme_description(self, theme: Theme, new_responses: List[str]) -> str:
        """
        Update a theme's description based on new responses.
        
        Args:
            theme: Existing theme
            new_responses: New responses to consider
            
        Returns:
            Updated description
        """
        logger.info(f"Updating description for theme: {theme.name}")
        
        formatted_responses = self._format_responses(new_responses)
        
        prompt = f"""You are updating a theme description based on new survey responses.

Existing Theme:
Name: {theme.name}
Current Description: {theme.description}

New Responses:
{formatted_responses}

Update the theme description to better reflect both the original theme and these new responses. The description should:
1. Maintain the core concept of the original theme
2. Incorporate insights from the new responses
3. Be more comprehensive and accurate
4. Remain concise (1-2 sentences)

Provide only the updated description, no other text."""
        
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.generation_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        'temperature': 0.3,
                        'num_predict': 200
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
            updated_description = response_data['response'].strip()
            
            # Clean up the description
            updated_description = re.sub(r'^["\']|["\']$', '', updated_description)
            updated_description = updated_description.strip()
            
            if not updated_description:
                logger.warning("Empty description returned, keeping original")
                return theme.description
            
            logger.info(f"Updated theme description: {updated_description[:100]}...")
            return updated_description
            
        except Exception as e:
            logger.error(f"Failed to update theme description: {e}")
            return theme.description
    
    def test_connection(self) -> bool:
        """Test connection to Ollama."""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            response.raise_for_status()
            models_data = response.json()
            available_models = [model['name'] for model in models_data['models']]
            
            if self.generation_model not in available_models:
                logger.warning(f"Model {self.generation_model} not found. Available: {available_models}")
                return False
            
            logger.info(f"Ollama connection successful. Available models: {available_models}")
            return True
            
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False
