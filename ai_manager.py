import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import errors
import logging
import ai_filter as filtering

load_dotenv(".env")


PRIMARY_MODEL = "gemini-3.8-flash"
BACKUP_MODEL = "gemini-3.7-flash"
TERTIARY_MODEL = "gemini-3.5-flash-lite"

MODEL_FALLBACKS = [
    PRIMARY_MODEL,
    BACKUP_MODEL,
    TERTIARY_MODEL
]

EXPECTED_HOTEL_FIELDS = [
    "name", "city", "country", "price_per_night_sgd", "rating",
    "amenities", "distance_to_mrt_m", "nearby_food", "nearby_activities",
]


def get_model(api_key=None):
    if api_key is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        print(api_key)
    if not api_key:
        print("api key is not found unfortunately.")
        return None
    return genai.Client(api_key=api_key)



def build_prompt(record):

    """Build a clear, specific prompt from the record dict, instructing
    the model to reply with JSON only."""
    prefs = (record.get("preferences") or "").strip() or "No additional preferences."


    return f"""
    You are a hotel-recommendation engine. Reply with STRICT JSON ONLY - no
    markdown, no commentary.
    
    Destination: {record.get('destination')}
    Budget (SGD/night): {record.get('budget_min')} to {record.get('budget_max')}
    Preferences: {prefs}
    
    For each hotel, also infer: nearby_food (2-3 suggestions), nearby_activities
    (2-3 suggestions), distance_to_mrt_m (meters, or null if unknown), and
    rating (out of 5).
    
    Return 3 hotels as JSON matching exactly this schema and nothing else:
    {{
    "hotels": [
        {{
        "name": "string", "city": "string", "country": "string",
        "price_per_night_sgd": number, "rating": number,
        "amenities": ["string"], "distance_to_mrt_m": number or null,
        "nearby_food": ["string"], "nearby_activities": ["string"]
        }}
    ]
    }}
    """.strip()




logger = logging.getLogger(__name__)
def call_api(prompt, client):

    for model in MODEL_FALLBACKS:

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            # Successful response
            if response.text:
                return response.text

            # Empty response -> try next model
            logger.warning(
                "%s returned an empty response. Trying fallback model.",
                model
            )
            continue

        except errors.APIError as error:

            # Errors where trying another model may help
            if error.code in {
                404, #model unavailable
                408, #timeout
                429, #rate limit
                500, #server error
                502, #server error
                503, #server error
                504 #server error
            }:
                logger.warning(
                    "%s failed with error %s. Trying fallback model.",
                    model,
                    error.code
                )
                continue

            # Non-recoverable errors such as 400 (bad request), 401 (invalid API key), 402(Token payment needed), 403 (permission issue)
            logger.error(
                "Gemini API error %s: %s",
                error.code,
                error
            )
            return None

        except (TimeoutError, ConnectionError):

            logger.warning(
                "%s had a connection problem. Trying fallback model.",
                model
            )
            continue

    # All models failed. 
    logger.error("All Gemini models failed.")
    return None




def parse_response(raw_ai_response_text):
    """Extract and parse JSON from the raw response text. Returns a dict
    on success, or None if the response can't be turned into one - every
    unexpected format is caught and handled instead of crashing the
    program. No print() here - that stays in io_manager.py; the caller
    decides what, if anything, to tell the user when this returns None."""

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


    #Important : returns data as a dictinoary
    return data


def validate_response(data):

    # Entire response must be a dictionary
    if not isinstance(data, dict):
        return False

    # Must contain "hotels"
    if "hotels" not in data:
        return False

    hotels = data["hotels"]

    # Hotels must be a list
    if not isinstance(hotels, list):
        return False

    # Project requires exactly 3 hotel recommendations
    if len(hotels) != 3:
        return False

    for hotel in hotels:

        # Each hotel must be a dictionary
        if not isinstance(hotel, dict):
            return False

        # All expected keys must exist
        for field in EXPECTED_HOTEL_FIELDS:
            if field not in hotel:
                return False

        # -------------------------
        # Required core values
        # -------------------------

        # Name
        if not isinstance(hotel["name"], str):
            return False

        if not hotel["name"].strip():
            return False

        # City
        if not isinstance(hotel["city"], str):
            return False

        if not hotel["city"].strip():
            return False

        # Country
        if not isinstance(hotel["country"], str):
            return False

        if not hotel["country"].strip():
            return False

        # Price
        price = hotel["price_per_night_sgd"]

        if not isinstance(price, (int, float)):
            return False

        if price <= 0:
            return False

        # -------------------------
        # Rating
        # Key required, None allowed
        # -------------------------

        rating = hotel["rating"]

        if rating is not None:

            if not isinstance(rating, (int, float)):
                return False

            if not 0 <= rating <= 5:
                return False

        # -------------------------
        # Amenities
        # Key required, [] allowed
        # -------------------------

        if not isinstance(hotel["amenities"], list):
            return False

        # -------------------------
        # MRT distance
        # Key required, None allowed
        # -------------------------

        distance = hotel["distance_to_mrt_m"]

        if distance is not None:

            if not isinstance(distance, (int, float)):
                return False

            if distance < 0:
                return False

        # -------------------------
        # Nearby food
        # Key required, [] allowed
        # -------------------------

        if not isinstance(hotel["nearby_food"], list):
            return False

        # -------------------------
        # Nearby activities
        # Key required, [] allowed
        # -------------------------

        if not isinstance(hotel["nearby_activities"], list):
            return False

    return True


#This will be used to access all the other functions
def data_process(record, client):

    prompt = build_prompt(record)

    ai_response_text = call_api(prompt, client)
    ai_response_parse = parse_response(ai_response_text)

    if not validate_response(ai_response_parse):
        logger.warning("Gemini returned an invalid response structure.")
        return None

    return ai_response_parse
