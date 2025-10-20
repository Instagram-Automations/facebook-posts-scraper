from __future__ import annotations

import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .utils import clean_text, safe_int, setup_logger

logger = setup_logger("parser")


def _extract_time(ts_text: str) -> (Optional[int], Optional[str]):
    """
    Attempt to parse mixed timestamp formats from visible text or time elements.
    """
    if not ts_text:
        return None, None
    ts_text = ts_text.strip()

    # Look for Unix epoch in milliseconds or seconds inside the text
    m = re.search(r"(\d{10,13})", ts_text)
    if m:
        raw = m.group(1)
        try:
            ts = int(raw)
            if len(raw) == 13:  # ms
                return ts, datetime.fromtimestamp(ts / 1000).isoformat()
            else:
                return ts * 1000, datetime.fromtimestamp(ts).isoformat()
        except Exception:
            pass

    # Fallback: try to parse human-readable date
    for fmt in ("%A, %d %B %Y at %H:%M", "%d %B %Y %H:%M", "%Y-%m-%d %H:%M", "%b %d, %Y %H:%M"):
        try:
            dt = datetime.strptime(ts_text, fmt)
            return int(dt.timestamp() * 1000), dt.isoformat()
        except Exception:
            continue

    return None, ts_text


def _post_id_from_href(href: str) -> Optional[str]:
    if not href:
        return None
    # Try to extract digits from typical patterns
    # /story.php?story_fbid=10153102379324999&id=5281959998
    m = re.search(r"(?:story_fbid|posts|videos)/?[:=]?/?(\d{8,})", href)
    if m:
        return m.group(1)
    # pfbid style as fallback (return pfbid token)
    m2 = re.search(r"(pfbid\w+)", href)
    if m2:
        return m2.group(1)
    return None


def parse_facebook_html(html: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Parse a public m.facebook.com page HTML and extract post cards.
    This parser aims to be resilient but may not cover all layouts.
    """
    soup = BeautifulSoup(html, "lxml")

    # Try to find page info (name/id) from og tags
    og_title = soup.find("meta", property="og:title")
    page_name = og_title["content"] if og_title and og_title.get("content") else None

    # Fallback name from page header
    if not page_name:
        header = soup.select_one("title")
        page_name = clean_text(header.text) if header else None

    cards = []
    # Posts on m.facebook often have data-ft or role=article blocks.
    # We'll target common containers:
    containers = soup.select("div.storyStream > div") or soup.select("article, div[data-ft], div.story_body_container")
    for container in containers:
        # Link to post
        post_link = container.find("a", href=re.compile(r"(story\.php|/posts/|/videos/|pfbid)"))
        href = post_link["href"] if post_link and post_link.has_attr("href") else None
        if not href:
            continue
        url = urljoin(base_url, href)
        post_id = _post_id_from_href(href)

        # Text content
        # m.facebook often uses <p> within the container for text
        text_parts = []
        for p in container.select("p"):
            text_parts.append(clean_text(p.get_text(" ", strip=True)))
        text = clean_text("\n".join([t for t in text_parts if t]))

        # Timestamp: try <abbr>, <time>, or aria-label on a small element
        time_node = container.find(["abbr", "time"])
        ts_text = None
        if time_node:
            ts_text = time_node.get("data-utime") or time_node.get_text(" ", strip=True)
        else:
            small = container.find("span", attrs={"title": True})
            if small:
                ts_text = small.get("title")
        timestamp, iso_display = _extract_time(ts_text or "")

        # counts: likes, comments, shares often appear as links or text like "12 likes"
        likes = comments = shares = None
        counts_text = container.get_text(" ", strip=True)
        if counts_text:
            like_match = re.search(r"(\d[\d,\.]*)\s+like", counts_text, re.I)
            comment_match = re.search(r"(\d[\d,\.]*)\s+comment", counts_text, re.I)
            share_match = re.search(r"(\d[\d,\.]*)\s+share", counts_text, re.I)
            likes = safe_int(like_match.group(1)) if like_match else None
            comments = safe_int(comment_match.group(1)) if comment_match else None
            shares = safe_int(share_match.group(1)) if share_match else None

        # image/thumb
        img = container.find("img")
        thumb = img["src"] if img and img.has_attr("src") else None

        item = {
            "facebookUrl": base_url,
            "pageId": None,  # Not always available without additional requests
            "postId": post_id,
            "pageName": page_name,
            "url": url,
            "time": iso_display or None,
            "timestamp": timestamp,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "text": text or None,
            "link": None,  # could be extracted from anchors; omitted for safety
            "thumb": thumb,
            "topLevelUrl": url,
            "facebookId": None,
            "postFacebookId": post_id,
        }

        # Keep only items that have at least a URL and some text or ID
        if item["url"] and (item["text"] or item["postId"]):
            cards.append(item)

    # Deduplicate by url/postId
    seen = set()
    unique_cards = []
    for c in cards:
        key = c.get("url") or c.get("postId")
        if key and key not in seen:
            seen.add(key)
            unique_cards.append(c)

    return unique_cards
