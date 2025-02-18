import threading
import time
import random
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class RotationStrategy(Enum):
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    PERCENTAGE_ACTIVE = "percentage_active"
    REST_READY = "rest_ready"
    STICKY_SESSION = "sticky_session"
    CUSTOM_RULES = "custom_rules"

@dataclass
class ProxyStats:
    success_count: int = 0
    failure_count: int = 0
    ban_count: int = 0
    last_used: float = 0
    rest_until: float = 0
    active_percentage: float = 0
    domain_rules: Dict[str, bool] = None

    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.success_count / self.total_requests

class ProxyManager:
    def __init__(self, proxies_list: List[Dict[str, str]], strategy: RotationStrategy = RotationStrategy.RANDOM):
        self.proxies = {
            proxy['http']: {
                "proxy_dict": proxy,
                "state": "active",
                "stats": ProxyStats(domain_rules={})
            } for proxy in proxies_list
        }
        self.strategy = strategy
        self.lock = threading.Lock()
        self.current_index = 0
        self.domain_sticky_proxies = {}

    def set_strategy(self, strategy: RotationStrategy) -> None:
        """Change the proxy rotation strategy."""
        with self.lock:
            self.strategy = strategy

    def configure_proxy(self, proxy_url: str, **kwargs) -> None:
        """Configure specific proxy settings."""
        with self.lock:
            if proxy_url in self.proxies:
                if 'active_percentage' in kwargs:
                    self.proxies[proxy_url]['stats'].active_percentage = kwargs['active_percentage']
                if 'domain_rules' in kwargs:
                    self.proxies[proxy_url]['stats'].domain_rules.update(kwargs['domain_rules'])
                if 'rest_time' in kwargs:
                    current_time = time.time()
                    self.proxies[proxy_url]['stats'].rest_until = current_time + kwargs['rest_time']

    def get_proxy(self, domain: Optional[str] = None) -> Tuple[Dict[str, str], str]:
        """Get a proxy based on the current strategy."""
        with self.lock:
            if self.strategy == RotationStrategy.RANDOM:
                return self._get_random_proxy()
            elif self.strategy == RotationStrategy.ROUND_ROBIN:
                return self._get_round_robin_proxy()
            elif self.strategy == RotationStrategy.PERCENTAGE_ACTIVE:
                return self._get_percentage_based_proxy()
            elif self.strategy == RotationStrategy.REST_READY:
                return self._get_rested_proxy()
            elif self.strategy == RotationStrategy.STICKY_SESSION and domain:
                return self._get_sticky_proxy(domain)
            elif self.strategy == RotationStrategy.CUSTOM_RULES and domain:
                return self._get_custom_rule_proxy(domain)
            return self._get_random_proxy()  # fallback

    def _get_random_proxy(self) -> Tuple[Dict[str, str], str]:
        """Get a random active proxy."""
        active_proxies = [
            (url, data) for url, data in self.proxies.items()
            if data['state'] == 'active' and time.time() >= data['stats'].rest_until
        ]
        if not active_proxies:
            raise Exception("No active proxies available")
        proxy_url, proxy_data = random.choice(active_proxies)
        return proxy_data['proxy_dict'], proxy_url

    def _get_round_robin_proxy(self) -> Tuple[Dict[str, str], str]:
        """Get the next proxy in rotation."""
        active_proxies = [
            (url, data) for url, data in self.proxies.items()
            if data['state'] == 'active' and time.time() >= data['stats'].rest_until
        ]
        if not active_proxies:
            raise Exception("No active proxies available")
        
        self.current_index = (self.current_index + 1) % len(active_proxies)
        proxy_url, proxy_data = active_proxies[self.current_index]
        return proxy_data['proxy_dict'], proxy_url

    def _get_percentage_based_proxy(self) -> Tuple[Dict[str, str], str]:
        """Get a proxy based on configured usage percentages."""
        current_time = time.time()
        available_proxies = [
            (url, data) for url, data in self.proxies.items()
            if data['state'] == 'active' and current_time >= data['stats'].rest_until
        ]
        
        if not available_proxies:
            raise Exception("No available proxies")

        # Calculate current usage percentages
        total_requests = sum(data['stats'].total_requests for _, data in available_proxies)
        if total_requests == 0:
            return self._get_random_proxy()

        # Find proxy furthest below its target percentage
        best_proxy = min(
            available_proxies,
            key=lambda x: (
                x[1]['stats'].total_requests / total_requests if total_requests > 0 else 0
            ) - x[1]['stats'].active_percentage
        )
        return best_proxy[1]['proxy_dict'], best_proxy[0]

    def _get_rested_proxy(self) -> Tuple[Dict[str, str], str]:
        """Get a proxy that has completed its rest period."""
        current_time = time.time()
        rested_proxies = [
            (url, data) for url, data in self.proxies.items()
            if data['state'] == 'active' and current_time >= data['stats'].rest_until
        ]
        if not rested_proxies:
            raise Exception("No rested proxies available")
        
        # Get proxy with longest rest
        best_proxy = max(rested_proxies, key=lambda x: current_time - x[1]['stats'].last_used)
        return best_proxy[1]['proxy_dict'], best_proxy[0]

    def _get_sticky_proxy(self, domain: str) -> Tuple[Dict[str, str], str]:
        """Get or assign a sticky proxy for a domain."""
        if domain in self.domain_sticky_proxies:
            proxy_url = self.domain_sticky_proxies[domain]
            if self.proxies[proxy_url]['state'] == 'active':
                return self.proxies[proxy_url]['proxy_dict'], proxy_url

        # Assign new proxy to domain
        proxy_dict, proxy_url = self._get_random_proxy()
        self.domain_sticky_proxies[domain] = proxy_url
        return proxy_dict, proxy_url

    def _get_custom_rule_proxy(self, domain: str) -> Tuple[Dict[str, str], str]:
        """Get a proxy based on custom domain rules."""
        matching_proxies = [
            (url, data) for url, data in self.proxies.items()
            if data['state'] == 'active' and
            data['stats'].domain_rules.get(domain, True) and
            time.time() >= data['stats'].rest_until
        ]
        if not matching_proxies:
            return self._get_random_proxy()
        
        proxy_url, proxy_data = random.choice(matching_proxies)
        return proxy_data['proxy_dict'], proxy_url

    def report_success(self, proxy_url: str) -> None:
        """Report successful proxy use."""
        with self.lock:
            if proxy_url in self.proxies:
                self.proxies[proxy_url]['stats'].success_count += 1
                self.proxies[proxy_url]['stats'].last_used = time.time()

    def report_failure(self, proxy_url: str, is_ban: bool = False) -> None:
        """Report proxy failure."""
        with self.lock:
            if proxy_url in self.proxies:
                proxy = self.proxies[proxy_url]
                proxy['stats'].failure_count += 1
                if is_ban:
                    proxy['stats'].ban_count += 1
                    proxy['stats'].rest_until = time.time() + 300  # 5 minute rest
                proxy['stats'].last_used = time.time()

    def get_stats(self) -> Dict[str, Dict]:
        """Get current proxy statistics."""
        with self.lock:
            return {
                url: {
                    "success_rate": data['stats'].success_rate,
                    "total_requests": data['stats'].total_requests,
                    "bans": data['stats'].ban_count,
                    "state": data['state'],
                    "last_used": data['stats'].last_used
                }
                for url, data in self.proxies.items()
            }
