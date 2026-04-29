"""
fetch_songs.py

One-time script: pulls top tracks per genre from Last.fm tag.getTopTracks
and writes data/songs2.csv with estimated audio features.

Usage:
    python src/fetch_songs.py YOUR_API_KEY

Output: data/songs2.csv (same schema as songs.csv)
"""

import sys
import csv
import random
import requests

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"
TRACKS_PER_GENRE = 5

# Genres to fetch — must match GENRE_SIMILARITY_GRAPH keys in recommender.py
GENRES = ["pop", "indie pop", "indie", "rock", "electronic", "synthwave", "ambient", "lofi", "jazz"]

# Estimated audio feature ranges per genre: (min, max)
GENRE_FEATURES = {
    "pop":        {"energy": (0.70, 0.92), "tempo_bpm": (110, 135), "valence": (0.70, 0.90), "danceability": (0.70, 0.90), "acousticness": (0.05, 0.25), "moods": ["happy", "intense"]},
    "indie pop":  {"energy": (0.58, 0.80), "tempo_bpm": (105, 130), "valence": (0.62, 0.84), "danceability": (0.62, 0.82), "acousticness": (0.15, 0.42), "moods": ["happy", "chill"]},
    "indie":      {"energy": (0.44, 0.70), "tempo_bpm": (88, 120),  "valence": (0.52, 0.78), "danceability": (0.48, 0.70), "acousticness": (0.28, 0.65), "moods": ["relaxed", "moody"]},
    "rock":       {"energy": (0.74, 0.95), "tempo_bpm": (130, 160), "valence": (0.38, 0.65), "danceability": (0.52, 0.74), "acousticness": (0.04, 0.20), "moods": ["intense", "moody"]},
    "electronic": {"energy": (0.74, 0.93), "tempo_bpm": (120, 145), "valence": (0.48, 0.72), "danceability": (0.74, 0.92), "acousticness": (0.02, 0.14), "moods": ["intense", "focused"]},
    "synthwave":  {"energy": (0.64, 0.85), "tempo_bpm": (105, 125), "valence": (0.42, 0.64), "danceability": (0.62, 0.80), "acousticness": (0.06, 0.24), "moods": ["moody", "chill"]},
    "ambient":    {"energy": (0.18, 0.40), "tempo_bpm": (52, 75),   "valence": (0.52, 0.74), "danceability": (0.28, 0.50), "acousticness": (0.74, 0.96), "moods": ["chill", "relaxed"]},
    "lofi":       {"energy": (0.28, 0.50), "tempo_bpm": (68, 92),   "valence": (0.48, 0.70), "danceability": (0.48, 0.68), "acousticness": (0.58, 0.86), "moods": ["chill", "focused"]},
    "jazz":       {"energy": (0.32, 0.55), "tempo_bpm": (82, 112),  "valence": (0.62, 0.82), "danceability": (0.44, 0.65), "acousticness": (0.72, 0.94), "moods": ["relaxed", "chill"]},
}


def fetch_top_tracks(genre: str, api_key: str, limit: int) -> list:
    params = {
        "method": "tag.getTopTracks",
        "tag": genre,
        "limit": limit,
        "api_key": api_key,
        "format": "json",
    }
    try:
        response = requests.get(LASTFM_URL, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f"  Last.fm error for '{genre}': {data.get('message')}")
            return []

        tracks = data.get("tracks", {}).get("track", [])
        return [(t["name"], t["artist"]["name"]) for t in tracks]

    except Exception as e:
        print(f"  Request failed for '{genre}': {e}")
        return []


def estimate_features(genre: str) -> dict:
    f = GENRE_FEATURES[genre]

    def rand(key):
        lo, hi = f[key]
        return round(random.uniform(lo, hi), 2)

    return {
        "energy":       rand("energy"),
        "tempo_bpm":    round(random.uniform(*f["tempo_bpm"])),
        "valence":      rand("valence"),
        "danceability": rand("danceability"),
        "acousticness": rand("acousticness"),
        "mood":         random.choice(f["moods"]),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/fetch_songs.py YOUR_LASTFM_API_KEY")
        sys.exit(1)

    api_key = sys.argv[1]
    # Path relative to this script's location, works regardless of where you run from
    import os
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "songs2.csv")
    rows = []
    song_id = 1

    for genre in GENRES:
        print(f"Fetching top {TRACKS_PER_GENRE} tracks for '{genre}'...")
        tracks = fetch_top_tracks(genre, api_key, TRACKS_PER_GENRE)

        if not tracks:
            print(f"  No tracks returned for '{genre}', skipping.")
            continue

        for title, artist in tracks:
            features = estimate_features(genre)
            rows.append({
                "id":           song_id,
                "title":        title,
                "artist":       artist,
                "genre":        genre,
                "mood":         features["mood"],
                "energy":       features["energy"],
                "tempo_bpm":    features["tempo_bpm"],
                "valence":      features["valence"],
                "danceability": features["danceability"],
                "acousticness": features["acousticness"],
            })
            song_id += 1

    if not rows:
        print("No songs fetched. Check your API key.")
        sys.exit(1)

    fieldnames = ["id", "title", "artist", "genre", "mood", "energy", "tempo_bpm", "valence", "danceability", "acousticness"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} songs written to {output_path}")


if __name__ == "__main__":
    main()
