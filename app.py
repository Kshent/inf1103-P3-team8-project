import os
import uuid
from dotenv import load_dotenv
import ai_manager as AIManager
# import data_manager as DataManager
import IO_manager as IOManager
import logic_manager as LogicManager
import result_display as ResultDisplay

load_dotenv(".env")

def main():

    # #Using this as replacement of IO manager for now

    # #focus on destination, no city. For preferences, 
    # user_input_fields = {
    #     "destination": "Singapore",
    #     "budget_min": 200,
    #     "budget_max": 400,
    #     "email_address": "testing@gmail.com",
    #     "preferences": "Nice food places to eat",
    # }

    # ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
    # ai_manager_result = AIManager.data_process(user_input_fields, ai_manager_connection)
    
    # ai_manager_result[str(uuid.uuid4())] = ai_manager_result.pop("hotels")

    # #This will output as dictionary. Logic manager access this dictionary
    # #process your logic etc.
    # print(ai_manager_result)

    # #Saves final output of logic manager
    # DataManager.save_record(ai_manager_result)

    user_input_details = {}

    try:
        # Step 1: Gather the required traveler details
        mandatory_data = IOManager.request_mandatory_inputs()
        
        # Step 2: Gather optional AI personalization preferences
        user_prefs = IOManager.request_user_preferences()
        
        # Combine everything to show the final structured output
        final_search_payload = {
            **mandatory_data,
            "preferences": user_prefs
        }
        
        print("\n=== Cleaned & Validated Data Prepared for Search ===")


        user_input_details["destination"] = final_search_payload["location"]
        user_input_details["budget_min"] = final_search_payload["price_range"]["min"]
        user_input_details["budget_max"] = final_search_payload["price_range"]["max"]
        user_input_details["email_address"] = final_search_payload["email_address"]
        user_input_details["preferences"] = final_search_payload["preferences"]

        
    except EOFError as e:
        # Catch the safe exit triggered by Ctrl+C or Ctrl+D in _safe_input
        print(e)
        return
    
    


    ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
    ai_manager_result = AIManager.data_process(user_input_details, ai_manager_connection)

    # Prevent crash if AI Manager/API fails
    if ai_manager_result is None:
        print("Hotel recommendation service is currently unavailable. Please try again later.")
        return
    
    logic_result = LogicManager.process_hotels(ai_manager_result, user_input_details)
    ResultDisplay.show_recommendations(logic_result, user_input_details)    
    
    ai_manager_result[str(uuid.uuid4())] = ai_manager_result.pop("hotels")

    #This will output as dictionary. Logic manager access this dictionary process your logic etc.
    print(ai_manager_result)
    

if __name__ == "__main__":
    main()