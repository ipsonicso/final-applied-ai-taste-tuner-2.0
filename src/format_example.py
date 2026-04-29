""" (From week 7)
Example output format combining:
- Option 4: Bar chart visualization
- Option 7: Summary + Detailed breakdown
- Component scores shown as values/percentages
"""

def format_recommendation_v2(song, score, user_prefs, components):
    """
    Format recommendation with bar chart + detailed breakdown

    components: dict with 'mood', 'genre', 'energy', 'acoustic' scores
    """
    # Build bar chart
    def make_bar(value, max_width=20):
        filled = int(value * max_width)
        return '█' * filled + '░' * (max_width - filled)

    # Calculate component match percentages
    mood_match = 1.0 if song['mood'] == user_prefs['mood'] else 0.0
    genre_match = 1.0 if song['genre'] == user_prefs['genre'] else 0.0

    # Energy is already a score (0-1), convert to percentage
    energy_pct = (1 - abs(song['energy'] - user_prefs['energy'])) * 100

    # Acoustic match
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_match = 1.0 if is_acoustic == user_likes_acoustic else 0.0

    # Build output
    lines = []

    # Title and score
    lines.append(f"\n{'='*70}")
    lines.append(f"{song['title']} - Final Score: {score:.2f}")
    lines.append(f"{'='*70}")

    # Bar chart
    lines.append("\nScore Breakdown:")
    lines.append(f"  Mood       {make_bar(components['mood']/0.40):22} {components['mood']:.2f} (match: {'100%' if mood_match else '0%'})")
    lines.append(f"  Genre      {make_bar(components['genre']/0.30):22} {components['genre']:.2f} (match: {'100%' if genre_match else '0%'})")
    lines.append(f"  Energy     {make_bar(components['energy']/0.20):22} {components['energy']:.2f} (proximity: {energy_pct:.0f}%)")
    lines.append(f"  Acoustic   {make_bar(components['acoustic']/0.10):22} {components['acoustic']:.2f} (match: {'100%' if acoustic_match else '0%'})")

    # Summary
    matched_factors = []
    if mood_match:
        matched_factors.append(f"{song['mood']} mood")
    if genre_match:
        matched_factors.append(f"{song['genre']} genre")
    if energy_pct > 85:
        matched_factors.append("well-matched energy")
    elif energy_pct > 70:
        matched_factors.append("close energy match")
    if acoustic_match:
        acoustic_pref = "acoustic" if user_likes_acoustic else "non-acoustic"
        matched_factors.append(f"{acoustic_pref} quality")

    if matched_factors:
        summary = f"Strong match: {', '.join(matched_factors)}"
    else:
        summary = "Best available match based on weighted preferences"

    lines.append(f"\nSummary: {summary}")

    # Detailed breakdown
    lines.append("\nDetailed Analysis:")

    # Mood
    if mood_match:
        lines.append(f"  ✓ Mood: '{song['mood']}' matches your preference '{user_prefs['mood']}' (100% match, +0.40)")
    else:
        lines.append(f"  ✗ Mood: '{song['mood']}' doesn't match your preference '{user_prefs['mood']}' (0% match, +0.00)")

    # Genre
    if genre_match:
        lines.append(f"  ✓ Genre: '{song['genre']}' matches your preference '{user_prefs['genre']}' (100% match, +0.30)")
    else:
        lines.append(f"  ✗ Genre: '{song['genre']}' doesn't match your preference '{user_prefs['genre']}' (0% match, +0.00)")

    # Energy
    energy_distance = abs(song['energy'] - user_prefs['energy'])
    energy_match_pct = (1 - energy_distance) * 100
    if energy_pct > 85:
        lines.append(f"  ✓ Energy: Song {song['energy']:.2f} vs your target {user_prefs['energy']:.2f} (proximity: {energy_pct:.0f}%, +{components['energy']:.2f})")
    elif energy_pct > 70:
        lines.append(f"  ~ Energy: Song {song['energy']:.2f} vs your target {user_prefs['energy']:.2f} (proximity: {energy_pct:.0f}%, +{components['energy']:.2f})")
    else:
        lines.append(f"  ✗ Energy: Song {song['energy']:.2f} vs your target {user_prefs['energy']:.2f} (proximity: {energy_pct:.0f}%, +{components['energy']:.2f})")

    # Acoustic
    is_acoustic = song['acousticness'] > 0.5
    user_likes_acoustic = user_prefs.get('likes_acoustic', False)
    acoustic_label = "acoustic" if is_acoustic else "non-acoustic"
    user_label = "acoustic" if user_likes_acoustic else "non-acoustic"

    if acoustic_match:
        lines.append(f"  ✓ Acoustic: Song is {acoustic_label}, you prefer {user_label} (100% match, +{components['acoustic']:.2f})")
    else:
        lines.append(f"  ✗ Acoustic: Song is {acoustic_label}, you prefer {user_label} (0% match, +{components['acoustic']:.2f})")

    lines.append(f"{'='*70}")

    return '\n'.join(lines)


# Example usage
if __name__ == "__main__":
    from recommender import load_songs, _get_component_scores

    songs = load_songs("data/songs.csv")

    user_prefs = {
        'genre': 'pop',
        'mood': 'happy',
        'energy': 0.80,
        'likes_acoustic': False,
    }

    print("\n" + "MUSIC RECOMMENDATION DEMO".center(70, "="))
    print(f"User Profile: {user_prefs['mood']} {user_prefs['genre']} with {user_prefs['energy']:.0%} energy\n")

    # Score all songs
    scored = []
    for song in songs:
        song_dict = {
            'genre': song['genre'],
            'mood': song['mood'],
            'energy': song['energy'],
            'acousticness': song['acousticness'],
        }
        components = _get_component_scores(user_prefs, song_dict)
        total_score = sum(components.values())
        scored.append((song, total_score, components))

    # Sort and display top 3
    scored.sort(key=lambda x: x[1], reverse=True)

    for song, score, components in scored[:3]:
        output = format_recommendation_v2(song, score, user_prefs, components)
        print(output)
