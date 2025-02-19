"""WebSocket routing configuration for the crawling application."""
from django.urls import re_path
from . import consumers

# CRITICAL: These routes handle WebSocket connections for real-time selector feedback
# TODO(future): Add authentication middleware
# CHECK(periodic): Monitor WebSocket connection patterns

websocket_urlpatterns = [
    # Route format: ws://server/ws/crawling/selector/<config_id>/
    re_path(
        r'ws/crawling/selector/(?P<config_id>\w+)/$',
        consumers.SelectorConsumer.as_asgi()
    ),
]

# WebSocket Event Documentation:
#
# Client -> Server Events:
# {
#     "action": "test_selector",
#     "selector": "css-selector-or-xpath",
#     "url": "http://example.com"
# }
#
# {
#     "action": "analyze_page",
#     "url": "http://example.com"
# }
#
# Server -> Client Events:
# {
#     "type": "selector_results",
#     "selector": "css-selector-or-xpath",
#     "matches": [
#         {
#             "tag": "div",
#             "text": "Element text...",
#             "attributes": {"class": "example", ...}
#         }
#     ],
#     "count": 1
# }
#
# {
#     "type": "page_analysis",
#     "url": "http://example.com",
#     "analysis": {
#         "links": 10,
#         "images": 5,
#         "headings": {"h1": 1, "h2": 3, "h3": 5},
#         "lists": {"ul": 2, "ol": 1},
#         "tables": 1,
#         "forms": 2
#     }
# }
#
# {
#     "type": "error",
#     "message": "Error description"
# }
