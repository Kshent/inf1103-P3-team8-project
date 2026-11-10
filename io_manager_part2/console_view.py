"""CLI boundary for the application: asks questions and shows results."""

import textwrap
from typing import Any, Callable

from .email_validator import EmailValidator
from .input_reader import InputReader
from .input_validator import InputValidator
from .location_validator import LocationValidator
from .price_range_validator import PriceRangeValidator
from .weight_validator import WeightValidator


class ConsoleView:
    """
    CLI boundary for the application.

    Composition: ConsoleView creates and owns its InputReader and validators.
    Encapsulation: implementation details are held in underscore-prefixed fields.
    """

    RESULT_WIDTH = 78
    HEAVY_LINE = "=" * 70
    LIGHT_LINE = "-" * 70

    RATING_FOOTER = (
        "About the ratings: Every rating shown is the customer review rating "
        "(the average of guest reviews, as reported by the AI). It is not the "
        "hotel's number of stars. Scores come from fixed rules applied to the hotel "
        "data shown above."
    )

    NOTE_TEXT = {
        "rating_missing": "No customer review rating was available.",
        "rating_may_be_stars": (
            "The rating is a whole number, so it may be a hotel's number of stars "
            "rather than an average of guest reviews. Please verify."
        ),
        "amenities_missing": "No amenities were listed.",
        "distance_unknown": "Distance to a requested place is unknown.",
    }


    # Traveller profile selector: menu number, profile name, label shown.
    # The names are what the Logic Manager receives.
    PROFILE_OPTIONS = (
        ("1", "balanced", "Balanced"),
        ("2", "budget", "Budget focused"),
        ("3", "quality_focused", "Quality Focused"),
        ("4", "custom", "Customisation"),
    )
    PROFILE_TOTAL_POINTS = 100
    WEIGHT_CRITERIA = (
        ("rating", "customer review rating"),
        ("price", "price"),
        ("location", "location"),
        ("amenities", "preferences"),
        ("bonus", "bonus"),
    )
 

    def __init__(
        self,
        input_function: Callable[[str], str] = input,
        output_function: Callable[[Any], None] = print,
    ):
        self._reader = InputReader(input_function)
        self._output = output_function

        # Validators are composed into this view and used polymorphically.
        self._location_validator: InputValidator = LocationValidator()
        self._price_validator: InputValidator = PriceRangeValidator()
        self._email_validator: InputValidator = EmailValidator()

    def _write(self, message: Any) -> None:
        self._output(message)

    def _wrap(self, value: str, indent: str = "") -> str:
        return textwrap.fill(
            str(value),
            width=self.RESULT_WIDTH,
            initial_indent=indent,
            subsequent_indent=indent,
        )

    @staticmethod
    def _money(value: Any) -> str:
        return "S$%g" % value

    @staticmethod
    def _join(items: list | None) -> str:
        return ", ".join(items) if items else "Not listed"

    @staticmethod
    def _activity_text(activity: Any) -> str:
        if isinstance(activity, dict):
            name = activity.get("name", "")
            distance = activity.get("distance_m")
            if isinstance(distance, (int, float)):
                return "%s (%s m)" % (name, "{:,}".format(int(distance)))
            return str(name)
        return str(activity)

    def request_mandatory_inputs(self) -> dict[str, Any]:
        """Collect destination, budget and email before hotel searching."""
        self._write("\n=== Hotel Search ===")

        while True:
            location = self._reader.read(
                "Enter your destination country or city: "
            )
            is_valid, error = self._location_validator.validate(location)
            if is_valid:
                break
            self._write(f"Error: {error}")

        while True:
            price_input = self._reader.read(
                "Enter your price range in SGD, for example 100-250: "
            )
            is_valid, error, price_range = self._price_validator.validate(price_input)
            if is_valid:
                break
            self._write(f"Error: {error}")

        while True:
            email = self._reader.read("Enter your email address: ")
            is_valid, error = self._email_validator.validate(email)
            if is_valid:
                break
            self._write(f"Error: {error}")

        return {
            "location": location,
            "price_range": price_range,
            "email_address": email,
        }

    def request_user_preferences(self) -> str:
        """Capture optional preferences for the AI Manager."""
        self._write(
            "\nDescribe your hotel preferences. "
            "For example: near public transport, breakfast included, "
            "quiet room and swimming pool."
        )
        while True:
            preferences = self._reader.read("\nYour preferences: ")
            if not preferences:
                return ""
            if len(preferences) > 2_000:
                self._write(
                    "Error: Preferences must not exceed 2,000 characters."
                )
                continue
            return preferences



    def request_traveller_profile(self, allowed_keys=None) -> dict[str, Any]:
        """Let the traveller choose how hotels are scored.
 
        Returns {"name": ..., "label": ..., "weights": ...}. Options 1 to 3
        return weights=None (the Logic Manager knows those profiles by name).
        Option 4 returns the five weightages, which add up to exactly 100.
        """
        self._write("\n=== Traveller Priorities ===")
        self._write(
            "Choose how hotels are scored. Every option adds up to 100 points.\n"
        )
        for number, _name, label in self.PROFILE_OPTIONS:
            self._write(f"{number}: {label}")
        self._write(
            "(Customise the scoring weightages for customer review rating, " 
            "price, location, preferences, and bonus points.\n" 
            "The total must add up to exactly /100.)"
        )
 
        choices = {number: (name, label) for number, name, label in self.PROFILE_OPTIONS}
        while True:
            choice = self._reader.read("\nChoose 1-4 (press Enter for Balanced): ")
            if choice == "":
                choice = "1"
            if choice in choices:
                break
            self._write("Error: Please enter a number from 1 to 4.")
 
        name, label = choices[choice]
        weights = (
            self._request_custom_weights(allowed_keys)
            if name == "custom"
            else None
        )
        self._write(f"Selected profile: {label}")
        return {"name": name, "label": label, "weights": weights}
 
    def _show_weights(self, weights: dict[str, int], total: int | None = None) -> None:
        for key, label in self.WEIGHT_CRITERIA:
            self._write(f"{label}: /{weights[key]}")
        shown_total = "" if total is None else total
        self._write(f"\nTotal: {shown_total}/{self.PROFILE_TOTAL_POINTS}")
 
    
    def _request_custom_weights(self, allowed_keys=None) -> dict[str, int]:
        """Collect custom scoring weightages that total exactly 100."""

        limit = self.PROFILE_TOTAL_POINTS

        # All five scoring criteria
        all_keys = {
            key for key, label in self.WEIGHT_CRITERIA
        }

        if allowed_keys is None:
            allowed_keys = all_keys
        else:
            allowed_keys = set(allowed_keys)

            # Logic Manager uses "preferences",
            # but IO Manager uses "amenities"
            if "preferences" in allowed_keys:
                allowed_keys.add("amenities")

        # Only ask users to allocate points to applicable criteria
        active_criteria = [
            (key, label)
            for key, label in self.WEIGHT_CRITERIA
            if key in allowed_keys
        ]

        # Identify categories that will be skipped
        skipped = [
            label
            for key, label in self.WEIGHT_CRITERIA
            if key not in allowed_keys
        ]

        self._write(
            "\nOption 4: Customisation "
            "(Customise the scoring weightages)"
        )

        self._show_weights({
            key: 0 for key, label in self.WEIGHT_CRITERIA
        })

        if skipped:
            self._write(
                "\nNot applicable (automatically 0 points): "
                + ", ".join(skipped)
            )

        self._write(
            f"\nAssign the points for each applicable criterion. "
            f"They must add up to exactly {limit}."
        )

        previous: dict[str, int] = {}

        while True:

            # Always initialise all five categories to 0
            weights: dict[str, int] = {
                key: 0 for key, label in self.WEIGHT_CRITERIA
            }

            running = 0

            # Prompt only for available categories
            for position, (key, label) in enumerate(active_criteria):

                remaining = limit - running
                hint = f"0-{remaining}"

                if position == len(active_criteria) - 1:
                    hint += f"; {remaining} makes {limit}"

                if key in previous:
                    hint += f"; Enter keeps {previous[key]}"

                validator = WeightValidator(remaining)

                while True:
                    answer = self._reader.read(
                        f"  {label} ({hint}): "
                    )

                    if answer == "" and key in previous:
                        answer = str(previous[key])

                    is_valid, error, points = validator.validate(answer)

                    if is_valid:
                        break

                    self._write(f"Error: {error}")

                weights[key] = points
                running += points

                self._write(
                    f"    Running total: {running}/{limit} "
                    f"({limit - running} left)"
                )

            if running == limit:
                self._write("\nYour scoring weightages:")
                self._show_weights(weights, running)
                return weights

            self._write(
                f"\nAlert: your weightages add up to {running}, "
                f"not {limit}. "
                f"{limit - running} point(s) are still unassigned. "
                "Please assign them again."
            )

            previous = weights



    def show_main_menu(self) -> str:
        """Display the main menu and return a valid option."""
        while True:
            self._write("\nWelcome to Team8's hotel recommendation app!\n")
            self._write("\n----------------------------------------------")
            self._write("1: Find a suitable hotel for your overseas travel needs!")
            self._write("2: View your previous hotel records")
            self._write("3: Admin login (NOT FOR USERS)")
            self._write("4: Quit")

            choice = self._reader.read("Please enter option 1, 2, 3 or 4: ")
            if choice in ("1", "2", "3", "4"):
                return choice
            self._write("Invalid option. Please enter 1, 2, 3 or 4")

    def request_record_email(self) -> str | None:
        """Ask for the email associated with saved hotel records."""
        while True:
            email = self._reader.read("Enter your email or q to quit: ")
            if email.lower() == "q":
                self._write("Exiting view hotel records")
                return None

            is_valid, error = self._email_validator.validate(email)
            if is_valid:
                return email.lower()
            self._write(f"Invalid input : {error}")

    def request_record_view_option(self) -> str:
        """Ask how to view saved records: by country or all of them."""
        while True:
            self._write("\n1: View your hotel records based on country")
            self._write("2: View all your hotel records")

            choice = self._reader.read("Please enter option 1 or 2: ")
            if choice in ("1", "2"):
                return choice
            self._write("Invalid option. Please enter 1 or 2")

    def request_record_country(self) -> str | None:
        """Ask for a full or partial country, e.g. "singa" for Singapore."""
        while True:
            country = self._reader.read(
                "Enter a country (e.g. singa for Singapore) or q to quit: "
            )
            if country.lower() == "q":
                self._write("Exiting view hotel records")
                return None

            is_valid, error = self._country_validator.validate(country)
            if is_valid:
                return " ".join(country.split())
            self._write(f"Invalid input : {error}")
            

    def display_message(self, message: str) -> None:
        self._write(message)

    def display_hotels(self, hotels: list[dict]) -> None:
        """Display hotel records in the existing compact format."""
        for number, hotel in enumerate(hotels, start=1):
            self._write(f"\n  {number}. {hotel['name']}")
            self._write(f"     {hotel['city']}, {hotel['country']}")
            self._write(
                f"     SGD {hotel['price_per_night_sgd']} per night | "
                f"Rating: {hotel['rating']}"
            )
            self._write(f"     Amenities: {', '.join(hotel['amenities'])}")
            self._write(f"     Nearby food options: {', '.join(hotel['nearby_food'])}")
            activities = [
                self._activity_text(item)
                for item in hotel.get("nearby_activities", [])
            ]
            self._write(f"     Nearby activities: {', '.join(activities)}")

    def display_records(self, records: list[dict]) -> None:
        """Display records shaped like email/searches."""
        if not records:
            self._write("\nNo records found.")
            return

        for record in records:
            self._write(f"\nEmail: {record['email']}")
            for number, hotels in enumerate(record["searches"], start=1):
                self._write(f"\n  --- Search {number} ---")
                self.display_hotels(hotels)

    def _show_hotel(self, hotel: dict) -> None:
        rating = hotel.get("rating")
        rating_text = (
            "%.1f / 5" % rating
            if isinstance(rating, (int, float))
            else "Not available"
        )

        self._write("")
        self._write("#%d  %s" % (hotel["rank"], hotel["name"]))
        self._write("    SCORE: %d/%d - %s" % (
            hotel["score"], hotel["score_max"], hotel["verdict"]
        ))
        self._write("    Price: %s per night" % self._money(
            hotel["price_per_night_sgd"]
        ))
        self._write(
            "    Customer review rating: %s (average of guest reviews, "
            "not hotel stars)" % rating_text
        )

        for item in hotel.get("distance_to_preferences") or []:
            distance = item.get("distance_m")
            if isinstance(distance, (int, float)):
                self._write("    Distance: %s m from %s" % (
                    "{:,}".format(int(distance)), item.get("target")
                ))

        self._write(self._wrap("Amenities: " + self._join(hotel.get("amenities")), "    "))
        self._write(self._wrap("Nearby food: " + self._join(hotel.get("nearby_food")), "    "))
        activities = [
            self._activity_text(item)
            for item in hotel.get("nearby_activities") or []
        ]
        self._write(self._wrap("Nearby activities: " + self._join(activities), "    "))

        self._write("")
        self._write("    Why %d/%d:" % (hotel["score"], hotel["score_max"]))
        for line in hotel["breakdown"]:
            self._write("      %-24s %2d / %2d" % (
                line["category"], line["points"], line["max"]
            ))
            self._write(self._wrap(line["reason"], "        "))
        self._write("      %-24s %2d / %2d" % (
            "TOTAL", hotel["score"], hotel["score_max"]
        ))

        if hotel.get("flags"):
            self._write("")
            for flag in hotel["flags"]:
                self._write(self._wrap(
                    "Note: " + self.NOTE_TEXT.get(flag, flag), "    "
                ))
        self._write(self.LIGHT_LINE)

    def display_recommendations(self, result: dict, record: dict) -> None:
        """Display the Logic Manager's ranked hotels and scoring details."""
        summary = result["summary"]
        requirements = result["requirements"]

        self._write("")
        self._write(self.HEAVY_LINE)
        self._write("TOP HOTEL RECOMMENDATIONS")
        self._write(self.HEAVY_LINE)
        self._write("Destination : %s" % record.get("destination"))
        self._write("Budget      : %s - %s per night" % (
            self._money(record.get("budget_min")),
            self._money(record.get("budget_max")),
        ))
        self._write("Preferences : %s" % (record.get("preferences") or "None"))
        if requirements["targets"]:
            self._write("Near        : %s" % ", ".join(requirements["targets"]))
        self._write("Reviewed    : %d hotels | Shown: %d | Rejected: %d" % (
            summary["received"], summary["returned"], summary["rejected"]
        ))
        self._write(self.HEAVY_LINE)

        if requirements["unverified"]:
            self._write(self._wrap(
                "Could not be checked against hotel data (so not scored): "
                + ", ".join(requirements["unverified"]) + "."
            ))
        for note in requirements["not_scored"]:
            self._write(self._wrap(note))

        if not result["top_hotels"]:
            self._write("")
            self._write("No hotels matched your requirements.")
        for hotel in result["top_hotels"]:
            self._show_hotel(hotel)

        if result["rejected_hotels"]:
            self._write("")
            self._write("REJECTED")
            for hotel in result["rejected_hotels"]:
                self._write(self._wrap(
                    "x %s: %s" % (hotel["name"], hotel["reject_reason"]), "  "
                ))
            self._write(self.LIGHT_LINE)

        self._write("")
        self._write(self._wrap(self.RATING_FOOTER))
        self._write("")

    def display_ai_dictionary(self, ai_dictionary: dict) -> None:
        self._write(ai_dictionary)

    def display_top_three_dictionary(self, top_three_dict: dict) -> None:
        self._write("\n=== TOP 3 HOTELS (DICTIONARY OUTPUT) ===")
        self._write(top_three_dict)
        self._write("=== END OF TOP 3 HOTELS (DICTIONARY OUTPUT) ===\n")

    def admin_login(self, admin_user: str, admin_password: str) -> bool:
        """Return True on successful login, False when the user chooses Q."""
        while True:
            username = self._reader.read("Enter username or Q to exit: ")
            if username.upper() == "Q":
                return False
            if username != admin_user:
                self._write("Wrong username")
                continue

            while True:
                password = self._reader.read("Enter password or Q to exit: ")
                if password.upper() == "Q":
                    return False
                if password != admin_password:
                    self._write("Wrong password")
                    continue
                return True
