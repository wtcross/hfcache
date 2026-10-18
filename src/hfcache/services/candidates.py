"""Non-network candidate policy assessment; installation belongs outside REST.

Plan §7 and decision 116 require installed authority before candidate planning.
These pure API-012 hooks cannot resolve credentials or load caller-selected paths.
"""

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hfcache.config import validate_config_mapping
from hfcache.errors import ConfigurationError, RequestError

if TYPE_CHECKING:
    from hfcache.config import ApplicationConfig

MAXIMUM_CANDIDATE_BYTES = 1048576


@dataclass(frozen=True, slots=True)
class CandidateAssessment:
    config: ApplicationConfig
    mismatches: tuple[str, ...]

    @property
    def authority_compatible(self) -> bool:
        return not self.mismatches


def authority_mismatches(
    candidate: ApplicationConfig, installed: ApplicationConfig
) -> tuple[str, ...]:
    """Compare only fixed authority fields; return names, never their values."""
    fields = (
        ("storage.archive_root", candidate.storage.archive_root, installed.storage.archive_root),
        ("storage.archive_id", candidate.storage.archive_id, installed.storage.archive_id),
        ("hub.endpoint", candidate.hub.endpoint, installed.hub.endpoint),
        ("hub.token_mode", candidate.hub.token_mode, installed.hub.token_mode),
        ("hub.credential_name", candidate.hub.credential_name, installed.hub.credential_name),
        ("hub.expected_account", candidate.hub.expected_account, installed.hub.expected_account),
    )
    return tuple(name for name, proposed, current in fields if proposed != current)


def assess_candidate(candidate: str, installed: ApplicationConfig) -> CandidateAssessment:
    """Validate syntax/policy independently of authority compatibility; never read files."""
    if not isinstance(candidate, str):
        raise RequestError
    try:
        encoded = candidate.encode("utf-8")
    except UnicodeError:
        raise RequestError from None
    if not encoded or len(encoded) > MAXIMUM_CANDIDATE_BYTES:
        raise RequestError(status_code=413)
    try:
        mapping = tomllib.loads(candidate)
    except tomllib.TOMLDecodeError:
        msg = "Candidate is not valid TOML"
        raise ConfigurationError.single(msg, code="HFCFG002") from None
    config = validate_config_mapping(mapping)
    return CandidateAssessment(config, authority_mismatches(config, installed))


def require_compatible_authority(
    candidate: ApplicationConfig, installed: ApplicationConfig
) -> None:
    """A candidate cannot redirect the installed credential or switch archive authority."""
    if authority_mismatches(candidate, installed):
        raise RequestError(
            code="HFAPI007",
            status_code=409,
            message="Candidate policy changes installed writer authority",
        )
