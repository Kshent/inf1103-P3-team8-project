import os
import json
from dotenv import load_dotenv
from google import genai

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

    response = client.models.generate_content(model=MODEL_VERSION, contents=prompt)
    if not response.text:
        raise ValueError("Gemini returned an empty response.")
    return response.text


#This will be used to access all the other functions
def data_process(record, client):

    prompt = build_prompt(record)

    ai_response_text = call_api(prompt, client)
    return ai_response_text


