from flask import Flask, render_template, jsonify, session, request
import logging
import random
# Import custom modules
from app.logic.word_loader import load_words
from app.logic.diagnosis import perform_diagnosis

# Initialize the Flask application
app = Flask(__name__)
# Secret key is crucial for session management. Replace with a strong, random key in production.
app.secret_key = 'dev_secret_key_for_word_swipe_game'

# Configure basic logging for the application
# In a production environment, consider more advanced logging configurations (e.g., file-based, log rotation)
logging.basicConfig(level=logging.INFO) # Set to logging.DEBUG for more verbose output during development
logger = logging.getLogger(__name__)

# --- Global Variables ---
# all_words_list: Stores all words loaded from words.json. Shuffled at startup.
# all_words_dict: A dictionary mapping word IDs to word objects for quick lookups.
all_words_list = []
all_words_dict = {}

# --- Application Startup ---
try:
    # Load words from the JSON file at application startup
    logger.info("Loading words from data file...")
    loaded_words = load_words()
    if not loaded_words:
        logger.warning("No words were loaded. Check 'app/data/words.json' and 'app/logic/word_loader.py'.")
    else:
        all_words_list = loaded_words
        random.shuffle(all_words_list) # Shuffle the list to ensure word order varies between sessions
        all_words_dict = {word['id']: word for word in all_words_list}
        logger.info(f"Successfully loaded and shuffled {len(all_words_list)} words.")
except Exception as e:
    logger.error(f"Critical error during initial word loading: {e}", exc_info=True)
    # Application might be in a degraded state if words cannot be loaded.

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page of the application."""
    return render_template('index.html')

@app.route('/api/initial_words', methods=['GET'])
def initial_words():
    """
    API endpoint to get the first batch of words for a new session.
    Initializes session variables for tracking seen words and user responses.
    """
    logger.info("Request received for /api/initial_words. Initializing new session.")
    # Clear any existing session data to start fresh for the user
    session.clear()
    # 'seen_word_ids': Stores IDs of words already presented to the user in this session to avoid repetition.
    session['seen_word_ids'] = []
    # 'responses': Stores user's swipe actions (positive/negative) for each word.
    session['responses'] = []

    initial_batch_size = 10
    initial_batch = []
    # Prefer common nouns/verbs for the very first batch for smoother onboarding.
    preferred_categories = ["common_verb", "common_noun"]

    # Create a mutable copy of the global word list for selection for this request
    temp_word_list = list(all_words_list)

    # Attempt to fill the batch with preferred categories first
    for word in temp_word_list:
        if len(initial_batch) < initial_batch_size and word['category'] in preferred_categories:
            if word['id'] not in session['seen_word_ids']: # Should always be true here due to session clear
                initial_batch.append(word)
                session['seen_word_ids'].append(word['id'])

    # Fill any remaining spots in the batch with other words
    # This ensures a full batch if not enough preferred words are available or if initial_batch_size is large.
    for word in temp_word_list:
        if len(initial_batch) < initial_batch_size:
            if word['id'] not in session['seen_word_ids']:
                initial_batch.append(word)
                session['seen_word_ids'].append(word['id'])
        else:
            break # Batch is full

    session.modified = True # Mark session as modified after setting initial lists
    logger.info(f"Initial words selection complete. Batch size: {len(initial_batch)}.")
    logger.debug(f"Initial batch IDs: {[word['id'] for word in initial_batch]}")
    logger.debug(f"Session seen_word_ids initialized: {session['seen_word_ids']}")
    logger.debug(f"Session responses initialized: {session['responses']}")
    return jsonify({"words": initial_batch})

@app.route('/api/next_words', methods=['POST'])
def next_words():
    """
    API endpoint to get the next batch of words based on the user's last response.
    Records the user's response and implements a simple adaptive word selection logic.
    """
    data = request.get_json()
    if not data or 'last_word_id' not in data or 'response' not in data:
        logger.warning("Bad request to /api/next_words. Missing required data.")
        return jsonify({"error": "Missing data: last_word_id or response"}), 400

    last_word_id = data['last_word_id']
    response_type = data['response'] # User's swipe: 'positive' or 'negative'

    # Retrieve details of the word the user just responded to for richer logging in session.
    word_details = all_words_dict.get(last_word_id, {})
    word_text = word_details.get('text', 'N/A')
    word_category = word_details.get('category', 'N/A')

    # Store the user's response in the session.
    # 'responses' accumulates a list of dicts: {'word_id': ..., 'text': ..., 'category': ..., 'response': ...}
    if 'responses' not in session: # Should have been initialized by initial_words
        session['responses'] = [] # Safety net
    session['responses'].append({
        'word_id': last_word_id,
        'text': word_text,
        'category': word_category,
        'response': response_type
    })
    session.modified = True # Crucial: Mark session as modified when changing mutable types like lists.

    # Define goals and batch properties for word selection
    TOTAL_WORDS_GOAL = 50  # Target number of unique words for a full session
    next_batch_size = 10   # Number of words for the next set
    new_words_batch = []   # List to hold the next batch of words

    # Check if the user has already seen the target number of words.
    # 'seen_word_ids' tracks all unique words presented in this session.
    if len(session.get('seen_word_ids', [])) >= TOTAL_WORDS_GOAL:
        logger.info(f"User has reached the goal of {TOTAL_WORDS_GOAL} seen words. No more words will be sent.")
        return jsonify({"words": [], "message": "Session complete. All words swiped."})

    # Select from words not yet seen by the user in this session.
    available_words = [word for word in all_words_list if word['id'] not in session.get('seen_word_ids', [])]

    if not available_words:
        logger.info("No more unique words available in the dataset to present.")
        return jsonify({"words": [], "message": "All unique words from dataset swiped."})

    # Simple Adaptive Selection Heuristic:
    # If the last response was positive to an 'action_verb', try to include another 'action_verb'.
    # This is a basic example of adapting the word flow. More complex rules could be added here.
    if response_type == 'positive' and last_word_id in all_words_dict:
        if len(session['seen_word_ids']) < TOTAL_WORDS_GOAL and len(new_words_batch) < next_batch_size: # Check limits
            last_word_cat = all_words_dict[last_word_id].get('category')
            if last_word_cat == 'action_verb':
                logger.debug("Adaptive logic: Last positive response was to an action_verb.")
                # Find available, unseen action verbs
                action_verbs = [w for w in available_words if w['category'] == 'action_verb' and w['id'] not in session['seen_word_ids']]
                if action_verbs:
                    chosen_verb = random.choice(action_verbs)
                    logger.debug(f"Adaptive logic: Adding action_verb '{chosen_verb['text']}'.")
                    new_words_batch.append(chosen_verb)
                    session['seen_word_ids'].append(chosen_verb['id']) # Mark as seen

    # Fill the rest of the batch with randomly selected words from the available (unseen) pool.
    # Continue until the batch is full or the overall session goal (TOTAL_WORDS_GOAL) is met.
    random.shuffle(available_words)
    for word in available_words:
        if len(new_words_batch) < next_batch_size and len(session['seen_word_ids']) < TOTAL_WORDS_GOAL:
            # Ensure word is not already in the current batch (e.g. from adaptive step) or seen_word_ids
            if word['id'] not in session['seen_word_ids']:
                new_words_batch.append(word)
                session['seen_word_ids'].append(word['id']) # Mark as seen
        else:
            break # Batch is full or session goal reached

    session.modified = True # Mark session as modified after updating 'seen_word_ids'.

    logger.info(f"Next words selection complete. Batch size: {len(new_words_batch)}. Total seen: {len(session['seen_word_ids'])}.")
    logger.debug(f"Next batch IDs: {[word['id'] for word in new_words_batch]}")
    logger.info(f"Last response recorded: {response_type} to '{word_text}' (ID: {last_word_id}). Total responses in session: {len(session['responses'])}.")
    return jsonify({"words": new_words_batch})

@app.route('/api/get_diagnosis', methods=['GET'])
def get_diagnosis_route():
    """
    API endpoint to generate and return a diagnosis based on all user responses in the session.
    This should typically be called after the user has completed the required number of words.
    """
    logger.info("Received request for /api/get_diagnosis.")
    TOTAL_WORDS_GOAL = 50 # This should be consistent with the goal in /api/next_words

    # Verify that the user has completed the session (seen enough words).
    seen_ids_count = len(session.get('seen_word_ids', []))
    if seen_ids_count < TOTAL_WORDS_GOAL:
        logger.warning(f"Diagnosis requested prematurely. Seen words: {seen_ids_count}/{TOTAL_WORDS_GOAL}.")
        return jsonify({
            "error": "Diagnosis cannot be generated until all words are swiped.",
            "message": f"Please complete all {TOTAL_WORDS_GOAL} words. You have swiped {seen_ids_count} so far."
        }), 403 # HTTP 403 Forbidden

    responses = session.get('responses', [])
    if not responses: # Should not happen if seen_ids_count >= TOTAL_WORDS_GOAL, but good check.
        logger.warning("No responses found in session for diagnosis, though goal was met.")
        return jsonify({"error": "No responses found to generate diagnosis."}), 400

    if not all_words_dict: # all_words_dict is loaded globally at startup
         logger.error("CRITICAL: all_words_dict is not available for diagnosis (not loaded at startup?).")
         return jsonify({"error": "Server error: Word data not available for diagnosis."}), 500

    logger.debug(f"Calling perform_diagnosis with {len(responses)} responses.")
    # Generate diagnosis by processing all collected responses.
    diagnosis_results = perform_diagnosis(responses, all_words_dict)

    logger.info(f"Diagnosis generated. Strengths found: {len(diagnosis_results.get('strengths',[]))}, Weaknesses found: {len(diagnosis_results.get('weaknesses',[]))}.")
    logger.debug(f"Diagnosis result summary: {diagnosis_results.get('summary_text')}")
    return jsonify(diagnosis_results)

# These endpoints were part of earlier development iterations and have been replaced or integrated.
# Removed old /api/submit_response as its functionality is integrated into /api/next_words
# Removed old /api/words, replaced by /api/initial_words and /api/next_words

if __name__ == '__main__':
    # Allows running the Flask app directly using 'python app/main.py'
    # The debug=True option is useful for development as it provides detailed error pages and auto-reloads on code changes.
    # For production, debug mode should be set to False.
    # The host '0.0.0.0' makes the server accessible externally (if firewall allows),
    # while '127.0.0.1' (default) is only accessible from the local machine.
    app.run(debug=True, port=5000) # Default port is 5000
