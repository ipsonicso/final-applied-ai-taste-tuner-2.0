"""
Comparison test (from week 7): Original mood-first vs. Genre-weighted recommendations
Shows how recommendations change when genre weight increases to 0.50
"""

from recommender import load_songs

def get_component_scores_original(user_prefs, song):
    """Original: mood 0.40, genre 0.30, energy 0.20, acoustic 0.10"""
    mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
    genre_match = 1.0 if song['genre'] == user_prefs['genre'] else 0.0
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    is_acoustic = song['acousticness'] > 0.5
    acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0

    return {
        'mood': mood_match * 0.40,
        'genre': genre_match * 0.30,
        'energy': (1.0 - energy_distance) * 0.20,
        'acoustic': acoustic_match * 0.10,
    }


def get_component_scores_genre_heavy(user_prefs, song):
    """Modified: mood 0.40, genre 0.50, energy 0.05, acoustic 0.05"""
    mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
    genre_match = 1.0 if song['genre'] == user_prefs['genre'] else 0.0
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    is_acoustic = song['acousticness'] > 0.5
    acoustic_match = 1.0 if is_acoustic == user_prefs.get('likes_acoustic', False) else 0.0

    return {
        'mood': mood_match * 0.40,
        'genre': genre_match * 0.50,
        'energy': (1.0 - energy_distance) * 0.05,
        'acoustic': acoustic_match * 0.05,
    }


def score_song(components_func, user_prefs, song):
    """Calculate total score from components"""
    components = components_func(user_prefs, song)
    return sum(components.values())


def compare_recommendations(test_name, user_prefs, songs):
    """Compare original vs. genre-heavy recommendations"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print(f"\nUser Profile:")
    print(f"  Genre: {user_prefs['genre']}")
    print(f"  Mood: {user_prefs['mood']}")
    print(f"  Energy: {user_prefs['energy']}")
    print(f"  Likes Acoustic: {user_prefs.get('likes_acoustic', False)}\n")

    # Score all songs with both methods
    scored_original = []
    scored_genre_heavy = []

    for song in songs:
        orig_score = score_song(get_component_scores_original, user_prefs, song)
        genre_score = score_song(get_component_scores_genre_heavy, user_prefs, song)

        scored_original.append((song, orig_score, get_component_scores_original(user_prefs, song)))
        scored_genre_heavy.append((song, genre_score, get_component_scores_genre_heavy(user_prefs, song)))

    # Sort both
    scored_original.sort(key=lambda x: x[1], reverse=True)
    scored_genre_heavy.sort(key=lambda x: x[1], reverse=True)

    # Display comparison
    print("ORIGINAL (Mood-First: 0.40 mood, 0.30 genre, 0.20 energy, 0.10 acoustic)")
    print("-" * 80)
    for i, (song, score, components) in enumerate(scored_original[:5], 1):
        print(f"{i}. {song['title']:25} | Score: {score:.2f} | "
              f"M:{components['mood']:.2f} G:{components['genre']:.2f} "
              f"E:{components['energy']:.2f} A:{components['acoustic']:.2f}")

    print("\nGENRE-HEAVY (0.40 mood, 0.50 genre, 0.05 energy, 0.05 acoustic)")
    print("-" * 80)
    for i, (song, score, components) in enumerate(scored_genre_heavy[:5], 1):
        print(f"{i}. {song['title']:25} | Score: {score:.2f} | "
              f"M:{components['mood']:.2f} G:{components['genre']:.2f} "
              f"E:{components['energy']:.2f} A:{components['acoustic']:.2f}")

    # Show what changed
    print("\nImpact Analysis:")
    print("-" * 80)

    # Get top songs from each approach
    original_top_titles = [s[0]['title'] for s in scored_original[:5]]
    genre_heavy_top_titles = [s[0]['title'] for s in scored_genre_heavy[:5]]

    print(f"Songs that appear in BOTH top 5: ", end="")
    overlap = set(original_top_titles) & set(genre_heavy_top_titles)
    print(f"{len(overlap)}/5 ({', '.join(list(overlap)[:3])}...)" if overlap else "None")

    print(f"Songs that MOVED UP with genre-heavy: ", end="")
    moved_up = []
    for title in genre_heavy_top_titles:
        orig_rank = next((i for i, s in enumerate(scored_original) if s[0]['title'] == title), None)
        genre_rank = next((i for i, s in enumerate(scored_genre_heavy) if s[0]['title'] == title), None)
        if orig_rank and genre_rank and orig_rank > genre_rank:
            moved_up.append(f"{title} (pos {orig_rank+1} to {genre_rank+1})")
    print(", ".join(moved_up[:3]) if moved_up else "None")

    print(f"Songs that MOVED DOWN with genre-heavy: ", end="")
    moved_down = []
    for title in original_top_titles:
        orig_rank = next((i for i, s in enumerate(scored_original) if s[0]['title'] == title), None)
        genre_rank = next((i for i, s in enumerate(scored_genre_heavy) if s[0]['title'] == title), None)
        if orig_rank and genre_rank and orig_rank < genre_rank:
            moved_down.append(f"{title} (pos {orig_rank+1} to {genre_rank+1})")
    print(", ".join(moved_down[:3]) if moved_down else "None")


if __name__ == "__main__":
    songs = load_songs("data/songs.csv")

    # Test Case 1: User wants happy pop (good genre match available)
    test_case_1 = {
        'genre': 'pop',
        'mood': 'happy',
        'energy': 0.80,
        'likes_acoustic': False,
    }
    compare_recommendations("Happy Pop (Perfect Genre Match Available)", test_case_1, songs)

    # Test Case 2: User wants intense rock (genre match + mood match)
    test_case_2 = {
        'genre': 'rock',
        'mood': 'intense',
        'energy': 0.90,
        'likes_acoustic': False,
    }
    compare_recommendations("Intense Rock (Both Genre & Mood Match)", test_case_2, songs)

    # Test Case 3: User wants chill lofi (genre-specific preference)
    test_case_3 = {
        'genre': 'lofi',
        'mood': 'chill',
        'energy': 0.40,
        'likes_acoustic': False,
    }
    compare_recommendations("Chill Lofi (Genre-Specific)", test_case_3, songs)

    # Test Case 4: User wants happy but with high energy (mood > genre priority)
    test_case_4 = {
        'genre': 'jazz',  # Jazz exists but mostly relaxed/chill
        'mood': 'happy',   # Happy songs exist but in pop/indie
        'energy': 0.90,
        'likes_acoustic': False,
    }
    compare_recommendations("Happy Jazz High-Energy (Genre Miss)", test_case_4, songs)

    # Test Case 5: User wants relaxed acoustic (mood + acoustic preference)
    test_case_5 = {
        'genre': 'jazz',
        'mood': 'relaxed',
        'energy': 0.35,
        'likes_acoustic': True,
    }
    compare_recommendations("Relaxed Acoustic Jazz", test_case_5, songs)

    print("\n" + "=" * 80)
    print("SUMMARY: Genre Weight 0.30 vs 0.50")
    print("=" * 80)
    print("""
ORIGINAL (Genre 0.30):
  - Mood-first approach
  - Emotional context dominates
  - Cross-genre discovery (e.g., happy songs from different genres)
  - Better for context-driven listening (workout, sleep, focus)

GENRE-HEAVY (Genre 0.50):
  - Genre becomes nearly equal to mood 
          #what do you mean "nearly equal"? it's more than 50% of the score!
  - Users stay within their preferred sound/instrumentation
  - Less cross-genre discovery
  - Better for "stay in my lane" listeners
  - Penalizes energy/acoustic mismatches more

TRADE-OFF:
  - mood 0.40, genre 0.30: "Find me songs that feel like THIS"
  - mood 0.40, genre 0.50: "Find me THIS kind of songs that feel this way"
""")
