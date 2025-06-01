from collections import defaultdict

def perform_diagnosis(responses: list, all_words_dict: dict) -> dict:
    """
    Performs a basic diagnosis based on user responses to a series of words.

    The diagnosis analyzes sentiments (positive/negative swipes) towards:
    1. Word Categories: Broad classifications of words (e.g., 'work_ethic', 'creativity_related').
    2. Word Attributes: Specific traits or concepts associated with words (e.g., 'leadership', 'analytical').

    Args:
        responses (list): A list of response objects from the user's session.
                          Each response_item is expected to be a dictionary:
                          {'word_id': str, 'text': str, 'category': str, 'response': 'positive'/'negative'}
        all_words_dict (dict): A dictionary of all words available in the application,
                               keyed by word_id. This is used to look up the 'attributes'
                               list for each word.
                               Example: {'cv_001': {'text': 'Run', ..., 'attributes': ['exercise', 'speed']}}

    Returns:
        dict: A dictionary containing the diagnosis results, structured as:
              {
                  'strengths': list_of_strings,  // Positive insights
                  'weaknesses': list_of_strings, // Areas for development
                  'summary_text': str,          // A brief overall summary
                  'category_details': dict,     // Raw sentiment counts for each category
                  'attribute_details': dict     // Raw sentiment counts for each attribute
              }
    """
    # Initialize dictionaries to store sentiment counts.
    # defaultdict(lambda: defaultdict(int)) creates a nested dictionary where:
    # - Outer keys are category/attribute names.
    # - Inner keys are 'positive' or 'negative'.
    # - Values are the counts, defaulting to 0.
    # Example: category_sentiments['work_ethic']['positive'] = 2
    category_sentiments = defaultdict(lambda: defaultdict(int))
    attribute_sentiments = defaultdict(lambda: defaultdict(int))

    # If there are no responses, return an empty diagnosis.
    if not responses:
        return {
            'strengths': [],
            'weaknesses': [],
            'summary_text': "Not enough data for a diagnosis. Please complete the word swipe session.",
            'category_details': {},
            'attribute_details': {}
        }

    # --- Step 1: Process all responses and aggregate sentiment counts ---
    for response_item in responses:
        word_id = response_item['word_id']
        # Text and category are directly available in the response_item, as per recent updates.
        # category = response_item['category']
        # text = response_item['text']
        sentiment = response_item['response'] # This will be 'positive' or 'negative'

        # Increment sentiment for the word's category.
        # The category is taken directly from the response_item.
        category_from_response = response_item.get('category', 'unknown_category')
        category_sentiments[category_from_response][sentiment] += 1

        # Retrieve the word's attributes from the all_words_dict using its ID.
        word_data = all_words_dict.get(word_id, {}) # Get the word's full data
        attributes = word_data.get('attributes', []) # Get its list of attributes

        # Increment sentiment for each attribute associated with the word.
        for attr in attributes:
            attribute_sentiments[attr][sentiment] += 1

    strengths = []  # List to store positive diagnostic statements
    weaknesses = [] # List to store areas for development statements

    # Define thresholds for determining significance. These can be tuned.
    positive_threshold_pct = 0.6  # More than 60% positive responses for a category/attribute.
    negative_threshold_pct = 0.6  # More than 60% negative responses.
    # Minimum number of responses related to a category/attribute to consider it for a statement.
    # This avoids making strong statements based on very few interactions.
    min_responses_for_significance = 2

    # --- Step 2: Analyze aggregated sentiments for Categories ---
    for category, sentiments in category_sentiments.items():
        positive_responses = sentiments.get('positive', 0)
        negative_responses = sentiments.get('negative', 0)
        total_responses_in_category = positive_responses + negative_responses

        if total_responses_in_category < min_responses_for_significance:
            continue # Not enough data for this category to make a reliable statement.

        # Check for strong positive inclination towards a category.
        if (positive_responses / total_responses_in_category) >= positive_threshold_pct:
            strengths.append(f"Shows positive engagement with concepts related to '{category}'.")
        # Check for strong negative inclination or challenges with a category.
        elif (negative_responses / total_responses_in_category) >= negative_threshold_pct:
            weaknesses.append(f"May find concepts related to '{category}' challenging or less appealing.")

    # --- Step 3: Analyze aggregated sentiments for Attributes ---
    # min_responses_for_attribute_significance can be same or different from category one.
    min_responses_for_attribute_significance = 2
    for attribute, sentiments in attribute_sentiments.items():
        positive_responses = sentiments.get('positive', 0)
        negative_responses = sentiments.get('negative', 0)
        total_responses_for_attribute = positive_responses + negative_responses

        if total_responses_for_attribute < min_responses_for_attribute_significance:
            continue # Not enough data for this attribute.

        # Check for strong positive association with an attribute.
        if (positive_responses / total_responses_for_attribute) >= positive_threshold_pct:
            strengths.append(f"Demonstrates a positive association with the attribute: '{attribute}'.")
        # Check for strong negative association or challenges with an attribute.
        elif (negative_responses / total_responses_for_attribute) >= negative_threshold_pct:
            weaknesses.append(f"May have reservations or challenges concerning the attribute: '{attribute}'.")

    # --- Step 4: Generate a simple summary text ---
    summary_text = f"Diagnosis based on {len(responses)} swipe responses. "
    if strengths:
        summary_text += f"Identified {len(strengths)} potential areas of strength. "
    if weaknesses:
        summary_text += f"Identified {len(weaknesses)} potential areas for development. "
    if not strengths and not weaknesses and len(responses) >= min_responses_for_significance : # check if enough responses were made overall
        summary_text += "Responses indicate a balanced engagement or no strong tendencies stood out with the current interactions."
    elif not strengths and not weaknesses:
         summary_text += "More interactions are needed to identify distinct patterns."


    # --- Step 5: Return the complete diagnosis ---
    return {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'summary_text': summary_text,
        'category_details': dict(category_sentiments), # Convert defaultdicts to dict for cleaner JSON output
        'attribute_details': dict(attribute_sentiments)
    }

if __name__ == '__main__':
    # This block provides an example of how to use perform_diagnosis and allows for direct testing.
    # To run this test: `python app/logic/diagnosis.py` from the project root.

    print("--- Running Diagnosis Test ---")
    # Sample all_words_dict (mirroring what would be loaded from words.json)
    sample_all_words = {
        'w1': {'id': 'w1', 'text': 'Lead', 'category': 'work_ethic', 'attributes': ['leadership', 'communication']},
        'w2': {'id': 'w2', 'text': 'Create', 'category': 'creativity_related', 'attributes': ['innovation', 'expression']},
        'w3': {'id': 'w3', 'text': 'Pressure', 'category': 'stress_related', 'attributes': ['pressure', 'time_management']},
        'w4': {'id': 'w4', 'text': 'Teamwork', 'category': 'social_interaction', 'attributes': ['collaboration', 'communication']},
        'w5': {'id': 'w5', 'text': 'Analyze', 'category': 'problem_solving', 'attributes': ['analytical', 'detail_oriented']},
        'w6': {'id': 'w6', 'text': 'Conflict', 'category': 'stress_related', 'attributes': ['pressure', 'communication', 'resolution']},
        'w7': {'id': 'w7', 'text': 'Innovate', 'category': 'creativity_related', 'attributes': ['innovation', 'risk_taking']},
    }

    # Sample list of responses (simulating user session data)
    sample_responses = [
        {'word_id': 'w1', 'text': 'Lead', 'category': 'work_ethic', 'response': 'positive'},
        {'word_id': 'w1', 'text': 'Lead', 'category': 'work_ethic', 'response': 'positive'},
        {'word_id': 'w2', 'text': 'Create', 'category': 'creativity_related', 'response': 'positive'},
        {'word_id': 'w7', 'text': 'Innovate', 'category': 'creativity_related', 'response': 'positive'},
        {'word_id': 'w3', 'text': 'Pressure', 'category': 'stress_related', 'response': 'negative'},
        {'word_id': 'w3', 'text': 'Pressure', 'category': 'stress_related', 'response': 'negative'},
        {'word_id': 'w6', 'text': 'Conflict', 'category': 'stress_related', 'response': 'negative'},
        {'word_id': 'w4', 'text': 'Teamwork', 'category': 'social_interaction', 'response': 'positive'},
        {'word_id': 'w5', 'text': 'Analyze', 'category': 'problem_solving', 'response': 'positive'},
    ]

    diagnosis_result = perform_diagnosis(sample_responses, sample_all_words)

    print("\nDiagnosis Result:")
    print(f"  Strengths ({len(diagnosis_result['strengths'])}):")
    for s in diagnosis_result['strengths']: print(f"    - {s}")

    print(f"\n  Weaknesses ({len(diagnosis_result['weaknesses'])}):")
    for w in diagnosis_result['weaknesses']: print(f"    - {w}")

    print(f"\n  Summary: {diagnosis_result['summary_text']}")

    # print("\n  Category Details (Raw Counts):")
    # for cat, sentiments in diagnosis_result['category_details'].items():
    #     print(f"    {cat}: Positive={sentiments.get('positive',0)}, Negative={sentiments.get('negative',0)}")

    # print("\n  Attribute Details (Raw Counts):")
    # for attr, sentiments in diagnosis_result['attribute_details'].items():
    #     print(f"    {attr}: Positive={sentiments.get('positive',0)}, Negative={sentiments.get('negative',0)}")

    print("\n--- Testing with no responses ---")
    diagnosis_no_responses = perform_diagnosis([], sample_all_words)
    print(f"  Summary: {diagnosis_no_responses['summary_text']}")
    print("--- Diagnosis Test Complete ---")
