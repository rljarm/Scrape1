"""Utility functions for the crawling app."""
import json
import os
from datetime import datetime
from django.conf import settings
from .models import Proxy

def get_proxy_for_session(session):
    """Get an available proxy for the session."""
    return Proxy.objects.filter(
        status='active'
    ).order_by('last_used').first()

def save_to_json(extracted_data, url):
    """Save extracted data to JSON file."""
    # Create output directory if it doesn't exist
    output_dir = os.path.join(settings.BASE_DIR, 'crawled_data')
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename based on timestamp and URL
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_url = url.replace('/', '_').replace(':', '_')[:100]  # Limit length and remove problematic chars
    filename = f"{timestamp}_{safe_url}.json"
    
    # Full path for the JSON file
    json_path = os.path.join(output_dir, filename)
    
    # Save the data
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'url': url,
            'timestamp': timestamp,
            'data': extracted_data
        }, f, indent=2, ensure_ascii=False)
    
    return json_path
