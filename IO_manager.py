"""
I/O Manager
 
Responsibilities:
1. Collect traveller input from the CLI.
2. Validate user-provided information.
3. Format data for the AI Manager.
4. Display hotel recommendations.
5. Coordinate communication between all managers.
 
This layer must not contain:
- Hotel ranking logic
- AI recommendation logic
- Database/file storage logic
 
Those responsibilities belong to the Logic Manager,
AI Manager and Data Manager respectively.
"""

from geonamescache import GeonamesCache

import re
import textwrap
from typing import Any, Callable


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

    # Validate against known country/city names using geonamescache.
    try:
        geonames = GeonamesCache()
        normalized = " ".join(location.split()).lower()

        countries = geonames.get_countries()
        for country_code, country_data in countries.items():
            country_name = str(country_data.get("name", "")).lower()
            if normalized == country_name or normalized == country_code.lower():
                return True, ""

        cities = geonames.get_cities()
        for city_data in cities.values():
            city_name = str(city_data.get("name", "")).lower()
            if normalized == city_name:
                return True, ""

        return False, (
            "Location not found. Please enter a valid country or city name."
        )

    except Exception:
        # Fallback if geonamescache is unavailable.
        return True, ""

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

    if not isinstance(price_range, str) or not price_range.strip():
        return False, "Price range cannot be empty.", None

    # Normalise common SGD formats
    cleaned_value = price_range.upper()

    cleaned_value = cleaned_value.replace("SGD", "")
    cleaned_value = cleaned_value.replace("S$", "")
    cleaned_value = cleaned_value.replace("$", "")

    # Remove spaces
    cleaned_value = re.sub(r"\s+", "", cleaned_value)

    # Accept:
    # 100-250
    # 100,250
    # 100to250
    match = re.fullmatch(
        r"(\d+(?:\.\d+)?)(?:-|,|TO)(\d+(?:\.\d+)?)",
        cleaned_value
    )

    if not match:
        return (
            False,
            "Enter a valid SGD price range, for example 100-250 or SGD 100-SGD 250.",
            None
        )

    minimum_price = float(match.group(1))
    maximum_price = float(match.group(2))

    if minimum_price <= 0 or maximum_price <= 0:
        return False, "Prices must be greater than zero.", None

    if minimum_price > maximum_price:
        return (
            False,
            "The minimum price cannot be higher than the maximum price.",
            None
        )

    if maximum_price > 1_000_000:
        return False, "The maximum price is too high.", None

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














def show_main_menu(
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print
) -> str:
    """Show the main menu and return a valid choice: "1", "2", "3"""

    while True:
        output_function("\nWelcome to Team8's hotel recommendation app!\n")
        output_function("\n----------------------------------------------")
        output_function("1: Find a suitable hotel for your overseas travel needs!")
        output_function("2: View your previous hotel records")
        output_function("3: Admin login (NOT FOR USERS)")
        output_function("4: Quit")

        choice = _safe_input(
            "Please enter option 1, 2, 3 or 4: ",
            input_function
        )

        if choice in ("1", "2", "3","4"):
            return choice

        output_function("Invalid option. Please enter 1, 2, 3 or 4")



def request_record_email(input_function=input, output_function = print):
    """Option 2: ask for the user email."""
    while True:
        email = _safe_input("Enter your email or q to quit: ", input_function)

        if email.lower() == "q":
            output_function("Exiting view hotel records")
            break

        cleaned_email = email.strip()

        is_valid, error_message = validate_email(cleaned_email)

        if is_valid:
            return cleaned_email.lower()

        output_function(f"Invalid input : {error_message}")


def display_message(message, output_function=print):
    output_function(message)


#updated to allow new ai json strucuture to be displayed in IO manager
def display_hotels(hotels, output_function=print):
    for number, hotel in enumerate(hotels, start=1):
        output_function(f"\n  {number}. {hotel['name']}")
        output_function(f"     {hotel['city']}, {hotel['country']}")
        output_function(
            f"     SGD {hotel['price_per_night_sgd']} per night | "
            f"Rating: {hotel['rating']}")
        output_function(
            f"     Amenities: {', '.join(hotel['amenities'])}")
        output_function(
            f"     Nearby food options: {', '.join(hotel['nearby_food'])}")
        activities = hotel.get("nearby_activities", [])
        formatted_activities = []
        for activity in activities:
            if isinstance(activity, dict):
                name = activity.get("name", "Unknown")
                distance = activity.get("distance_m")
                if distance is not None:
                    formatted_activities.append(
                        f"{name} ({distance}m)"
                    )
                else:
                    formatted_activities.append(name)
            else:
                # Supports older saved records
                formatted_activities.append(str(activity))
        output_function(
            f"     Nearby activities: {', '.join(formatted_activities)}"
        )
        #need to output logic manager distance to preferences too later on


def display_records(records, output_function=print):
    """Print records shaped like [{"email": email, "searches": [[hotels], ...]}]."""
    if not records:
        output_function("\nNo records found.")
        return

    for record in records:
        output_function(f"\nEmail: {record['email']}")

        for number, hotels in enumerate(record["searches"], start=1):
            output_function(f"\n  --- Search {number} ---")
            display_hotels(hotels, output_function)


# ---------------------------------------------------------------------
# Logic Manager results display
# (moved here from result_display.py so all printing lives in this file)
# ---------------------------------------------------------------------
RESULT_WIDTH = 78
HEAVY_LINE = "=" * 70
LIGHT_LINE = "-" * 70

RATING_FOOTER = (
    "About the ratings: every rating shown is the customer review rating "
    "(the average of guest reviews, as reported by the AI). It is not the "
    "hotel's number of stars. Scores come from fixed rules applied to the hotel "
    "data shown above."
)

NOTE_TEXT = {
    "rating_missing": "No customer review rating was available.",
    "rating_may_be_stars": (
        "The rating is a whole number, so it may be a hotel's number of stars "
        "rather than an average of guest reviews. Please verify."),
    "amenities_missing": "No amenities were listed.",
    "distance_unknown": "Distance to a requested place is unknown.",
}


def _wrap(text, indent):
    return textwrap.fill(text, width=RESULT_WIDTH, initial_indent=indent,
                         subsequent_indent=indent)


def _money(value):
    return "S$%g" % value


def _join(items):
    return ", ".join(items) if items else "Not listed"


def _activity_text(activity):
    if isinstance(activity, dict):
        name = activity.get("name", "")
        distance = activity.get("distance_m")
        if isinstance(distance, (int, float)):
            return "%s (%s m)" % (name, "{:,}".format(int(distance)))
        return str(name)
    return str(activity)


def _show_hotel(hotel, output_function=print):
    rating = hotel.get("rating")
    rating_text = "%.1f / 5" % rating if isinstance(rating, (int, float)) \
        else "Not available"

    output_function("")
    output_function("#%d  %s" % (hotel["rank"], hotel["name"]))
    output_function("    SCORE: %d/%d - %s" % (
        hotel["score"], hotel["score_max"], hotel["verdict"]))
    output_function("    Price: %s per night" % _money(hotel["price_per_night_sgd"]))
    output_function("    Customer review rating: %s (average of guest reviews, "
                    "not hotel stars)" % rating_text)
    for item in hotel.get("distance_to_preferences") or []:
        distance = item.get("distance_m")
        if isinstance(distance, (int, float)):
            output_function("    Distance: %s m from %s" % (
                "{:,}".format(int(distance)), item.get("target")))
    output_function(_wrap("Amenities: " + _join(hotel.get("amenities")), "    "))
    output_function(_wrap("Nearby food: " + _join(hotel.get("nearby_food")), "    "))
    output_function(_wrap("Nearby activities: " + _join(
        [_activity_text(a) for a in hotel.get("nearby_activities") or []]),
        "    "))

    output_function("")
    output_function("    Why %d/%d:" % (hotel["score"], hotel["score_max"]))
    for line in hotel["breakdown"]:
        output_function("      %-24s %2d / %2d" % (
            line["category"], line["points"], line["max"]))
        output_function(_wrap(line["reason"], "        "))
    output_function("      %-24s %2d / %2d" % ("TOTAL", hotel["score"],
                                               hotel["score_max"]))

    if hotel.get("flags"):
        output_function("")
        for flag in hotel["flags"]:
            output_function(_wrap("Note: " + NOTE_TEXT.get(flag, flag), "    "))
    output_function(LIGHT_LINE)


def display_recommendations(result, record, output_function=print):
    """Show the Logic Manager's top hotels with score and breakdown."""
    summary = result["summary"]
    requirements = result["requirements"]

    output_function("")
    output_function(HEAVY_LINE)
    output_function("TOP HOTEL RECOMMENDATIONS")
    output_function(HEAVY_LINE)
    output_function("Destination : %s" % record.get("destination"))
    output_function("Budget      : %s - %s per night" % (
        _money(record.get("budget_min")), _money(record.get("budget_max"))))
    output_function("Preferences : %s" % (record.get("preferences") or "None"))
    if requirements["targets"]:
        output_function("Near        : %s" % ", ".join(requirements["targets"]))
    output_function("Reviewed    : %d hotels | Shown: %d | Rejected: %d" % (
        summary["received"], summary["returned"], summary["rejected"]))
    output_function(HEAVY_LINE)

    if requirements["unverified"]:
        output_function(_wrap("Could not be checked against hotel data (so not "
                              "scored): " + ", ".join(requirements["unverified"]) + ".",
                              ""))
    for note in requirements["not_scored"]:
        output_function(_wrap(note, ""))

    if not result["top_hotels"]:
        output_function("")
        output_function("No hotels matched your requirements.")
    for hotel in result["top_hotels"]:
        _show_hotel(hotel, output_function)

    if result["rejected_hotels"]:
        output_function("")
        output_function("REJECTED")
        for hotel in result["rejected_hotels"]:
            output_function(_wrap("x %s: %s" % (hotel["name"], hotel["reject_reason"]),
                                  "  "))
        output_function(LIGHT_LINE)

    output_function("")
    output_function(_wrap(RATING_FOOTER, ""))
    output_function("")


def display_ai_dictionary(ai_dictionary, output_function=print):
    """Show the AI Manager's output as a plain dictionary."""
    output_function(ai_dictionary)


def display_top_three_dictionary(top_three_dict, output_function=print):
    """Show the chosen top hotels as a plain dictionary."""
    output_function("\n=== TOP 3 HOTELS (DICTIONARY OUTPUT) ===")
    output_function(top_three_dict)
    output_function("=== END OF TOP 3 HOTELS (DICTIONARY OUTPUT) ===\n")


def admin_login(admin_user, admin_password, input_function=input, output_function=print):
    """Option 3: returns True if login succeeds, False if the user quits with Q."""
    while True:
        username = _safe_input("Enter username or Q to exit: ", input_function)

        if username.upper() == "Q":
            return False
        if username != admin_user:
            output_function("Wrong username")
            continue

        while True:
            password = _safe_input("Enter password or Q to exit: ", input_function)

            if password.upper() == "Q":
                return False
            if password != admin_password:
                output_function("Wrong password")
                continue

            return True