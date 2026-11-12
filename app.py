import os
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv
from ai_manager.ai_factory import AIManagerFactory
from data_managerpart2.data_manager import DataManager, RECORDS_FILE
from data_managerpart2.json_storage import JsonStorage
from data_managerpart2.memory_storage import MemoryStorage
from data_managerpart2.send_email import EmailSender
import io_manager_part2.__init__ as IOManager
import logic_manager_part2.logic_manager as LogicManager
load_dotenv(Path(__file__).resolve().with_name(".env"))

ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


# NO PRINTS AND INPUTS ALLOWED!

def main():
    console = IOManager.ConsoleView()
    sender = EmailSender(os.environ.get("EMAIL_ADDRESS"), os.environ.get("EMAIL_APP_PASSWORD"))
    ai_manager = AIManagerFactory.create_hotel_manager()


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


                
                mandatory_data = console.request_mandatory_inputs()
                user_prefs = console.request_user_preferences()

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

                ai_manager_result = ai_manager.generate_candidates(user_input_details)
                
                # Prevent crash if AI Manager/API fails
                if ai_manager_result is None:
                    console.display_message(
                        "Hotel recommendation service is currently unavailable. Please try again later."
                    )
                    continue

                email = user_input_details["email_address"]

                # STEP 1: Keep the original AI output for Logic Manager
                original_ai_output = ai_manager_result

                # Create a separate copy for displaying the AI output
                ai_manager_result = ai_manager_result.copy()

                ai_manager_result[str(uuid.uuid4())] = ai_manager_result.pop("hotels")

                #This will output as dictionary. Logic manager access this dictionary process your logic etc.
                console.display_ai_dictionary(ai_manager_result)

                # STEP 3: Process hotels using Logic Manager
                logic_result = logic_manager.process_hotels(
                    original_ai_output,
                    user_input_details
                )

                # STEP 4: Display neatly formatted Top 3 hotels
                console.display_recommendations(
                    logic_result,
                    user_input_details
                )

                # STEP 5: Display Top 3 hotels using original AI data

                # Match ranked hotels to the original AI hotel dictionaries
                original_hotels_by_name = {
                    hotel["name"]: hotel
                    for hotel in original_ai_output["hotels"]
                }


                # Keep only the Top 3, in their ranked order
                top_three_dict = {
                    "top_hotels": [
                        original_hotels_by_name[hotel["name"]]
                        for hotel in logic_result["top_hotels"]
                    ]
                }

                console.display_top_three_dictionary(top_three_dict)

                # DATA MANAGER: save the top 3 in the same format as the printed dictionary
                if top_three_dict["top_hotels"]:

                    sender.send(
                        to_address=email,
                        subject="Your Hotel Recommendations for " + user_input_details["destination"],
                        body=f"Here are the top 3 hotels you might like!\n\n{top_three_dict['top_hotels']}"
                    )

                    data_manager.save({
                        email: top_three_dict["top_hotels"]
                    })
                    console.display_message(
                        "Hotel recommendations saved successfully."
                    )
                else:
                    console.display_message(
                        "No hotels matched your requirements, nothing was saved."
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

                if console.admin_login(ADMIN_USER, ADMIN_PASSWORD):

                    console.display_records(
                        data_manager.load()
                    )

            elif menu_display == "4":
                console.display_message("Thanks for using our app!")
                break

        except EOFError as error:
            console.display_message(str(error))
            continue


if __name__ == "__main__":
    main()