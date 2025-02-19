"""Celery tasks for the crawling app."""
import logging
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from playwright.sync_api import sync_playwright
from .models import CrawlSession, ExtractedData, Proxy
from .utils import get_proxy_for_session, save_to_json

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()

@shared_task
def start_crawl_session(session_id):
    """Start a crawling session."""
    try:
        session = CrawlSession.objects.get(id=session_id)
        session.status = 'running'
        session.start_time = timezone.now()
        session.save()

        send_session_update(session)

        # Start crawling each URL
        for url in session.configuration.urls:
            if session.status != 'running':
                break
            
            crawl_url.delay(session_id, url)

    except CrawlSession.DoesNotExist:
        logger.error(f"Session {session_id} not found")
    except Exception as e:
        logger.error(f"Error starting crawl session: {e}")
        update_session_status(session_id, 'failed', error=str(e))

@shared_task
def crawl_url(session_id, url):
    """Crawl a specific URL."""
    try:
        session = CrawlSession.objects.get(id=session_id)
        
        if session.configuration.proxy_enabled:
            proxy = get_proxy_for_session(session)
            if not proxy:
                raise Exception("No available proxies")
        else:
            proxy = None

        with sync_playwright() as p:
            browser_type = p.chromium
            browser_args = {}
            
            if proxy:
                browser_args['proxy'] = {
                    'server': f'{proxy.protocol}://{proxy.host}:{proxy.port}'
                }
                if proxy.username and proxy.password:
                    browser_args['proxy']['username'] = proxy.username
                    browser_args['proxy']['password'] = proxy.password

            browser = browser_type.launch(**browser_args)
            context = browser.new_context()
            page = context.new_page()

            try:
                response = page.goto(url)
                if not response:
                    raise Exception("Failed to load page")

                # Wait for dynamic content
                if session.configuration.extractor_type in ['dynamic', 'hybrid']:
                    page.wait_for_load_state('networkidle')

                # Extract data based on selectors
                extracted_data = {}
                for selector in session.configuration.selector_set.all():
                    try:
                        if selector.css_selector:
                            elements = page.query_selector_all(selector.css_selector)
                        elif selector.xpath_selector:
                            elements = page.query_selector_all(f"xpath={selector.xpath_selector}")
                        else:
                            continue

                        data = []
                        for element in elements:
                            if selector.element_type == 'text':
                                value = element.inner_text()
                            elif selector.element_type == 'link':
                                value = element.get_attribute('href')
                            elif selector.element_type == 'image':
                                value = element.get_attribute('src')
                            else:
                                value = element.inner_text()

                            if selector.attributes:
                                attrs = {}
                                for attr in selector.attributes:
                                    attrs[attr] = element.get_attribute(attr)
                                data.append({'value': value, 'attributes': attrs})
                            else:
                                data.append(value)

                        extracted_data[selector.name] = data[0] if len(data) == 1 else data

                    except Exception as e:
                        logger.error(f"Error extracting {selector.name}: {e}")
                        if selector.required:
                            raise

                # Save extracted data to both database and JSON
                data = ExtractedData.objects.create(
                    session=session,
                    url=url,
                    content_type=response.headers.get('content-type', ''),
                    data=extracted_data
                )
                
                # Save to JSON file
                json_path = save_to_json(extracted_data, url)
                logger.info(f"Saved extracted data to JSON: {json_path}")

                # Update session progress
                session.pages_crawled += 1
                session.save()

                # Send updates
                send_session_update(session)
                send_data_extracted(session_id, data)

                if proxy:
                    update_proxy_stats(proxy.id, success=True)

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                session.pages_failed += 1
                session.save()
                
                if proxy:
                    update_proxy_stats(proxy.id, success=False)
                
                send_error(session_id, f"Error crawling {url}: {str(e)}")

            finally:
                context.close()
                browser.close()

        # Check if all URLs have been processed
        total_pages = session.pages_crawled + session.pages_failed
        if total_pages >= len(session.configuration.urls):
            update_session_status(session_id, 'completed')

    except CrawlSession.DoesNotExist:
        logger.error(f"Session {session_id} not found")
    except Exception as e:
        logger.error(f"Error in crawl_url task: {e}")
        update_session_status(session_id, 'failed', error=str(e))

@shared_task
def update_proxy_stats(proxy_id, success=True):
    """Update proxy statistics."""
    try:
        proxy = Proxy.objects.get(id=proxy_id)
        proxy.last_used = timezone.now()
        
        if success:
            proxy.success_count += 1
            if proxy.status == 'failed':
                proxy.status = 'active'
        else:
            proxy.fail_count += 1
            if proxy.fail_count >= 3:
                proxy.status = 'failed'
        
        proxy.save()

        # Send proxy update
        async_to_sync(channel_layer.group_send)(
            'proxy_updates',
            {
                'type': 'proxy_update',
                'data': {
                    'id': proxy.id,
                    'status': proxy.status,
                    'success_rate': proxy.success_rate,
                }
            }
        )

    except Proxy.DoesNotExist:
        logger.error(f"Proxy {proxy_id} not found")
    except Exception as e:
        logger.error(f"Error updating proxy stats: {e}")

def update_session_status(session_id, status, error=None):
    """Update session status and send update."""
    try:
        session = CrawlSession.objects.get(id=session_id)
        session.status = status
        if status in ['completed', 'failed']:
            session.end_time = timezone.now()
        if error:
            session.error_log['last_error'] = error
        session.save()

        send_session_update(session)

    except CrawlSession.DoesNotExist:
        logger.error(f"Session {session_id} not found")
    except Exception as e:
        logger.error(f"Error updating session status: {e}")

def send_session_update(session):
    """Send session update through WebSocket."""
    async_to_sync(channel_layer.group_send)(
        f'crawl_{session.id}',
        {
            'type': 'crawl_update',
            'data': {
                'id': session.id,
                'status': session.status,
                'pages_crawled': session.pages_crawled,
                'pages_failed': session.pages_failed,
                'start_time': session.start_time.isoformat() if session.start_time else None,
                'end_time': session.end_time.isoformat() if session.end_time else None,
            }
        }
    )

def send_data_extracted(session_id, data):
    """Send extracted data update through WebSocket."""
    async_to_sync(channel_layer.group_send)(
        f'crawl_{session_id}',
        {
            'type': 'data_extracted',
            'data': {
                'id': data.id,
                'url': data.url,
                'content_type': data.content_type,
                'extracted_at': data.extracted_at.isoformat(),
            }
        }
    )

def send_error(session_id, error_message):
    """Send error message through WebSocket."""
    async_to_sync(channel_layer.group_send)(
        f'crawl_{session_id}',
        {
            'type': 'error_occurred',
            'data': {
                'message': error_message,
                'timestamp': timezone.now().isoformat(),
            }
        }
    )
