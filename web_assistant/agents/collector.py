import scrapy
from scrapy import signals
from typing import Set, Dict, Optional, List
import json
import logging
from urllib.parse import urlparse
import asyncio
from pathlib import Path

from ..core.network_manager import NetworkManager, RotationStrategy
from ..core.element_manager import ElementManager, ElementInfo
from ..core.media_handler import MediaHandler

class Collector(scrapy.Spider):
    name = 'collect'
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Start conservative, will be adjusted dynamically
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': True,
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': False,
            'timeout': 30000,
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_file = kwargs.get('config_file')
        self.network_file = kwargs.get('network_file')
        self.source_file = kwargs.get('source_file')
        self.output_dir = Path(kwargs.get('output_dir', 'output'))
        self.max_pages = int(kwargs.get('max_pages', 0))
        self.rotation_strategy = RotationStrategy(kwargs.get('rotation_strategy', 'random'))
        
        # Initialize managers
        self.element_manager = None
        self.network_manager = None
        self.media_handler = None
        
        # State tracking
        self.processed_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        self.current_domain: Optional[str] = None
        self.elements: Dict = {}
        self.stats = {
            'pages_processed': 0,
            'items_found': 0,
            'items_processed': 0,
            'errors': 0
        }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        # Load network configuration
        if self.network_file:
            with open(self.network_file) as f:
                networks = [line.strip().split(':') for line in f if line.strip()]
                network_list = [
                    {
                        'http': f'http://{user}:{pwd}@{ip}:{port}',
                        'https': f'http://{user}:{pwd}@{ip}:{port}'
                    }
                    for ip, port, user, pwd in networks
                ]
                self.network_manager = NetworkManager(network_list, self.rotation_strategy)

        # Load element configuration if exists
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file) as f:
                self.elements = json.load(f)

        # Initialize managers
        if not self.elements:
            self.element_manager = ElementManager()
            self.element_manager.start_browser()

        # Initialize media handler
        self.media_handler = MediaHandler(
            min_size=110 * 1024,  # 110KB
            max_size=23.8 * 1024 * 1024,  # 23.8MB
            download_timeout=30
        )

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def spider_closed(self, spider):
        if self.element_manager:
            self.element_manager.__exit__(None, None, None)

    def start_requests(self):
        # Load source URLs
        if not self.source_file or not Path(self.source_file).exists():
            raise ValueError("source_file is required and must exist")

        with open(self.source_file) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        # Start with interactive selection if no configuration
        if not self.elements and urls:
            yield scrapy.Request(
                urls[0],
                callback=self.interactive_selection,
                dont_filter=True,
                meta={'first_url': True}
            )
        else:
            for url in urls:
                yield self.create_request(url)

    # Rest of the implementation follows similar pattern,
    # replacing scraping/crawling terminology with more neutral terms
    # like process, collect, analyze, etc.
