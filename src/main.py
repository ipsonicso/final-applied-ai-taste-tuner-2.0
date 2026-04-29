"""
Command line runner for the Music Recommender Simulation.

Three-mode genre similarity system:
1. Offline - songs.csv genres only (original behavior)
2. Enhanced - genre_cache.json genres (expanded set)
3. Online - any genre with Last.fm API
"""

from recommender import load_songs, recommend_songs, _get_component_scores, GenreSimilarityEngine
import json
import os
import random


def format_recommendation(song, score, user_prefs, components, genre_engine):
    lines = []

    # Compute match values
    mood_pct   = int(round((components['mood']  / 0.40) * 100))
    genre_pct  = int(round((components['genre'] / 0.30) * 100))
    energy_pct = int(round((1 - abs(song['energy'] - user_prefs['energy'])) * 100))
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_match = is_acoustic == user_likes_acoustic
    acoustic_pct = 100 if acoustic_match else 0
    pref_label = 'acoustic' if user_likes_acoustic else 'non-acoustic'

    # Title and score
    lines.append(f"\n{'=' * 70}")
    lines.append(f"{song['title']} - Final Score: {score:.2f}")
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
        genre_verb = "matches perfectly"
        genre_detail = f"{song['genre']} genre {genre_verb} your preference"
    else:
        genre_detail = f"'{song['genre']}' genre is {int(genre_similarity*100)}% similar to '{user_prefs['genre']}'"
    lines.append(f"  {genre_symbol} Genre:    {genre_detail} ({genre_pct}% match, +{components['genre']:.2f})")

    energy_symbol = '[+]' if energy_pct >= 85 else ('[~]' if energy_pct >= 70 else '[-]')
    energy_verb = "is aligned with" if energy_pct >= 85 else ("is close to" if energy_pct >= 70 else "is not aligned with")
    lines.append(f"  {energy_symbol} Energy:   energy level {energy_verb} your target {user_prefs['energy']:.2f} (proximity: {energy_pct}%, +{components['energy']:.2f})")

    acoustic_symbol = '[+]' if acoustic_match else '[-]'
    acoustic_verb = "has" if acoustic_match else "does not have"
    lines.append(f"  {acoustic_symbol} Acoustic: {acoustic_verb} the {pref_label} quality you prefer ({acoustic_pct}% match, +{components['acoustic']:.2f})")

    return '\n'.join(lines)


VALID_MOODS = ["happy", "chill", "intense", "relaxed", "moody", "focused"]
SAMPLE_PREFS = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}


def get_mode_selection() -> str:
    """
    Get user's similarity engine choice.
    Returns: "offline", "enhanced", or "online"
    """
    print("\n" + "CHOOSE SIMILARITY ENGINE".center(70, "="))
    print("  1. Legacy Offline:\tOriginal behavior - songs.csv genres only")
    print("  2. Enhanced Offline:\tExtended genres from genre dictionary")
    print("  3. Online (Last.fm):\tAny genre with Last.fm API")

    while True:
        choice = input("\nChoose an option (1, 2, or 3): ").strip()
        if choice == "1":
            print("  Mode: Offline (songs.csv)")
            return "offline"
        elif choice == "2":
            print("  Mode: Enhanced Offline (genre dictionary)")
            return "enhanced"
        elif choice == "3":
            print("  Mode: Online (Last.fm API)")
            return "online"
        print("  Please enter 1, 2, or 3.")


def get_songs_genres(songs: list) -> list:
    """Extract unique genres from songs.csv."""
    genres = sorted(set(song['genre'] for song in songs))
    return genres


def get_genre_input(valid_genres: list = None) -> str:
    """
    Get genre input with error handling.
    If valid_genres is provided, validates against it.
    Returns genre string or empty string to skip genre matching.
    """
    if valid_genres:
        print(f"\nAvailable genres: {', '.join(valid_genres)}")
    else:
        print("\nEnter any genre (or leave blank to skip):")

    while True:
        genre = input("Enter your favorite genre: ").strip().lower()

        # If valid_genres is None (online mode), accept anything or blank to skip
        if valid_genres is None:
            if not genre:
                print("  Skipping genre matching (will use other factors for recommendations)")
                return ""
            return genre

        # Validate against list
        if genre in valid_genres:
            return genre

        # Invalid genre - show options
        print(f"  Genre '{genre}' not found.")
        choice = input("  1) Try another genre, 2) Pick from list, 3) Skip genre matching: ").strip()

        if choice == "1":
            print(f"  Available genres: {', '.join(valid_genres)}")
            continue

        elif choice == "2":
            print(f"  Available genres: {', '.join(valid_genres)}")
            while True:
                genre = input("  Enter genre from list: ").strip().lower()
                if genre in valid_genres:
                    return genre
                print(f"    Invalid. Choose from: {', '.join(valid_genres)}")

        elif choice == "3":
            print("  Skipping genre matching (will use other factors for recommendations)")
            return ""

        else:
            print("  Invalid choice. Please enter 1, 2, or 3.")


def get_cache_genres() -> list:
    """Extract genres from genre_cache.json."""
    cache_file = "genre_cache.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            # Extract all genres that are keys (not metadata)
            genres = [g for g in cache.keys() if not g.startswith('_')]
            return sorted(genres)
        except:
            return []
    return []


def get_user_prefs_offline(songs: list) -> dict:
    """Build profile for Offline mode - genres from songs.csv."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile (skip to genre)")

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
        # Custom profile - get mood, energy, acoustic
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
                likes_acoustic = True
                break
            elif acoustic in ("no", "n"):
                likes_acoustic = False
                break
            print("  Please answer yes or no.")

    valid_genres = get_songs_genres(songs)
    genre = get_genre_input(valid_genres)

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic}


def get_user_prefs_enhanced() -> dict:
    """Build profile for Enhanced mode - genres from genre_cache.json."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile (skip to genre)")

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
        # Custom profile - get mood, energy, acoustic
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
                likes_acoustic = True
                break
            elif acoustic in ("no", "n"):
                likes_acoustic = False
                break
            print("  Please answer yes or no.")

    cache_genres = get_cache_genres()
    if cache_genres:
        genre = get_genre_input(cache_genres)
    else:
        print("\nNo genres in cache yet. Enter any genre to start building cache (or leave blank to skip):")
        genre = get_genre_input(None)  # Accept any input for online mode

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic}


def get_user_prefs_online() -> dict:
    """Build profile for Online mode - any genre allowed."""
    print("\n" + "BUILD YOUR PROFILE".center(70, "="))
    print("  1. Use sample profile")
    print("  2. Enter my own preferences")
    print("  3. Random profile (skip to genre)")

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
        # Custom profile - get mood, energy, acoustic
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
                likes_acoustic = True
                break
            elif acoustic in ("no", "n"):
                likes_acoustic = False
                break
            print("  Please answer yes or no.")

    genre = get_genre_input(None)  # Online mode accepts any genre

    return {"genre": genre, "mood": mood, "energy": energy, "likes_acoustic": likes_acoustic}


def get_online_engine(api_key: str = None) -> tuple[str, GenreSimilarityEngine]:
    """
    Get or prompt for Last.fm API key and create engine.
    Returns (engine_type, GenreSimilarityEngine) where engine_type is "online" or "enhanced"
    """
    if not api_key:
        api_key = input("\nEnter your Last.fm API key (or leave blank to skip): ").strip()

    if api_key:
        engine = GenreSimilarityEngine(use_lastfm=True, lastfm_api_key=api_key)
        print("  Using online mode (Last.fm API with caching)")
        return "online", engine
    else:
        print("  No API key provided. Falling back to enhanced offline mode.")
        engine = GenreSimilarityEngine(use_lastfm=False)
        return "enhanced", engine


def main() -> None:
    songs = load_songs("../data/songs.csv")

    # Step 1: Mode selection
    mode = get_mode_selection()

    # Step 2: Profile building based on mode
    if mode == "offline":
        user_prefs = get_user_prefs_offline(songs)
        engine_type, genre_engine = "offline", GenreSimilarityEngine(use_lastfm=False)
    elif mode == "enhanced":
        user_prefs = get_user_prefs_enhanced()
        engine_type, genre_engine = "enhanced", GenreSimilarityEngine(use_lastfm=False)
    else:  # online
        user_prefs = get_user_prefs_online()
        engine_type, genre_engine = get_online_engine()

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
