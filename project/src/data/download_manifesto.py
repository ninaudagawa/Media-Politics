import argparse
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


class DownloadManifesto:
    def __init__(self, dataset_key="MPDS2024a", version="2024-1", api_key=None):
        self.dataset_key = dataset_key
        self.version = version
        self.api_key = api_key or os.getenv("MANIFESTO_API")
        if not self.api_key:
            raise ValueError("Pass api_key or set the MANIFESTO_API environment variable.")
        self.base_url = "https://manifesto-project.wzb.eu/api/v1/"

    def _api_call(self, endpoint, params=None):
        """Make an API call and return the JSON response."""
        params = params or {}
        params["api_key"] = self.api_key
        query_string = urlencode(params, doseq=True)
        url = f"{self.base_url}{endpoint}?{query_string}"
        try:
            with urlopen(url, timeout=60) as response:
                return json.load(response)
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Manifesto API request failed: {exc.code} {error_body}") from exc

    @staticmethod
    def _manifesto_key(party, date):
        return f"{int(party)}_{int(date)}"
    
    def get_country_data(self, country):
        """Get core data filtered by country with party-date keys."""
        data = self._api_call("get_core", {"key": self.dataset_key})
        if not data:
            return None
            
        df = pd.DataFrame(data[1:], columns=data[0])
        df = df[df['countryname'] == country][['countryname', 'party', 'partyname', 'date']].copy()
        df['keys'] = df.apply(lambda row: self._manifesto_key(row['party'], row['date']), axis=1)
        return df
    
    def get_metadata(self, df):
        """Get metadata and add corpus manifesto IDs to the dataframe."""
        df = df.copy()
        metadata = self._api_call("metadata", {"keys[]": df['keys'].tolist(), "version": self.version})
        if not metadata:
            return df, None

        metadata_rows = []
        for item in metadata.get('items', []):
            manifesto_id = item.get("manifesto_id")

            core_key = item.get("key")
            if not core_key and item.get("party") is not None and item.get("date") is not None:
                core_key = self._manifesto_key(item["party"], item["date"])
            if not core_key and item.get("party_id") is not None and item.get("election_date") is not None:
                core_key = self._manifesto_key(item["party_id"], item["election_date"])

            if core_key:
                metadata_rows.append(
                    {
                        "keys": str(core_key),
                        "manifesto_id": str(manifesto_id) if manifesto_id else None,
                        "annotations": item.get("annotations"),
                        "translation_en": item.get("translation_en"),
                        "language": item.get("language"),
                        "title": item.get("title"),
                    }
                )

        if metadata_rows:
            df = df.merge(pd.DataFrame(metadata_rows), on="keys", how="left")
        else:
            df["manifesto_id"] = None
        
        return df, metadata
    
    def get_texts(self, df, translation=None):
        """Get texts and merge with dataframe (requires manifesto_id column)."""
        if 'manifesto_id' not in df.columns:
            raise ValueError("DataFrame must have 'manifesto_id' column. Call get_metadata() first.")
            
        df = df.copy()
        valid_ids = [mid for mid in df['manifesto_id'].dropna().unique()]
        if not valid_ids:
            df["text"] = pd.NA
            return df

        params = {"keys[]": valid_ids, "version": self.version}
        if translation:
            params["translation"] = translation

        texts_data = self._api_call("texts_and_annotations", params)
        
        texts = {}
        if texts_data:
            for item in texts_data.get('items', []):
                key = item.get('key')
                text_items = item.get('items', [])
                texts[key] = ' '.join(text_item.get('text', '') for text_item in text_items)
        
        df['text'] = df['manifesto_id'].map(texts)
        return df.dropna(subset=["text"]).set_index(['countryname', 'date'])


def download_country_manifestos(country, limit=None, translation=None, **kwargs):
    """Download manifesto text rows for one country."""
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


def main():
    parser = argparse.ArgumentParser(description="Download Manifesto Project texts for one country.")
    parser.add_argument("--country", default="Japan")
    parser.add_argument("--dataset-key", default="MPDS2024a")
    parser.add_argument("--version", default="2024-1")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--translation", default=None)
    args = parser.parse_args()

    data = download_country_manifestos(
        args.country,
        limit=args.limit,
        translation=args.translation,
        dataset_key=args.dataset_key,
        version=args.version,
    )
    preview_cols = ["party", "partyname", "manifesto_id", "text"]
    print(data[preview_cols].assign(text=data["text"].str.slice(0, 200)))


if __name__ == "__main__":
    main()
