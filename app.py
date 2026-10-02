<<<<<<< HEAD
print("Test if can run code")
## zy test git pull git commit
=======
import os
import json
from dotenv import load_dotenv

from google import genai


MODEL_VERSION = "gemini-3.6-flash"

#first git "Establish successful gemini api connection"
def get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("api key is not found unfortunately.")
        return None
    return genai.Client(api_key=api_key)


if __name__ == "__main__":

    client = get_model()
    print("Successfully run get_model()")
>>>>>>> d6e624fb0e76c4c3f1ec1a8909d6942d4990acb2
