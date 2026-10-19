"""Explicit REST semantic modes and concrete evidence for the API-016 gate.

The documentation table is a contract, not an inventory inferred from handlers.
Keep these independently declared fields and named pytest functions in agreement.
Parameter evidence identifies one AST expression rather than a generated pytest ID.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    module: str
    function: str
    parameter: str | None = None
    case: str | None = None

    @property
    def citation(self) -> str:
        return f"tests/unit/{self.module}.py::{self.function}"


@dataclass(frozen=True)
class ParityMode:
    cli_mode: str
    service: str
    route: str
    role: str
    lock: str
    hub: str
    execution: str
    effects: str
    cli_tests: tuple[Evidence, ...]
    api_tests: tuple[Evidence, ...]

    @property
    def contract(self) -> tuple[str, ...]:
        return (
            self.cli_mode,
            self.service,
            self.route,
            self.role,
            self.lock,
            self.hub,
            self.execution,
            self.effects,
        )


def read_case(case: str) -> Evidence:
    return Evidence(
        "test_cli_api_reads",
        "test_reader_modes_need_no_client_archive_config_or_hub_credentials",
        "arguments",
        case,
    )


def writer_case(case: str) -> Evidence:
    return Evidence(
        "test_cli_api_writes", "test_writer_cli_emits_exact_real_terminal_result", "arguments", case
    )


PAGINATION = Evidence(
    "test_rest_pagination_gate",
    "test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids",
)


PARITY = (
    ParityMode(
        "version --server",
        "version",
        "GET /version",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (read_case("['version', '--server']"),),
        (
            Evidence(
                "test_api_reads",
                "test_version_health_diagnose_later_invalid_policy_and_capabilities_show_role",
            ),
        ),
    ),
    ParityMode(
        "capabilities",
        "capabilities",
        "GET /capabilities",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_api_client_sockets", "test_reader_client_uses_real_unix_tcp_and_verified_tls"
            ),
            Evidence(
                "test_api_client_adversarial",
                "test_failed_capability_envelope_cannot_authorize_from_partial_data",
            ),
        ),
        (
            Evidence(
                "test_api_reads",
                "test_version_health_diagnose_later_invalid_policy_and_capabilities_show_role",
            ),
        ),
    ),
    ParityMode(
        "config validate (installed)",
        "validate_config",
        "POST /config/validate",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (read_case("['config', 'validate']"),),
        (
            Evidence(
                "test_api_commands",
                "test_installed_validation_reports_domain_failure_without_hub_or_probes",
            ),
            Evidence(
                "test_api_candidates",
                "test_candidate_validation_keeps_useful_legacy_fields_separate_from_authority",
            ),
        ),
    ),
    ParityMode(
        "config validate --config (candidate)",
        "validate_candidate",
        "POST /config/validate",
        "W",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_api_reads",
                "test_candidate_cli_sends_content_and_preserves_validation_compatibility",
            ),
        ),
        (
            Evidence(
                "test_api_candidates_adversarial",
                "test_valid_incompatible_candidate_is_assessed_without_credentials",
            ),
            Evidence(
                "test_api_candidates_adversarial",
                "test_malformed_candidate_preserves_configuration_problems",
            ),
            Evidence(
                "test_api_candidates_adversarial",
                "test_candidate_validation_survives_invalid_installed_policy_without_claiming_compatibility",
            ),
        ),
    ),
    ParityMode(
        "archive init --inspect",
        "inspect_archive",
        "GET /archive/inspection",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            read_case("['archive', 'init', '--inspect']"),
            Evidence("test_archive_init", "test_inspect_mutates_nothing"),
            Evidence("test_archive_init", "test_inspect_reports_an_adoptable_published"),
        ),
        (
            Evidence(
                "test_api_adversarial",
                "test_inspection_diagnoses_corrupt_or_vanished_sentinel_without_repair",
            ),
        ),
    ),
    ParityMode(
        "archive init --confirm",
        "initialize_archive",
        "POST /archive/initializations",
        "W",
        "archive",
        "no",
        "J",
        "receipt; initial layout/sentinel",
        (
            Evidence("test_archive_init", "test_confirm_creates_the_archive"),
            Evidence("test_archive_init", "test_confirm_adopts_a_pre_existing_published"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_initialization_is_only_explicit_confirmed_and_configured",
                "enabled",
                "True",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_initialization_is_disabled_before_body_or_receipt",
            ),
        ),
    ),
    ParityMode(
        "doctor --read-only",
        "diagnose",
        "POST /diagnostics",
        "R",
        "none",
        "explicit",
        "J",
        "receipt only",
        (
            read_case("['doctor', '--read-only']"),
            Evidence(
                "test_readonly_commands", "test_read_only_never_reports_a_capability_as_passing"
            ),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries",
            ),
            Evidence(
                "test_api_command_adversarial",
                "test_only_literal_true_diagnostics_is_reader_authorized",
            ),
        ),
    ),
    ParityMode(
        "doctor (probes)",
        "diagnose",
        "POST /diagnostics",
        "W",
        "archive",
        "explicit",
        "J",
        "receipt; temporary health probes",
        (
            writer_case("['doctor']"),
            Evidence("test_readonly_commands", "test_doctor_reports_checks_in_the_normative_order"),
            Evidence("test_readonly_commands", "test_the_writability_probe_leaves_nothing_behind"),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries",
            ),
        ),
    ),
    ParityMode(
        "plan (installed)",
        "plan_sync",
        "POST /plans",
        "R",
        "none",
        "yes",
        "J",
        "receipt only",
        (
            read_case("['plan']"),
            Evidence(
                "test_readonly_commands", "test_plan_keeps_configuration_order_not_selector_order"
            ),
            Evidence(
                "test_readonly_commands", "test_one_repository_failing_does_not_hide_the_others"
            ),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries",
            ),
            Evidence(
                "test_api_command_adversarial",
                "test_plan_selector_normalization_and_caller_class_namespace",
            ),
        ),
    ),
    ParityMode(
        "plan --config (candidate)",
        "plan_candidate",
        "POST /plans",
        "W",
        "none",
        "yes",
        "J",
        "receipt only",
        (
            Evidence(
                "test_cli_api_reads",
                "test_compatible_candidate_plan_cli_preserves_selection_and_never_downloads",
            ),
        ),
        (
            Evidence(
                "test_api_candidates_adversarial",
                "test_candidate_plan_uses_installed_credential_and_candidate_repository_policy",
            ),
            Evidence(
                "test_api_candidates_adversarial",
                "test_candidate_plan_refuses_authority_before_credentials_or_hub",
            ),
            Evidence(
                "test_api_candidates_adversarial",
                "test_queued_candidate_rechecks_fresh_installed_authority",
            ),
        ),
    ),
    ParityMode(
        "sync",
        "synchronize",
        "POST /syncs",
        "W",
        "archive",
        "yes",
        "J",
        "receipt; journals/cache/publication/catalog/report",
        (
            writer_case("['sync', MODEL.selector]"),
            Evidence("test_synchronize", "test_the_sync_command_restricts_a_run_to_its_selectors"),
            Evidence(
                "test_cli_api_writes",
                "test_sync_cli_keeps_failure_aggregation_priority_and_report_identity",
            ),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_sync_rest_runs_real_publication_and_reobserves_without_download",
            ),
            Evidence("test_api_commands", "test_sync_http_preserves_partial_failure_priority"),
            Evidence(
                "test_api_commands", "test_sync_refuses_unknown_journal_before_first_hub_contact"
            ),
        ),
    ),
    ParityMode(
        "status [selectors]",
        "archive_status",
        "GET /status",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            read_case("['status']"),
            Evidence(
                "test_readonly_commands",
                "test_a_selector_restricts_the_command",
                "command",
                "'status'",
            ),
            Evidence(
                "test_cli_api_reads",
                "test_status_walks_every_page_and_preserves_first_server_envelope",
            ),
        ),
        (
            Evidence(
                "test_api_reads",
                "test_status_pages_reconstruct_configuration_order_and_refuse_stale_cursor",
            ),
            Evidence(
                "test_query_boundary", "test_latest_run_status_checks_archive_and_filename_identity"
            ),
            PAGINATION,
        ),
    ),
    ParityMode(
        "list [selectors] [--type]",
        "list_repositories",
        "GET /repositories",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence("test_synchronize", "test_list_restricts_to_one_repository_type"),
            Evidence("test_synchronize", "test_list_restricts_to_its_selectors"),
            Evidence(
                "test_cli_api_reads",
                "test_real_inventory_includes_unmanaged_revisions_and_known_empty_selection",
            ),
        ),
        (
            Evidence(
                "test_query_boundary",
                "test_metadata_queries_refuse_symlink_components",
                "method",
                "'list_repositories'",
            ),
            Evidence(
                "test_api_client_adversarial",
                "test_inventory_uses_actual_repeated_selector_and_type_wire_parameters",
            ),
            PAGINATION,
        ),
    ),
    ParityMode(
        "list --revisions [selectors] [--type]",
        "list_revisions",
        "GET /repositories/revisions",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            read_case("['list', '--revisions']"),
            Evidence("test_synchronize", "test_list_revisions_describes_each_retained_revision"),
            Evidence(
                "test_cli_api_reads",
                "test_revision_join_preserves_empty_rows_and_pins_current_publication",
            ),
        ),
        (
            Evidence(
                "test_api_reads", "test_exact_namespace_name_refs_manifests_and_report_run_identity"
            ),
            Evidence(
                "test_api_client_adversarial",
                "test_inventory_uses_actual_repeated_selector_and_type_wire_parameters",
            ),
            PAGINATION,
        ),
    ),
    ParityMode(
        "verify --estimate",
        "estimate_verification",
        "GET /verification/estimate",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            read_case("['verify', '--estimate']"),
            Evidence("test_verify_command", "test_estimate_hashes_nothing_and_takes_no_lock"),
            Evidence("test_verify_command", "test_estimate_exits_zero_on_a_damaged_archive"),
        ),
        (
            Evidence(
                "test_query_boundary",
                "test_estimate_stats_artifacts_without_opening_them_for_content",
            ),
            Evidence(
                "test_query_boundary",
                "test_estimate_counts_a_damaged_retained_reference_once_unless_current_is_also_damaged",
            ),
        ),
    ),
    ParityMode(
        "verify --new [--run-id]",
        "verify_archive",
        "POST /verifications",
        "W",
        "worker archive",
        "no",
        "J",
        "receipt; report/catalog",
        (
            writer_case("['verify', '--new']"),
            Evidence(
                "test_verify_command",
                "test_named_run_cli_crosses_http_and_private_worker_without_selecting_latest",
            ),
            Evidence("test_verify_command", "test_a_named_report_that_will_not_load_is_reported"),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result",
                "body",
                "{'mode': 'new'}",
            ),
            Evidence(
                "test_verification_executor",
                "test_real_worker_delegates_all_modes_through_guarded_service",
                "mode",
                "'new'",
            ),
        ),
    ),
    ParityMode(
        "verify --full",
        "verify_archive",
        "POST /verifications",
        "W",
        "worker archive",
        "no",
        "J",
        "receipt; report/catalog",
        (
            writer_case("['verify', '--full']"),
            Evidence(
                "test_verify_command", "test_full_covers_a_repository_that_is_no_longer_configured"
            ),
            Evidence("test_verify_command", "test_full_exits_forty_on_corrupted_content"),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result",
                "body",
                "{'mode': 'full'}",
            ),
            Evidence(
                "test_verification_executor",
                "test_real_worker_delegates_all_modes_through_guarded_service",
                "mode",
                "'full'",
            ),
        ),
    ),
    ParityMode(
        "verify --revision",
        "verify_archive",
        "POST /verifications",
        "W",
        "worker archive",
        "no",
        "J",
        "receipt; report/catalog",
        (
            writer_case("['verify', '--revision', f'{MODEL.selector}@{SHA_A}']"),
            Evidence(
                "test_verify_command", "test_revision_verifies_a_repository_that_is_not_configured"
            ),
            Evidence("test_verify_command", "test_revision_with_an_abbreviated_sha_is_refused"),
        ),
        (
            Evidence(
                "test_api_commands",
                "test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result",
                "body",
                "{'mode': 'revision', 'revision': f'{MODEL.selector}@{SHA_A}'}",
            ),
            Evidence(
                "test_verification_executor",
                "test_real_worker_delegates_all_modes_through_guarded_service",
                "mode",
                "'revision'",
            ),
        ),
    ),
    ParityMode(
        "prune --dry-run",
        "preview_prune",
        "POST /prune-plans",
        "R",
        "none",
        "no",
        "J",
        "receipt only",
        (
            writer_case("['prune', '--dry-run']"),
            Evidence("test_synchronize", "test_prune_dry_run_reports_the_plan_and_mutates_nothing"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_prune_previews_and_applies_one_round_without_replaying_key",
            ),
        ),
    ),
    ParityMode(
        "prune --apply",
        "apply_prune",
        "POST /prunes",
        "W",
        "archive",
        "no",
        "J",
        "receipt; guarded domain mutation/audit",
        (
            writer_case("['prune', '--apply']"),
            Evidence("test_synchronize", "test_prune_apply_takes_the_lock_and_completes_a_plan"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_prune_previews_and_applies_one_round_without_replaying_key",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_preview_key_does_not_authorize_apply_and_maintenance_gate_only_controls_init",
            ),
        ),
    ),
    ParityMode(
        "purge --dry-run [selectors XOR --all-unmanaged]",
        "preview_purge",
        "POST /purge-plans",
        "R",
        "none",
        "no",
        "J",
        "receipt only",
        (
            writer_case("['purge', '--dry-run', '--all-unmanaged']"),
            Evidence(
                "test_cli_api_writes",
                "test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository",
                "mode",
                "'--dry-run'",
            ),
            Evidence(
                "test_synchronize",
                "test_purge_all_unmanaged_removes_only_repositories_absent_from_configuration",
            ),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_unmanaged_purge_preserves_unknown_entries_then_audits_explicit_apply",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_purge_requires_one_explicit_unmanaged_repository_scope",
            ),
        ),
    ),
    ParityMode(
        "purge --apply [selectors XOR --all-unmanaged]",
        "apply_purge",
        "POST /purges",
        "W",
        "archive",
        "no",
        "J",
        "receipt; guarded domain mutation/audit",
        (
            writer_case("['purge', '--apply', '--all-unmanaged']"),
            Evidence(
                "test_cli_api_writes",
                "test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository",
                "mode",
                "'--apply'",
            ),
            Evidence(
                "test_synchronize",
                "test_purge_all_unmanaged_removes_only_repositories_absent_from_configuration",
            ),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_unmanaged_purge_preserves_unknown_entries_then_audits_explicit_apply",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_queued_purge_becoming_managed_refuses_under_lock_before_hub_or_deletion",
            ),
        ),
    ),
    ParityMode(
        "recover --dry-run",
        "preview_recovery",
        "POST /recovery-plans",
        "R",
        "none",
        "no",
        "J",
        "receipt only",
        (
            writer_case("['recover', '--dry-run']"),
            Evidence("test_readonly_commands", "test_recover_dry_run_mutates_nothing"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_recovery_preview_and_apply_preserve_exact_durable_report_identity",
            ),
        ),
    ),
    ParityMode(
        "recover --apply",
        "apply_recovery",
        "POST /recoveries",
        "W",
        "archive",
        "no",
        "J",
        "receipt; guarded domain mutation/audit",
        (
            writer_case("['recover', '--apply']"),
            Evidence(
                "test_readonly_commands", "test_recover_apply_takes_the_lock_and_runs_the_preflight"
            ),
            Evidence(
                "test_readonly_commands",
                "test_recover_apply_performs_nothing_when_the_plan_is_blocked",
            ),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_recovery_preview_and_apply_preserve_exact_durable_report_identity",
            ),
        ),
    ),
    ParityMode(
        "quarantine --dry-run IDs",
        "preview_quarantine",
        "POST /quarantine-plans",
        "R",
        "none",
        "no",
        "J",
        "receipt only",
        (
            writer_case("['quarantine', '--dry-run', 'a' * 32]"),
            Evidence("test_quarantine", "test_cli_dry_run_and_apply_select_only_named_findings"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_quarantine_cleanup_uses_full_batch_proof_and_preserves_other_evidence",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_quarantine_requires_a_bounded_explicit_transaction_id_array",
            ),
        ),
    ),
    ParityMode(
        "quarantine --apply IDs",
        "apply_quarantine",
        "POST /quarantine-cleanups",
        "W",
        "archive",
        "no",
        "J",
        "receipt; guarded domain mutation/audit",
        (
            writer_case("['quarantine', '--apply', 'a' * 32]"),
            Evidence("test_quarantine", "test_cli_validates_entire_batch_before_deleting"),
            Evidence(
                "test_quarantine", "test_cli_cleans_hardlinks_shared_between_selected_targets"
            ),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_quarantine_cleanup_uses_full_batch_proof_and_preserves_other_evidence",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_quarantine_apply_reproves_entire_batch_after_preview_and_preserves_unknown_evidence",
            ),
        ),
    ),
    ParityMode(
        "repair TYPE:ID@SHA [--reason]",
        "repair_revision",
        "POST /repairs",
        "W",
        "archive",
        "yes",
        "J",
        "receipt; guarded domain mutation/audit",
        (
            writer_case("['repair', f'{MODEL.selector}@{SHA_A}']"),
            Evidence(
                "test_cli_api_writes",
                "test_repair_reason_cli_is_persisted_with_exact_terminal_identity",
            ),
            Evidence("test_crash_injection", "test_the_repair_command_reports_a_refused_download"),
        ),
        (
            Evidence(
                "test_api_maintenance",
                "test_repair_keeps_original_manifest_generation_locator_and_grace",
            ),
            Evidence(
                "test_api_maintenance_adversarial",
                "test_repair_requires_exact_revision_and_never_accepts_credential_override",
            ),
        ),
    ),
    ParityMode(
        "reports/references/manifests",
        "read_evidence",
        "GET /runs; GET /runs/{run_id}; repository subresources",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_query_evidence", "test_report_reads_preserve_every_existing_report_variant"
            ),
            Evidence(
                "test_query_evidence",
                "test_exact_reference_and_manifest_preserve_their_distinct_locator_bases",
            ),
        ),
        (
            Evidence(
                "test_api_reads", "test_exact_namespace_name_refs_manifests_and_report_run_identity"
            ),
            Evidence(
                "test_api_reads",
                "test_large_reports_stream_in_bounded_chunks_and_sanitize_registered_secrets",
            ),
            PAGINATION,
        ),
    ),
    ParityMode(
        "operations show/wait/lookup",
        "observe_operation",
        "GET /operations; GET /operations/lookup; GET /operations/{id}[/result or /events]",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_operation_helpers",
                "test_show_and_lookup_preserve_server_envelope_metadata",
            ),
            Evidence(
                "test_cli_operations_adversarial",
                "test_operations_wait_resumes_event_cursor_and_returns_exact_terminal_envelope",
            ),
            Evidence(
                "test_cli_operations_adversarial",
                "test_lost_post_ack_recovers_by_printed_key_and_retry_never_resubmits",
            ),
        ),
        (
            Evidence(
                "test_api_operations",
                "test_reader_can_observe_writer_history_but_lookup_is_class_scoped",
            ),
            Evidence(
                "test_api_operations",
                "test_exact_stored_result_preserves_domain_envelope_and_failed_exit",
            ),
            Evidence(
                "test_api_operations",
                "test_event_pages_have_explicit_dropped_prefix_and_sequence_cursor",
            ),
            PAGINATION,
        ),
    ),
    ParityMode(
        "search",
        "catalog_search",
        "GET /catalog/search",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_catalog",
                "test_cli_catalog_reads_collect_and_preserve_server_envelope",
                "arguments",
                "['search', '--scope', 'all', '--page-size', '1']",
            ),
        ),
        (
            Evidence(
                "test_api_catalog",
                "test_catalog_routes_share_strict_wrappers_and_original_capabilities",
            ),
        ),
    ),
    ParityMode(
        "tags",
        "catalog_facets",
        "GET /catalog/facets",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_catalog",
                "test_cli_catalog_reads_collect_and_preserve_server_envelope",
                "arguments",
                "['tags', '--scope', 'all', '--page-size', '1']",
            ),
        ),
        (
            Evidence(
                "test_api_catalog",
                "test_catalog_routes_share_strict_wrappers_and_original_capabilities",
            ),
        ),
    ),
    ParityMode(
        "catalog show TYPE:ID",
        "catalog_entry",
        "GET /catalog/repositories/{repository_type}/{namespace}/{name}",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_catalog",
                "test_cli_catalog_reads_collect_and_preserve_server_envelope",
                "arguments",
                "['catalog', 'show', MODEL.selector]",
            ),
        ),
        (
            Evidence(
                "test_api_catalog",
                "test_catalog_routes_share_strict_wrappers_and_original_capabilities",
            ),
        ),
    ),
    ParityMode(
        "catalog variants TYPE:ID",
        "catalog_variants",
        "GET /catalog/repositories/{repository_type}/{namespace}/{name}/variants",
        "R",
        "none",
        "no",
        "Q",
        "none",
        (
            Evidence(
                "test_cli_catalog",
                "test_cli_catalog_reads_collect_and_preserve_server_envelope",
                "arguments",
                "['catalog', 'variants', MODEL.selector, '--page-size', '1']",
            ),
        ),
        (
            Evidence(
                "test_api_catalog",
                "test_catalog_routes_share_strict_wrappers_and_original_capabilities",
            ),
        ),
    ),
    ParityMode(
        "catalog refresh [selectors]",
        "refresh_catalog",
        "POST /catalog/refreshes",
        "W",
        "archive",
        "no",
        "J",
        "receipt; supplemental metadata",
        (Evidence("test_cli_catalog", "test_refresh_cli_observes_exact_typed_writer_result"),),
        (
            Evidence(
                "test_api_catalog_refresh",
                "test_refresh_http_captures_once_replays_original_and_new_key_recaptures",
            ),
        ),
    ),
)
