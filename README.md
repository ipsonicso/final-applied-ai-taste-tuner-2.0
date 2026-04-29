# Final Project: Taste Tuner 2.0
    Explicitly name your original project (from Modules 1-3) and 
    provide a 2-3 sentence summary of its original goals and capabilities.    
  **Background:**
  On week 7 I developed **Taste Tuner**, a music recommendation system, to simulate algorthims used in industry-leading music apps' recommended playlist systems.
  Version 1 pulls song attributes (particularly *Mood, Genre, Energy, Acousticness*) from a .csv file, takes user text input from a list of predefined attributes, and matches the user with the top 5 songs, ranked by how well they meet the user-set criteria.    

---
## Project Summary
**Taste Tuner 2.0**
### Architecture Overview:

[![System Diagram with Claude and Mermaid.live](assets/System-diagram-1-mermaid.png)] *System Diagram with Claude (Mermaid.live)*
**System Architecture:** Desc.


[![UI with Claude and Mermaid.live](assets/UI-diagram-mermaid.png) *User Interface Flowchart with Claude (Mermaid.live)* 
**User Interface Experience:** Desc.

### Setup
    
     Setup Instructions: Step-by-step directions to run your code.
    
1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```
2. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
3. Run the program
    ```
    python -m src.main
    ```

### Sample Interactions
    Sample Interactions: Include at least 2-3 examples of inputs and the resulting AI outputs to demonstrate the system is functional.
### Design Decisiions
    Design Decisions: Why you built it this way, and what trade-offs you made.

1) Taking user input for taste profile
2) 1) **Advantages:** Allows to test a wider range of options and experiment with managing user queries. It also provides a full experience of an easy-to-use recommender in this enclosed model.
   2) **Tradeoffs:** have to rework for more practical implementations, where work
      
3) API integration
4) 1) **Advantages:** *possibly allow for more user input, build up personal dictionary emulating LLMs.
   3) **Tradeoffs:** *probably slow, depends on online element, workarounds by building local dictionary would not scale well for a small-budget project.
   
  

### Testing Summary 
    Testing Summary: What worked, what didn't, and what you learned.
1) I originally planned to use a useful feature that didn't work (tag comparison), so I used a workaround, importing real song info, approximating stats by the program's metrics, and compare artist tags on artists' profiles instead.
2) I was ambitious in my use of API, but I'm happy I could make it work despite flaws in the. In a practical model, I may use a better quality API more relevant to my needs.
 
### Reflection
  
The AI was great for bouncing ideas off, when I had a good idea, it would give me possible paths to continue down. Still, it was vital to be able to keep it on track and reiterate what I wanted. When I felt at a loss for a technical description, I could give it detailed instructions on how I want it to behave, ask it to repeat its understanding until it matched what I wanted, then have it implement these choices.
