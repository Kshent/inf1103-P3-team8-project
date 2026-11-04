"""app.py - composition root of the hotel recommendation app.

This file only wires the four layers together and runs the menu loop:

    Layer 1  IO_manager     ConsoleView            (all print/input lives here)
    Layer 2  ai_manager     HotelAIService         (Gemini)
    Layer 3  logic_manager  RecommendationEngine   (rules, scoring, ranking)
    Layer 4  data_manager   RecordRepository, ProfileRepository (JSON files)

HotelApp receives its collaborators through the constructor (dependency
injection) and only uses their public methods. Swapping Gemini for another AI,
or the JSON files for a database, means changing build_app() and nothing else.

# NO PRINTS AND INPUTS ALLOWED in this file!
"""
import os
import uuid

import ai_manager as AIManager
import data_manager as DataManager
import io_manager as IOManager
import logic_manager as LogicManager

try:
    from dotenv import load_dotenv
    load_dotenv(".env")
except ImportError:          # python-dotenv is optional
    pass


class HotelApp:
    def __init__(self, view, ai_service, engine, records, profiles,
                 authenticator):
        self.__view = view
        self.__ai_service = ai_service
        self.__engine = engine
        self.__records = records            # RecordRepository
        self.__profiles = profiles          # ProfileRepository
        self.__authenticator = authenticator

        # menu option -> handler (a handler returns False to stop the app)
        self.__handlers = {
            "1": self._find_hotels,
            "2": self._view_my_records,
            "3": self._view_all_records,
            "4": self._quit,
        }

    # ------------------------------------------------------------------
    def run(self):
        while True:
            try:
                choice = self.__view.show_main_menu()
                if self.__handlers[choice]() is False:
                    break
            except EOFError as error:          # input cancelled (Ctrl-C / Ctrl-D)
                self.__view.display_message(str(error))
                break

    # ------------------------------------------------------------------
    # Menu option 1: find a hotel
    # ------------------------------------------------------------------
    def _find_hotels(self):
        details = self._collect_search_details()
        email = details["email_address"]

        saved_profile = self.__profiles.load_profile(email)
        profile_choice = self.__view.request_priority_profile(
            LogicManager.ProfileFactory.catalog(),
            LogicManager.ProfileFactory.categories(),
            saved_profile)
        profile = LogicManager.ProfileFactory.from_dict(profile_choice)

        ai_output = self.__ai_service.fetch_candidates(details)

        # Prevent a crash if the AI Manager / API fails
        if ai_output is None:
            self.__view.display_message(
                "Hotel recommendation service is currently unavailable. "
                "Please try again later.")
            return

        self.__view.display_ai_dictionary(self._as_display_dictionary(ai_output))

        result = self.__engine.recommend(ai_output, details, profile)
        self.__view.display_recommendations(result.to_dict(), details)

        # The top 3 in ranked order, exactly as the AI returned them
        top_three = {"top_hotels": result.original_top_hotels()}
        self.__view.display_top_three_dictionary(top_three)

        self.__profiles.save_profile(email, profile.to_dict())

        if top_three["top_hotels"]:
            self.__records.save(email, top_three["top_hotels"])
            self.__view.display_message(
                "Hotel recommendations saved successfully.")
        else:
            self.__view.display_message(
                "No hotels matched your requirements, nothing was saved.")

    def _collect_search_details(self):
        mandatory = self.__view.request_mandatory_inputs()
        preferences = self.__view.request_user_preferences()
        return {
            "destination": mandatory["location"],
            "budget_min": mandatory["price_range"]["min"],
            "budget_max": mandatory["price_range"]["max"],
            "email_address": mandatory["email_address"],
            "preferences": preferences,
        }

    @staticmethod
    def _as_display_dictionary(ai_output):
        """Copy of the AI output with the hotel list stored under a uuid key
        (the dictionary format shown on screen)."""
        display = dict(ai_output)
        display[str(uuid.uuid4())] = display.pop("hotels")
        return display

    # ------------------------------------------------------------------
    # Menu options 2, 3 and 4
    # ------------------------------------------------------------------
    def _view_my_records(self):
        email = self.__view.request_record_email()
        if email is None:                      # the user chose to go back
            return
        self.__view.display_records(self.__records.find_by_email(email))

    def _view_all_records(self):
        if self.__view.admin_login(self.__authenticator):
            self.__view.display_records(self.__records.find_all())

    def _quit(self):
        self.__view.display_message("Thanks for using our app!")
        return False


def build_app():
    """Create the real objects and connect them."""
    return HotelApp(
        view=IOManager.ConsoleView(),
        ai_service=AIManager.create_default_service(
            os.environ.get("GEMINI_API_KEY")),
        engine=LogicManager.RecommendationEngine.default(),
        records=DataManager.JsonRecordRepository(),
        profiles=DataManager.JsonProfileRepository(),
        authenticator=LogicManager.AdminAuthenticator.from_environment(),
    )


def main():
    build_app().run()


if __name__ == "__main__":
    main()