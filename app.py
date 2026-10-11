import os
import logging
from dotenv import load_dotenv
import ai_manager as AIManager
import data_manager as DataManager
import IO_manager as IOManager

load_dotenv(".env")

ADMIN_USER = "team8"
ADMIN_PASSWORD = "12345"


#NO PRINTS AND INPUTS ALLOWED!

def main():
    
    while True:

        menu_display = IOManager.show_main_menu()

        if menu_display == "1":

            user_input_details = {}

            try:

                mandatory_data = IOManager.request_mandatory_inputs()
                user_prefs = IOManager.request_user_preferences()
                
                # Combine everything to show the final structured output
                final_search_payload = {
                    **mandatory_data,
                    "preferences": user_prefs
                }


                user_input_details["destination"] = final_search_payload["location"]
                user_input_details["budget_min"] = final_search_payload["price_range"]["min"]
                user_input_details["budget_max"] = final_search_payload["price_range"]["min"]
                user_input_details["email_address"] = final_search_payload["email_address"]
                user_input_details["preferences"] = final_search_payload["preferences"]

                
            except EOFError as e:
                # Catch the safe exit triggered by Ctrl+C or Ctrl+D in _safe_input
                logging.error("Input cancelled by user: %s", e)


            ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
            ai_manager_result = AIManager.data_process(user_input_details, ai_manager_connection)

            #Hasini implement this inside ai_manager when airesult is none
            try:
                hotels = ai_manager_result["hotels"]  # LOGIC MANAGER USE THIS
                email = user_input_details["email_address"]

                DataManager.save({email: hotels})
            except TypeError:
                IOManager.display_message("We encountered an issue fetching hotel data. Please try again.")

        elif menu_display == "2":
            #def query(fn)
            record_email = IOManager.request_record_email()
            IOManager.display_records(DataManager.query(record_email))


        elif menu_display == "3":
            #def load()
            if IOManager.admin_login(ADMIN_USER, ADMIN_PASSWORD):
                IOManager.display_records(DataManager.load())


if __name__ == "__main__":
    main()