"""
Scraper for "The World and Japan" Database - Speeches of Prime Ministers
(Project Leader: TANAKA Akihiko)
Database of Japanese Politics and International Relations
National Graduate Institute for Policy Studies (GRIPS)
Institute for Advanced Studies on Asia (IASA), The University of Tokyo

Source: https://worldjpn.net/documents/indices/exdpm/index-ENG.html

Extracts: title, date, place, source, notes, body
Output: speeches.csv
"""

import re
import time
import csv
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class SpeechScraper:
    BASE_URL = "https://worldjpn.net"
    INDEX_URL = "https://worldjpn.net/documents/indices/exdpm/index-ENG.html"
    HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"}

    def __init__(self, delay=1.0):
        self.delay = delay

    # 1. Collect all English speech links from the index page

    def get_speech_links(self) -> list[dict]:
        resp = requests.get(self.INDEX_URL, headers=self.HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        entries = []
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue

            date_text = cells[-1].get_text(strip=True)

            eng_link = None
            for a in row.find_all("a"):
                if a.get_text(strip=True).lower() == "english":
                    href = a.get("href", "")
                    eng_link = urljoin(self.INDEX_URL, href)  # ← handles relative paths
                    break

            if not eng_link:
                continue

            title = cells[0].get_text(strip=True)
            entries.append({"index_title": title, "index_date": date_text, "url": eng_link})

        return entries

    # 2. Parse a single speech page

    def parse_field(self, text: str, tag: str) -> str:
        """Extract the value following a bracketed tag like [Title], [Date], etc."""
        pattern = rf"\[{tag}\](.*?)(?=\[\w|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def parse_speech_page(self, url: str) -> dict:
        """Fetch a speech page and extract structured fields."""
        resp = requests.get(url, headers=self.HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        raw = soup.get_text(separator="\n")

        start = raw.find("[Title]")
        if start == -1:
            return {
                "title": "", "date": "", "place": "",
                "source": "", "notes": "", "body": raw.strip(), "url": url
            }

        content = raw[start:]

        title  = self.parse_field(content, "Title")
        place  = self.parse_field(content, "Place")
        date   = self.parse_field(content, "Date")
        source = self.parse_field(content, "Source")
        notes  = self.parse_field(content, "Notes")
        body   = self.parse_field(content, "Full text")

        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        return {
            "title":  title,
            "date":   date,
            "place":  place,
            "source": source,
            "notes":  notes,
            "body":   body,
            "url":    url,
        }

    # 3. Main scrape loop

    def scrape_all(self) -> list[dict]:
        """Scrape all English speech pages and return list of record dicts."""
        print(f"Fetching index: {self.INDEX_URL}")
        links = self.get_speech_links()
        print(f"Found {len(links)} English speech links\n")

        records = []
        for i, entry in enumerate(links, 1):
            url = entry["url"]
            print(f"[{i}/{len(links)}] {url}")
            try:
                record = self.parse_speech_page(url)
                if not record["title"]:
                    record["title"] = entry["index_title"]
                if not record["date"]:
                    record["date"] = entry["index_date"]
                records.append(record)
            except Exception as e:
                print(f"  ERROR: {e}")
                records.append({
                    "title":  entry["index_title"],
                    "date":   entry["index_date"],
                    "place":  "",
                    "source": "",
                    "notes":  "",
                    "body":   "",
                    "url":    url,
                    "error":  str(e),
                })
            time.sleep(self.delay)

        return records

    # 4. Save output

    def save_csv(self, records: list[dict], path: str = "speeches.csv"):
        fields = ["title", "date", "place", "source", "notes", "body", "url"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        print(f"Saved CSV → {path}")


if __name__ == "__main__":
    scraper = SpeechScraper(delay=1.0)
    records = scraper.scrape_all()
    scraper.save_csv(records)
    scraper.save_json(records)
    print(f"\nDone. {len(records)} speeches scraped.")