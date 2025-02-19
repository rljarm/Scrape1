"""URL patterns for the AI app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'models', views.AIModelViewSet)
router.register(r'search-apis', views.SearchAPIViewSet)
router.register(r'tasks', views.ProcessingTaskViewSet)
router.register(r'queries', views.SearchQueryViewSet)
router.register(r'youtube', views.YouTubeDataViewSet)
router.register(r'rules', views.ProcessingRuleViewSet)

websocket_urlpatterns = []  # Will be populated by consumers

urlpatterns = [
    path('', include(router.urls)),
]
