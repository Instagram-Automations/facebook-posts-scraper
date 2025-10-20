import json
from pathlib import Path

import pytest

from src.scraper.facebook_scraper import FacebookScraper


MOCK_HTML = """
<html>
  <head>
    <title>The New York Times - Home</title>
    <meta property="og:title" content="The New York Times" />
  </head>
  <body>
    <div class="storyStream">
      <div class="post">
        <a href="/nytimes/posts/10153102379324999">Post Link</a>
        <p>First line of the post.</p>
        <p>Second line of the post.</p>
        <time data-utime="1680790202">Thursday, 6 April 2023 at 07:10</time>
        <div>22 likes · 3 comments · 1 share</div>
        <img src="https://example.com/image1.jpg" />
      </div>
      <div class="post">
        <a href="/story.php?story_fbid=10153102374144999&id=5281959998">Another post</a>
        <p>Different text</p>
        <abbr title="Thursday, 6 April 2023 at 06:55">time</abbr>
        <div>9 likes · 17 comments</div>
      </div>
    </div>
  </body>
</html>
"""


class MockScraper(FacebookScraper):
    def _fetch(self, url: str) -> str:
        # bypass network for tests
        return MOCK_HTML


def test_scrape_returns_items(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    scraper = MockScraper(max_retries=1, results_limit=5)
    items = scraper.scrape("https://m.facebook.com/nytimes")
    assert len(items) == 2

    # Validate fields
    first = items[0]
    assert first["pageName"] == "The New York Times"
    assert first["postId"] == "10153102379324999"
    assert first["likes"] == 22
    assert first["comments"] == 3
    assert first["shares"] == 1
    assert first["thumb"] == "https://example.com/image1.jpg"
    assert first["timestamp"] == 1680790202000
