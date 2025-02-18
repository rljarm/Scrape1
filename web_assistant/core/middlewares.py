from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import time

class ImageScraperSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

class ImageScraperDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

class CustomRetryMiddleware(RetryMiddleware):
    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            # Check if using proxy and mark it for break if needed
            proxy = request.meta.get('proxy')
            if proxy and hasattr(spider, 'proxy_manager'):
                base_url = request.meta.get('base_url')
                if base_url in spider.base_proxy_map:
                    spider.proxy_manager.mark_break(spider.base_proxy_map[base_url])
            
            time.sleep(2)  # Add delay before retry
            return self._retry(request, reason, spider) or response
        
        return response

    def process_exception(self, request, exception, spider):
        # Handle proxy failures
        if request.meta.get('proxy'):
            base_url = request.meta.get('base_url')
            if base_url in spider.base_proxy_map:
                spider.proxy_manager.mark_break(spider.base_proxy_map[base_url])
        
        return super().process_exception(request, exception, spider)
