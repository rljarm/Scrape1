import os
import logging
import subprocess
from PIL import Image
import imagehash
import requests
from urllib.parse import urlparse

class ImageProcessor:
    def __init__(self, min_size, max_size, download_timeout):
        self.min_size = min_size
        self.max_size = max_size
        self.download_timeout = download_timeout

    def get_image_info(self, image_path):
        """Extract image information including dimensions, aspect ratio, and perceptual hash."""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                res = f"{width}x{height}"
                if width == 0 or height == 0:
                    hw_ratio = 0
                    wh_ratio = 0
                    aspect_type = "m"
                else:
                    hw_ratio = int((height / width) * 100000)
                    wh_ratio = int((width / height) * 100000)
                    aspect_type = "p" if hw_ratio >= 110000 else "l" if hw_ratio <= 90000 else "m"
                perceptual_hash = str(imagehash.phash(img))
        except Exception as e:
            logging.error(f"Error getting image info for {image_path}: {e}")
            return 0, 0, "0x0", 0, 0, "m", "unknown", "none"
        
        quality = self.get_image_quality(image_path)
        return width, height, res, hw_ratio, wh_ratio, aspect_type, quality, perceptual_hash

    def get_image_quality(self, image_path):
        """Use exiftool to extract image quality information."""
        try:
            result = subprocess.run(
                ["exiftool", "-JPEGQuality", "-s", "-s", "-s", str(image_path)],
                capture_output=True, text=True, timeout=self.download_timeout
            )
            if result.returncode != 0:
                logging.error(f"Exiftool error on {image_path}: {result.stderr.strip()}")
                return "unknown"
            quality = result.stdout.strip()
            return quality if quality else "unknown"
        except Exception as e:
            logging.error(f"Error running exiftool on {image_path}: {e}")
            return "unknown"

    def download_image(self, url, proxy, dest_path):
        """Download an image with size validation."""
        try:
            response = requests.get(url, proxies=proxy, stream=True, timeout=self.download_timeout)
            response.raise_for_status()
            
            content_length = response.headers.get('Content-Length')
            if content_length:
                content_length = int(content_length)
                if content_length < self.min_size or content_length > self.max_size:
                    logging.info(f"Skipping {url} due to Content-Length {content_length}")
                    return False

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = os.path.getsize(dest_path)
            if file_size < self.min_size or file_size > self.max_size:
                logging.info(f"Downloaded file {dest_path} size {file_size} out of bounds, removing.")
                os.remove(dest_path)
                return False

            return True
        except Exception as e:
            logging.error(f"Download failed for {url} using proxy {proxy['http']}: {e}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
