"""URL patterns for the crawling application."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# CRITICAL: These URLs define the API endpoints
# TODO(future): Add API versioning
# CHECK(periodic): Review URL patterns for consistency

# Create a router and register our viewsets
router = DefaultRouter()
router.register(
    r'configurations',
    views.CrawlConfigurationViewSet,
    basename='crawlconfiguration'
)
router.register(
    r'selectors',
    views.SelectorViewSet,
    basename='selector'
)
router.register(
    r'proxies',
    views.ProxyConfigurationViewSet,
    basename='proxyconfiguration'
)
router.register(
    r'jobs',
    views.CrawlJobViewSet,
    basename='crawljob'
)
router.register(
    r'data',
    views.ExtractedDataViewSet,
    basename='extracteddata'
)

# URL patterns for the crawling application
urlpatterns = [
    # Include the router URLs
    path('', include(router.urls)),
]

# API Documentation:
#
# Configurations:
# GET    /api/crawling/configurations/       - List configurations
# POST   /api/crawling/configurations/       - Create configuration
# GET    /api/crawling/configurations/{id}/  - Get configuration detail
# PUT    /api/crawling/configurations/{id}/  - Update configuration
# DELETE /api/crawling/configurations/{id}/  - Delete configuration
# POST   /api/crawling/configurations/{id}/test_selectors/ - Test selectors
#
# Selectors:
# GET    /api/crawling/selectors/           - List selectors
# POST   /api/crawling/selectors/           - Create selector
# GET    /api/crawling/selectors/{id}/      - Get selector detail
# PUT    /api/crawling/selectors/{id}/      - Update selector
# DELETE /api/crawling/selectors/{id}/      - Delete selector
# POST   /api/crawling/selectors/{id}/test/ - Test selector
#
# Proxies:
# GET    /api/crawling/proxies/             - List proxies
# POST   /api/crawling/proxies/             - Create proxy
# GET    /api/crawling/proxies/{id}/        - Get proxy detail
# PUT    /api/crawling/proxies/{id}/        - Update proxy
# DELETE /api/crawling/proxies/{id}/        - Delete proxy
# POST   /api/crawling/proxies/{id}/test/   - Test proxy
#
# Jobs:
# GET    /api/crawling/jobs/                - List jobs
# POST   /api/crawling/jobs/                - Create job
# GET    /api/crawling/jobs/{id}/           - Get job detail
# PUT    /api/crawling/jobs/{id}/           - Update job
# DELETE /api/crawling/jobs/{id}/           - Delete job
# POST   /api/crawling/jobs/{id}/cancel/    - Cancel job
# GET    /api/crawling/jobs/{id}/status/    - Get job status
#
# Extracted Data:
# GET    /api/crawling/data/                - List extracted data
# GET    /api/crawling/data/{id}/           - Get data detail
# GET    /api/crawling/data/export/         - Export data
