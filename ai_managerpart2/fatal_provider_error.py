from .ai_errors import AIError

class FatalProviderError(AIError):
    """Retrying on another model is pointless.

    Examples: invalid request, bad API key, missing client.
    """