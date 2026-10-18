"""Client failures preserve transport uncertainty without inventing domain results."""

from hfcache.errors import ConfigurationError, ExitCode, HfcacheError, Problem, SafetyError


class ClientProtocolError(ConfigurationError):
    def __init__(self) -> None:
        super().__init__([Problem("HFAPI018", "API response or protocol is incompatible")])


class ClientConnectionError(SafetyError):
    def __init__(self) -> None:
        super().__init__([Problem("HFAPI019", "API connection or observation is unavailable")])


class UncertainSubmission(SafetyError):  # noqa: N818 - public retained-key submission result name
    """Retain the original key for lookup; this exception never submits again."""

    def __init__(self, key: str, route: str) -> None:
        self.key, self.route = key, route
        super().__init__(
            [Problem("HFAPI020", "Submission outcome is uncertain; inspect its original key")]
        )


class RemoteApiError(HfcacheError):
    """A validated stable API refusal, with no untrusted remote message interpolation."""

    def __init__(self, *, code: str, exit_code: int, status_code: int, request_id: str) -> None:
        self.code, self.status_code, self.request_id = code, status_code, request_id
        self.key: str | None = None
        self.route: str | None = None
        self.exit_code = ExitCode(exit_code)
        super().__init__(
            [Problem(code, "API request was refused", context={"request_id": request_id})]
        )
