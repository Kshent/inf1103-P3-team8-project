import os


class AIConfig:
    """Central configuration for AI processing and response validation."""

    PRIMARY_MODEL = "gemini-3.5-flash-lite"
    BACKUP_MODEL = "gemini-3.7-flash"
    TERTIARY_MODEL = "gemini-3.6-flash"

    MODEL_FALLBACKS = (
        PRIMARY_MODEL,
        BACKUP_MODEL,
        TERTIARY_MODEL,
    )

    AI_CANDIDATE_COUNT = 10

    EXPECTED_HOTEL_FIELDS = (
        "name",
        "city",
        "country",
        "price_per_night_sgd",
        "rating",
        "amenities",
        "distance_to_preferences",
        "nearby_food",
        "nearby_activities",
    )

    EXPECTED_PROXIMITY_FIELDS = (
        "specified",
        "preferences",
    )

    EXPECTED_DISTANCE_FIELDS = (
        "target",
        "distance_m",
    )

    EXPECTED_ACTIVITY_FIELDS = (
        "name",
        "distance_m",
    )

    RECOVERABLE_API_ERROR_CODES = frozenset({404, 408, 429, 500, 502, 503, 504})

    LOG_DIRECTORY = "logs"
    AI_ERROR_LOG_FILE = os.path.join(LOG_DIRECTORY, "ai_api_errors.log")
