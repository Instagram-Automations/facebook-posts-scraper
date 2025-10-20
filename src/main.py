#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

from scraper.facebook_scraper import FacebookScraper
from scraper.export_manager import ExportManager
from scraper.utils import load_json, setup_logger, ensure_dir

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"

logger = setup_logger("main")


def load_settings(settings_path: Path) -> Dict[str, Any]:
    if not settings_path.exists():
        # sensible defaults if missing
        logger.warning("settings.json not found, using default settings.")
        return {
            "resultsLimit": 5,
            "startUrls": [{"url": "https://m.facebook.com/nytimes"}],
            "maxRequestRetries": 3,
            "downloadThumbnails": False,
        }
    return load_json(settings_path)


def main():
    ensure_dir(DATA_DIR)
    ensure_dir(DATA_DIR / "thumbnails")

    settings = load_settings(CONFIG_DIR / "settings.json")

    start_urls: List[str] = [u.get("url") for u in settings.get("startUrls", []) if u.get("url")]
    if not start_urls:
        logger.error("No start URLs provided in settings.json 'startUrls'.")
        sys.exit(1)

    results_limit = int(settings.get("resultsLimit", 25))
    retries = int(settings.get("maxRequestRetries", 3))
    download_thumbs = bool(settings.get("downloadThumbnails", False))

    scraper = FacebookScraper(
        proxies_file=CONFIG_DIR / "proxies.txt",
        max_retries=retries,
        results_limit=results_limit,
    )

    logger.info("Starting scrape for %d URL(s)", len(start_urls))
    all_items: List[Dict[str, Any]] = []
    for url in start_urls:
        try:
            items = scraper.scrape(url)
            if results_limit:
                items = items[:results_limit]
            all_items.extend(items)
            logger.info("Collected %d item(s) from %s", len(items), url)
        except Exception as e:
            logger.exception("Failed to scrape %s: %s", url, e)

    if not all_items:
        logger.warning("No items collected.")
    else:
        exporter = ExportManager(data_dir=DATA_DIR)
        exporter.to_json(all_items, DATA_DIR / "output.json")
        exporter.to_csv(all_items, DATA_DIR / "sample.csv")
        if download_thumbs:
            exporter.download_thumbnails(all_items, DATA_DIR / "thumbnails")

    logger.info("Done. JSON -> %s, CSV -> %s", DATA_DIR / "output.json", DATA_DIR / "sample.csv")


if __name__ == "__main__":
    main()
