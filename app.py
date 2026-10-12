import os
import logging
from dotenv import load_dotenv
import ai_manager as AIManager
import data_manager as DataManager
import IO_manager as IOManager

load_dotenv(".env")

ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


# NO PRINTS AND INPUTS ALLOWED!

def main():

    while True:

        menu_display = IOManager.show_main_menu()

        if menu_display == "1":

            user_input_details = {}

            try:
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

            except EOFError as e:
                logging.error("Input cancelled by user: %s", e)
                return


            ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))

            ai_manager_result = AIManager.data_process(user_input_details,ai_manager_connection)

            # FIX FROM AI BRANCH
            if ai_manager_result is None:
                IOManager.display_message(
                    "We encountered an issue fetching hotel data. Please try again."
                )
                continue


            # AI Manager output remains unchanged
            hotels = ai_manager_result["hotels"]

            # Logic Manager will eventually use this
            email = user_input_details["email_address"]

            #added this for testing purpose after ai and data managers integration, to display the hotels in the console
            IOManager.display_hotels(hotels)

            # Save AI hotel results through Data Manager
            DataManager.save({
                email: hotels
            })


            IOManager.display_message(
            "Hotel recommendations saved successfully."
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


if __name__ == "__main__":
    main()