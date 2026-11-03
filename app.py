import uuid

import data_manager as DataManager
import IO_manager as IOManager

from ai_manager.ai_factory import AIManagerFactory
from logic_manager import LogicManager


ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


# One AIManager object, reused for every search
ai_manager = AIManagerFactory.create_hotel_manager()

# One LogicManager object, reused for every search
logic_manager = LogicManager()


def main():

    while True:

        try:
            menu_display = IOManager.show_main_menu()

            if menu_display == "1":

                user_input_details = {}

                mandatory_data = IOManager.request_mandatory_inputs()
                user_prefs = IOManager.request_user_preferences()

                final_search_payload = {
                    **mandatory_data,
                    "preferences": user_prefs
                }

                user_input_details["destination"] = (
                    final_search_payload["location"]
                )

                user_input_details["budget_min"] = (
                    final_search_payload["price_range"]["min"]
                )

                user_input_details["budget_max"] = (
                    final_search_payload["price_range"]["max"]
                )

                user_input_details["email_address"] = (
                    final_search_payload["email_address"]
                )

                user_input_details["preferences"] = (
                    final_search_payload["preferences"]
                )

                # AI MANAGER:
                # Build prompt, call Gemini, parse and validate response.
                # If the first AI response is invalid, one correction
                # attempt is performed automatically.
                ai_manager_result = ai_manager.generate_candidates(
                    user_input_details
                )

                # Prevent crash if AI Manager/API fails
                if ai_manager_result is None:
                    IOManager.display_message(
                        "Hotel recommendation service is currently "
                        "unavailable. Please try again later."
                    )
                    continue

                email = user_input_details["email_address"]

                # STEP 1: Keep the original AI output for Logic Manager
                original_ai_output = ai_manager_result

                # STEP 2: Create a separate copy for displaying AI output
                display_ai_output = ai_manager_result.copy()

                display_ai_output[str(uuid.uuid4())] = (
                    display_ai_output.pop("hotels")
                )

                # Display AI output as dictionary
                IOManager.display_ai_dictionary(
                    display_ai_output
                )

                # STEP 3: Process hotels using Logic Manager
                # Must receive the ORIGINAL output because it still
                # contains the "hotels" key.
                logic_result = logic_manager.process_hotels(
                    original_ai_output,
                    user_input_details
                )

                # STEP 4: Display neatly formatted Top 3 hotels
                IOManager.display_recommendations(
                    logic_result,
                    user_input_details
                )

                # STEP 5: Display Top 3 using original AI data

                # Match ranked hotels to original AI hotel dictionaries
                original_hotels_by_name = {
                    hotel["name"]: hotel
                    for hotel in original_ai_output["hotels"]
                }

                # Keep only the Top 3 in ranked order
                top_three_dict = {
                    "top_hotels": [
                        original_hotels_by_name[hotel["name"]]
                        for hotel in logic_result["top_hotels"]
                    ]
                }

                IOManager.display_top_three_dictionary(
                    top_three_dict
                )

                # DATA MANAGER:
                # Save Top 3 in the same format as displayed
                if top_three_dict["top_hotels"]:

                    DataManager.save({
                        email: top_three_dict["top_hotels"]
                    })

                    IOManager.display_message(
                        "Hotel recommendations saved successfully."
                    )

                else:

                    IOManager.display_message(
                        "No hotels matched your requirements, "
                        "nothing was saved."
                    )

            elif menu_display == "2":

                record_email = IOManager.request_record_email()

                IOManager.display_records(
                    DataManager.query(record_email)
                )

            elif menu_display == "3":

                if IOManager.admin_login(
                    ADMIN_USER,
                    ADMIN_PASSWORD
                ):

                    IOManager.display_records(
                        DataManager.load()
                    )

            elif menu_display == "4":

                IOManager.display_message(
                    "Thanks for using our app!"
                )
                break

        except EOFError as error:

            IOManager.display_message(
                str(error)
            )

            continue


if __name__ == "__main__":
    main()