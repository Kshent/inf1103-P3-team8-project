from __future__ import annotations

from .ai_config import AIConfig
from .prompt_builder import PromptBuilder


class HotelPromptBuilder(PromptBuilder):
    """Builds the normal hotel prompt and the one permitted correction prompt."""

    def __init__(self, candidate_count: int = AIConfig.AI_CANDIDATE_COUNT):
        self.__candidate_count = candidate_count

    def build_prompt(self, record: dict) -> str:
        """Build the hotel recommendation prompt using the user's search details."""

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


Return exactly {self.__candidate_count} distinct hotel candidates
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

    def build_correction_prompt(
        self,
        original_prompt: str,
        invalid_response: str,
    ) -> str:
        """Build one correction prompt after malformed or invalid AI output."""

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
- Return exactly {self.__candidate_count} distinct hotel objects.
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