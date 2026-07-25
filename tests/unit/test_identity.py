"""Repository identity and identifier grammars (`docs/architecture.md` §5.3).

Two things are proven here beyond the obvious accept/reject cases: that no
grammar accepts a trailing newline, and that a `RepositoryIdentity` cannot be
constructed around a segment that would be unsafe as a path component.
"""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hfcache import identity
from hfcache.config import RepositoryConfig
from hfcache.errors import CodedError, ConfigurationError, ExitCode
from hfcache.identity import (
    COMMIT_SHA_LENGTH,
    OPAQUE_ID_LENGTH,
    PROBE_ID_LENGTH,
    REPOSITORY_TYPES,
    RepositoryIdentity,
    RepositorySelector,
    new_probe_id,
    new_publication_id,
    new_run_id,
    new_transaction_id,
    parse_commit_sha,
    parse_probe_id,
    parse_publication_id,
    parse_repository_id,
    parse_repository_type,
    parse_revision,
    parse_run_id,
    parse_selector,
    parse_transaction_id,
)

FULL_SHA = "0123456789abcdef0123456789abcdef01234567"
OPAQUE = "9f14c0b7a2d4423fa0e6b1c8d95e3f27"
PROBE = "0123456789abcdef"


def code_of(call) -> str:
    with pytest.raises(CodedError) as raised:
        call()
    return raised.value.code


# --------------------------------------------------------------------------- #
# The trailing-newline hole
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("parser", "value"),
    [
        (parse_repository_id, "organization/model-name\n"),
        (parse_revision, "main\n"),
        (parse_revision, f"{FULL_SHA}\n"),
        (parse_commit_sha, f"{FULL_SHA}\n"),
        (parse_publication_id, f"{OPAQUE}\n"),
        (parse_transaction_id, f"{OPAQUE}\n"),
        (parse_run_id, f"{OPAQUE}\n"),
        (parse_probe_id, f"{PROBE}\n"),
    ],
)
def test_no_grammar_accepts_a_trailing_newline(parser, value):
    # An anchored `match` would accept every one of these, because `$` matches
    # before a trailing newline. The value would then be written into a path.
    with pytest.raises(CodedError):
        parser(value)


def test_the_grammars_are_applied_with_fullmatch():
    # A structural guard: an anchored pattern would reintroduce the hole above
    # for whichever grammar is written that way next.
    patterns = {
        name: value for name, value in vars(identity).items() if isinstance(value, re.Pattern)
    }

    assert patterns, "no compiled patterns found; this guard has stopped guarding anything"
    for name, pattern in patterns.items():
        assert not pattern.pattern.startswith("^"), f"{name} is anchored; use fullmatch"
        assert not pattern.pattern.endswith("$"), f"{name} is anchored; use fullmatch"


# --------------------------------------------------------------------------- #
# Repository identifiers
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "identifier",
    [
        "organization/model-name",
        "openai-community/gpt2",
        "google-bert/bert-base-uncased",
        "a/b",
        "Org.With.Dots/repo_with_underscores",
        f"{'n' * 96}/{'r' * 96}",
    ],
)
def test_valid_repository_identifiers_are_accepted(identifier):
    assert parse_repository_id(identifier) == identifier


@pytest.mark.parametrize(
    "identifier",
    [
        "gpt2",
        "a/b/c",
        "",
        "/repo",
        "org/",
        "org//repo",
        "../repo",
        "org/..",
        "org/.",
        ".hidden/repo",
        "-leading/repo",
        "org/repo name",
        "org/repo\tname",
        f"{'n' * 97}/repo",
        # U+202E RIGHT-TO-LEFT OVERRIDE, written as an escape so the source file
        # itself does not contain a bidirectional control character.
        "org/\u202eevil",
    ],
)
def test_invalid_repository_identifiers_are_hfcfg008(identifier):
    assert code_of(lambda: parse_repository_id(identifier)) == "HFCFG008"


def test_a_non_string_repository_id_is_hfcfg008():
    assert code_of(lambda: parse_repository_id(42)) == "HFCFG008"


@pytest.mark.parametrize("repository_type", REPOSITORY_TYPES)
def test_both_repository_types_are_accepted(repository_type):
    assert parse_repository_type(repository_type) == repository_type


@pytest.mark.parametrize("value", ["models", "Model", "space", "", None])
def test_an_unsupported_repository_type_is_hfcfg005(value):
    assert code_of(lambda: parse_repository_type(value)) == "HFCFG005"


# --------------------------------------------------------------------------- #
# Revisions
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("value", ["main", "v1.0", "refs/pr/3", FULL_SHA, "release-2026.07"])
def test_valid_revisions_are_accepted(value):
    assert parse_revision(value) == value


@pytest.mark.parametrize(
    "value",
    [
        FULL_SHA.upper(),
        "0123456",
        "",
        "/main",
        "main/",
        "-main",
        "a//b",
        "a/../b",
        "main.lock",
        "main branch",
        "x" * 256,
    ],
)
def test_invalid_revisions_are_hfcfg009(value):
    assert code_of(lambda: parse_revision(value)) == "HFCFG009"


def test_a_miscased_sha_is_rejected_with_the_lowercase_form_offered():
    with pytest.raises(CodedError) as raised:
        parse_revision(FULL_SHA.upper())

    assert FULL_SHA in str(raised.value)


def test_an_abbreviated_sha_says_so():
    with pytest.raises(CodedError) as raised:
        parse_revision("0123456789abcdef")

    assert "abbreviated" in str(raised.value)


def test_a_non_string_revision_is_hfcfg009():
    assert code_of(lambda: parse_revision(None)) == "HFCFG009"


# --------------------------------------------------------------------------- #
# Opaque identifiers
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("parser", "length"),
    [
        (parse_commit_sha, COMMIT_SHA_LENGTH),
        (parse_publication_id, OPAQUE_ID_LENGTH),
        (parse_transaction_id, OPAQUE_ID_LENGTH),
        (parse_run_id, OPAQUE_ID_LENGTH),
        (parse_probe_id, PROBE_ID_LENGTH),
    ],
)
def test_opaque_identifier_grammars(parser, length):
    good = "a" * length
    assert parser(good) == good

    for bad in ("a" * (length - 1), "a" * (length + 1), ("A" * length), "g" * length, "", 7):
        with pytest.raises(CodedError):
            parser(bad)


def test_an_identifier_parser_reports_the_caller_s_code():
    assert code_of(lambda: parse_commit_sha("nope", code="HFVER007")) == "HFVER007"


@pytest.mark.parametrize(
    ("mint", "parser"),
    [
        (new_publication_id, parse_publication_id),
        (new_transaction_id, parse_transaction_id),
        (new_run_id, parse_run_id),
        (new_probe_id, parse_probe_id),
    ],
)
def test_minted_identifiers_satisfy_their_own_grammar(mint, parser):
    minted = mint()

    assert parser(minted) == minted
    assert mint() != minted


# --------------------------------------------------------------------------- #
# RepositoryIdentity
# --------------------------------------------------------------------------- #


def test_identity_exposes_the_documented_forms():
    identity = RepositoryIdentity.of("model", "organization/model-name")

    assert identity.namespace == "organization"
    assert identity.name == "model-name"
    assert identity.id == "organization/model-name"
    assert identity.selector == "model:organization/model-name"
    assert identity.directory == "models"
    assert str(identity) == "model:organization/model-name"


def test_a_dataset_lives_under_the_plural_directory():
    assert RepositoryIdentity.of("dataset", "org/set").directory == "datasets"


def test_identity_is_built_from_a_configuration_entry():
    entry = RepositoryConfig(id="organization/model-name", type="dataset")

    assert RepositoryIdentity.from_config(entry) == RepositoryIdentity.of(
        "dataset", "organization/model-name"
    )
    assert entry.identity.directory == "datasets"


@pytest.mark.parametrize(
    ("namespace", "name"),
    [("..", "repo"), ("org", ".."), ("org", "."), ("org", "a/b"), ("", "repo"), ("org", "")],
)
def test_the_generated_constructor_cannot_smuggle_an_unsafe_segment(namespace, name):
    # The type is meant to be proof that a name is safe to build a path from.
    # Validation therefore lives in __post_init__, not only in `of`.
    with pytest.raises(CodedError):
        RepositoryIdentity(type="model", namespace=namespace, name=name)


def test_the_generated_constructor_validates_the_type():
    with pytest.raises(CodedError):
        # pyrefly: ignore[bad-argument-type]
        # The type checker rejects this too, which is half the guarantee; the
        # other half is that it fails at run time for a caller that is not
        # type-checked.
        RepositoryIdentity(type="models", namespace="org", name="repo")


def test_identity_is_hashable_and_compares_by_value():
    first = RepositoryIdentity.of("model", "org/repo")
    second = RepositoryIdentity.of("model", "org/repo")

    assert first == second
    assert len({first, second}) == 1
    assert first != RepositoryIdentity.of("dataset", "org/repo")


def test_sort_key_orders_byte_wise_on_the_identifier():
    # `-` (0x2d) sorts before `/` (0x2f), so byte-wise ordering on the whole
    # identifier puts `a-b/x` first. Comparing (namespace, name) tuples would
    # invert this pair, which is why sort_key exists instead of order=True.
    hyphen = RepositoryIdentity.of("model", "a-b/x")
    slash = RepositoryIdentity.of("model", "a/b-x")

    assert sorted([slash, hyphen], key=lambda item: item.sort_key) == [hyphen, slash]
    assert [item.id for item in sorted([slash, hyphen], key=lambda item: item.sort_key)] == sorted(
        ["a/b-x", "a-b/x"]
    )


def test_datasets_sort_before_models():
    dataset = RepositoryIdentity.of("dataset", "z/z")
    model = RepositoryIdentity.of("model", "a/a")

    assert sorted([model, dataset], key=lambda item: item.sort_key) == [dataset, model]


# --------------------------------------------------------------------------- #
# Selectors (`docs/cli.md` §1.1)
# --------------------------------------------------------------------------- #


def test_a_bare_selector_parses():
    selector = parse_selector("model:organization/model-name")

    assert selector.identity == RepositoryIdentity.of("model", "organization/model-name")
    assert selector.commit_sha is None
    assert str(selector) == "model:organization/model-name"


def test_a_pinned_selector_parses():
    selector = parse_selector(f"dataset:organization/set@{FULL_SHA}")

    assert selector.identity.type == "dataset"
    assert selector.commit_sha == FULL_SHA
    assert str(selector) == f"dataset:organization/set@{FULL_SHA}"


def test_selector_sort_key_is_total():
    bare = parse_selector("model:org/repo")
    pinned = parse_selector(f"model:org/repo@{FULL_SHA}")

    assert sorted([pinned, bare], key=lambda item: item.sort_key) == [bare, pinned]


@pytest.mark.parametrize(
    "value",
    [
        "model/organization/model-name",
        "organization/model-name",
        "",
        "model:",
        "model:gpt2",
        "model:a/b/c",
        ":org/repo",
        "models:org/repo",
        "model:org/repo@",
        "model:org/repo@0123456",
        f"model:org/repo@{FULL_SHA.upper()}",
        f"model:org/repo@{FULL_SHA}@extra",
        "model:org/repo:extra",
    ],
)
def test_every_malformed_selector_is_hfarg001(value):
    with pytest.raises(ConfigurationError) as raised:
        parse_selector(value)

    assert [problem.code for problem in raised.value.problems] == ["HFARG001"]
    assert raised.value.exit_code == ExitCode.CONFIGURATION


def test_an_abbreviated_selector_sha_says_so():
    with pytest.raises(ConfigurationError) as raised:
        parse_selector("model:org/repo@0123456789abcdef")

    assert "abbreviated" in raised.value.problems[0].message


def test_a_rejected_selector_names_itself_so_one_of_several_can_be_found():
    with pytest.raises(ConfigurationError) as raised:
        parse_selector("model:gpt2")

    assert raised.value.problems[0].location == "model:gpt2"


# --------------------------------------------------------------------------- #
# Round trips
# --------------------------------------------------------------------------- #

segment_strategy = st.from_regex(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,20}\Z")


@given(
    repository_type=st.sampled_from(REPOSITORY_TYPES),
    namespace=segment_strategy,
    name=segment_strategy,
)
def test_any_valid_identity_round_trips_through_its_selector(repository_type, namespace, name):
    identity = RepositoryIdentity.of(repository_type, f"{namespace}/{name}")

    assert parse_selector(identity.selector) == RepositorySelector(identity=identity)


@given(sha=st.from_regex(r"\A[0-9a-f]{40}\Z"))
def test_any_valid_pinned_selector_round_trips(sha):
    selector = parse_selector(f"model:org/repo@{sha}")

    assert parse_selector(str(selector)) == selector
