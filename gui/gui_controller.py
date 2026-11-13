from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from nicegui import run

from ai_manager.ai_factory import AIManagerFactory

from data_managerpart2.data_manager import (
    DataManager,
    RECORDS_FILE,
)
from data_managerpart2.json_storage import JsonStorage
from data_managerpart2.memory_storage import MemoryStorage
from data_managerpart2.send_email import EmailSender

import logic_manager_part2.logic_manager as LogicManager


class GuiController:
    """
    Connects the NiceGUI pages to the existing
    AI, Logic and Data layers.
    """

    PROFILE_NAMES = {
        '1': 'Balanced',
        '2': 'Budget Focused',
        '3': 'Quality Focused',
        '4': 'Customisation',
    }

    ADMIN_USER = 'team8'
    ADMIN_PASSWORD = '12345'

    def __init__(self) -> None:

        # Load .env from project root
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(project_root / '.env')

        # Create existing managers
        self.ai_manager = (
            AIManagerFactory.create_hotel_manager()
        )

        self.logic_manager = (
            LogicManager.LogicManager()
        )

        # Same Data Manager setup as app.py
        if (
            os.environ.get(
                'DATA_STORAGE',
                'json'
            ).lower()
            == 'memory'
        ):
            storage = MemoryStorage()

        else:
            storage = JsonStorage(RECORDS_FILE)

        self.data_manager = DataManager(storage)

        self.email_sender = EmailSender(
            os.environ.get('EMAIL_ADDRESS'),
            os.environ.get('EMAIL_APP_PASSWORD'),
        )

    def profile_name(
        self,
        choice: str,
    ) -> str:

        return self.PROFILE_NAMES.get(
            choice,
            'Traveller Profile',
        )

    def _resolve_profile(
        self,
        choice: str,
        preferences: str,
        custom_weights: dict[str, int],
    ):

        profiles = {
            '1': {
                'name': 'balanced',
                'label': 'Balanced',
                'weights': None,
            },
            '2': {
                'name': 'budget',
                'label': 'Budget focused',
                'weights': None,
            },
            '3': {
                'name': 'quality_focused',
                'label': 'Quality Focused',
                'weights': None,
            },
            '4': {
                'name': 'custom',
                'label': 'Customisation',
                'weights': custom_weights,
            },
        }

        traveller_profile = profiles[choice]

        return self.logic_manager.resolve_profile(
            traveller_profile,
            preferences,
        )

    async def search_hotels(
        self,
        destination: str,
        budget_min: float,
        budget_max: float,
        email: str,
        preferences: str,
        profile_choice: str,
        custom_weights: dict[str, int],
    ) -> dict:
        """
        Run the same hotel search workflow currently
        performed by app.py.
        """

        # Resolve traveller profile through Logic Manager
        selected_profile = self._resolve_profile(
            profile_choice,
            preferences,
            custom_weights,
        )

        user_input_details = {
            'destination': destination,
            'budget_min': budget_min,
            'budget_max': budget_max,
            'email_address': email,
            'preferences': preferences,
            'priority_profile': selected_profile,
        }

        # Gemini call is blocking I/O.
        # Run it outside the GUI event loop.
        ai_result = await run.io_bound(
            self.ai_manager.generate_candidates,
            user_input_details,
        )

        if ai_result is None:

            raise RuntimeError(
                'Hotel recommendation service is '
                'currently unavailable.'
            )

        # Existing Logic Manager
        logic_result = (
            self.logic_manager.process_hotels(
                ai_result,
                user_input_details,
            )
        )

        # Same matching logic from your app.py
        original_hotels_by_name = {
            hotel['name']: hotel
            for hotel in ai_result['hotels']
        }

        top_three_original = [
            original_hotels_by_name[hotel['name']]
            for hotel in logic_result['top_hotels']
        ]

        saved = False

        if top_three_original:

            # Save recommendations
            await run.io_bound(
                self.data_manager.save,
                {
                    email:
                    top_three_original
                },
            )

            saved = True

            # Send email
            await run.io_bound(
                self.email_sender.send,
                to_address=email,
                subject=(
                    'Your Hotel Recommendations for '
                    + destination
                ),
                body=(
                    'Here are the top 3 hotels '
                    'you might like!\n\n'
                    f'{top_three_original}'
                ),
            )

        return {
            'logic_result': logic_result,
            'user_input_details': user_input_details,
            'profile_name': self.profile_name(
                profile_choice
            ),
            'saved': saved,
        }

    def query_records(
        self,
        email: str,
        country: str = '',
    ):

        if country.strip():

            return (
                self.data_manager.query_by_country(
                    email,
                    country.strip(),
                )
            )

        return self.data_manager.query(email)

    def load_all_records(self):

        return self.data_manager.load()

    def admin_login(
        self,
        username: str,
        password: str,
    ) -> bool:

        return (
            username == self.ADMIN_USER
            and password == self.ADMIN_PASSWORD
        )