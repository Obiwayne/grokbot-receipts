"""Render a case's card.html to a 1200x675 PNG (the size X and Bluesky show link images at).

Usage: python scripts/card_png.py <case folder> [out.png]
Needs Playwright's Chromium, which `crawl4ai-setup` installs.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    folder = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else folder / "card.png"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
        page.goto((folder / "card.html").as_uri())
        page.locator(".card").screenshot(path=str(out))
        browser.close()
    print(out)


if __name__ == "__main__":
    main()
