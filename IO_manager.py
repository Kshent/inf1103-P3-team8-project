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
 

# ===========================================================================
# The view
# ===========================================================================
class ConsoleView:
    """Asks the traveller questions and shows results."""
 
    def __init__(self, source=None, sink=None, formatter=None):
        self.__source = source or ConsoleInput()
        self.__sink = sink or ConsoleOutput()
        self.__formatter = formatter or HotelFormatter()



    # -- internal helpers --------------------------------------------------
    def _show(self, lines):
        for line in lines:
            self.__sink.write(line)
 
    def _ask(self, prompt, validator):
        """Keep asking until the validator accepts the answer."""
        while True:
            result = validator.validate(self.__source.read(prompt))
            if result.ok:
                return result.value
            self.__sink.write(f"Error: {result.message}")
 
    # -- menus -------------------------------------------------------------
    def show_main_menu(self):
        """Show the main menu and return a valid choice: "1" to "4"."""
        validator = ChoiceValidator(("1", "2", "3", "4"),
                                    "Invalid option. Please enter 1, 2, 3 or 4")
        while True:
            self.__sink.write("\nWelcome to Team8's hotel recommendation app!\n")
            self.__sink.write("\n----------------------------------------------")
            self.__sink.write("1: Find a suitable hotel for your overseas "
                              "travel needs!")
            self.__sink.write("2: View your previous hotel records")
            self.__sink.write("3: Admin login (NOT FOR USERS)")
            self.__sink.write("4: Quit")
 
            result = validator.validate(self.__source.read(
                "Please enter option 1, 2, 3 or 4: "))
            if result.ok:
                return result.value
            self.__sink.write(result.message)
 
    # -- search inputs -----------------------------------------------------
    def request_mandatory_inputs(self):
        """Collect everything required before a search can begin."""
        self.__sink.write("\n=== Hotel Search ===")
        location = self._ask("Enter your destination country or city: ",
                             LocationValidator())
        price_range = self._ask(
            "Enter your price range in SGD, for example 100-250: ",
            PriceRangeValidator())
        email_address = self._ask("Enter your email address: ",
                                  EmailValidator())
        return {"location": location, "price_range": price_range,
                "email_address": email_address}
 
    def request_user_preferences(self):
        """Optional free-text preferences (an empty answer is allowed)."""
        self.__sink.write(
            "\nDescribe your hotel preferences. For example: near public "
            "transport, breakfast included, quiet room and swimming pool.")
        return self._ask("\nYour preferences: ", PreferencesValidator())
 
    def request_priority_profile(self, options, categories, saved=None):
        """Let the traveller choose how hotels are weighed (new feature).
 
        options    - [{"name", "label", "description"}, ...] preset profiles
        categories - [{"key", "label"}, ...] used by the Custom choice
        saved      - the profile dict saved from last time, or None
 
        Returns {"name": ..., "weights": {...} or None}."""
        write = self.__sink.write
        write("\n=== Priorities ===")
        write("What matters most to you? This changes how hotels are scored.")
 
        choices = {}
        for number, option in enumerate(options, start=1):
            write(f"{number}: {option['label']} - {option['description']}")
            choices[str(number)] = option["name"]
        custom_number = str(len(options) + 1)
        write(f"{custom_number}: Custom - rate each category yourself")
        choices[custom_number] = "custom"
 
        if saved:
            hint = ("press Enter to keep your saved choice: "
                    f"{saved.get('label') or saved.get('name')}")
        else:
            hint = f"press Enter for {options[0]['label']}"
 
        validator = ChoiceValidator(
            [""] + list(choices),
            f"Please enter a number from 1 to {custom_number}.")
        answer = self._ask(f"Choose 1-{custom_number} ({hint}): ", validator)
 
        if answer == "":
            return saved if saved else {"name": options[0]["name"],
                                        "weights": None}
        name = choices[answer]
        if name != "custom":
            return {"name": name, "weights": None}
 
        write("Rate how important each category is, from 1 (low) to 5 (high).")
        rating_validator = IntegerRangeValidator(1, 5)
        weights = {category["key"]: self._ask(
            f"  {category['label']} (1-5): ", rating_validator)
            for category in categories}
        return {"name": "custom", "weights": weights}
 
    # -- records and admin -------------------------------------------------
    def request_record_email(self):
        """Ask for the email whose records to view. Returns the lower-case
        email, or None if the user typed q."""
        validator = EmailValidator()
        while True:
            email = self.__source.read("Enter your email or q to quit: ")
            if email.lower() == "q":
                self.__sink.write("Exiting view hotel records")
                return None
            result = validator.validate(email)
            if result.ok:
                return result.value.lower()
            self.__sink.write(f"Invalid input : {result.message}")
 
    def admin_login(self, authenticator):
        """Returns True if login succeeds, False if the user quits with Q.
        `authenticator` is any object with check_username / check_password."""
        while True:
            username = self.__source.read("Enter username or Q to exit: ")
            if username.upper() == "Q":
                return False
            if not authenticator.check_username(username):
                self.__sink.write("Wrong username")
                continue
 
            while True:
                password = self.__source.read("Enter password or Q to exit: ")
                if password.upper() == "Q":
                    return False
                if not authenticator.check_password(password):
                    self.__sink.write("Wrong password")
                    continue
                return True
 
    # -- display -----------------------------------------------------------
    def display_message(self, message):
        self.__sink.write(message)
 
    def display_ai_dictionary(self, ai_dictionary):
        """Show the AI Manager's output as a plain dictionary."""
        self.__sink.write(ai_dictionary)
 
    def display_top_three_dictionary(self, top_three_dict):
        """Show the chosen top hotels as a plain dictionary."""
        self.__sink.write("\n=== TOP 3 HOTELS (DICTIONARY OUTPUT) ===")
        self.__sink.write(top_three_dict)
        self.__sink.write("=== END OF TOP 3 HOTELS (DICTIONARY OUTPUT) ===\n")
 
    def display_recommendations(self, result, record):
        """Show the Logic Manager's top hotels with score and breakdown."""
        self._show(self.__formatter.recommendation_report(result, record))
 
    def display_records(self, records):
        """Show records shaped like
        [{"email": email, "searches": [[hotels], ...]}]."""
        self._show(self.__formatter.records(records))
