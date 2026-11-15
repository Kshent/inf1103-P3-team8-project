from __future__ import annotations

from google.genai import errors, types

from .ai_config import AIConfig
from .ai_logger import AILogger
from .base_ai_provider import BaseAIProvider
from .fatal_provider_error import FatalProviderError
from .recoverable_provider_error import RecoverableProviderError


class GeminiProvider(BaseAIProvider):
    """Gemini implementation for a single model request.

    Model fallback behaviour is handled by BaseAIProvider.
    This class is responsible only for communicating with Gemini.
    """

    def __init__(
        self,
        logger: AILogger,
        client,
        models=AIConfig.MODEL_FALLBACKS,
    ):
        super().__init__(logger, models)
        self.__client = client

    @property
    def name(self) -> str:
        """Return the provider name used by the AI Manager."""

        return "Gemini"

    def _generate(self, model: str, prompt: str) -> str | None:
        """Send one request to one Gemini model."""

        if self.__client is None:
            raise FatalProviderError(
                "Gemini API request could not start because client is unavailable."
            )

        try:
            response = self.__client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    automatic_function_calling=
                    types.AutomaticFunctionCallingConfig(
                        disable=True
                    )
                ),
            )

            return response.text

        except errors.APIError as error:

            message = f"API error code {error.code}: {error}"

            if error.code in AIConfig.RECOVERABLE_API_ERROR_CODES:
                raise RecoverableProviderError(message) from error

            raise FatalProviderError(message) from error

        except (TimeoutError, ConnectionError) as error:

            raise RecoverableProviderError(
                f"connection problem ({type(error).__name__}): {error}"
            ) from error