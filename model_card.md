# 🎧 Model Card: Music Recommender Simulation

## Model Name : Taste Tuner 2.0
---
## Intended Use  

- The model uses user profile for preferences in mood, genre, energy, acousticness, and possibly artist to compare to song.csv weighed on a scale of 0.0 to 0.1 match.
- The model suggests the top 5 songs, ranked by relevance to that taste profile.
- The second iteration of this model uses API from a music statistic website to inform tag relevance.
- This model is limited and for classroom exploration only.

> 

---

## 3. How the Model Works  

> The model uses Mood, Genre, Energy, Acousticness
> Adding up to 1.0
> score = 
>   (genre_match * 0.4) +           # Most important
>   (mood_match * 0.3) +            # Very important
>   (1 - |energy_distance| * 0.2) + # Continuous tuning
>   (acoustic_match * 0.1)          # Tiebreaker

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- The model is based on a new file, *songs2.csv* of 45 songs, with five songs from each of nine genres.
> This csv was populated with real artist, genre, and estimated stats for energy, acousticness, mood, valence, danceability
> It is lacking some relevant data for later on, like album name category, and has some information that may be redundant. 

---

## 5. Strengths  

---
> Successfully ranks the top results.
> Successfully matches mood and genre preference above all else.
> Successfully uses API to find genres similarity to each other

## 6. Limitations and Bias 

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

- API is limited: tags.getsimiarity function does not work. Resulting workaround is not yet optimised.
- The metric for genre similarity is a bit convoluted because it is a workaround.
> The metadata it currently draws is limited. It's from can't take into account language and lyrics, year, bands vs artists, or albums 

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

[ src/test_edge_cases.py

**TEST 1**: Offline, Profile: **Sample** {mood: happy, genre: pop} = highest at 1.00 ,bruno mars.
**TEST 2**: Offline, Profile: **Custom** {mood: moody, genre: **rock**, energy=0.3, acoustic} = 
**TEST 3**: Online, Profile: **Sample** {mood: happy, genre: pop} 
**TEST 4**: Online, Profile: **Custom** {mood: chill, genre: indie, artist: **Arctic Monkeys**}
  -
---

## 8. Future Work  

Ideas for how you would improve the model next.  

- Switching API used
- Implementing Likes and dislikes
- Adding UI or using streamlit, cursor to create more user-friendly interface
- Built-in category-based on other factors (such as a workout recommender based on BPM or Mood playlist based on genres,artists user has already liked in that mood)
  
---
## 9. Personal Reflection  

> Considering how I only used the 4 most relevant categories from a system with only 10, I think bigger platforms must involve very complex algorithms with a lot of alternating parts (especially for songs with more or less information) in their recommendations, and I wonder how they account for missing and moving parts.
> I thought about music recommenders like Spotify that categorize and recategorize all your listening tastes in their yearly Wrapped, assigning a super specific genre <https://artists.spotify.com/blog/how-spotify-discovers-the-genres-of-tomorrow> 
> I wonder how similar the earliest music recommender or the earliest version of Spotify would look to my simple program, and what I can do to bridge the gap to that version if I choose to continue this project.

- Working with AI is a requires constant clarity, control, and check-ins to ensure you're on the same page.
- while I defined what I want in UML diagrams, flow charts, at the beginning, it was hard to clarify my ideas
- At times it was frustrating because, even after detailed descriptions, it suddenly reveals it has been going another direction for a while.
- It helped that I could explain in simple terms but extreme what I wanted, and claude could help with putting that plan into action and definining it in proper terms, with proper algoritm
- despit new errors involved,

- 

