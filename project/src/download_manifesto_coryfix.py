"""
download_manifesto_coryfix.py
─────────────────────────────
Downloads data from the Manifesto Project API.

Two separate classes handle two separate jobs:
  • DownloadManifesto  – talks to the JSON API to get metadata and machine-readable text
  • ManifestoPDFSession – logs in to the website and downloads the original PDF files

Why two classes? The API (JSON endpoints) uses an API key for authentication.
The PDF file server (/down/originals/...) requires a real web login (email + password).
Keeping them separate makes each piece easier to understand and test on its own.

Required environment variables (put these in a .env file at the project root):
  MANIFESTO_API      – your API key from manifesto-project.wzb.eu/profile
  MANIFESTO_EMAIL    – the email you used to register on the website
  MANIFESTO_PASSWORD – your website password (only needed for PDF downloads)
"""

import argparse
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import requests
from dotenv import load_dotenv

# Load variables from the .env file into the environment so os.getenv() can read them.
load_dotenv()

# The Manifesto Project website root — used for PDF downloads.
_SITE_BASE = "https://manifesto-project.wzb.eu"


# ─────────────────────────────────────────────────────────────────────────────
# Class 1: API access (metadata + machine-readable text)
# ─────────────────────────────────────────────────────────────────────────────

class DownloadManifesto:
    """
    Wraps the Manifesto Project JSON API.

    Typical usage:
        downloader = DownloadManifesto()
        df = downloader.get_country_data("Japan")
        df, _ = downloader.get_metadata(df)
        df = downloader.get_texts(df[df["manifesto_id"].notna()])
    """

    def __init__(self, dataset_key="MPDS2024a", version="2024-1", api_key=None):
        self.dataset_key = dataset_key
        self.version = version
        # Use the passed key, or fall back to the environment variable.
        self.api_key = api_key or os.getenv("MANIFESTO_API")
        if not self.api_key:
            raise ValueError("Pass api_key= or set the MANIFESTO_API environment variable.")
        self.base_url = f"{_SITE_BASE}/api/v1/"

    # ── private helpers ───────────────────────────────────────────────────────

    def _api_call(self, endpoint, params=None):
        """Send a GET request to one API endpoint and return the parsed JSON."""
        params = params or {}
        params["api_key"] = self.api_key
        url = f"{self.base_url}{endpoint}?{urlencode(params, doseq=True)}"
        try:
            with urlopen(url, timeout=60) as resp:
                return json.load(resp)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API error {exc.code}: {body}") from exc

    @staticmethod
    def _make_key(party, date):
        """Build the '<party>_<date>' string the API uses as a document key."""
        return f"{int(party)}_{int(date)}"

    # ── public methods ────────────────────────────────────────────────────────

    def get_country_data(self, country):
        """
        Download the main dataset and return rows for one country.

        Each row is one party × election combination. Not all of them have
        machine-readable text — that is determined in get_metadata().
        """
        data = self._api_call("get_core", {"key": self.dataset_key})
        if not data:
            return None
        df = pd.DataFrame(data[1:], columns=data[0])
        df = df[df["countryname"] == country][
            ["countryname", "party", "partyname", "date"]
        ].copy()
        df["keys"] = df.apply(
            lambda row: self._make_key(row["party"], row["date"]), axis=1
        )
        return df

    def get_metadata(self, df):
        """
        Fetch corpus metadata for each row and merge it into the dataframe.

        Adds columns including:
          manifesto_id  – the key used to download machine-readable text
                          (None/NaN means only a scanned PDF exists, no text)
          url_original  – relative path to the original PDF on the website
          language      – language the manifesto was written in
          annotations   – True if the text has been hand-coded by researchers
          translation_en– True if an English translation is available
        """
        df = df.copy()
        raw = self._api_call(
            "metadata", {"keys[]": df["keys"].tolist(), "version": self.version}
        )
        if not raw:
            return df, None

        rows = []
        for item in raw.get("items", []):
            # The API sometimes returns the key under different field names.
            key = item.get("key")
            if not key and item.get("party") is not None:
                key = self._make_key(item["party"], item["date"])
            if not key and item.get("party_id") is not None:
                key = self._make_key(item["party_id"], item["election_date"])
            if not key:
                continue

            mid = item.get("manifesto_id")
            rows.append({
                "keys":           str(key),
                "manifesto_id":   str(mid) if mid else None,
                "annotations":    item.get("annotations"),
                "translation_en": item.get("translation_en"),
                "language":       item.get("language"),
                "title":          item.get("title"),
                "url_original":   item.get("url_original"),
            })

        if rows:
            df = df.merge(pd.DataFrame(rows), on="keys", how="left")
        else:
            df["manifesto_id"] = None

        return df, raw

    def get_texts(self, df, translation=None):
        """
        Download machine-readable text for every row that has a manifesto_id.

        Rows without text are dropped. The returned dataframe is indexed by
        (countryname, date) and has a 'text' column with the full document.

        Pass translation='en' to get English translations where available.
        """
        if "manifesto_id" not in df.columns:
            raise ValueError("Call get_metadata() first to add the manifesto_id column.")

        df = df.copy()
        valid_ids = df["manifesto_id"].dropna().unique().tolist()
        if not valid_ids:
            df["text"] = pd.NA
            return df

        params = {"keys[]": valid_ids, "version": self.version}
        if translation:
            params["translation"] = translation

        raw = self._api_call("texts_and_annotations", params)

        # The API returns a list of documents; each document is a list of
        # quasi-sentences. We join them into one string per document.
        texts = {}
        for item in (raw or {}).get("items", []):
            key = item.get("key")
            texts[key] = " ".join(
                s.get("text", "") for s in item.get("items", [])
            )

        df["text"] = df["manifesto_id"].map(texts)
        return df.dropna(subset=["text"]).set_index(["countryname", "date"])


# ─────────────────────────────────────────────────────────────────────────────
# Class 2: PDF downloads (requires web login)
# ─────────────────────────────────────────────────────────────────────────────

class ManifestoPDFSession:
    """
    Logs in to the Manifesto Project website and downloads original PDF files.

    Why is this separate from DownloadManifesto?
    The API uses an API key for auth. The PDF file server (/down/originals/...)
    uses a browser session (cookie) that you only get after logging in with your
    email and password. This class handles that login and keeps the session alive
    across multiple PDF downloads.

    Usage:
        pdf_session = ManifestoPDFSession()
        pdf_session.login()
        df = pdf_session.download_pdfs(meta_df, dest_dir="japan_pdfs")
    """

    def __init__(self, email=None, password=None):
        self.email    = email    or os.getenv("MANIFESTO_EMAIL")
        self.password = password or os.getenv("MANIFESTO_PASSWORD")
        if not self.email or not self.password:
            raise ValueError(
                "Set MANIFESTO_EMAIL and MANIFESTO_PASSWORD in your .env file."
            )
        # requests.Session keeps cookies across requests, just like a browser does.
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

    def login(self):
        """
        Log in to the Manifesto Project website.

        Step 1: GET the login page to get the CSRF token.
                (Rails apps include a hidden security token on every form to
                prevent cross-site request forgery. We have to send it back
                when we submit the login form.)
        Step 2: POST the login form with our credentials + that token.
        Step 3: The server responds by setting a session cookie. From here on,
                every request from self._session automatically sends that cookie,
                so the server knows we're logged in.
        """
        login_page = self._session.get(f"{_SITE_BASE}/login", timeout=10)
        # Extract the CSRF token from the hidden input in the login form.
        match = re.search(
            r'name="authenticity_token"[^>]+value="([^"]+)"', login_page.text
        )
        if not match:
            raise RuntimeError("Could not find CSRF token on the login page.")
        csrf_token = match.group(1)

        resp = self._session.post(
            f"{_SITE_BASE}/user_sessions",
            data={
                "utf8":                "✓",
                "authenticity_token":  csrf_token,
                "session[email]":      self.email,
                "session[password]":   self.password,
                "commit":              "login",
            },
            headers={"Referer": f"{_SITE_BASE}/login", "Origin": _SITE_BASE},
            timeout=15,
        )
        if resp.url.endswith("/login"):
            raise RuntimeError("Login failed — check your email and password.")
        print("Logged in to Manifesto Project website.")

    def download_pdfs(self, df, dest_dir="data/raw/pdfs"):
        """
        Download original PDFs for every row in df that has a url_original value.

        Requires:
          - df must have columns: party, date, url_original
            (call DownloadManifesto.get_metadata() to add these)
          - login() must have been called first

        Saves each PDF as '<party>_<date>.pdf' (or '<manifesto_id>.pdf' if
        available) inside dest_dir. Adds a 'pdf_path' column to the dataframe.

        Note: Add the dest_dir folder to your .gitignore — PDFs can be large
        and should not be committed to git. Each teammate runs this once to
        build their own local copy.
        """
        if "url_original" not in df.columns:
            raise ValueError("Call get_metadata() first to add the url_original column.")

        os.makedirs(dest_dir, exist_ok=True)
        df = df.copy()
        pdf_paths = []

        for _, row in df.iterrows():
            url_original = row.get("url_original")

            # Skip rows that have no original document.
            if not url_original or pd.isna(url_original):
                pdf_paths.append(None)
                continue

            # Build a sensible filename: prefer manifesto_id, fall back to party_date.
            mid = row.get("manifesto_id")
            filename = (
                mid if (mid and not pd.isna(mid))
                else f"{int(row['party'])}_{int(row['date'])}"
            )
            dest_path = os.path.join(dest_dir, f"{filename}.pdf")

            # Skip files we already downloaded (allows re-running without re-downloading).
            if os.path.exists(dest_path):
                pdf_paths.append(dest_path)
                continue

            # url_original is a relative path like /down/originals/2016-2/71220_2014.pdf
            url = f"{_SITE_BASE}/{url_original.lstrip('/')}"
            resp = self._session.get(url, timeout=60)

            # Check that we actually got a PDF (starts with the PDF magic bytes %PDF).
            if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                with open(dest_path, "wb") as f:
                    f.write(resp.content)
                pdf_paths.append(dest_path)
                print(f"  Downloaded: {filename}.pdf  ({len(resp.content) // 1024} KB)")
            else:
                print(f"  Skipped:    {filename}  (status {resp.status_code} — no PDF available)")
                pdf_paths.append(None)

        df["pdf_path"] = pdf_paths
        n_ok = sum(p is not None for p in pdf_paths)
        print(f"\nDone: {n_ok}/{len(df)} PDFs saved to '{dest_dir}/'")
        return df


# ─────────────────────────────────────────────────────────────────────────────
# Convenience function (combines both classes in one call)
# ─────────────────────────────────────────────────────────────────────────────

def download_country_manifestos(country, limit=None, translation=None, **kwargs):
    """
    One-liner helper: download machine-readable text for an entire country.

    Returns a dataframe indexed by (countryname, date) with a 'text' column.
    Only rows that have machine-readable text are included.
    """
    downloader = DownloadManifesto(**kwargs)
    country_data = downloader.get_country_data(country)
    if country_data is None or country_data.empty:
        return pd.DataFrame()

    country_data, _ = downloader.get_metadata(country_data)
    country_data = country_data[country_data["manifesto_id"].notna()]

    if translation == "en" and "translation_en" in country_data.columns:
        country_data = country_data[country_data["translation_en"].eq(True)]
    if limit is not None:
        country_data = country_data.head(limit)

    return downloader.get_texts(country_data, translation=translation)


# ─────────────────────────────────────────────────────────────────────────────
# Command-line interface
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download Manifesto Project texts and/or PDFs for one country."
    )
    parser.add_argument("--country",     default="Japan")
    parser.add_argument("--dataset-key", default="MPDS2024a")
    parser.add_argument("--version",     default="2024-1")
    parser.add_argument("--limit",       type=int, default=None)
    parser.add_argument("--translation", default=None)
    parser.add_argument("--pdfs",        action="store_true",
                        help="Download original PDFs instead of text.")
    parser.add_argument("--dest-dir",    default="data/raw/pdfs",
                        help="Where to save PDFs (only used with --pdfs).")
    args = parser.parse_args()

    downloader = DownloadManifesto(dataset_key=args.dataset_key, version=args.version)
    country_data = downloader.get_country_data(args.country)
    country_data, _ = downloader.get_metadata(country_data)

    if args.limit:
        country_data = country_data.head(args.limit)

    if args.pdfs:
        pdf_session = ManifestoPDFSession()
        pdf_session.login()
        result = pdf_session.download_pdfs(country_data, dest_dir=args.dest_dir)
        print(result[["manifesto_id", "partyname", "url_original", "pdf_path"]])
    else:
        text_data = country_data[country_data["manifesto_id"].notna()].copy()
        result = downloader.get_texts(text_data, translation=args.translation)
        print(result[["party", "partyname", "manifesto_id", "text"]].assign(
            text=result["text"].str.slice(0, 200)
        ))


if __name__ == "__main__":
    main()
