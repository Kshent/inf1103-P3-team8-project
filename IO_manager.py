
import re
from typing import Any, Callable


class InputCancelledError(Exception):
    """Raised when the user exits the application."""


def _safe_input(
    prompt: str,
    input_function: Callable[[str], str] = input
) -> str:
    """
    Read user input and handle common CLI errors.
    """
    try:
        value = input_function(prompt)
    except (KeyboardInterrupt, EOFError):
        raise InputCancelledError(
            "\nInput cancelled. Goodbye."
        )

    if value is None:
        raise InputCancelledError("\nInput cancelled. Goodbye.")

    return value.strip()


def validate_location(location: str) -> tuple[bool, str]:
    """
    Validate a country or city name.

    Allows letters, spaces, apostrophes, hyphens and periods.
    """
    if not location:
        return False, "Location cannot be empty."

    if len(location) < 2:
        return False, "Location must contain at least 2 characters."

    if len(location) > 100:
        return False, "Location must not exceed 100 characters."

    valid_location = re.fullmatch(
        r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9 .,'-]*",
        location
    )

    if not valid_location:
        return False, (
            "Location contains invalid characters. "
            "Please enter a valid country or city."
        )

    return True, ""


def validate_price_range(price_range: str) -> tuple[bool, str, int | None]:
    """
    Validate a price range in Singapore dollars.

    Accepted examples:
        100-250
        100 - 250
        100,250

    Returns:
        (is_valid, error_message, price_range_value)
    """
    if not price_range:
        return False, "Price range cannot be empty.", None

    cleaned_value = price_range.replace(" ", "")

    match = re.fullmatch(r"(\d+(?:\.\d+)?)[-,](\d+(?:\.\d+)?)", cleaned_value)

    if not match:
        return (
            False,
            "Enter the price range in this format: 100-250.",
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
    Validate an email address using a practical CLI validation rule.
    """
    if not email_address:
        return False, "Email address cannot be empty."

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
    Step 1:
    Request and validate location, price range and email address.
    """
    output_function("\n=== Hotel Search ===")

    while True:
        location = _safe_input(
            "Enter your destination country or city: ",
            input_function
        )

        is_valid, error_message = validate_location(location)

        if is_valid:
            break

        output_function(f"Error: {error_message}")

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

    while True:
        email_address = _safe_input(
            "Enter your email address: ",
            input_function
        )

        is_valid, error_message = validate_email(email_address)

        if is_valid:
            break

        output_function(f"Error: {error_message}")

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
    Step 2:
    Request elaborative, free-form hotel preferences.
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

        if not preferences:
            output_function(
                "Error: Please enter at least one hotel preference."
            )
            continue

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
    Step 3:
    Combine Step 1 and Step 2 data into one AI request.
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
    Display the final hotel recommendations in the CLI.
    """
    if not hotels:
        output_function(
            "\nNo matching hotels were found for your search."
        )
        return

    output_function("\n=== Top Hotel Recommendations ===")

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

        amenities = hotel.get("amenities", [])
        if amenities:
            output_function(
                f"   Amenities: {', '.join(map(str, amenities))}"
            )

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
    Main I/O Manager workflow.

    Steps:
        1. Request mandatory inputs.
        2. Request user preferences.
        3. Send combined information to the AI Manager.
        4. Save AI output using the Data Manager.
        5. Filter the top three hotels using the Logic Manager.
        6. Email the recommendations using the Email Manager.

    Returns:
        True when the workflow succeeds.
        False when the workflow fails.
    """
    try:
        mandatory_inputs = request_mandatory_inputs(
            input_function=input_function,
            output_function=output_function
        )

        preferences = request_user_preferences(
            input_function=input_function,
            output_function=output_function
        )

        ai_request = build_ai_request(
            mandatory_inputs=mandatory_inputs,
            preferences=preferences
        )

        output_function("\nSearching for suitable hotels...")

        # Step 3: Call the AI Manager.
        ai_response = ai_manager.generate_hotel_recommendations(
            ai_request
        )

        if not isinstance(ai_response, dict):
            raise ValueError(
                "The AI Manager returned an invalid response."
            )

        hotels = ai_response.get("hotels", [])

        if not isinstance(hotels, list):
            raise ValueError(
                "The AI response does not contain a valid hotel list."
            )

        # Step 4: Store the raw AI response using the Data Manager.
        data_manager.save_ai_results(
            ai_response,
            output_file_path
        )

        # Step 5: Remove duplicates and find the best three hotels.
        top_hotels = logic_manager.filter_top_hotels(
            hotels,
            limit=3
        )

        display_top_hotels(
            top_hotels,
            output_function=output_function
        )

        # Step 6: Send the results to the requested email address.
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

    except InputCancelledError as error:
        output_function(str(error))
        return False

    except TimeoutError:
        output_function(
            "\nError: The request timed out. "
            "Please try again later."
        )
        return False

    except ConnectionError:
        output_function(
            "\nError: Unable to connect to one of the application services."
        )
        return False

    except ValueError as error:
        output_function(f"\nError: {error}")
        return False

    except Exception as error:
        # Do not expose sensitive implementation details to CLI users.
        output_function(
            "\nUnexpected error: The hotel search could not be completed."
        )
        output_function(
            f"Technical details: {type(error).__name__}"
        )
        return False