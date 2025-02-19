import scrapy
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import threading
from pathlib import Path

from ..proxy_manager import ProxyManager, load_proxies
from ..image_processor import ImageProcessor
from ..utils import GalleryUtils, FileUtils, JsonUtils
from .. import settings

class GallerySpider(scrapy.Spider):
    name = 'gallery'
    total_downloaded = 0
    total_downloaded_lock = threading.Lock()
    root_master_lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        super(GallerySpider, self).__init__(*args, **kwargs)
        self.proxies = load_proxies(settings.PROXIES_FILE)
        self.proxy_manager = ProxyManager(self.proxies)
        self.image_processor = ImageProcessor(
            settings.MIN_FILE_SIZE,
            settings.MAX_FILE_SIZE,
            settings.DOWNLOAD_TIMEOUT
        )
        self.base_proxy_map = {}

    def start_requests(self):
        urls = FileUtils.read_urls_file(settings.URLS_FILE)
        self.logger.info(f"Found {len(urls)} URLs to process")
        
        for url in urls:
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            proxy = self.get_proxy_for_base(base_url)
            
            yield scrapy.Request(
                url,
                callback=self.parse_gallery,
                errback=self.handle_error,
                meta={'proxy': proxy['http'], 'base_url': base_url},
                dont_filter=True
            )

    def parse_gallery(self, response):
        base_url = response.meta['base_url']
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract title
        title_tag = soup.select_one('.container .title-box span')
        title = title_tag.get_text(strip=True) if title_tag else "No Title Found"
        
        # Extract image links
        href_links = []
        for a_tag in soup.select('a.short'):
            link = a_tag.get('href')
            if link:
                href_links.append(self.create_image_link_dict(link))
                
        # Additional selectors from the update
        for a_tag in soup.select("div.gallery a"):
            link = a_tag.get("href")
            if link:
                href_links.append(self.create_image_link_dict(link))
        
        # Extract tags
        tags = []
        tags.extend([a.get_text(strip=True) for a in soup.select('.video-tags a') if a.get_text(strip=True)])
        tags.extend([a.get_text(strip=True) for a in soup.select("ul.subnav li a") if a.get_text(strip=True)])
        
        if not href_links:
            self.logger.info(f"No image links found in {response.url}")
            return
        
        gallery_name = title.replace(' ', '-') if title else "none"
        gallery_folder = Path(settings.OUTPUT_ROOT) / gallery_name
        gallery_folder.mkdir(parents=True, exist_ok=True)
        
        gallery_data = {
            "gallery_name": gallery_name,
            "title": title,
            "tags": tags,
            "href_links": href_links,
            "source_url": response.url
        }
        
        # Process images
        for link_data in href_links:
            image_url = link_data["href"]
            image_filename = os.path.basename(urlparse(image_url).path)
            dest_path = gallery_folder / image_filename
            
            if self.process_image(image_url, dest_path, link_data, response.meta['proxy']):
                self.update_gallery_json(gallery_folder, gallery_name, gallery_data)
        
        # Calculate and schedule rehits
        total_hits = GalleryUtils.calculate_rehits(len(href_links))
        proxy = self.base_proxy_map.get(base_url, {}).get('proxy_dict')
        if proxy:
            GalleryUtils.hit_base_url(base_url, total_hits, proxy)

    def process_image(self, image_url, dest_path, link_data, proxy):
        """Process a single image download and update its metadata."""
        if self.image_processor.download_image(image_url, {'http': proxy, 'https': proxy}, dest_path):
            file_size = os.path.getsize(dest_path)
            with self.total_downloaded_lock:
                self.total_downloaded += file_size
                if self.total_downloaded >= settings.TOTAL_DOWNLOAD_LIMIT:
                    self.logger.info("Total download limit reached")
                    return False
            
            width, height, res, hw_ratio, wh_ratio, aspect_type, quality, phash = \
                self.image_processor.get_image_info(dest_path)
            
            link_data.update({
                "file_path": str(dest_path.relative_to(settings.OUTPUT_ROOT)),
                "file_size": f"{file_size / 1024:.2f}KB",
                "resolution": res,
                "aspect_hw": hw_ratio,
                "aspect_wh": wh_ratio,
                "p_a": aspect_type,
                "image_quality": quality,
                "phash": phash
            })
            return True
        return False

    def create_image_link_dict(self, href):
        """Create the initial image link dictionary structure."""
        return {
            "href": href,
            "file_size": "none",
            "file_path": "none",
            "resolution": "none",
            "aspect_hw": "none",
            "aspect_wh": "none",
            "p_a": "none",
            "full_length_description": "none",
            "number_models": "none",
            "setting": "none",
            "image_quality": "none",
            "image_clarity": "none",
            "image_apparent_age": "none",
            "confidence_scores": {
                "physical_description": "none",
                "actions": "none",
                "pose": "none",
                "setting": "none"
            },
            "models": [],
            "grouped_models": {
                "count": "none",
                "general_tags": [],
                "dominant_submissive": "none",
                "level_of_dress": "none",
                "pose": "none",
                "actions": [],
                "skin_tone_variation": [],
                "body_type_variation": [],
                "ethnicities": []
            },
            "lighting": "none",
            "image_style": "none",
            "color_balance": "none",
            "image_noise_level": "none",
            "motion_intensity": "none",
            "sequence_suggestion": "none",
            "scene_pacing": "none",
            "relationship_type": "none",
            "emotional_tone": "none",
            "explicit_rating": "none",
            "fluid_presence": [],
            "props": [],
            "phash": "none"
        }

    def update_gallery_json(self, gallery_folder, gallery_name, gallery_data):
        """Update the gallery's JSON file and root master file."""
        gallery_json_path = gallery_folder / f"{gallery_name}.json"
        JsonUtils.update_json_file(gallery_json_path, gallery_data)
        JsonUtils.update_json_file(
            settings.ROOT_MASTER_FILE,
            [gallery_data],
            self.root_master_lock
        )

    def get_proxy_for_base(self, base_url):
        """Get or assign a proxy for the given base URL."""
        if base_url in self.base_proxy_map:
            return self.base_proxy_map[base_url]["proxy_dict"]
        else:
            proxy_entry = self.proxy_manager.get_proxy_entry()
            if proxy_entry is None:
                self.logger.error("No available proxies.")
                raise Exception("No available proxies")
            self.base_proxy_map[base_url] = proxy_entry
            return proxy_entry["proxy_dict"]

    def handle_error(self, failure):
        """Handle request failures."""
        self.logger.error(f"Request failed: {failure.value}")
        if hasattr(failure.value, 'response') and failure.value.response:
            self.logger.error(f"Response status: {failure.value.response.status}")
