from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
import json
import os
import requests

# Static genre similarity graph (hand-crafted weights)
GENRE_SIMILARITY_GRAPH = {
    "indie pop": {"pop": 0.80, "indie": 0.85, "electronic": 0.50, "rock": 0.45},
    "pop": {"indie pop": 0.80, "electronic": 0.45, "indie": 0.50},
    "indie": {"indie pop": 0.85, "pop": 0.50, "rock": 0.60, "electronic": 0.40},
    "rock": {"indie": 0.60, "indie pop": 0.45, "electronic": 0.35},
    "electronic": {"synthwave": 0.75, "ambient": 0.50, "pop": 0.45, "indie": 0.40, "indie pop": 0.50},
    "synthwave": {"electronic": 0.75, "ambient": 0.50, "lofi": 0.40},
    "ambient": {"lofi": 0.70, "synthwave": 0.50, "electronic": 0.50, "jazz": 0.40},
    "lofi": {"ambient": 0.70, "jazz": 0.45, "synthwave": 0.40},
    "jazz": {"lofi": 0.45, "ambient": 0.40},
}


class GenreSimilarityEngine:
    """
    Provides genre similarity scoring using either a static graph or Last.fm API.
    Caches Last.fm results to a JSON file to respect rate limits.
    Displays errors from Last.fm API to user instead of silently failing.
    """

    def __init__(
        self,
        use_lastfm: bool = False,
        lastfm_api_key: Optional[str] = None,
        cache_file: str = "genre_cache.json",
        catalog_songs: Optional[List[Dict]] = None,
        use_cached_similarity: bool = False,
        use_live_similarity: bool = False,
    ):
        self.use_lastfm = use_lastfm
        self.lastfm_api_key = lastfm_api_key
        self.cache_file = cache_file
        self.use_cached_similarity = use_cached_similarity
        self.use_live_similarity = use_live_similarity
        self.cache = self._load_cache()
        self.last_error = None
        self._genre_artist_map: Dict[str, List[str]] = {}
        if catalog_songs:
            self._build_genre_artist_map(catalog_songs)

    def _build_genre_artist_map(self, songs: List[Dict]) -> None:
        """Map genre -> unique artist names from catalog songs."""
        for song in songs:
            genre = song['genre'].lower()
            artist = song['artist']
            if genre not in self._genre_artist_map:
                self._genre_artist_map[genre] = []
            if artist not in self._genre_artist_map[genre]:
                self._genre_artist_map[genre].append(artist)

    def get_artist_similarity(self, favorite_artist: str, song_artist: str) -> float:
        """
        Returns Last.fm match score (0.0-1.0) between favorite_artist and song_artist.
        Reads from disk cache first; falls back to live API if online mode.
        Returns 1.0 for exact match, 0.0 if not found or not cached.
        """
        fav = favorite_artist.strip().lower()
        song = song_artist.strip().lower()

        if fav == song:
            return 1.0

        similar_map = self._fetch_similar_artists_cached(favorite_artist)
        return similar_map.get(song, 0.0)

    def _fetch_similar_artists_cached(self, artist: str) -> Dict[str, float]:
        """
        Returns {artist_name_lower: match_score} for the given artist.
        Reads from disk cache using 'artist_sim:<artist>' key.
        Falls back to live API if use_lastfm=True and not cached.
        """
        cache_key = f"artist_sim:{artist.strip().lower()}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        if not self.use_lastfm or not self.lastfm_api_key:
            return {}

        result = self._fetch_similar_artists(artist)
        self.cache[cache_key] = result
        self._save_cache()
        return result

    def _fetch_similar_artists(self, artist: str) -> Dict[str, float]:
        """Call artist.getSimilar and return {artist_name_lower: match_score}."""
        try:
            params = {
                "method": "artist.getSimilar",
                "artist": artist,
                "limit": 50,
                "api_key": self.lastfm_api_key,
                "format": "json",
            }
            response = requests.get("https://ws.audioscrobbler.com/2.0/", params=params, timeout=8)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_map = {10: "Invalid Last.fm API key", 6: "Artist not found", 29: "Rate limit exceeded"}
                self.last_error = error_map.get(data["error"], data.get("message", "Last.fm error"))
                return {}

            artists = data.get("similarartists", {}).get("artist", [])
            return {a["name"].lower(): float(a["match"]) for a in artists}

        except Exception as e:
            self.last_error = f"Last.fm API error: {str(e)}"
            return {}

    def _load_cache(self) -> Dict:
        """Load genre similarity cache from JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self):
        """Save genre similarity cache to JSON file."""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def get_similarity(self, user_genre: str, song_genre: str) -> float:
        """
        Get similarity score between two genres (0.0 to 1.0).
        Mode 1 (offline):  static graph only
        Mode 2 (cached):   artist-bridged score from cache, fallback to static graph
        Mode 3 (online):   artist-bridged score computed live, written to cache
        """
        if user_genre.lower() == song_genre.lower():
            return 1.0

        if self.use_live_similarity:
            return self.compute_artist_bridged_similarity(user_genre, song_genre)

        if self.use_cached_similarity:
            return self._get_cached_similarity(user_genre, song_genre)

        # Mode 1: static graph only
        static_score = self._get_static_similarity(user_genre, song_genre)
        return static_score if static_score is not None else 0.0

    def _get_cached_similarity(self, genre_a: str, genre_b: str) -> float:
        """Read artist-bridged similarity from cache. Falls back to static graph."""
        cache_key = f"{genre_a.lower()}_{genre_b.lower()}"
        val = self.cache.get(cache_key)
        if isinstance(val, (int, float)):
            return float(val)
        static_score = self._get_static_similarity(genre_a, genre_b)
        return static_score if static_score is not None else 0.0

    def compute_artist_bridged_similarity(self, genre_a: str, genre_b: str) -> float:
        """
        Compute artist-bridged genre similarity live via artist.getSimilar.
        Degree 1: genre_a artist -> similar artist in genre_b catalog  (score × 1.0)
        Degree 2: genre_a artist -> similar -> similar in genre_b      (score × match2 × 0.5)
        Takes the maximum score found. Writes result to cache.
        """
        cache_key = f"{genre_a.lower()}_{genre_b.lower()}"
        val = self.cache.get(cache_key)
        if isinstance(val, (int, float)):
            return float(val)

        genre_a_artists = self._genre_artist_map.get(genre_a.lower(), [])
        genre_b_artists_lower = {a.lower() for a in self._genre_artist_map.get(genre_b.lower(), [])}

        if not genre_a_artists or not genre_b_artists_lower:
            self.cache[cache_key] = 0.0
            self._save_cache()
            return 0.0

        best_score = 0.0
        print(f"  [Computing {genre_a} -> {genre_b} similarity...]", flush=True)

        # Degree 1: genre_a artist -> similar artist directly in genre_b catalog
        for artist_a in genre_a_artists:
            similar_to_a = self._fetch_similar_artists_cached(artist_a)
            for sim_name, match_score in similar_to_a.items():
                if sim_name in genre_b_artists_lower:
                    best_score = max(best_score, match_score)
            if best_score >= 0.9:
                break

        # Degree 2: only if degree-1 found NO connection at all
        if best_score == 0.0:
            for artist_a in genre_a_artists:
                similar_to_a = self._fetch_similar_artists_cached(artist_a)
                top10 = sorted(similar_to_a.items(), key=lambda x: x[1], reverse=True)[:10]
                for sim_artist, sim_score in top10:
                    similar_to_sim = self._fetch_similar_artists_cached(sim_artist)
                    for sim2_name, sim2_score in similar_to_sim.items():
                        if sim2_name in genre_b_artists_lower:
                            best_score = max(best_score, sim_score * sim2_score * 0.5)
                    if best_score >= 0.9:
                        break
                if best_score >= 0.9:
                    break

        best_score = min(1.0, max(0.0, round(best_score, 4)))
        self.cache[cache_key] = best_score
        self._save_cache()
        return best_score

    def _get_static_similarity(self, genre_a: str, genre_b: str) -> Optional[float]:
        """Check static graph for similarity score."""
        genre_a_lower = genre_a.lower()
        genre_b_lower = genre_b.lower()

        # Check if genre_a has genre_b in its adjacencies
        for g, similarities in GENRE_SIMILARITY_GRAPH.items():
            if g.lower() == genre_a_lower:
                for adj_genre, score in similarities.items():
                    if adj_genre.lower() == genre_b_lower:
                        return score

        return None

    def check_genre_exists_on_lastfm(self, genre: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a genre exists on Last.fm using tag.getInfo (cheap call).
        Returns (exists, error_message)
        If error_message is not None, the genre existence check failed.
        """
        if not self.lastfm_api_key:
            return False, "No Last.fm API key configured"

        try:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "tag.getInfo",
                "tag": genre,
                "api_key": self.lastfm_api_key,
                "format": "json"
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            data = response.json()

            # Check for Last.fm error response
            if "error" in data:
                error_code = data.get("error")
                error_message = data.get("message", f"Last.fm error code {error_code}")

                # Map error codes
                error_map = {
                    6: "Invalid parameters",
                    10: "Invalid Last.fm API key",
                    29: "Rate limit exceeded - please wait a moment and try again",
                }

                user_message = error_map.get(error_code, error_message)
                return False, user_message

            # A tag object is returned even for fake genres — check reach/taggings to confirm it's real
            tag_data = data.get("tag", {})
            reach = int(tag_data.get("reach", 0))
            taggings = int(tag_data.get("taggings", 0))
            if reach > 0 or taggings > 0:
                return True, None

            return False, None

        except requests.exceptions.Timeout:
            return False, "Last.fm API timeout - please check your internet connection"

        except requests.exceptions.HTTPError as e:
            return False, f"Last.fm API error: {e.response.status_code}"

        except Exception as e:
            return False, f"Last.fm API error: {str(e)}"

    def validate_genre_input(self, max_attempts: int = 2) -> str:
        """
        Interactive genre validation with API checking and intelligent retry logic.

        Flow:
        1. Prompt user for genre input
        2. Check cache first (skip API if cached result found)
        3. If not cached, query Last.fm API to validate genre
        4. On 1st validation failure: ask user to retry (4A) or skip (4B)
        5. On 2nd validation failure: auto-skip without asking (4B)

        Returns: validated genre string or empty string to skip genre matching
        """
        for attempt in range(1, max_attempts + 1):
            print(f"\n(Attempt {attempt}/{max_attempts})")
            genre = input("Enter your favorite genre (or leave blank to skip): ").strip().lower()

            # Allow blank to skip
            if not genre:
                print("  Skipping genre matching (will use other factors for recommendations)")
                return ""

            # Try to validate genre
            validation_result = self._validate_genre(genre)

            if validation_result["success"]:
                print(f"  Confirmed genre: '{genre}'")
                return genre

            # Validation failed
            if validation_result.get("error"):
                print(f"  Error: {validation_result['error']}")

            # Ask user what to do
            if attempt < max_attempts:
                # Not the last attempt - ask user
                choice = input(f"  Try another genre (a) or skip genre? (b): ").strip().lower()
                if choice == "b":
                    print("  Skipping genre matching (will use other factors for recommendations)")
                    return ""
                # If 'a' or anything else, loop to next attempt
            else:
                # Last attempt failed - auto-skip without asking
                print("  Skipping genre matching (will use other factors for recommendations)")
                return ""

        return ""

    def _validate_genre(self, genre: str) -> Dict:
        """
        Validate a genre against cache and Last.fm API.
        Returns {"success": bool, "error": optional_error_message}
        Cache key format: "exists:<genre>"  Value: True or False (plain bool)
        """
        cache_key = f"exists:{genre.lower()}"

        if cache_key in self.cache:
            val = self.cache[cache_key]
            if val is True:
                return {"success": True}
            if val is False:
                return {"success": False, "error": f"Genre '{genre}' not found on Last.fm"}

        if not self.use_lastfm:
            return {"success": False, "error": f"Genre '{genre}' not in cache"}

        exists, error = self.check_genre_exists_on_lastfm(genre)

        if error:
            # Don't cache transient errors (timeout, rate limit)
            return {"success": False, "error": error}

        self.cache[cache_key] = exists
        self._save_cache()

        if exists:
            return {"success": True}
        return {"success": False, "error": f"Genre '{genre}' not found on Last.fm"}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song], genre_engine: Optional['GenreSimilarityEngine'] = None):
        self.songs = songs
        # Use default offline engine if not provided
        self.genre_engine = genre_engine or GenreSimilarityEngine(use_lastfm=False)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """
        Recommend songs based on user profile.
        Returns top k songs sorted by recommendation score (highest first).
        """
        # Convert Song objects to dicts for scoring
        user_prefs = {
            'genre': user.favorite_genre,
            'mood': user.favorite_mood,
            'energy': user.target_energy,
            'likes_acoustic': user.likes_acoustic,
        }

        # Score each song
        scored_songs = []
        for song in self.songs:
            song_dict = {
                'energy': song.energy,
                'mood': song.mood,
                'genre': song.genre,
                'acousticness': song.acousticness,
            }
            score = _score_song(user_prefs, song_dict, self.genre_engine)
            scored_songs.append((song, score))

        # Sort by score descending
        scored_songs.sort(key=lambda x: x[1], reverse=True)

        # Return top k songs
        return [song for song, score in scored_songs[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """
        Generate a natural language explanation for why a song was recommended.
        """
        factors = []

        # Check mood match
        if song.mood == user.favorite_mood:
            factors.append(f"{song.mood} mood matches your preference")

        # Check genre match
        if song.genre == user.favorite_genre:
            factors.append(f"{song.genre} genre matches your preference")

        # Check energy proximity
        energy_distance = abs(song.energy - user.target_energy)
        if energy_distance < 0.15:
            factors.append(f"energy level is aligned with your target")

        # Check acoustic preference
        is_acoustic = song.acousticness > 0.5
        if is_acoustic == user.likes_acoustic:
            acoustic_pref = "acoustic" if user.likes_acoustic else "non-acoustic"
            factors.append(f"has the {acoustic_pref} quality you prefer")

        if factors:
            explanation = "Matches: " + ", ".join(factors)
        else:
            explanation = "Closest match based on audio characteristics"

        return explanation


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields to appropriate types
            song = {
                'id': int(row['id']),
                'title': row['title'],
                'artist': row['artist'],
                'genre': row['genre'],
                'mood': row['mood'],
                'energy': float(row['energy']),
                'tempo_bpm': float(row['tempo_bpm']),
                'valence': float(row['valence']),
                'danceability': float(row['danceability']),
                'acousticness': float(row['acousticness']),
            }
            songs.append(song)
    return songs


def _score_song(user_prefs: Dict, song: Dict, genre_engine: Optional['GenreSimilarityEngine'] = None) -> float:
    """
    Calculate recommendation score using mood-first metric.

    Without favorite_artist (modes 1 & 2 — unchanged):
        score = (mood × 0.40) + (genre × 0.30) + (energy × 0.20) + (acoustic × 0.10)

    With favorite_artist (mode 3 — online):
        score = (mood × 0.35) + (genre × 0.25) + (artist × 0.25) + (energy × 0.10) + (acoustic × 0.05)

    Returns a score between 0 and 1.0 (higher is better).
    """
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    favorite_artist = user_prefs.get('favorite_artist', '').strip()
    use_artist = bool(favorite_artist) and (genre_engine.use_lastfm or genre_engine.use_cached_similarity)

    if use_artist:
        # Online mode weights
        mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
        mood_score = mood_match * 0.35

        genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
        genre_score = genre_similarity * 0.25

        artist_similarity = genre_engine.get_artist_similarity(favorite_artist, song['artist'])
        artist_score = artist_similarity * 0.25

        energy_distance = abs(song['energy'] - user_prefs['energy'])
        energy_score = (1.0 - energy_distance) * 0.10

        is_acoustic = song['acousticness'] > 0.5
        acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0
        acoustic_score = acoustic_match * 0.05

        return mood_score + genre_score + artist_score + energy_score + acoustic_score

    else:
        # Offline/enhanced mode — original weights, untouched
        mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
        mood_score = mood_match * 0.40

        genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
        genre_score = genre_similarity * 0.30

        energy_distance = abs(song['energy'] - user_prefs['energy'])
        energy_score = (1.0 - energy_distance) * 0.20

        is_acoustic = song['acousticness'] > 0.5
        acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0
        acoustic_score = acoustic_match * 0.10

        return mood_score + genre_score + energy_score + acoustic_score


def _get_component_scores(user_prefs: Dict, song: Dict, genre_engine: Optional['GenreSimilarityEngine'] = None) -> Dict:
    """
    Calculate individual component scores for explanation purposes.
    Returns dict with mood, genre, artist, energy, acoustic, and total scores.
    artist score is 0.0 in offline/enhanced modes.
    """
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    favorite_artist = user_prefs.get('favorite_artist', '').strip()
    use_artist = bool(favorite_artist) and (genre_engine.use_lastfm or genre_engine.use_cached_similarity)

    if use_artist:
        mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
        mood_score = mood_match * 0.35

        genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
        genre_score = genre_similarity * 0.25

        artist_similarity = genre_engine.get_artist_similarity(favorite_artist, song['artist'])
        artist_score = artist_similarity * 0.25

        energy_distance = abs(song['energy'] - user_prefs['energy'])
        energy_score = (1.0 - energy_distance) * 0.10

        is_acoustic = song['acousticness'] > 0.5
        acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0
        acoustic_score = acoustic_match * 0.05
    else:
        mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
        mood_score = mood_match * 0.40

        genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
        genre_score = genre_similarity * 0.30

        artist_score = 0.0

        energy_distance = abs(song['energy'] - user_prefs['energy'])
        energy_score = (1.0 - energy_distance) * 0.20

        is_acoustic = song['acousticness'] > 0.5
        acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0
        acoustic_score = acoustic_match * 0.10

    total_score = mood_score + genre_score + artist_score + energy_score + acoustic_score

    return {
        'mood': mood_score,
        'genre': genre_score,
        'artist': artist_score,
        'energy': energy_score,
        'acoustic': acoustic_score,
        'total': total_score,
    }


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, genre_engine: Optional['GenreSimilarityEngine'] = None) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    # Score all songs
    scored_songs = []
    for song in songs:
        score = _score_song(user_prefs, song, genre_engine)
        explanation = _explain_score(user_prefs, song, score, genre_engine)
        scored_songs.append((song, score, explanation))

    # Sort by score descending (highest first)
    scored_songs.sort(key=lambda x: x[1], reverse=True)

    # Return top k
    return scored_songs[:k]


def _explain_score(user_prefs: Dict, song: Dict, score: float, genre_engine: Optional['GenreSimilarityEngine'] = None) -> str:
    """Generate natural language explanation with component scores in bold parentheses."""
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    components = _get_component_scores(user_prefs, song, genre_engine)
    factors = []

    # Check mood match
    if song['mood'] == user_prefs['mood']:
        factors.append(f"{song['mood']} mood matches (mood: {components['mood']:.2f})")

    # Check genre similarity
    genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
    if genre_similarity > 0:
        genre_pct = int(round(genre_similarity * 100))
        if genre_similarity == 1.0:
            factors.append(f"{song['genre']} genre matches perfectly (genre: {components['genre']:.2f})")
        else:
            factors.append(f"{song['genre']} is {genre_pct}% similar to {user_prefs['genre']} (genre: {components['genre']:.2f})")

    # Check energy proximity
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    if energy_distance < 0.15:
        factors.append(f"energy level is close to your preference (energy: {components['energy']:.2f})")

    # Check acoustic preference
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    if is_acoustic == user_likes_acoustic:
        acoustic_pref = "acoustic" if user_likes_acoustic else "non-acoustic"
        factors.append(f"is {acoustic_pref} as you prefer (acoustic: {components['acoustic']:.2f})")

    if factors:
        explanation = "Because " + ", ".join(factors)
    else:
        explanation = "Closest match based on audio characteristics"

    return explanation
