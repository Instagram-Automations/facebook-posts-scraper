from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def get_default_headers() -> Dict[str, str]:
    # Allow override via env
    ua = os.environ.get(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    )
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        s = str(value).replace(",", "").replace(".", "")
        return int(s)
    except Exception:
        return None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
