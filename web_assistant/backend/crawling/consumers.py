"""WebSocket consumers for the crawling application."""
import json
import aiohttp
from bs4 import BeautifulSoup
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from playwright.async_api import async_playwright
from .models import CrawlConfiguration
from .utils.selector_analysis import SelectorPattern

# CRITICAL: These consumers handle real-time selector feedback
# TODO(future): Add reconnection handling
# CHECK(periodic): Monitor WebSocket connection stability

class SelectorConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time selector testing and feedback."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Get the configuration ID from the URL route
        self.config_id = self.scope['url_route']['kwargs']['config_id']
        self.room_group_name = f'selector_{self.config_id}'

        # Join the configuration group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the configuration group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'test_selector':
                await self.handle_test_selector(data)
            elif action == 'analyze_page':
                await self.handle_analyze_page(data)
            else:
                await self.send_error('Unknown action')

        except json.JSONDecodeError:
            await self.send_error('Invalid JSON data')
        except Exception as e:
            await self.send_error(str(e))

    async def handle_test_selector(self, data):
        """Test a selector on a page and return matching elements with pattern analysis."""
        selector = data.get('selector')
        url = data.get('url')

        if not selector or not url:
            await self.send_error('Missing selector or URL')
            return

        try:
            # Fetch page content
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()

            # Initialize pattern analyzer
            pattern_analyzer = SelectorPattern(html)
            
            # Launch browser for element testing
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url)

                # Find matching elements
                elements = await page.query_selector_all(selector)
                
                # Extract basic info about matching elements
                matches = []
                for element in elements:
                    tag_name = await element.evaluate('el => el.tagName')
                    inner_text = await element.inner_text()
                    element_html = await element.evaluate('el => el.outerHTML')
                    
                    # Parse element for pattern analysis
                    element_soup = BeautifulSoup(element_html, 'html.parser')
                    suggestions = pattern_analyzer.suggest_selectors(element_soup)
                    
                    matches.append({
                        'tag': tag_name.lower(),
                        'text': inner_text[:100],  # First 100 chars
                        'attributes': await element.evaluate('''el => {
                            const attrs = {};
                            for (const attr of el.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            return attrs;
                        }'''),
                        'suggested_selectors': suggestions
                    })

                await browser.close()

                # Analyze page structure for patterns
                structure_analysis = pattern_analyzer.analyze_page_structure()

                # Send enhanced results back to the client
                await self.send_json({
                    'type': 'selector_results',
                    'selector': selector,
                    'matches': matches,
                    'count': len(matches),
                    'pattern_analysis': {
                        'page_structure': structure_analysis,
                        'similar_elements': len(structure_analysis['recommendations']),
                        'confidence': sum(r['confidence'] for r in structure_analysis['recommendations']) / 
                                    len(structure_analysis['recommendations']) if structure_analysis['recommendations'] else 0
                    }
                })

        except Exception as e:
            await self.send_error(f'Error testing selector: {str(e)}')

    async def handle_analyze_page(self, data):
        """Analyze a page for potential selectable elements."""
        url = data.get('url')
        if not url:
            await self.send_error('Missing URL')
            return

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(url)

                # Analyze page structure
                analysis = await page.evaluate('''() => {
                    const analysis = {
                        links: document.querySelectorAll('a').length,
                        images: document.querySelectorAll('img').length,
                        headings: {
                            h1: document.querySelectorAll('h1').length,
                            h2: document.querySelectorAll('h2').length,
                            h3: document.querySelectorAll('h3').length
                        },
                        lists: {
                            ul: document.querySelectorAll('ul').length,
                            ol: document.querySelectorAll('ol').length
                        },
                        tables: document.querySelectorAll('table').length,
                        forms: document.querySelectorAll('form').length
                    };
                    return analysis;
                }''')

                await browser.close()

                # Send analysis back to the client
                await self.send_json({
                    'type': 'page_analysis',
                    'url': url,
                    'analysis': analysis
                })

        except Exception as e:
            await self.send_error(f'Error analyzing page: {str(e)}')

    async def send_json(self, data):
        """Helper method to send JSON data."""
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message):
        """Helper method to send error messages."""
        await self.send_json({
            'type': 'error',
            'message': message
        })

    async def selector_update(self, event):
        """Handle selector update messages from other consumers."""
        await self.send_json(event)
