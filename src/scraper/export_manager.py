from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlparse
import requests

from .utils import setup_logger, ensure_dir

logger = setup_logger("export")


class ExportManager:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        ensure_dir(self.data_dir)

    def to_json(self, rows: List[Dict[str, Any]], path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        logger.info("Wrote JSON: %s", path)

    def to_csv(self, rows: List[Dict[str, Any]], path: Path) -> None:
        if not rows:
            # write an empty file with headers commonly expected
            headers = [
                "facebookUrl",
                "pageId",
                "postId",
                "pageName",
                "url",
                "time",
                "timestamp",
                "likes",
                "comments",
                "shares",
                "text",
                "link",
                "thumb",
                "topLevelUrl",
                "facebookId",
                "postFacebookId",
            ]
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
            logger.info("Wrote empty CSV with headers: %s", path)
            return

        headers = sorted({k for row in rows for k in row.keys()})
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        logger.info("Wrote CSV: %s", path)

    def download_thumbnails(self, rows: List[Dict[str, Any]], thumbs_dir: Path) -> None:
        ensure_dir(thumbs_dir)
        s = requests.Session()
        for row in rows:
            url = row.get("thumb")
            if not url:
                continue
            try:
                name = self._filename_from_url(url)
                out = thumbs_dir / name
                if out.exists():
                    continue
                resp = s.get(url, timeout=15)
                if resp.status_code == 200:
                    with open(out, "wb") as f:
                        f.write(resp.content)
            except Exception as e:
                logger.debug("Failed to download %s: %s", url, e)

    @staticmethod
    def _filename_from_url(url: str) -> str:
        parsed = urlparse(url)
        base = os.path.basename(parsed.path) or "thumb.jpg"
        if not os.path.splitext(base)[1]:
            base += ".jpg"
        return base
