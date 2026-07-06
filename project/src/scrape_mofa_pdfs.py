"""
Scraper for NDL WARP-archived MOFA "Foreign Minister" statement pages.

WARP wraps each archived page in a viewer shell with an <iframe id="pywb-frame">
whose src points at the real archived content. That src is present as plain,
static HTML from the very first response (it's not JS-injected), so a normal
`requests.get` + BeautifulSoup can find it directly with no headless browser
needed. Resolving it is just a normal urljoin -- no special path-patching
required, despite what an earlier version of this script assumed.

Notebook usage:
    from src.scrape_mofa_pdfs import MofaScraper

    scraper = MofaScraper()
    index_soup, index_url, fm_pages = scraper.build_fm_page_sequence()

    for url, text in fm_pages:
        print(text, "->", url)

    # debug (no downloads)
    scraper.run(debug=True)

    # real run
    scraper.run(debug=False)

Requires: requests, beautifulsoup4
    pip install requests beautifulsoup4
"""

import re
import time
import sys
import random
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import pandas as pd
import pdfplumber
from dateutil import parser as date_parser


class PdfDownloader:
    """Fetches pages (following the WARP viewer iframe to reach real content) and downloads PDFs."""

    def __init__(self, headers=None, timeout=30, request_delay_seconds=3.0):
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0; academic use)"
        }
        self.timeout = timeout
        self.request_delay_seconds = request_delay_seconds

    def get_soup(self, url: str) -> BeautifulSoup:
        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return BeautifulSoup(resp.text, "html.parser")

    def get_content_soup(self, url: str):
        """
        Fetch `url`. If it's a WARP viewer wrapper page (containing a
        <iframe id="pywb-frame"> rather than the real archived content),
        follow that iframe's src to fetch the actual content instead.

        Returns: (soup, resolved_url) where resolved_url is whichever URL
        actually held the content (use this as the base for resolving any
        relative links found within it).
        """
        soup = self.get_soup(url)
        iframe = soup.find("iframe", id="pywb-frame")
        if iframe is not None and iframe.get("src"):
            inner_url = urljoin(url, iframe["src"])
            inner_soup = self.get_soup(inner_url)
            return inner_soup, inner_url
        return soup, url

    def sleep(self):
        # add jitter so requests aren't spaced at a suspiciously exact interval
        time.sleep(self.request_delay_seconds + random.uniform(0, 1.5))

    def download_pdf(self, url: str, dest_folder: Path):
        dest_folder = Path(dest_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)
        filename = Path(urlparse(url).path).name
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"
        dest_path = dest_folder / filename

        if not dest_path.exists():
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            dest_path.write_bytes(resp.content)
            print(f"    saved: {filename}")
        else:
            print(f"    skip (already downloaded): {filename}")
        return dest_path

    @staticmethod
    def extract_pdf_text(pdf_path: Path) -> str:
        """Extract all text from a downloaded PDF file, page by page."""
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)

    @staticmethod
    def extract_speech_text(soup: BeautifulSoup) -> str:
        """
        Pull the actual speech/statement text out of a MOFA archive page,
        stripping header/nav/footer boilerplate. These pages consistently
        put the real content inside #maincontents (same container we've
        seen on the archive listing and FM sub-pages), so this targets
        that; falls back to <body> text if #maincontents isn't found.
        """
        container = soup.find(id="maincontents") or soup.find("body") or soup
        # Drop script/style tags so their contents don't leak into the text
        for tag in container.find_all(["script", "style"]):
            tag.decompose()
        text = container.get_text(separator="\n", strip=True)
        # Collapse runs of blank lines left behind by stripped elements
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def download_text(self, url: str, dest_folder: Path):
        """
        Fetch a non-PDF speech page and save its extracted text content as
        a .txt file (named after the last path segment of the URL).
        """
        dest_folder = Path(dest_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)
        filename = Path(urlparse(url).path).stem + ".txt"
        dest_path = dest_folder / filename

        if dest_path.exists():
            print(f"    skip (already downloaded): {filename}")
            return dest_path

        soup = self.get_soup(url)
        text = self.extract_speech_text(soup)
        dest_path.write_text(text, encoding="utf-8")
        print(f"    saved: {filename}")
        return dest_path


class LinkParser:
    """Finds FM sub-page links and PDF links within a page's HTML."""

    def __init__(self, stop_name: str = "koumura"):
        self.stop_name = stop_name

    @staticmethod
    def is_fm_subpage_link(href: str) -> bool:
        """
        Matches links to individual FM statement pages, e.g.:
          .../announce/fm/t_kono.html
          .../announce/fm/koumura/index.html
          .../announce/fm/koumura/index2.html
        Excludes only the literal top-level .../fm/index.html and
        .../fm/archive.html (no subfolder) -- NOT "<name>/index.html",
        since many real FM sub-pages are themselves named that way
        (aso/index.html, kawaguchi/index.html, koumura/index.html, etc).
        """
        m = re.search(r"/announce/fm/([^/]+(?:/[^/]+)?)\.html?$", href, re.IGNORECASE)
        if not m:
            return False
        tail = m.group(1).lower()
        # only exclude when there's NO subfolder (tail is exactly "index"
        # or "archive"), i.e. the literal top-level pages themselves
        return tail not in ("index", "archive")

    def find_fm_subpage_links(self, soup: BeautifulSoup, base_url: str):
        """Return list of (absolute_url, link_text) for FM sub-pages, in document order."""
        results = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not self.is_fm_subpage_link(href):
                continue
            abs_url = urljoin(base_url, href)
            # Normalize away WARP snapshot/timestamp differences so we dedupe
            # the same target page even if captured at slightly different times.
            key = re.sub(r"/\d+/\d+[a-z_]*/http", "/*/http", abs_url)
            if key in seen:
                continue
            seen.add(key)
            results.append((abs_url, a.get_text(strip=True)))
        return results

    @staticmethod
    def find_pdf_links(soup: BeautifulSoup, base_url: str):
        """Return list of absolute PDF URLs found on a page, in document order."""
        results = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.lower().split("?")[0].endswith(".pdf"):
                abs_url = urljoin(base_url, href)
                if abs_url not in seen:
                    seen.add(abs_url)
                    results.append(abs_url)
        return results

    @staticmethod
    def find_text_links(soup: BeautifulSoup, base_url: str):
        """
        Return list of absolute .html speech-text links found on a page
        (as opposed to PDFs), excluding nav-ish index/archive links.
        """
        results = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].lower().split("?")[0]
            if not href.endswith(".html"):
                continue
            if href.endswith("index.html") or href.endswith("archive.html"):
                continue
            if href.endswith(".pdf"):
                continue
            abs_url = urljoin(base_url, a["href"])
            if abs_url not in seen:
                seen.add(abs_url)
                results.append(abs_url)
        return results

    @staticmethod
    def guess_date(text: str):
        """
        Try to pull a date out of a chunk of surrounding text (e.g. a link's
        parent <li> or <tr>). Returns a datetime.date on success, else None.
        Uses dateutil's fuzzy parsing, which tolerates the date being
        embedded alongside a title rather than standing alone.
        """
        try:
            dt = date_parser.parse(text, fuzzy=True)
            return dt.date()
        except (ValueError, OverflowError):
            return None

    def find_speech_entries(self, soup: BeautifulSoup, base_url: str):
        """
        Find every speech link (PDF or .html text) on a page, along with
        its link text and a best-effort guessed date pulled from the
        surrounding context (parent <li>/<tr>/<p>/<div> text).

        Returns a list of dicts:
            {"url": str, "is_pdf": bool, "link_text": str, "date": date|None}
        """
        results = []
        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].lower().split("?")[0]
            is_pdf = href.endswith(".pdf")
            is_text = href.endswith(".html") and not href.endswith("index.html") and not href.endswith("archive.html")
            if not (is_pdf or is_text):
                continue

            abs_url = urljoin(base_url, a["href"])
            if abs_url in seen:
                continue
            seen.add(abs_url)

            link_text = a.get_text(strip=True)
            parent = a.find_parent(["li", "tr", "p", "div"])
            context_text = parent.get_text(" ", strip=True) if parent else link_text
            date = self.guess_date(context_text)

            results.append({
                "url": abs_url,
                "is_pdf": is_pdf,
                "link_text": link_text,
                "date": date,
            })
        return results

    @staticmethod
    def clean_minister_name(link_text: str) -> str:
        """Strip the 'Former Foreign Minister' / date-range boilerplate off an FM link's text."""
        name = re.sub(r"^Former Foreign Minister\s+", "", link_text, flags=re.IGNORECASE)
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name)  # trailing "(month year - month year)"
        return name.strip()


    @staticmethod
    def safe_folder_name(url: str, link_text: str) -> str:
        """Derive a folder name from the FM sub-page URL, e.g. '.../fm/t_kono.html' -> 't_kono'."""
        m = re.search(r"/announce/fm/([^/]+(?:/[^/]+)?)\.html?$", url, re.IGNORECASE)
        if m:
            return m.group(1).replace("/", "_")
        cleaned = re.sub(r"[^\w\-]+", "_", link_text.strip()) or "unknown"
        return cleaned


class MofaScraper:
    """
    Orchestrates scraping of MOFA Foreign Minister statement pages
    archived on NDL WARP.
    """

    INDEX_URL = "https://warp.ndl.go.jp/web/20211001134951/http://www.mofa.go.jp/announce/fm/index.html"
    ARCHIVE_URL = "https://warp.ndl.go.jp/web/20211001214459/http://www.mofa.go.jp/announce/fm/archive.html"

    def __init__(
        self,
        index_url: str = None,
        archive_url: str = None,
        stop_name: str = "koumura",
        stop_url_suffix: str = "koumura/index.html",
        stop_inclusive: bool = True,
        output_dir: Path = Path("mofa_pdfs"),
        request_delay_seconds: float = 3.0,
    ):
        self.index_url = index_url or self.INDEX_URL
        self.archive_url = archive_url or self.ARCHIVE_URL
        self.stop_name = stop_name
        # Koumura appears twice in the archive list (two separate terms as
        # FM): "koumura/index2.html" (2007-2008 term) comes first, then
        # "koumura/index.html" (his earlier term) comes later. Matching on
        # just the name "koumura" would stop at the FIRST occurrence, so we
        # match on this more specific URL suffix to stop at the correct one.
        self.stop_url_suffix = stop_url_suffix.lower()
        self.stop_inclusive = stop_inclusive
        self.output_dir = Path(output_dir)

        self.downloader = PdfDownloader(request_delay_seconds=request_delay_seconds)
        self.parser = LinkParser(stop_name=stop_name)

    def build_fm_page_sequence(self):
        """
        Combine FM sub-page links from the index and archive pages into a
        single ordered, de-duplicated sequence, then truncate at the
        stop-name page (e.g. Koumura).

        Returns: (index_soup, index_content_url, [(url, link_text), ...])
        """
        print(f"Fetching index page: {self.index_url}")
        index_soup, index_content_url = self.downloader.get_content_soup(self.index_url)
        self.downloader.sleep()

        print(f"Fetching archive page: {self.archive_url}")
        archive_soup, archive_content_url = self.downloader.get_content_soup(self.archive_url)
        self.downloader.sleep()

        index_links = self.parser.find_fm_subpage_links(index_soup, index_content_url)
        archive_links = self.parser.find_fm_subpage_links(archive_soup, archive_content_url)

        combined = []
        seen_keys = set()
        for url, text in index_links + archive_links:
            key = re.sub(r"/\d+/\d+[a-z_]*/http", "/*/http", url)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            combined.append((url, text))

        truncated = []
        for url, text in combined:
            truncated.append((url, text))
            if url.lower().endswith(self.stop_url_suffix):
                if not self.stop_inclusive:
                    truncated.pop()
                break

        self._index_soup = index_soup
        self._index_content_url = index_content_url
        self._fm_pages = truncated
        return index_soup, index_content_url, truncated

    def get_current_fm_pdfs(self, index_soup: BeautifulSoup = None, index_content_url: str = None):
        """PDFs linked directly on the top index page (current FM's speeches)."""
        soup = index_soup or getattr(self, "_index_soup", None)
        content_url = index_content_url or getattr(self, "_index_content_url", None)
        if soup is None or content_url is None:
            soup, content_url = self.downloader.get_content_soup(self.index_url)
        return self.parser.find_pdf_links(soup, content_url)

    def get_page_pdfs(self, page_url: str):
        """PDFs linked on a single FM sub-page."""
        soup, content_url = self.downloader.get_content_soup(page_url)
        return self.parser.find_pdf_links(soup, content_url)

    def get_page_text_links(self, page_url: str):
        """Non-PDF (.html) speech-text links on a single FM sub-page."""
        soup, content_url = self.downloader.get_content_soup(page_url)
        return self.parser.find_text_links(soup, content_url)

    def get_text_content(self, text_url: str) -> str:
        """Fetch a single non-PDF speech page and return its extracted text."""
        soup = self.downloader.get_soup(text_url)
        return self.downloader.extract_speech_text(soup)

    def debug_dump_links(self, url: str = None, limit: int = 60):
        """
        Print every <a href> found on a page (index page by default) so you
        can see the real structure. Follows the WARP viewer iframe if
        present, so this reflects the actual archived content.
        """
        target = url or self.index_url
        soup, content_url = self.downloader.get_content_soup(target)
        links = soup.find_all("a", href=True)
        print(f"Requested:  {target}")
        print(f"Content at: {content_url}")
        print(f"Total <a href> tags found: {len(links)}\n")
        for a in links[:limit]:
            text = a.get_text(strip=True)
            print(f"  href={a['href']!r:60s} text={text!r}")
        if len(links) > limit:
            print(f"  ... ({len(links) - limit} more not shown)")
        return links

    def build_dataframe(self, verbose: bool = True) -> pd.DataFrame:
        """
        Scrape everything (current FM + past FMs up to the stop point) and
        return a pandas DataFrame with one row per speech, containing:
            minister    - cleaned minister name
            date        - best-effort guessed date (may be None/NaT)
            text        - full text (PDF-extracted or scraped HTML text)
            source_url  - the speech's original URL
            source_type - "pdf" or "html"

        PDFs are downloaded to disk under self.output_dir (required, since
        a local file is needed to extract their text). HTML speech pages
        are only fetched and scraped into memory -- no .txt files are
        written for them, since the DataFrame is the only output needed.
        """
        index_soup, index_content_url, fm_pages = self.build_fm_page_sequence()

        rows = []

        def process_page(soup, content_url, minister_name, folder_name):
            entries = self.parser.find_speech_entries(soup, content_url)
            if verbose:
                print(f"=== {minister_name}: {len(entries)} speech(es) found ===")
            for entry in entries:
                url = entry["url"]
                try:
                    if entry["is_pdf"]:
                        pdf_path = self.downloader.download_pdf(url, self.output_dir / folder_name)
                        text = self.downloader.extract_pdf_text(pdf_path)
                        source_type = "pdf"
                    else:
                        text = self.get_text_content(url)
                        source_type = "html"
                except Exception as e:
                    print(f"    ERROR processing {url}: {e}", file=sys.stderr)
                    text = None
                    source_type = "pdf" if entry["is_pdf"] else "html"

                rows.append({
                    "minister": minister_name,
                    "date": entry["date"],
                    "text": text,
                    "source_url": url,
                    "source_type": source_type,
                })
                self.downloader.sleep()

        # 1. Current FM
        process_page(index_soup, index_content_url, "Current Foreign Minister", "current")

        # 2. Each past FM
        for page_url, link_text in fm_pages:
            minister_name = self.parser.clean_minister_name(link_text)
            folder_name = self.parser.safe_folder_name(page_url, link_text)
            try:
                page_soup, page_content_url = self.downloader.get_content_soup(page_url)
            except requests.RequestException as e:
                print(f"  ERROR fetching page for {minister_name}: {e}", file=sys.stderr)
                continue
            self.downloader.sleep()
            process_page(page_soup, page_content_url, minister_name, folder_name)

        df = pd.DataFrame(rows, columns=["minister", "date", "text", "source_url", "source_type"])
        return df


        """
        Full pipeline: build the FM page sequence, then download (or just
        print, if debug=True) PDFs from the current-FM index page and every
        past-FM sub-page up to the stop name.

        If include_text_links is True, also finds non-PDF speech-text
        (.html) links on each page and downloads their extracted text as
        .txt files into the same per-minister folder as the PDFs (or just
        lists the URLs, if debug=True).
        """
        index_soup, index_content_url, fm_pages = self.build_fm_page_sequence()

        print("\n=== FM sub-pages to process (in order) ===")
        for url, text in fm_pages:
            print(f"  {text!r:30s} -> {url}")
        print(f"Total FM sub-pages: {len(fm_pages)}\n")

        if not fm_pages:
            print(
                "WARNING: no FM sub-pages matched. The page structure may differ "
                "from what this script expects. Inspect the HTML and adjust "
                "LinkParser.is_fm_subpage_link().",
                file=sys.stderr,
            )

        # 1. Current FM's PDFs
        current_pdfs = self.get_current_fm_pdfs(index_soup, index_content_url)
        print(f"=== Current FM page: {len(current_pdfs)} PDF(s) found ===")
        for pdf_url in current_pdfs:
            print(f"  {pdf_url}")
        if not debug:
            for pdf_url in current_pdfs:
                self.downloader.download_pdf(pdf_url, self.output_dir / "current")
                self.downloader.sleep()
        print()

        # 2. Each past FM's sub-page
        for page_url, link_text in fm_pages:
            folder_name = self.parser.safe_folder_name(page_url, link_text)
            print(f"=== {folder_name} ({page_url}) ===")
            try:
                page_soup, page_content_url = self.downloader.get_content_soup(page_url)
            except requests.RequestException as e:
                print(f"  ERROR fetching page: {e}", file=sys.stderr)
                continue
            self.downloader.sleep()

            pdf_links = self.parser.find_pdf_links(page_soup, page_content_url)
            print(f"  {len(pdf_links)} PDF(s) found")
            for pdf_url in pdf_links:
                print(f"    {pdf_url}")

            if include_text_links:
                text_links = self.parser.find_text_links(page_soup, page_content_url)
                print(f"  {len(text_links)} text-only (.html) speech link(s) found")
                for text_url in text_links:
                    print(f"    {text_url}")
                if not debug:
                    for text_url in text_links:
                        try:
                            self.downloader.download_text(text_url, self.output_dir / folder_name)
                        except requests.RequestException as e:
                            print(f"    ERROR downloading {text_url}: {e}", file=sys.stderr)
                        self.downloader.sleep()

            if not debug:
                for pdf_url in pdf_links:
                    try:
                        self.downloader.download_pdf(pdf_url, self.output_dir / folder_name)
                    except requests.RequestException as e:
                        print(f"    ERROR downloading {pdf_url}: {e}", file=sys.stderr)
                    self.downloader.sleep()
            print()

        if debug:
            print("Debug mode: no files were downloaded. Re-run with run(debug=False) to download.")
        else:
            print(f"Done. PDFs saved under: {self.output_dir.resolve()}")