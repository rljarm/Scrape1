"""Tests for the crawling application views."""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from ..models import (
    CrawlConfiguration,
    Selector,
    ProxyConfiguration,
    CrawlJob,
)

# CRITICAL: These tests verify API endpoint functionality
# TODO(future): Add more edge cases
# CHECK(periodic): Review test coverage

class CrawlConfigurationTests(TestCase):
    """Test cases for CrawlConfiguration endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.config_data = {
            'name': 'Test Config',
            'description': 'Test configuration',
            'start_url': 'https://example.com',
            'allowed_domains': ['example.com'],
            'max_depth': 2,
            'max_pages': 100,
            'request_delay': 1.0,
            'timeout': 30,
            'use_playwright': True,
        }

        self.config = CrawlConfiguration.objects.create(
            user=self.user,
            **self.config_data
        )

    def test_create_configuration(self):
        """Test creating a new configuration."""
        url = reverse('crawlconfiguration-list')
        response = self.client.post(url, self.config_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CrawlConfiguration.objects.count(),
            2  # Including the one from setUp
        )
        self.assertEqual(
            response.data['name'],
            self.config_data['name']
        )

    def test_get_configuration_list(self):
        """Test retrieving configuration list."""
        url = reverse('crawlconfiguration-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_configuration_detail(self):
        """Test retrieving configuration detail."""
        url = reverse('crawlconfiguration-detail', args=[self.config.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.config.name)

    def test_update_configuration(self):
        """Test updating a configuration."""
        url = reverse('crawlconfiguration-detail', args=[self.config.id])
        updated_data = {
            **self.config_data,
            'name': 'Updated Config',
            'max_depth': 3
        }
        response = self.client.put(url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.config.refresh_from_db()
        self.assertEqual(self.config.name, 'Updated Config')
        self.assertEqual(self.config.max_depth, 3)

    def test_delete_configuration(self):
        """Test deleting a configuration."""
        url = reverse('crawlconfiguration-detail', args=[self.config.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CrawlConfiguration.objects.count(), 0)

class SelectorTests(TestCase):
    """Test cases for Selector endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.config = CrawlConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            start_url='https://example.com'
        )

        self.selector_data = {
            'configuration': self.config.id,
            'name': 'Test Selector',
            'selector': '.test-class',
            'type': 'css',
            'multiple': False,
            'required': True,
            'extract_text': True
        }

        self.selector = Selector.objects.create(
            configuration=self.config,
            **{k: v for k, v in self.selector_data.items() if k != 'configuration'}
        )

    def test_create_selector(self):
        """Test creating a new selector."""
        url = reverse('selector-list')
        response = self.client.post(url, self.selector_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Selector.objects.count(),
            2  # Including the one from setUp
        )

    def test_test_selector(self):
        """Test the selector testing endpoint."""
        url = reverse('selector-test', args=[self.selector.id])
        test_data = {
            'url': 'https://example.com/test'
        }
        response = self.client.post(url, test_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Testing initiated')

class ProxyConfigurationTests(TestCase):
    """Test cases for ProxyConfiguration endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.proxy_data = {
            'name': 'Test Proxy',
            'host': 'proxy.example.com',
            'port': 8080,
            'protocol': 'http',
            'username': 'proxyuser',
            'password': 'proxypass',
            'enabled': True
        }

        self.proxy = ProxyConfiguration.objects.create(
            user=self.user,
            **self.proxy_data
        )

    def test_create_proxy(self):
        """Test creating a new proxy configuration."""
        url = reverse('proxyconfiguration-list')
        response = self.client.post(url, self.proxy_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ProxyConfiguration.objects.count(),
            2  # Including the one from setUp
        )

    def test_test_proxy(self):
        """Test the proxy testing endpoint."""
        url = reverse('proxyconfiguration-test', args=[self.proxy.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'Testing initiated')

class CrawlJobTests(TestCase):
    """Test cases for CrawlJob endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.config = CrawlConfiguration.objects.create(
            user=self.user,
            name='Test Config',
            start_url='https://example.com'
        )

        self.job_data = {
            'configuration_id': str(self.config.id)
        }

        self.job = CrawlJob.objects.create(
            configuration=self.config,
            status='pending'
        )

    def test_create_job(self):
        """Test creating a new crawl job."""
        url = reverse('crawljob-list')
        response = self.client.post(url, self.job_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            CrawlJob.objects.count(),
            2  # Including the one from setUp
        )

    def test_cancel_job(self):
        """Test cancelling a crawl job."""
        url = reverse('crawljob-cancel', args=[self.job.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'cancelled')

    def test_get_job_status(self):
        """Test getting job status."""
        url = reverse('crawljob-status', args=[self.job.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
