"""Models for the crawling application."""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
import uuid

# CRITICAL: These models define the core data structure
# TODO(future): Add versioning support
# CHECK(periodic): Review index performance

class CrawlConfiguration(models.Model):
    """Configuration for a crawl job."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Base configuration
    start_url = models.URLField(validators=[URLValidator()])
    allowed_domains = models.JSONField(default=list)  # List of domains
    max_depth = models.IntegerField(default=3)
    max_pages = models.IntegerField(default=1000)
    
    # Timing configuration
    request_delay = models.FloatField(default=1.0)  # Seconds between requests
    timeout = models.IntegerField(default=30)  # Seconds
    
    # Browser configuration
    use_playwright = models.BooleanField(default=True)
    wait_for_selector = models.CharField(max_length=255, blank=True)
    wait_for_timeout = models.IntegerField(default=5000)  # Milliseconds
    
    # Proxy configuration
    use_proxy = models.BooleanField(default=False)
    proxy_configuration = models.ForeignKey(
        'ProxyConfiguration',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['name']),
        ]

class Selector(models.Model):
    """Element selector for data extraction."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration = models.ForeignKey(CrawlConfiguration, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    selector = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Selector type and options
    TYPE_CHOICES = [
        ('css', 'CSS Selector'),
        ('xpath', 'XPath'),
        ('regex', 'Regular Expression'),
    ]
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='css')
    multiple = models.BooleanField(default=False)
    required = models.BooleanField(default=False)
    
    # Extraction configuration
    extract_attribute = models.CharField(max_length=50, blank=True)  # e.g., 'href', 'src'
    extract_text = models.BooleanField(default=True)
    post_process = models.JSONField(default=dict)  # Processing steps
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['configuration', 'name']),
            models.Index(fields=['type']),
        ]

class ProxyConfiguration(models.Model):
    """Proxy server configuration."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Proxy details
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    
    # Configuration
    protocol = models.CharField(
        max_length=10,
        choices=[
            ('http', 'HTTP'),
            ('https', 'HTTPS'),
            ('socks4', 'SOCKS4'),
            ('socks5', 'SOCKS5'),
        ],
        default='http'
    )
    enabled = models.BooleanField(default=True)
    
    # Usage limits
    max_requests = models.IntegerField(default=0)  # 0 = unlimited
    requests_made = models.IntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['enabled', 'requests_made']),
        ]

class CrawlJob(models.Model):
    """Instance of a crawl execution."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    configuration = models.ForeignKey(CrawlConfiguration, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Progress tracking
    pages_crawled = models.IntegerField(default=0)
    items_scraped = models.IntegerField(default=0)
    
    # Performance metrics
    average_page_time = models.FloatField(default=0.0)
    total_time = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['configuration', '-started_at']),
            models.Index(fields=['status']),
        ]

class ExtractedData(models.Model):
    """Data extracted during crawling."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(CrawlJob, on_delete=models.CASCADE)
    selector = models.ForeignKey(Selector, on_delete=models.CASCADE)
    url = models.URLField(validators=[URLValidator()])
    extracted_at = models.DateTimeField(auto_now_add=True)
    
    # Extracted content
    content = models.JSONField()  # Structured data
    html_content = models.TextField(blank=True)  # Raw HTML if needed
    
    # Metadata
    page_title = models.CharField(max_length=500, blank=True)
    extraction_time = models.FloatField(default=0.0)  # Time taken to extract
    
    class Meta:
        ordering = ['-extracted_at']
        indexes = [
            models.Index(fields=['job', '-extracted_at']),
            models.Index(fields=['selector', '-extracted_at']),
            models.Index(fields=['url']),
        ]
