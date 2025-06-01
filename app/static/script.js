// This script handles the frontend logic for the Word Swipe Game.
// It communicates with the backend API to fetch words, send responses, and display diagnosis.

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const wordTextElement = document.getElementById('word-text'); // Displays the current word
    const swipeLeftArea = document.getElementById('swipe-left-area'); // Button for "positive" swipe
    const swipeRightArea = document.getElementById('swipe-right-area'); // Button for "negative" swipe
    const progressIndicatorElement = document.getElementById('progress-indicator'); // Shows "Card X of Y"
    const gameContainer = document.getElementById('game-container'); // Main container for game elements
    const resultsContainer = document.getElementById('results-container'); // Container for diagnosis results
    const strengthsListUl = document.querySelector('#strengths-list ul'); // UL for strengths
    const weaknessesListUl = document.querySelector('#weaknesses-list ul'); // UL for weaknesses
    const diagnosisSummaryP = document.getElementById('diagnosis-summary'); // Paragraph for diagnosis summary

    // --- Global State Variables ---
    let currentWordsBatch = []; // Stores the current batch of words fetched from the backend
    let currentWordIndexInBatch = 0; // Index of the word currently displayed from currentWordsBatch
    let totalSwipedCount = 0; // Total number of words swiped by the user in this session
    const TOTAL_WORDS_GOAL = 50; // Target number of words for a complete session

    /**
     * Updates the progress indicator text (e.g., "Card 1 of 50").
     * Called after each swipe and when the game initializes.
     */
    function updateProgressIndicator() {
        if (totalSwipedCount >= TOTAL_WORDS_GOAL) {
            progressIndicatorElement.textContent = `Completed ${TOTAL_WORDS_GOAL} of ${TOTAL_WORDS_GOAL}! Fetching diagnosis...`;
        } else {
            // Display current card number (1-based) up to the goal.
            const currentCardNumber = Math.min(totalSwipedCount + 1, TOTAL_WORDS_GOAL);
            progressIndicatorElement.textContent = `Card ${currentCardNumber} of ${TOTAL_WORDS_GOAL}`;
        }
    }

    /**
     * Fetches the initial batch of words from the backend when the page loads.
     * Initializes the game state.
     */
    async function fetchInitialWords() {
        console.log("Fetching initial words...");
        try {
            wordTextElement.textContent = 'Loading...'; // Initial display text
            resultsContainer.style.display = 'none';  // Ensure results section is hidden
            gameContainer.style.display = 'flex';   // Ensure game section is visible
            updateProgressIndicator(); // Set initial progress (e.g., "Card 1 of 50")

            const response = await fetch('/api/initial_words');
            console.log("Initial words API response status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log("Initial words data received:", data);

            currentWordsBatch = data.words || []; // Store fetched words
            currentWordIndexInBatch = 0; // Reset index for the new batch
            totalSwipedCount = 0; // Reset total count for a new session

            if (currentWordsBatch.length > 0) {
                displayWord(currentWordIndexInBatch); // Display the first word
            } else {
                // Handle case where backend returns no initial words (e.g., error or empty word list)
                wordTextElement.textContent = 'No words available to start.';
                progressIndicatorElement.textContent = 'Game Over';
                disableSwipeAreas();
                console.warn("No initial words loaded.");
            }
        } catch (error) {
            console.error('Error fetching initial words:', error);
            wordTextElement.textContent = 'Failed to load initial words.';
            progressIndicatorElement.textContent = 'Error';
            disableSwipeAreas();
        }
    }

    /**
     * Fetches the next batch of words from the backend.
     * Called when the current batch is exhausted.
     * Sends the ID of the last swiped word and the swipe response to the backend.
     * @param {string} lastWordId - The ID of the word just swiped.
     * @param {string} swipeResponse - The user's response ('positive' or 'negative').
     */
    async function fetchNextBatch(lastWordId, swipeResponse) {
        console.log(`Fetching next batch. Last word ID: ${lastWordId}, Response: ${swipeResponse}`);
        try {
            wordTextElement.textContent = 'Loading next set...';
            disableSwipeAreas(); // Prevent further swipes while loading

            const payload = {
                last_word_id: lastWordId,
                response: swipeResponse,
            };
            console.log("Sending to /api/next_words:", payload);

            const response = await fetch('/api/next_words', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            console.log("Next words API response status:", response.status);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            console.log("Next words data received:", data);

            currentWordsBatch = data.words || []; // Update with the new batch
            currentWordIndexInBatch = 0; // Reset index for the new batch

            if (currentWordsBatch.length > 0) {
                displayWord(currentWordIndexInBatch); // Display the first word of the new batch
            } else {
                // No more words in the new batch; session might be complete or words exhausted.
                updateProgressIndicator();
                // Check if goal is met or backend signals completion
                if (totalSwipedCount >= TOTAL_WORDS_GOAL || (data.message && data.message.toLowerCase().includes("complete"))) {
                    wordTextElement.textContent = data.message || 'All words swiped! Generating diagnosis...';
                    console.log("All words swiped or goal reached, fetching diagnosis.");
                    fetchAndDisplayDiagnosis(); // Proceed to diagnosis
                } else {
                    // Words ran out before reaching the goal
                    wordTextElement.textContent = data.message || 'No more unique words available.';
                    progressIndicatorElement.textContent = `Completed ${totalSwipedCount} words.`;
                    disableSwipeAreas();
                    console.warn("No more words in batch, goal not reached, or no specific completion message.");
                }
            }
        } catch (error) {
            console.error('Error fetching next batch of words:', error);
            wordTextElement.textContent = 'Failed to load next words.';
            progressIndicatorElement.textContent = 'Error';
            disableSwipeAreas();
        }
    }

    /**
     * Fetches the diagnosis results from the backend after all words are swiped.
     * Displays the results in the UI.
     */
    async function fetchAndDisplayDiagnosis() {
        console.log("Fetching and displaying diagnosis...");
        progressIndicatorElement.textContent = "Generating your diagnosis...";
        disableSwipeAreas();
        wordTextElement.textContent = "Please wait...";

        try {
            const response = await fetch('/api/get_diagnosis');
            console.log("Diagnosis API response status:", response.status);
            if (!response.ok) {
                const errorData = await response.json(); // Attempt to get error message from backend
                console.error("Diagnosis API error data:", errorData);
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const diagnosis = await response.json();
            console.log("Diagnosis data received:", diagnosis);

            // Hide game, show results
            gameContainer.style.display = 'none';
            resultsContainer.style.display = 'block';

            // Populate strengths list
            strengthsListUl.innerHTML = ''; // Clear any previous items
            diagnosis.strengths.forEach(strength => {
                const li = document.createElement('li');
                li.textContent = strength;
                strengthsListUl.appendChild(li);
            });
            if (diagnosis.strengths.length === 0) {
                 strengthsListUl.innerHTML = '<li>No specific strengths highlighted from these responses.</li>';
            }

            // Populate weaknesses list
            weaknessesListUl.innerHTML = ''; // Clear any previous items
            diagnosis.weaknesses.forEach(weakness => {
                const li = document.createElement('li');
                li.textContent = weakness;
                weaknessesListUl.appendChild(li);
            });
            if (diagnosis.weaknesses.length === 0) {
                 weaknessesListUl.innerHTML = '<li>No specific areas for development highlighted from these responses.</li>';
            }

            // Display summary text
            diagnosisSummaryP.textContent = diagnosis.summary_text || 'No summary available.';
            console.log("Diagnosis displayed successfully.");

        } catch (error) {
            console.error('Error fetching or displaying diagnosis:', error);
            diagnosisSummaryP.textContent = `Failed to generate diagnosis: ${error.message}`;
            // Show the results container to display the error message.
            gameContainer.style.display = 'none';
            resultsContainer.style.display = 'block';
            strengthsListUl.innerHTML = ''; // Clear lists on error too
            weaknessesListUl.innerHTML = '';
        }
    }

    /**
     * Displays a word from the current batch in the UI.
     * @param {number} indexInBatch - The index of the word to display from `currentWordsBatch`.
     */
    function displayWord(indexInBatch) {
        console.log(`Displaying word. Index in batch: ${indexInBatch}, Total swiped: ${totalSwipedCount}`);

        // This condition is a safeguard. Diagnosis transition is primarily handled by fetchNextBatch.
        if (totalSwipedCount >= TOTAL_WORDS_GOAL && currentWordsBatch.length > 0 && indexInBatch < currentWordsBatch.length) {
             console.log("DisplayWord called after goal met, but words still in batch. Diagnosis should be pending.");
        }

        // If goal is met and there are no more words to process from the current batch (e.g. batch was emptied by last swipe)
        if (totalSwipedCount >= TOTAL_WORDS_GOAL && currentWordsBatch.length === 0 ) {
             wordTextElement.textContent = 'Session complete! Preparing diagnosis...';
             updateProgressIndicator(); // Ensure progress shows completion
             disableSwipeAreas();
             console.log("DisplayWord: Goal met, no more words in batch. Diagnosis should be triggered by fetchNextBatch.");
             return; // Stop further display attempts
        }

        if (indexInBatch >= 0 && indexInBatch < currentWordsBatch.length) {
            // Valid word to display
            wordTextElement.textContent = currentWordsBatch[indexInBatch].text;
            console.log(`Current word: "${currentWordsBatch[indexInBatch].text}", ID: ${currentWordsBatch[indexInBatch].id}`);
            enableSwipeAreas(); // Allow user to swipe
        } else {
            // Invalid index or empty batch, but goal not necessarily met yet.
            if (totalSwipedCount < TOTAL_WORDS_GOAL && currentWordsBatch.length === 0) {
                 // This can happen if backend runs out of unique words before goal.
                 wordTextElement.textContent = 'No more unique words available.';
                 progressIndicatorElement.textContent = `Completed ${totalSwipedCount} words.`;
                 console.warn("DisplayWord: No words in current batch, goal not met.");
            } else {
                 // Generic loading message if state is unclear (e.g., during transitions)
                 wordTextElement.textContent = 'Loading...';
                 console.log("DisplayWord: Condition not met for showing word, showing loading.");
            }
            disableSwipeAreas(); // Prevent actions if no word is properly displayed
        }
        updateProgressIndicator(); // Update progress after displaying
    }

    /**
     * Disables the swipe buttons (e.g., during API calls or when game ends).
     */
    function disableSwipeAreas() {
        swipeLeftArea.disabled = true;
        swipeRightArea.disabled = true;
        // console.debug("Swipe areas disabled.");
    }

    /**
     * Enables the swipe buttons.
     */
    function enableSwipeAreas() {
        swipeLeftArea.disabled = false;
        swipeRightArea.disabled = false;
        // console.debug("Swipe areas enabled.");
    }

    /**
     * Handles the swipe action (left or right click).
     * Records the response, updates UI, and fetches next batch or diagnosis if needed.
     * @param {boolean} isLeftSwipe - True if left swipe (positive), false if right swipe (negative).
     */
    function handleSwipe(isLeftSwipe) {
        console.log(`HandleSwipe called. Left swipe: ${isLeftSwipe}. Current index in batch: ${currentWordIndexInBatch}, Batch length: ${currentWordsBatch.length}`);

        // If goal already met and no words left in current batch (diagnosis should be showing/loading)
        if (totalSwipedCount >= TOTAL_WORDS_GOAL && currentWordsBatch.length === 0) {
            console.log("Goal met and no words in batch, swipe ignored. Diagnosis should be in progress or displayed.");
            return;
        }

        // If trying to swipe beyond current batch (shouldn't happen if buttons are disabled correctly)
        if (currentWordIndexInBatch >= currentWordsBatch.length) {
            console.warn("Attempted to swipe when current batch is exhausted or not loaded. Swipe ignored.");
            return;
        }

        const currentWord = currentWordsBatch[currentWordIndexInBatch];
        const swipeDirection = isLeftSwipe ? 'positive' : 'negative';

        console.log(`Swiped ${swipeDirection} on: "${currentWord.text}" (ID: ${currentWord.id}). Total swiped before this: ${totalSwipedCount}`);

        totalSwipedCount++; // Increment total words swiped in the session
        currentWordIndexInBatch++; // Move to next word in the current batch

        console.log(`Total swiped after this: ${totalSwipedCount}. New index in batch: ${currentWordIndexInBatch}`);
        updateProgressIndicator(); // Update progress immediately

        // Determine next action based on swipe count and batch status
        if (totalSwipedCount >= TOTAL_WORDS_GOAL) {
            // User has reached the target number of words for the session.
            console.log("Goal of 50 words met with this swipe. Sending final response and fetching diagnosis.");
            fetchNextBatch(currentWord.id, swipeDirection); // Send this last response, then fetchNextBatch will trigger diagnosis.
        } else if (currentWordIndexInBatch >= currentWordsBatch.length) {
            // Current batch is exhausted, but session goal not yet met.
            console.log("End of current batch. Fetching next batch.");
            fetchNextBatch(currentWord.id, swipeDirection); // Send response and get new words.
        } else {
            // Still words left in the current batch.
            console.log("Displaying next word in current batch.");
            displayWord(currentWordIndexInBatch); // Display the next word.
        }
    }

    // --- Event Listeners ---
    swipeLeftArea.addEventListener('click', () => handleSwipe(true)); // Positive swipe
    swipeRightArea.addEventListener('click', () => handleSwipe(false)); // Negative swipe

    // --- Initialisation ---
    fetchInitialWords(); // Start the game by fetching the first set of words.
});
