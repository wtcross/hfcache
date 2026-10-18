"""Static dependency detection — docs/architecture.md AD-07, `AD-07`, `AD-15`.

Two properties get the most attention, and both are safety properties rather
than feature ones.

**Nothing is executed.** The tests feed the detector metadata that would run
code under any loader that imported it — a YAML tag naming a Python callable, a
model card whose front matter is not YAML at all — and assert that the result is
an observation rather than an effect.

**A warning never becomes an action.** An undeclared dependency produces a code,
a manifest entry, and a `completed_with_warnings` status, and leaves the exit
code at `0`. It never downloads, never reorders retention, and never fails the
repository.
"""

import json
from typing import TYPE_CHECKING

import pytest

from hfcache.dependencies import (
    ADAPTER_CONFIG,
    MODEL_CARD,
    detect_dependencies,
    undeclared,
    undeclared_warnings,
)

if TYPE_CHECKING:
    from pathlib import Path

BASE = "meta-llama/Llama-3.1-8B"


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    path = tmp_path / "tree"
    path.mkdir()
    return path


def card(tree: Path, front_matter: str) -> None:
    (tree / MODEL_CARD).write_text(f"---\n{front_matter}\n---\n\n# A model\n", encoding="utf-8")


def adapter(tree: Path, payload: object) -> None:
    (tree / ADAPTER_CONFIG).write_text(json.dumps(payload), encoding="utf-8")


def ids(observations) -> list[str]:
    return [observation.detected_id for observation in observations]


# --------------------------------------------------------------------------- #
# Model-card metadata
# --------------------------------------------------------------------------- #


def test_a_base_model_in_the_card_is_detected(tree):
    card(tree, f"base_model: {BASE}\nlicense: llama3.1")

    observations = detect_dependencies(tree)

    assert ids(observations) == [BASE]
    assert observations[0].source_file == MODEL_CARD
    assert observations[0].source_field == "base_model"
    assert observations[0].confidence == "medium"


def test_a_merged_model_naming_several_parents_reports_each(tree):
    card(tree, "base_model:\n  - org/first\n  - org/second")

    assert ids(detect_dependencies(tree)) == ["org/first", "org/second"]


def test_a_card_with_no_front_matter_reports_nothing(tree):
    (tree / MODEL_CARD).write_text("# Just a readme\n", encoding="utf-8")

    assert detect_dependencies(tree) == ()


def test_a_repository_with_no_card_reports_nothing(tree):
    assert detect_dependencies(tree) == ()


def test_a_card_with_no_base_model_reports_nothing(tree):
    card(tree, "license: apache-2.0\ntags:\n  - text-generation")

    assert detect_dependencies(tree) == ()


def test_unparseable_front_matter_is_reported_not_guessed_at(tree):
    # §17: unparseable or ambiguous metadata is reported without executing code.
    card(tree, "base_model: [unclosed\n  : : :")

    observations = detect_dependencies(tree)

    assert ids(observations) == ["(unparseable)"]
    assert observations[0].confidence == "low"


def test_a_yaml_tag_naming_a_callable_is_not_constructed(tree):
    # `safe_load` refuses the tag rather than resolving it (`AD-15`, T-04). What
    # comes back is a finding; what does not happen is a call.
    card(tree, "base_model: !!python/object/apply:os.system ['true']")

    observations = detect_dependencies(tree)

    assert ids(observations) == ["(unparseable)"]


def test_a_base_model_that_is_not_an_identifier_is_low_confidence(tree):
    card(tree, "base_model: not a repository id at all")

    observations = detect_dependencies(tree)

    assert observations[0].confidence == "low"
    assert observations[0].detected_id == "not a repository id at all"


def test_front_matter_that_is_not_a_mapping_reports_nothing(tree):
    card(tree, "- just\n- a\n- list")

    # The library raises for a non-mapping block, which is one finding.
    assert ids(detect_dependencies(tree)) == ["(unparseable)"]


# --------------------------------------------------------------------------- #
# Adapter configuration
# --------------------------------------------------------------------------- #


def test_an_adapter_base_model_is_high_confidence(tree):
    # An adapter without its base cannot be loaded at all, which is a stronger
    # claim than a card's `base_model`.
    adapter(tree, {"base_model_name_or_path": BASE, "peft_type": "LORA"})

    observations = detect_dependencies(tree)

    assert ids(observations) == [BASE]
    assert observations[0].confidence == "high"
    assert observations[0].source_file == ADAPTER_CONFIG


def test_an_adapter_config_that_is_not_json_is_reported(tree):
    (tree / ADAPTER_CONFIG).write_text("{ not json", encoding="utf-8")

    observations = detect_dependencies(tree)

    assert ids(observations) == ["(unparseable)"]
    assert observations[0].confidence == "low"


def test_an_adapter_config_that_is_not_an_object_is_reported(tree):
    adapter(tree, ["a", "list"])

    assert ids(detect_dependencies(tree)) == ["(unparseable)"]


def test_an_adapter_config_without_a_base_reports_nothing(tree):
    adapter(tree, {"peft_type": "LORA"})

    assert detect_dependencies(tree) == ()


def test_both_sources_are_read_and_sorted(tree):
    card(tree, f"base_model: {BASE}")
    adapter(tree, {"base_model_name_or_path": "org/other"})

    observations = detect_dependencies(tree)

    # Sorted by `(source_file, source_field, detected_id)`, so two runs over one
    # revision produce the same manifest bytes.
    assert [o.source_file for o in observations] == [MODEL_CARD, ADAPTER_CONFIG]


# --------------------------------------------------------------------------- #
# Declared and managed
# --------------------------------------------------------------------------- #


def test_a_declared_dependency_is_marked_declared(tree):
    card(tree, f"base_model: {BASE}")

    observations = detect_dependencies(tree, declared=[BASE])

    assert observations[0].declared is True
    assert undeclared_warnings(observations) == []


def test_a_declaration_differing_only_in_case_still_counts(tree):
    # The Hub treats them as one repository and the declaration is typed by
    # hand; reporting it undeclared would train an operator to ignore the code.
    card(tree, f"base_model: {BASE}")

    observations = detect_dependencies(tree, declared=[BASE.upper()])

    assert observations[0].declared is True


def test_an_undeclared_dependency_produces_hfdep001(tree):
    card(tree, f"base_model: {BASE}")

    observations = detect_dependencies(tree)

    assert observations[0].declared is False
    assert undeclared_warnings(observations) == ["HFDEP001"]
    assert ids(undeclared(observations)) == [BASE]


def test_four_undeclared_dependencies_are_one_problem(tree):
    # `HFDEP001` names the condition, not the instance.
    card(tree, "base_model:\n  - org/a\n  - org/b\n  - org/c\n  - org/d")

    assert undeclared_warnings(detect_dependencies(tree)) == ["HFDEP001"]


def test_declared_and_managed_are_separate_questions(tree):
    # Declared but unmanaged: the operator knows and has decided not to archive
    # it. Managed but undeclared: it is archived and the declaration is stale.
    card(tree, f"base_model: {BASE}")

    declared_only = detect_dependencies(tree, declared=[BASE])
    managed_only = detect_dependencies(tree, managed=[BASE])

    assert (declared_only[0].declared, declared_only[0].managed) == (True, False)
    assert (managed_only[0].declared, managed_only[0].managed) == (False, True)


def test_an_unrelated_declaration_does_not_satisfy_the_warning(tree):
    card(tree, f"base_model: {BASE}")

    observations = detect_dependencies(tree, declared=["org/something-else"])

    assert undeclared_warnings(observations) == ["HFDEP001"]
