import os
import random
import json
import logging
import threading
import requests
from urllib.parse import urlparse
import time

class GalleryUtils:
    @staticmethod
    def calculate_rehits(num_images):
        """Calculate number of times to hit the base URL after downloading images."""
        n = random.randint(1, 10)
        y = random.uniform(0.5, 2.0)
        k = 11
        return max(1, int((n * y * k / 100) * num_images))

    @staticmethod
    def hit_base_url(base_url, num_hits, proxy, timeout=30):
        """Hit the base URL a given number of times using the assigned proxy."""
        for _ in range(num_hits):
            try:
                time.sleep(random.uniform(0.5, 2.0))
                requests.get(base_url, proxies=proxy, timeout=timeout)
            except Exception as e:
                logging.debug(f"Base URL hit failed for {base_url}: {e}")

class FileUtils:
    @staticmethod
    def read_urls_file(file_path):
        """Read URLs from file, skipping lines that begin with '***'."""
        if not os.path.exists(file_path):
            logging.error(f"{file_path} not found.")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        urls = [line for line in lines if not line.startswith('***')]
        random.shuffle(urls)
        return urls

    @staticmethod
    def update_urls_file(file_path, processed_urls):
        """Update URLs file by prefixing processed URLs with '***'."""
        if not os.path.exists(file_path):
            logging.error(f"{file_path} not found for update.")
            return
            
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped in processed_urls or stripped.lstrip('***') in processed_urls:
                if not stripped.startswith('***'):
                    new_lines.append('***' + stripped + "\n")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

class JsonUtils:
    @staticmethod
    def update_json_file(file_path, data, lock=None):
        """Thread-safe JSON file update."""
        def _write():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        if lock:
            with lock:
                _write()
        else:
            _write()

    @staticmethod
    def read_json_file(file_path):
        """Read JSON file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading JSON file {file_path}: {e}")
            return None

    @staticmethod
    def create_batch_json(data_list, output_dir, prefix, batch_size=200, padding=6):
        """Create batched JSON files from a list of data."""
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i+batch_size]
            batch_filename = os.path.join(output_dir, f"{prefix}{i:0{padding}d}.json")
            JsonUtils.update_json_file(batch_filename, batch)
            logging.info(f"Batch JSON saved: {batch_filename}")
