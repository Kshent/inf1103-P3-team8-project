"""
IO_Manager.py - Input/Output Manager for handling user interactions.


Responsibilities:
1. Collect traveller input from the CLI.
2. Validate user-provided information.
3. Display hotel recommendations and saved records.

This layer must not contain hotel ranking logic, AI logic or file storage.
It also does not import the other layers: it receives plain dictionaries
(and, for admin login and profile choices, small objects/lists passed in by
app.py) and returns plain dictionaries.
 
Class map
---------
  InputSource (interface)   -> ConsoleInput, ScriptedInput
  OutputSink (interface)    -> ConsoleOutput, BufferOutput
  FieldValidator (abstract) -> LocationValidator, PriceRangeValidator,
                               EmailValidator, PreferencesValidator,
                               ChoiceValidator, IntegerRangeValidator
  HotelFormatter            turns results into lines of text (no printing)
  ConsoleView               asks questions and shows results
 
ConsoleView only depends on the InputSource / OutputSink interfaces, so tests
can drive it with ScriptedInput and BufferOutput instead of a real keyboard
and screen.
"""


from curses import raw
import re
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# ===========================================================================
# Input and output channels
# ===========================================================================
class InputCancelled(EOFError):
    """Raised when the user cancels input."""

class InputSource(ABC):
    """Abstract base class for input sources."""

    @abstractmethod
    def read(self, prompt):
        """Show the prompt and return the user's reply."""
        pass

class ConsoleInput(InputSource):
    """Reads from the keyboard. Turns Ctrl-C / Ctrl-D into InputCancelled
      so the application never crashed with a traceback."""

    def __init__(self, input_function=input):
        self.input_function = input_function

    def read(self, prompt):
        try:
            value = self.input_function(prompt)
        except (KeyboardInterrupt, EOFError):
            raise InputCancelled("\nInput cancelled. Goodbye.") from None
        if value is None:
            raise InputCancelled("\nInput cancelled. Goodbye.")
        return value.strip()

class ScriptInput(InputSource):
    """Returns pre-written answers one by one. Used for testing."""

    def __init__(self, answers):
        self.__answers = list(answers)
        self.prompt = []       #every prompt that was shown


    def read(self, prompt):
        self.prompts.append(prompt)
        if not self.__answers:
            raise InputCancelled("\nInput cancelled. Goodbye.") 
        return str(self.__answers.pop(0)).strip()   


    
class OutputSink(ABC):
    """Abstract base class for output sinks."""

    @abstractmethod
    def write(self, text):
     """Show one line of text."""


class ConsoleOutput(OutputSink):
    """Writes to the console."""

    def __init__(self, output_function=print):
        self.output_function = output_function

    def write(self, text):
        self.output_function(text)

class BufferOutput(OutputSink):
    """Collects output in a list. Used for testing."""

    def __init__(self):
        self.lines = []

    def write(self, text):
        self.lines.append(text)


# ===========================================================================
# Validators (abstract class with a template method)
# ===========================================================================
@dataclass(frozen=True)
class ValidationResult:
    ok:boolmessage: str = ""
    value: Any = None


class FieldValidator(ABC):
    """validate() is the template: normalise the text, then run the subclass's own _check()."""
        
    def validate(self, raw):
        if not isinstance(raw, str):
            return self._fail("Value must be text.")
        return self._check(self._normalise(raw))

    def _normalise(self, raw):
        return raw.strip()

    abstractmethod
    def _check(self, text):
        ...

    @staticmethod
    def _ok(value):
        return ValidationResult(True, "", value)

    @staticmethod
    def _fail(message):
        return ValidationResult(False, message, None)


class LocationValidator(FieldValidator):
        """Accepts country and city names, including multi-part destinations. 
        The geonamescache name list is built once and the reused."""

        _known_names = None
        _lookup_failed = False

        def _check(self, value):
            if not value:
                return self._fail("Location cannot be empty.")
            if len(value) < 2:
                return self._fail("Location must contain at least 2 characters.")
            if len(value) > 100:
                return self._fail("Location must not exceed 100 characters.")


            names = self._names()
            if names is None:        # geonamescache unavailable: accept
                return self._ok(value)
            if " ".join(value.split()).lower() in names:
                return self._ok(value)
                return self._fail(
                    "Location validation is temporarily unavailable. "
                    "Please try again later."
                )

        @classmethod
        def _names(cls):
            if cls._known_names is None and not cls._lookup_failed:
            try:
                from geonamescache import GeonamesCache
                geonames = GeonamesCache()
                names = set()
                for code, country in geonames.get_countries().items():
                    names.add(code.lower())
                    names.add(str(country.get("name", "")).lower())
                for city in geonames.get_cities().values():
                    names.add(str(city.get("name", "")).lower())
                cls._known_names = frozenset(names)
            except Exception:          # noqa: BLE001 - fall back to accepting
                cls._lookup_failed = True
        return cls._known_names

            
class PriceRangeValidator(FieldValidator):
    """Accepts a price range in SGD, e.g. 100-250 or 100,250."""

    _PATTERN = re.compile(r"(\d+(?:\.\d+)?)(?:-|,|TO)(\d+(?:\.\d+)?)")
 
    def _check(self, value):
        if not value:
            return self._fail("Price range cannot be empty.")
 
        cleaned = value.upper().replace("SGD", "").replace("S$", "")
        cleaned = re.sub(r"\s+", "", cleaned.replace("$", ""))
        match = self._PATTERN.fullmatch(cleaned)
        if not match:
            return self._fail("Enter a valid SGD price range, for example "
                              "100-250 or SGD 100-SGD 250.")
 
        minimum = float(match.group(1))
        maximum = float(match.group(2))
        if minimum <= 0 or maximum <= 0:
            return self._fail("Prices must be greater than zero.")
        if minimum > maximum:
            return self._fail("The minimum price cannot be higher than the "
                              "maximum price.")
        if maximum > 1_000_000:
            return self._fail("The maximum price is too high.")
 
        return self._ok({"min": round(minimum, 2), "max": round(maximum, 2),
                         "currency": "SGD"})


class EmailValidator(FieldValidator):
    _PATTERN = re.compile(
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$")
 
    def _check(self, value):
        if not value:
            return self._fail("Email address cannot be empty.")
        if len(value) > 254:          # RFC limit
            return self._fail("Email address is too long.")
        if not self._PATTERN.fullmatch(value):
            return self._fail("Please enter a valid email address.")
        return self._ok(value)
    

class PreferencesValidator(FieldValidator):
    """Preferences are optional: an empty answer is allowed."""
 
    MAX_LENGTH = 2_000
 
    def _check(self, value):
        if len(value) > self.MAX_LENGTH:
            return self._fail("Preferences must not exceed 2,000 characters.")
        return self._ok(value)

    
class ChoiceValidator(FieldValidator):
    def __init__(self, choices, message):
        self.__choices = tuple(choices)
        self.__message = message
 
    def _check(self, value):
        if value in self.__choices:
            return self._ok(value)
        return self._fail(self.__message)


class IntegerRangeValidator(FieldValidator):
    def __init__(self, low, high):
        self.__low = low
        self.__high = high
 
    def _check(self, value):
        if value.isdigit() and self.__low <= int(value) <= self.__high:
            return self._ok(int(value))
        return self._fail("Please enter a whole number from %d to %d."
                          % (self.__low, self.__high))
 

# ===========================================================================
# Formatting (builds text, never prints)
# ===========================================================================
class HotelFormatter:
    WIDTH = 78
    HEAVY_LINE = "=" * 70
    LIGHT_LINE = "-" * 70
 
    RATING_FOOTER = (
        "About the ratings: Every rating shown is the customer review rating "
        "(the average of guest reviews, as reported by the AI). It is not the "
        "hotel's number of stars. Scores come from fixed rules applied to the "
        "hotel data shown above.")
 

    # -- small helpers -----------------------------------------------------
    def _wrap(self, text, indent):
        return textwrap.fill(text, width=self.WIDTH, initial_indent=indent,
                             subsequent_indent=indent)
 
    @staticmethod
    def _money(value):
        return "S$%g" % value
 
    @staticmethod
    def _join(items):
        return ", ".join(items) if items else "Not listed"
 
    @staticmethod
    def _activity_text(activity):
        if isinstance(activity, dict):
            name = activity.get("name", "")
            distance = activity.get("distance_m")
            if isinstance(distance, (int, float)):
                return "%s (%s m)" % (name, "{:,}".format(int(distance)))
            return str(name)
        return str(activity)          # older saved records
 

 
    # -- saved records -----------------------------------------------------
    def hotel_list(self, hotels):
        """Lines for a plain list of hotel dictionaries (saved records)."""
        lines = []
        for number, hotel in enumerate(hotels, start=1):
            lines.append(f"\n  {number}. {hotel['name']}")
            lines.append(f"     {hotel['city']}, {hotel['country']}")
            lines.append(f"     SGD {hotel['price_per_night_sgd']} per night | "
                         f"Rating: {hotel['rating']}")
            lines.append(f"     Amenities: {', '.join(hotel['amenities'])}")
            lines.append("     Nearby food options: "
                         f"{', '.join(hotel['nearby_food'])}")
            activities = [self._plain_activity(a)
                          for a in hotel.get("nearby_activities", [])]
            lines.append(f"     Nearby activities: {', '.join(activities)}")
        return lines
 
    @staticmethod
    def _plain_activity(activity):
        if isinstance(activity, dict):
            name = activity.get("name", "Unknown")
            distance = activity.get("distance_m")
            return f"{name} ({distance}m)" if distance is not None else name
        return str(activity)
 
    def records(self, records):
        if not records:
            return ["\nNo records found."]
        lines = []
        for record in records:
            lines.append(f"\nEmail: {record['email']}")
            for number, hotels in enumerate(record["searches"], start=1):
                lines.append(f"\n  --- Search {number} ---")
                lines.extend(self.hotel_list(hotels))
        return lines
 
    # -- recommendation report ---------------------------------------------
    def recommendation_report(self, result, record):
        summary = result["summary"]
        requirements = result["requirements"]
        profile = result.get("profile")
 
        lines = ["", self.HEAVY_LINE, "TOP HOTEL RECOMMENDATIONS",
                 self.HEAVY_LINE,
                 "Destination : %s" % record.get("destination"),
                 "Budget      : %s - %s per night" % (
                     self._money(record.get("budget_min")),
                     self._money(record.get("budget_max"))),
                 "Preferences : %s" % (record.get("preferences") or "None")]
        if profile:
            lines.append("Priorities  : %s" % profile["label"])
        if requirements["targets"]:
            lines.append("Near        : %s" % ", ".join(requirements["targets"]))
        lines.append("Reviewed    : %d hotels | Shown: %d | Rejected: %d" % (
            summary["received"], summary["returned"], summary["rejected"]))
        lines.append(self.HEAVY_LINE)
 
        if requirements["unverified"]:
            lines.append(self._wrap(
                "Could not be checked against hotel data (so not scored): "
                + ", ".join(requirements["unverified"]) + ".", ""))
        for note in requirements["not_scored"]:
            lines.append(self._wrap(note, ""))
 
        if not result["top_hotels"]:
            lines += ["", "No hotels matched your requirements."]
        for hotel in result["top_hotels"]:
            lines.extend(self._hotel_block(hotel))
 
        if result["rejected_hotels"]:
            lines += ["", "REJECTED"]
            for hotel in result["rejected_hotels"]:
                lines.append(self._wrap(
                    "x %s: %s" % (hotel["name"], hotel["reject_reason"]), "  "))
            lines.append(self.LIGHT_LINE)
 
        lines += ["", self._wrap(self.RATING_FOOTER, ""), ""]
        return lines
 
    def _hotel_block(self, hotel):
        rating = hotel.get("rating")
        rating_text = ("%.1f / 5" % rating
                       if isinstance(rating, (int, float)) else "Not available")
 
        lines = ["", "#%d  %s" % (hotel["rank"], hotel["name"]),
                 "    SCORE: %d/%d - %s" % (hotel["score"], hotel["score_max"],
                                             hotel["verdict"]),
                 "    Price: %s per night" % self._money(
                     hotel["price_per_night_sgd"]),
                 "    Customer review rating: %s (average of guest reviews, "
                 "not hotel stars)" % rating_text]
        for item in hotel.get("distance_to_preferences") or []:
            distance = item.get("distance_m")
            if isinstance(distance, (int, float)):
                lines.append("    Distance: %s m from %s" % (
                    "{:,}".format(int(distance)), item.get("target")))
        lines.append(self._wrap("Amenities: " + self._join(
            hotel.get("amenities")), "    "))
        lines.append(self._wrap("Nearby food: " + self._join(
            hotel.get("nearby_food")), "    "))
        lines.append(self._wrap("Nearby activities: " + self._join(
            [self._activity_text(a)
             for a in hotel.get("nearby_activities") or []]), "    "))
 
        lines += ["", "    Why %d/%d:" % (hotel["score"], hotel["score_max"])]
        for line in hotel["breakdown"]:
            lines.append("      %-24s %2d / %2d" % (
                line["category"], line["points"], line["max"]))
            lines.append(self._wrap(line["reason"], "        "))
        lines.append("      %-24s %2d / %2d" % (
            "TOTAL", hotel["score"], hotel["score_max"]))
 
        if hotel.get("notes"):
            lines.append("")
            for note in hotel["notes"]:
                lines.append(self._wrap("Note: " + note, "    "))
        lines.append(self.LIGHT_LINE)
        return lines
 



def _safe_input(
    prompt: str,
    input_function: Callable[[str], str] = input
) -> str:
    """
    Centralised input reader for the I/O Manager.

    Prevents the application from crashing when a user
    exits the CLI unexpectedly.
    """
    try:
        value = input_function(prompt)
    except (KeyboardInterrupt, EOFError):
        raise EOFError("\nInput cancelled. Goodbye.") from None

    # Defensive validation in case a mock input function
    # returns None during testing.
    if value is None:
        raise EOFError("\nInput cancelled. Goodbye.")

    # Remove leading/trailing spaces before validation.
    return value.strip()


def validate_location(location: str) -> tuple[bool, str]:
    """
    Validate destination entered by the traveller.

    Accept country and city names, including multi-part destinations.
    """

    if not isinstance(location, str):
        return False, "Location must be text."

    location = location.strip()

    # Empty values are not allowed.
    if not location:
        return False, "Location cannot be empty."

    # Prevent unrealistic one-character locations.
    if len(location) < 2:
        return False, "Location must contain at least 2 characters."

    # Protect against excessively long user input.
    if len(location) > 100:
        return False, "Location must not exceed 100 characters."

    # Validate destination text so cities and neighbourhoods are accepted.
    if not re.fullmatch(r"[^\W\d_][\w\s.,'’()-]*", location, re.UNICODE):
        return False, (
            "Location contains invalid characters. "
            "Please enter a valid country or city name."
        )

    return True, ""


def validate_price_range(
    price_range: str
) -> tuple[bool, str, dict[str, int | float | str] | None]:
    """
    Validate traveller budget range in SGD.

    Examples:
        100-250
        100 - 250
        100,250
    """

    if not isinstance(price_range, str) or not price_range.strip():
        return False, "Price range cannot be empty.", None

    # Remove whitespace to support flexible user formatting.
    cleaned_value = re.sub(r"\s+", "", price_range)

    # Accept either hyphen or comma as a separator.
    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)[,-](\d+(?:\.\d+)?)",
        cleaned_value
    )

    if not match:
        return (
            False,
            "Enter the price range in this format: 100-250.",
            None
        )

    minimum_price = float(match.group(1))
    maximum_price = float(match.group(2))

    # Hotel prices must be positive values.
    if minimum_price <= 0 or maximum_price <= 0:
        return False, "Prices must be greater than zero.", None

    # Logical validation to ensure valid range ordering.
    if minimum_price > maximum_price:
        return (
            False,
            "The minimum price cannot be higher than the maximum price.",
            None
        )

    # Protect against unrealistic budget values.
    if maximum_price > 1_000_000:
        return False, "The maximum price is too high.", None

    # Return structured budget information for later layers.
    return True, "", {
        "min": round(minimum_price, 2),
        "max": round(maximum_price, 2),
        "currency": "SGD"
    }


def validate_email(email_address: str) -> tuple[bool, str]:
    """
    Validate traveller email address.

    Email is required because recommendations
    will be delivered through the Email Manager.
    """

    if not isinstance(email_address, str) or not email_address:
        return False, "Email address cannot be empty."

    # RFC-compliant email addresses cannot exceed 254 characters.
    if len(email_address) > 254:
        return False, "Email address is too long."

    email_pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    )

    if not re.fullmatch(email_pattern, email_address):
        return False, "Please enter a valid email address."

    return True, ""


def request_mandatory_inputs(
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print
) -> dict[str, Any]:
    """
    I/O Manager Step 1.

    Collect all mandatory traveller information
    required before hotel searching can begin.
    """

    output_function("\n=== Hotel Search ===")

    # Keep requesting destination until valid.
    while True:
        location = _safe_input(
            "Enter your destination country or city: ",
            input_function
        )

        is_valid, error_message = validate_location(location)

        if is_valid:
            break

        output_function(f"Error: {error_message}")

    # Keep requesting budget until valid.
    while True:
        price_input = _safe_input(
            "Enter your price range in SGD, for example 100-250: ",
            input_function
        )

        is_valid, error_message, price_range = validate_price_range(
            price_input
        )

        if is_valid:
            break

        output_function(f"Error: {error_message}")

    # Keep requesting email until valid.
    while True:
        email_address = _safe_input(
            "Enter your email address: ",
            input_function
        )

        is_valid, error_message = validate_email(email_address)

        if is_valid:
            break

        output_function(f"Error: {error_message}")

    # Return structured data for downstream managers.
    return {
        "location": location,
        "price_range": price_range,
        "email_address": email_address
    }


def request_user_preferences(
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print
) -> str:
    """
    I/O Manager Step 2.

    Capture traveller preferences that will be used
    by the AI Manager to personalise recommendations.
    """

    output_function(
        "\nDescribe your hotel preferences. "
        "For example: near public transport, breakfast included, "
        "quiet room and swimming pool."
    )

    while True:
        preferences = _safe_input(
            "\nYour preferences: ",
            input_function
        )

        # Allow the traveller to skip this step.
        if not preferences:
            return ""

        # Prevent excessively large text submissions.
        if len(preferences) > 2_000:
            output_function(
                "Error: Preferences must not exceed 2,000 characters."
            )
            continue

        return preferences


def build_ai_request(
    mandatory_inputs: dict[str, Any],
    preferences: str
) -> dict[str, Any]:
    """
    I/O Manager Step 3.

    Transform traveller inputs into a standard request
    format expected by the AI Manager.
    """

    return {
        "task": "Find suitable hotels for the traveller.",
        "destination": mandatory_inputs["location"],
        "price_range": mandatory_inputs["price_range"],
        "preferences": preferences,
        "required_response_format": {
            "hotels": [
                {
                    "name": "Hotel name",
                    "location": "Hotel location",
                    "price_per_night_sgd": 0,
                    "rating": 0,
                    "description": "Short description",
                    "amenities": [],
                    "booking_url": "https://example.com"
                }
            ]
        }
    }


def display_top_hotels(
    hotels: list[dict[str, Any]],
    output_function: Callable[[str], None] = print
) -> None:
    """
    Present final recommendations to the traveller.

    This function is responsible only for output formatting
    and does not perform any business logic.
    """

    if not hotels:
        output_function(
            "\nNo matching hotels were found for your search."
        )
        return

    output_function("\n=== Top Hotel Recommendations ===")

    # Display each hotel in a numbered format.
    for index, hotel in enumerate(hotels, start=1):

        output_function(
            f"\n{index}. {hotel.get('name', 'Unnamed hotel')}"
        )

        output_function(
            f"   Location: {hotel.get('location', 'Not provided')}"
        )

        output_function(
            "   Price per night: "
            f"SGD {hotel.get('price_per_night_sgd', 'Not provided')}"
        )

        output_function(
            f"   Rating: {hotel.get('rating', 'Not provided')}"
        )

        output_function(
            f"   Description: "
            f"{hotel.get('description', 'Not provided')}"
        )

        # Display amenities only when available.
        amenities = hotel.get("amenities", [])

        if amenities:
            output_function(
                f"   Amenities: {', '.join(map(str, amenities))}"
            )

        # Display booking link when provided by AI.
        if hotel.get("booking_url"):
            output_function(
                f"   Booking URL: {hotel['booking_url']}"
            )


def run_hotel_search(
    ai_manager: Any,
    data_manager: Any,
    logic_manager: Any,
    email_manager: Any,
    output_file_path: str = "hotel_recommendations.json",
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print
) -> bool:
    """
    Main I/O Manager orchestrator.

    Coordinates communication between:
    - User
    - AI Manager
    - Logic Manager
    - Data Manager
    - Email Manager
    """

    try:

        # Step 1: Collect mandatory traveller details.
        mandatory_inputs = request_mandatory_inputs(
            input_function=input_function,
            output_function=output_function
        )

        # Step 2: Collect optional preference details.
        preferences = request_user_preferences(
            input_function=input_function,
            output_function=output_function
        )

        # Build standard AI request payload.
        ai_request = build_ai_request(
            mandatory_inputs=mandatory_inputs,
            preferences=preferences
        )

        output_function("\nSearching for suitable hotels...")

        # Step 3: Request hotel recommendations from AI Manager.
        ai_response = ai_manager.generate_hotel_recommendations(
            ai_request
        )

        # Ensure AI Manager returned expected structure.
        if not isinstance(ai_response, dict):
            raise ValueError(
                "The AI Manager returned an invalid response."
            )

        hotels = ai_response.get("hotels")

        if not isinstance(hotels, list) or not all(
            isinstance(hotel, dict) for hotel in hotels
        ):
            raise ValueError(
                "The AI response does not contain a valid list of hotels."
            )

        # Step 4: Persist raw AI output for auditing and traceability.
        data_manager.save_ai_results(
            ai_response,
            output_file_path
        )

        # Step 5: Logic Manager selects best hotel recommendations.
        top_hotels = logic_manager.filter_top_hotels(
            hotels,
            limit=3
        )

        if not isinstance(top_hotels, list) or not all(
            isinstance(hotel, dict) for hotel in top_hotels
        ):
            raise ValueError(
                "The Logic Manager returned an invalid hotel list."
            )

        # Display shortlisted hotels in CLI.
        display_top_hotels(
            top_hotels,
            output_function=output_function
        )

        # Step 6: Deliver results to traveller's email.
        output_function(
            f"\nSending recommendations to "
            f"{mandatory_inputs['email_address']}..."
        )

        email_manager.send_hotel_recommendations(
            recipient_email=mandatory_inputs["email_address"],
            hotels=top_hotels
        )

        output_function(
            "\nSuccess: Hotel recommendations have been emailed."
        )
        return True

    except EOFError as error:
        # User intentionally stopped the workflow.
        output_function(str(error))
        return False

    except TimeoutError:
        # External dependency failed to respond in time.
        output_function(
            "\nError: The hotel search request timed out. "
            "Please try again later."
        )
        return False

    except ConnectionError:
        # Unable to reach one of the application managers/services.
        output_function(
            "\nError: Unable to connect to one of the application services."
        )
        return False

    except ValueError as error:
        # Validation or data structure errors have safe, local messages.
        output_function(
            f"\nError: {error}"
        )
        return False

    except Exception as error:
        # Prevent internal implementation details from leaking
        # to end users while still providing basic diagnostics.
        output_function(
            "\nUnexpected error: The hotel search could not be completed."
        )
        output_function(
            f"Technical details: {type(error).__name__}"
        )
        return False
