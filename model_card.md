# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name : Taste Tuner 2.0
---
## 2. Intended Use  

- The model uses user profile for preferences in mood, genre, energy, acousticness, and possibly artist to compare to song.csv weighed on a scale of 0.0 to 0.1 match.
- The model suggests the top 5 songs, ranked by relevance to that taste profile.
- The second iteration of this model uses API from a music statistic website to inform tag relevance.
- This model is limited and for classroom exploration only.

> 

---

## 3. How the Model Works  

 The model uses Mood, Genre, Energy, Acousticness
 Adding up to 1.0:
> score = 
>   (mood_match * 0.4) + 
>   (genre_match * 0.3) +  
>   (1 - |energy_distance| * 0.2) + 
>   (acoustic_match * 0.1)

 OR with artist
> score = 
>   (mood_match * 0.35) +  
>   (genre_match * 0.25) + 
>   (artist_match * 0.25) +  
>   (1 - |energy_distance| * 0.1) + 
>   (acoustic_match * 0.05)

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

For 2.0, I wanted to check how the new API inclusion worked and how efficiently it solved the problem that inspired its inclusion (difficulty recognizing related tags). So the key aspects evaluated were:
- a change in behavior for similar genre overlap, specifically, the ability to recognize an overlap in "pop" and "indie pop".
- testing the api call with online mode-- time taken
- accuracy and relevance of new artist preference criteria
- failsafe/fallback option worked for 1) switching to offline cached mode when api key was invalid and 2) accepting non predefined genre tags 3) checking validity of new tags 

**TEST 1**: Offline, Profile: **Sample** {mood: happy, genre: pop} = highest at 1.00 ,bruno mars.
- snippet: ```"'indie pop' genre is 80% similar to 'pop' (80% match, +0.24)```

**TEST 2**: Cached, Profile: **Sample** {mood: happy, genre: pop} 
- 1st place: highest at 1.00, bruno mars.
- 5th snippet:
  ```
  ... Final Score: 0.77 ...
  'indie pop' genre is 35% similar to pop (36% match, +0.11)
  ```
**TEST 3**: Online, Profile: **Sample** {mood: happy, genre: pop, (API key invalid or skipped)}
- same results as test 2, sign it fell back
- it gives the warning "No API key provided..." when "" (enter, skipped), but not when "1" (invalid). 

**TEST 4**: Online, Profile: **Custom** {mood: chill, energy: 0.4, acoustic: y, genre (1st try): 'frejoi' (invalid), genre (2nd try): indie, artist: 'arctic monkeys'}  
- invalid genre input tested, rejected
- 1st Snippet: ```Final Score: 0.59 ... 'Arctic Monkeys' is your favorite artist (+0.25)```
- also tested with 'arctic mon' and accepted because api includes small scale accounts as artists names. need to improve threshold on accepted input

**Insight:** 
- While it does play a role in recommended, the artist preference was a bit confusing since preferred artist didn't always show up if the music type was too far off
- the api call worked with key, but I realized I need to rethink structure or find more relevant api
- While tag recognition works, there is a disparity between offline and cached that I need to improve on, perhaps because using artists as reference offsets accuracy 
failsafes seemed to work:
- wouldn't take spelling errors or invalid genres
- only accepted 2 mistakes before asking to choose from cached
- tested new tags against api if online or against cached genres if offline
- invalid API key defaulted to offline mode
- need to update warning, give sign that it's checkign API key, and says whether it's valid or not. 


---

## 8. Future Work  

Ideas for how you would improve the model next.  

- Switching API used
- consistent warning messages
- Improving consitency in tags related score 
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

