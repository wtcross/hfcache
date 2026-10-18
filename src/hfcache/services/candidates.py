"""Non-network candidate policy assessment; installation belongs outside REST.

Plan §7 and decision 116 require installed authority before candidate planning.
These pure API-012 hooks cannot resolve credentials or load caller-selected paths.
"""

import re
import tomllib
from dataclasses import dataclass

from hfcache.config import (
    ApplicationConfig,
    HubConfig,
    RepairConfig,
    RepositoryConfig,
    StorageConfig,
    SyncConfig,
    VerificationConfig,
    validate_config_mapping,
)
from hfcache.errors import ConfigurationError, HfcacheError, Problem, RequestError
from hfcache.services.context import ServiceResult
from hfcache.services.queries import validate_config

MAXIMUM_CANDIDATE_BYTES = 1048576
_KNOWN_FIELDS = frozenset(ApplicationConfig.model_fields) | frozenset(
    prefix + "." + field
    for prefix, model in (
        ("storage", StorageConfig),
        ("hub", HubConfig),
        ("sync", SyncConfig),
        ("verification", VerificationConfig),
        ("repair", RepairConfig),
        ("repositories[]", RepositoryConfig),
    )
    for field in model.model_fields
)


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
    config = parse_candidate(candidate)
    return CandidateAssessment(config, authority_mismatches(config, installed))


def parse_candidate(candidate: str) -> ApplicationConfig:
    """Parse content without consulting installed files, credentials or archive paths."""
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
        return validate_config_mapping(mapping)
    except tomllib.TOMLDecodeError, RecursionError:
        msg = "Candidate is not valid TOML"
        raise ConfigurationError.single(msg, code="HFCFG002") from None


def candidate_problems(error: HfcacheError) -> tuple[Problem, ...]:
    """Keep every ordered code while rejected values stay out of outputs/receipts."""
    safe = []
    for problem in error.problems:
        location = problem.location or "candidate"
        if re.sub(r"\[\d+\]", "[]", location) not in _KNOWN_FIELDS:
            location = "candidate"
        message = (
            "Candidate authority is incompatible with installed policy"
            if problem.code == "HFAPI007"
            else "Candidate policy is invalid"
        )
        safe.append(Problem(problem.code, message, location=location))
    return tuple(safe)


def validate_candidate(content: str, installed: ApplicationConfig | None) -> ServiceResult:
    """Syntax validation is independent of authority and never resolves a credential."""
    try:
        config = parse_candidate(content)
    except HfcacheError as error:
        return ServiceResult(
            "config validate",
            {
                "valid": False,
                "syntax_valid": False,
                "authority_compatible": None,
                "authority_mismatches": [],
                "installed_policy_valid": installed is not None,
            },
            errors=candidate_problems(error),
            exit_code=int(error.exit_code),
        )
    mismatches = authority_mismatches(config, installed) if installed is not None else ()
    return ServiceResult(
        "config validate",
        validate_config(config, token_source="not-resolved").data  # noqa: S106 - provenance label
        | {
            "valid": True,
            "syntax_valid": True,
            "authority_compatible": not mismatches if installed is not None else None,
            "authority_mismatches": list(mismatches),
            "installed_policy_valid": installed is not None,
        },
    )


def prepare_candidate_plan(
    content: str, installed: ApplicationConfig
) -> CandidateAssessment | ServiceResult:
    """Fresh admission only; freeze candidate intent or a complete safe domain refusal."""
    try:
        assessment = assess_candidate(content, installed)
        require_compatible_authority(assessment.config, installed)
    except HfcacheError as error:
        return ServiceResult(
            "plan", {}, errors=candidate_problems(error), exit_code=int(error.exit_code)
        )
    return assessment


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
