"""Serializers for the AI app."""
from rest_framework import serializers
from .models import (
    AIModel,
    SearchAPI,
    ProcessingTask,
    SearchQuery,
    YouTubeData,
    ProcessingRule,
)

class AIModelSerializer(serializers.ModelSerializer):
    """Serializer for AIModel."""
    class Meta:
        model = AIModel
        fields = '__all__'
        extra_kwargs = {
            'config': {'write_only': True}
        }

class SearchAPISerializer(serializers.ModelSerializer):
    """Serializer for SearchAPI."""
    class Meta:
        model = SearchAPI
        fields = [
            'id', 'name', 'provider', 'enabled',
            'daily_quota', 'requests_made', 'last_reset',
        ]
        read_only_fields = ['requests_made', 'last_reset']

class SearchAPICreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating SearchAPI with API key."""
    class Meta:
        model = SearchAPI
        fields = '__all__'

class ProcessingTaskSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingTask."""
    ai_model_name = serializers.CharField(source='ai_model.name', read_only=True)
    
    class Meta:
        model = ProcessingTask
        fields = [
            'id', 'extracted_data', 'ai_model', 'ai_model_name',
            'task_type', 'status', 'output_data', 'error_message',
            'created_at', 'updated_at', 'processing_time',
        ]
        read_only_fields = [
            'status', 'output_data', 'error_message',
            'created_at', 'updated_at', 'processing_time',
        ]

class ProcessingTaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a ProcessingTask."""
    class Meta:
        model = ProcessingTask
        fields = [
            'extracted_data', 'ai_model', 'task_type',
            'input_data',
        ]

class SearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for SearchQuery."""
    api_name = serializers.CharField(source='api.name', read_only=True)

    class Meta:
        model = SearchQuery
        fields = [
            'id', 'query', 'api', 'api_name', 'results',
            'status', 'created_at', 'error_message',
        ]
        read_only_fields = [
            'results', 'status', 'created_at',
            'error_message',
        ]

class YouTubeDataSerializer(serializers.ModelSerializer):
    """Serializer for YouTubeData."""
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = YouTubeData
        fields = [
            'id', 'video_id', 'title', 'channel',
            'published_at', 'duration', 'duration_seconds',
            'metadata', 'ai_processed', 'ai_results',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'duration_seconds', 'metadata', 'ai_processed',
            'ai_results', 'created_at', 'updated_at',
        ]

    def get_duration_seconds(self, obj):
        """Convert duration to seconds."""
        return obj.duration.total_seconds()

class YouTubeDataCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating YouTubeData."""
    class Meta:
        model = YouTubeData
        fields = [
            'video_id', 'title', 'channel', 'published_at',
            'duration', 'transcript', 'metadata',
        ]

class ProcessingRuleSerializer(serializers.ModelSerializer):
    """Serializer for ProcessingRule."""
    ai_model_name = serializers.CharField(source='ai_model.name', read_only=True)

    class Meta:
        model = ProcessingRule
        fields = '__all__'

    def validate_conditions(self, value):
        """Validate the conditions JSON structure."""
        required_fields = ['field', 'operator', 'value']
        valid_operators = ['contains', 'equals', 'startswith', 'endswith', 'regex']

        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Conditions must be a dictionary"
            )

        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"Missing required field: {field}"
                )

        if value['operator'] not in valid_operators:
            raise serializers.ValidationError(
                f"Invalid operator. Must be one of: {', '.join(valid_operators)}"
            )

        return value

class AIProcessingStatsSerializer(serializers.Serializer):
    """Serializer for AI processing statistics."""
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    failed_tasks = serializers.IntegerField()
    average_processing_time = serializers.FloatField()
    tasks_by_type = serializers.DictField()
    tasks_by_model = serializers.DictField()
    success_rate = serializers.FloatField()

class SearchStatsSerializer(serializers.Serializer):
    """Serializer for search statistics."""
    total_queries = serializers.IntegerField()
    queries_by_api = serializers.DictField()
    average_results_per_query = serializers.FloatField()
    quota_usage = serializers.DictField()
