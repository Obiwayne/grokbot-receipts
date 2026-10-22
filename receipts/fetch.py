"""Fetch a page as Markdown: Crawl4AI when it is installed, a plain HTTP fetch otherwise."""

import asyncio
import re
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

USER_AGENT = "Mozilla/5.0 (compatible; grokbot-receipts/0.1; +https://github.com/Obiwayne/grokbot-receipts)"


@dataclass
class Page:
    url: str
    final_url: str
    title: str
    markdown: str
    fetcher: str


class FetchError(Exception):
    pass


def have_crawl4ai() -> bool:
    try:
        import crawl4ai  # noqa: F401
    except ImportError:
        return False
    return True


def fetch(url: str, fetcher: str = "auto", timeout: float = 30) -> Page:
    if fetcher == "auto":
        fetcher = "crawl4ai" if have_crawl4ai() else "plain"
    if fetcher == "crawl4ai":
        return asyncio.run(_crawl4ai(url, timeout))
    if fetcher == "plain":
        return _plain(url, timeout)
    raise ValueError(f"unknown fetcher {fetcher!r}")


async def _crawl4ai(url: str, timeout: float) -> Page:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

    run = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=int(timeout * 1000), verbose=False)
    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        result = await crawler.arun(url, config=run)
    if not result.success:
        raise FetchError(f"{url}: {result.error_message or 'crawl failed'}")
    md = result.markdown
    markdown = getattr(md, "raw_markdown", None) or str(md or "")
    title = (result.metadata or {}).get("title") or ""
    final = getattr(result, "redirected_url", None) or result.url or url
    return Page(url, final, title.strip(), markdown, "crawl4ai")


def _plain(url: str, timeout: float) -> Page:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(5_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
            final = resp.geturl()
            ctype = resp.headers.get_content_type()
    except Exception as e:  # urllib raises several unrelated types
        raise FetchError(f"{url}: {e}") from e
    html = raw.decode(charset, errors="replace")
    if ctype == "text/plain":
        return Page(url, final, "", html, "plain")
    parser = _ToMarkdown()
    parser.feed(html)
    parser.close()
    return Page(url, final, parser.title.strip(), parser.markdown(), "plain")


class _ToMarkdown(HTMLParser):
    """Just enough HTML to Markdown for reading articles: headings, paragraphs, list items, links as text."""

    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form", "button", "template", "aside"}
    BLOCK = {"p", "div", "section", "article", "main", "li", "tr", "blockquote", "br", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "figcaption"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "title":
            self.in_title = True
        elif not self.skip and tag in self.BLOCK:
            self.parts.append("\n\n")
            if tag[0] == "h" and tag[1:].isdigit():
                self.parts.append("#" * int(tag[1]) + " ")
            elif tag == "li":
                self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag == "title":
            self.in_title = False
        elif not self.skip and tag in self.BLOCK:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not self.skip:
            self.parts.append(data)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t\r\f\v]+", " ", text)
        text = re.sub(r" *\n *", "\n", text)
        return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
