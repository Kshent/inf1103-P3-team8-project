from __future__ import annotations

from .ai_attempt import AIAttempt
from .ai_logger import AILogger
from .ai_provider import AIProvider
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .response_validator import ResponseValidator


class AIManager:
    """Coordinates prompt creation, AI calls, parsing, validation, and correction."""

    def __init__(
        self,
        provider: AIProvider,
        prompt_builder: PromptBuilder,
        response_parser: ResponseParser,
        response_validator: ResponseValidator,
        logger: AILogger,
    ):
        self.__provider = provider
        self.__prompt_builder = prompt_builder
        self.__response_parser = response_parser
        self.__response_validator = response_validator
        self.__logger = logger

    def generate_candidates(self, record: dict) -> dict | None:
        """
        Return a validated AI response dictionary.

        Performs one normal AI request and, if that response exists
        but fails validation, performs at most one correction request.
        """

        prompt = self.__prompt_builder.build_prompt(record)

        # First AI request
        first_attempt = self.__attempt(prompt)

        # First response is valid
        if first_attempt.data is not None:
            return first_attempt.data

        # API failure: no response exists to correct
        if first_attempt.raw_text is None:
            self.__logger.error(
                "AI processing stopped because no Gemini model returned a response."
            )
            return None

        # First response exists but is invalid
        self.__logger.warning(
            "Gemini returned an invalid response. Attempting one regeneration."
        )

        correction_prompt = self.__prompt_builder.build_correction_prompt(
            prompt,
            first_attempt.raw_text,
        )

        # One correction attempt
        second_attempt = self.__attempt(correction_prompt)

        # Corrected response is valid
        if second_attempt.data is not None:
            return second_attempt.data

        # API failed during correction
        if second_attempt.raw_text is None:
            self.__logger.error(
                "Correction attempt stopped because no Gemini model returned a response."
            )
            return None

        # Corrected response still failed validation
        self.__logger.error(
            "Gemini response remained invalid after regeneration."
        )

        return None

    def __attempt(self, prompt: str) -> AIAttempt:
        """Perform one AI call, parse the response, and validate the result."""

        raw_text = self.__provider.call_api(prompt)

        if raw_text is None:
            return AIAttempt(
                raw_text=None,
                data=None,
            )

        parsed_data = self.__response_parser.parse_response(raw_text)

        if self.__response_validator.validate_response(parsed_data):
            return AIAttempt(
                raw_text=raw_text,
                data=parsed_data,
            )

        return AIAttempt(
            raw_text=raw_text,
            data=None,
        )