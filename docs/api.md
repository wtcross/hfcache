# Writer REST API contract

Status: API-006 implements authenticated archive metadata and API-007 adds
bounded receipt/admission primitives and operation observation; API-009 adds
typed command routes, with guarded maintenance/initialization added by API-010,
under [the active plan](plans/2026-10-17-plan-rest-api-and-mcp.md).
API-012 adds candidate validation/planning/read CLI and API-013 completes
operational CLI/observation. API-014 packages activated/scheduled services and
API-015 integrates Cockpit; API-016 completes REST acceptance. MCP-001 adds an
optional authenticated transport with no tools yet; see [MCP](mcp.md). No
production installation or listener start is asserted by implementation evidence.

## Service and transport boundary

Decision [108](adr/decision-108.md) introduces ordinary typed query/command
services. HTTP and future MCP adapters never invoke Typer/public CLI callbacks or
parse CLI stdout; the operational CLI uses an independent typed HTTP client.
Adapter implementations do not call one another's callbacks. Archive algorithms, FS/TX
requirements, sentinel identity, local flock, and publication authority remain
unchanged. HTTP metadata is not artifact transfer: locators are relative to
`published/` and identify exact immutable publication instances (FS-12).

All routes below have prefix `/api/v1`. R permits a REST reader or writer;
W requires a REST writer. MCP credentials authorize no REST requests.
Short queries return typed data; heavyweight calls return durable receipts
and eventually the exact schema-1 CLI Envelope. Auth precedes all reads,
including health, docs, and OpenAPI. Interactive docs default disabled.

## Operation parity matrix

This table is the machine-readable parity source. Test columns cite concrete
CLI/API enforcement evidence; API-016 checks every row and reference. Preserve
one row for each mode when filling them. `archive` means the cross-process
local flock through all domain persistence; `worker archive` means that same
lock is owned by the offline executor. A preview cannot grant apply authority.
An implemented row means its HTTP resource exists; API-012/013 now use those
resources for operational CLI modes and explicit resumable observation.
Native Unix requests may use unprefixed `/api/v1` despite a public TCP prefix;
links/docs follow the trusted effective request prefix, without changing TCP
security or client schemas ([decision 123](adr/decision-123.md)).
Evidence cells use stable `path::test_function` references. The independent
[`tests/rest_parity.py`](../tests/rest_parity.py) manifest records the same rows,
fields and citation sets, including selected parameter cases; the
[gate tests](../tests/unit/test_rest_parity_gate.py) resolve them statically without
importing test modules. Capability/evidence-only rows cite typed client tests and
do not add new public CLI command families.

| CLI mode | Service | Route | Role | Lock | Hub | Execution | Effects | CLI test | API test | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| version --server | version | GET /version | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials` | `tests/unit/test_api_reads.py::test_version_health_diagnose_later_invalid_policy_and_capabilities_show_role` | implemented |
| capabilities | capabilities | GET /capabilities | R | none | no | Q | none | `tests/unit/test_api_client_sockets.py::test_reader_client_uses_real_unix_tcp_and_verified_tls`; `tests/unit/test_api_client_adversarial.py::test_failed_capability_envelope_cannot_authorize_from_partial_data` | `tests/unit/test_api_reads.py::test_version_health_diagnose_later_invalid_policy_and_capabilities_show_role` | implemented |
| config validate (installed) | validate_config | POST /config/validate | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials` | `tests/unit/test_api_commands.py::test_installed_validation_reports_domain_failure_without_hub_or_probes`; `tests/unit/test_api_candidates.py::test_candidate_validation_keeps_useful_legacy_fields_separate_from_authority` | implemented |
| config validate --config (candidate) | validate_candidate | POST /config/validate | W | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_candidate_cli_sends_content_and_preserves_validation_compatibility` | `tests/unit/test_api_candidates_adversarial.py::test_valid_incompatible_candidate_is_assessed_without_credentials`; `tests/unit/test_api_candidates_adversarial.py::test_malformed_candidate_preserves_configuration_problems`; `tests/unit/test_api_candidates_adversarial.py::test_candidate_validation_survives_invalid_installed_policy_without_claiming_compatibility` | implemented |
| archive init --inspect | inspect_archive | GET /archive/inspection | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_archive_init.py::test_inspect_mutates_nothing`; `tests/unit/test_archive_init.py::test_inspect_reports_an_adoptable_published` | `tests/unit/test_api_adversarial.py::test_inspection_diagnoses_corrupt_or_vanished_sentinel_without_repair` | implemented |
| archive init --confirm | initialize_archive | POST /archive/initializations | W | archive | no | J | receipt; initial layout/sentinel | `tests/unit/test_archive_init.py::test_confirm_creates_the_archive`; `tests/unit/test_archive_init.py::test_confirm_adopts_a_pre_existing_published` | `tests/unit/test_api_maintenance.py::test_initialization_is_only_explicit_confirmed_and_configured`; `tests/unit/test_api_maintenance_adversarial.py::test_initialization_is_disabled_before_body_or_receipt` | implemented |
| doctor --read-only | diagnose | POST /diagnostics | R | none | explicit | J | receipt only | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_readonly_commands.py::test_read_only_never_reports_a_capability_as_passing` | `tests/unit/test_api_commands.py::test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries`; `tests/unit/test_api_command_adversarial.py::test_only_literal_true_diagnostics_is_reader_authorized` | implemented |
| doctor (probes) | diagnose | POST /diagnostics | W | archive | explicit | J | receipt; temporary health probes | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_readonly_commands.py::test_doctor_reports_checks_in_the_normative_order`; `tests/unit/test_readonly_commands.py::test_the_writability_probe_leaves_nothing_behind` | `tests/unit/test_api_commands.py::test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries` | implemented |
| plan (installed) | plan_sync | POST /plans | R | none | yes | J | receipt only | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_readonly_commands.py::test_plan_keeps_configuration_order_not_selector_order`; `tests/unit/test_readonly_commands.py::test_one_repository_failing_does_not_hide_the_others` | `tests/unit/test_api_commands.py::test_reader_plan_and_explicit_diagnostics_keep_effects_and_lock_boundaries`; `tests/unit/test_api_command_adversarial.py::test_plan_selector_normalization_and_caller_class_namespace` | implemented |
| plan --config (candidate) | plan_candidate | POST /plans | W | none | yes | J | receipt only | `tests/unit/test_cli_api_reads.py::test_compatible_candidate_plan_cli_preserves_selection_and_never_downloads` | `tests/unit/test_api_candidates_adversarial.py::test_candidate_plan_uses_installed_credential_and_candidate_repository_policy`; `tests/unit/test_api_candidates_adversarial.py::test_candidate_plan_refuses_authority_before_credentials_or_hub`; `tests/unit/test_api_candidates_adversarial.py::test_queued_candidate_rechecks_fresh_installed_authority` | implemented |
| sync | synchronize | POST /syncs | W | archive | yes | J | receipt; journals/cache/publication/catalog/report | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_synchronize.py::test_the_sync_command_restricts_a_run_to_its_selectors`; `tests/unit/test_cli_api_writes.py::test_sync_cli_keeps_failure_aggregation_priority_and_report_identity` | `tests/unit/test_api_commands.py::test_sync_rest_runs_real_publication_and_reobserves_without_download`; `tests/unit/test_api_commands.py::test_sync_http_preserves_partial_failure_priority`; `tests/unit/test_api_commands.py::test_sync_refuses_unknown_journal_before_first_hub_contact` | implemented |
| status [selectors] | archive_status | GET /status | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_readonly_commands.py::test_a_selector_restricts_the_command`; `tests/unit/test_cli_api_reads.py::test_status_walks_every_page_and_preserves_first_server_envelope` | `tests/unit/test_api_reads.py::test_status_pages_reconstruct_configuration_order_and_refuse_stale_cursor`; `tests/unit/test_query_boundary.py::test_latest_run_status_checks_archive_and_filename_identity`; `tests/unit/test_rest_pagination_gate.py::test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids` | implemented |
| list [selectors] [--type] | list_repositories | GET /repositories | R | none | no | Q | none | `tests/unit/test_synchronize.py::test_list_restricts_to_one_repository_type`; `tests/unit/test_synchronize.py::test_list_restricts_to_its_selectors`; `tests/unit/test_cli_api_reads.py::test_real_inventory_includes_unmanaged_revisions_and_known_empty_selection` | `tests/unit/test_query_boundary.py::test_metadata_queries_refuse_symlink_components`; `tests/unit/test_api_client_adversarial.py::test_inventory_uses_actual_repeated_selector_and_type_wire_parameters`; `tests/unit/test_rest_pagination_gate.py::test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids` | implemented |
| list --revisions [selectors] [--type] | list_revisions | GET /repositories/revisions | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_synchronize.py::test_list_revisions_describes_each_retained_revision`; `tests/unit/test_cli_api_reads.py::test_revision_join_preserves_empty_rows_and_pins_current_publication` | `tests/unit/test_api_reads.py::test_exact_namespace_name_refs_manifests_and_report_run_identity`; `tests/unit/test_api_client_adversarial.py::test_inventory_uses_actual_repeated_selector_and_type_wire_parameters`; `tests/unit/test_rest_pagination_gate.py::test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids` | implemented |
| verify --estimate | estimate_verification | GET /verification/estimate | R | none | no | Q | none | `tests/unit/test_cli_api_reads.py::test_reader_modes_need_no_client_archive_config_or_hub_credentials`; `tests/unit/test_verify_command.py::test_estimate_hashes_nothing_and_takes_no_lock`; `tests/unit/test_verify_command.py::test_estimate_exits_zero_on_a_damaged_archive` | `tests/unit/test_query_boundary.py::test_estimate_stats_artifacts_without_opening_them_for_content`; `tests/unit/test_query_boundary.py::test_estimate_counts_a_damaged_retained_reference_once_unless_current_is_also_damaged` | implemented |
| verify --new [--run-id] | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_verify_command.py::test_named_run_cli_crosses_http_and_private_worker_without_selecting_latest`; `tests/unit/test_verify_command.py::test_a_named_report_that_will_not_load_is_reported` | `tests/unit/test_api_commands.py::test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result`; `tests/unit/test_verification_executor.py::test_real_worker_delegates_all_modes_through_guarded_service` | implemented |
| verify --full | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_verify_command.py::test_full_covers_a_repository_that_is_no_longer_configured`; `tests/unit/test_verify_command.py::test_full_exits_forty_on_corrupted_content` | `tests/unit/test_api_commands.py::test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result`; `tests/unit/test_verification_executor.py::test_real_worker_delegates_all_modes_through_guarded_service` | implemented |
| verify --revision | verify_archive | POST /verifications | W | worker archive | no | J | receipt; report/catalog | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_verify_command.py::test_revision_verifies_a_repository_that_is_not_configured`; `tests/unit/test_verify_command.py::test_revision_with_an_abbreviated_sha_is_refused` | `tests/unit/test_api_commands.py::test_every_public_verification_mode_delegates_and_preserves_exact_integrity_result`; `tests/unit/test_verification_executor.py::test_real_worker_delegates_all_modes_through_guarded_service` | implemented |
| prune --dry-run | preview_prune | POST /prune-plans | R | none | no | J | receipt only | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_synchronize.py::test_prune_dry_run_reports_the_plan_and_mutates_nothing` | `tests/unit/test_api_maintenance.py::test_prune_previews_and_applies_one_round_without_replaying_key` | implemented |
| prune --apply | apply_prune | POST /prunes | W | archive | no | J | receipt; guarded domain mutation/audit | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_synchronize.py::test_prune_apply_takes_the_lock_and_completes_a_plan` | `tests/unit/test_api_maintenance.py::test_prune_previews_and_applies_one_round_without_replaying_key`; `tests/unit/test_api_maintenance_adversarial.py::test_preview_key_does_not_authorize_apply_and_maintenance_gate_only_controls_init` | implemented |
| purge --dry-run [selectors XOR --all-unmanaged] | preview_purge | POST /purge-plans | R | none | no | J | receipt only | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_cli_api_writes.py::test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository`; `tests/unit/test_synchronize.py::test_purge_all_unmanaged_removes_only_repositories_absent_from_configuration` | `tests/unit/test_api_maintenance.py::test_unmanaged_purge_preserves_unknown_entries_then_audits_explicit_apply`; `tests/unit/test_api_maintenance_adversarial.py::test_purge_requires_one_explicit_unmanaged_repository_scope` | implemented |
| purge --apply [selectors XOR --all-unmanaged] | apply_purge | POST /purges | W | archive | no | J | receipt; guarded domain mutation/audit | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_cli_api_writes.py::test_explicit_unmanaged_purge_cli_scope_keeps_configured_repository`; `tests/unit/test_synchronize.py::test_purge_all_unmanaged_removes_only_repositories_absent_from_configuration` | `tests/unit/test_api_maintenance.py::test_unmanaged_purge_preserves_unknown_entries_then_audits_explicit_apply`; `tests/unit/test_api_maintenance_adversarial.py::test_queued_purge_becoming_managed_refuses_under_lock_before_hub_or_deletion` | implemented |
| recover --dry-run | preview_recovery | POST /recovery-plans | R | none | no | J | receipt only | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_readonly_commands.py::test_recover_dry_run_mutates_nothing` | `tests/unit/test_api_maintenance.py::test_recovery_preview_and_apply_preserve_exact_durable_report_identity` | implemented |
| recover --apply | apply_recovery | POST /recoveries | W | archive | no | J | receipt; guarded domain mutation/audit | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_readonly_commands.py::test_recover_apply_takes_the_lock_and_runs_the_preflight`; `tests/unit/test_readonly_commands.py::test_recover_apply_performs_nothing_when_the_plan_is_blocked` | `tests/unit/test_api_maintenance.py::test_recovery_preview_and_apply_preserve_exact_durable_report_identity` | implemented |
| quarantine --dry-run IDs | preview_quarantine | POST /quarantine-plans | R | none | no | J | receipt only | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_quarantine.py::test_cli_dry_run_and_apply_select_only_named_findings` | `tests/unit/test_api_maintenance.py::test_quarantine_cleanup_uses_full_batch_proof_and_preserves_other_evidence`; `tests/unit/test_api_maintenance_adversarial.py::test_quarantine_requires_a_bounded_explicit_transaction_id_array` | implemented |
| quarantine --apply IDs | apply_quarantine | POST /quarantine-cleanups | W | archive | no | J | receipt; guarded domain mutation/audit | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_quarantine.py::test_cli_validates_entire_batch_before_deleting`; `tests/unit/test_quarantine.py::test_cli_cleans_hardlinks_shared_between_selected_targets` | `tests/unit/test_api_maintenance.py::test_quarantine_cleanup_uses_full_batch_proof_and_preserves_other_evidence`; `tests/unit/test_api_maintenance_adversarial.py::test_quarantine_apply_reproves_entire_batch_after_preview_and_preserves_unknown_evidence` | implemented |
| repair TYPE:ID@SHA [--reason] | repair_revision | POST /repairs | W | archive | yes | J | receipt; guarded domain mutation/audit | `tests/unit/test_cli_api_writes.py::test_writer_cli_emits_exact_real_terminal_result`; `tests/unit/test_cli_api_writes.py::test_repair_reason_cli_is_persisted_with_exact_terminal_identity`; `tests/unit/test_crash_injection.py::test_the_repair_command_reports_a_refused_download` | `tests/unit/test_api_maintenance.py::test_repair_keeps_original_manifest_generation_locator_and_grace`; `tests/unit/test_api_maintenance_adversarial.py::test_repair_requires_exact_revision_and_never_accepts_credential_override` | implemented |
| reports/references/manifests | read_evidence | GET /runs; GET /runs/{run_id}; repository subresources | R | none | no | Q | none | `tests/unit/test_query_evidence.py::test_report_reads_preserve_every_existing_report_variant`; `tests/unit/test_query_evidence.py::test_exact_reference_and_manifest_preserve_their_distinct_locator_bases` | `tests/unit/test_api_reads.py::test_exact_namespace_name_refs_manifests_and_report_run_identity`; `tests/unit/test_api_reads.py::test_large_reports_stream_in_bounded_chunks_and_sanitize_registered_secrets`; `tests/unit/test_rest_pagination_gate.py::test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids` | implemented |
| operations show/wait/lookup | observe_operation | GET /operations; GET /operations/lookup; GET /operations/{id}[/result or /events] | R | none | no | Q | none | `tests/unit/test_cli_operation_helpers.py::test_show_and_lookup_preserve_server_envelope_metadata`; `tests/unit/test_cli_operations_adversarial.py::test_operations_wait_resumes_event_cursor_and_returns_exact_terminal_envelope`; `tests/unit/test_cli_operations_adversarial.py::test_lost_post_ack_recovers_by_printed_key_and_retry_never_resubmits` | `tests/unit/test_api_operations.py::test_reader_can_observe_writer_history_but_lookup_is_class_scoped`; `tests/unit/test_api_operations.py::test_exact_stored_result_preserves_domain_envelope_and_failed_exit`; `tests/unit/test_api_operations.py::test_event_pages_have_explicit_dropped_prefix_and_sequence_cursor`; `tests/unit/test_rest_pagination_gate.py::test_all_size_one_pages_match_local_truth_and_preserve_empty_unmanaged_and_exact_ids` | implemented |

Local `version`, help, `serve`, and `config validate --local` are explicit
bootstrap commands, outside remote operation parity. API-backed commands reject
Hub token overrides. Selectors retain existing grammars and unmanaged-repository
exceptions. Sync is explicitly included here (the draft's §4 table omitted it).

## Shared query results (API-002)

Transport-neutral local queries share orchestration with the CLI and implemented
HTTP metadata routes. `LocalQueries` receives one frozen policy snapshot and
`ExecutionContext` captures execution identity; `ServiceResult` carries payload, problems, classification
and run correlation without rendering. `MetadataQueries` is the narrow read
interface implemented by `LocalQueries`; it offers no command or credential
resolver. Config-validation payload construction takes an already resolved
credential source, never a token value.

Status/list retain schema-1 payload keys, deterministic ordering and unknown
verification confidence. Status covers configured plus unmanaged published
repositories; selectors unknown to both fail HFARG004. Missing/corrupt derived
repository catalogs never authorize a rebuild. ID-based report, reference and
manifest reads reject identity mismatch and unsafe paths and retain exact
publication identity and `published/`-relative locators. API-006 wire
pagination/projections remain separate from these domain results.

API-006 strengthens the shared local read boundary with descriptor-relative
no-follow traversal and optional `QueryBounds`. HTTP supplies finite entry,
artifact and total-byte budgets; a refusal is `HFAPI005`, never an empty or
silently truncated success. Direct `LocalQueries` callers retain complete default
results without transport ceilings; API-backed CLI aggregation is finite and
refuses overflow rather than silently truncating. Status/list/latest-run/catalog reads and
the health/estimate paths use the same safe reader. Missing/corrupt derived
catalogs retain unknown verification confidence and grant no rebuild authority.
Latest-run summaries ignore unreadable or identity-mismatched informational
reports; exact report reads refuse them. Reports check the configured archive
UUID, filename/time and run ID. The verification catalog has no archive-ID field;
safe parse/containment and exact publication-instance keys govern its derived
confidence. References/manifests check repository, SHA, publication identity,
generation and canonical locators. These metadata checks do not assert that
every read revalidates the archive sentinel. Policy pins configured root/UUID;
archive inspection remains a separate diagnostic and performs no repair.

API-003 adds `CommandServices` and immutable requests for the command rows above.
These services preserve domain ordering and classified partial results; public
commands own the common archive lock once. Adapters and later operation runners
must call them without an outer archive lock. Verification persistence now stays
inside its lock/preflight boundary (decision 110). API-009/010 expose the command resources below through those services;
API-012 adds candidate routes/reader CLI modes and API-013 operational CLI/observation.

## Implemented metadata resources (API-006)

All paths below use `/api/v1` and require a REST reader or writer bearer.
Repository IDs have two separately validated path components, `{namespace}` and
`{name}`; `{repository_type}` is `model` or `dataset`. Full SHAs and publication/
run IDs retain domain grammars. No path parameter is an arbitrary filesystem path.

| GET resource | Result in `envelope.data` | Pagination |
| --- | --- | --- |
| `/version` | Existing local version payload; no archive-policy read per request | none |
| `/capabilities` | API/instance identity, credential class/capabilities, enabled read features and maximum page size; API-009/010 advertise `operations=true`, `operation_history=true` and the actual `maintenance_enabled` initialization gate; MCP-001 advertises `mcp` only when enabled, without claiming tools | none |
| `/health` | Daemon readiness, policy-validation state and read-only archive inspection when available | none |
| `/status` | Archive headline plus repository status rows | `repositories` |
| `/repositories` | Published inventory, including unmanaged repositories | `repositories` |
| `/repositories/revisions` | Flat rows containing `repository_type`, `repository_id` and each retained revision's existing fields | `revisions` |
| `/verification/estimate` | Existing estimate payload; no hashing, lock, persistence or Hub | none |
| `/archive/inspection` | Read-only initialization inspection and classified domain problems | none |
| `/runs` | Report IDs in reverse chronological filename order | `runs` |
| `/runs/{run_id}` | Validated existing `report`; preserves that report's domain run ID | bounded JSON stream |
| `/repositories/{repository_type}/{namespace}/{name}/references/{revision}` | `reference` plus `locator_base="published/"`; revision is `current` or a full SHA | none |
| `/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}` | Exact `manifest` plus `tree_base="archive-root/"` | bounded JSON stream |

`health.ready` describes the daemon, not archive integrity, mount proof or
initialization. `policy_valid` is true after a valid fresh snapshot, false on a
classified failed policy/inspection, or null when query capacity prevents that
diagnosis; `archive` may be null. Health returns diagnostics without repairing,
probing writability or reconstructing a catalog. Version/capabilities remain
available if installed archive policy later becomes invalid. Startup still
requires valid server configuration/credentials and an initial installed policy.

### Read and problem wire models

[`ReadResponse`](../src/hfcache/api/models.py) is separate from durable schemas:

| Field | Meaning |
| --- | --- |
| `schema_version` | Wire wrapper version `1` |
| `request_id` | Authoritative server-generated ID for this HTTP request |
| `archive_id` | Fresh snapshot UUID, or startup-pinned configured UUID for policy-independent/fallback diagnostics; never a sentinel-proof claim |
| `config_fingerprint` | Existing archive-policy fingerprint, or null when no fresh snapshot was used |
| `envelope` | Complete schema-1 Envelope, or an explicitly paged piece of its data |
| `next_cursor` | Opaque next-page token, or null |

The Envelope retains domain warnings/errors, exit classification, command and
run identity. Archive inspection can return HTTP 200 with a failed domain
Envelope; a transport success does not make the archive healthy. Report reads
use the existing report's run ID while request correlation remains independent.
Future CLI clients reconstruct paged arrays and retain the first Envelope's
invocation metadata. For `list --revisions`, combine inventory rows with revision
pages grouped by repository; the transport does not silently discard inventory
metadata or claim the current CLI is already remote.

`ApiProblem` has exactly `request_id`, `code`, safe `message` and `exit_code`.
It contains no framework input echo, raw artifact context, exception or traceback.
Every HTTP response carries `X-Request-ID`, `Cache-Control: no-store`,
`X-Content-Type-Options: nosniff` and a frame-ancestor CSP. Incoming request IDs do
not choose authoritative correlation. Authentication precedes known/unknown
routes, method errors, docs/schema and request-body validation.
Noncanonical trailing-slash paths return an error without automatic redirects,
so a rejected query is never reflected into a Location header. OpenAPI and the
optional docs HTML obey the same normal response byte ceiling.

### Query parameters and page ordering

Status, repository inventory and revision pages accept repeated `selector`
values using domain `TYPE:ID`, optional `type=model|dataset`, `limit` and `cursor`.
Report inventory accepts only `limit` and `cursor`. Other read routes reject all
query parameters. Unknown keys, repeated scalar parameters, coercive numeric
forms and malformed domain values fail safely. `limit` is a positive ASCII
decimal integer, default `100`, capped by `limits.max_page_size`; at most `100`
selectors of at most `256` characters are accepted. Cursors are at most `256`
characters. The raw query is capped at `8192` bytes and total header name/value
bytes at `32768`. Read routes accept no nonempty body; the byte limit is enforced
even without Content-Length.

Status preserves configured order followed by unmanaged publication order;
inventory uses canonical repository order, revisions use that order followed by
retained publication generation, and report IDs use reverse timestamped filename
order. Offset cursors bind route/filter scope, policy fingerprint and a digest
of the sanitized paged array. Changed scope/policy/array or an offset beyond the
current result returns 409; malformed encoding returns 422. Restart the walk
after a stale-cursor refusal. Cursor contents are not an authorization grant.
Walk until `next_cursor=null`; page sequences are not an archive-wide snapshot
and ancillary fields can change independently of the paged array. No page silently substitutes a newer exact
publication or truncates a legacy result.

### Response and evidence budgets

Normal JSON responses are capped at `limits.max_response_bytes` (default 8 MiB).
Shared metadata work is bounded by `max_scan_entries` and per-artifact plus
aggregate bytes, each byte ceiling defaulting to `max_artifact_bytes` (64 MiB).
Exhaustion is `HFAPI005`/503, never an empty page or an unverified-to-verified
upgrade. A small returned page does not bypass the bounded underlying scan.

Reports/manifests are parsed and identity-validated within that source budget,
then stream a `ReadResponse` using incremental JSON encoding with chunks at most
8192 bytes. The encoded stream is pre-counted and capped at eight times the
configured artifact ceiling to allow JSON escaping/wrapper overhead. It retains
a bounded parsed representation in memory; it is not bulk file transfer or an
unbounded raw-file relay. Response-size refusal happens before headers, and the
metadata lease remains held through stream completion/disconnect.

## Implemented command resources (API-009)

Five explicit POST resources use shared services. They are management commands,
not arbitrary command/path dispatch. All reject query parameters and unknown
body fields. Every request authenticates before body reception; sync and
verification require writer capability before any body is read. Body-dependent
checks require writer capability before DTO validation when `candidate` is
present, or when diagnostics does not contain literal `read_only=true`.

| Route under `/api/v1` | Strict JSON object | Role/effect | Response |
| --- | --- | --- | --- |
| `POST /syncs` | `selectors` array, default `[]` | W; ordinary whole-run sync, archive mutation/automatic retention under the shared lock | Keyed job, 202 |
| `POST /verifications` | Required `mode`: `new`, `full` or `revision`; nullable `revision`/`run_id` as below | W; private offline verification, report/catalog persistence under worker-owned lock | Keyed job, 202 |
| `POST /plans` | `selectors` array, default `[]`; optional bounded TOML `candidate` (API-012) | R installed / W candidate; Hub planning with installed authority, no archive mutation/lock | Keyed job, 202 |
| `POST /diagnostics` | Required strict `read_only` boolean | R for `true`, W for `false`; Hub checks in both, write probes/lock only for `false` | Keyed job, 202 |
| `POST /config/validate` | `{}` for installed policy, or bounded TOML `candidate` (API-012) | R installed / W candidate; no Hub request, receipt or archive mutation | Immediate `ReadResponse`, 200 |

Sync/plan accept at most 100 selectors, each at most 256 characters, parsed by
existing repository validators and canonicalized as a sorted distinct repository
set before request hashing. Execution still follows installed configuration
order and enabled/continuation/capacity policy, never caller array order. Empty
selectors use all configured repositories. A missing configured repository is
reported by the existing service rather than silently substituted.
For sync/plan, a valid full-SHA suffix is validated then discarded when selecting
the repository, matching the existing service: it does not override that
repository's configured revision. The canonical digest uses distinct `TYPE:ID`
values, so duplicates, ordering and a valid unused suffix do not change scope.

Verification requires exactly one mode. A nonnull `revision` is required exactly
in revision mode and must identify `TYPE:ID@` a full lowercase 40-character SHA;
it is null or omitted otherwise. Nonnull `run_id` is optional only for new mode
and uses the existing 32-lowercase-hex
run grammar. These are selectors of existing domain evidence, not arbitrary
files. `estimate` is not an accepted job mode; use `GET /verification/estimate`.
New/full/revision all delegate to the private executor, which owns target
resolution, hashing, report persistence and catalog merge. The API bearer/Hub
credential is never forwarded there.

Diagnostics always requires an explicit boolean. A reader sending false,
missing mode or a non-boolean value receives 403 before DTO validation; a writer
with missing/invalid mode receives 422 and starts no probe. `read_only=true`
suppresses write probes but can resolve the installed Hub credential and contact
the Hub. Planning likewise resolves/tree-inspects through installed authority.
Both use the heavy lane and control-state receipts, so neither is an MCP metadata
read. Probing diagnostics retains the existing ability to diagnose uninitialized
storage without treating a missing sentinel as permission to initialize it.

### POST body boundary

Recognized command POSTs require exactly one `Content-Type: application/json`,
optionally `charset=utf-8` (quoted UTF-8 is accepted), and no `Content-Encoding`.
The body must contain a JSON object; `{}` is valid where the DTO permits it.
Empty bodies, arrays/scalars, invalid UTF-8 or escaped invalid Unicode, duplicate
keys, nonfinite constants, excessive nesting (maximum depth 32), unknown fields
and coercions fail safely. Shape/type failures use `HFAPI006`/422; shared selector
grammar refusals retain `HFARG001` with HTTP 422. Actual body bytes
over `max_request_bytes` are 413, including chunked bodies. Errors never echo
raw body, unknown keys, credentials or framework validation input. Unknown/read
routes retain their empty-body contract. Missing/invalid authentication takes
precedence over body reading, and a reader cannot send a malformed writer POST
to bypass the capability boundary.

### Admission model and exact results

These four job resources require exactly one valid `Idempotency-Key`. They use the
installed snapshot's `sync.lock_wait_seconds` for sync/planning/diagnostics and
`verification.lock_wait_seconds` for verification; one absolute budget spans
admission/queue and lock/delegation waiting. Matching retries consult the durable
binding before fresh policy, capacity or verifier probes. These routes never
turn a client-supplied timeout, configuration file or command name into execution
policy.

`AcceptanceResponse` is independent of `ReadResponse` and the durable schema.
It contains `schema_version=1`, current server-generated `request_id`, admitted
`archive_id`/`config_fingerprint`, public `operation: OperationView`, `created`
and `links: {status, result, events}`. HTTP 202 carries `Location` equal to the
status link; links include the configured URL prefix. A new operation has
`created=true`; a matching retry has `created=false` and the original operation,
including its admitted fingerprint after policy changes. Both return 202 even
if the operation has already finished. No terminal success Envelope is fabricated
inside an admission response, and no key/request digest or original body is exposed.

Poll the authenticated status link to inspect state and the events link with its
sequence cursor for bounded progress. Retrieve the result link for the exact
schema-1 Envelope/domain run ID/partial results and exit classification. A result
GET may return HTTP 200 with a failed domain Envelope; known unfinished/interrupted
results are `HFAPI015`/409 and missing/expired history is `HFAPI013`/404, both
exit 20. HTTP 202 is admission only. Losing the acknowledgement, response or
observer never proves nonexecution: use the original key's non-submitting lookup
before any deliberate retry. Do not generate another key to repeat uncertain work.

For an authenticated request, representative bodies are:

```http
POST /api/v1/plans
Content-Type: application/json
Idempotency-Key: example-plan-request

{"selectors":["model:organization/model-name"]}
```

```http
POST /api/v1/diagnostics
Content-Type: application/json
Idempotency-Key: example-read-only-diagnostics

{"read_only":true}
```

Writer-only sync uses the same selector body; verification uses, for example,
`{"mode":"full"}` or `{"mode":"new","run_id":"0123456789abcdef0123456789abcdef"}`.
Examples omit bearer values; authentication is required on submission and every
poll. Installed validation sends `{}` without a key and returns its ordinary
schema-1 validation result in `ReadResponse.envelope`; classified policy/credential
failures remain failed Envelopes at HTTP 200. It reports nonsecret token-source
classification and never returns a credential.

### Candidate content and installed authority (API-012)

`candidate` is TOML text, not a server pathname. Raw field presence requires writer
capability before DTO validation, including explicit null; readers use the installed
shape without that field. Only an absent field means installed intent; explicit
null is refused. For plans, only an absent candidate is omitted from canonical
request projection, preserving the previous
installed `{"selectors": [...]}` key digest. Candidate text binds the request as
exact text; different text is a different keyed request even if policy is equivalent.

Local CLI content reads and server candidate assessment are bounded to 1 MiB of
UTF-8. The server's total JSON request bound applies independently; escaping/wrapper
overhead may cause 413 even before the content limit. Unknown dispatch fields,
top-level token/source/endpoint overrides and arbitrary-path dispatch remain refused.
Proposed authority changes inside candidate policy can be assessed without use.
These routes never
install configuration, create an archive or resolve candidate-selected credentials.

Valid candidate validation includes the four legacy validation payload fields
plus `valid`, `syntax_valid`, `authority_compatible`, `authority_mismatches` and
`installed_policy_valid`, with `token_source="not-resolved"`. Invalid candidates
retain the validity/compatibility flags and ordered errors without inventing
unavailable counts/fingerprints. Valid syntax/policy
with incompatible authority stays valid at exit 0, reports compatibility false
and only fixed mismatch field names. If installed policy is currently unavailable/
invalid, candidate syntax validation still works: a valid candidate has true
validity, null compatibility and `installed_policy_valid=false`. Null compatibility
is unknown, not authority to plan. Invalid candidate syntax/policy retains its
ordered safe classified errors. No credential, Hub request, archive probe or
configuration installation occurs during candidate validation.

Candidate planning is a keyed writer job. It requires all six installed authority
fields to match before credential-bearing work: archive root/UUID, Hub endpoint,
token mode, credential name and expected account. Compatible candidate repository,
retention and worker policy can be previewed, while only the installed credential
is resolved. Incompatibility or malformed policy yields 202 admission followed by
the exact classified failed terminal Envelope, not Hub work against the proposed
endpoint. The receipt/result wrapper retains the installed admitted fingerprint;
candidate intent cannot replace its operation authority. Recheck all six fields
again immediately before Hub work after queue waiting: `hub.credential_name` is
excluded from the policy fingerprint, so fingerprint equality alone cannot prove
that credential authority still matches. Syntax validation alone
never grants planning, installation or later mutation authority.

The CLI reads `--config` on its own host for validate/plan and submits content.
Other migrated reads reject explicit archive `--config` and Hub `--token-file`.
Exact server Envelope IDs/times survive rendering, complete page reconstruction
and inventory/revision consistency checks. See [decision 119](adr/decision-119.md),
[client migration](api-client.md#cli-migration-api-012) and
[candidate configuration](configuration.md#12-candidate-authority-validation-and-planning-api-012).

## Implemented maintenance resources (API-010)

API-010 extends the same strict authenticated POST boundary, keyed 202
`AcceptanceResponse`, bounded lane and exact-result observation to ten explicit
maintenance resources. The active task records actual validation evidence.
Every route rejects query parameters and unknown fields. The URL fixes preview
versus apply: no `apply`, `dry_run`, `mode`, `preview` or executable `plan` field
is accepted. Every route requires an idempotency key, including previews that
write control-state receipts while leaving the archive unchanged.

| Route under `/api/v1` | Strict JSON object | Role and locked behavior |
| --- | --- | --- |
| `POST /prune-plans` | `selectors`, default `[]` | R; current installed-policy preview, no archive lock |
| `POST /prunes` | Same selector body | W; fresh locked plan/apply, at most one eligible revision per selected repository |
| `POST /purge-plans` | `selectors`, default `[]`; `all_unmanaged`, default `false`; exactly one scope | R; unmanaged whole-repository preview, no archive lock |
| `POST /purges` | Same explicit scope body | W; fresh locked unmanaged scope/layout proof and per-repository transactions |
| `POST /recovery-plans` | Exactly `{}` | R; describe current recovery evidence/refusals, no archive lock |
| `POST /recoveries` | Exactly `{}` | W; reconstruct/validate recovery under lock, never execute a supplied plan |
| `POST /quarantine-plans` | Required `transaction_ids` array | R; prove the complete explicitly named batch, no archive lock |
| `POST /quarantine-cleanups` | Same explicit ID body | W; fresh locked batch proof/removal, no unrelated reconciliation |
| `POST /repairs` | Required `revision`; optional `reason`, default `operator_requested` | W; exact-SHA original-manifest repair under lock, using installed Hub authority |
| `POST /archive/initializations` | Required `archive_root`, `archive_id` and `confirm=true` | W plus enabled maintenance gate; restate configured authority, initialize only after its own locked checks |

Prune selectors follow sync's configured selection grammar and sorted distinct
canonical repository set, with at most 100 items of 256 characters; a valid SHA
suffix does not override installed policy. Purge uses whole-repository selectors
only and rejects any SHA suffix. Nonempty selectors and `all_unmanaged=true` are
mutually exclusive; empty selectors with false/missing `all_unmanaged` is invalid.
Configuration removal alone never purges anything, and an explicitly configured
target remains ineligible. Quarantine requires 1–100 explicit 32-lowercase-hex
transaction IDs, sorted/deduplicated before canonical hashing, not paths or an
implicit all-entries scope. Repair requires one
`TYPE:ID@` full lowercase 40-character SHA and at most 2,048 characters of audit
reason (empty text retains the existing CLI semantics); it accepts no endpoint,
credential or source-path override. The shared repair service redacts registered
credential values from the audit reason after resolving its installed Hub source
and before passing the reason to durable repair/audit writing.

Apply does not accept the preview payload, preview operation ID or client-provided
filesystem proof. It reacquires the shared service's archive lock, checks the
admitted fingerprint against freshly installed policy and repeats the operation's
guards/scope/evidence checks. A queued stale policy is a refusal before mutation;
a purge target becoming configured cannot acquire deletion authority from its
old preview. Quarantine proof covers every requested entry before any removal;
changed bytes, unknown files, repair evidence or unfinished transactions refuse
and remain preserved. Recovery ambiguity retains its diagnostic payload and
safety classification rather than guessing or initializing an archive.

Prune/purge retain the existing logical commit point: before it, recovery restores
content; afterwards it finishes audit/physical cleanup without republishing.
Canonical cache deletion uses supported Hub APIs, audits/original manifests stay
preserved and empty containers use `rmdir`. Repair reproduces original expectations,
reverifies a new publication instance before reference switches, preserves the
SHA's generation and keeps the predecessor at its locator through the grace period.
The separate documented RET-011 generation gap is not resolved by these routes.

### Initialization gate and observation

`maintenance_enabled=false` is the restart-only default and gates initialization
only. A disabled initialization POST is `HFAPI002`/403 before body reception or
POST retry handling, even when its key was bound before a restart. Original
lookup/status/events/result reads remain available. Other maintenance resources
retain their own capabilities/domain safeguards and do not require that switch.
Initialization additionally requires strict literal `confirm=true`, an absolute
`archive_root` normalized by the DTO and canonical UUID `archive_id` equal to the
installed configured values. The path is bounded to 4,096 UTF-8 bytes and refuses
dot/traversal components, backslashes and nonprintable characters. Malformed
path/UUID/confirmation is a 422 wire refusal; a valid but mismatched root/UUID
can be admitted but ends with the existing HFARG002 / exit 10 and no initialization.
This is redundant confirmation, never caller-selected root or UUID authority. Existing/unknown content, unsafe mounts and a pre-existing
sentinel remain domain refusals; the sentinel is written last. There is no implicit
initialization from startup, health, recovery, missing-sentinel diagnosis or
ordinary operations.

For an authenticated preview, a representative request is:

```http
POST /api/v1/purge-plans
Content-Type: application/json
Idempotency-Key: example-purge-preview

{"selectors":["model:retired/model-name"]}
```

An independently authorized `POST /api/v1/purges` uses only the same explicit scope
and a distinct deliberate operation key, after reviewing the current evidence.
Never copy the returned plan into the request. Quarantine preview uses, for example,
`{"transaction_ids":["0123456789abcdef0123456789abcdef"]}`; apply uses the separate
`/quarantine-cleanups` URL and proves the batch again. Repair uses
`{"revision":"model:organization/model-name@0123456789abcdef0123456789abcdef01234567","reason":"operator_requested"}`.
Initialization requires a deliberately provisioned throwaway/configured target,
the explicit server gate and all three required confirmation fields; these route
examples do not authorize initializing an existing production archive.

Every 202 is admission only. Poll status/events and retrieve the exact terminal
Envelope, including domain errors, partial recovery diagnostics and application
exit classification. Result HTTP 200 does not prove successful deletion/repair;
a refusal is still a failed Envelope. On lost acknowledgement, use the original
key's lookup, never a new key to repeat uncertain mutation. Restart never replays
receipts or reconstructs work from journals. No production operation or installed
host-hardening proof is supplied by hermetic HTTP/domain tests.

## Execution correlation (API-004)

[Decision 111](adr/decision-111.md) separates four identities without changing
schema-1 archive records. A trusted server boundary mints a fresh `request_id`
for each received request; caller headers cannot select the authoritative ID.
API-007 admission mints an independent `operation_id`, shared by its submission,
observation requests and execution. A domain `run_id` continues to identify the
CLI Envelope and any durable run report. A `transaction_id` continues to identify
one archive journal; a run may contain several transactions. These IDs use the
existing 32-lowercase-hex grammar. A request is not a run or a transaction, and
retrying or polling an operation does not mint a replacement domain identity.
API-007 receipts preserve domain relationships and the authenticated coarse
credential-class submitter; API-008 still owns actual execution propagation.

`ExecutionContext` holds the run ID and optional request/operation IDs.
Its `activate()` scope binds an immutable `ContextVar` correlation snapshot and
restores the prior scope after success or failure. Command services activate
their context; adapters must scope local query work too. `emit` captures that
snapshot in the log record when the event is emitted, so delayed formatting
cannot borrow another request's identity. Reserved event, level and correlation
fields supplied by a call site cannot override the captured values. Each service
thread submission copies its own context through `submit_with_context`; the
existing sync producer now uses the same boundary. Reused workers retain no
completed request scope.

`configure_daemon` installs one request-neutral handler and level at startup;
repeated startup calls are idempotent. Requests never call CLI `configure` or
reset handlers. Quiet/verbose preferences belong to client rendering and bounded
event selection, not a process-wide logger level. The isolated CLI retains its
per-invocation startup configuration and stderr-only event output.

Shared verification constructs no Hub client or credential and never changes
`os.environ`. The removed scoped offline toggle cannot affect concurrent work.
`offline.initialize_offline_process()` is the startup-only primitive for the
API-008 dedicated executor: call it before importing or using Hub libraries and retain
the flag for that process's lifetime. The helper does not deny IP sockets.
API-008 supplies the dedicated process/protocol and credential checks; API-014
must establish installed credential-free/no-IP hardening. No ASGI-process
verification fallback is permitted.

## Wire validation and errors

Wire models are separate from durable archive models. Forbid unknown keys,
coercion, conflicting modes, arbitrary paths, and oversized bodies, including
chunked bodies. Validate repository type/ID, full SHA, publication ID, run ID,
and transaction IDs with domain validators. Query strings have explicit
conversion to strict typed values. Bound strings, lists, query concurrency,
page sizes, report projections, and event buffers.

`ApiProblem` contains a request ID, stable code/message, and applicable exit
classification, never raw framework exception input or tracebacks. HTTP errors:
401 missing/invalid bearer with challenge; 403 wrong capability; 404 absent;
409 stale policy, conflicting key, or unfinished result; 422 invalid request;
503 full/draining/unavailable executor; 500 sanitized unexpected error. Unsupported
methods receive authenticated 405 with `HFAPI007`. Current read integrity
refusals use 409 and retain their domain HFVER code/exit classification.
A terminal failed domain Envelope is retrieved with HTTP 200 and retains its
application exit code (priority 40, 50, 30); HTTP success never means domain
success. New HFAPI client config/auth failures exit 10; unavailable or uncertain
execution exits 20.

The shared sanitizer removes sensitive keys, known Hub/bearer/signed-URL shapes
and exact registered credential values from diagnostic trees. Opaque tokens must
be registered when loaded, before use; arbitrary unknown strings cannot be
recognized as secrets. `Problem` snapshots sanitized diagnostics, and public
rendering plus exception string/repr paths sanitize again to cover late
registration or mutable legacy contexts. API-005 registers inbound API
credentials and API-006 applies the same boundary to response diagnostics and
validation/exception output.

Inventory, revisions, reports, operations, and events use bounded cursor pages
with deterministic ordering documented as each route lands. Clients walk all
pages to preserve complete legacy envelopes. Pages are not an archive-wide
snapshot. Ref/manifest reads pin exact publication identity; vanished instances
return a visible stale/absent result, never substitute a new current tree.
Existing large reports stream without unbounded duplicate buffers.

## Admission, idempotency, and lifecycle

Decisions [109](adr/decision-109.md) and [114](adr/decision-114.md) permit a
bounded non-resuming submission registry, separate from archive journals.
API-007 implements durable admission primitives and HTTP observation. API-008
supplies one heavyweight FIFO lane (16 pending by default), policy/lock
revalidation and private verification protocol/process primitives;
API-009/010 add command submissions. The bounded metadata pool and daemon-instance
lock already exist. Never hold the archive flock for daemon lifetime. The process
is single-worker without auto-reload; heavy work stays outside the ASGI event loop.

Side-effecting submissions require `Idempotency-Key`. Persist a restrictive
atomic JSON receipt under service-private `/var/lib/hfcache/api/` before 202 or
execution. Bind fixed credential-class principal identity and the SHA-256 key
digest to a canonical route/request digest and admitted policy fingerprint.
Persist no raw key, candidate body, bearer or credential source/digest in server
receipts. API-014's separate private scheduled-client handle retains only its
generated nonsecret key for observation; it changes no server receipt schema. The
receipt itself is the authoritative binding; indexes are derived. Matching
retries return the original operation before requesting a fresh policy snapshot,
even after policy changes; conflicting requests/routes return 409. Every
retry/lookup reauthenticates. Header-based lookup searches only the caller's
credential-class namespace, which survives credential rotation. It does not
submit work. All REST principals with read capability may observe any operation
metadata, events and results, just as they can read archive reports under AD-21.
An operation ID is never authentication.

The core key grammar is `1`–`128` ASCII characters from letters, digits,
`.`, `_`, `~`, `+` and `-`. Empty, whitespace, control or oversized keys fail
validation without echoing their value. Canonical request hashing uses the shared
deterministic JSON serializer over `{route, request}` with sorted keys and the
validated request mapping; the serialized comparison input is bounded to 8 MiB.
Object insertion order therefore does not change the digest; meaningful array
order and route identity do. It is never a hash of raw HTTP bytes and never
authorizes replaying the request. Public submission routes must validate strict
domain DTOs and require a key before calling admission.

For example, after losing an acknowledgement, an authenticated client sends
`GET /api/v1/operations/lookup` with the original `Idempotency-Key` header. It
does not resubmit or move the key into a URL. The core admission outcomes are:

| Retry condition | Outcome |
| --- | --- |
| Same credential class, key, route and validated request; object keys reordered | Original operation, no new policy lookup or admission |
| Same binding after installed policy changes or same-class credential rotation | Original admitted operation and fingerprint |
| Same class/key with a changed route or request | `HFAPI012`/409 conflict; no new operation |
| Same key under a different credential class | Separate namespace; lookup cannot find the first class's binding |
| Missing/expired history | `HFAPI013`/404 with unknown execution outcome; never automatic replay |

API-007 exposes non-submitting lookup; API-009 now provides the strict command
POST examples above; API-010 adds the same boundary to maintenance/initialization.

States: queued, waiting_lock, running, succeeded, failed, interrupted. Store the
exact terminal Envelope in a validated bounded result reference. Interrupted
means uncertain execution outcome and has no fabricated domain report. API-008
applies one absolute waiting deadline across queue, delegation and lock time,
reloads installed policy under the service-owned lock and refuses stale scope
before mutation without duplicate/nested lock acquisition. Verification delegates
to the private socket executor, which owns its lock through report/catalog
persistence. API-009/010 implement the command/maintenance resources above;
API-012 adds candidate HTTP and API-013 operational CLI integration.

Disconnect and Ctrl-C stop observation. They do not cancel accepted work. API-013
CLI clients emit the validated nonsecret key before mutation submission and operation
ID before waiting, even in quiet mode; stdout carries exactly one terminal
Envelope. Sequenced sanitized events are bounded application evidence, never
arbitrary journald output.

Shutdown stops admission, drains/joins workers, and preserves receipts. Restart
never automatically reruns old queued/running work. API-007 opens the store
without classification; an explicit `interrupt_unfinished()` primitive is
available. API-008 reconciles exact surviving workers before marking unresolved
nonterminal receipts interrupted: recover an exact durable terminal Envelope or
reattach/await an exactly identified live worker without re-execution. Missing or
unavailable proof retains uncertainty, never a fabricated report. PID, released
lock, elapsed time or disconnected client do not prove
completion. Terminal key/result retention defaults to 30 days. Count/byte caps
refuse new admission rather than evicting unexpired bindings. Nonterminal and
interrupted records retain their receipt/result space reservation; they never
expire. Ambiguous, malformed, unsafe and unknown-version records are preserved
and fail admission closed. Healthy validated IDs remain observable. Delete only
validated owned succeeded/failed history after expiry. Expired/missing history
is uncertainty, not proof of nonexecution or permission to replay. See the
independent [schema/compatibility contract](schemas.md#13-service-private-operation-control-state-api-007)
and [recovery runbook](recovery.md#10-operation-history-and-uncertain-submissions).

Unavailable/unsafe verifier status specifically preserves the parent's active
receipt and disables fresh execution across restarts, while metadata remains
observable. Only trusted missing/interrupted evidence permits parent interrupted
classification. A transport failure cannot be converted to an interrupted marker
that a subsequent startup would skip while reopening the lane. Restored exact
status resolves this barrier without replay.

### Heavy-lane execution boundary (API-008)

Only new durable admission can create runnable work; retrying/observing an old
operation cannot. The single FIFO lane bounds pending work separately from
metadata workers. Full/draining admission returns `HFAPI009`/503. One absolute
host-monotonic deadline consumes queue residence and the remaining service-owned
archive-lock wait. A deadline bounds waiting to start, not the duration of a
running sync/verification. The under-lock guard reloads installed policy and
compares the admitted fingerprint before mutation; the daemon never pre-locks a
service or passes a held lock to the verifier.

The default lane permits one active item plus `max_queued_operations` pending.
Zero waiting budget is an idle-lane single lock attempt and cannot queue behind
another item. Expiry before execution records a failed `HFAPI015` Envelope;
archive-lock timeout keeps `HFMNT010`, and an under-lock changed fingerprint keeps
`HFAPI007`. These terminal domain/admission results are later retrieved with
HTTP 200 and their original exit classification, not translated into fabricated
success. Immediate full/draining refusal is `HFAPI009`/503 without new work.
Observation timeouts do not cancel accepted execution.

Every non-estimate verification requires the configured private executor.
Fresh admission probes availability before persisting a new receipt; matching
idempotent retries return the old binding without a new probe. A probe never
submits work.
`HFAPI016`/503, exit 20, reports unavailable/untrusted socket, peer, frame or
executor evidence. No generic command/config/path/credential crosses that
protocol, and no production fallback executes verification in ASGI. The private
worker preserves the API operation ID in its own schema-1 receipt and returns
the exact domain Envelope. Status lookup never submits; matching retry never
double-starts. Exact trusted running progress updates the parent receipt's phase
and domain run ID. A private `running` label with no owned live execution thread
is unavailable evidence and keeps the execution barrier closed. OS no-IP
enforcement and socket-activated unit acceptance remain
API-014, not a property of the process's library offline flag. See
[wire/trust/deadline details](server.md#verification-wire-and-local-trust).

### Implemented operation observation (API-007)

Every route below requires a REST principal with `read` capability. Observation
uses the same bounded metadata pool, request/response safeguards and stream
leases as archive reads. It does not load a fresh archive-policy snapshot, call
any domain command, acquire the archive flock, admit work or change a receipt.
Healthy exact-ID history therefore remains available after an invalid policy
update or unrelated corrupt receipt. Collection/key-lookup scans refuse unsafe,
unsupported or unexplained state instead of silently dropping it.
Capabilities advertises `operation_history=true` and, since API-009,
`operations=true` for its implemented command routes. Roles still apply; this
flag does not imply candidate routes or full REST acceptance. API-010 includes
maintenance routes and advertises `maintenance_enabled` for initialization only.

| Route under `/api/v1` | `envelope.data` / behavior |
| --- | --- |
| `GET /operations` | `operations`: newest-first public metadata; supports `limit`/`cursor` only |
| `GET /operations/lookup` | `operation`: original receipt found by exactly one `Idempotency-Key` header in the caller's namespace; no query parameters |
| `GET /operations/{operation_id}` | `operation`: public metadata by validated server ID; no query parameters |
| `GET /operations/{operation_id}/result` | Exact stored terminal domain Envelope in the response's `envelope`; no query parameters |
| `GET /operations/{operation_id}/events` | `operation_id`, `events`, integer `next_cursor`, `oldest_sequence`, `truncated`; accepts only `after`/`limit` |

`OperationView` exposes `schema_version`, `operation_id`, coarse `principal`,
`route`, admitted `archive_id`/`config_fingerprint`, `state`, `created_at`,
`updated_at`, nullable `completed_at`/`domain_run_id`, `transaction_ids`,
`next_event_sequence` and `result_recorded`. It excludes the key and request
digests, result-file reference and inline events. The principal is `rest-writer`
or `rest-reader`, not a person's identity. No raw key or original request is
available for retrieval.

All routes use `ReadResponse`. Exact show/lookup/events/result responses carry
the receipt's admitted archive UUID/fingerprint, even if installed policy later
changes. A collection uses the startup-pinned configured UUID and null wrapper
fingerprint; each item retains its own admitted identity. Ordinary observation
Envelopes identify the current request. The result endpoint preserves the stored
domain Envelope/run ID/exit classification: HTTP 200 can contain a failed domain
result. A known queued/waiting/running/interrupted receipt without a result returns
`HFAPI015`/409, exit 20; absent/expired history returns `HFAPI013`/404, exit 20.
It never invents an empty successful result. Invalid IDs/header/query input is
`HFAPI006`/422 without echoing input. Unsafe/unavailable/unexplained storage is
`HFAPI014`/503, exit 20.
API-014 also uses HFAPI014 / exit 20 locally for unsafe/malformed/future/mismatched
scheduled observation handles; that client refusal is not an HTTP response.

Collection ordering is descending `(created_at, operation_id)`. Its default
limit is 100, bounded by `max_page_size`; its opaque cursor binds ordered IDs
and the daemon instance. Changed membership/order or a restart invalidates
continuation with `HFAPI007`/409. Receipt fields can change between pages without
changing membership, so this is not a frozen history snapshot. Start a fresh walk
after a stale cursor. Collection cursors are distinct from event sequences.

For events, `after` is a nonnegative decimal sequence (default `0`); `limit`
defaults to the minimum of `100`, `max_page_size` and `operation_max_events` and
cannot exceed either configured ceiling. Both are single ASCII decimal values
of at most ten digits. Events are returned in increasing sequence after `after`.
`next_cursor` is the last returned sequence, or the supplied `after` if empty;
pass it as the next `after`. `oldest_sequence` identifies the first retained
sequence, or the next sequence if no event exists. `truncated=true` explicitly
reports a gap when the caller's cursor predates the retained suffix. Event
retention is bounded independently of the receipt/key window; clients must
present a gap honestly rather than fabricate progress. No long-poll, SSE,
WebSocket, raw journal stream or cancellation endpoint is added.

Result reads validate the referenced file's bytes/hash/identity and schema-1
Envelope before streaming with the existing bounded JSON encoder/lease. Source
bytes are capped by `operation_max_result_bytes`; normal metadata uses
`max_response_bytes`, and encoded result responses use the existing large-evidence
ceiling of eight times `max_artifact_bytes`. No endpoint serves arbitrary control
files. The independent [durable schema](schemas.md#13-service-private-operation-control-state-api-007)
records file ownership, transitions, event/result bounds and compatibility.

## Credentials and configuration

API-005 supplies strict configuration, credential loading, fixed capability
principals and a reusable FastAPI bearer adapter. API-006 authenticates all
metadata HTTP routes/errors/schema/docs and applies transport bounds. API-009/010
extend those controls to keyed command/maintenance jobs. API-012 adds candidate
operations and reader integration. MCP-001 supplies optional authenticated
transport only; curated tools and installed-host acceptance retain their gates.

| Credential class | Accepted interface | Core capability | REST read | REST write |
| --- | --- | --- | --- | --- |
| REST writer | REST | `read`, `write` | authorized | authorized, subject to maintenance/domain gates |
| REST reader | REST | `read` | authorized | 403 `HFAPI002` |
| MCP reader | Enabled MCP only | `mcp-read` | 401 `HFAPI001` | 401 `HFAPI001` |
| Absent, invalid or malformed bearer | none | none | 401 `HFAPI001` | 401 `HFAPI001` |

Capabilities do not register MCP tools or bypass the initialization gate,
locked scope/evidence checks or domain refusal. Only enabled MCP accepts its
distinct credential; REST credentials cannot access that mount.
Cross-interface credentials are rejected as unauthenticated. Missing,
malformed and invalid authentication uses the same safe detail `Not authenticated`
and `WWW-Authenticate: Bearer realm="hfcache"`; capability refusal is `Forbidden`.
Active configured missing/unsafe/racing/malformed API credentials are startup
`HFAPI003`; duplicate active class values are `HFAPI004`. Disabled MCP never
reads its inert optional source. All four codes retain
the exit-10 authentication/configuration classification. No raw bearer or
credential-derived principal identifier is returned.

Separate strict versioned archive, server, and client config domains. Server
transport/auth changes require restart. Each request/admission freezes a freshly
loaded archive policy and nonsecret fingerprint; root/UUID changes fail closed
until restart. Invalid new policy fails archive operations while health/version
remain diagnostic. Candidate content is bounded TOML, never a server path.
Planning requires installed root/UUID/Hub/credential authority; only the installed
credential is resolved. Validation does not install a candidate.

Distinct protected bearer files/systemd credentials for REST writer, optional
REST reader, and later MCP reader. Reject duplicates, bound lengths, validate
ownership/type/mode, compare in constant time, redact opaque tokens everywhere.
API-005 opens credential files through pinned no-follow descriptors, validates
root/effective-user ownership, one hardlink and explicit protected modes, then
compares fixed-size digests over all three slots. Unconfigured optional classes
authorize nobody; every configured source must load. The
[server contract](server.md#implemented-credential-and-capability-boundary-api-005)
states token grammar/limits, file policy, rotation and exact configuration keys.
No ambient discovery or credential forwarding. Unix sockets still authenticate.
Local default socket is `/run/hfcache/api.sock`; TCP defaults loopback. Off-host
access requires verified TLS or an explicitly trusted local TLS proxy. Validate
Host/Origin, disallow wildcard CORS, URL userinfo and token queries, and explicitly
configure trusted proxies. Every reader is authorized for the entire archive
(AD-21); no per-repository ACL claim.

## Independent typed client (API-011)

[The client contract](api-client.md) defines separate strict reader settings,
explicit endpoint/API credential precedence, verified TLS/Unix transport and
finite response/page/retry/poll observation. It uses the base HTTPX dependency
without archive TOML/mount/Hub credentials or optional server/MCP frameworks.
Constructor setup makes no request; explicit capabilities negotiation refuses
unsupported versions/needed capabilities rather than guessing.

Strict client wire models preserve wrapper/request identity, admitted operation
UUID/fingerprint and exact domain Envelope/run classification. Page iteration pins
archive/policy/command while allowing per-page request identities; exact same-
operation status/result/event links cannot redirect bearer authority. No automatic
POST replay or new-key retry follows lost acknowledgement. HFAPI017/018 classify
client configuration/protocol at exit 10; HFAPI019/020 classify connectivity/
uncertain submission at exit 20, retaining existing server/domain codes.

API-012 uses the global choices for public reader/candidate modes, completing all
29 HTTP parity rows; API-013 completes command/operation UX. These integrations
change no durable shape, writer authority or MCP gate. See
[decision 118](adr/decision-118.md) and [decision 119](adr/decision-119.md).

## CLI admission and observation (API-013)

The CLI has no direct operational mutation backend. Pure shared request types
select fixed typed resources and preserve server-owned archive/credential/lock/
recovery/private-verifier authority. Default command output waits for the exact
terminal Envelope. Show/lookup preserve existing metadata Envelopes, while wait
returns the original stored command result. Distinct domain run, operation and
request identities are never substituted.

Explicit detach is client presentation, not a new server or durable format:
schema 1, `kind="operation_admission"`, original `idempotency_key` and exact
validated `acceptance`. It has no fabricated terminal outcome/exit. Safety handles
appear on stderr even quiet, before POST and before waiting respectively. Bounded
sanitized event/status/result observations share an absolute finite deadline;
timeout/Ctrl-C retains handles and may leave accepted work running. No automatic
replay/cancel/new-key retry follows client loss. Existing HFAPI013/015/018–020 and
exact terminal domain classifications retain their meaning.

Initialization's optional CLI UUID comes from authenticated configured-target
inspection, never local archive config. A supplied UUID must match; root and
confirmation remain explicit. The server DTO still requires strict restated
root/UUID/confirmation and its initialization-only maintenance gate. No-confirm
CLI refusal submits nothing, preserving failed server inspection exactly or using
local refusal metadata with successful inspection evidence. See
[decision 120](adr/decision-120.md), [CLI operations](cli.md#operations) and
[client resume](api-client.md#submit-detach-and-resume-api-013).

## Acceptance boundaries

[Server contract](server.md) owns deployment/lifecycle detail. API-016 requires
complete REST, CLI, Cockpit, packaging and offline build acceptance before MCP
code, dependencies, imports or endpoints are added. A 29-mode matrix is separate
from the independent 34 method/path security inventory (33 with interactive docs
disabled); both must remain complete. Invalid bearers authenticate before body
reception on every route, including docs/schema/error surfaces. Mixed candidate/
probing roles cannot admit work before their capability check.

Concrete gate evidence lives in the [parity manifest](../tests/rest_parity.py),
[route-complete security tests](../tests/unit/test_rest_security_gate.py),
[actual Unix/TCP/OpenAPI tests](../tests/unit/test_rest_transport_gate.py),
[complete paged-reader tests](../tests/unit/test_rest_pagination_gate.py) and
[example/docs/disabled-import tests](../tests/unit/test_rest_examples_gate.py).
Pagination includes size-one pages, empty/unmanaged inventory and exact identity;
it never claims an archive-wide snapshot. Prefix spelling does not change the
canonical operation route/key binding: native/public retries return the original
operation and admitted fingerprint, while links use the current trusted request
prefix. Public/native OpenAPI views are deterministic without mutating shared
schema state.

All five current examples use their strict independent loaders, without resolving
credentials, contacting the Hub/API, opening the archive or starting listeners:

| Example | Domain/loader |
| --- | --- |
| [Archive policy](../examples/config.toml) | `ApplicationConfig` through `load_config` |
| [Server](../packaging/server.toml) | `ServerConfig` through `load_server_config` |
| [Reader](../packaging/client.example.toml) | `ClientConfig` through `resolve_client_config` |
| [Scheduled client](../packaging/scheduled-client.example.toml) | Same client schema, explicit expected UUID required at execution |
| [Cockpit client](../packaging/cockpit-client.toml) | Same client schema, API-only named credential |

Example parse success does not provision credentials, prove UUID/sentinel identity
or authorize installation. Placeholder endpoint/source/UUID values require
operator selection. API-016 runs fresh `scripts/check.sh --with-build`, complete
Cockpit and isolated locked base/server wheel checks, actual local sockets and
old/current parser compatibility. A cold disabled app imports no MCP and creates
no archive/control state. The task records actual counts and results; prior
package counts do not stand in for fresh acceptance.

Installed systemd activation, cgroup no-IP/credential-source masking (including
custom paths), hardening, browser/PAM bridge, SELinux/NFS, executor drain and
verify-calendar approval remain explicit [operator holds](progress.md#operator-handoff).
Repository fixtures do not pass them. This plan authorizes no production operation
or deployment.

## Optional MCP interface (MCP-001)

MCP is separate from the REST operation matrix and never converts its OpenAPI
into tools. After committed REST acceptance the optional `/mcp` transport shares
one app/lifespan, preserves transport checks and accepts only the distinct MCP
reader credential. Disabled mode imports/resolves neither its package nor its
credential. No tool/resources/prompts or job execution is added by MCP-001;
MCP-002 owns curated read services and side-effect proof. Protocol messages are
MCP wire objects, not fabricated REST domain Envelopes or admission receipts.
See [the MCP contract](mcp.md) and [decision 124](adr/decision-124.md).
