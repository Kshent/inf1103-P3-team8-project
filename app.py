import os
import uuid
import logging
from dotenv import load_dotenv
import ai_manager as AIManager
import data_manager as DataManager
import IO_manager as IOManager
import logic_manager as LogicManager

load_dotenv(".env")

ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


# NO PRINTS AND INPUTS ALLOWED!

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

                user_input_details["destination"] = final_search_payload["location"]
                user_input_details["budget_min"] = final_search_payload["price_range"]["min"]
                user_input_details["budget_max"] = final_search_payload["price_range"]["max"]
                user_input_details["email_address"] = final_search_payload["email_address"]
                user_input_details["preferences"] = final_search_payload["preferences"]


                ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
                ai_manager_result = AIManager.data_process(user_input_details, ai_manager_connection)

                # Prevent crash if AI Manager/API fails
                if ai_manager_result is None:
                    IOManager.display_message(
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
                IOManager.display_ai_dictionary(ai_manager_result)

                # STEP 3: Process hotels using Logic Manager
                logic_result = LogicManager.process_hotels(
                    original_ai_output,
                    user_input_details
                )

                # STEP 4: Display neatly formatted Top 3 hotels
                IOManager.display_recommendations(
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

                IOManager.display_top_three_dictionary(top_three_dict)

                # DATA MANAGER: save the top 3 in the same format as the printed dictionary
                if top_three_dict["top_hotels"]:
                    DataManager.save({
                        email: top_three_dict["top_hotels"]
                    })
                    IOManager.display_message(
                        "Hotel recommendations saved successfully."
                    )
                else:
                    IOManager.display_message(
                        "No hotels matched your requirements, nothing was saved."
                    )

            elif menu_display == "2":

                record_email = IOManager.request_record_email()

                IOManager.display_records(
                    DataManager.query(record_email)
                )

            elif menu_display == "3":

                if IOManager.admin_login(ADMIN_USER, ADMIN_PASSWORD):

                    IOManager.display_records(
                        DataManager.load()
                    )

            elif menu_display == "4":
                IOManager.display_message("Thanks for using our app!")
                break

        except EOFError as error:
            IOManager.display_message(str(error))
            continue


if __name__ == "__main__":
    main()