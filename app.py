import os
import uuid
from dotenv import load_dotenv
import ai_manager as AIManager

load_dotenv(".env")

def main():

    #Using this as replacement of IO manager for now

    #focus on destination, no city. For preferences, 
    user_input_fields = {
        "destination": "Singapore",
        "budget_min": 200,
        "budget_max": 400,
        "email_address": "testing@gmail.com",
        "preferences": "Nice food places to eat",
    }

    ai_manager_connection = AIManager.get_model(api_key=os.environ.get("GEMINI_API_KEY"))
    ai_manager_result = AIManager.data_process(user_input_fields, ai_manager_connection)
    

    #This will output as dictionary. Logic manager access this dictionary
    #process your logic etc.
    ai_manager_result[str(uuid.uuid4())] = ai_manager_result.pop("hotels")

    print(ai_manager_result)
    

if __name__ == "__main__":
    main()