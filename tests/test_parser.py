from src.scraper.parser import parse_facebook_html

HTML = """
<html>
  <head><title>Sample Page</title></head>
  <body>
    <div class="storyStream">
      <div>
        <a href="/pfbid02abc123">Post</a>
        <p>Alpha</p><p>Beta</p>
        <time data-utime="1700000000"></time>
        <div>1,234 likes · 56 comments · 7 shares</div>
      </div>
    </div>
  </body>
</html>
"""


def test_parser_extracts_counts_and_text():
    items = parse_facebook_html(HTML, base_url="https://m.facebook.com/test")
    assert len(items) == 1
    it = items[0]
    # pfbid retained as ID fallback
    assert it["postId"].startswith("pfbid")
    assert it["likes"] == 1234
    assert it["comments"] == 56
    assert it["shares"] == 7
    assert "Alpha" in it["text"] and "Beta" in it["text"]
    assert it["timestamp"] == 1700000000 * 1000
