"""
Quick test: verify artist.getSimilar returns usable data
and that similar artists appear in songs2.csv

Usage: python src/test_artist_similar.py YOUR_API_KEY
"""

import sys
import csv
import requests
import os

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


def get_similar_artists(artist: str, api_key: str, limit: int = 20) -> list:
    params = {
        "method": "artist.getSimilar",
        "artist": artist,
        "limit": limit,
        "api_key": api_key,
        "format": "json",
    }
    r = requests.get(LASTFM_URL, params=params, timeout=8)
    r.raise_for_status()
    data = r.json()

    if "error" in data:
        print(f"  API error: {data.get('message')}")
        return []

    artists = data.get("similarartists", {}).get("artist", [])
    return [(a["name"], float(a["match"])) for a in artists]


def load_catalog_artists(csv_path: str) -> set:
    artists = set()
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            artists.add(row["artist"].lower())
    return artists


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/test_artist_similar.py YOUR_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1]
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "songs2.csv")
    catalog_artists = load_catalog_artists(csv_path)

    print(f"Catalog has {len(catalog_artists)} unique artists.")
    print("Checking which catalog artists have similar artists also in the catalog...\n")

    found_any = False
    for artist in sorted(catalog_artists):
        similar = get_similar_artists(artist, api_key, limit=30)
        matches = [(name, round(score, 3)) for name, score in similar if name.lower() in catalog_artists]

        if matches:
            found_any = True
            print(f"  '{artist}' → similar in catalog: {matches}")

    if not found_any:
        print("No cross-catalog artist similarity found. Catalog may be too small for this feature.")


if __name__ == "__main__":
    main()
