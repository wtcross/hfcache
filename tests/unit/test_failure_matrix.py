"""Plan §26.6's failure-injection matrix, and what covers each of its points.

§26.6 lists eleven points at which failure must be injected, and one property
that has to hold at every one of them: *the previous current revision remains
usable and no retained verified revision is accidentally destroyed.*

The tests that establish that are spread across four modules, because each lives
beside the fixtures it needs — the crash injections next to the recovery they
exercise, the verification interruption next to the `verify` command. That is the
right place for them to run and the wrong place to read the matrix from, because
no single module holds the whole map.

So the map lives here, and it is executable. `MATRIX` names, for each of §26.6's
eleven points, the test functions that cover it; the test below resolves every
one of those names and fails if it has been renamed, moved, or deleted. A
coverage claim in a comment rots silently. This one cannot.

`OPS-005` is the audit that produced it.
"""

import importlib
from typing import Final

import pytest

# Exactly the modules named in `MATRIX` — asserted below, so the list can
# neither miss a module the matrix names nor keep one it no longer does.
MODULES: Final = (
    "tests.unit.test_crash_injection",
    "tests.unit.test_purge",
    "tests.unit.test_recovery_planning",
    "tests.unit.test_synchronize",
    "tests.unit.test_verify_command",
)

MATRIX: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    # 1
    "before download": (
        (
            "tests.unit.test_synchronize",
            "test_a_download_the_archive_has_no_room_for_is_refused_before_it_starts",
        ),
        ("tests.unit.test_synchronize", "test_the_sync_command_refuses_an_unmounted_archive"),
        (
            "tests.unit.test_synchronize",
            "test_a_journal_that_asked_for_an_operator_stops_the_run_before_the_hub",
        ),
    ),
    # 2 — no test kills a transfer mid-flight; what is asserted instead is that a
    # cache left partial publishes nothing and is detected rather than trusted.
    "mid-download": (
        ("tests.unit.test_synchronize", "test_a_snapshot_missing_a_listed_file_fails_completeness"),
        (
            "tests.unit.test_synchronize",
            "test_a_repository_that_fails_is_recorded_and_the_run_continues",
        ),
        (
            "tests.unit.test_recovery_planning",
            "test_a_publication_that_stopped_before_publishing_rolls_back",
        ),
    ),
    # 3
    "after download, before hash completion": (
        (
            "tests.unit.test_synchronize",
            "test_integrity_outranks_synchronization_in_the_reported_exit",
        ),
        ("tests.unit.test_synchronize", "test_a_snapshot_missing_a_listed_file_fails_completeness"),
    ),
    # 4 — the staged manifest is written at §7.3 step 4 and published at step 6;
    # crashing the second write is a crash during manifest creation.
    "during manifest creation": (
        (
            "tests.unit.test_crash_injection",
            "test_a_publication_interrupted_after_the_rename_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_staged_manifest_that_vanished_is_quarantined_not_published",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_tree_that_cannot_be_validated_is_quarantined_not_published",
        ),
    ),
    # 5
    "during staging publication": (
        (
            "tests.unit.test_synchronize",
            "test_a_failure_before_the_rename_leaves_no_staging_behind",
        ),
        (
            "tests.unit.test_synchronize",
            "test_a_failure_after_the_rename_keeps_its_staged_manifest",
        ),
        (
            "tests.unit.test_recovery_planning",
            "test_a_publication_that_stopped_before_publishing_rolls_back",
        ),
    ),
    # 6
    "after revision rename, before ref replacement": (
        (
            "tests.unit.test_crash_injection",
            "test_a_publication_interrupted_after_the_rename_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_publication_interrupted_before_the_reference_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_published_tree_that_does_not_match_its_manifest_is_never_referenced",
        ),
    ),
    # 7 — `revision_ref_published`, one of the two rows `OPS-005` found thin.
    "after ref replacement, before pruning": (
        (
            "tests.unit.test_crash_injection",
            "test_a_publication_interrupted_before_the_current_ref_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_publication_interrupted_before_the_catalog_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_an_older_revision_rolled_forward_does_not_become_current",
        ),
    ),
    # 8 — the §7.4 prune commit point, the other thin row.
    "during publication-tree removal": (
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_interrupted_before_its_commit_point_rolls_back",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_interrupted_at_its_commit_point_rolls_back",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_interrupted_after_its_commit_point_rolls_forward",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_interrupted_before_its_containers_are_removed_is_completed",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_that_crashed_before_the_tombstone_rolls_back_with_no_trash",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_prune_whose_audit_records_landed_only_needs_its_trash_removed",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_rollback_that_cannot_restore_the_tree_is_hfret005",
        ),
        (
            "tests.unit.test_purge",
            "test_recovery_rolls_an_interrupted_precommit_purge_back",
        ),
        (
            "tests.unit.test_purge",
            "test_recovery_finishes_an_interrupted_postcommit_purge",
        ),
    ),
    # 9
    "during hub cache cleanup": (
        ("tests.unit.test_synchronize", "test_a_cache_deletion_failure_is_hfret002"),
        (
            "tests.unit.test_synchronize",
            "test_prune_apply_completes_retention_an_earlier_failure_deferred",
        ),
    ),
    # 10
    "before and between repair ref replacements": (
        (
            "tests.unit.test_crash_injection",
            "test_a_repair_interrupted_before_the_rename_changes_nothing_and_rolls_back",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_repair_interrupted_between_the_two_ref_switches_is_completed",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_an_interrupted_repair_whose_replacement_is_damaged_switches_nothing",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_replacement_lost_between_the_rename_and_the_re_read_switches_nothing",
        ),
        (
            "tests.unit.test_crash_injection",
            "test_a_repair_of_a_non_current_revision_completes_without_moving_current",
        ),
    ),
    # 11
    "during quarterly verification": (
        (
            "tests.unit.test_verify_command",
            "test_a_verification_interrupted_leaves_the_archive_exactly_as_it_was",
        ),
        ("tests.unit.test_verify_command", "test_a_failing_verification_writes_its_report_too"),
        (
            "tests.unit.test_verify_command",
            "test_full_is_refused_while_another_command_holds_the_lock",
        ),
    ),
}
"""Each §26.6 injection point, and the tests that inject failure there."""

POINTS: Final = 11
"""§26.6 lists eleven. If the plan gains a twelfth, this fails until it is mapped."""


def test_every_documented_injection_point_is_mapped():
    assert len(MATRIX) == POINTS


@pytest.mark.parametrize("module", MODULES)
def test_every_module_named_in_the_matrix_imports(module):
    assert importlib.import_module(module) is not None


def test_the_module_list_is_exactly_what_the_matrix_names():
    """`MODULES` claims to be the modules `MATRIX` draws from — so derive that
    set and compare, rather than trusting the tuple to be maintained by hand."""
    named = {module for covering in MATRIX.values() for module, _ in covering}
    assert set(MODULES) == named


@pytest.mark.parametrize(("point", "covering"), sorted(MATRIX.items()))
def test_every_injection_point_names_tests_that_exist(point, covering):
    """The claim this file makes is that these tests cover these points.

    Half of that claim — that the tests exist and are named what this says — is
    checkable, so it is checked. The other half is judgement, and lives in the
    comments above and in `docs/progress.md`'s `OPS-005` entry.
    """
    assert covering, f"{point} is mapped to nothing"
    for module_name, test_name in covering:
        module = importlib.import_module(module_name)
        assert hasattr(module, test_name), f"{point}: {module_name}.{test_name} is gone"
        assert callable(getattr(module, test_name))
