import os
from dotenv import load_dotenv
import ai_manager as AIManager

load_dotenv(".env")

def main():

    #Using this as replacement of IO manager for now

    user_input_fields = {
        "destination": "Singapore, Raffles Place",
        "budget_min": 300,
        "budget_max": 500,
        "email_address": "testing@gmail.com",
        "preferences": "near MRT, family friendly",
    }

    ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
    ai_manager_result = AIManager.data_process(user_input_fields, ai_manager_connection)
    

    #This will output as dictionary. Logic manager access this dictionary
    #process your logic etc.
    print(ai_manager_result)
    

if __name__ == "__main__":
    main()