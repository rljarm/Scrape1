"""Models for the AI app."""
from django.db import models
from django.contrib.postgres.fields import JSONField
from crawling.models import ExtractedData

class AIModel(models.Model):
    """Configuration for an AI model."""
    name = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20,
        choices=[
            ('openai', 'OpenAI'),
            ('anthropic', 'Anthropic'),
            ('local', 'Local Model'),
        ]
    )
    model_id = models.CharField(max_length=255)  # e.g., 'gpt-4', 'claude-2'
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=2000)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    config = JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"

class SearchAPI(models.Model):
    """Configuration for a search API."""
    name = models.CharField(max_length=255)
    provider = models.CharField(
        max_length=20,
        choices=[
            ('bing', 'Bing'),
            ('google', 'Google'),
            ('brave', 'Brave'),
        ]
    )
    api_key = models.CharField(max_length=255)
    enabled = models.BooleanField(default=True)
    daily_quota = models.IntegerField(default=1000)
    requests_made = models.IntegerField(default=0)
    last_reset = models.DateField(auto_now_add=True)
    config = JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"

class ProcessingTask(models.Model):
    """AI processing task for extracted data."""
    extracted_data = models.ForeignKey(ExtractedData, on_delete=models.CASCADE)
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    task_type = models.CharField(
        max_length=20,
        choices=[
            ('classification', 'Content Classification'),
            ('summarization', 'Text Summarization'),
            ('extraction', 'Information Extraction'),
            ('translation', 'Translation'),
        ]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    input_data = JSONField()
    output_data = JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_time = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.task_type} for {self.extracted_data}"

class SearchQuery(models.Model):
    """Search query and results."""
    query = models.TextField()
    api = models.ForeignKey(SearchAPI, on_delete=models.SET_NULL, null=True)
    results = JSONField(default=list)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    error_message = models.TextField(blank=True)
    metadata = JSONField(default=dict, blank=True)

    def __str__(self):
        return self.query[:50]

class YouTubeData(models.Model):
    """YouTube video data and processing results."""
    video_id = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    channel = models.CharField(max_length=255)
    published_at = models.DateTimeField()
    duration = models.DurationField()
    transcript = models.TextField(blank=True)
    metadata = JSONField(default=dict)
    ai_processed = models.BooleanField(default=False)
    ai_results = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.video_id})"

class ProcessingRule(models.Model):
    """Rule for automatic AI processing."""
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    conditions = JSONField()  # e.g., {"field": "title", "operator": "contains", "value": "news"}
    task_type = models.CharField(
        max_length=20,
        choices=[
            ('classification', 'Content Classification'),
            ('summarization', 'Text Summarization'),
            ('extraction', 'Information Extraction'),
            ('translation', 'Translation'),
        ]
    )
    ai_model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    enabled = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    config = JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-priority', 'name']
