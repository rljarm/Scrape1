from pathlib import Path
import os

# Scrapy settings
BOT_NAME = 'image_scraper'
SPIDER_MODULES = ['image_scraper.spiders']
NEWSPIDER_MODULE = 'image_scraper.spiders'
ROBOTSTXT_OBEY = True

# File size limits
MIN_FILE_SIZE = 110 * 1024            # 110 KB
MAX_FILE_SIZE = 23.8 * 1024 * 1024    # 23.8 MB

# Batch processing
BATCH_SIZE = 200
OUTPUT_PADDING = 6
DOWNLOAD_TIMEOUT = 30                  # seconds

# File paths
URLS_FILE = "3xmcls30000.txt"         # file with gallery URLs
PROXIES_FILE = "proxies.txt"          # file with proxies in ip:port:user:pwd format
INDEX_FILE = "index1.json"            # index file for galleries
MASTER_JSON_PREFIX = "main-3xmsc-"    # prefix for master JSON sets
OUTPUT_ROOT = Path.cwd() / "output1"   # output folder
TOT_FILE = "tot1.txt"                 # total download tracking file
ROOT_MASTER_FILE = "root_master1.json" # root level master JSON tracking

# Create output directory
OUTPUT_ROOT.mkdir(exist_ok=True)

# Download limits
TOTAL_DOWNLOAD_LIMIT = 70 * 1024 * 1024 * 1024  # 70GB limit

# Concurrent processing
CONCURRENT_REQUESTS = 10
CONCURRENT_REQUESTS_PER_DOMAIN = 10
DOWNLOAD_DELAY = 1

# Additional Scrapy settings
ITEM_PIPELINES = {
    'image_scraper.pipelines.ImageScraperPipeline': 300,
}

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Default headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
