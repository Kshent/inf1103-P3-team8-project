import os
import json
import re
from dotenv import load_dotenv
from google import genai

import ai_filter as filtering

load_dotenv(".env")


MODEL_VERSION = "gemini-3.6-flash"
REQUIRED_HOTEL_FIELDS = [
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



def call_api(prompt, client):

    #catch connection errors and timeouts; log do not crash

    response = client.models.generate_content(model=MODEL_VERSION, contents=prompt)
    if not response.text:
        raise ValueError("Gemini returned an empty response.")
    return response.text




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




#This will be used to access all the other functions
def data_process(record, client):

    prompt = build_prompt(record)

    ai_response_text = call_api(prompt, client)
    ai_response_parse = parse_response(ai_response_text)
    return ai_response_parse