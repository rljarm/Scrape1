from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import re
from playwright.sync_api import sync_playwright, Page, Browser
import json
import logging
from bs4 import BeautifulSoup

@dataclass
class ElementSelector:
    css_selector: str
    xpath_selector: str
    attributes: List[str]
    inner_text: Optional[str]
    element_type: str
    parent_selector: Optional[str] = None
    children_selectors: List[str] = None

@dataclass
class PaginationInfo:
    next_button: Optional[ElementSelector] = None
    page_numbers: Optional[ElementSelector] = None
    last_page: Optional[str] = None
    current_page: Optional[str] = None
    url_pattern: Optional[str] = None
    discovered_urls: Set[str] = None

class SelectorManager:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.selected_elements: List[ElementSelector] = []
        self.pagination: Optional[PaginationInfo] = None
        self.base_url: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        self.playwright.stop()

    def start_browser(self) -> None:
        """Initialize browser with proxy support."""
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    def navigate_to_url(self, url: str, proxy: Optional[Dict[str, str]] = None) -> bool:
        """Navigate to URL and wait for page load."""
        try:
            self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            if proxy:
                context = self.browser.new_context(
                    proxy={
                        "server": proxy["http"],
                        "username": proxy.get("username"),
                        "password": proxy.get("password"),
                    }
                )
                self.page = context.new_page()
            
            self.page.goto(url, wait_until="networkidle")
            return True
        except Exception as e:
            logging.error(f"Navigation failed: {e}")
            return False

    def get_element_selector(self, x: int, y: int) -> Optional[ElementSelector]:
        """Get element information from click coordinates."""
        try:
            element = self.page.evaluate(f"""() => {{
                const element = document.elementFromPoint({x}, {y});
                if (!element) return null;
                
                function getOptimalSelector(el) {{
                    // Try ID
                    if (el.id) return `#${{el.id}}`;
                    
                    // Try unique class combination
                    if (el.classList.length) {{
                        const classSelector = '.' + Array.from(el.classList).join('.');
                        if (document.querySelectorAll(classSelector).length === 1)
                            return classSelector;
                    }}
                    
                    // Try nth-child with parent
                    const parent = el.parentElement;
                    if (parent) {{
                        const children = Array.from(parent.children);
                        const index = children.indexOf(el);
                        return `${{getOptimalSelector(parent)}} > :nth-child(${{index + 1}})`;
                    }}
                    
                    return null;
                }}
                
                const selector = getOptimalSelector(element);
                return {{
                    cssSelector: selector,
                    xpath: getXPath(element),
                    attributes: Array.from(element.attributes).map(attr => 
                        `${{attr.name}}="${{attr.value}}"`),
                    innerText: element.innerText,
                    elementType: element.tagName.toLowerCase()
                }};
            }}""")
            
            if not element:
                return None
                
            return ElementSelector(
                css_selector=element["cssSelector"],
                xpath_selector=element["xpath"],
                attributes=element["attributes"],
                inner_text=element["innerText"],
                element_type=element["elementType"]
            )
        except Exception as e:
            logging.error(f"Error getting element selector: {e}")
            return None

    def detect_grid_pattern(self, element: ElementSelector) -> List[ElementSelector]:
        """Detect grid pattern from selected element."""
        try:
            similar_elements = self.page.evaluate(f"""(selector) => {{
                const element = document.querySelector(selector);
                if (!element) return [];
                
                const parent = element.parentElement;
                const siblings = Array.from(parent.children);
                
                // Check if elements have similar structure
                const pattern = siblings.filter(el => 
                    el.tagName === element.tagName &&
                    el.classList.length === element.classList.length &&
                    Array.from(el.classList).some(c => 
                        element.classList.contains(c))
                );
                
                return pattern.map(el => ({{
                    cssSelector: getOptimalSelector(el),
                    xpath: getXPath(el),
                    attributes: Array.from(el.attributes).map(attr => 
                        `${{attr.name}}="${{attr.value}}"`),
                    innerText: el.innerText,
                    elementType: el.tagName.toLowerCase()
                }}));
            }}""", element.css_selector)
            
            return [ElementSelector(**e) for e in similar_elements]
        except Exception as e:
            logging.error(f"Error detecting grid pattern: {e}")
            return []

    def detect_pagination(self) -> Optional[PaginationInfo]:
        """Detect pagination elements and patterns."""
        try:
            pagination_data = self.page.evaluate("""() => {
                // Common pagination selectors
                const patterns = {
                    nextButton: [
                        'a[rel="next"]',
                        '.pagination .next',
                        '.next-page',
                        '[aria-label="Next page"]'
                    ],
                    pageNumbers: [
                        '.pagination a',
                        '.page-numbers',
                        '[aria-label*="Page"]'
                    ]
                };
                
                let nextButton = null;
                let pageNumbers = [];
                let lastPage = null;
                let currentPage = null;
                
                // Find next button
                for (const selector of patterns.nextButton) {
                    const element = document.querySelector(selector);
                    if (element) {
                        nextButton = {
                            cssSelector: selector,
                            xpath: getXPath(element),
                            attributes: Array.from(element.attributes).map(attr => 
                                `${attr.name}="${attr.value}"`),
                            innerText: element.innerText,
                            elementType: element.tagName.toLowerCase()
                        };
                        break;
                    }
                }
                
                // Find page numbers
                for (const selector of patterns.pageNumbers) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        pageNumbers = Array.from(elements).map(el => ({
                            cssSelector: getOptimalSelector(el),
                            xpath: getXPath(el),
                            attributes: Array.from(el.attributes).map(attr => 
                                `${attr.name}="${attr.value}"`),
                            innerText: el.innerText,
                            elementType: el.tagName.toLowerCase()
                        }));
                        
                        // Try to find last page number
                        const numbers = Array.from(elements)
                            .map(el => parseInt(el.innerText))
                            .filter(n => !isNaN(n));
                        if (numbers.length > 0) {
                            lastPage = Math.max(...numbers).toString();
                        }
                        
                        // Try to find current page
                        const current = Array.from(elements)
                            .find(el => el.classList.contains('current') ||
                                      el.getAttribute('aria-current') === 'page');
                        if (current) {
                            currentPage = current.innerText;
                        }
                        
                        break;
                    }
                }
                
                return {
                    nextButton,
                    pageNumbers: pageNumbers.length > 0 ? pageNumbers[0] : null,
                    lastPage,
                    currentPage
                };
            }""")
            
            if not pagination_data:
                return None
                
            return PaginationInfo(
                next_button=ElementSelector(**pagination_data["nextButton"]) if pagination_data["nextButton"] else None,
                page_numbers=ElementSelector(**pagination_data["pageNumbers"]) if pagination_data["pageNumbers"] else None,
                last_page=pagination_data["lastPage"],
                current_page=pagination_data["currentPage"],
                discovered_urls=set()
            )
        except Exception as e:
            logging.error(f"Error detecting pagination: {e}")
            return None

    def extract_pagination_urls(self) -> Set[str]:
        """Extract all pagination URLs from current page."""
        if not self.pagination:
            self.pagination = self.detect_pagination()
            if not self.pagination:
                return set()

        try:
            # Extract URLs from page numbers
            if self.pagination.page_numbers:
                urls = self.page.evaluate(f"""(selector) => {{
                    const elements = document.querySelectorAll(selector);
                    return Array.from(elements)
                        .map(el => el.href)
                        .filter(href => href);
                }}""", self.pagination.page_numbers.css_selector)
                
                valid_urls = {urljoin(self.base_url, url) for url in urls if url}
                self.pagination.discovered_urls.update(valid_urls)

            # Try to detect URL pattern
            if self.pagination.discovered_urls:
                patterns = []
                for url in self.pagination.discovered_urls:
                    match = re.search(r'page[=/](\d+)', url, re.IGNORECASE)
                    if match:
                        pattern = url.replace(match.group(1), '{page}')
                        patterns.append(pattern)
                
                if patterns:
                    # Use most common pattern
                    self.pagination.url_pattern = max(set(patterns), key=patterns.count)

            return self.pagination.discovered_urls
        except Exception as e:
            logging.error(f"Error extracting pagination URLs: {e}")
            return set()

    def generate_pagination_urls(self, max_pages: Optional[int] = None) -> Set[str]:
        """Generate pagination URLs based on detected pattern."""
        if not self.pagination or not self.pagination.url_pattern:
            return set()

        try:
            last_page = int(self.pagination.last_page) if self.pagination.last_page else max_pages
            if not last_page:
                return set()

            urls = set()
            for page in range(1, min(last_page + 1, (max_pages or last_page) + 1)):
                url = self.pagination.url_pattern.replace('{page}', str(page))
                urls.add(url)

            return urls
        except Exception as e:
            logging.error(f"Error generating pagination URLs: {e}")
            return set()

    def save_selectors(self, filename: str) -> bool:
        """Save selected elements and pagination info to file."""
        try:
            data = {
                "elements": [
                    {
                        "css_selector": e.css_selector,
                        "xpath_selector": e.xpath_selector,
                        "attributes": e.attributes,
                        "element_type": e.element_type,
                        "parent_selector": e.parent_selector,
                        "children_selectors": e.children_selectors
                    }
                    for e in self.selected_elements
                ],
                "pagination": {
                    "next_button": self.pagination.next_button.__dict__ if self.pagination and self.pagination.next_button else None,
                    "page_numbers": self.pagination.page_numbers.__dict__ if self.pagination and self.pagination.page_numbers else None,
                    "last_page": self.pagination.last_page if self.pagination else None,
                    "url_pattern": self.pagination.url_pattern if self.pagination else None
                } if self.pagination else None
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving selectors: {e}")
            return False
