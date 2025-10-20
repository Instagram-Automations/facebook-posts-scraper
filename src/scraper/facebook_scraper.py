from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urlunparse

import requests

from .parser import parse_facebook_html
from .proxy_manager import ProxyManager
from .utils import setup_logger, get_default_headers


@dataclass
class FacebookScraper:
    proxies_file: Optional[str] = None
    max_retries: int = 3
    results_limit: int = 50
    timeout: int = 20

    def __post_init__(self):
        self.logger = setup_logger(self.__class__.__name__)
        self.proxy_manager = ProxyManager(self.proxies_file) if self.proxies_file else None
        self.session = requests.Session()
        self.session.headers.update(get_default_headers())

    def _normalize_to_mobile(self, url: str) -> str:
        """
        Prefer m.facebook.com for simpler DOM when scraping public pages.
        """
        parsed = urlparse(url)
        netloc = parsed.netloc
        if "facebook.com" in netloc and not netloc.startswith(("m.", "mbasic.")):
            netloc = "m.facebook.com"
        return urlunparse(parsed._replace(netloc=netloc))

    def _choose_proxy(self) -> Optional[dict]:
        if not self.proxy_manager:
            return None
        proxy_url = self.proxy_manager.pick()
        if not proxy_url:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def _fetch(self, url: str) -> str:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(self._normalize_to_mobile(url), proxies=self._choose_proxy(), timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.text
                self.logger.warning("Non-200 status %s for %s (attempt %d)", resp.status_code, url, attempt)
            except requests.RequestException as e:
                last_exc = e
                self.logger.warning("Request failed (%d/%d): %s", attempt, self.max_retries, e)
            # backoff with jitter
            time.sleep(min(4.0, 0.5 * attempt + random.random()))
        raise RuntimeError(f"Failed to fetch {url}: {last_exc}")

    def scrape(self, url: str) -> List[Dict[str, Any]]:
        """
        Scrape public posts from given page/profile URL.
        """
        html = self._fetch(url)
        items = parse_facebook_html(html, base_url=url)
        if self.results_limit:
            items = items[: self.results_limit]
        return items
