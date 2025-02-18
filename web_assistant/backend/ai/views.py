"""Views for the AI app."""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .models import (
    AIModel,
    SearchAPI,
    ProcessingTask,
    SearchQuery,
    YouTubeData,
    ProcessingRule,
)
from .serializers import (
    AIModelSerializer,
    SearchAPISerializer,
    SearchAPICreateSerializer,
    ProcessingTaskSerializer,
    ProcessingTaskCreateSerializer,
    SearchQuerySerializer,
    YouTubeDataSerializer,
    YouTubeDataCreateSerializer,
    ProcessingRuleSerializer,
    AIProcessingStatsSerializer,
    SearchStatsSerializer,
)
from .tasks import (
    process_data,
    perform_search,
    process_youtube_video,
)

class AIModelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI models."""
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'provider', 'model_id']
    ordering_fields = ['name', 'created_at']

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test the AI model with sample data."""
        model = self.get_object()
        # TODO: Implement model testing logic
        return Response({'status': 'test initiated'})

class SearchAPIViewSet(viewsets.ModelViewSet):
    """ViewSet for managing search APIs."""
    queryset = SearchAPI.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'provider']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action in ['create', 'update', 'partial_update']:
            return SearchAPICreateSerializer
        return SearchAPISerializer

    @action(detail=True, methods=['post'])
    def reset_quota(self, request, pk=None):
        """Reset the daily quota counter."""
        api = self.get_object()
        api.requests_made = 0
        api.last_reset = timezone.now().date()
        api.save()
        return Response({'status': 'quota reset'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get search API statistics."""
        stats = {
            'total_queries': SearchQuery.objects.count(),
            'queries_by_api': SearchQuery.objects.values(
                'api__name'
            ).annotate(
                count=Count('id')
            ),
            'average_results_per_query': SearchQuery.objects.filter(
                status='completed'
            ).aggregate(
                avg=Avg('results__len')
            )['avg'] or 0.0,
            'quota_usage': {
                api.name: (api.requests_made / api.daily_quota) * 100
                for api in SearchAPI.objects.all()
            }
        }
        serializer = SearchStatsSerializer(stats)
        return Response(serializer.data)

class ProcessingTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processing tasks."""
    queryset = ProcessingTask.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'status']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return ProcessingTaskCreateSerializer
        return ProcessingTaskSerializer

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed processing task."""
        task = self.get_object()
        if task.status == 'failed':
            task.status = 'pending'
            task.error_message = ''
            task.save()
            process_data.delay(task.id)
            return Response({'status': 'task queued'})
        return Response(
            {'error': 'Only failed tasks can be retried'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get processing statistics."""
        total = ProcessingTask.objects.count()
        completed = ProcessingTask.objects.filter(status='completed').count()
        failed = ProcessingTask.objects.filter(status='failed').count()
        
        stats = {
            'total_tasks': total,
            'completed_tasks': completed,
            'failed_tasks': failed,
            'average_processing_time': ProcessingTask.objects.filter(
                processing_time__isnull=False
            ).aggregate(avg=Avg('processing_time'))['avg'] or 0.0,
            'tasks_by_type': ProcessingTask.objects.values(
                'task_type'
            ).annotate(count=Count('id')),
            'tasks_by_model': ProcessingTask.objects.values(
                'ai_model__name'
            ).annotate(count=Count('id')),
            'success_rate': (completed / total * 100) if total > 0 else 0
        }
        
        serializer = AIProcessingStatsSerializer(stats)
        return Response(serializer.data)

class SearchQueryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing search queries."""
    queryset = SearchQuery.objects.all()
    serializer_class = SearchQuerySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['query']
    ordering_fields = ['created_at']

    def perform_create(self, serializer):
        """Create a new search query and initiate search."""
        query = serializer.save()
        perform_search.delay(query.id)

class YouTubeDataViewSet(viewsets.ModelViewSet):
    """ViewSet for managing YouTube data."""
    queryset = YouTubeData.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'channel']
    ordering_fields = ['published_at', 'created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return YouTubeDataCreateSerializer
        return YouTubeDataSerializer

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process YouTube video data with AI."""
        video = self.get_object()
        if not video.ai_processed:
            process_youtube_video.delay(video.id)
            return Response({'status': 'processing initiated'})
        return Response(
            {'error': 'Video already processed'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ProcessingRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing processing rules."""
    queryset = ProcessingRule.objects.all()
    serializer_class = ProcessingRuleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'content_type']
    ordering_fields = ['priority', 'name']

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply the rule to existing data."""
        rule = self.get_object()
        # TODO: Implement rule application logic
        return Response({'status': 'rule application initiated'})
