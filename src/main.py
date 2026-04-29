"""
Command line runner for the Music Recommender Simulation.

Three-mode genre similarity system:
1. Offline    - static genre graph only (original behavior, untouched)
2. Cached     - artist-bridged genre similarity from cache (no live API calls)
3. Online     - live Last.fm API for genre similarity and artist scoring
"""

from recommender import load_songs, recommend_songs, _get_component_scores, GenreSimilarityEngine
import random


def format_recommendation(song, score, user_prefs, components, genre_engine):
    lines = []

    favorite_artist = user_prefs.get('favorite_artist', '').strip()
    use_artist = bool(favorite_artist) and (genre_engine.use_lastfm or genre_engine.use_cached_similarity)

    # Compute match values — use correct weight denominators per mode
    mood_denom  = 0.35 if use_artist else 0.40
    genre_denom = 0.25 if use_artist else 0.30
    mood_pct    = int(round((components['mood']  / mood_denom) * 100))
    genre_pct   = int(round((components['genre'] / genre_denom) * 100))
    energy_pct  = int(round((1 - abs(song['energy'] - user_prefs['energy'])) * 100))
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_match = is_acoustic == user_likes_acoustic
    acoustic_pct = 100 if acoustic_match else 0
    pref_label = 'acoustic' if user_likes_acoustic else 'non-acoustic'

    # Title and score
    lines.append(f"\n{'=' * 70}")
    lines.append(f"{song['title']} - {song['artist']} | Final Score: {score:.2f}")
    lines.append('=' * 70)

    # Summary
    matched = []
    if components['mood'] > 0:
        matched.append(f"{song['mood']} mood")
    if components['genre'] > 0:
        genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
        if genre_similarity == 1.0:
            matched.append(f"{song['genre']} genre")
        else:
            matched.append(f"{song['genre']} genre ({int(genre_similarity*100)}% match)")
    if use_artist and components['artist'] > 0:
        artist_sim = genre_engine.get_artist_similarity(favorite_artist, song['artist'])
        matched.append(f"similar to {favorite_artist} ({int(artist_sim*100)}%)")
    if energy_pct >= 85:
        matched.append("well-matched energy")
    elif energy_pct >= 70:
        matched.append("close energy match")
    if acoustic_match:
        matched.append(f"{pref_label} quality")

    summary = f"Strong match: {', '.join(matched)}" if matched else "Best available match based on weighted preferences"
    lines.append(f"\nSummary: {summary}")

    # Detailed breakdown
    lines.append("\nDetailed Analysis:")

    mood_symbol = '[+]' if components['mood'] > 0 else '[-]'
    mood_verb = "matches" if components['mood'] > 0 else "does not match"
    lines.append(f"  {mood_symbol} Mood:     '{song['mood']}' mood {mood_verb} your preference '{user_prefs['mood']}' ({mood_pct}% match, +{components['mood']:.2f})")

    genre_symbol = '[+]' if components['genre'] > 0 else '[-]'
    genre_similarity = genre_engine.get_similarity(user_prefs['genre'], song['genre'])
    if genre_similarity == 1.0:
        genre_detail = f"{song['genre']} genre matches perfectly your preference"
    else:
        genre_detail = f"'{song['genre']}' genre is {int(genre_similarity*100)}% similar to '{user_prefs['genre']}'"
    lines.append(f"  {genre_symbol} Genre:    {genre_detail} ({genre_pct}% match, +{components['genre']:.2f})")

    if use_artist:
        artist_sim = genre_engine.get_artist_similarity(favorite_artist, song['artist'])
        artist_pct = int(artist_sim * 100)
        artist_symbol = '[+]' if artist_sim > 0 else '[-]'
        if artist_sim == 1.0:
            artist_detail = f"'{song['artist']}' is your favorite artist"
        elif artist_sim > 0:
            artist_detail = f"'{song['artist']}' is {artist_pct}% similar to '{favorite_artist}' (via Last.fm)"
        else:
            artist_detail = f"'{song['artist']}' is not similar to '{favorite_artist}'"
        lines.append(f"  {artist_symbol} Artist:   {artist_detail} (+{components['artist']:.2f})")

    energy_symbol = '[+]' if energy_pct >= 85 else ('[~]' if energy_pct >= 70 else '[-]')
    energy_verb = "is aligned with" if energy_pct >= 85 else ("is close to" if energy_pct >= 70 else "is not aligned with")
    lines.append(f"  {energy_symbol} Energy:   energy level {energy_verb} your target {user_prefs['energy']:.2f} (proximity: {energy_pct}%, +{components['energy']:.2f})")

    acoustic_symbol = '[+]' if acoustic_match else '[-]'
    acoustic_verb = "has" if acoustic_match else "does not have"
    lines.append(f"  {acoustic_symbol} Acoustic: {acoustic_verb} the {pref_label} quality you prefer ({acoustic_pct}% match, +{components['acoustic']:.2f})")

    return '\n'.join(lines)


VALID_MOODS = ["happy", "chill", "intense", "relaxed", "moody", "focused"]
SAMPLE_PREFS = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False, "favorite_artist": ""}


def get_mode_selection() -> str:
    """
    Get user's similarity engine choice.
    Returns: "offline", "cached", or "online"
    """
    print("\n" + "CHOOSE SIMILARITY ENGINE".center(70, "="))
    print("  1. Offline     — static genre graph only (original)")
    print("  2. Cached      — artist-bridged similarity from cache (no API calls)")
    print("  3. Online/Live — live Last.fm API for genre + artist scoring")

    while True:
        choice = input("\nChoose an option (1, 2, or 3): ").strip()
        if choice == "1":
            print("  Mode: Offline")
            return "offline"
        elif choice == "2":
            print("  Mode: Cached")
            return "cached"
        elif choice == "3":
            print("  Mode: Online/Live")
            return "online"
        print("  Please enter 1, 2, or 3.")


def get_songs_genres(songs: list) -> list:
    """Extract unique genres from catalog."""
    return sorted(set(song['genre'] for song in songs))


def get_genre_input(valid_genres: list) -> str:
    """
    Get genre input validated against catalog genres.
    Returns genre string or empty string to skip genre matching.
    """
    print(f"\nAvailable genres: {', '.join(valid_genres)}")

    while True:
        genre = input("Enter your favorite genre (or leave blank to skip): ").strip().lower()

        if not genre:
            print("  Skipping genre matching (will use other factors for recommendations)")
            return ""

        if genre in valid_genres:
            return genre

        print(f"  Genre '{genre}' not found.")
        choice = input("  1) Try another  2) Pick from list  3) Skip: ").strip()

        if choice == "2":
            while True:
                genre = input("  Enter genre from list: ").strip().lower()
                if genre in valid_genres:
                    return genre
                print(f"    Invalid. Choose from: {', '.join(valid_genres)}")
        elif choice == "3":
            print("  Skipping genre matching (will use other factors for recommendations)")
            return ""


def _collect_mood_energy_acoustic() -> tuple:
    """Shared helper: collect mood, energy, acoustic preference from user."""
    print(f"\nAvailable moods: {', '.join(VALID_MOODS)}")
    while True:
        mood = input("Enter your favorite mood: ").strip().lower()
        if mood in VALID_MOODS:
            break
        print(f"  Invalid mood. Choose from: {', '.join(VALID_MOODS)}")

    while True:
        try:
            energy = float(input("\nEnter your target energy level (0.0 = very calm, 1.0 = very intense): ").strip())
            if 0.0 <= energy <= 1.0:
                break
            print("  Please enter a value between 0.0 and 1.0.")
        except ValueError:
            print("  Please enter a number like 0.7.")

    while True:
        acoustic = input("\nDo you prefer acoustic songs? (yes/no): ").strip().lower()
        if acoustic in ("yes", "y"):
            return mood, energy, True
        elif acoustic in ("no", "n"):
            return mood, energy, False
        print("  Please answer yes or no.")


def get_user_prefs_offline(songs: list) -> dict:
    """Build profile for Offline mode — genres from catalog only."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile")

    choice = input("\nChoose an option (1, 2, or 3): ").strip()
    if choice == "1":
        print(f"  Using sample profile: {SAMPLE_PREFS}")
        return SAMPLE_PREFS
    elif choice == "3":
        mood = random.choice(VALID_MOODS)
        energy = round(random.uniform(0.0, 1.0), 1)
        likes_acoustic = random.choice([True, False])
        print(f"  Random profile: {mood} | energy {energy:.1f} | {'acoustic' if likes_acoustic else 'non-acoustic'}")
    else:
        mood, energy, likes_acoustic = _collect_mood_energy_acoustic()

    genre = get_genre_input(get_songs_genres(songs))
    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic, "favorite_artist": ""}


def get_user_prefs_cached(songs: list, genre_engine: 'GenreSimilarityEngine') -> dict:
    """Build profile for Cached mode — catalog genres, optional artist from cache."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile")

    choice = input("\nChoose an option (1, 2, or 3): ").strip()
    if choice == "1":
        print(f"  Using sample profile: {SAMPLE_PREFS}")
        return SAMPLE_PREFS
    elif choice == "3":
        mood = random.choice(VALID_MOODS)
        energy = round(random.uniform(0.0, 1.0), 1)
        likes_acoustic = random.choice([True, False])
        print(f"  Random profile: {mood} | energy {energy:.1f} | {'acoustic' if likes_acoustic else 'non-acoustic'}")
    else:
        mood, energy, likes_acoustic = _collect_mood_energy_acoustic()

    genre = get_genre_input(get_songs_genres(songs))

    print("\nArtist Similarity (optional):")
    print("  Note: only applies if artist data was cached by a prior Online/Live run.")
    favorite_artist = input("Enter a favorite artist (or leave blank to skip): ").strip()
    if favorite_artist:
        cache_key = f"artist_sim:{favorite_artist.lower()}"
        if cache_key in genre_engine.cache:
            print(f"  Found cached data for '{favorite_artist}' — artist similarity will apply.")
        else:
            print(f"  No cached data for '{favorite_artist}' — artist similarity will be skipped.")
            favorite_artist = ""

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic, "favorite_artist": favorite_artist}


def get_user_prefs_online(genre_engine: 'GenreSimilarityEngine') -> dict:
    """Build profile for Online/Live mode — any genre validated via Last.fm, live artist scoring."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile")

    choice = input("\nChoose an option (1, 2, or 3): ").strip()
    if choice == "1":
        print(f"  Using sample profile: {SAMPLE_PREFS}")
        return SAMPLE_PREFS
    elif choice == "3":
        mood = random.choice(VALID_MOODS)
        energy = round(random.uniform(0.0, 1.0), 1)
        likes_acoustic = random.choice([True, False])
        print(f"  Random profile: {mood} | energy {energy:.1f} | {'acoustic' if likes_acoustic else 'non-acoustic'}")
    else:
        mood, energy, likes_acoustic = _collect_mood_energy_acoustic()

    print("\nGenre Selection:")
    genre = genre_engine.validate_genre_input(max_attempts=2)

    print("\nArtist Similarity (optional):")
    favorite_artist = input("Enter a favorite artist for smarter recommendations (or leave blank to skip): ").strip()
    if favorite_artist:
        similar = genre_engine._fetch_similar_artists_cached(favorite_artist)
        if similar:
            print(f"  Using '{favorite_artist}' for live artist similarity scoring via Last.fm.")
        else:
            print(f"  Artist '{favorite_artist}' not found on Last.fm — skipping artist similarity.")
            favorite_artist = ""
    else:
        print("  Skipping artist similarity.")

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic, "favorite_artist": favorite_artist}


def get_api_key() -> str:
    """Prompt for Last.fm API key."""
    return input("\nEnter your Last.fm API key: ").strip()


def main() -> None:
    songs = load_songs("../data/songs2.csv")

    mode = get_mode_selection()

    if mode == "offline":
        genre_engine = GenreSimilarityEngine(use_lastfm=False)
        user_prefs = get_user_prefs_offline(songs)
        engine_type = "offline"

    elif mode == "cached":
        genre_engine = GenreSimilarityEngine(
            use_lastfm=False,
            catalog_songs=songs,
            use_cached_similarity=True,
        )
        user_prefs = get_user_prefs_cached(songs, genre_engine)
        engine_type = "cached"

    else:  # online
        api_key = get_api_key()
        if not api_key:
            print("  No API key provided. Falling back to Cached mode.")
            genre_engine = GenreSimilarityEngine(
                use_lastfm=False,
                catalog_songs=songs,
                use_cached_similarity=True,
            )
            user_prefs = get_user_prefs_cached(songs, genre_engine)
            engine_type = "cached"
        else:
            genre_engine = GenreSimilarityEngine(
                use_lastfm=True,
                lastfm_api_key=api_key,
                catalog_songs=songs,
                use_live_similarity=True,
            )
            user_prefs = get_user_prefs_online(genre_engine)
            engine_type = "online"

    recommendations = recommend_songs(user_prefs, songs, k=5, genre_engine=genre_engine)

    print("\n" + "TOP RECOMMENDATIONS".center(70, "="))
    print(f"Profile: {user_prefs['mood']} {user_prefs['genre']} | energy {user_prefs['energy']:.0%} | {'acoustic' if user_prefs['likes_acoustic'] else 'non-acoustic'}")
    print(f"Mode: {engine_type.upper()}")

    titles = "  ".join(f"{i}. {s['title']}" for i, (s, _, _) in enumerate(recommendations, 1))
    print(f"Results: {titles}")

    for song, score, _ in recommendations:
        components = _get_component_scores(user_prefs, song, genre_engine)
        print(format_recommendation(song, score, user_prefs, components, genre_engine))

    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    main()
