from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

from .ai_error_logger import AIErrorLogger
from .ai_logger import AILogger
from .ai_manager import AIManager
from .ai_provider import AIProvider
from .ai_response_parser import AIResponseParser
from .hotel_prompt_builder import HotelPromptBuilder
from .hotel_response_validator import HotelResponseValidator


class AIManagerFactory:
    """Composition root: the only place concrete classes are wired together.

    Environment and API-key handling live here, not in the provider or manager.
    """

    @staticmethod
    def create_gemini_client(
        logger: AILogger,
        api_key: str | None = None,
    ):
        """Return a Gemini client, or None if no API key is available."""

        project_root = Path(__file__).resolve().parent.parent
        env_file = project_root / ".env"

        load_dotenv(env_file)

        api_key = api_key or os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.error("Gemini API key was not found.")
            return None

        from google import genai

        return genai.Client(api_key=api_key)

    @staticmethod
    def create_hotel_manager(
        provider: AIProvider | None = None, logger: AILogger | None = None
    ) -> AIManager:
        """Build a hotel AIManager. Pass a provider (e.g. FakeAIProvider) to
        run without a live API; pass nothing for production Gemini."""
        logger = logger or AIErrorLogger()
        if provider is None:
            from .gemini_provider import GeminiProvider

            client = AIManagerFactory.create_gemini_client(logger)
            provider = GeminiProvider(logger, client)

        return AIManager(
            provider,
            HotelPromptBuilder(),
            AIResponseParser(),
            HotelResponseValidator(),
            logger,
        )
