"""ASGI config for web_assistant project."""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# CRITICAL: This configuration handles both HTTP and WebSocket routing
# TODO(future): Add WebSocket authentication middleware
# CHECK(periodic): Monitor WebSocket connection patterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_assistant.settings')

# Initialize Django ASGI application early to ensure the app is loaded
django_asgi_app = get_asgi_application()

# Import websocket patterns after Django is initialized
from crawling.routing import websocket_urlpatterns as crawling_websocket_urlpatterns
from ai.routing import websocket_urlpatterns as ai_websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's ASGI application
    'http': django_asgi_app,
    
    # WebSocket requests are handled by our custom consumers
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                crawling_websocket_urlpatterns +
                ai_websocket_urlpatterns
            )
        )
    ),
})

# Protocol Documentation:
#
# HTTP:
# - All HTTP requests are handled by Django's standard routing
# - See urls.py for endpoint documentation
#
# WebSocket:
# - Crawling WebSocket routes:
#   ws://server/ws/crawling/selector/<config_id>/
#   Events:
#   - test_selector: Test a selector on a page
#   - analyze_page: Analyze page structure
#
# - AI WebSocket routes:
#   (To be implemented based on AI app requirements)
