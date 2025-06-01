# Word Swipe Game

This is a simple word swipe game application. Users are presented with a series of words and swipe left (positive) or right (negative) to indicate their response to each word. After a set number of swipes, a basic diagnostic profile is generated based on the user's responses to different word categories and attributes.

## Features

- **Word Card Swiping:** Interactive interface to swipe through word cards.
- **Session Management:** Tracks user progress (seen words, responses) within a session.
- **Fixed-Length Sessions:** Each session consists of swiping 50 unique words.
- **Simple Adaptive Word Selection:** The backend includes a minor heuristic to slightly adjust word selection based on recent positive responses (e.g., showing more "action_verb" if one was liked). Primarily, it ensures unseen words are presented.
- **Diagnosis Generation:** After completing the session, a diagnosis is generated highlighting potential strengths and areas for development based on response patterns to word categories and attributes.
- **Results Display:** Shows the generated diagnosis (strengths, weaknesses, summary) on a separate results screen.
- **Dynamic Word Loading:** Words are loaded from a `words.json` file, allowing for easy updates to the word list.

## Technology Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Data:** JSON (for word list)

## Project Structure

- `app/`: Main application directory.
  - `main.py`: Flask backend logic (API endpoints, session management).
  - `static/`: Contains static assets.
    - `style.css`: CSS for styling the application.
    - `script.js`: JavaScript for frontend interactivity and API communication.
  - `templates/`: HTML templates.
    - `index.html`: The main HTML file for the application interface.
  - `logic/`: Contains business logic modules.
    - `word_loader.py`: Handles loading and parsing of the word list from JSON.
    - `diagnosis.py`: Implements the logic for generating diagnosis from user responses.
  - `data/`: Contains data files.
    - `words.json`: JSON file storing the list of words, their categories, and attributes.
- `README.md`: This file.
- `.gitignore`: Standard Python .gitignore file.

## Setup and Running the Application

1.  **Python Version:** Python 3.7+ is recommended.
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install Dependencies:**
    The primary dependency is Flask.
    ```bash
    pip install Flask
    ```
4.  **Run the Application:**
    Navigate to the project's root directory (where this README is located) and run:
    ```bash
    python app/main.py
    ```
    Alternatively, if you have Flask CLI configured (usually by setting `FLASK_APP=app/main.py`), you can use:
    ```bash
    flask run --debug
    ```
5.  **Access the Application:**
    Open your web browser and go to `http://127.0.0.1:5000/`.

## How it Works

1.  **Start:** When the application loads, it fetches an initial batch of words.
2.  **Swipe:** The user is presented with a word. They can swipe "Positive" (left button) or "Negative" (right button).
3.  **Next Word:** After each swipe, the response is sent to the backend. The backend records the response and provides the next word. The selection process aims to show unique words and includes a very simple adaptive heuristic (e.g., if an "action_verb" is liked, another might be shown sooner).
4.  **Session Completion:** The user continues swiping until they have responded to 50 unique words.
5.  **View Diagnosis:** Once 50 words are completed, the game interface is replaced by a diagnosis screen. This screen displays:
    *   A list of potential strengths.
    *   A list of potential areas for development.
    *   A brief summary statement.
    The diagnosis is based on patterns of positive and negative responses to different categories of words (e.g., "creativity_related", "problem_solving") and specific attributes associated with those words (e.g., "innovation", "analytical").

## Word Data

The words used in the application are stored in `app/data/words.json`. Each word entry in this JSON file includes:
- `id`: A unique identifier for the word.
- `text`: The word itself.
- `category`: The general category the word belongs to (e.g., "work_ethic", "social_interaction").
- `attributes`: A list of specific traits or concepts associated with the word (e.g., "leadership", "empathy").

This data file is loaded by the application at startup. The diagnosis logic uses the categories and attributes to identify patterns in user responses.
