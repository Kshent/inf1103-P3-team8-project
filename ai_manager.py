import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import errors
import logging
import ai_filter as filtering


load_dotenv(".env")


PRIMARY_MODEL = "gemini-3.6-flash"
BACKUP_MODEL = "gemini-3.7-flash"
TERTIARY_MODEL = "gemini-3.5-flash-lite"

MODEL_FALLBACKS = [
    PRIMARY_MODEL,
    BACKUP_MODEL,
    TERTIARY_MODEL
]


AI_CANDIDATE_COUNT = 10


# =========================================================
# DISTANCE LOGIC CHANGE 1:
# distance_to_preference_m becomes distance_to_preferences
# =========================================================

EXPECTED_HOTEL_FIELDS = [
    "name",
    "city",
    "country",
    "price_per_night_sgd",
    "rating",
    "amenities",
    "distance_to_preferences",
    "nearby_food",
    "nearby_activities",
]


# =========================================================
# DISTANCE LOGIC CHANGE 2:
# One overall flag + support multiple preference locations
# =========================================================

EXPECTED_PROXIMITY_FIELDS = [
    "specified",
    "preferences",
]


# Structure used inside distance_to_preferences
EXPECTED_DISTANCE_FIELDS = [
    "target",
    "distance_m",
]


# Structure used inside nearby_activities
EXPECTED_ACTIVITY_FIELDS = [
    "name",
    "distance_m",
]


# ---------------------------------------------------------
# AI API error logging
# ---------------------------------------------------------

LOG_DIRECTORY = "logs"

AI_ERROR_LOG_FILE = os.path.join(
    LOG_DIRECTORY,
    "ai_api_errors.log"
)

os.makedirs(LOG_DIRECTORY, exist_ok=True)

logger = logging.getLogger("ai_manager")
logger.setLevel(logging.WARNING)

# Prevent logs from also appearing in console
logger.propagate = False

if not logger.handlers:

    file_handler = logging.FileHandler(
        AI_ERROR_LOG_FILE,
        encoding="utf-8"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def get_model(api_key=None):

    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        logger.error("Gemini API key was not found.")
        return None

    return genai.Client(api_key=api_key)


def build_prompt(record):

    """Build a clear, specific prompt from the record dict,
    instructing the model to reply with JSON only."""

    prefs = (
        (record.get("preferences") or "").strip()
        or "No additional preferences."
    )

    return f"""
You are a hotel-recommendation engine.

Reply with STRICT JSON ONLY.
Do not include markdown, explanations or commentary.

Destination: {record.get('destination')}
Budget (SGD/night): {record.get('budget_min')} to {record.get('budget_max')}
Preferences: {prefs}


PROXIMITY PREFERENCE RULES:

Analyse the user's natural-language preferences and identify whether
they explicitly mention one or more places they want the hotel to be near.

Examples:

"near NUS"
- specified = true
- preferences = ["National University of Singapore"]

"near NUS and Marina Bay Sands"
- specified = true
- preferences = [
    "National University of Singapore",
    "Marina Bay Sands"
  ]

"I want a bathtub and swimming pool"
- specified = false
- preferences = []

Rules:

- Extract zero, one or multiple proximity preferences.
- Only extract locations the user actually asks to be near.
- Do NOT invent proximity preferences.
- If no proximity location is mentioned:
  specified must be false and preferences must be [].
- If one or more proximity locations are mentioned:
  specified must be true.


DISTANCE RULES:

If specified is true:

- For every hotel, return one entry in
  "distance_to_preferences" for EACH proximity preference.

Example:

"distance_to_preferences": [
    {{
        "target": "National University of Singapore",
        "distance_m": 850
    }},
    {{
        "target": "Marina Bay Sands",
        "distance_m": 7200
    }}
]

- The target must correspond to one of the user's
  proximity preferences.
- distance_m must be a non-negative number in metres,
  or null if the distance cannot be reliably determined.


If specified is false:

- "distance_to_preferences" must be [].

- Recommend 2-3 useful nearby activities for each hotel.

- For each nearby activity, provide its distance from the hotel
  in metres when reliably available.

Example:

"nearby_activities": [
    {{
        "name": "National Museum",
        "distance_m": 450
    }},
    {{
        "name": "Botanic Gardens",
        "distance_m": 900
    }}
]


HOTEL RULES:

For each hotel also provide:

- name
- city
- country
- price per night in SGD
- rating out of 5
- amenities
- nearby food suggestions
- nearby activities

Do NOT fabricate information.

If a distance or optional piece of information cannot be
reliably determined, use null or [] where allowed.


Return exactly {AI_CANDIDATE_COUNT} distinct hotel candidates
matching exactly this JSON structure:

{{
    "proximity_preference": {{
        "specified": true or false,
        "preferences": ["string"]
    }},

    "hotels": [
        {{
            "name": "string",
            "city": "string",
            "country": "string",
            "price_per_night_sgd": number,
            "rating": number or null,
            "amenities": ["string"],

            "distance_to_preferences": [
                {{
                    "target": "string",
                    "distance_m": number or null
                }}
            ],

            "nearby_food": ["string"],

            "nearby_activities": [
                {{
                    "name": "string",
                    "distance_m": number or null
                }}
            ]
        }}
    ]
}}
""".strip()


# ---------------------------------------------------------
# Correction prompt
# ---------------------------------------------------------

def build_correction_prompt(original_prompt, invalid_response):

    """
    Used once when Gemini returns malformed JSON or a
    response that does not pass structure validation.
    """

    return f"""
{original_prompt}

CORRECTION:

Your previous response did not pass the required response validation.

Previous response:
{invalid_response}

Regenerate the response from scratch and correct the structure
or data-type problems.

Strict correction requirements:

- Return STRICT JSON only.
- Do not include markdown, code fences, explanations or commentary.
- Return exactly {AI_CANDIDATE_COUNT} distinct hotel objects.
- Include every field shown in the required schema.
- Use the correct data type for every field.


Proximity rules:

- "proximity_preference" must be a dictionary.

- "specified" must be true or false.

- "preferences" must be a list.

- If "specified" is false:
  "preferences" must be [].

- If "specified" is true:
  "preferences" must contain at least one non-empty location string.

- Do NOT invent proximity preferences.


Distance rules:

- "distance_to_preferences" must be a list.

- Every entry must contain:
  "target" and "distance_m".

- "target" must be a non-empty string.

- "distance_m" must be a non-negative number or null.

- When proximity preferences exist, every hotel must contain
  exactly one distance entry for every proximity preference.

- When no proximity preference exists,
  "distance_to_preferences" must be [].


Hotel field rules:

- "name" must be a non-empty string.

- "city" must be a non-empty string.

- "country" must be a non-empty string.

- "price_per_night_sgd" must be a positive number.

- "rating" must be a number from 0 to 5, or null.

- If a source rating uses another numeric scale, convert it to
  0-to-5 only if the original scale is known.

- Do not treat hotel star classification as customer review rating.

- "amenities" must be a list.
  Use [] if unknown.

- "nearby_food" must be a list.
  Use [] if unknown.

- "nearby_activities" must be a list.

- Every nearby activity must contain:
  "name" and "distance_m".

- Activity "name" must be a non-empty string.

- Activity "distance_m" must be a non-negative number or null.


Accuracy rules:

- Do NOT invent or guess information.

- Do NOT fabricate hotel names, prices, ratings,
  amenities, distances, food options or activities.

- If information cannot be reliably provided,
  use the allowed null or empty-list value instead.
""".strip()


def call_api(prompt, client):

    if client is None:

        logger.error(
            "Gemini API request could not start because client is unavailable."
        )

        return None

    for model in MODEL_FALLBACKS:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            if response.text:
                return response.text

            logger.warning(
                "Model %s returned an empty response. "
                "Attempting fallback model.",
                model
            )

        except errors.APIError as error:

            if error.code in {
                404,  # model unavailable
                408,  # timeout
                429,  # rate limit
                500,  # server error
                502,  # server error
                503,  # server error
                504   # server error
            }:

                logger.warning(
                    "Model %s failed. API error code: %s. "
                    "Reason: %s. Attempting fallback model.",
                    model,
                    error.code,
                    error
                )

                continue

            logger.error(
                "Model %s encountered a non-recoverable API error. "
                "Error code: %s. Reason: %s",
                model,
                error.code,
                error
            )

            return None

        except (TimeoutError, ConnectionError) as error:

            logger.warning(
                "Model %s encountered a connection error. "
                "Reason: %s. Attempting fallback model.",
                model,
                error
            )

            continue

        except Exception as error:

            logger.error(
                "Unexpected error while calling model %s. "
                "Error type: %s. Reason: %s",
                model,
                type(error).__name__,
                error
            )

            return None

    logger.error(
        "All Gemini models failed. Models attempted: %s",
        ", ".join(MODEL_FALLBACKS)
    )

    return None


def parse_response(raw_ai_response_text):

    """Extract and parse JSON from the raw response text.
    Returns a dict on success, or None if the response
    can't be turned into one."""

    if raw_ai_response_text is None:
        return None

    if not isinstance(raw_ai_response_text, str):
        return None

    text = raw_ai_response_text.strip()

    if not text:
        return None

    text = filtering._strip_code_fences(text)
    text = filtering._extract_json_block(text)

    if not text:
        return None

    try:
        data = json.loads(text)

    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    return data


def validate_response(data):

    # Entire response must be a dictionary
    if not isinstance(data, dict):
        return False

    # =====================================================
    # DISTANCE LOGIC CHANGE 3:
    # Validate proximity preference information
    # =====================================================

    if "proximity_preference" not in data:
        return False

    proximity = data["proximity_preference"]

    if not isinstance(proximity, dict):
        return False

    for field in EXPECTED_PROXIMITY_FIELDS:
        if field not in proximity:
            return False

    # specified must be boolean
    if not isinstance(proximity["specified"], bool):
        return False

    preferences = proximity["preferences"]

    # preferences must be a list
    if not isinstance(preferences, list):
        return False

    preference_targets = set()

    for preference in preferences:

        if not isinstance(preference, str):
            return False

        if not preference.strip():
            return False

        normalised_preference = preference.strip().lower()

        # Do not allow duplicate preference locations
        if normalised_preference in preference_targets:
            return False

        preference_targets.add(normalised_preference)

    # specified=True must have at least one preference
    if proximity["specified"] and len(preferences) == 0:
        return False

    # specified=False must have no preferences
    if not proximity["specified"] and len(preferences) != 0:
        return False


    # -----------------------------------------------------
    # Hotels
    # -----------------------------------------------------

    if "hotels" not in data:
        return False

    hotels = data["hotels"]

    if not isinstance(hotels, list):
        return False

    # AI Manager must return exactly 10 candidates
    if len(hotels) != AI_CANDIDATE_COUNT:
        return False

    hotel_names = set()

    for hotel in hotels:

        # Each hotel must be a dictionary
        if not isinstance(hotel, dict):
            return False

        # All expected keys must exist
        for field in EXPECTED_HOTEL_FIELDS:
            if field not in hotel:
                return False


        # -------------------------
        # Name
        # -------------------------

        if not isinstance(hotel["name"], str):
            return False

        if not hotel["name"].strip():
            return False

        hotel_name = hotel["name"].strip().lower()

        if hotel_name in hotel_names:
            return False

        hotel_names.add(hotel_name)


        # -------------------------
        # City
        # -------------------------

        if not isinstance(hotel["city"], str):
            return False

        if not hotel["city"].strip():
            return False


        # -------------------------
        # Country
        # -------------------------

        if not isinstance(hotel["country"], str):
            return False

        if not hotel["country"].strip():
            return False


        # -------------------------
        # Price
        # -------------------------

        price = hotel["price_per_night_sgd"]

        if (
            not isinstance(price, (int, float))
            or isinstance(price, bool)
        ):
            return False

        if price <= 0:
            return False


        # -------------------------
        # Rating
        # -------------------------

        rating = hotel["rating"]

        if rating is not None:

            if (
                not isinstance(rating, (int, float))
                or isinstance(rating, bool)
            ):
                return False

            if not 0 <= rating <= 5:
                return False


        # -------------------------
        # Amenities
        # -------------------------

        if not isinstance(hotel["amenities"], list):
            return False


        # =================================================
        # DISTANCE LOGIC CHANGE 4:
        # Validate distances to user preferences
        # =================================================

        distances = hotel["distance_to_preferences"]

        if not isinstance(distances, list):
            return False

        distance_targets = set()

        for distance_item in distances:

            if not isinstance(distance_item, dict):
                return False

            for field in EXPECTED_DISTANCE_FIELDS:
                if field not in distance_item:
                    return False

            target = distance_item["target"]

            if not isinstance(target, str):
                return False

            if not target.strip():
                return False

            normalised_target = target.strip().lower()

            # Prevent duplicate targets for the same hotel
            if normalised_target in distance_targets:
                return False

            distance_targets.add(normalised_target)

            distance_m = distance_item["distance_m"]

            if distance_m is not None:

                if (
                    not isinstance(distance_m, (int, float))
                    or isinstance(distance_m, bool)
                ):
                    return False

                if distance_m < 0:
                    return False


        # Every hotel must contain exactly the same
        # preference targets that the AI extracted above.
        #
        # When no preference exists, both sets are empty.
        if distance_targets != preference_targets:
            return False


        # -------------------------
        # Nearby food
        # -------------------------

        if not isinstance(hotel["nearby_food"], list):
            return False


        # =================================================
        # DISTANCE LOGIC CHANGE 5:
        # Nearby activities now include their distance
        # =================================================

        activities = hotel["nearby_activities"]

        if not isinstance(activities, list):
            return False

        for activity in activities:

            if not isinstance(activity, dict):
                return False

            for field in EXPECTED_ACTIVITY_FIELDS:
                if field not in activity:
                    return False

            if not isinstance(activity["name"], str):
                return False

            if not activity["name"].strip():
                return False

            activity_distance = activity["distance_m"]

            if activity_distance is not None:

                if (
                    not isinstance(activity_distance, (int, float))
                    or isinstance(activity_distance, bool)
                ):
                    return False

                if activity_distance < 0:
                    return False

    return True


# This will be used to access all the other functions

def data_process(record, client):

    prompt = build_prompt(record)

    ai_response_text = call_api(
        prompt,
        client
    )

    # API failure is different from invalid AI output.
    # There is nothing to correct if no response was returned.
    if ai_response_text is None:

        logger.error(
            "AI processing stopped because no Gemini model returned a response."
        )

        return None

    ai_response_parse = parse_response(
        ai_response_text
    )

    # First response is valid
    if validate_response(ai_response_parse):
        return ai_response_parse

    # -----------------------------------------------------
    # One correction attempt
    # -----------------------------------------------------

    logger.warning(
        "Gemini returned an invalid response. "
        "Attempting one regeneration."
    )

    correction_prompt = build_correction_prompt(
        prompt,
        ai_response_text
    )

    corrected_response_text = call_api(
        correction_prompt,
        client
    )

    # Stop if the API failed during the correction attempt
    if corrected_response_text is None:

        logger.error(
            "Correction attempt stopped because no Gemini model returned a response."
        )

        return None

    corrected_response_parse = parse_response(
        corrected_response_text
    )

    # Corrected response is valid
    if validate_response(corrected_response_parse):
        return corrected_response_parse

    # Still invalid after one correction attempt
    logger.error(
        "Gemini response remained invalid after regeneration."
    )

    return None