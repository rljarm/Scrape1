import scrapy
from scrapy import signals
from typing import Set, Dict, Optional, List
import json
import logging
from urllib.parse import urlparse
import asyncio
from pathlib import Path

from ..proxy_manager import ProxyManager, RotationStrategy
from ..selector_manager import SelectorManager, ElementSelector

class DataSpider(scrapy.Spider):
    name = 'data'
    
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
        self.selector_file = kwargs.get('selector_file')
        self.proxy_file = kwargs.get('proxy_file')
        self.start_urls_file = kwargs.get('urls_file')
        self.output_dir = Path(kwargs.get('output_dir', 'output'))
        self.max_pages = int(kwargs.get('max_pages', 0))
        self.rotation_strategy = RotationStrategy(kwargs.get('rotation_strategy', 'random'))
        
        # Initialize managers
        self.selector_manager = None
        self.proxy_manager = None
        
        # State tracking
        self.processed_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        self.current_domain: Optional[str] = None
        self.selectors: Dict = {}
        self.extracted_data: List[Dict] = []
        self.stats = {
            'pages_processed': 0,
            'items_found': 0,
            'errors': 0
        }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        # Load proxies
        if self.proxy_file:
            with open(self.proxy_file) as f:
                proxies = [line.strip().split(':') for line in f if line.strip()]
                proxy_list = [
                    {
                        'http': f'http://{user}:{pwd}@{ip}:{port}',
                        'https': f'http://{user}:{pwd}@{ip}:{port}'
                    }
                    for ip, port, user, pwd in proxies
                ]
                self.proxy_manager = ProxyManager(proxy_list, self.rotation_strategy)

        # Load selectors if file exists
        if self.selector_file and Path(self.selector_file).exists():
            with open(self.selector_file) as f:
                self.selectors = json.load(f)

        # Initialize selector manager for interactive mode if no selectors
        if not self.selectors:
            self.selector_manager = SelectorManager()
            self.selector_manager.start_browser()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def spider_closed(self, spider):
        if self.selector_manager:
            self.selector_manager.__exit__(None, None, None)
        
        # Save extracted data
        if self.extracted_data:
            output_file = self.output_dir / f"{spider.name}_data.json"
            with open(output_file, 'w') as f:
                json.dump(self.extracted_data, f, indent=2)

    def start_requests(self):
        # Load start URLs
        if not self.start_urls_file or not Path(self.start_urls_file).exists():
            raise ValueError("start_urls_file is required and must exist")

        with open(self.start_urls_file) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('***')]

        # Start with interactive selection if no selectors
        if not self.selectors and urls:
            yield scrapy.Request(
                urls[0],
                callback=self.interactive_selection,
                dont_filter=True,
                meta={'first_url': True}
            )
        else:
            for url in urls:
                yield self.create_request(url)

    def create_request(self, url: str) -> scrapy.Request:
        """Create a request with appropriate proxy and metadata."""
        meta = {'url': url}
        
        if self.proxy_manager:
            domain = urlparse(url).netloc
            proxy_dict, proxy_url = self.proxy_manager.get_proxy(domain)
            meta.update({
                'proxy': proxy_dict['http'],
                'proxy_url': proxy_url,
                'domain': domain
            })

        return scrapy.Request(
            url,
            callback=self.parse_page,
            errback=self.handle_error,
            meta=meta,
            dont_filter=True
        )

    async def interactive_selection(self, response):
        """Handle interactive element selection."""
        if not self.selector_manager:
            return

        # Navigate to page
        success = self.selector_manager.navigate_to_url(
            response.url,
            response.meta.get('proxy')
        )
        if not success:
            return

        # Wait for user to select elements
        self.logger.info("Please select elements in the browser window...")
        self.logger.info("Press Ctrl+C when finished...")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            # Save selectors
            if self.selector_manager.selected_elements:
                self.selectors = {
                    'elements': [
                        {
                            'css_selector': e.css_selector,
                            'xpath_selector': e.xpath_selector,
                            'attributes': e.attributes,
                            'element_type': e.element_type,
                            'name': f"field_{i}"  # Default field names
                        }
                        for i, e in enumerate(self.selector_manager.selected_elements)
                    ],
                    'pagination': self.selector_manager.pagination.__dict__ if self.selector_manager.pagination else None
                }
                
                if self.selector_file:
                    with open(self.selector_file, 'w') as f:
                        json.dump(self.selectors, f, indent=2)

        # Start normal crawling
        yield self.create_request(response.url)

    async def parse_page(self, response):
        """Parse page using selected elements."""
        if not self.selectors:
            return

        # Update domain tracking
        domain = response.meta.get('domain')
        if domain != self.current_domain:
            self.current_domain = domain
            self.discovered_urls.clear()

        # Extract data using selectors
        page_data = {}
        for element in self.selectors['elements']:
            items = response.css(element['css_selector'])
            self.stats['items_found'] += len(items)
            
            # Extract data based on element type
            data = []
            for item in items:
                if element['element_type'] in ['input', 'textarea']:
                    value = item.attrib.get('value', '')
                elif element['element_type'] == 'select':
                    value = item.css('option[selected]::text').get('')
                else:
                    value = item.css('::text').get('').strip()
                
                # Add any specified attributes
                attributes = {
                    attr.split('=')[0]: attr.split('=')[1].strip('"')
                    for attr in element['attributes']
                } if element['attributes'] else {}
                
                if attributes:
                    data.append({'value': value, 'attributes': attributes})
                else:
                    data.append(value)
            
            page_data[element['name']] = data[0] if len(data) == 1 else data

        if page_data:
            page_data['url'] = response.url
            self.extracted_data.append(page_data)

        # Handle pagination
        if self.selectors.get('pagination'):
            pagination = self.selectors['pagination']
            
            # Extract new URLs
            if pagination.get('url_pattern'):
                urls = self.selector_manager.generate_pagination_urls(self.max_pages)
                self.discovered_urls.update(urls)
            
            # Follow next button
            if pagination.get('next_button'):
                next_url = response.css(pagination['next_button']['css_selector']).attrib.get('href')
                if next_url and next_url not in self.processed_urls:
                    self.discovered_urls.add(next_url)

            # Schedule discovered URLs
            for url in self.discovered_urls - self.processed_urls:
                if self.max_pages and self.stats['pages_processed'] >= self.max_pages:
                    break
                yield self.create_request(url)

        self.processed_urls.add(response.url)
        self.stats['pages_processed'] += 1

    async def handle_error(self, failure):
        """Handle request failures."""
        self.stats['errors'] += 1
        
        # Report proxy failure
        if failure.request.meta.get('proxy_url'):
            self.proxy_manager.report_failure(
                failure.request.meta['proxy_url'],
                is_ban='banned' in str(failure.value).lower()
            )

        # Retry with different proxy
        if failure.request.meta.get('retry_count', 0) < 3:
            request = failure.request.copy()
            request.meta['retry_count'] = request.meta.get('retry_count', 0) + 1
            
            if self.proxy_manager:
                proxy_dict, proxy_url = self.proxy_manager.get_proxy(
                    request.meta.get('domain')
                )
                request.meta.update({
                    'proxy': proxy_dict['http'],
                    'proxy_url': proxy_url
                })
            
            yield request
