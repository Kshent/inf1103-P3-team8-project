from __future__ import annotations

from .ai_config import AIConfig
from .response_validator import ResponseValidator


class HotelResponseValidator(ResponseValidator):
    """Validates the structured hotel response returned by the AI.

    The validation rules preserve the behaviour of the Phase 1
    AI Manager while separating validation into a dedicated class.
    """

    def __init__(
        self,
        candidate_count: int = AIConfig.AI_CANDIDATE_COUNT,
    ):
        self.__candidate_count = candidate_count

    def find_errors(self, data) -> list[str]:
        """Return validation errors. An empty list means the response is valid."""

        if not isinstance(data, dict):
            return ["Response is not a JSON object."]

        errors: list[str] = []

        preference_targets = self.__check_proximity(
            data.get("proximity_preference"),
            errors,
        )

        hotels = data.get("hotels")

        if not isinstance(hotels, list):
            errors.append("'hotels' must be a list.")
            return errors

        if preference_targets is None:
            return errors

        if len(hotels) != self.__candidate_count:
            errors.append(
                f"Expected exactly {self.__candidate_count} hotels, "
                f"got {len(hotels)}."
            )

        hotel_names: set[str] = set()

        for index, hotel in enumerate(hotels):
            self.__check_hotel(
                f"hotels[{index}]",
                hotel,
                preference_targets,
                hotel_names,
                errors,
            )

        return errors

    def __check_proximity(
        self,
        proximity,
        errors: list[str],
    ) -> set[str] | None:
        """Validate proximity preference information."""

        if (
            not isinstance(proximity, dict)
            or not self._has_fields(
                proximity,
                AIConfig.EXPECTED_PROXIMITY_FIELDS,
            )
        ):
            errors.append(
                "'proximity_preference' must be an object with "
                "'specified' and 'preferences'."
            )
            return None

        specified = proximity["specified"]
        preferences = proximity["preferences"]

        if not isinstance(specified, bool):
            errors.append(
                "'proximity_preference.specified' must be a boolean."
            )
            return None

        if not isinstance(preferences, list):
            errors.append(
                "'proximity_preference.preferences' must be a list."
            )
            return None

        preference_targets: set[str] = set()

        for preference in preferences:

            if not self._is_text(preference):
                errors.append(
                    "'proximity_preference.preferences' must contain "
                    "non-empty strings."
                )
                return None

            normalised_preference = preference.strip().lower()

            if normalised_preference in preference_targets:
                errors.append(
                    "'proximity_preference.preferences' must not "
                    "contain duplicate locations."
                )
                return None

            preference_targets.add(normalised_preference)

        if specified and len(preferences) == 0:
            errors.append(
                "'specified' cannot be true when 'preferences' is empty."
            )
            return None

        if not specified and len(preferences) != 0:
            errors.append(
                "'specified' cannot be false when proximity "
                "preferences exist."
            )
            return None

        return preference_targets

    def __check_hotel(
        self,
        label: str,
        hotel,
        preference_targets: set[str],
        hotel_names: set[str],
        errors: list[str],
    ) -> None:
        """Validate one hotel candidate."""

        if not isinstance(hotel, dict):
            errors.append(f"{label} must be an object.")
            return

        if not self._has_fields(
            hotel,
            AIConfig.EXPECTED_HOTEL_FIELDS,
        ):
            errors.append(f"{label} is missing required fields.")
            return

        # Name
        name = hotel["name"]

        if not self._is_text(name):
            errors.append(
                f"{label}.name must be a non-empty string."
            )
        else:
            normalised_name = name.strip().lower()

            if normalised_name in hotel_names:
                errors.append(
                    f"{label}.name is a duplicate."
                )
            else:
                hotel_names.add(normalised_name)

        # City and country
        for field in ("city", "country"):
            if not self._is_text(hotel[field]):
                errors.append(
                    f"{label}.{field} must be a non-empty string."
                )

        # Price
        price = hotel["price_per_night_sgd"]

        if not self._is_number(price) or price <= 0:
            errors.append(
                f"{label}.price_per_night_sgd must be "
                "a positive number."
            )

        # Rating
        rating = hotel["rating"]

        if rating is not None:
            if (
                not self._is_number(rating)
                or not 0 <= rating <= 5
            ):
                errors.append(
                    f"{label}.rating must be a number "
                    "from 0 to 5, or null."
                )

        # Amenities
        if not isinstance(hotel["amenities"], list):
            errors.append(
                f"{label}.amenities must be a list."
            )

        # Distances
        self.__check_distances(
            label,
            hotel["distance_to_preferences"],
            preference_targets,
            errors,
        )

        # Nearby food
        if not isinstance(hotel["nearby_food"], list):
            errors.append(
                f"{label}.nearby_food must be a list."
            )

        # Nearby activities
        self.__check_activities(
            label,
            hotel["nearby_activities"],
            errors,
        )

    def __check_distances(
        self,
        label: str,
        distances,
        preference_targets: set[str],
        errors: list[str],
    ) -> None:
        """Validate distances to proximity preferences."""

        if not isinstance(distances, list):
            errors.append(
                f"{label}.distance_to_preferences must be a list."
            )
            return

        distance_targets: set[str] = set()

        for distance_item in distances:

            if not isinstance(distance_item, dict):
                errors.append(
                    f"{label} has a malformed distance entry."
                )
                return

            if not self._has_fields(
                distance_item,
                AIConfig.EXPECTED_DISTANCE_FIELDS,
            ):
                errors.append(
                    f"{label} has a malformed distance entry."
                )
                return

            target = distance_item["target"]

            if not self._is_text(target):
                errors.append(
                    f"{label} has an invalid distance target."
                )
                return

            normalised_target = target.strip().lower()

            if normalised_target in distance_targets:
                errors.append(
                    f"{label} repeats distance target "
                    f"'{normalised_target}'."
                )
                return

            distance_targets.add(normalised_target)

            distance_m = distance_item["distance_m"]

            if not self._is_optional_distance(distance_m):
                errors.append(
                    f"{label} has an invalid distance value."
                )
                return

        if distance_targets != preference_targets:
            errors.append(
                f"{label}.distance_to_preferences targets do not "
                "match the proximity preferences."
            )

    def __check_activities(
        self,
        label: str,
        activities,
        errors: list[str],
    ) -> None:
        """Validate nearby activity information."""

        if not isinstance(activities, list):
            errors.append(
                f"{label}.nearby_activities must be a list."
            )
            return

        for activity in activities:

            if not isinstance(activity, dict):
                errors.append(
                    f"{label} has a malformed nearby activity."
                )
                return

            if not self._has_fields(
                activity,
                AIConfig.EXPECTED_ACTIVITY_FIELDS,
            ):
                errors.append(
                    f"{label} has a malformed nearby activity."
                )
                return

            if not self._is_text(activity["name"]):
                errors.append(
                    f"{label} has an invalid nearby activity name."
                )
                return

            if not self._is_optional_distance(
                activity["distance_m"]
            ):
                errors.append(
                    f"{label} has an invalid nearby activity distance."
                )
                return

    @staticmethod
    def _has_fields(mapping, fields) -> bool:
        """Return True when all required fields exist."""

        return all(field in mapping for field in fields)

    @staticmethod
    def _is_text(value) -> bool:
        """Return True for a non-empty string."""

        return (
            isinstance(value, str)
            and bool(value.strip())
        )

    @staticmethod
    def _is_number(value) -> bool:
        """Match the numeric checks used in Phase 1."""

        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
        )

    @classmethod
    def _is_optional_distance(cls, value) -> bool:
        """Validate a nullable, non-negative distance."""

        if value is None:
            return True

        if not cls._is_number(value):
            return False

        return not value < 0