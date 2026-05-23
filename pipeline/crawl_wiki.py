"""Crawls ss13.moe and writes a markdown bundle for the MCP server."""

import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import html2text
import httpx
from selectolax.parser import HTMLParser

log = logging.getLogger(__name__)

WIKI_BASE = "https://ss13.moe/wiki/"
USER_AGENT = "vgstation13-mcp-bump (+https://github.com/vg14-developers/vgstation13-mcp)"
CRAWL_DELAY_S = 1.0


def _clean_title(raw: str, fallback: str) -> str:
    """Strip common wiki suffixes from a <title> tag, fall back if empty."""
    title = raw.strip()
    # Strip suffixes like " - vgstation13", " — vg13 wiki", " | Wiki", etc.
    for sep in (" - ", " — ", " | "):
        if sep in title:
            title = title.split(sep, 1)[0].strip()
            break
    return title or fallback


def fetch_page_list(client: httpx.Client) -> list[str]:
    pages: list[str] = []
    next_url: str | None = urljoin(WIKI_BASE, "index.php/Special:AllPages")
    while next_url:
        resp = client.get(next_url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        tree = HTMLParser(resp.text)
        for a in tree.css(".mw-allpages-chunk li a"):
            href = a.attributes.get("href", "")
            m = re.search(r"/wiki/index\.php\?title=([^&]+)", href) or re.search(
                r"/wiki/([^?#]+)$", href
            )
            if m:
                pages.append(m.group(1))
        nxt = tree.css_first(".mw-allpages-nav a:contains('Next page')")
        next_url = urljoin(WIKI_BASE, nxt.attributes["href"]) if nxt else None
        time.sleep(CRAWL_DELAY_S)
    return pages


def fetch_and_save(client: httpx.Client, page: str, out_dir: Path) -> dict | None:
    url = urljoin(WIKI_BASE, f"index.php?title={page}&action=raw")
    resp = client.get(url, headers={"User-Agent": USER_AGENT})
    if resp.status_code != 200:
        log.warning("failed: %s status=%s", page, resp.status_code)
        return None
    html_url = urljoin(WIKI_BASE, f"index.php/{page}")
    html_resp = client.get(html_url, headers={"User-Agent": USER_AGENT})
    html_resp.raise_for_status()
    tree = HTMLParser(html_resp.text)
    title_el = tree.css_first("#firstHeading")
    title = title_el.text() if title_el else page

    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_images = True
    content_el = tree.css_first("#mw-content-text")
    md = converter.handle(content_el.html if content_el else html_resp.text)

    out_path = out_dir / f"{page}.md"
    out_path.write_text(f"# {title}\n\n{md.strip()}\n")
    return {"page": page, "title": title}


def html_to_markdown_bundle(html_dir: Path, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    converter = html2text.HTML2Text()
    converter.body_width = 0
    converter.ignore_images = True
    index = []
    for html_file in sorted(html_dir.glob("*.html")):
        text = html_file.read_text()
        tree = HTMLParser(text)
        title_el = tree.css_first("title")
        if title_el and title_el.text().strip():
            title = _clean_title(title_el.text(), html_file.stem)
        else:
            h1_el = tree.css_first("h1")
            title = h1_el.text().strip() if h1_el else html_file.stem
        body_el = tree.css_first("body") or tree
        md = converter.handle(body_el.html if hasattr(body_el, "html") else text)
        page_name = html_file.stem
        out_path = out_dir / f"{page_name}.md"
        out_path.write_text(f"# {title}\n\n{md.strip()}\n")
        index.append({"page": page_name, "title": title})
    (out_dir / "index.json").write_text(json.dumps(index, indent=2))
    return index


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=30.0) as client:
        pages = fetch_page_list(client)
        log.info("found %d pages", len(pages))
        index = []
        ok = 0
        for page in pages:
            entry = fetch_and_save(client, page, out_dir)
            if entry:
                index.append(entry)
                ok += 1
            time.sleep(CRAWL_DELAY_S)
        (out_dir / "index.json").write_text(json.dumps(index, indent=2))
        success_rate = ok / max(len(pages), 1)
        log.info("crawled %d/%d pages (%.1f%%)", ok, len(pages), success_rate * 100)
        if success_rate < 0.95:
            raise RuntimeError(f"wiki crawl below 95% threshold: {success_rate:.1%}")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    main(Path(sys.argv[1]))
