"""Utility functions for the AI app."""
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from .models import AIModel, SearchAPI, ProcessingRule

def validate_model_config(config: Dict[str, Any]) -> bool:
    """Validate AI model configuration."""
    required_fields = {
        'openai': ['api_key'],
        'anthropic': ['api_key'],
        'local': ['model_path', 'device'],
    }

    if 'provider' not in config:
        return False

    provider = config['provider']
    if provider not in required_fields:
        return False

    return all(field in config for field in required_fields[provider])

def format_api_response(response: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """Format API response to a standardized structure."""
    if provider == 'openai':
        return {
            'text': response.get('choices', [{}])[0].get('message', {}).get('content', ''),
            'tokens_used': response.get('usage', {}).get('total_tokens', 0),
            'model': response.get('model', ''),
            'timestamp': timezone.now().isoformat(),
        }
    elif provider == 'anthropic':
        return {
            'text': response.get('completion', ''),
            'tokens_used': response.get('usage', {}).get('total_tokens', 0),
            'model': response.get('model', ''),
            'timestamp': timezone.now().isoformat(),
        }
    return response

def check_api_quota(api: SearchAPI) -> bool:
    """Check if API has remaining quota for today."""
    if not api.enabled:
        return False

    # Reset quota if last reset was not today
    today = timezone.now().date()
    if api.last_reset != today:
        api.requests_made = 0
        api.last_reset = today
        api.save()

    return api.requests_made < api.daily_quota

def parse_youtube_duration(duration: str) -> timedelta:
    """Parse YouTube duration string to timedelta."""
    match = re.match(
        r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
        duration
    )
    if not match:
        return timedelta()

    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0

    return timedelta(
        hours=hours,
        minutes=minutes,
        seconds=seconds
    )

def evaluate_processing_rule(
    rule: ProcessingRule,
    content: Dict[str, Any]
) -> bool:
    """Evaluate if content matches processing rule conditions."""
    field = rule.conditions.get('field')
    operator = rule.conditions.get('operator')
    value = rule.conditions.get('value')

    if not all([field, operator, value]):
        return False

    content_value = content.get(field)
    if content_value is None:
        return False

    if operator == 'contains':
        return str(value).lower() in str(content_value).lower()
    elif operator == 'equals':
        return str(content_value).lower() == str(value).lower()
    elif operator == 'startswith':
        return str(content_value).lower().startswith(str(value).lower())
    elif operator == 'endswith':
        return str(content_value).lower().endswith(str(value).lower())
    elif operator == 'regex':
        try:
            return bool(re.search(value, str(content_value)))
        except re.error:
            return False
    return False

def get_available_model(
    task_type: str,
    provider: Optional[str] = None
) -> Optional[AIModel]:
    """Get an available AI model suitable for the task type."""
    query = Q(enabled=True)
    
    if provider:
        query &= Q(provider=provider)

    # Get models sorted by preference for task type
    if task_type == 'classification':
        models = AIModel.objects.filter(
            query
        ).order_by('-max_tokens')
    elif task_type == 'summarization':
        models = AIModel.objects.filter(
            query
        ).order_by('-max_tokens')
    elif task_type == 'extraction':
        models = AIModel.objects.filter(
            query
        ).order_by('temperature')
    elif task_type == 'translation':
        models = AIModel.objects.filter(
            query
        ).order_by('temperature')
    else:
        models = AIModel.objects.filter(query)

    return models.first()

def chunk_content(
    content: str,
    max_tokens: int,
    overlap: int = 100
) -> List[str]:
    """Split content into chunks respecting token limits."""
    # Rough estimate: 1 token ≈ 4 characters
    chunk_size = max_tokens * 4
    overlap_size = overlap * 4
    
    if len(content) <= chunk_size:
        return [content]

    chunks = []
    start = 0
    
    while start < len(content):
        end = start + chunk_size
        
        # If not at the end, try to break at a sentence
        if end < len(content):
            # Look for sentence end within overlap region
            overlap_start = end - overlap_size
            overlap_text = content[overlap_start:end]
            
            # Find last sentence end in overlap region
            sentence_end = -1
            for match in re.finditer(r'[.!?]\s+', overlap_text):
                sentence_end = match.end()
            
            if sentence_end != -1:
                end = overlap_start + sentence_end

        chunks.append(content[start:end].strip())
        start = end - overlap_size if end < len(content) else end

    return chunks

def format_error_message(error: Exception) -> str:
    """Format error message for consistent error reporting."""
    if hasattr(error, 'response'):
        try:
            response = error.response.json()
            return response.get('error', {}).get('message', str(error))
        except (ValueError, AttributeError):
            return str(error)
    return str(error)

def sanitize_model_input(text: str) -> str:
    """Sanitize text input for AI models."""
    # Remove null characters
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Remove control characters except newlines and tabs
    text = ''.join(
        char for char in text
        if char == '\n' or char == '\t' or (ord(char) >= 32 and ord(char) != 127)
    )
    
    return text.strip()
