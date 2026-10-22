"""The same fetch through Crawl4AI's headless browser. Skipped when Crawl4AI or its browser isn't installed."""

import pytest

from receipts.fetch import fetch, have_crawl4ai

pytestmark = pytest.mark.skipif(not have_crawl4ai(), reason="crawl4ai not installed")


def test_crawl4ai_reads_the_article(sites):
    try:
        page = fetch(sites["council"], "crawl4ai", timeout=60)
    except Exception as e:  # no browser downloaded yet
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            pytest.skip("Crawl4AI's browser isn't installed (run crawl4ai-setup)")
        raise
    assert page.fetcher == "crawl4ai"
    assert "free for everyone" in page.markdown
    assert "Fare-free buses approved" in page.title
