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

    def __init__(self, use_lastfm: bool = False, lastfm_api_key: Optional[str] = None, cache_file: str = "genre_cache.json"):
        self.use_lastfm = use_lastfm
        self.lastfm_api_key = lastfm_api_key
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.last_error = None  # Track errors to display to user

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
        Returns 1.0 if genres are identical.
        Errors are cached and logged but don't crash the system.
        """
        # Exact match
        if user_genre.lower() == song_genre.lower():
            return 1.0

        # Try static graph first (always fast, no API call)
        static_score = self._get_static_similarity(user_genre, song_genre)
        if static_score is not None:
            return static_score

        # Fall back to Last.fm if online mode and not in static graph
        if self.use_lastfm and self.lastfm_api_key:
            score, error = self._get_lastfm_similarity(user_genre, song_genre)
            if error:
                self.last_error = error
            return score

        # Default: 0.0 if not found
        return 0.0

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

    def _get_lastfm_similarity(self, genre_a: str, genre_b: str) -> Tuple[float, Optional[str]]:
        """
        Query Last.fm API to find similarity between genres.
        Returns (similarity_score, error_message)
        If error_message is not None, similarity_score should be ignored.
        """
        cache_key = f"{genre_a.lower()}_{genre_b.lower()}"

        # Check cache first
        if cache_key in self.cache:
            result = self.cache[cache_key]
            if isinstance(result, dict) and "error" in result:
                return 0.0, result["error"]
            if isinstance(result, (int, float)):
                return float(result), None
            return 0.0, None

        # Query Last.fm for top artists of each genre, then score by overlap.
        # Replaces tag.getSimilar which is deprecated and returns empty results.
        def _fetch_top_artists(tag: str) -> Tuple[set, Optional[str]]:
            url = "https://ws.audioscrobbler.com/2.0/"
            params = {
                "method": "tag.getTopArtists",
                "tag": tag,
                "limit": 30,
                "api_key": self.lastfm_api_key,
                "format": "json"
            }
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                error_code = data.get("error")
                error_map = {
                    6: "Invalid parameters",
                    10: "Invalid Last.fm API key",
                    29: "Rate limit exceeded - please wait a moment and try again",
                }
                msg = error_map.get(error_code, data.get("message", f"Last.fm error code {error_code}"))
                return set(), msg

            artists = data.get("topartists", {}).get("artist", [])
            return {a["name"].lower() for a in artists}, None

        try:
            artists_a, err = _fetch_top_artists(genre_a)
            if err:
                self.cache[cache_key] = {"error": err}
                self._save_cache()
                return 0.0, err

            artists_b, err = _fetch_top_artists(genre_b)
            if err:
                self.cache[cache_key] = {"error": err}
                self._save_cache()
                return 0.0, err

            if not artists_a or not artists_b:
                self.cache[cache_key] = 0.0
                self._save_cache()
                return 0.0, None

            # Jaccard similarity: overlap / union
            overlap = len(artists_a & artists_b)
            union = len(artists_a | artists_b)
            similarity_score = round(overlap / union, 4) if union > 0 else 0.0

            self.cache[cache_key] = similarity_score
            self._save_cache()
            return similarity_score, None

        except requests.exceptions.Timeout:
            timeout_msg = "Last.fm API timeout - please check your internet connection"
            self.cache[cache_key] = {"error": timeout_msg}
            self._save_cache()
            return 0.0, timeout_msg

        except requests.exceptions.HTTPError as e:
            http_msg = f"Last.fm API error: {e.response.status_code}"
            self.cache[cache_key] = {"error": http_msg}
            self._save_cache()
            return 0.0, http_msg

        except Exception as e:
            generic_msg = f"Last.fm API error: {str(e)}"
            self.cache[cache_key] = {"error": generic_msg}
            self._save_cache()
            return 0.0, generic_msg

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

            # If tag data exists, the genre is valid on Last.fm
            if "tag" in data:
                return True, None

            return False, None

        except requests.exceptions.Timeout:
            return False, "Last.fm API timeout - please check your internet connection"

        except requests.exceptions.HTTPError as e:
            return False, f"Last.fm API error: {e.response.status_code}"

        except Exception as e:
            return False, f"Last.fm API error: {str(e)}"


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

    score = (mood_match × 0.40) +
            (genre_similarity × 0.30) +
            (1 - |energy_distance| × 0.20) +
            (acoustic_match × 0.10)

    Returns a score between 0 and 1.0 (higher is better).
    """
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    # Mood match (0.40 weight) - primary filter
    mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
    mood_score = mood_match * 0.40

    # Genre similarity (0.30 weight) - now supports adjacent genres
    genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
    genre_score = genre_similarity * 0.30

    # Energy distance (0.20 weight) - fine-tuning
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    energy_score = (1.0 - energy_distance) * 0.20

    # Acoustic match (0.10 weight) - tiebreaker
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_match = 1.0 if is_acoustic == user_likes_acoustic else 0.0
    acoustic_score = acoustic_match * 0.10

    return mood_score + genre_score + energy_score + acoustic_score


def _get_component_scores(user_prefs: Dict, song: Dict, genre_engine: Optional['GenreSimilarityEngine'] = None) -> Dict:
    """
    Calculate individual component scores for explanation purposes.
    Returns dict with mood, genre, energy, acoustic, and total scores.
    """
    if genre_engine is None:
        genre_engine = GenreSimilarityEngine(use_lastfm=False)

    # Mood match (0.40 weight)
    mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
    mood_score = mood_match * 0.40

    # Genre similarity (0.30 weight)
    genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
    genre_score = genre_similarity * 0.30

    # Energy distance (0.20 weight)
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    energy_score = (1.0 - energy_distance) * 0.20

    # Acoustic match (0.10 weight)
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_match = 1.0 if is_acoustic == user_likes_acoustic else 0.0
    acoustic_score = acoustic_match * 0.10

    total_score = mood_score + genre_score + energy_score + acoustic_score

    return {
        'mood': mood_score,
        'genre': genre_score,
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
