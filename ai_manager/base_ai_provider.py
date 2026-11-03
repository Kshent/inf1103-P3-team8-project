from __future__ import annotations

from abc import ABC, abstractmethod

from .ai_logger import AILogger
from .ai_provider import AIProvider
from .recoverable_provider_error import RecoverableProviderError
from .fatal_provider_error import FatalProviderError


class BaseAIProvider(AIProvider, ABC):
    """Abstract class (is-a): owns the model-fallback algorithm once.

    Template Method pattern: call_api() fixes the algorithm; subclasses only
    implement _generate(), a single attempt on a single model.
    """

    def __init__(self, logger: AILogger, models):
        models = tuple(models)
        if not models:
            raise ValueError("At least one model is required.")
        self._logger = logger
        self._models = models

    def call_api(self, prompt: str) -> str | None:
        for model in self._models:
            try:
                text = self._generate(model, prompt)
                if text:
                    return text
                self._logger.warning(
                    "Model %s returned an empty response. "
                    "Attempting fallback model.",
                    model,
                )
            except RecoverableProviderError as error:
                self._logger.warning(
                    "Model %s failed: %s. Attempting fallback model.",
                    model,
                    error,
                )
            except FatalProviderError as error:
                self._logger.error(
                    "Model %s encountered a non-recoverable error: %s",
                    model,
                    error,
                )
                return None
            except Exception as error:  # honour "never raise" contract
                self._logger.error(
                    "Unexpected error while calling model %s. "
                    "Error type: %s. Reason: %s",
                    model,
                    type(error).__name__,
                    error,
                )
                return None

        self._logger.error(
            "All %s models failed. Models attempted: %s",
            self.name,
            ", ".join(self._models),
        )
        return None

    @abstractmethod
    def _generate(self, model: str, prompt: str) -> str | None:
        """One attempt on one model.

        Return text (or None/empty if the model gave nothing). Raise
        RecoverableProviderError to try the next model, FatalProviderError to
        stop.
        """
