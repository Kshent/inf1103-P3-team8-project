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


print("Loading I/O Manager...")

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














def show_main_menu(
    input_function: Callable[[str], str] = input,
    output_function: Callable[[str], None] = print
) -> str:
    """Show the main menu and return a valid choice: "1", "2", "3"""

    while True:
        output_function("Welcome to Team8's hotel recommendation app!\n")
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




# def build_ai_request(
#     mandatory_inputs: dict[str, Any],
#     preferences: str
# ) -> dict[str, Any]:
#     """
#     I/O Manager Step 3.

#     Transform traveller inputs into a standard request
#     format expected by the AI Manager.
#     """

#     return {
#         "task": "Find suitable hotels for the traveller.",
#         "destination": mandatory_inputs["location"],
#         "price_range": mandatory_inputs["price_range"],
#         "preferences": preferences,
#         "required_response_format": {
#             "hotels": [
#                 {
#                     "name": "Hotel name",
#                     "location": "Hotel location",
#                     "price_per_night_sgd": 0,
#                     "rating": 0,
#                     "description": "Short description",
#                     "amenities": [],
#                     "booking_url": "https://example.com"
#                 }
#             ]
#         }
#     }


# def display_top_hotels(
#     hotels: list[dict[str, Any]],
#     output_function: Callable[[str], None] = print
# ) -> None:
#     """
#     Present final recommendations to the traveller.

#     This function is responsible only for output formatting
#     and does not perform any business logic.
#     """

#     if not hotels:
#         output_function(
#             "\nNo matching hotels were found for your search."
#         )
#         return

#     output_function("\n=== Top Hotel Recommendations ===")

#     # Display each hotel in a numbered format.
#     for index, hotel in enumerate(hotels, start=1):

#         output_function(
#             f"\n{index}. {hotel.get('name', 'Unnamed hotel')}"
#         )

#         output_function(
#             f"   Location: {hotel.get('location', 'Not provided')}"
#         )

#         output_function(
#             "   Price per night: "
#             f"SGD {hotel.get('price_per_night_sgd', 'Not provided')}"
#         )

#         output_function(
#             f"   Rating: {hotel.get('rating', 'Not provided')}"
#         )

#         output_function(
#             f"   Description: "
#             f"{hotel.get('description', 'Not provided')}"
#         )

#         # Display amenities only when available.
#         amenities = hotel.get("amenities", [])

#         if amenities:
#             output_function(
#                 f"   Amenities: {', '.join(map(str, amenities))}"
#             )

#         # Display booking link when provided by AI.
#         if hotel.get("booking_url"):
#             output_function(
#                 f"   Booking URL: {hotel['booking_url']}"
#             )


# def run_hotel_search(
#     ai_manager: Any,
#     data_manager: Any,
#     logic_manager: Any,
#     email_manager: Any,
#     output_file_path: str = "hotel_recommendations.json",
#     input_function: Callable[[str], str] = input,
#     output_function: Callable[[str], None] = print
# ) -> bool:
#     """
#     Main I/O Manager orchestrator.

#     Coordinates communication between:
#     - User
#     - AI Manager
#     - Logic Manager
#     - Data Manager
#     - Email Manager
#     """

#     try:

#         # Step 1: Collect mandatory traveller details.
#         mandatory_inputs = request_mandatory_inputs(
#             input_function=input_function,
#             output_function=output_function
#         )

#         # Step 2: Collect optional preference details.
#         preferences = request_user_preferences(
#             input_function=input_function,
#             output_function=output_function
#         )

#         # Build standard AI request payload.
#         ai_request = build_ai_request(
#             mandatory_inputs=mandatory_inputs,
#             preferences=preferences
#         )

#         output_function("\nSearching for suitable hotels...")

#         # Step 3: Request hotel recommendations from AI Manager.
#         ai_response = ai_manager.generate_hotel_recommendations(
#             ai_request
#         )

#         # Ensure AI Manager returned expected structure.
#         if not isinstance(ai_response, dict):
#             raise ValueError(
#                 "The AI Manager returned an invalid response."
#             )

#         hotels = ai_response.get("hotels")

#         if not isinstance(hotels, list) or not all(
#             isinstance(hotel, dict) for hotel in hotels
#         ):
#             raise ValueError(
#                 "The AI response does not contain a valid list of hotels."
#             )

#         # Step 4: Persist raw AI output for auditing and traceability.
#         data_manager.save_ai_results(
#             ai_response,
#             output_file_path
#         )

#         # Step 5: Logic Manager selects best hotel recommendations.
#         top_hotels = logic_manager.filter_top_hotels(
#             hotels,
#             limit=3
#         )

#         if not isinstance(top_hotels, list) or not all(
#             isinstance(hotel, dict) for hotel in top_hotels
#         ):
#             raise ValueError(
#                 "The Logic Manager returned an invalid hotel list."
#             )

#         # Display shortlisted hotels in CLI.
#         display_top_hotels(
#             top_hotels,
#             output_function=output_function
#         )

#         # Step 6: Deliver results to traveller's email.
#         output_function(
#             f"\nSending recommendations to "
#             f"{mandatory_inputs['email_address']}..."
#         )

#         email_manager.send_hotel_recommendations(
#             recipient_email=mandatory_inputs["email_address"],
#             hotels=top_hotels
#         )

#         output_function(
#             "\nSuccess: Hotel recommendations have been emailed."
#         )
#         return True

#     except EOFError as error:
#         # User intentionally stopped the workflow.
#         output_function(str(error))
#         return False

#     except TimeoutError:
#         # External dependency failed to respond in time.
#         output_function(
#             "\nError: The hotel search request timed out. "
#             "Please try again later."
#         )
#         return False

#     except ConnectionError:
#         # Unable to reach one of the application managers/services.
#         output_function(
#             "\nError: Unable to connect to one of the application services."
#         )
#         return False

#     except ValueError as error:
#         # Validation or data structure errors have safe, local messages.
#         output_function(
#             f"\nError: {error}"
#         )
#         return False

#     except Exception as error:
#         # Prevent internal implementation details from leaking
#         # to end users while still providing basic diagnostics.
#         output_function(
#             "\nUnexpected error: The hotel search could not be completed."
#         )
#         output_function(
#             f"Technical details: {type(error).__name__}"
#         )
#         return False