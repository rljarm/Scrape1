import os
from pathlib import Path
from .utils import JsonUtils
from . import settings

class ImageScraperPipeline:
    def __init__(self):
        self.gallery_list = []
        self.processed_urls = set()

    def process_item(self, item, spider):
        """Process each gallery item and update relevant files."""
        if item.get('saved', False) and item.get('gallery_data'):
            self.gallery_list.append(item['gallery_data'])
            if 'source_url' in item['gallery_data']:
                self.processed_urls.add(item['gallery_data']['source_url'])
        return item

    def close_spider(self, spider):
        """Called when the spider is closed."""
        # Create master JSON files
        JsonUtils.create_batch_json(
            self.gallery_list,
            settings.OUTPUT_ROOT,
            settings.MASTER_JSON_PREFIX,
            settings.BATCH_SIZE,
            settings.OUTPUT_PADDING
        )

        # Create index file
        index_records = [
            {
                "gallery": data["gallery_name"],
                "saved": True
            }
            for data in self.gallery_list
        ]
        JsonUtils.update_json_file(
            os.path.join(settings.OUTPUT_ROOT, settings.INDEX_FILE),
            index_records
        )

        # Update URLs file to mark processed URLs
        if self.processed_urls:
            from .utils import FileUtils
            FileUtils.update_urls_file(settings.URLS_FILE, self.processed_urls)

        # Update total downloaded size
        if hasattr(spider, 'total_downloaded'):
            with open(settings.TOT_FILE, 'a', encoding='utf-8') as f:
                f.write(str(spider.total_downloaded) + "\n")
