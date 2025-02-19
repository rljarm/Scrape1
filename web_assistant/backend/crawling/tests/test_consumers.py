"""Tests for the crawling application WebSocket consumers."""
import json
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import re_path
from ..consumers import SelectorConsumer
from ..models import CrawlConfiguration

# CRITICAL: These tests verify WebSocket functionality
# TODO(future): Add more error cases
# CHECK(periodic): Review WebSocket stability

class TestSelectorConsumer(TestCase):
    """Test cases for the SelectorConsumer."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        super().setUpClass()
        
        # Create application
        cls.application = AuthMiddlewareStack(
            URLRouter([
                re_path(
                    r'ws/crawling/selector/(?P<config_id>[^/]+)/$',
                    SelectorConsumer.as_asgi()
                ),
            ])
        )

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.config = CrawlConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            start_url='https://example.com'
        )

    async def test_connect(self):
        """Test WebSocket connection."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        connected, _ = await communicator.connect()
        
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_test_selector(self):
        """Test selector testing functionality."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send test message
        await communicator.send_json_to({
            'action': 'test_selector',
            'selector': '.test-class',
            'url': 'https://example.com'
        })
        
        # Get response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'selector_results')
        self.assertIn('matches', response)
        
        await communicator.disconnect()

    async def test_analyze_page(self):
        """Test page analysis functionality."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send analysis request
        await communicator.send_json_to({
            'action': 'analyze_page',
            'url': 'https://example.com'
        })
        
        # Get response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'page_analysis')
        self.assertIn('analysis', response)
        
        await communicator.disconnect()

    async def test_invalid_action(self):
        """Test handling of invalid actions."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send invalid action
        await communicator.send_json_to({
            'action': 'invalid_action',
            'data': 'test'
        })
        
        # Get error response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['message'], 'Unknown action')
        
        await communicator.disconnect()

    async def test_invalid_json(self):
        """Test handling of invalid JSON."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send invalid JSON
        await communicator.send_to('invalid json')
        
        # Get error response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['message'], 'Invalid JSON data')
        
        await communicator.disconnect()

    async def test_missing_parameters(self):
        """Test handling of missing parameters."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send message without required parameters
        await communicator.send_json_to({
            'action': 'test_selector',
            'selector': '.test-class'
            # Missing 'url' parameter
        })
        
        # Get error response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'error')
        self.assertEqual(response['message'], 'Missing selector or URL')
        
        await communicator.disconnect()

    async def test_pattern_analysis(self):
        """Test pattern analysis in selector results."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send test message
        await communicator.send_json_to({
            'action': 'test_selector',
            'selector': '.test-class',
            'url': 'https://example.com'
        })
        
        # Get response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'selector_results')
        self.assertIn('pattern_analysis', response)
        self.assertIn('page_structure', response['pattern_analysis'])
        self.assertIn('similar_elements', response['pattern_analysis'])
        self.assertIn('confidence', response['pattern_analysis'])
        
        await communicator.disconnect()

    async def test_selector_suggestions(self):
        """Test selector suggestions in results."""
        communicator = WebsocketCommunicator(
            self.application,
            f'/ws/crawling/selector/{self.config.id}/'
        )
        await communicator.connect()
        
        # Send test message
        await communicator.send_json_to({
            'action': 'test_selector',
            'selector': '.test-class',
            'url': 'https://example.com'
        })
        
        # Get response
        response = await communicator.receive_json_from()
        
        self.assertEqual(response['type'], 'selector_results')
        for match in response['matches']:
            self.assertIn('suggested_selectors', match)
            if match['suggested_selectors']:
                suggestion = match['suggested_selectors'][0]
                self.assertIn('selector', suggestion)
                self.assertIn('type', suggestion)
                self.assertIn('description', suggestion)
        
        await communicator.disconnect()
