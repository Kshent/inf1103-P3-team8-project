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

        choice = _safe_input("Please enter option 1, 2 or 3: ", input_function)

        if choice in ("1", "2", "3"):
            return choice

        output_function("Invalid option. Please enter 1, 2 or 3")


#get uuid key in json
def request_record_id(input_function=input):
    """Option 2: ask for the record uuid."""
    return _safe_input("Enter your record ID: ", input_function)


def display_message(message, output_function=print):
    output_function(message)


def display_hotels(hotels, output_function=print):
    for number, hotel in enumerate(hotels, start=1):
        output_function(f"\n  {number}. {hotel['name']}")
        output_function(f"     {hotel['city']}, {hotel['country']}")
        output_function(f"     SGD {hotel['price_per_night_sgd']} per night | Rating: {hotel['rating']}")
        output_function(f"     Amenities: {', '.join(hotel['amenities'])}")


def display_records(records, output_function=print):
    """Print records shaped like [{"id": uuid, "hotels": [...]}]."""
    if not records:
        output_function("\nNo records found.")
        return

    for record in records:
        output_function(f"\nRecord ID: {record['id']}")
        display_hotels(record["hotels"], output_function)


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
