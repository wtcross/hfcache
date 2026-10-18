"""Token resolution (`docs/configuration.md` §7, `docs/security.md` T-07).

Three things are asserted here that are controls rather than behaviour:

* Every documented resolution branch, including the ones whose correct outcome is
  "no token".
* Every failure shape for both sources, each with the code the taxonomy assigns.
* That a secret cannot escape through a repr, a description, an error message, or
  an exception summary — proven over generated tokens, not one example.
"""

import os
from typing import TYPE_CHECKING, Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

if TYPE_CHECKING:
    from pathlib import Path

from hfcache.config import HubConfig, validate_config_mapping
from hfcache.credentials import (
    AMBIENT_TOKEN_VARIABLES,
    CREDENTIALS_DIRECTORY_VARIABLE,
    MAXIMUM_TOKEN_FILE_BYTES,
    NO_TOKEN,
    RepositoryScope,
    ResolvedToken,
    TokenSource,
    ambient_token_variables,
    resolve_token,
)
from hfcache.errors import ConfigurationError, ExitCode, Problem

SECRET = "hf_ExampleTokenValueNotARealCredential"

# Tokens as the Hub issues them: printable ASCII with no whitespace. The `hf_`
# prefix and minimum length keep a generated value from being a substring of the
# temporary path that also appears in these messages, which would make the
# leak-detection assertions below fail for a reason that is not a leak.
token_strategy = st.builds(
    "hf_{}".format,
    st.text(
        alphabet=st.characters(min_codepoint=0x21, max_codepoint=0x7E, exclude_characters="/"),
        min_size=8,
        max_size=80,
    ),
)


def optional_hub() -> HubConfig:
    """The default `[hub]`: `token_mode = "optional"`."""
    return HubConfig()


def disabled_hub() -> HubConfig:
    return HubConfig(token_mode="disabled")


def required_hub() -> HubConfig:
    return HubConfig(token_mode="required")


def write_token(directory: Path, name: str = "hf-token", body: str = SECRET + "\n") -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def test_resolved_opaque_credentials_are_registered_before_use(tmp_path):
    opaque = "opaque-credential-Q1w2e3r4t5y6u7i8o9p0"
    token = resolve_token(optional_hub(), token_file=write_token(tmp_path, body=opaque))

    assert token.hub_argument == opaque
    problem = Problem(code="HFHUB001", message=f"failed with {opaque}", context={"detail": opaque})
    assert opaque not in repr(problem)
    assert opaque not in str(problem.as_envelope_entry())


def codes_for(**kwargs: Any) -> list[str]:
    with pytest.raises(ConfigurationError) as raised:
        resolve_token(**kwargs)
    return [problem.code for problem in raised.value.problems]


# --------------------------------------------------------------------------- #
# Resolution order (§7): --token-file, then systemd credential, then no token
# --------------------------------------------------------------------------- #


def test_no_source_resolves_to_no_token():
    resolved = resolve_token(optional_hub(), environ={})

    assert resolved.source is TokenSource.NONE
    assert resolved.has_token is False
    assert resolved.secret is None


def test_token_file_is_read_and_trailing_newline_stripped(tmp_path: Path):
    path = write_token(tmp_path)

    resolved = resolve_token(optional_hub(), token_file=path, environ={})

    assert resolved.source is TokenSource.TOKEN_FILE
    assert resolved.origin == path
    assert resolved.secret == SECRET


def test_token_file_without_trailing_newline_is_read(tmp_path: Path):
    path = write_token(tmp_path, body=SECRET)

    assert resolve_token(optional_hub(), token_file=path, environ={}).secret == SECRET


def test_systemd_credential_is_read_when_no_token_file(tmp_path: Path):
    write_token(tmp_path)

    resolved = resolve_token(
        optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    )

    assert resolved.source is TokenSource.SYSTEMD_CREDENTIAL
    assert resolved.origin == tmp_path / "hf-token"
    assert resolved.secret == SECRET


def test_credential_name_selects_the_credential_file(tmp_path: Path):
    write_token(tmp_path, name="hf-token")
    write_token(tmp_path, name="other-token", body="second-value\n")

    resolved = resolve_token(
        HubConfig(credential_name="other-token"),
        environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)},
    )

    assert resolved.secret == "second-value"


def test_token_file_wins_over_systemd_credential(tmp_path: Path):
    # First match wins: an operator running a command by hand overrides the
    # credential the unit installed.
    credentials = tmp_path / "credentials"
    credentials.mkdir()
    write_token(credentials, body="from-systemd\n")
    explicit = write_token(tmp_path, name="explicit", body="from-operator\n")

    resolved = resolve_token(
        optional_hub(),
        token_file=explicit,
        environ={CREDENTIALS_DIRECTORY_VARIABLE: str(credentials)},
    )

    assert resolved.source is TokenSource.TOKEN_FILE
    assert resolved.secret == "from-operator"


def test_absent_credential_in_a_supplied_directory_is_not_an_error(tmp_path: Path):
    # "A credential is used if present. Its absence is not an error" (§3).
    resolved = resolve_token(
        optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    )

    assert resolved.source is TokenSource.NONE


def test_empty_credentials_directory_variable_is_treated_as_unset():
    resolved = resolve_token(optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: ""})

    assert resolved.source is TokenSource.NONE


def test_required_mode_without_any_credential_is_hfarg008():
    assert codes_for(hub=required_hub(), environ={}) == ["HFARG008"]


def test_required_mode_with_absent_named_credential_is_hfarg008(tmp_path: Path):
    assert codes_for(
        hub=required_hub(),
        environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)},
    ) == ["HFARG008"]


def test_required_token_file_enables_restricted_repository_scope(tmp_path: Path):
    resolved = resolve_token(required_hub(), token_file=write_token(tmp_path), environ={})

    assert resolved.repository_scope is RepositoryScope.RESTRICTED
    assert resolved.allows_restricted_repositories is True


def test_required_systemd_credential_enables_restricted_repository_scope(tmp_path: Path):
    write_token(tmp_path)

    resolved = resolve_token(
        required_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    )

    assert resolved.source is TokenSource.SYSTEMD_CREDENTIAL
    assert resolved.repository_scope is RepositoryScope.RESTRICTED


def test_optional_token_remains_public_repository_scope(tmp_path: Path):
    resolved = resolve_token(optional_hub(), token_file=write_token(tmp_path), environ={})

    assert resolved.repository_scope is RepositoryScope.PUBLIC
    assert resolved.allows_restricted_repositories is False


def test_process_environment_is_used_when_no_mapping_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    write_token(tmp_path)
    monkeypatch.setenv(CREDENTIALS_DIRECTORY_VARIABLE, str(tmp_path))

    assert resolve_token(optional_hub()).secret == SECRET


# --------------------------------------------------------------------------- #
# token_mode = "disabled" reads nothing
# --------------------------------------------------------------------------- #


def test_disabled_mode_resolves_to_no_token():
    assert resolve_token(disabled_hub(), environ={}).source is TokenSource.NONE


def test_disabled_mode_does_not_read_an_installed_credential(tmp_path: Path):
    write_token(tmp_path)

    resolved = resolve_token(
        disabled_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    )

    assert resolved.source is TokenSource.NONE
    assert resolved.secret is None


def test_disabled_mode_does_not_read_a_credential_it_could_not_parse(tmp_path: Path):
    # Proof the file is never opened: an unusable credential would be HFARG006
    # in optional mode, and is silent here.
    (tmp_path / "hf-token").write_bytes(b"")

    environ = {CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}

    assert resolve_token(disabled_hub(), environ=environ) == NO_TOKEN


def test_token_file_with_disabled_mode_is_a_contradiction(tmp_path: Path):
    path = write_token(tmp_path)

    assert codes_for(hub=disabled_hub(), token_file=path, environ={}) == ["HFARG002"]


# --------------------------------------------------------------------------- #
# HFARG005 — every documented --token-file failure shape
# --------------------------------------------------------------------------- #


def test_missing_token_file_is_hfarg005(tmp_path: Path):
    assert codes_for(hub=optional_hub(), token_file=tmp_path / "absent", environ={}) == ["HFARG005"]


def test_directory_as_token_file_is_hfarg005(tmp_path: Path):
    assert codes_for(hub=optional_hub(), token_file=tmp_path, environ={}) == ["HFARG005"]


def test_empty_token_file_is_hfarg005(tmp_path: Path):
    path = tmp_path / "hf-token"
    path.write_bytes(b"")

    assert codes_for(hub=optional_hub(), token_file=path, environ={}) == ["HFARG005"]


def test_newline_only_token_file_is_hfarg005(tmp_path: Path):
    assert codes_for(
        hub=optional_hub(), token_file=write_token(tmp_path, body="\n"), environ={}
    ) == ["HFARG005"]


def test_oversized_token_file_is_hfarg005(tmp_path: Path):
    path = write_token(tmp_path, body="x" * (MAXIMUM_TOKEN_FILE_BYTES + 1))

    assert codes_for(hub=optional_hub(), token_file=path, environ={}) == ["HFARG005"]


def test_non_utf8_token_file_is_hfarg005(tmp_path: Path):
    path = tmp_path / "hf-token"
    path.write_bytes(b"\xff\xfe not utf-8")

    assert codes_for(hub=optional_hub(), token_file=path, environ={}) == ["HFARG005"]


@pytest.mark.parametrize(
    "body",
    [
        "hf_two_newlines\n\n",
        "hf_carriage_return\r\n",
        "hf_internal space\n",
        "hf_tab\t\n",
        " hf_leading_space\n",
        "hf_non_ascii_é\n",
    ],
    ids=["two-newlines", "crlf", "internal-space", "tab", "leading-space", "non-ascii"],
)
def test_malformed_token_body_is_hfarg005(tmp_path: Path, body: str):
    # A token becomes an Authorization header; whitespace in one is never
    # forwarded, it is reported.
    assert codes_for(
        hub=optional_hub(), token_file=write_token(tmp_path, body=body), environ={}
    ) == ["HFARG005"]


@pytest.mark.skipif(os.geteuid() == 0, reason="root bypasses the permission check")
def test_unreadable_token_file_is_hfarg005(tmp_path: Path):
    path = write_token(tmp_path)
    path.chmod(0o000)

    assert codes_for(hub=optional_hub(), token_file=path, environ={}) == ["HFARG005"]


def test_token_file_that_cannot_be_stat_ed_is_hfarg005(tmp_path: Path):
    # A symlink loop fails at stat() rather than at read(), which is the other
    # side of the "unreadable" branch the permission test exercises.
    path = tmp_path / "loop"
    path.symlink_to(path)

    assert codes_for(hub=optional_hub(), token_file=path, environ={}) == ["HFARG005"]


# --------------------------------------------------------------------------- #
# HFARG006 — a systemd credential that is present but unusable
# --------------------------------------------------------------------------- #


def test_empty_systemd_credential_is_hfarg006(tmp_path: Path):
    (tmp_path / "hf-token").write_bytes(b"")

    assert codes_for(
        hub=optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    ) == ["HFARG006"]


def test_dangling_credential_symlink_is_hfarg006(tmp_path: Path):
    # The name exists, so the credential was installed and then broke. Failing
    # loudly beats running anonymously and reporting success.
    (tmp_path / "hf-token").symlink_to(tmp_path / "absent")

    assert codes_for(
        hub=optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    ) == ["HFARG006"]


def test_credential_that_is_a_directory_is_hfarg006(tmp_path: Path):
    (tmp_path / "hf-token").mkdir()

    assert codes_for(
        hub=optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    ) == ["HFARG006"]


def test_malformed_systemd_credential_is_hfarg006(tmp_path: Path):
    write_token(tmp_path, body="hf_with space\n")

    assert codes_for(
        hub=optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: str(tmp_path)}
    ) == ["HFARG006"]


def test_relative_credentials_directory_is_hfarg006():
    assert codes_for(hub=optional_hub(), environ={CREDENTIALS_DIRECTORY_VARIABLE: "run/creds"}) == [
        "HFARG006"
    ]


def test_credential_name_cannot_be_a_directory_entry():
    # Rejected at configuration time (HFCFG013) so it never reaches resolution.
    mapping = {
        "schema_version": 1,
        "hub": {"credential_name": ".."},
        "storage": {
            "archive_root": "/srv/hfcache",
            "archive_id": "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
        },
    }
    with pytest.raises(ConfigurationError) as raised:
        validate_config_mapping(mapping)

    assert [problem.code for problem in raised.value.problems] == ["HFCFG013"]


# --------------------------------------------------------------------------- #
# Every failure exits 10, before any Hub request
# --------------------------------------------------------------------------- #


def test_credential_failures_exit_ten(tmp_path: Path):
    with pytest.raises(ConfigurationError) as raised:
        resolve_token(optional_hub(), token_file=tmp_path / "absent", environ={})

    assert raised.value.exit_code == ExitCode.CONFIGURATION


# --------------------------------------------------------------------------- #
# Hub calls never see token=None (T-07)
# --------------------------------------------------------------------------- #


def test_absent_token_passes_false_not_none():
    argument = resolve_token(optional_hub(), environ={}).hub_argument

    # `is False`, not falsy: None would re-enable implicit discovery.
    assert argument is False


def test_present_token_passes_the_exact_string(tmp_path: Path):
    resolved = resolve_token(optional_hub(), token_file=write_token(tmp_path), environ={})

    assert resolved.hub_argument == SECRET


def test_no_token_constant_is_anonymous():
    assert NO_TOKEN.hub_argument is False
    assert NO_TOKEN.describe() == "no token; Hub calls pass token=False"


def test_source_and_secret_must_agree():
    with pytest.raises(ValueError, match="inconsistent"):
        ResolvedToken(source=TokenSource.NONE, secret=SECRET)

    with pytest.raises(ValueError, match="inconsistent"):
        ResolvedToken(source=TokenSource.TOKEN_FILE, secret=None)


def test_restricted_scope_requires_a_secret():
    with pytest.raises(ValueError, match="restricted repository scope"):
        ResolvedToken(
            source=TokenSource.NONE,
            repository_scope=RepositoryScope.RESTRICTED,
        )


# --------------------------------------------------------------------------- #
# Ambient discovery is disabled (T-07)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variable", sorted(AMBIENT_TOKEN_VARIABLES))
def test_ambient_variables_do_not_supply_a_token(variable: str):
    resolved = resolve_token(optional_hub(), environ={variable: SECRET})

    assert resolved.source is TokenSource.NONE
    assert resolved.hub_argument is False


def test_ambient_variables_are_reported_for_doctor():
    present = ambient_token_variables({"HF_TOKEN": SECRET, "PATH": "/usr/bin"})

    assert present == ("HF_TOKEN",)


def test_empty_ambient_variable_is_not_reported():
    assert ambient_token_variables({"HF_TOKEN": ""}) == ()


def test_ambient_report_reads_the_process_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HF_TOKEN", SECRET)

    assert "HF_TOKEN" in ambient_token_variables()


# --------------------------------------------------------------------------- #
# A secret cannot escape through any rendering path
# --------------------------------------------------------------------------- #


@given(secret=token_strategy)
def test_repr_and_description_never_contain_the_secret(
    secret: str, tmp_path_factory: pytest.TempPathFactory
):
    directory = tmp_path_factory.mktemp("creds")
    resolved = resolve_token(
        optional_hub(), token_file=write_token(directory, body=secret + "\n"), environ={}
    )

    assert resolved.secret == secret
    for rendering in (repr(resolved), str(resolved), f"{resolved}", resolved.describe()):
        assert secret not in rendering
    assert resolved.source.value in repr(resolved)


@given(secret=token_strategy)
def test_error_messages_never_contain_the_secret(
    secret: str, tmp_path_factory: pytest.TempPathFactory
):
    # The file is well-formed except for an appended space, so the secret itself
    # is what the rejected content is made of.
    directory = tmp_path_factory.mktemp("creds")
    path = write_token(directory, body=secret + " \n")

    with pytest.raises(ConfigurationError) as raised:
        resolve_token(optional_hub(), token_file=path, environ={})

    problem = raised.value.problems[0]
    assert secret not in problem.message
    assert secret not in problem.as_line()
    assert secret not in str(raised.value)
    assert problem.location == str(path)
