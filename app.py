import uuid
<<<<<<< HEAD

import data_manager as DataManager
import IO_manager as IOManager

from ai_manager.ai_factory import AIManagerFactory
from logic_manager import LogicManager

=======
import logging
from pathlib import Path
from dotenv import load_dotenv
import ai_manager as AIManager
from data_managerpart2.data_manager import DataManager, RECORDS_FILE
from data_managerpart2.json_storage import JsonStorage
from data_managerpart2.memory_storage import MemoryStorage
from data_managerpart2.send_email import EmailSender
import io_manager_part2.__init__ as IOManager
import logic_manager_part2.logic_manager as LogicManager
load_dotenv(Path(__file__).resolve().with_name(".env"))
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a

ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


<<<<<<< HEAD
# One AIManager object, reused for every search
ai_manager = AIManagerFactory.create_hotel_manager()

# One LogicManager object, reused for every search
logic_manager = LogicManager()
=======
# NO PRINTS AND INPUTS ALLOWED!
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a


def main():
    console = IOManager.ConsoleView()
    sender = EmailSender(os.environ.get("EMAIL_ADDRESS"), os.environ.get("EMAIL_APP_PASSWORD"))



    # DATA_STORAGE=memory runs without saving to disk (e.g. for a demo);
    # anything else uses the JSON records file.
    if os.environ.get("DATA_STORAGE", "json").lower() == "memory":
        storage = MemoryStorage()
    else:
        storage = JsonStorage(RECORDS_FILE)
    data_manager = DataManager(storage)

    while True:

        try:
            menu_display = console.show_main_menu()

            if menu_display == "1":

                user_input_details = {}

<<<<<<< HEAD
                mandatory_data = IOManager.request_mandatory_inputs()
                user_prefs = IOManager.request_user_preferences()
=======

                
                mandatory_data = console.request_mandatory_inputs()
                user_prefs = console.request_user_preferences()
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a

                # Create Logic Manager boss
                logic_manager = LogicManager.LogicManager()

                # Ask Logic which scoring categories are applicable
                allowed_keys = logic_manager.available_weight_keys(
                    user_prefs
                )

                # IO collects the traveller style and custom weights
                while True:

                    traveller_profile = console.request_traveller_profile(
                        allowed_keys=allowed_keys
                    )

                    try:
                        selected_profile = logic_manager.resolve_profile(
                            traveller_profile,
                            user_prefs
                        )
                        break

                    except ValueError as error:
                        console.display_message(
                            f"Invalid weightages: {error}"
                        )
                    
                final_search_payload = {
<<<<<<< HEAD
                    **mandatory_data,
                    "preferences": user_prefs
                }

                user_input_details["destination"] = (
                    final_search_payload["location"]
                )
=======
                        **mandatory_data,
                        "preferences": user_prefs,
                        "priority_profile": selected_profile
                }

                user_input_details["destination"] = final_search_payload["location"]
                user_input_details["budget_min"] = final_search_payload["price_range"]["min"]
                user_input_details["budget_max"] = final_search_payload["price_range"]["max"]
                user_input_details["email_address"] = final_search_payload["email_address"]
                user_input_details["preferences"] = final_search_payload["preferences"]
                user_input_details["priority_profile"] = final_search_payload["priority_profile"]
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a

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
<<<<<<< HEAD
                    IOManager.display_message(
                        "Hotel recommendation service is currently "
                        "unavailable. Please try again later."
=======
                    console.display_message(
                        "Hotel recommendation service is currently unavailable. Please try again later."
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
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

<<<<<<< HEAD
                # Display AI output as dictionary
                IOManager.display_ai_dictionary(
                    display_ai_output
                )

                # STEP 3: Process hotels using Logic Manager
                # Must receive the ORIGINAL output because it still
                # contains the "hotels" key.
=======
                #This will output as dictionary. Logic manager access this dictionary process your logic etc.
                console.display_ai_dictionary(ai_manager_result)

                # STEP 3: Process hotels using Logic Manager
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
                logic_result = logic_manager.process_hotels(
                    original_ai_output,
                    user_input_details
                )

                # STEP 4: Display neatly formatted Top 3 hotels
                console.display_recommendations(
                    logic_result,
                    user_input_details
                )

                # STEP 5: Display Top 3 using original AI data

                # Match ranked hotels to original AI hotel dictionaries
                original_hotels_by_name = {
                    hotel["name"]: hotel
                    for hotel in original_ai_output["hotels"]
                }

<<<<<<< HEAD
                # Keep only the Top 3 in ranked order
=======

                # Keep only the Top 3, in their ranked order
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
                top_three_dict = {
                    "top_hotels": [
                        original_hotels_by_name[hotel["name"]]
                        for hotel in logic_result["top_hotels"]
                    ]
                }

<<<<<<< HEAD
                IOManager.display_top_three_dictionary(
                    top_three_dict
                )
=======
                console.display_top_three_dictionary(top_three_dict)
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a

                # DATA MANAGER:
                # Save Top 3 in the same format as displayed
                if top_three_dict["top_hotels"]:

<<<<<<< HEAD
                    DataManager.save({
                        email: top_three_dict["top_hotels"]
                    })

                    IOManager.display_message(
=======
                    sender.send(
                        to_address=email,
                        subject="Your Hotel Recommendations for " + user_input_details["destination"],
                        body=f"Here are the top 3 hotels you might like!\n\n{top_three_dict['top_hotels']}"
                    )

                    data_manager.save({
                        email: top_three_dict["top_hotels"]
                    })
                    console.display_message(
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
                        "Hotel recommendations saved successfully."
                    )

                else:
<<<<<<< HEAD

                    IOManager.display_message(
                        "No hotels matched your requirements, "
                        "nothing was saved."
=======
                    console.display_message(
                        "No hotels matched your requirements, nothing was saved."
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
                    )

            elif menu_display == "2":

                record_email = console.request_record_email()

                records = data_manager.query(record_email)

                # Nothing saved for this email, so no need to ask how to view it
                if not records:
                    console.display_records(records)
                    continue

                if console.request_record_view_option() == "1":

                    country_records = None
                    while country_records is None:

                        country = console.request_record_country()

                        if country is None:
                            break

                        found = data_manager.query_by_country(record_email, country)
                        if found:
                            country_records = found

                        else:
                            console.display_message(
                                f"\nNo hotel records found for a country matching '{country}'."
                            )

                    if country_records is None:
                        continue
                    records = country_records


                console.display_records(records)

            elif menu_display == "3":

<<<<<<< HEAD
                if IOManager.admin_login(
                    ADMIN_USER,
                    ADMIN_PASSWORD
                ):
=======
                if console.admin_login(ADMIN_USER, ADMIN_PASSWORD):
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a

                    console.display_records(
                        data_manager.load()
                    )

            elif menu_display == "4":
<<<<<<< HEAD

                IOManager.display_message(
                    "Thanks for using our app!"
                )
                break

        except EOFError as error:

            IOManager.display_message(
                str(error)
            )

=======
                console.display_message("Thanks for using our app!")
                break

        except EOFError as error:
            console.display_message(str(error))
>>>>>>> c140c5128f519558eb7249c1b3d0dd7210a1fc1a
            continue


if __name__ == "__main__":
    main()