from .ai_errors import AIError

class RecoverableProviderError(AIError):
    """A single model attempt failed but another model may succeed.

    Examples: rate limit (429), server errors (5xx), timeouts, dropped
    connections.
    """