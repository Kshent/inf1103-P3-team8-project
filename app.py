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

class HotelRecommenderApp:
    ADMIN_USER = "team8"
    ADMIN_PASSWORD = "12345"

    def __init__(self):
        self.console = IOManager.ConsoleView()
        self.sender = EmailSender(os.environ.get("EMAIL_ADDRESS"),
                                  os.environ.get("EMAIL_APP_PASSWORD"))
        self.ai_manager = AIManagerFactory.create_hotel_manager()
        self.data_manager = DataManager(self.create_storage())
        # Created fresh for every search (see search_hotels)
        self.logic_manager = None

    @staticmethod
    def create_storage():
        """DATA_STORAGE=memory runs without saving to disk (e.g. for a demo);
        anything else uses the JSON records file."""
        if os.environ.get("DATA_STORAGE", "json").lower() == "memory":
            return MemoryStorage()
        return JsonStorage(RECORDS_FILE)

    # menu loop
    def run(self):
        while True:
            try:
                menu_display = self.console.show_main_menu()

                if menu_display == "1":
                    self.search_hotels()
                elif menu_display == "2":
                    self.view_my_records()
                elif menu_display == "3":
                    self.view_all_records()
                elif menu_display == "4":
                    self.console.display_message("Thanks for using our app!")
                    break

            except EOFError as error:
                self.console.display_message(str(error))
                continue

    #   option 1: search for hotels
    def search_hotels(self):
        user_input_details = {}

        mandatory_data = self.console.request_mandatory_inputs()
        user_prefs = self.console.request_user_preferences()

        # Create Logic Manager
        self.logic_manager = LogicManager.LogicManager()

        # Ask Logic which scoring categories are applicable
        allowed_keys = self.logic_manager.available_weight_keys(user_prefs)

        # IO collects the traveller style and custom weights
        while True:

            traveller_profile = self.console.request_traveller_profile(
                allowed_keys=allowed_keys
            )

            try:
                selected_profile = self.logic_manager.resolve_profile(
                    traveller_profile,
                    user_prefs
                )
                break

            except ValueError as error:
                self.console.display_message(
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

        ai_manager_result = self.ai_manager.generate_candidates(
            user_input_details)

        # Prevent crash if AI Manager/API fails
        if ai_manager_result is None:
            self.console.display_message(
                "Hotel recommendation service is currently unavailable. Please try again later."
            )
            return

        email = user_input_details["email_address"]
        original_ai_output = ai_manager_result # Keep the original AI output for Logic Manager
        ai_manager_result = ai_manager_result.copy() # Create a separate copy for displaying the AI output
        ai_manager_result[str(uuid.uuid4())] = ai_manager_result.pop("hotels")

        # This will output as dictionary
        self.console.display_ai_dictionary(ai_manager_result)

        # Process hotels using Logic Manager
        logic_result = self.logic_manager.process_hotels(
            original_ai_output,
            user_input_details
        )

        # Display neatly formatted Top 3 hotels
        self.console.display_recommendations(
            logic_result,
            user_input_details
        )

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

        self.console.display_top_three_dictionary(top_three_dict)

        # DATA MANAGER: save the top 3 in the same format as the printed
        # dictionary
        if top_three_dict["top_hotels"]:

            self.sender.send(
                to_address=email,
                subject="Your Hotel Recommendations for " + user_input_details["destination"],
                body=f"Here are the top 3 hotels you might like!\n\n{top_three_dict['top_hotels']}"
            )

            self.data_manager.save({
                email: top_three_dict["top_hotels"]
            })
            self.console.display_message(
                "Hotel recommendations saved successfully."
            )
        else:
            self.console.display_message(
                "No hotels matched your requirements, nothing was saved."
            )

    # option 2: view saved records for one email
    def view_my_records(self):
        record_email = self.console.request_record_email()
        records = self.data_manager.query(record_email)

        # Nothing saved for this email, so no need to ask how to view it
        if not records:
            self.console.display_records(records)
            return

        if self.console.request_record_view_option() == "1":

            country_records = None
            while country_records is None:

                country = self.console.request_record_country()

                if country is None:
                    break

                found = self.data_manager.query_by_country(
                    record_email, country)
                if found:
                    country_records = found

                else:
                    self.console.display_message(
                        f"\nNo hotel records found for a country matching '{country}'."
                    )

            if country_records is None:
                return
            records = country_records

        self.console.display_records(records)

    # option 3: admin sees every record
    def view_all_records(self):
        if self.console.admin_login(self.ADMIN_USER, self.ADMIN_PASSWORD):
            self.console.display_records(
                self.data_manager.load()
            )

def main():
    HotelRecommenderApp().run()

if __name__ == "__main__":
    main()