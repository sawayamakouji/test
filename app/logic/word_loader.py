import json
import os

# Define the path to the words data file.
# This assumes 'words.json' is in a 'data' directory, one level up from 'logic' directory.
# e.g., project_root/app/data/words.json
#        project_root/app/logic/word_loader.py
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'words.json')

def load_words():
    """
    Reads the words.json file, parses the JSON data, and returns the list of word objects.

    The function handles potential errors such as:
    - FileNotFoundError: If the words.json file does not exist at the specified path.
    - json.JSONDecodeError: If the file content is not valid JSON.
    - Other unexpected exceptions during file operations.

    Returns:
        list: A list of word objects (dictionaries) if successful.
              Each word object is expected to have keys like 'id', 'text', 'category', 'attributes'.
              Returns an empty list ([]) if an error occurs during loading or parsing,
              or if the "words" key is not found in the JSON structure.
    """
    try:
        # Attempt to open and read the JSON file.
        # 'utf-8' encoding is specified for broader compatibility, though often default.
        with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f) # Parse the JSON content from the file
            # Expects the JSON to have a top-level key "words" containing a list of word objects.
            # If "words" key is missing, data.get() will return None, then the 'or []' ensures an empty list.
            return data.get("words", [])
    except FileNotFoundError:
        # Handle the case where the data file does not exist.
        # Print an error message to stderr or use proper logging in a larger application.
        print(f"Error: The word data file was not found at {DATA_FILE_PATH}")
        return []
    except json.JSONDecodeError:
        # Handle errors in JSON parsing (e.g., malformed JSON).
        print(f"Error: The word data file at {DATA_FILE_PATH} contains invalid JSON.")
        return []
    except Exception as e:
        # Catch any other unexpected errors during the file loading process.
        print(f"An unexpected error occurred while loading words from {DATA_FILE_PATH}: {e}")
        return []

if __name__ == '__main__':
    # This block allows for direct testing of the load_words function
    # when this script is executed directly (e.g., `python app/logic/word_loader.py`).
    print("Attempting to load words for testing...")
    words = load_words()
    if words:
        print(f"Successfully loaded {len(words)} words.")
        # Example: Print the first 3 words if any are loaded.
        # for i, word in enumerate(words[:3]):
        #     print(f"  Word {i+1}: {word.get('text', 'N/A')} (Category: {word.get('category', 'N/A')})")
    else:
        print("No words were loaded or an error occurred.")
