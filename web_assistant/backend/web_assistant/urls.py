"""web_assistant URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# CRITICAL: These URLs define the API contract with the frontend
# TODO(future): Add API versioning
# CHECK(periodic): Monitor API usage patterns

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App endpoints
    path('api/crawling/', include('crawling.urls')),
    path('api/ai/', include('ai.urls')),
]

# API Documentation:
#
# Authentication:
# POST /api/token/ - Obtain JWT token pair (username, password)
# POST /api/token/refresh/ - Refresh access token (refresh_token)
#
# Crawling:
# See crawling.urls for detailed endpoint documentation
#
# AI:
# See ai.urls for detailed endpoint documentation

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
