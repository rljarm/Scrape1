"""Serializers for the crawling application."""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    CrawlConfiguration,
    Selector,
    ProxyConfiguration,
    CrawlJob,
    ExtractedData,
)

# CRITICAL: These serializers handle API data validation
# TODO(future): Add custom validation methods
# CHECK(periodic): Review serialization performance

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']

class ProxyConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for ProxyConfiguration model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProxyConfiguration
        fields = [
            'id', 'name', 'description', 'created_at', 'updated_at',
            'user', 'host', 'port', 'username', 'password', 'protocol',
            'enabled', 'max_requests', 'requests_made', 'last_used'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'requests_made', 'last_used']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """Create a new proxy configuration."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class SelectorSerializer(serializers.ModelSerializer):
    """Serializer for Selector model."""
    class Meta:
        model = Selector
        fields = [
            'id', 'configuration', 'name', 'selector', 'description',
            'created_at', 'updated_at', 'type', 'multiple', 'required',
            'extract_attribute', 'extract_text', 'post_process'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CrawlConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for CrawlConfiguration model."""
    user = UserSerializer(read_only=True)
    selectors = SelectorSerializer(many=True, read_only=True, source='selector_set')
    proxy_configuration = ProxyConfigurationSerializer(read_only=True)
    proxy_configuration_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = CrawlConfiguration
        fields = [
            'id', 'name', 'description', 'created_at', 'updated_at',
            'user', 'start_url', 'allowed_domains', 'max_depth',
            'max_pages', 'request_delay', 'timeout', 'use_playwright',
            'wait_for_selector', 'wait_for_timeout', 'use_proxy',
            'proxy_configuration', 'proxy_configuration_id', 'selectors'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create a new crawl configuration."""
        proxy_id = validated_data.pop('proxy_configuration_id', None)
        validated_data['user'] = self.context['request'].user
        
        if proxy_id:
            try:
                proxy = ProxyConfiguration.objects.get(id=proxy_id)
                validated_data['proxy_configuration'] = proxy
            except ProxyConfiguration.DoesNotExist:
                raise serializers.ValidationError(
                    {'proxy_configuration_id': 'Invalid proxy configuration ID'}
                )
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a crawl configuration."""
        proxy_id = validated_data.pop('proxy_configuration_id', None)
        
        if proxy_id:
            try:
                proxy = ProxyConfiguration.objects.get(id=proxy_id)
                validated_data['proxy_configuration'] = proxy
            except ProxyConfiguration.DoesNotExist:
                raise serializers.ValidationError(
                    {'proxy_configuration_id': 'Invalid proxy configuration ID'}
                )
        
        return super().update(instance, validated_data)

class CrawlJobSerializer(serializers.ModelSerializer):
    """Serializer for CrawlJob model."""
    configuration = CrawlConfigurationSerializer(read_only=True)
    configuration_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = CrawlJob
        fields = [
            'id', 'configuration', 'configuration_id', 'started_at',
            'completed_at', 'status', 'error_message', 'pages_crawled',
            'items_scraped', 'average_page_time', 'total_time'
        ]
        read_only_fields = [
            'id', 'started_at', 'completed_at', 'status', 'error_message',
            'pages_crawled', 'items_scraped', 'average_page_time', 'total_time'
        ]

    def create(self, validated_data):
        """Create a new crawl job."""
        config_id = validated_data.pop('configuration_id')
        try:
            config = CrawlConfiguration.objects.get(id=config_id)
            validated_data['configuration'] = config
        except CrawlConfiguration.DoesNotExist:
            raise serializers.ValidationError(
                {'configuration_id': 'Invalid configuration ID'}
            )
        
        return super().create(validated_data)

class ExtractedDataSerializer(serializers.ModelSerializer):
    """Serializer for ExtractedData model."""
    job = CrawlJobSerializer(read_only=True)
    selector = SelectorSerializer(read_only=True)
    
    class Meta:
        model = ExtractedData
        fields = [
            'id', 'job', 'selector', 'url', 'extracted_at', 'content',
            'html_content', 'page_title', 'extraction_time'
        ]
        read_only_fields = [
            'id', 'extracted_at', 'extraction_time'
        ]

# Nested serializers for detailed views
class DetailedCrawlConfigurationSerializer(CrawlConfigurationSerializer):
    """Detailed serializer for CrawlConfiguration with related data."""
    jobs = CrawlJobSerializer(many=True, read_only=True, source='crawljob_set')
    
    class Meta(CrawlConfigurationSerializer.Meta):
        fields = CrawlConfigurationSerializer.Meta.fields + ['jobs']

class DetailedCrawlJobSerializer(CrawlJobSerializer):
    """Detailed serializer for CrawlJob with extracted data."""
    extracted_data = ExtractedDataSerializer(
        many=True,
        read_only=True,
        source='extracteddata_set'
    )
    
    class Meta(CrawlJobSerializer.Meta):
        fields = CrawlJobSerializer.Meta.fields + ['extracted_data']
