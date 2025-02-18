"""Views for the crawling application."""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from .models import (
    CrawlConfiguration,
    Selector,
    ProxyConfiguration,
    CrawlJob,
    ExtractedData,
)
from .serializers import (
    CrawlConfigurationSerializer,
    DetailedCrawlConfigurationSerializer,
    SelectorSerializer,
    ProxyConfigurationSerializer,
    CrawlJobSerializer,
    DetailedCrawlJobSerializer,
    ExtractedDataSerializer,
)

# CRITICAL: These views handle API endpoints
# TODO(future): Add caching
# CHECK(periodic): Review query performance

class CrawlConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for CrawlConfiguration model."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CrawlConfigurationSerializer
    
    def get_queryset(self):
        """Filter configurations by user."""
        return CrawlConfiguration.objects.filter(
            user=self.request.user
        ).prefetch_related(
            'selector_set',
            'proxy_configuration'
        )

    def get_serializer_class(self):
        """Return different serializer for detailed view."""
        if self.action == 'retrieve':
            return DetailedCrawlConfigurationSerializer
        return self.serializer_class

    @action(detail=True, methods=['post'])
    def test_selectors(self, request, pk=None):
        """Test selectors on a sample page."""
        config = self.get_object()
        url = request.data.get('url')
        
        if not url:
            return Response(
                {'error': 'URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement selector testing logic
        return Response({'status': 'Testing initiated'})

class SelectorViewSet(viewsets.ModelViewSet):
    """ViewSet for Selector model."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SelectorSerializer
    
    def get_queryset(self):
        """Filter selectors by configuration and user."""
        return Selector.objects.filter(
            configuration__user=self.request.user
        )

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a selector on a specific URL."""
        selector = self.get_object()
        url = request.data.get('url')
        
        if not url:
            return Response(
                {'error': 'URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Implement selector testing logic
        return Response({'status': 'Testing initiated'})

class ProxyConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for ProxyConfiguration model."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProxyConfigurationSerializer
    
    def get_queryset(self):
        """Filter proxy configurations by user."""
        return ProxyConfiguration.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test proxy configuration."""
        proxy = self.get_object()
        url = request.data.get('url', 'https://api.ipify.org?format=json')
        
        # TODO: Implement proxy testing logic
        return Response({'status': 'Testing initiated'})

class CrawlJobViewSet(viewsets.ModelViewSet):
    """ViewSet for CrawlJob model."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CrawlJobSerializer
    
    def get_queryset(self):
        """Filter jobs by user."""
        return CrawlJob.objects.filter(
            configuration__user=self.request.user
        ).select_related('configuration')

    def get_serializer_class(self):
        """Return different serializer for detailed view."""
        if self.action == 'retrieve':
            return DetailedCrawlJobSerializer
        return self.serializer_class

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running crawl job."""
        job = self.get_object()
        
        if job.status not in ['pending', 'running']:
            return Response(
                {'error': 'Job cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'cancelled'
        job.save()
        
        # TODO: Implement job cancellation logic
        return Response({'status': 'Job cancelled'})

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get detailed job status."""
        job = self.get_object()
        return Response({
            'status': job.status,
            'pages_crawled': job.pages_crawled,
            'items_scraped': job.items_scraped,
            'average_page_time': job.average_page_time,
            'total_time': job.total_time,
            'error_message': job.error_message
        })

class ExtractedDataViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ExtractedData model (read-only)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExtractedDataSerializer
    
    def get_queryset(self):
        """Filter extracted data by user."""
        return ExtractedData.objects.filter(
            job__configuration__user=self.request.user
        ).select_related(
            'job',
            'selector'
        )

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export extracted data in various formats."""
        job_id = request.query_params.get('job_id')
        format = request.query_params.get('format', 'json')
        
        if not job_id:
            return Response(
                {'error': 'job_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify job belongs to user
        job = get_object_or_404(
            CrawlJob,
            id=job_id,
            configuration__user=request.user
        )
        
        # TODO: Implement export logic for different formats
        return Response({'status': 'Export initiated'})
