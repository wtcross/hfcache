"""The error taxonomy, aggregation, and the `--json` envelope contract.

The first section reads the published tables out of `docs/cli.md` §5 and
`docs/configuration.md` §8 and checks the implementation against them, in both
directions. That is the test that stops the taxonomy drifting: a code added to
the documentation with no family, or a family here that the documentation never
mentions, fails without anyone having to notice.
"""

import re
from pathlib import Path

import pytest

from hfcache.errors import ExitCode
from hfcache.reporting import ENVELOPE_SCHEMA_VERSION, Envelope, EnvelopeProblem
from hfcache.taxonomy import (
    AGGREGATION_ORDER,
    PREFIX_EXIT_CODES,
    WARNING_PREFIXES,
    aggregate_exit_code,
    classify,
    is_warning,
)

DOCS = Path(__file__).parent.parent.parent / "docs"

CODE = re.compile(r"HF[A-Z]{3}\d{3}")
SECTION = re.compile(r"^### 5\.\d+ (?P<title>.+?)(?: — exit `(?P<exit>\d+)`)?$", re.MULTILINE)
# Only the leading cell of a table row. The prose around a table cross-references
# codes from other sections — §5.3 explains how `HFSYN003` relates to `HFVER002`
# — and those mentions are not claims about which section a code belongs to.
TABLE_ROW = re.compile(r"^\| `(HF[A-Z]{3}\d{3})` \|", re.MULTILINE)

RUN_ID = "4c1e8a55b0d24f1e9a3c7d2b6f80e114"
STARTED = "2026-07-24T20:38:11.500000Z"
COMPLETED = "2026-07-24T20:41:46.002000Z"


def documented_sections() -> dict[str, list[str]]:
    """Map each `docs/cli.md` §5 subsection title to the codes it lists."""
    text = (DOCS / "cli.md").read_text(encoding="utf-8")
    matches = list(SECTION.finditer(text))
    sections: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        key = match.group("exit") or "warning"
        sections.setdefault(key, []).extend(TABLE_ROW.findall(body))
    return sections


def documented_codes() -> set[str]:
    """Every code named anywhere in the two normative documents."""
    codes: set[str] = set()
    for name in ("cli.md", "configuration.md"):
        codes |= set(CODE.findall((DOCS / name).read_text(encoding="utf-8")))
    return codes


# --------------------------------------------------------------------------- #
# The taxonomy matches the documents that define it
# --------------------------------------------------------------------------- #


def test_the_documents_really_were_parsed():
    sections = documented_sections()

    assert set(sections) == {"10", "20", "30", "40", "50", "warning"}
    assert len(documented_codes()) > 60


@pytest.mark.parametrize(
    ("exit_value", "expected"),
    [
        ("10", ExitCode.CONFIGURATION),
        ("20", ExitCode.SAFETY),
        ("30", ExitCode.SYNC),
        ("40", ExitCode.INTEGRITY),
        ("50", ExitCode.RETENTION),
    ],
)
def test_every_documented_code_classifies_as_its_section_says(exit_value, expected):
    codes = documented_sections()[exit_value]

    assert codes, f"section for exit {exit_value} listed no codes"
    for code in codes:
        assert classify(code) == expected, code


def test_every_documented_warning_classifies_as_success():
    # `docs/cli.md` §5.6: a warning never changes a `0` exit on its own.
    for code in documented_sections()["warning"]:
        assert is_warning(code), code
        assert classify(code) == ExitCode.SUCCESS, code


def test_every_documented_code_has_a_family():
    for code in documented_codes():
        classify(code)


def test_every_implemented_family_appears_in_the_documents():
    # The other direction: a family here that no document mentions is either a
    # typo or a code invented without being written down.
    documented = {code[:5] for code in documented_codes()}

    assert set(PREFIX_EXIT_CODES) | WARNING_PREFIXES <= documented


def test_the_configuration_codes_are_numbered_without_gaps():
    # `docs/configuration.md` §8 promises HFCFG001-HFCFG016.
    numbers = sorted(int(code[5:]) for code in documented_codes() if code.startswith("HFCFG"))

    assert numbers == list(range(1, 17))


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("HFCFG001", ExitCode.CONFIGURATION),
        ("HFARG004", ExitCode.CONFIGURATION),
        ("HFMNT011", ExitCode.SAFETY),
        ("HFTXN004", ExitCode.SAFETY),
        ("HFHUB007", ExitCode.SYNC),
        ("HFSYN004", ExitCode.SYNC),
        ("HFVER001", ExitCode.INTEGRITY),
        ("HFRET006", ExitCode.RETENTION),
        ("HFWRN003", ExitCode.SUCCESS),
        ("HFDEP001", ExitCode.SUCCESS),
    ],
)
def test_classification(code, expected):
    assert classify(code) == expected


@pytest.mark.parametrize(
    "code", ["", "HFVER", "HFVER0001", "hfver001", "HFVERXXX", "HF001", "HFXXX001"]
)
def test_a_value_that_is_not_a_code_is_refused(code):
    with pytest.raises(ValueError, match=r"taxonomy code|no known family"):
        classify(code)


def test_a_well_formed_code_from_an_unknown_family_is_refused():
    # Shaped like a code but belonging to nothing. Guessing a classification
    # would put an arbitrary number in front of a scheduler.
    with pytest.raises(ValueError, match="no known family"):
        classify("HFZZZ001")


# --------------------------------------------------------------------------- #
# Aggregation (`docs/cli.md` §3)
# --------------------------------------------------------------------------- #


def test_no_codes_is_success():
    assert aggregate_exit_code([]) == ExitCode.SUCCESS


def test_warnings_alone_leave_the_exit_at_zero():
    assert aggregate_exit_code(["HFDEP001", "HFWRN004", "HFWRN007"]) == ExitCode.SUCCESS


def test_integrity_outranks_retention_and_sync():
    # Possible data corruption is what an operator should look at first.
    assert aggregate_exit_code(["HFSYN001", "HFRET003", "HFVER001"]) == ExitCode.INTEGRITY


def test_retention_outranks_sync():
    assert aggregate_exit_code(["HFSYN001", "HFRET003"]) == ExitCode.RETENTION


def test_aggregation_does_not_depend_on_order():
    codes = ["HFVER001", "HFRET003", "HFSYN001", "HFDEP001"]

    assert aggregate_exit_code(codes) == aggregate_exit_code(reversed(codes))


@pytest.mark.parametrize("aborting", ["HFCFG001", "HFMNT002"])
def test_an_aborting_classification_wins_outright(aborting):
    # Exits 10 and 20 abort before per-repository work, so a run holding one
    # describes work that did not happen rather than work that partly did.
    assert aggregate_exit_code([aborting, "HFVER001"]) == classify(aborting)


def test_configuration_outranks_safety():
    assert aggregate_exit_code(["HFMNT002", "HFCFG001"]) == ExitCode.CONFIGURATION


def test_the_documented_order_is_the_implemented_one():
    assert AGGREGATION_ORDER == (ExitCode.INTEGRITY, ExitCode.RETENTION, ExitCode.SYNC)


def test_a_run_that_continued_past_a_failure_still_exits_non_zero():
    # `docs/plan.md` §11.2: systemd must record the unit as failed.
    assert aggregate_exit_code(["HFHUB004"]) != ExitCode.SUCCESS


# --------------------------------------------------------------------------- #
# The envelope (`docs/cli.md` §4)
# --------------------------------------------------------------------------- #


def envelope(  # noqa: PLR0913 - one keyword per envelope field under test
    *,
    command: str = "sync",
    exit_code: int = 0,
    outcome: str = "success",
    schema_version: int = ENVELOPE_SCHEMA_VERSION,
    errors: tuple[EnvelopeProblem, ...] = (),
    warnings: tuple[EnvelopeProblem, ...] = (),
) -> Envelope:
    """A valid envelope, with one field at a time replaced by the case under test."""
    return Envelope(
        command=command,
        completed_at=COMPLETED,
        data={},
        errors=errors,
        exit_code=exit_code,
        outcome=outcome,  # pyrefly: ignore[bad-argument-type]
        run_id=RUN_ID,
        schema_version=schema_version,
        started_at=STARTED,
        warnings=warnings,
    )


def test_the_envelope_has_exactly_the_documented_fields():
    assert set(envelope().to_payload()) == {
        "command",
        "completed_at",
        "data",
        "errors",
        "exit_code",
        "outcome",
        "run_id",
        "schema_version",
        "started_at",
        "warnings",
    }


def test_the_envelope_is_versioned_independently_of_the_durable_schemas():
    # `docs/cli.md` §4. An invocation record and an archived manifest change for
    # different reasons; tying their versions together would force a bump on
    # consumers of one because the other moved.
    assert envelope().schema_version == ENVELOPE_SCHEMA_VERSION


def test_the_envelope_is_one_line_with_sorted_keys():
    text = envelope().to_json(indent=None)

    assert text.count("\n") == 1
    assert text.startswith('{"command": "sync",')


def test_a_problem_entry_has_the_documented_shape():
    entry = EnvelopeProblem(
        code="HFCFG010", context={"location": "hub.token"}, message="looks like a secret"
    )

    assert set(entry.to_payload()) == {"code", "context", "message", "repository"}
    assert entry.repository is None


@pytest.mark.parametrize("exit_code", [0, 10, 20, 30, 40, 50])
def test_every_documented_exit_code_is_accepted(exit_code):
    outcome = "success" if exit_code == 0 else "failed"
    errors = () if exit_code == 0 else (EnvelopeProblem(code="HFCFG001", message="x"),)

    assert envelope(exit_code=exit_code, outcome=outcome, errors=errors).exit_code == exit_code


def test_an_undocumented_exit_code_is_refused():
    with pytest.raises(ValueError, match="not a documented classification"):
        envelope(exit_code=1, outcome="failed", errors=(EnvelopeProblem(code="X", message="y"),))


def test_an_outcome_that_contradicts_its_exit_code_is_refused():
    with pytest.raises(ValueError, match="contradicts exit_code"):
        envelope(exit_code=30)


def test_a_failed_envelope_carries_its_errors():
    with pytest.raises(ValueError, match="carries the errors"):
        envelope(exit_code=30, outcome="failed")


def test_success_with_warnings_requires_warnings():
    with pytest.raises(ValueError, match="exactly when warnings"):
        envelope(outcome="success_with_warnings")


def test_success_cannot_hide_warnings():
    with pytest.raises(ValueError, match="exactly when warnings"):
        envelope(warnings=(EnvelopeProblem(code="HFDEP001", message="dependency"),))


def test_a_failed_envelope_preserves_warnings_alongside_errors():
    result = envelope(
        exit_code=30,
        outcome="failed",
        errors=(EnvelopeProblem(code="HFHUB004", message="Hub failure"),),
        warnings=(EnvelopeProblem(code="HFDEP001", message="undeclared dependency"),),
    )

    assert result.errors[0].code == "HFHUB004"
    assert result.warnings[0].code == "HFDEP001"


def test_warnings_do_not_make_an_envelope_fail():
    result = envelope(
        outcome="success_with_warnings",
        warnings=(EnvelopeProblem(code="HFDEP001", message="undeclared dependency"),),
    )

    assert result.exit_code == ExitCode.SUCCESS


def test_an_unknown_envelope_version_is_refused():
    with pytest.raises(ValueError, match="schema_version"):
        envelope(schema_version=2)


def test_an_envelope_is_frozen():
    with pytest.raises(ValueError, match="frozen"):
        # pyrefly: ignore[read-only]
        envelope().command = "something else"
