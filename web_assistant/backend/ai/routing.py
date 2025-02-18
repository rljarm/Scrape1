"""WebSocket URL routing for the AI app."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/ai/task/(?P<task_id>\d+)/$',
        consumers.ProcessingTaskConsumer.as_asgi()
    ),
    re_path(
        r'ws/ai/search/(?P<query_id>\d+)/$',
        consumers.SearchQueryConsumer.as_asgi()
    ),
    re_path(
        r'ws/ai/youtube/(?P<video_id>\d+)/$',
        consumers.YouTubeProcessingConsumer.as_asgi()
    ),
    re_path(
        r'ws/ai/model-status/$',
        consumers.AIModelStatusConsumer.as_asgi()
    ),
]
