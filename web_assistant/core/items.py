import scrapy

class GalleryItem(scrapy.Item):
    """Item class for gallery data."""
    gallery_name = scrapy.Field()
    title = scrapy.Field()
    tags = scrapy.Field()
    href_links = scrapy.Field()
    source_url = scrapy.Field()
    saved = scrapy.Field()
    gallery_data = scrapy.Field()
