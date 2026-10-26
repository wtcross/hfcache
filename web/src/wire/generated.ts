/** Generated from source digest 4f3b1b07176239b5a5e40975a04544379b50fc37b69a80ac20fcecf4b256ef63. Run generate:wire; do not edit. */
export const WIRE_SOURCE_DIGEST =
    "4f3b1b07176239b5a5e40975a04544379b50fc37b69a80ac20fcecf4b256ef63";
import {
    wireObject,
    wireRequestObject,
    wireArray,
    wireString,
    wireInteger,
    wireNumber,
    wireBoolean,
    wireNull,
    wireLiteral,
    wireUnion,
    wireJsonValue,
} from "./runtime";
import type { JsonObject } from "./runtime";
import { WireError } from "./json";
import { applySemantic } from "./semantics";
function checked<T>(value: T, ids: readonly string[]): T {
    for (const id of ids) applySemantic(id, value);
    return value;
}
export type Acceptance = {
    readonly ["schema_version"]: number;
    readonly ["request_id"]: string;
    readonly ["archive_id"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["operation"]: ClientOperation;
    readonly ["created"]: boolean;
    readonly ["links"]: ClientLinks;
};
export type ApiProblem = ClientProblem;
export type AreaFindingPayload = {
    readonly ["age_hours"]: number;
    readonly ["area"]: string;
    readonly ["path"]: string;
    readonly ["stale"]: boolean;
    readonly ["transaction_id"]: string;
};
export type CandidateInvalidPayload = {
    readonly ["valid"]: false;
    readonly ["syntax_valid"]: false;
    readonly ["authority_compatible"]: null;
    readonly ["authority_mismatches"]: readonly string[];
    readonly ["installed_policy_valid"]: boolean;
};
export type CandidateValidPayload = {
    readonly ["config_fingerprint"]: string;
    readonly ["enabled_repositories"]: number;
    readonly ["repositories"]: number;
    readonly ["token_source"]: string;
    readonly ["valid"]: true;
    readonly ["syntax_valid"]: true;
    readonly ["authority_compatible"]: boolean | null;
    readonly ["authority_mismatches"]: readonly string[];
    readonly ["installed_policy_valid"]: boolean;
};
export type Capabilities = {
    readonly ["api_version"]: number;
    readonly ["credential_class"]: "rest-writer" | "rest-reader";
    readonly ["capabilities"]: readonly ("read" | "write")[];
    readonly ["instance_id"]: string;
    readonly ["reads"]: boolean;
    readonly ["operations"]: boolean;
    readonly ["operation_history"]: boolean;
    readonly ["mcp"]: boolean;
    readonly ["maintenance_enabled"]: boolean;
    readonly ["max_page_size"]: number;
};
export type CatalogCoverage = {
    readonly ["repositories"]: number;
    readonly ["tags_known"]: number;
    readonly ["tags_unknown"]: number;
    readonly ["publications"]: number;
    readonly ["usable"]: number;
    readonly ["partial"]: number;
    readonly ["unsupported"]: number;
    readonly ["failed"]: number;
    readonly ["missing"]: number;
    readonly ["technical_required"]: boolean;
    readonly ["incomplete"]: boolean;
};
export type CatalogDetailPayload = {
    readonly ["schema_version"]: 1;
    readonly ["catalog_identity"]: string;
    readonly ["coverage"]: CatalogCoverage;
    readonly ["entry"]: CatalogEntry;
    readonly ["observations"]: readonly ObservationSummary[];
};
export type CatalogEntry = {
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["repository_id"]: string;
    readonly ["tags"]: readonly string[];
    readonly ["tag_origin"]: "configured" | "last_observed" | "unknown";
    readonly ["tag_observed_at"]: string | null;
    readonly ["curation_fingerprint"]: string | null;
    readonly ["configured"]: boolean;
    readonly ["enabled"]: boolean | null;
    readonly ["archived"]: boolean;
    readonly ["matching_variant_count"]: number;
    readonly ["representative_variant"]: QualifiedVariant | null;
    readonly ["dataset_formats"]: readonly string[];
};
export type CatalogFacetPayload = {
    readonly ["schema_version"]: 1;
    readonly ["catalog_identity"]: string;
    readonly ["coverage"]: CatalogCoverage;
    readonly ["facet"]:
        "tag" | "format" | "quantization_method" | "quantization";
    readonly ["total_matches"]: number;
    readonly ["entries"]: readonly CatalogFacetValue[];
};
export type CatalogFacetValue = {
    readonly ["value"]: string;
    readonly ["repository_count"]: number;
};
export type CatalogRefreshResult = {
    readonly ["schema_version"]: 1;
    readonly ["state"]: "complete" | "partial" | "failed";
    readonly ["archive_id"]: string;
    readonly ["revision_scope"]: "current" | "retained";
    readonly ["tags"]: boolean;
    readonly ["technical"]: boolean;
    readonly ["curation_fingerprint"]: string;
    readonly ["curation_observed_at"]: string;
    readonly ["counts"]: RefreshCounts;
    readonly ["repositories"]: readonly RepositoryRefresh[];
};
export type CatalogSearchPayload = {
    readonly ["schema_version"]: 1;
    readonly ["catalog_identity"]: string;
    readonly ["coverage"]: CatalogCoverage;
    readonly ["total_matches"]: number;
    readonly ["entries"]: readonly CatalogEntry[];
};
export type CatalogVariantsPayload = {
    readonly ["schema_version"]: 1;
    readonly ["catalog_identity"]: string;
    readonly ["coverage"]: CatalogCoverage;
    readonly ["total_matches"]: number;
    readonly ["entries"]: readonly QualifiedVariant[];
};
export type ClientEvent = {
    readonly ["schema_version"]: number;
    readonly ["sequence"]: number;
    readonly ["at"]: string;
    readonly ["kind"]: string;
    readonly ["message"]: string;
};
export type ClientEvents = {
    readonly ["operation_id"]: string;
    readonly ["events"]: readonly ClientEvent[];
    readonly ["next_cursor"]: number;
    readonly ["oldest_sequence"]: number;
    readonly ["truncated"]: boolean;
};
export type ClientLinks = {
    readonly ["status"]: string;
    readonly ["result"]: string;
    readonly ["events"]: string;
};
export type ClientOperation = {
    readonly ["schema_version"]: number;
    readonly ["operation_id"]: string;
    readonly ["principal"]: "rest-writer" | "rest-reader";
    readonly ["route"]: string;
    readonly ["archive_id"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["state"]:
        | "queued"
        | "waiting_lock"
        | "running"
        | "succeeded"
        | "failed"
        | "interrupted";
    readonly ["created_at"]: string;
    readonly ["updated_at"]: string;
    readonly ["completed_at"]: string | null;
    readonly ["domain_run_id"]: string | null;
    readonly ["transaction_ids"]: readonly string[];
    readonly ["next_event_sequence"]: number;
    readonly ["result_recorded"]: boolean;
};
export type ClientProblem = {
    readonly ["request_id"]: string;
    readonly ["code"]: string;
    readonly ["message"]: string;
    readonly ["exit_code"]: number;
};
export type ClientRead = {
    readonly ["schema_version"]: number;
    readonly ["request_id"]: string;
    readonly ["archive_id"]: string | null;
    readonly ["config_fingerprint"]: string | null;
    readonly ["envelope"]: Envelope;
    readonly ["next_cursor"]: string | null;
};
export type ConfigApplicationOutcome = {
    readonly ["schema_version"]: 1;
    readonly ["archive_id"]: string;
    readonly ["operation_id"]: string;
    readonly ["request_digest"]: string;
    readonly ["base_revision"]: string | null;
    readonly ["candidate_revision"]: string | null;
    readonly ["config_fingerprint"]: string | null;
    readonly ["state"]:
        | "staged"
        | "unchanged"
        | "installed_unconfirmed"
        | "confirmed"
        | "conflict"
        | "unknown";
    readonly ["pending"]: boolean;
};
export type ConfigRead = {
    readonly ["schema_version"]: 1;
    readonly ["archive_id"]: string;
    readonly ["base_revision"]: string;
    readonly ["editable"]: EditableConfig;
    readonly ["editable_fields"]: readonly string[];
    readonly ["protected_fields"]: readonly ProtectedField[];
};
export type DependencyObservation = {
    readonly ["confidence"]: "high" | "medium" | "low";
    readonly ["declared"]: boolean;
    readonly ["detected_id"]: string;
    readonly ["managed"]: boolean;
    readonly ["source_field"]: string;
    readonly ["source_file"]: string;
};
export type DiagnosticCheckPayload = {
    readonly ["detail"]: string;
    readonly ["name"]: string;
    readonly ["outcome"]: "pass" | "fail" | "skipped";
};
export type DiagnosticsPayload = {
    readonly ["checks"]: readonly DiagnosticCheckPayload[];
};
export type EditableConfig = {
    readonly ["storage"]: EditableStorage;
    readonly ["sync"]: EditableSync;
    readonly ["verification"]: EditableVerification;
    readonly ["repair"]: EditableRepair;
    readonly ["repositories"]: readonly RepositoryConfig[];
};
export type EditableRepair = {
    readonly ["retired_instance_grace_hours"]: number;
};
export type EditableStorage = {
    readonly ["publication_mode"]: "hardlink" | "copy";
    readonly ["minimum_free_space_gib"]: number;
    readonly ["minimum_free_space_percent"]: number;
    readonly ["maximum_revisions"]: number;
};
export type EditableSync = {
    readonly ["max_workers"]: number;
    readonly ["lock_wait_seconds"]: number;
    readonly ["continue_on_repository_error"]: boolean;
    readonly ["dependency_policy"]: "warn";
    readonly ["stale_staging_age_hours"]: number;
};
export type EditableVerification = { readonly ["lock_wait_seconds"]: number };
export type EmptyPayload = Readonly<Record<string, never>>;
export type Envelope = {
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["data"]: JsonObject;
    readonly ["errors"]: readonly EnvelopeProblem[];
    readonly ["exit_code"]: number;
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["run_id"]: string;
    readonly ["schema_version"]: number;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly EnvelopeProblem[];
};
export type EnvelopeProblem = {
    readonly ["code"]: string;
    readonly ["context"]: JsonObject;
    readonly ["message"]: string;
    readonly ["repository"]: string | null;
};
export type EstimatePayload = {
    readonly ["estimated_duration_seconds"]: number | null;
    readonly ["measured_throughput_bytes_per_second"]: number | null;
    readonly ["mode"]: "estimate";
    readonly ["repositories"]: number;
    readonly ["revisions"]: number;
    readonly ["storage_maintenance"]: "undetectable";
    readonly ["unique_bytes"]: number;
    readonly ["unique_objects"]: number;
    readonly ["unreadable_objects"]: number;
};
export type FileEntry = {
    readonly ["path"]: string;
    readonly ["provenance"]: FileProvenance;
    readonly ["sha256"]: string;
    readonly ["size"]: number;
    readonly ["upstream"]: UpstreamIdentifiers;
};
export type FileProvenance = {
    readonly ["cache_root"]: "canonical" | "repair";
    readonly ["hash_reused_from"]: HashReuse | null;
    readonly ["hashed"]: boolean;
    readonly ["source"]: "hub_download" | "cache_reuse" | "repair_download";
};
export type Finding = {
    readonly ["commit_sha"]: string | null;
    readonly ["expected"]: string | null;
    readonly ["kind"]:
        | "missing"
        | "extra"
        | "size_mismatch"
        | "digest_mismatch"
        | "not_regular"
        | "unreadable"
        | "ref_invalid"
        | "manifest_invalid";
    readonly ["observed"]: string | null;
    readonly ["path"]: string | null;
    readonly ["publication_id"]: string | null;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
};
export type FullVerificationSummary = {
    readonly ["completed_at"]: string;
    readonly ["duration_seconds"]: number;
    readonly ["outcome"]: "clean" | "failed";
    readonly ["report"]: string;
    readonly ["started_at"]: string;
    readonly ["throughput_bytes_per_second"]: number;
    readonly ["unique_bytes"]: number;
    readonly ["unique_objects"]: number;
};
export type HashReuse = {
    readonly ["commit_sha"]: string;
    readonly ["publication_id"]: string;
};
export type HealthPayload = ReadyHealthPayload | UnavailableHealthPayload;
export type HostBinding = {
    readonly ["deployment_sha256"]: string;
    readonly ["policy_sha256"]: string;
    readonly ["release_version"]: string;
    readonly ["source_commit"]: string;
    readonly ["source_snapshot_sha256"]: string;
    readonly ["source_dirty"]: boolean;
    readonly ["archive_id"]: string;
    readonly ["archive_root"]: "/srv/hfcache";
};
export type HostFacts = {
    readonly ["guard"]: "held" | "absent" | "inactive";
    readonly ["archive_mount"]:
        "nfs-ro" | "nfs-rw" | "local-ro" | "local-rw" | "absent";
    readonly ["units"]: {
        readonly ["hfcache-sync.service"]: HostUnitState;
        readonly ["hfcache-sync.timer"]: HostUnitState;
        readonly ["hfcache-verify.service"]: HostUnitState;
        readonly ["hfcache-verify.timer"]: HostUnitState;
    };
    readonly ["sync_schedule"]: HostSyncSchedule;
};
export type HostPermissionReasons = {
    readonly ["archive"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
    readonly ["hub"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
    readonly ["control"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
    readonly ["schedule"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
    readonly ["configuration"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
    readonly ["observer"]:
        | "granted"
        | "policy-denied"
        | "guard-held"
        | "profile-unproved"
        | "authority-unknown"
        | "helper-unavailable";
};
export type HostPermissions = {
    readonly ["archive"]: boolean;
    readonly ["hub"]: boolean;
    readonly ["control"]: boolean;
    readonly ["schedule"]: boolean;
    readonly ["configuration"]: boolean;
    readonly ["observer"]: boolean;
};
export type HostStatus = {
    readonly ["schema_version"]: 1;
    readonly ["state"]: "supported" | "guarded" | "unknown" | "unavailable";
    readonly ["reason"]:
        | (
              | "helper-disabled"
              | "helper-unavailable"
              | "helper-timeout"
              | "helper-refused"
              | "helper-busy"
              | "policy-missing"
              | "policy-invalid"
              | "deployment-unverified"
              | "facts-unavailable"
              | "guard-unconfirmed"
              | "key-missing"
              | "key-invalid"
              | "config-unavailable"
          )
        | null;
    readonly ["profile"]: ("native" | "rootless") | null;
    readonly ["binding"]: HostBinding | null;
    readonly ["permissions"]: HostPermissions;
    readonly ["permission_reasons"]: HostPermissionReasons;
    readonly ["facts"]: HostFacts | null;
};
export type HostSyncSchedule = {
    readonly ["state"]: "observed" | "unavailable";
    readonly ["reason"]: ("profile-unproved" | "facts-unavailable") | null;
    readonly ["revision"]: string | null;
    readonly ["source"]: ("default" | "managed") | null;
    readonly ["on_calendar"]: string | null;
    readonly ["randomized_delay_sec"]: string | null;
};
export type HostUnitState = {
    readonly ["load"]: "loaded" | "masked" | "not-found";
    readonly ["active"]: "active" | "inactive" | "failed";
    readonly ["unit_file"]:
        | "enabled"
        | "enabled-runtime"
        | "disabled"
        | "static"
        | "linked"
        | "linked-runtime"
        | "masked"
        | "masked-runtime"
        | "not-found";
};
export type InitializationPayload = {
    readonly ["adopted_published"]: boolean;
    readonly ["archive_id"]: string;
    readonly ["archive_root"]: string;
    readonly ["created_directories"]: readonly string[];
    readonly ["removed_temporaries"]: readonly string[];
    readonly ["sentinel"]: string;
};
export type InspectionPayload = {
    readonly ["adopted_published"]: boolean;
    readonly ["archive_id"]: string | null;
    readonly ["archive_root"]: string;
    readonly ["existing_directories"]: readonly string[];
    readonly ["initializable"]: boolean;
    readonly ["leftover_temporaries"]: readonly string[];
    readonly ["missing_directories"]: readonly string[];
    readonly ["mount"]: MountPayload;
    readonly ["state"]:
        "uninitialized" | "partially_initialized" | "initialized" | "unusable";
    readonly ["unknown_entries"]: readonly string[];
    readonly ["unknown_entry_count"]: number;
};
export type InstalledValidationPayload = {
    readonly ["config_fingerprint"]: string;
    readonly ["enabled_repositories"]: number;
    readonly ["repositories"]: number;
    readonly ["token_source"]: string;
};
export type ManagedAssessment = {
    readonly ["schema_version"]: 1;
    readonly ["archive_id"]: string;
    readonly ["base_revision"]: string;
    readonly ["candidate_revision"]: string;
    readonly ["required_selectors"]: readonly string[];
    readonly ["complete"]: boolean;
    readonly ["sizing"]: PlanPayload | null;
};
export type ManagedValidation = {
    readonly ["schema_version"]: 1;
    readonly ["archive_id"]: string;
    readonly ["base_revision"]: string;
    readonly ["candidate_revision"]: string;
    readonly ["required_selectors"]: readonly string[];
    readonly ["valid"]: true;
};
export type ManifestPayload = {
    readonly ["manifest"]: RevisionManifest;
    readonly ["tree_base"]: "archive-root/";
};
export type ModelVariant = {
    readonly ["variant_id"]: string;
    readonly ["format"]: string;
    readonly ["encoding"]: string | null;
    readonly ["quantization"]: string | null;
    readonly ["quantization_method"]: string | null;
    readonly ["bits"]: number | null;
    readonly ["group_size"]: number | null;
    readonly ["role"]:
        "primary" | "adapter" | "projector" | "auxiliary" | "unknown";
    readonly ["members"]: readonly VariantMember[];
    readonly ["total_bytes"]: number | null;
    readonly ["completeness"]: "complete" | "incomplete" | "unknown";
    readonly ["evidence"]: "header" | "declaration" | "filename";
    readonly ["source_paths"]: readonly string[];
    readonly ["diagnostics"]: readonly string[];
};
export type MountPayload = {
    readonly ["exists"]: boolean;
    readonly ["filesystem_type"]: string | null;
    readonly ["is_mount_point"]: boolean;
    readonly ["read_only"]: boolean | null;
    readonly ["source"]: string | null;
};
export type ObservationSummary = {
    readonly ["commit_sha"]: string;
    readonly ["publication_id"]: string;
    readonly ["publication_generation"]: number;
    readonly ["extractor_version"]: string;
    readonly ["observed_at"]: string;
    readonly ["status"]: "complete" | "partial" | "unsupported" | "failed";
    readonly ["sources"]: readonly SourceObservation[];
    readonly ["dataset_formats"]: readonly string[];
    readonly ["diagnostics"]: readonly string[];
};
export type OperationPayload = { readonly ["operation"]: ClientOperation };
export type OperationsPayload = {
    readonly ["operations"]: readonly ClientOperation[];
};
export type PlanPayload = {
    readonly ["repositories"]: readonly PlannedRepositoryPayload[];
};
export type PlanResultPayload = PlanPayload | ManagedAssessment;
export type PlannedRepositoryPayload = {
    readonly ["enabled"]: boolean;
    readonly ["estimated_new_bytes"]: number | null;
    readonly ["file_count"]: number | null;
    readonly ["logical_bytes"]: number | null;
    readonly ["projected_publication_bytes"]: number | null;
    readonly ["publication_mode"]: "hardlink" | "copy";
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["requested_revision"]: string;
    readonly ["resolved_commit_sha"]: string | null;
    readonly ["upstream_state"]:
        | "unknown"
        | "available"
        | "missing"
        | "forbidden"
        | "refused"
        | "unresolvable"
        | "unreachable";
};
export type ProtectedField = {
    readonly ["field"]: string;
    readonly ["description"]: string;
};
export type PrunePayload = {
    readonly ["plans"]: readonly PrunePlan[];
    readonly ["applied"]: readonly PrunedRevisionRecord[];
};
export type PrunePlan = {
    readonly ["schema_version"]: number;
    readonly ["cache_revisions_to_delete"]: readonly string[];
    readonly ["current"]: RevisionSummary;
    readonly ["generated_at"]: string;
    readonly ["plan_id"]: string;
    readonly ["reason"]: "sixth_unique_revision_published";
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["retained"]: readonly RevisionSummary[];
    readonly ["selected"]: PruneSelection;
    readonly ["unique_bytes_released_estimate"]: number;
};
export type PruneSelection = {
    readonly ["commit_sha"]: string;
    readonly ["file_count"]: number;
    readonly ["logical_bytes"]: number;
    readonly ["manifest"]: string;
    readonly ["publication_generation"]: number;
    readonly ["publication_id"]: string;
    readonly ["tree"]: string;
};
export type PrunedRevision = {
    readonly ["commit_sha"]: string;
    readonly ["logical_bytes"]: number;
    readonly ["publication_generation"]: number;
};
export type PrunedRevisionRecord = {
    readonly ["schema_version"]: number;
    readonly ["commit_sha"]: string;
    readonly ["file_count"]: number;
    readonly ["logical_bytes"]: number;
    readonly ["manifest_archived_at"]: string;
    readonly ["plan_id"]: string;
    readonly ["publication_generation"]: number;
    readonly ["publication_id"]: string;
    readonly ["pruned_at"]: string;
    readonly ["reason"]:
        | "sixth_unique_revision_published"
        | "operator_requested_repository_purge";
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["retained_after"]: readonly RevisionSummary[];
    readonly ["transaction_id"]: string;
    readonly ["tree"]: string;
};
export type PublicationRefresh = {
    readonly ["commit_sha"]: string;
    readonly ["publication_id"]: string;
    readonly ["publication_generation"]: number;
    readonly ["write_status"]: "written" | "failed";
    readonly ["observation_status"]:
        ("complete" | "partial" | "unsupported" | "failed") | null;
    readonly ["observed_at"]: string | null;
    readonly ["manifest_digest"]: string | null;
    readonly ["error_code"]: string | null;
};
export type PurgePayload = {
    readonly ["plans"]: readonly PurgePlan[];
    readonly ["applied"]: readonly PrunedRevisionRecord[];
};
export type PurgePlan = {
    readonly ["schema_version"]: number;
    readonly ["cache_revisions_to_delete"]: readonly string[];
    readonly ["current"]: RevisionSummary;
    readonly ["generated_at"]: string;
    readonly ["plan_id"]: string;
    readonly ["reason"]: "operator_requested_repository_purge";
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["revisions"]: readonly PruneSelection[];
    readonly ["unique_bytes_released_estimate"]: number;
};
export type QualifiedVariant = {
    readonly ["commit_sha"]: string;
    readonly ["publication_id"]: string;
    readonly ["publication_generation"]: number;
    readonly ["variant"]: ModelVariant;
};
export type QuarantineAppliedPayload = {
    readonly ["transaction_id"]: string;
    readonly ["repository"]: string;
    readonly ["quarantine_path"]: string;
    readonly ["recovery_transaction_id"]: string;
    readonly ["files"]: readonly QuarantineFilePayload[];
    readonly ["directories"]: readonly string[];
    readonly ["logical_bytes"]: number;
    readonly ["already_absent"]: boolean;
    readonly ["removed_files"]: number;
    readonly ["removed_directories"]: number;
    readonly ["removed_logical_bytes"]: number;
};
export type QuarantineFilePayload = {
    readonly ["path"]: string;
    readonly ["size"]: number;
    readonly ["sha256"]: string;
    readonly ["retained_path"]: string;
};
export type QuarantinePayload = {
    readonly ["plans"]: readonly QuarantinePlanPayload[];
    readonly ["applied"]: readonly QuarantineAppliedPayload[];
};
export type QuarantinePlanPayload = {
    readonly ["transaction_id"]: string;
    readonly ["repository"]: string;
    readonly ["quarantine_path"]: string;
    readonly ["recovery_transaction_id"]: string;
    readonly ["files"]: readonly QuarantineFilePayload[];
    readonly ["directories"]: readonly string[];
    readonly ["logical_bytes"]: number;
    readonly ["already_absent"]: boolean;
};
export type ReachableArchivePayload = {
    readonly ["archive_id"]: string;
    readonly ["root"]: string;
    readonly ["reachable"]: true;
    readonly ["verification"]: VerificationHealthPayload;
    readonly ["available_bytes"]: number;
    readonly ["available_gib"]: number;
    readonly ["headroom_bytes"]: number;
    readonly ["reserve_bytes"]: number;
    readonly ["total_bytes"]: number;
    readonly ["deferred_cleanup"]: number;
    readonly ["findings"]: readonly AreaFindingPayload[];
    readonly ["unfinished_transactions"]: number;
    readonly ["unknown_entries"]: readonly string[];
    readonly ["quarantined_bytes"]: number;
};
export type ReadyHealthPayload = {
    readonly ["ready"]: true;
    readonly ["policy_valid"]: true;
    readonly ["archive"]: InspectionPayload;
};
export type RecoveryAppliedPayload = {
    readonly ["actionable"]: number;
    readonly ["blocked"]: number;
    readonly ["plan"]: readonly RemediationPayload[];
    readonly ["applied"]: number;
    readonly ["report"]: string;
};
export type RecoveryPlanPayload = {
    readonly ["actionable"]: number;
    readonly ["blocked"]: number;
    readonly ["plan"]: readonly RemediationPayload[];
};
export type RecoveryReport = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["archive_id"]: string;
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["errors"]: readonly string[];
    readonly ["exit_code"]: number;
    readonly ["hostname"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["invocation_mode"]: "systemd" | "interactive";
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["python_version"]: string;
    readonly ["run_id"]: string;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly string[];
    readonly ["remediations"]: readonly Remediation[];
};
export type Reference = {
    readonly ["schema_version"]: number;
    readonly ["commit_sha"]: string;
    readonly ["manifest"]: string;
    readonly ["publication_generation"]: number;
    readonly ["publication_id"]: string;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["tree"]: string;
    readonly ["updated_at"]: string;
};
export type ReferencePayload = {
    readonly ["locator_base"]: "published/";
    readonly ["reference"]: Reference;
};
export type RefreshCounts = {
    readonly ["repositories"]: number;
    readonly ["snapshots_written"]: number;
    readonly ["observations_written"]: number;
    readonly ["records_failed"]: number;
    readonly ["technical_incomplete"]: number;
    readonly ["technical_skipped"]: number;
};
export type Remediation = {
    readonly ["evidence"]: JsonObject;
    readonly ["outcome"]: "applied" | "blocked" | "pending";
    readonly ["reason"]: string;
    readonly ["remedy"]: string;
    readonly ["transaction_id"]: string;
};
export type RemediationPayload = {
    readonly ["last_checkpoint"]: string | null;
    readonly ["operation"]: string;
    readonly ["reason"]: string;
    readonly ["remedy"]: string;
    readonly ["state"]: string;
    readonly ["transaction_id"]: string;
};
export type RepairPayload = {
    readonly ["commit_sha"]: string;
    readonly ["grace_expires_at"]: string;
    readonly ["replacement_publication_id"]: string;
    readonly ["retired_publication_id"]: string;
    readonly ["retirement_record"]: string;
    readonly ["transaction_id"]: string;
    readonly ["verified"]: true;
};
export type RepairProvenance = {
    readonly ["reason"]: string;
    readonly ["repair_of"]: string;
    readonly ["repair_of_manifest"]: string;
    readonly ["repaired_at"]: string;
    readonly ["transaction_id"]: string;
};
export type ReportPayload = {
    readonly ["report"]: RunReport | RecoveryReport | VerificationReport;
};
export type RepositoriesPayload = {
    readonly ["repositories"]: readonly RepositoryPayload[];
};
export type RepositoryCardRead = {
    readonly ["schema_version"]: 1;
    readonly ["kind"]: "repository_card";
    readonly ["archive_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["repository_id"]: string;
    readonly ["commit_sha"]: string;
    readonly ["publication_id"]: string;
    readonly ["publication_generation"]: number;
    readonly ["manifest_path"]: string;
    readonly ["manifest_digest"]: string;
    readonly ["source_path"]: "README.md" | null;
    readonly ["expected_source_sha256"]: string | null;
    readonly ["captured_at"]: string | null;
    readonly ["presentation_version"]: "markdown-1" | null;
    readonly ["state"]:
        | (
              | "present"
              | "absent"
              | "unsupported"
              | "oversize"
              | "unsafe"
              | "failed"
          )
        | "not_captured";
    readonly ["markdown"]: string | null;
    readonly ["presentation_sha256"]: string | null;
    readonly ["diagnostics"]: readonly (
        | "readme_absent"
        | "source_oversize"
        | "presentation_oversize"
        | "source_digest_mismatch"
        | "source_changed"
        | "invalid_utf8"
        | "unsupported_markdown"
        | "unsafe_content"
        | "secret_suppressed"
        | "work_limit"
        | "read_failed"
    )[];
};
export type RepositoryConfig = {
    readonly ["id"]: string;
    readonly ["type"]: "model" | "dataset";
    readonly ["revision"]: string;
    readonly ["enabled"]: boolean;
    readonly ["tags"]: readonly string[];
    readonly ["declared_dependencies"]: readonly string[];
};
export type RepositoryPayload = {
    readonly ["current_commit_sha"]: string | null;
    readonly ["current_publication_id"]: string | null;
    readonly ["enabled"]: boolean | null;
    readonly ["managed"]: boolean;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["retained_revisions"]: number;
};
export type RepositoryRefresh = {
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["repository_id"]: string;
    readonly ["tag_status"]:
        "captured" | "not_requested" | "skipped_unconfigured" | "failed";
    readonly ["technical_status"]:
        | "complete"
        | "incomplete"
        | "failed"
        | "not_requested"
        | "skipped_unpublished";
    readonly ["publications"]: readonly PublicationRefresh[];
    readonly ["warnings"]: readonly string[];
    readonly ["errors"]: readonly string[];
};
export type RepositoryRunResult = {
    readonly ["downloaded_bytes"]: number;
    readonly ["duration_seconds"]: number;
    readonly ["errors"]: readonly string[];
    readonly ["file_count"]: number;
    readonly ["hashed_bytes"]: number;
    readonly ["publication_generation"]: number | null;
    readonly ["publication_id"]: string | null;
    readonly ["pruned"]: PrunedRevision | null;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["requested_revision"]: string;
    readonly ["resolved_commit_sha"]: string | null;
    readonly ["reused_bytes"]: number;
    readonly ["status"]:
        | "skipped"
        | "ref_moved_to_retained_revision"
        | "published"
        | "completed_with_warnings"
        | "failed"
        | "disabled";
    readonly ["warnings"]: readonly string[];
};
export type RepositoryStatusPayload = {
    readonly ["current_commit_sha"]: string | null;
    readonly ["current_publication_generation"]: number | null;
    readonly ["enabled"]: boolean | null;
    readonly ["last_run_status"]: string | null;
    readonly ["managed"]: boolean;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["requested_revision"]: string | null;
    readonly ["retained_generations"]: readonly number[];
    readonly ["retained_revisions"]: number;
    readonly ["upstream_state"]: "unknown";
    readonly ["verification_state"]: "verified" | "unverified" | "failed";
};
export type RequestCandidatePayload = { readonly ["candidate"]: string };
export type RequestCatalogRefreshSubmission = {
    readonly ["selectors"]?: readonly string[];
    readonly ["revision_scope"]?: "current" | "retained";
    readonly ["tags"]?: boolean;
    readonly ["technical"]?: boolean;
};
export type RequestConfigApplicationSubmission = {
    readonly ["managed"]: RequestManagedEditRequest;
    readonly ["preview"]: RequestConfigPreviewReference;
};
export type RequestConfigPreviewReference = {
    readonly ["operation_id"]: string;
    readonly ["key"]: string;
};
export type RequestDiagnosticsSubmission = { readonly ["read_only"]: boolean };
export type RequestFullVerification = {
    readonly ["mode"]: "full";
    readonly ["revision"]?: null;
    readonly ["run_id"]?: null;
};
export type RequestInitializationSubmission = {
    readonly ["archive_root"]: string;
    readonly ["archive_id"]: string;
    readonly ["confirm"]: boolean;
};
export type RequestInstalledPlan = RequestSyncSubmission;
export type RequestInstalledValidation = RequestInstalledValidationSubmission;
export type RequestInstalledValidationSubmission = Readonly<
    Record<string, never>
>;
export type RequestLiteralCandidatePlan = {
    readonly ["selectors"]?: readonly string[];
    readonly ["candidate"]: string;
};
export type RequestLiteralCandidateValidation = RequestCandidatePayload;
export type RequestManagedEditRequest = {
    readonly ["base_revision"]: string;
    readonly ["edits"]: readonly (
        | RequestRepositoryUpsert
        | RequestRepositoryRemove
        | RequestSettingsReplace
    )[];
};
export type RequestManagedPlanRequest = {
    readonly ["managed"]: RequestManagedEditRequest;
    readonly ["selectors"]?: readonly string[];
};
export type RequestManagedValidationRequest = {
    readonly ["managed"]: RequestManagedEditRequest;
};
export type RequestNewVerification = {
    readonly ["mode"]: "new";
    readonly ["revision"]?: null;
    readonly ["run_id"]?: string | null;
};
export type RequestPlanSubmission = {
    readonly ["selectors"]?: readonly string[];
    readonly ["candidate"]?: string | null;
    readonly ["managed"]?: RequestManagedEditRequest | null;
};
export type RequestProbeDiagnostics = { readonly ["read_only"]: false };
export type RequestPruneSubmission = {
    readonly ["selectors"]?: readonly string[];
};
export type RequestPurgeSubmission = {
    readonly ["selectors"]?: readonly string[];
    readonly ["all_unmanaged"]?: boolean;
};
export type RequestQuarantineSubmission = {
    readonly ["transaction_ids"]: readonly string[];
};
export type RequestReadOnlyDiagnostics = { readonly ["read_only"]: true };
export type RequestRecoverySubmission = Readonly<Record<string, never>>;
export type RequestRepairReplacement = {
    readonly ["retired_instance_grace_hours"]?: number | null;
};
export type RequestRepairSubmission = {
    readonly ["revision"]: string;
    readonly ["reason"]?: string;
};
export type RequestRepositoryConfig = {
    readonly ["id"]: string;
    readonly ["type"]: "model" | "dataset";
    readonly ["revision"]?: string;
    readonly ["enabled"]?: boolean;
    readonly ["tags"]?: readonly string[];
    readonly ["declared_dependencies"]?: readonly string[];
};
export type RequestRepositoryRemove = {
    readonly ["kind"]: "repository-remove";
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["repository_id"]: string;
};
export type RequestRepositoryUpsert = {
    readonly ["kind"]: "repository-upsert";
    readonly ["repository"]: RequestRepositoryConfig;
};
export type RequestRevisionVerification = {
    readonly ["mode"]: "revision";
    readonly ["revision"]: string;
    readonly ["run_id"]?: null;
};
export type RequestSettingsReplace = {
    readonly ["kind"]: "settings-replace";
    readonly ["settings"]: RequestSettingsReplacement;
};
export type RequestSettingsReplacement = {
    readonly ["storage"]?: RequestStorageReplacement | null;
    readonly ["sync"]?: RequestSyncReplacement | null;
    readonly ["verification"]?: RequestVerificationReplacement | null;
    readonly ["repair"]?: RequestRepairReplacement | null;
};
export type RequestStorageReplacement = {
    readonly ["publication_mode"]?: ("hardlink" | "copy") | null;
    readonly ["minimum_free_space_gib"]?: number | null;
    readonly ["minimum_free_space_percent"]?: number | null;
    readonly ["maximum_revisions"]?: number | null;
};
export type RequestSyncReplacement = {
    readonly ["max_workers"]?: number | null;
    readonly ["lock_wait_seconds"]?: number | null;
    readonly ["continue_on_repository_error"]?: boolean | null;
    readonly ["dependency_policy"]?: "warn" | null;
    readonly ["stale_staging_age_hours"]?: number | null;
};
export type RequestSyncSubmission = {
    readonly ["selectors"]?: readonly string[];
};
export type RequestValidationSubmission = {
    readonly ["candidate"]?: string | null;
    readonly ["managed"]?: RequestManagedEditRequest | null;
};
export type RequestVerificationReplacement = {
    readonly ["lock_wait_seconds"]?: number | null;
};
export type RequestVerificationSubmission = {
    readonly ["mode"]: "new" | "full" | "revision";
    readonly ["revision"]?: string | null;
    readonly ["run_id"]?: string | null;
};
export type RevisionManifest = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["commit_sha"]: string;
    readonly ["dependencies"]: readonly DependencyObservation[];
    readonly ["download_completed_at"]: string;
    readonly ["download_started_at"]: string;
    readonly ["file_count"]: number;
    readonly ["files"]: readonly FileEntry[];
    readonly ["first_observed_at"]: string;
    readonly ["hub_endpoint"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["publication_generation"]: number;
    readonly ["publication_id"]: string;
    readonly ["publication_mode"]: "hardlink" | "copy";
    readonly ["published_at"]: string;
    readonly ["python_version"]: string;
    readonly ["repair"]: RepairProvenance | null;
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["requested_revision"]: string;
    readonly ["total_bytes"]: number;
    readonly ["tree"]: string;
    readonly ["verification"]: VerificationSummary;
    readonly ["verified_at"]: string;
};
export type RevisionPayload = {
    readonly ["repository_id"]: string;
    readonly ["repository_type"]: "model" | "dataset";
    readonly ["commit_sha"]: string;
    readonly ["file_count"]: number;
    readonly ["publication_generation"]: number;
    readonly ["publication_id"]: string;
    readonly ["published_at"]: string;
    readonly ["total_bytes"]: number;
    readonly ["verification_state"]: "verified" | "unverified" | "failed";
};
export type RevisionSummary = {
    readonly ["commit_sha"]: string;
    readonly ["publication_generation"]: number;
};
export type RevisionsPayload = {
    readonly ["revisions"]: readonly RevisionPayload[];
};
export type RunReport = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["archive_id"]: string;
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["errors"]: readonly string[];
    readonly ["exit_code"]: number;
    readonly ["hostname"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["invocation_mode"]: "systemd" | "interactive";
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["python_version"]: string;
    readonly ["run_id"]: string;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly string[];
    readonly ["repositories"]: readonly RepositoryRunResult[];
    readonly ["totals"]: RunTotals;
};
export type RunResultPayload = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["archive_id"]: string;
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["errors"]: readonly string[];
    readonly ["exit_code"]: number;
    readonly ["hostname"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["invocation_mode"]: "systemd" | "interactive";
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["python_version"]: string;
    readonly ["run_id"]: string;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly string[];
    readonly ["repositories"]: readonly RepositoryRunResult[];
    readonly ["totals"]: RunTotals;
    readonly ["report"]: string;
};
export type RunTotals = {
    readonly ["downloaded_bytes"]: number;
    readonly ["hashed_bytes"]: number;
    readonly ["published_bytes"]: number;
    readonly ["pruned_logical_bytes"]: number;
    readonly ["reused_bytes"]: number;
    readonly ["xet_cache_peak_bytes"]: number;
};
export type RunsPayload = { readonly ["runs"]: readonly string[] };
export type SourceObservation = {
    readonly ["path"]: string;
    readonly ["sha256"]: string;
    readonly ["field"]:
        | "task"
        | "language"
        | "license"
        | "base_model"
        | "upstream_tags"
        | "dataset_config"
        | "dataset_split"
        | "dataset_feature"
        | "format";
    readonly ["values"]: readonly string[];
    readonly ["evidence"]: "declaration" | "header" | "filename";
};
export type StatusPayload = {
    readonly ["archive"]: ReachableArchivePayload | UnreachableArchivePayload;
    readonly ["repositories"]: readonly RepositoryStatusPayload[];
};
export type UiAdminPermission = {
    readonly ["capability"]:
        | "config-read"
        | "config-write"
        | "host-read"
        | "observer-stop"
        | "schedule-write";
    readonly ["granted"]: boolean;
    readonly ["effective"]: boolean;
    readonly ["reason"]: "allowed" | "not_granted" | "feature_unavailable";
};
export type UiAssetManifest = {
    readonly ["schema_version"]: 1;
    readonly ["kind"]: "hfcache_web_assets";
    readonly ["build"]: UiBuildMetadata;
    readonly ["entrypoint"]: "index.html";
    readonly ["meta_identity"]: UiHtmlMetaIdentity;
    readonly ["members"]: readonly UiAssetMember[];
};
export type UiAssetMember = {
    readonly ["path"]: string;
    readonly ["bytes"]: number;
    readonly ["sha256"]: string;
    readonly ["mime"]:
        | "text/html"
        | "text/css"
        | "text/javascript"
        | "application/json"
        | "image/png"
        | "image/webp"
        | "font/woff2"
        | "text/plain";
};
export type UiBootstrap = {
    readonly ["schema_version"]: 1;
    readonly ["kind"]: "hfcache_ui_bootstrap";
    readonly ["ui_contract_version"]: 1;
    readonly ["rest_api_schema_version"]: 1;
    readonly ["wire_source_digest"]: string;
    readonly ["instance_id"]: string;
    readonly ["authority_epoch"]: string;
    readonly ["configured_archive_id"]: string;
    readonly ["archive_identity_source"]: "installed_policy";
    readonly ["config_fingerprint"]: null;
    readonly ["configured_origin"]: string;
    readonly ["paths"]: UiPaths;
    readonly ["user"]: UiUser;
    readonly ["build"]: UiBuildIdentity;
};
export type UiBuildIdentity = {
    readonly ["asset_manifest_sha256"]: string;
    readonly ["metadata"]: UiBuildMetadata;
};
export type UiBuildMetadata = {
    readonly ["application_version"]: string;
    readonly ["source_commit"]: string;
    readonly ["source_snapshot_sha256"]: string;
    readonly ["source_dirty"]: boolean;
    readonly ["ui_contract_version"]: 1;
    readonly ["rest_api_schema_version"]: 1;
    readonly ["wire_source_digest"]: string;
    readonly ["pnpm_lock_sha256"]: string;
    readonly ["toolchain"]: UiToolchain;
    readonly ["toolchain_sha256"]: string;
    readonly ["licenses_sha256"]: string;
    readonly ["notices_sha256"]: string;
};
export type UiHtmlMetaIdentity = {
    readonly ["ui_base"]: "__HFCACHE_UI_BASE_V1__";
    readonly ["bootstrap_path"]: "__HFCACHE_UI_BOOTSTRAP_V1__";
    readonly ["asset_fingerprint"]: "__HFCACHE_UI_FINGERPRINT_V1__";
    readonly ["ui_contract"]: "__HFCACHE_UI_CONTRACT_V1__";
};
export type UiPaths = {
    readonly ["public_prefix"]: string;
    readonly ["effective_prefix"]: string;
    readonly ["ui_base"]: string;
    readonly ["bootstrap"]: string;
    readonly ["api_base"]: string;
    readonly ["mcp_base"]: string | null;
};
export type UiToolchain = {
    readonly ["node"]: string;
    readonly ["pnpm"]: string;
    readonly ["typescript"]: string;
    readonly ["vite"]: string;
};
export type UiUser = {
    readonly ["subject"]: string;
    readonly ["display_name"]: string;
    readonly ["authentication_method"]: "basic";
    readonly ["credential_class"]: "rest-writer";
    readonly ["rest_capabilities"]: readonly ("read" | "write")[];
    readonly ["admin_permissions"]: readonly UiAdminPermission[];
};
export type UnavailableHealthPayload = {
    readonly ["ready"]: true;
    readonly ["policy_valid"]: false | null;
    readonly ["archive"]: null;
};
export type UnreachableArchivePayload = {
    readonly ["archive_id"]: string;
    readonly ["root"]: string;
    readonly ["reachable"]: false;
    readonly ["verification"]: VerificationHealthPayload;
};
export type UpstreamIdentifiers = {
    readonly ["git_oid"]: string | null;
    readonly ["lfs_sha256"]: string | null;
    readonly ["xet_hash"]: string | null;
};
export type VariantMember = {
    readonly ["path"]: string;
    readonly ["size_bytes"]: number;
};
export type VerificationHealthPayload = {
    readonly ["degraded"]: boolean;
    readonly ["last_full_verification"]: FullVerificationSummary | null;
    readonly ["outstanding_failures"]: number;
};
export type VerificationReport = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["archive_id"]: string;
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["errors"]: readonly string[];
    readonly ["exit_code"]: number;
    readonly ["hostname"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["invocation_mode"]: "systemd" | "interactive";
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["python_version"]: string;
    readonly ["run_id"]: string;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly string[];
    readonly ["findings"]: readonly Finding[];
    readonly ["mode"]: "new" | "full" | "revision";
    readonly ["scope"]: VerificationScope;
    readonly ["throughput_bytes_per_second"]: number;
    readonly ["verification_outcome"]: "clean" | "failed";
};
export type VerificationResultPayload = {
    readonly ["schema_version"]: number;
    readonly ["application_version"]: string;
    readonly ["archive_id"]: string;
    readonly ["command"]: string;
    readonly ["completed_at"]: string;
    readonly ["config_fingerprint"]: string;
    readonly ["errors"]: readonly string[];
    readonly ["exit_code"]: number;
    readonly ["hostname"]: string;
    readonly ["huggingface_hub_version"]: string;
    readonly ["invocation_mode"]: "systemd" | "interactive";
    readonly ["outcome"]: "success" | "success_with_warnings" | "failed";
    readonly ["python_version"]: string;
    readonly ["run_id"]: string;
    readonly ["started_at"]: string;
    readonly ["warnings"]: readonly string[];
    readonly ["findings"]: readonly Finding[];
    readonly ["mode"]: "new" | "full" | "revision";
    readonly ["scope"]: VerificationScope;
    readonly ["throughput_bytes_per_second"]: number;
    readonly ["verification_outcome"]: "clean" | "failed";
    readonly ["report"]: string;
};
export type VerificationScope = {
    readonly ["repositories"]: number;
    readonly ["revisions"]: number;
    readonly ["unique_bytes_read"]: number;
    readonly ["unique_objects_read"]: number;
};
export type VerificationSummary = {
    readonly ["algorithm"]: "sha256";
    readonly ["completeness_checked"]: boolean;
    readonly ["hashed_bytes"]: number;
    readonly ["hashed_objects"]: number;
    readonly ["outcome"]: "verified";
    readonly ["reused_digests"]: number;
    readonly ["verified_at"]: string;
};
export type VersionPayload = {
    readonly ["application"]: string;
    readonly ["huggingface_hub"]: string;
    readonly ["python"]: string;
    readonly ["transfer_backend"]: string;
};
export function decodeAcceptance(value: unknown): Acceptance {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "request_id",
                "archive_id",
                "config_fingerprint",
                "operation",
                "created",
                "links",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireInteger(object["schema_version"], null, null),
                    ["hfcache.client_models.exact_version"],
                ),
                ["request_id"]: checked(
                    wireString(object["request_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.client_models._archive_id"],
                ),
                ["config_fingerprint"]: wireString(
                    object["config_fingerprint"],
                    64,
                    64,
                    "^[a-f0-9]{64}$",
                ),
                ["operation"]: decodeClientOperation(object["operation"]),
                ["created"]: wireBoolean(object["created"]),
                ["links"]: decodeClientLinks(object["links"]),
            });
        })(value),
        ["hfcache.client_models.Acceptance.identity"],
    );
}
export function decodeApiProblem(value: unknown): ApiProblem {
    return decodeClientProblem(value);
}
export function decodeAreaFindingPayload(value: unknown): AreaFindingPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "age_hours",
            "area",
            "path",
            "stale",
            "transaction_id",
        ]);
        return Object.freeze({
            ["age_hours"]: wireNumber(object["age_hours"], null, null),
            ["area"]: wireString(object["area"], null, null, null),
            ["path"]: wireString(object["path"], null, null, null),
            ["stale"]: wireBoolean(object["stale"]),
            ["transaction_id"]: wireString(
                object["transaction_id"],
                null,
                null,
                null,
            ),
        });
    })(value);
}
export function decodeCandidateInvalidPayload(
    value: unknown,
): CandidateInvalidPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "valid",
            "syntax_valid",
            "authority_compatible",
            "authority_mismatches",
            "installed_policy_valid",
        ]);
        return Object.freeze({
            ["valid"]: wireLiteral(object["valid"], false),
            ["syntax_valid"]: wireLiteral(object["syntax_valid"], false),
            ["authority_compatible"]: wireNull(object["authority_compatible"]),
            ["authority_mismatches"]: wireArray(
                object["authority_mismatches"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                0,
            ),
            ["installed_policy_valid"]: wireBoolean(
                object["installed_policy_valid"],
            ),
        });
    })(value);
}
export function decodeCandidateValidPayload(
    value: unknown,
): CandidateValidPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "config_fingerprint",
            "enabled_repositories",
            "repositories",
            "token_source",
            "valid",
            "syntax_valid",
            "authority_compatible",
            "authority_mismatches",
            "installed_policy_valid",
        ]);
        return Object.freeze({
            ["config_fingerprint"]: checked(
                wireString(object["config_fingerprint"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["enabled_repositories"]: wireInteger(
                object["enabled_repositories"],
                "0",
                null,
            ),
            ["repositories"]: wireInteger(object["repositories"], "0", null),
            ["token_source"]: wireString(
                object["token_source"],
                null,
                null,
                null,
            ),
            ["valid"]: wireLiteral(object["valid"], true),
            ["syntax_valid"]: wireLiteral(object["syntax_valid"], true),
            ["authority_compatible"]: wireUnion<boolean | null>(
                object["authority_compatible"],
                [
                    (member: unknown) => wireBoolean(member),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["authority_mismatches"]: wireArray(
                object["authority_mismatches"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["installed_policy_valid"]: wireBoolean(
                object["installed_policy_valid"],
            ),
        });
    })(value);
}
export function decodeCapabilities(value: unknown): Capabilities {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "api_version",
                "credential_class",
                "capabilities",
                "instance_id",
                "reads",
                "operations",
                "operation_history",
                "mcp",
                "maintenance_enabled",
                "max_page_size",
            ]);
            return Object.freeze({
                ["api_version"]: checked(
                    wireInteger(object["api_version"], null, null),
                    ["hfcache.client_models.exact_version"],
                ),
                ["credential_class"]: wireUnion<"rest-writer" | "rest-reader">(
                    object["credential_class"],
                    [
                        (member: unknown) => wireLiteral(member, "rest-writer"),
                        (member: unknown) => wireLiteral(member, "rest-reader"),
                    ],
                ),
                ["capabilities"]: wireArray(
                    object["capabilities"],
                    (member: unknown) =>
                        wireUnion<"read" | "write">(member, [
                            (member: unknown) => wireLiteral(member, "read"),
                            (member: unknown) => wireLiteral(member, "write"),
                        ]),
                    null,
                    null,
                ),
                ["instance_id"]: checked(
                    wireString(object["instance_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["reads"]: wireBoolean(object["reads"]),
                ["operations"]: wireBoolean(object["operations"]),
                ["operation_history"]: wireBoolean(object["operation_history"]),
                ["mcp"]: wireBoolean(object["mcp"]),
                ["maintenance_enabled"]: wireBoolean(
                    object["maintenance_enabled"],
                ),
                ["max_page_size"]: wireInteger(
                    object["max_page_size"],
                    "1",
                    "10000",
                ),
            });
        })(value),
        ["hfcache.client_models.Capabilities.permissions"],
    );
}
export function decodeCatalogCoverage(value: unknown): CatalogCoverage {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "repositories",
                "tags_known",
                "tags_unknown",
                "publications",
                "usable",
                "partial",
                "unsupported",
                "failed",
                "missing",
                "technical_required",
                "incomplete",
            ]);
            return Object.freeze({
                ["repositories"]: wireInteger(
                    object["repositories"],
                    "0",
                    "9223372036854775807",
                ),
                ["tags_known"]: wireInteger(
                    object["tags_known"],
                    "0",
                    "9223372036854775807",
                ),
                ["tags_unknown"]: wireInteger(
                    object["tags_unknown"],
                    "0",
                    "9223372036854775807",
                ),
                ["publications"]: wireInteger(
                    object["publications"],
                    "0",
                    "9223372036854775807",
                ),
                ["usable"]: wireInteger(
                    object["usable"],
                    "0",
                    "9223372036854775807",
                ),
                ["partial"]: wireInteger(
                    object["partial"],
                    "0",
                    "9223372036854775807",
                ),
                ["unsupported"]: wireInteger(
                    object["unsupported"],
                    "0",
                    "9223372036854775807",
                ),
                ["failed"]: wireInteger(
                    object["failed"],
                    "0",
                    "9223372036854775807",
                ),
                ["missing"]: wireInteger(
                    object["missing"],
                    "0",
                    "9223372036854775807",
                ),
                ["technical_required"]: wireBoolean(
                    object["technical_required"],
                ),
                ["incomplete"]: wireBoolean(object["incomplete"]),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogCoverage._coherent"],
    );
}
export function decodeCatalogDetailPayload(
    value: unknown,
): CatalogDetailPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "catalog_identity",
                "coverage",
                "entry",
                "observations",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.catalog_query_models.CatalogPayload._version"],
                ),
                ["catalog_identity"]: checked(
                    wireString(object["catalog_identity"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["coverage"]: decodeCatalogCoverage(object["coverage"]),
                ["entry"]: decodeCatalogEntry(object["entry"]),
                ["observations"]: wireArray(
                    object["observations"],
                    (member: unknown) => decodeObservationSummary(member),
                    null,
                    64,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogDetailPayload._coherent"],
    );
}
export function decodeCatalogEntry(value: unknown): CatalogEntry {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "repository_type",
                "repository_id",
                "tags",
                "tag_origin",
                "tag_observed_at",
                "curation_fingerprint",
                "configured",
                "enabled",
                "archived",
                "matching_variant_count",
                "representative_variant",
                "dataset_formats",
            ]);
            return Object.freeze({
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["tags"]: checked(
                    wireArray(
                        object["tags"],
                        (member: unknown) =>
                            wireString(member, null, null, null),
                        null,
                        64,
                    ),
                    ["hfcache.catalog_query_models._canonical_tags"],
                ),
                ["tag_origin"]: wireUnion<
                    "configured" | "last_observed" | "unknown"
                >(object["tag_origin"], [
                    (member: unknown) => wireLiteral(member, "configured"),
                    (member: unknown) => wireLiteral(member, "last_observed"),
                    (member: unknown) => wireLiteral(member, "unknown"),
                ]),
                ["tag_observed_at"]: wireUnion<string | null>(
                    object["tag_observed_at"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "timestamp.serialized",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["curation_fingerprint"]: wireUnion<string | null>(
                    object["curation_fingerprint"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.models._parse_sha256",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["configured"]: wireBoolean(object["configured"]),
                ["enabled"]: wireUnion<boolean | null>(object["enabled"], [
                    (member: unknown) => wireBoolean(member),
                    (member: unknown) => wireNull(member),
                ]),
                ["archived"]: wireBoolean(object["archived"]),
                ["matching_variant_count"]: wireInteger(
                    object["matching_variant_count"],
                    "0",
                    "9223372036854775807",
                ),
                ["representative_variant"]: wireUnion<QualifiedVariant | null>(
                    object["representative_variant"],
                    [
                        (member: unknown) => decodeQualifiedVariant(member),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["dataset_formats"]: wireArray(
                    object["dataset_formats"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.catalog_models._identifier",
                        ]),
                    null,
                    64,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogEntry._coherent"],
    );
}
export function decodeCatalogFacetPayload(value: unknown): CatalogFacetPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "catalog_identity",
                "coverage",
                "facet",
                "total_matches",
                "entries",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.catalog_query_models.CatalogPayload._version"],
                ),
                ["catalog_identity"]: checked(
                    wireString(object["catalog_identity"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["coverage"]: decodeCatalogCoverage(object["coverage"]),
                ["facet"]: wireUnion<
                    "tag" | "format" | "quantization_method" | "quantization"
                >(object["facet"], [
                    (member: unknown) => wireLiteral(member, "tag"),
                    (member: unknown) => wireLiteral(member, "format"),
                    (member: unknown) =>
                        wireLiteral(member, "quantization_method"),
                    (member: unknown) => wireLiteral(member, "quantization"),
                ]),
                ["total_matches"]: wireInteger(
                    object["total_matches"],
                    "0",
                    "9223372036854775807",
                ),
                ["entries"]: wireArray(
                    object["entries"],
                    (member: unknown) => decodeCatalogFacetValue(member),
                    null,
                    10000,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogFacetPayload._coherent"],
    );
}
export function decodeCatalogFacetValue(value: unknown): CatalogFacetValue {
    return ((input: unknown) => {
        const object = wireObject(input, ["value", "repository_count"]);
        return Object.freeze({
            ["value"]: checked(wireString(object["value"], 1, 64, null), [
                "hfcache.catalog_query_models.CatalogFacetValue._safe_value",
            ]),
            ["repository_count"]: wireInteger(
                object["repository_count"],
                "0",
                "9223372036854775807",
            ),
        });
    })(value);
}
export function decodeCatalogRefreshResult(
    value: unknown,
): CatalogRefreshResult {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "state",
                "archive_id",
                "revision_scope",
                "tags",
                "technical",
                "curation_fingerprint",
                "curation_observed_at",
                "counts",
                "repositories",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    [
                        "hfcache.catalog_refresh_models.CatalogRefreshResult._strict_version",
                    ],
                ),
                ["state"]: wireUnion<"complete" | "partial" | "failed">(
                    object["state"],
                    [
                        (member: unknown) => wireLiteral(member, "complete"),
                        (member: unknown) => wireLiteral(member, "partial"),
                        (member: unknown) => wireLiteral(member, "failed"),
                    ],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["revision_scope"]: wireUnion<"current" | "retained">(
                    object["revision_scope"],
                    [
                        (member: unknown) => wireLiteral(member, "current"),
                        (member: unknown) => wireLiteral(member, "retained"),
                    ],
                ),
                ["tags"]: wireBoolean(object["tags"]),
                ["technical"]: wireBoolean(object["technical"]),
                ["curation_fingerprint"]: checked(
                    wireString(
                        object["curation_fingerprint"],
                        null,
                        null,
                        null,
                    ),
                    ["hfcache.models._parse_sha256"],
                ),
                ["curation_observed_at"]: checked(
                    wireString(
                        object["curation_observed_at"],
                        null,
                        null,
                        null,
                    ),
                    ["timestamp.serialized"],
                ),
                ["counts"]: decodeRefreshCounts(object["counts"]),
                ["repositories"]: wireArray(
                    object["repositories"],
                    (member: unknown) => decodeRepositoryRefresh(member),
                    null,
                    256,
                ),
            });
        })(value),
        ["hfcache.catalog_refresh_models.CatalogRefreshResult._coherent"],
    );
}
export function decodeCatalogSearchPayload(
    value: unknown,
): CatalogSearchPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "catalog_identity",
                "coverage",
                "total_matches",
                "entries",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.catalog_query_models.CatalogPayload._version"],
                ),
                ["catalog_identity"]: checked(
                    wireString(object["catalog_identity"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["coverage"]: decodeCatalogCoverage(object["coverage"]),
                ["total_matches"]: wireInteger(
                    object["total_matches"],
                    "0",
                    "9223372036854775807",
                ),
                ["entries"]: wireArray(
                    object["entries"],
                    (member: unknown) => decodeCatalogEntry(member),
                    null,
                    10000,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogSearchPayload._coherent"],
    );
}
export function decodeCatalogVariantsPayload(
    value: unknown,
): CatalogVariantsPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "catalog_identity",
                "coverage",
                "total_matches",
                "entries",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.catalog_query_models.CatalogPayload._version"],
                ),
                ["catalog_identity"]: checked(
                    wireString(object["catalog_identity"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["coverage"]: decodeCatalogCoverage(object["coverage"]),
                ["total_matches"]: wireInteger(
                    object["total_matches"],
                    "0",
                    "9223372036854775807",
                ),
                ["entries"]: wireArray(
                    object["entries"],
                    (member: unknown) => decodeQualifiedVariant(member),
                    null,
                    10000,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.CatalogVariantsPayload._coherent"],
    );
}
export function decodeClientEvent(value: unknown): ClientEvent {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "sequence",
                "at",
                "kind",
                "message",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireInteger(object["schema_version"], null, null),
                    ["hfcache.client_models.exact_version"],
                ),
                ["sequence"]: wireInteger(object["sequence"], "1", null),
                ["at"]: checked(wireString(object["at"], null, null, null), [
                    "timestamp.wire",
                ]),
                ["kind"]: wireString(
                    object["kind"],
                    null,
                    null,
                    "^[a-z][a-z0-9_.-]{0,63}$",
                ),
                ["message"]: wireString(object["message"], null, null, null),
            });
        })(value),
        ["hfcache.client_models.ClientEvent.timestamp"],
    );
}
export function decodeClientEvents(value: unknown): ClientEvents {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "operation_id",
            "events",
            "next_cursor",
            "oldest_sequence",
            "truncated",
        ]);
        return Object.freeze({
            ["operation_id"]: checked(
                wireString(object["operation_id"], null, null, null),
                ["hfcache.identity.parse_run_id"],
            ),
            ["events"]: wireArray(
                object["events"],
                (member: unknown) => decodeClientEvent(member),
                null,
                null,
            ),
            ["next_cursor"]: wireInteger(object["next_cursor"], "0", null),
            ["oldest_sequence"]: wireInteger(
                object["oldest_sequence"],
                "1",
                null,
            ),
            ["truncated"]: wireBoolean(object["truncated"]),
        });
    })(value);
}
export function decodeClientLinks(value: unknown): ClientLinks {
    return ((input: unknown) => {
        const object = wireObject(input, ["status", "result", "events"]);
        return Object.freeze({
            ["status"]: wireString(object["status"], null, null, null),
            ["result"]: wireString(object["result"], null, null, null),
            ["events"]: wireString(object["events"], null, null, null),
        });
    })(value);
}
export function decodeClientOperation(value: unknown): ClientOperation {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "operation_id",
                "principal",
                "route",
                "archive_id",
                "config_fingerprint",
                "state",
                "created_at",
                "updated_at",
                "completed_at",
                "domain_run_id",
                "transaction_ids",
                "next_event_sequence",
                "result_recorded",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireInteger(object["schema_version"], null, null),
                    ["hfcache.client_models.exact_version"],
                ),
                ["operation_id"]: checked(
                    wireString(object["operation_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["principal"]: wireUnion<"rest-writer" | "rest-reader">(
                    object["principal"],
                    [
                        (member: unknown) => wireLiteral(member, "rest-writer"),
                        (member: unknown) => wireLiteral(member, "rest-reader"),
                    ],
                ),
                ["route"]: wireString(object["route"], null, null, null),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.client_models._archive_id"],
                ),
                ["config_fingerprint"]: wireString(
                    object["config_fingerprint"],
                    64,
                    64,
                    "^[a-f0-9]{64}$",
                ),
                ["state"]: wireUnion<
                    | "queued"
                    | "waiting_lock"
                    | "running"
                    | "succeeded"
                    | "failed"
                    | "interrupted"
                >(object["state"], [
                    (member: unknown) => wireLiteral(member, "queued"),
                    (member: unknown) => wireLiteral(member, "waiting_lock"),
                    (member: unknown) => wireLiteral(member, "running"),
                    (member: unknown) => wireLiteral(member, "succeeded"),
                    (member: unknown) => wireLiteral(member, "failed"),
                    (member: unknown) => wireLiteral(member, "interrupted"),
                ]),
                ["created_at"]: checked(
                    wireString(object["created_at"], null, null, null),
                    ["timestamp.wire"],
                ),
                ["updated_at"]: checked(
                    wireString(object["updated_at"], null, null, null),
                    ["timestamp.wire"],
                ),
                ["completed_at"]: wireUnion<string | null>(
                    object["completed_at"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "timestamp.wire",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["domain_run_id"]: wireUnion<string | null>(
                    object["domain_run_id"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.identity.parse_run_id",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["transaction_ids"]: wireArray(
                    object["transaction_ids"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_transaction_id",
                        ]),
                    null,
                    null,
                ),
                ["next_event_sequence"]: wireInteger(
                    object["next_event_sequence"],
                    "1",
                    null,
                ),
                ["result_recorded"]: wireBoolean(object["result_recorded"]),
            });
        })(value),
        ["hfcache.client_models.ClientOperation.evidence"],
    );
}
export function decodeClientProblem(value: unknown): ClientProblem {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "request_id",
            "code",
            "message",
            "exit_code",
        ]);
        return Object.freeze({
            ["request_id"]: checked(
                wireString(object["request_id"], null, null, null),
                ["hfcache.identity.parse_run_id"],
            ),
            ["code"]: wireString(object["code"], null, null, null),
            ["message"]: wireString(object["message"], null, null, null),
            ["exit_code"]: wireInteger(object["exit_code"], null, null),
        });
    })(value);
}
export function decodeClientRead(value: unknown): ClientRead {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "request_id",
                "archive_id",
                "config_fingerprint",
                "envelope",
                "next_cursor",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireInteger(object["schema_version"], null, null),
                    ["hfcache.client_models.exact_version"],
                ),
                ["request_id"]: checked(
                    wireString(object["request_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["archive_id"]: wireUnion<string | null>(object["archive_id"], [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.client_models._archive_id",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["config_fingerprint"]: wireUnion<string | null>(
                    object["config_fingerprint"],
                    [
                        (member: unknown) =>
                            wireString(member, 64, 64, "^[a-f0-9]{64}$"),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["envelope"]: decodeEnvelope(object["envelope"]),
                ["next_cursor"]: wireUnion<string | null>(
                    object["next_cursor"],
                    [
                        (member: unknown) => wireString(member, 1, 256, null),
                        (member: unknown) => wireNull(member),
                    ],
                ),
            });
        })(value),
        [
            "hfcache.client_models.ClientRead.required_envelope_version",
            "hfcache.client_models.ClientRead.coherent_envelope",
        ],
    );
}
export function decodeConfigApplicationOutcome(
    value: unknown,
): ConfigApplicationOutcome {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "archive_id",
                "operation_id",
                "request_digest",
                "base_revision",
                "candidate_revision",
                "config_fingerprint",
                "state",
                "pending",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.config_models._one"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["operation_id"]: checked(
                    wireString(object["operation_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["request_digest"]: checked(
                    wireString(object["request_digest"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["base_revision"]: wireUnion<string | null>(
                    object["base_revision"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.config_models._revision",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["candidate_revision"]: wireUnion<string | null>(
                    object["candidate_revision"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.config_models._revision",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["config_fingerprint"]: wireUnion<string | null>(
                    object["config_fingerprint"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.config_models._revision",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["state"]: wireUnion<
                    | "staged"
                    | "unchanged"
                    | "installed_unconfirmed"
                    | "confirmed"
                    | "conflict"
                    | "unknown"
                >(object["state"], [
                    (member: unknown) => wireLiteral(member, "staged"),
                    (member: unknown) => wireLiteral(member, "unchanged"),
                    (member: unknown) =>
                        wireLiteral(member, "installed_unconfirmed"),
                    (member: unknown) => wireLiteral(member, "confirmed"),
                    (member: unknown) => wireLiteral(member, "conflict"),
                    (member: unknown) => wireLiteral(member, "unknown"),
                ]),
                ["pending"]: wireBoolean(object["pending"]),
            });
        })(value),
        ["hfcache.config_models.ConfigApplicationOutcome.coherent_identity"],
    );
}
export function decodeConfigRead(value: unknown): ConfigRead {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "archive_id",
                "base_revision",
                "editable",
                "editable_fields",
                "protected_fields",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.config_models._one"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["base_revision"]: checked(
                    wireString(object["base_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["editable"]: decodeEditableConfig(object["editable"]),
                ["editable_fields"]: wireArray(
                    object["editable_fields"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["protected_fields"]: wireArray(
                    object["protected_fields"],
                    (member: unknown) => decodeProtectedField(member),
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.config_models.ConfigRead.fixed_fields"],
    );
}
export function decodeDependencyObservation(
    value: unknown,
): DependencyObservation {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "confidence",
            "declared",
            "detected_id",
            "managed",
            "source_field",
            "source_file",
        ]);
        return Object.freeze({
            ["confidence"]: wireUnion<"high" | "medium" | "low">(
                object["confidence"],
                [
                    (member: unknown) => wireLiteral(member, "high"),
                    (member: unknown) => wireLiteral(member, "medium"),
                    (member: unknown) => wireLiteral(member, "low"),
                ],
            ),
            ["declared"]: wireBoolean(object["declared"]),
            ["detected_id"]: wireString(
                object["detected_id"],
                null,
                null,
                null,
            ),
            ["managed"]: wireBoolean(object["managed"]),
            ["source_field"]: wireString(
                object["source_field"],
                null,
                null,
                null,
            ),
            ["source_file"]: checked(
                wireString(object["source_file"], null, null, null),
                ["hfcache.models._repository_path"],
            ),
        });
    })(value);
}
export function decodeDiagnosticCheckPayload(
    value: unknown,
): DiagnosticCheckPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["detail", "name", "outcome"]);
        return Object.freeze({
            ["detail"]: wireString(object["detail"], null, null, null),
            ["name"]: wireString(object["name"], null, null, null),
            ["outcome"]: wireUnion<"pass" | "fail" | "skipped">(
                object["outcome"],
                [
                    (member: unknown) => wireLiteral(member, "pass"),
                    (member: unknown) => wireLiteral(member, "fail"),
                    (member: unknown) => wireLiteral(member, "skipped"),
                ],
            ),
        });
    })(value);
}
export function decodeDiagnosticsPayload(value: unknown): DiagnosticsPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["checks"]);
        return Object.freeze({
            ["checks"]: wireArray(
                object["checks"],
                (member: unknown) => decodeDiagnosticCheckPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeEditableConfig(value: unknown): EditableConfig {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "storage",
                "sync",
                "verification",
                "repair",
                "repositories",
            ]);
            return Object.freeze({
                ["storage"]: decodeEditableStorage(object["storage"]),
                ["sync"]: decodeEditableSync(object["sync"]),
                ["verification"]: decodeEditableVerification(
                    object["verification"],
                ),
                ["repair"]: decodeEditableRepair(object["repair"]),
                ["repositories"]: wireArray(
                    object["repositories"],
                    (member: unknown) => decodeRepositoryConfig(member),
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.config_models.EditableConfig.unique_repositories"],
    );
}
export function decodeEditableRepair(value: unknown): EditableRepair {
    return ((input: unknown) => {
        const object = wireObject(input, ["retired_instance_grace_hours"]);
        return Object.freeze({
            ["retired_instance_grace_hours"]: wireInteger(
                object["retired_instance_grace_hours"],
                "168",
                "8760",
            ),
        });
    })(value);
}
export function decodeEditableStorage(value: unknown): EditableStorage {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "publication_mode",
            "minimum_free_space_gib",
            "minimum_free_space_percent",
            "maximum_revisions",
        ]);
        return Object.freeze({
            ["publication_mode"]: wireUnion<"hardlink" | "copy">(
                object["publication_mode"],
                [
                    (member: unknown) => wireLiteral(member, "hardlink"),
                    (member: unknown) => wireLiteral(member, "copy"),
                ],
            ),
            ["minimum_free_space_gib"]: wireInteger(
                object["minimum_free_space_gib"],
                "0",
                "1048576",
            ),
            ["minimum_free_space_percent"]: wireInteger(
                object["minimum_free_space_percent"],
                "0",
                "100",
            ),
            ["maximum_revisions"]: checked(
                wireInteger(object["maximum_revisions"], null, null),
                ["hfcache.config_models._retention"],
            ),
        });
    })(value);
}
export function decodeEditableSync(value: unknown): EditableSync {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "max_workers",
            "lock_wait_seconds",
            "continue_on_repository_error",
            "dependency_policy",
            "stale_staging_age_hours",
        ]);
        return Object.freeze({
            ["max_workers"]: wireInteger(object["max_workers"], "1", "32"),
            ["lock_wait_seconds"]: wireInteger(
                object["lock_wait_seconds"],
                "0",
                "86400",
            ),
            ["continue_on_repository_error"]: wireBoolean(
                object["continue_on_repository_error"],
            ),
            ["dependency_policy"]: wireLiteral(
                object["dependency_policy"],
                "warn",
            ),
            ["stale_staging_age_hours"]: wireInteger(
                object["stale_staging_age_hours"],
                "1",
                "8760",
            ),
        });
    })(value);
}
export function decodeEditableVerification(
    value: unknown,
): EditableVerification {
    return ((input: unknown) => {
        const object = wireObject(input, ["lock_wait_seconds"]);
        return Object.freeze({
            ["lock_wait_seconds"]: wireInteger(
                object["lock_wait_seconds"],
                "0",
                "604800",
            ),
        });
    })(value);
}
export function decodeEmptyPayload(value: unknown): EmptyPayload {
    return ((input: unknown) => {
        wireObject(input, []);
        return Object.freeze({});
    })(value);
}
export function decodeEnvelope(value: unknown): Envelope {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
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
            ]);
            return Object.freeze({
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.wire"],
                ),
                ["data"]: wireJsonValue(object["data"], 32, 100000, true),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => decodeEnvelopeProblem(member),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.wire"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => decodeEnvelopeProblem(member),
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.reporting.Envelope._check"],
    );
}
export function decodeEnvelopeProblem(value: unknown): EnvelopeProblem {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "code",
            "context",
            "message",
            "repository",
        ]);
        return Object.freeze({
            ["code"]: wireString(object["code"], null, null, null),
            ["context"]: wireJsonValue(object["context"], 32, 100000, true),
            ["message"]: wireString(object["message"], null, null, null),
            ["repository"]: wireUnion<string | null>(object["repository"], [
                (member: unknown) => wireString(member, null, null, null),
                (member: unknown) => wireNull(member),
            ]),
        });
    })(value);
}
export function decodeEstimatePayload(value: unknown): EstimatePayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "estimated_duration_seconds",
            "measured_throughput_bytes_per_second",
            "mode",
            "repositories",
            "revisions",
            "storage_maintenance",
            "unique_bytes",
            "unique_objects",
            "unreadable_objects",
        ]);
        return Object.freeze({
            ["estimated_duration_seconds"]: wireUnion<number | null>(
                object["estimated_duration_seconds"],
                [
                    (member: unknown) => wireNumber(member, "0", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["measured_throughput_bytes_per_second"]: wireUnion<number | null>(
                object["measured_throughput_bytes_per_second"],
                [
                    (member: unknown) => wireNumber(member, "0", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["mode"]: wireLiteral(object["mode"], "estimate"),
            ["repositories"]: wireInteger(object["repositories"], "0", null),
            ["revisions"]: wireInteger(object["revisions"], "0", null),
            ["storage_maintenance"]: wireLiteral(
                object["storage_maintenance"],
                "undetectable",
            ),
            ["unique_bytes"]: wireInteger(object["unique_bytes"], "0", null),
            ["unique_objects"]: wireInteger(
                object["unique_objects"],
                "0",
                null,
            ),
            ["unreadable_objects"]: wireInteger(
                object["unreadable_objects"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeFileEntry(value: unknown): FileEntry {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "path",
            "provenance",
            "sha256",
            "size",
            "upstream",
        ]);
        return Object.freeze({
            ["path"]: checked(wireString(object["path"], null, null, null), [
                "hfcache.models._repository_path",
            ]),
            ["provenance"]: decodeFileProvenance(object["provenance"]),
            ["sha256"]: checked(
                wireString(object["sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["size"]: wireInteger(object["size"], "0", null),
            ["upstream"]: decodeUpstreamIdentifiers(object["upstream"]),
        });
    })(value);
}
export function decodeFileProvenance(value: unknown): FileProvenance {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "cache_root",
                "hash_reused_from",
                "hashed",
                "source",
            ]);
            return Object.freeze({
                ["cache_root"]: wireUnion<"canonical" | "repair">(
                    object["cache_root"],
                    [
                        (member: unknown) => wireLiteral(member, "canonical"),
                        (member: unknown) => wireLiteral(member, "repair"),
                    ],
                ),
                ["hash_reused_from"]: wireUnion<HashReuse | null>(
                    object["hash_reused_from"],
                    [
                        (member: unknown) => decodeHashReuse(member),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["hashed"]: wireBoolean(object["hashed"]),
                ["source"]: wireUnion<
                    "hub_download" | "cache_reuse" | "repair_download"
                >(object["source"], [
                    (member: unknown) => wireLiteral(member, "hub_download"),
                    (member: unknown) => wireLiteral(member, "cache_reuse"),
                    (member: unknown) => wireLiteral(member, "repair_download"),
                ]),
            });
        })(value),
        ["hfcache.manifests.FileProvenance._check"],
    );
}
export function decodeFinding(value: unknown): Finding {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "commit_sha",
                "expected",
                "kind",
                "observed",
                "path",
                "publication_id",
                "repository_id",
                "repository_type",
            ]);
            return Object.freeze({
                ["commit_sha"]: wireUnion<string | null>(object["commit_sha"], [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["expected"]: wireUnion<string | null>(object["expected"], [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ]),
                ["kind"]: wireUnion<
                    | "missing"
                    | "extra"
                    | "size_mismatch"
                    | "digest_mismatch"
                    | "not_regular"
                    | "unreadable"
                    | "ref_invalid"
                    | "manifest_invalid"
                >(object["kind"], [
                    (member: unknown) => wireLiteral(member, "missing"),
                    (member: unknown) => wireLiteral(member, "extra"),
                    (member: unknown) => wireLiteral(member, "size_mismatch"),
                    (member: unknown) => wireLiteral(member, "digest_mismatch"),
                    (member: unknown) => wireLiteral(member, "not_regular"),
                    (member: unknown) => wireLiteral(member, "unreadable"),
                    (member: unknown) => wireLiteral(member, "ref_invalid"),
                    (member: unknown) =>
                        wireLiteral(member, "manifest_invalid"),
                ]),
                ["observed"]: wireUnion<string | null>(object["observed"], [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ]),
                ["path"]: wireUnion<string | null>(object["path"], [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.models._repository_path",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["publication_id"]: wireUnion<string | null>(
                    object["publication_id"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.identity.parse_publication_id",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
            });
        })(value),
        ["hfcache.reporting.Finding._check"],
    );
}
export function decodeFullVerificationSummary(
    value: unknown,
): FullVerificationSummary {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "completed_at",
            "duration_seconds",
            "outcome",
            "report",
            "started_at",
            "throughput_bytes_per_second",
            "unique_bytes",
            "unique_objects",
        ]);
        return Object.freeze({
            ["completed_at"]: checked(
                wireString(object["completed_at"], null, null, null),
                ["timestamp.serialized"],
            ),
            ["duration_seconds"]: wireNumber(
                object["duration_seconds"],
                "0.0",
                null,
            ),
            ["outcome"]: wireUnion<"clean" | "failed">(object["outcome"], [
                (member: unknown) => wireLiteral(member, "clean"),
                (member: unknown) => wireLiteral(member, "failed"),
            ]),
            ["report"]: checked(
                wireString(object["report"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["started_at"]: checked(
                wireString(object["started_at"], null, null, null),
                ["timestamp.serialized"],
            ),
            ["throughput_bytes_per_second"]: wireNumber(
                object["throughput_bytes_per_second"],
                "0.0",
                null,
            ),
            ["unique_bytes"]: wireInteger(object["unique_bytes"], "0", null),
            ["unique_objects"]: wireInteger(
                object["unique_objects"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeHashReuse(value: unknown): HashReuse {
    return ((input: unknown) => {
        const object = wireObject(input, ["commit_sha", "publication_id"]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["publication_id"]: checked(
                wireString(object["publication_id"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
        });
    })(value);
}
export function decodeHealthPayload(value: unknown): HealthPayload {
    return wireUnion<ReadyHealthPayload | UnavailableHealthPayload>(value, [
        (member: unknown) => decodeReadyHealthPayload(member),
        (member: unknown) => decodeUnavailableHealthPayload(member),
    ]);
}
export function decodeHostBinding(value: unknown): HostBinding {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "deployment_sha256",
            "policy_sha256",
            "release_version",
            "source_commit",
            "source_snapshot_sha256",
            "source_dirty",
            "archive_id",
            "archive_root",
        ]);
        return Object.freeze({
            ["deployment_sha256"]: checked(
                wireString(object["deployment_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["policy_sha256"]: checked(
                wireString(object["policy_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["release_version"]: checked(
                wireString(object["release_version"], null, 128, null),
                ["hfcache.host_models._version"],
            ),
            ["source_commit"]: checked(
                wireString(object["source_commit"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["source_snapshot_sha256"]: checked(
                wireString(object["source_snapshot_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["source_dirty"]: wireBoolean(object["source_dirty"]),
            ["archive_id"]: checked(
                wireString(object["archive_id"], null, null, null),
                ["hfcache.models._parse_archive_id"],
            ),
            ["archive_root"]: wireLiteral(
                object["archive_root"],
                "/srv/hfcache",
            ),
        });
    })(value);
}
export function decodeHostFacts(value: unknown): HostFacts {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "guard",
                "archive_mount",
                "units",
                "sync_schedule",
            ]);
            return Object.freeze({
                ["guard"]: wireUnion<"held" | "absent" | "inactive">(
                    object["guard"],
                    [
                        (member: unknown) => wireLiteral(member, "held"),
                        (member: unknown) => wireLiteral(member, "absent"),
                        (member: unknown) => wireLiteral(member, "inactive"),
                    ],
                ),
                ["archive_mount"]: wireUnion<
                    "nfs-ro" | "nfs-rw" | "local-ro" | "local-rw" | "absent"
                >(object["archive_mount"], [
                    (member: unknown) => wireLiteral(member, "nfs-ro"),
                    (member: unknown) => wireLiteral(member, "nfs-rw"),
                    (member: unknown) => wireLiteral(member, "local-ro"),
                    (member: unknown) => wireLiteral(member, "local-rw"),
                    (member: unknown) => wireLiteral(member, "absent"),
                ]),
                ["units"]: ((input: unknown) => {
                    const object = wireObject(input, [
                        "hfcache-sync.service",
                        "hfcache-sync.timer",
                        "hfcache-verify.service",
                        "hfcache-verify.timer",
                    ]);
                    return Object.freeze({
                        ["hfcache-sync.service"]: decodeHostUnitState(
                            object["hfcache-sync.service"],
                        ),
                        ["hfcache-sync.timer"]: decodeHostUnitState(
                            object["hfcache-sync.timer"],
                        ),
                        ["hfcache-verify.service"]: decodeHostUnitState(
                            object["hfcache-verify.service"],
                        ),
                        ["hfcache-verify.timer"]: decodeHostUnitState(
                            object["hfcache-verify.timer"],
                        ),
                    });
                })(object["units"]),
                ["sync_schedule"]: decodeHostSyncSchedule(
                    object["sync_schedule"],
                ),
            });
        })(value),
        ["hfcache.host_models.HostFacts.exact_units"],
    );
}
export function decodeHostPermissionReasons(
    value: unknown,
): HostPermissionReasons {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "archive",
            "hub",
            "control",
            "schedule",
            "configuration",
            "observer",
        ]);
        return Object.freeze({
            ["archive"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["archive"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
            ["hub"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["hub"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
            ["control"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["control"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
            ["schedule"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["schedule"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
            ["configuration"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["configuration"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
            ["observer"]: wireUnion<
                | "granted"
                | "policy-denied"
                | "guard-held"
                | "profile-unproved"
                | "authority-unknown"
                | "helper-unavailable"
            >(object["observer"], [
                (member: unknown) => wireLiteral(member, "granted"),
                (member: unknown) => wireLiteral(member, "policy-denied"),
                (member: unknown) => wireLiteral(member, "guard-held"),
                (member: unknown) => wireLiteral(member, "profile-unproved"),
                (member: unknown) => wireLiteral(member, "authority-unknown"),
                (member: unknown) => wireLiteral(member, "helper-unavailable"),
            ]),
        });
    })(value);
}
export function decodeHostPermissions(value: unknown): HostPermissions {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "archive",
            "hub",
            "control",
            "schedule",
            "configuration",
            "observer",
        ]);
        return Object.freeze({
            ["archive"]: wireBoolean(object["archive"]),
            ["hub"]: wireBoolean(object["hub"]),
            ["control"]: wireBoolean(object["control"]),
            ["schedule"]: wireBoolean(object["schedule"]),
            ["configuration"]: wireBoolean(object["configuration"]),
            ["observer"]: wireBoolean(object["observer"]),
        });
    })(value);
}
export function decodeHostStatus(value: unknown): HostStatus {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "state",
                "reason",
                "profile",
                "binding",
                "permissions",
                "permission_reasons",
                "facts",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.host_models._one"],
                ),
                ["state"]: wireUnion<
                    "supported" | "guarded" | "unknown" | "unavailable"
                >(object["state"], [
                    (member: unknown) => wireLiteral(member, "supported"),
                    (member: unknown) => wireLiteral(member, "guarded"),
                    (member: unknown) => wireLiteral(member, "unknown"),
                    (member: unknown) => wireLiteral(member, "unavailable"),
                ]),
                ["reason"]: wireUnion<
                    | (
                          | "helper-disabled"
                          | "helper-unavailable"
                          | "helper-timeout"
                          | "helper-refused"
                          | "helper-busy"
                          | "policy-missing"
                          | "policy-invalid"
                          | "deployment-unverified"
                          | "facts-unavailable"
                          | "guard-unconfirmed"
                          | "key-missing"
                          | "key-invalid"
                          | "config-unavailable"
                      )
                    | null
                >(object["reason"], [
                    (member: unknown) =>
                        wireUnion<
                            | "helper-disabled"
                            | "helper-unavailable"
                            | "helper-timeout"
                            | "helper-refused"
                            | "helper-busy"
                            | "policy-missing"
                            | "policy-invalid"
                            | "deployment-unverified"
                            | "facts-unavailable"
                            | "guard-unconfirmed"
                            | "key-missing"
                            | "key-invalid"
                            | "config-unavailable"
                        >(member, [
                            (member: unknown) =>
                                wireLiteral(member, "helper-disabled"),
                            (member: unknown) =>
                                wireLiteral(member, "helper-unavailable"),
                            (member: unknown) =>
                                wireLiteral(member, "helper-timeout"),
                            (member: unknown) =>
                                wireLiteral(member, "helper-refused"),
                            (member: unknown) =>
                                wireLiteral(member, "helper-busy"),
                            (member: unknown) =>
                                wireLiteral(member, "policy-missing"),
                            (member: unknown) =>
                                wireLiteral(member, "policy-invalid"),
                            (member: unknown) =>
                                wireLiteral(member, "deployment-unverified"),
                            (member: unknown) =>
                                wireLiteral(member, "facts-unavailable"),
                            (member: unknown) =>
                                wireLiteral(member, "guard-unconfirmed"),
                            (member: unknown) =>
                                wireLiteral(member, "key-missing"),
                            (member: unknown) =>
                                wireLiteral(member, "key-invalid"),
                            (member: unknown) =>
                                wireLiteral(member, "config-unavailable"),
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["profile"]: wireUnion<("native" | "rootless") | null>(
                    object["profile"],
                    [
                        (member: unknown) =>
                            wireUnion<"native" | "rootless">(member, [
                                (member: unknown) =>
                                    wireLiteral(member, "native"),
                                (member: unknown) =>
                                    wireLiteral(member, "rootless"),
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["binding"]: wireUnion<HostBinding | null>(object["binding"], [
                    (member: unknown) => decodeHostBinding(member),
                    (member: unknown) => wireNull(member),
                ]),
                ["permissions"]: decodeHostPermissions(object["permissions"]),
                ["permission_reasons"]: decodeHostPermissionReasons(
                    object["permission_reasons"],
                ),
                ["facts"]: wireUnion<HostFacts | null>(object["facts"], [
                    (member: unknown) => decodeHostFacts(member),
                    (member: unknown) => wireNull(member),
                ]),
            });
        })(value),
        ["hfcache.host_models.HostStatus.coherent_authority"],
    );
}
export function decodeHostSyncSchedule(value: unknown): HostSyncSchedule {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "state",
                "reason",
                "revision",
                "source",
                "on_calendar",
                "randomized_delay_sec",
            ]);
            return Object.freeze({
                ["state"]: wireUnion<"observed" | "unavailable">(
                    object["state"],
                    [
                        (member: unknown) => wireLiteral(member, "observed"),
                        (member: unknown) => wireLiteral(member, "unavailable"),
                    ],
                ),
                ["reason"]: wireUnion<
                    ("profile-unproved" | "facts-unavailable") | null
                >(object["reason"], [
                    (member: unknown) =>
                        wireUnion<"profile-unproved" | "facts-unavailable">(
                            member,
                            [
                                (member: unknown) =>
                                    wireLiteral(member, "profile-unproved"),
                                (member: unknown) =>
                                    wireLiteral(member, "facts-unavailable"),
                            ],
                        ),
                    (member: unknown) => wireNull(member),
                ]),
                ["revision"]: wireUnion<string | null>(object["revision"], [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.models._parse_sha256",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["source"]: wireUnion<("default" | "managed") | null>(
                    object["source"],
                    [
                        (member: unknown) =>
                            wireUnion<"default" | "managed">(member, [
                                (member: unknown) =>
                                    wireLiteral(member, "default"),
                                (member: unknown) =>
                                    wireLiteral(member, "managed"),
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["on_calendar"]: wireUnion<string | null>(
                    object["on_calendar"],
                    [
                        (member: unknown) => wireString(member, 1, 4096, null),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["randomized_delay_sec"]: wireUnion<string | null>(
                    object["randomized_delay_sec"],
                    [
                        (member: unknown) => wireString(member, 1, 256, null),
                        (member: unknown) => wireNull(member),
                    ],
                ),
            });
        })(value),
        ["hfcache.host_models.HostSyncSchedule.complete_schedule"],
    );
}
export function decodeHostUnitState(value: unknown): HostUnitState {
    return ((input: unknown) => {
        const object = wireObject(input, ["load", "active", "unit_file"]);
        return Object.freeze({
            ["load"]: wireUnion<"loaded" | "masked" | "not-found">(
                object["load"],
                [
                    (member: unknown) => wireLiteral(member, "loaded"),
                    (member: unknown) => wireLiteral(member, "masked"),
                    (member: unknown) => wireLiteral(member, "not-found"),
                ],
            ),
            ["active"]: wireUnion<"active" | "inactive" | "failed">(
                object["active"],
                [
                    (member: unknown) => wireLiteral(member, "active"),
                    (member: unknown) => wireLiteral(member, "inactive"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ],
            ),
            ["unit_file"]: wireUnion<
                | "enabled"
                | "enabled-runtime"
                | "disabled"
                | "static"
                | "linked"
                | "linked-runtime"
                | "masked"
                | "masked-runtime"
                | "not-found"
            >(object["unit_file"], [
                (member: unknown) => wireLiteral(member, "enabled"),
                (member: unknown) => wireLiteral(member, "enabled-runtime"),
                (member: unknown) => wireLiteral(member, "disabled"),
                (member: unknown) => wireLiteral(member, "static"),
                (member: unknown) => wireLiteral(member, "linked"),
                (member: unknown) => wireLiteral(member, "linked-runtime"),
                (member: unknown) => wireLiteral(member, "masked"),
                (member: unknown) => wireLiteral(member, "masked-runtime"),
                (member: unknown) => wireLiteral(member, "not-found"),
            ]),
        });
    })(value);
}
export function decodeInitializationPayload(
    value: unknown,
): InitializationPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "adopted_published",
            "archive_id",
            "archive_root",
            "created_directories",
            "removed_temporaries",
            "sentinel",
        ]);
        return Object.freeze({
            ["adopted_published"]: wireBoolean(object["adopted_published"]),
            ["archive_id"]: checked(
                wireString(object["archive_id"], null, null, null),
                ["hfcache.models._parse_archive_id"],
            ),
            ["archive_root"]: wireString(
                object["archive_root"],
                null,
                null,
                null,
            ),
            ["created_directories"]: wireArray(
                object["created_directories"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["removed_temporaries"]: wireArray(
                object["removed_temporaries"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["sentinel"]: checked(
                wireString(object["sentinel"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
        });
    })(value);
}
export function decodeInspectionPayload(value: unknown): InspectionPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "adopted_published",
            "archive_id",
            "archive_root",
            "existing_directories",
            "initializable",
            "leftover_temporaries",
            "missing_directories",
            "mount",
            "state",
            "unknown_entries",
            "unknown_entry_count",
        ]);
        return Object.freeze({
            ["adopted_published"]: wireBoolean(object["adopted_published"]),
            ["archive_id"]: wireUnion<string | null>(object["archive_id"], [
                (member: unknown) =>
                    checked(wireString(member, null, null, null), [
                        "hfcache.models._parse_archive_id",
                    ]),
                (member: unknown) => wireNull(member),
            ]),
            ["archive_root"]: wireString(
                object["archive_root"],
                null,
                null,
                null,
            ),
            ["existing_directories"]: wireArray(
                object["existing_directories"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["initializable"]: wireBoolean(object["initializable"]),
            ["leftover_temporaries"]: wireArray(
                object["leftover_temporaries"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["missing_directories"]: wireArray(
                object["missing_directories"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["mount"]: decodeMountPayload(object["mount"]),
            ["state"]: wireUnion<
                | "uninitialized"
                | "partially_initialized"
                | "initialized"
                | "unusable"
            >(object["state"], [
                (member: unknown) => wireLiteral(member, "uninitialized"),
                (member: unknown) =>
                    wireLiteral(member, "partially_initialized"),
                (member: unknown) => wireLiteral(member, "initialized"),
                (member: unknown) => wireLiteral(member, "unusable"),
            ]),
            ["unknown_entries"]: wireArray(
                object["unknown_entries"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["unknown_entry_count"]: wireInteger(
                object["unknown_entry_count"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeInstalledValidationPayload(
    value: unknown,
): InstalledValidationPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "config_fingerprint",
            "enabled_repositories",
            "repositories",
            "token_source",
        ]);
        return Object.freeze({
            ["config_fingerprint"]: checked(
                wireString(object["config_fingerprint"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["enabled_repositories"]: wireInteger(
                object["enabled_repositories"],
                "0",
                null,
            ),
            ["repositories"]: wireInteger(object["repositories"], "0", null),
            ["token_source"]: wireString(
                object["token_source"],
                null,
                null,
                null,
            ),
        });
    })(value);
}
export function decodeManagedAssessment(value: unknown): ManagedAssessment {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "archive_id",
                "base_revision",
                "candidate_revision",
                "required_selectors",
                "complete",
                "sizing",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.config_models._one"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["base_revision"]: checked(
                    wireString(object["base_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["candidate_revision"]: checked(
                    wireString(object["candidate_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["required_selectors"]: wireArray(
                    object["required_selectors"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.config_models._whole_selector",
                        ]),
                    null,
                    256,
                ),
                ["complete"]: wireBoolean(object["complete"]),
                ["sizing"]: wireUnion<PlanPayload | null>(object["sizing"], [
                    (member: unknown) => decodePlanPayload(member),
                    (member: unknown) => wireNull(member),
                ]),
            });
        })(value),
        ["hfcache.config_models.ManagedAssessment.complete_scope"],
    );
}
export function decodeManagedValidation(value: unknown): ManagedValidation {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "archive_id",
                "base_revision",
                "candidate_revision",
                "required_selectors",
                "valid",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.config_models._one"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["base_revision"]: checked(
                    wireString(object["base_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["candidate_revision"]: checked(
                    wireString(object["candidate_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["required_selectors"]: wireArray(
                    object["required_selectors"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.config_models._whole_selector",
                        ]),
                    null,
                    256,
                ),
                ["valid"]: wireLiteral(object["valid"], true),
            });
        })(value),
        [
            "hfcache.config_models.ManagedValidation.strict_valid",
            "hfcache.config_models.ManagedValidation.unique_scope",
        ],
    );
}
export function decodeManifestPayload(value: unknown): ManifestPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["manifest", "tree_base"]);
        return Object.freeze({
            ["manifest"]: decodeRevisionManifest(object["manifest"]),
            ["tree_base"]: wireLiteral(object["tree_base"], "archive-root/"),
        });
    })(value);
}
export function decodeModelVariant(value: unknown): ModelVariant {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "variant_id",
                "format",
                "encoding",
                "quantization",
                "quantization_method",
                "bits",
                "group_size",
                "role",
                "members",
                "total_bytes",
                "completeness",
                "evidence",
                "source_paths",
                "diagnostics",
            ]);
            return Object.freeze({
                ["variant_id"]: checked(
                    wireString(object["variant_id"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["format"]: checked(
                    wireString(object["format"], null, null, null),
                    ["hfcache.catalog_models._identifier"],
                ),
                ["encoding"]: wireUnion<string | null>(object["encoding"], [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.catalog_models._identifier",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["quantization"]: wireUnion<string | null>(
                    object["quantization"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.catalog_models._identifier",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["quantization_method"]: wireUnion<string | null>(
                    object["quantization_method"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.catalog_models._identifier",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["bits"]: wireUnion<number | null>(object["bits"], [
                    (member: unknown) => wireInteger(member, "1", "64"),
                    (member: unknown) => wireNull(member),
                ]),
                ["group_size"]: wireUnion<number | null>(object["group_size"], [
                    (member: unknown) =>
                        wireInteger(member, "1", "9223372036854775807"),
                    (member: unknown) => wireNull(member),
                ]),
                ["role"]: wireUnion<
                    | "primary"
                    | "adapter"
                    | "projector"
                    | "auxiliary"
                    | "unknown"
                >(object["role"], [
                    (member: unknown) => wireLiteral(member, "primary"),
                    (member: unknown) => wireLiteral(member, "adapter"),
                    (member: unknown) => wireLiteral(member, "projector"),
                    (member: unknown) => wireLiteral(member, "auxiliary"),
                    (member: unknown) => wireLiteral(member, "unknown"),
                ]),
                ["members"]: wireArray(
                    object["members"],
                    (member: unknown) => decodeVariantMember(member),
                    1,
                    4096,
                ),
                ["total_bytes"]: wireUnion<number | null>(
                    object["total_bytes"],
                    [
                        (member: unknown) =>
                            wireInteger(member, "0", "9223372036854775807"),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["completeness"]: wireUnion<
                    "complete" | "incomplete" | "unknown"
                >(object["completeness"], [
                    (member: unknown) => wireLiteral(member, "complete"),
                    (member: unknown) => wireLiteral(member, "incomplete"),
                    (member: unknown) => wireLiteral(member, "unknown"),
                ]),
                ["evidence"]: wireUnion<"header" | "declaration" | "filename">(
                    object["evidence"],
                    [
                        (member: unknown) => wireLiteral(member, "header"),
                        (member: unknown) => wireLiteral(member, "declaration"),
                        (member: unknown) => wireLiteral(member, "filename"),
                    ],
                ),
                ["source_paths"]: wireArray(
                    object["source_paths"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.models._repository_path",
                        ]),
                    1,
                    64,
                ),
                ["diagnostics"]: wireArray(
                    object["diagnostics"],
                    (member: unknown) => wireString(member, null, 512, null),
                    null,
                    64,
                ),
            });
        })(value),
        ["hfcache.catalog_models.ModelVariant.coherent"],
    );
}
export function decodeMountPayload(value: unknown): MountPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "exists",
            "filesystem_type",
            "is_mount_point",
            "read_only",
            "source",
        ]);
        return Object.freeze({
            ["exists"]: wireBoolean(object["exists"]),
            ["filesystem_type"]: wireUnion<string | null>(
                object["filesystem_type"],
                [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["is_mount_point"]: wireBoolean(object["is_mount_point"]),
            ["read_only"]: wireUnion<boolean | null>(object["read_only"], [
                (member: unknown) => wireBoolean(member),
                (member: unknown) => wireNull(member),
            ]),
            ["source"]: wireUnion<string | null>(object["source"], [
                (member: unknown) => wireString(member, null, null, null),
                (member: unknown) => wireNull(member),
            ]),
        });
    })(value);
}
export function decodeObservationSummary(value: unknown): ObservationSummary {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "commit_sha",
                "publication_id",
                "publication_generation",
                "extractor_version",
                "observed_at",
                "status",
                "sources",
                "dataset_formats",
                "diagnostics",
            ]);
            return Object.freeze({
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["extractor_version"]: checked(
                    wireString(object["extractor_version"], null, null, null),
                    ["hfcache.catalog_models._identifier"],
                ),
                ["observed_at"]: checked(
                    wireString(object["observed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["status"]: wireUnion<
                    "complete" | "partial" | "unsupported" | "failed"
                >(object["status"], [
                    (member: unknown) => wireLiteral(member, "complete"),
                    (member: unknown) => wireLiteral(member, "partial"),
                    (member: unknown) => wireLiteral(member, "unsupported"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["sources"]: wireArray(
                    object["sources"],
                    (member: unknown) => decodeSourceObservation(member),
                    null,
                    4096,
                ),
                ["dataset_formats"]: wireArray(
                    object["dataset_formats"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.catalog_models._identifier",
                        ]),
                    null,
                    64,
                ),
                ["diagnostics"]: wireArray(
                    object["diagnostics"],
                    (member: unknown) => wireString(member, null, 512, null),
                    null,
                    64,
                ),
            });
        })(value),
        ["hfcache.catalog_query_models.ObservationSummary._ordered"],
    );
}
export function decodeOperationPayload(value: unknown): OperationPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["operation"]);
        return Object.freeze({
            ["operation"]: decodeClientOperation(object["operation"]),
        });
    })(value);
}
export function decodeOperationsPayload(value: unknown): OperationsPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["operations"]);
        return Object.freeze({
            ["operations"]: wireArray(
                object["operations"],
                (member: unknown) => decodeClientOperation(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodePlanPayload(value: unknown): PlanPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["repositories"]);
        return Object.freeze({
            ["repositories"]: wireArray(
                object["repositories"],
                (member: unknown) => decodePlannedRepositoryPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodePlanResultPayload(value: unknown): PlanResultPayload {
    return wireUnion<PlanPayload | ManagedAssessment>(value, [
        (member: unknown) => decodePlanPayload(member),
        (member: unknown) => decodeManagedAssessment(member),
    ]);
}
export function decodePlannedRepositoryPayload(
    value: unknown,
): PlannedRepositoryPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "enabled",
            "estimated_new_bytes",
            "file_count",
            "logical_bytes",
            "projected_publication_bytes",
            "publication_mode",
            "repository_id",
            "repository_type",
            "requested_revision",
            "resolved_commit_sha",
            "upstream_state",
        ]);
        return Object.freeze({
            ["enabled"]: wireBoolean(object["enabled"]),
            ["estimated_new_bytes"]: wireUnion<number | null>(
                object["estimated_new_bytes"],
                [
                    (member: unknown) => wireInteger(member, "0", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["file_count"]: wireUnion<number | null>(object["file_count"], [
                (member: unknown) => wireInteger(member, "0", null),
                (member: unknown) => wireNull(member),
            ]),
            ["logical_bytes"]: wireUnion<number | null>(
                object["logical_bytes"],
                [
                    (member: unknown) => wireInteger(member, "0", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["projected_publication_bytes"]: wireUnion<number | null>(
                object["projected_publication_bytes"],
                [
                    (member: unknown) => wireInteger(member, "0", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["publication_mode"]: wireUnion<"hardlink" | "copy">(
                object["publication_mode"],
                [
                    (member: unknown) => wireLiteral(member, "hardlink"),
                    (member: unknown) => wireLiteral(member, "copy"),
                ],
            ),
            ["repository_id"]: checked(
                wireString(object["repository_id"], null, null, null),
                ["hfcache.identity.parse_repository_id"],
            ),
            ["repository_type"]: checked(
                wireUnion<"model" | "dataset">(object["repository_type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ["hfcache.identity.parse_repository_type"],
            ),
            ["requested_revision"]: wireString(
                object["requested_revision"],
                null,
                null,
                null,
            ),
            ["resolved_commit_sha"]: wireUnion<string | null>(
                object["resolved_commit_sha"],
                [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["upstream_state"]: wireUnion<
                | "unknown"
                | "available"
                | "missing"
                | "forbidden"
                | "refused"
                | "unresolvable"
                | "unreachable"
            >(object["upstream_state"], [
                (member: unknown) => wireLiteral(member, "unknown"),
                (member: unknown) => wireLiteral(member, "available"),
                (member: unknown) => wireLiteral(member, "missing"),
                (member: unknown) => wireLiteral(member, "forbidden"),
                (member: unknown) => wireLiteral(member, "refused"),
                (member: unknown) => wireLiteral(member, "unresolvable"),
                (member: unknown) => wireLiteral(member, "unreachable"),
            ]),
        });
    })(value);
}
export function decodeProtectedField(value: unknown): ProtectedField {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, ["field", "description"]);
            return Object.freeze({
                ["field"]: wireString(object["field"], null, null, null),
                ["description"]: wireString(
                    object["description"],
                    null,
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.config_models.ProtectedField.fixed_description"],
    );
}
export function decodePrunePayload(value: unknown): PrunePayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["plans", "applied"]);
        return Object.freeze({
            ["plans"]: wireArray(
                object["plans"],
                (member: unknown) => decodePrunePlan(member),
                null,
                null,
            ),
            ["applied"]: wireArray(
                object["applied"],
                (member: unknown) => decodePrunedRevisionRecord(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodePrunePlan(value: unknown): PrunePlan {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "cache_revisions_to_delete",
                "current",
                "generated_at",
                "plan_id",
                "reason",
                "repository_id",
                "repository_type",
                "retained",
                "selected",
                "unique_bytes_released_estimate",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["cache_revisions_to_delete"]: wireArray(
                    object["cache_revisions_to_delete"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    null,
                    null,
                ),
                ["current"]: decodeRevisionSummary(object["current"]),
                ["generated_at"]: checked(
                    wireString(object["generated_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["plan_id"]: checked(
                    wireString(object["plan_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["reason"]: wireLiteral(
                    object["reason"],
                    "sixth_unique_revision_published",
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["retained"]: wireArray(
                    object["retained"],
                    (member: unknown) => decodeRevisionSummary(member),
                    null,
                    null,
                ),
                ["selected"]: decodePruneSelection(object["selected"]),
                ["unique_bytes_released_estimate"]: wireInteger(
                    object["unique_bytes_released_estimate"],
                    "0",
                    null,
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.models.PrunePlan._check",
        ],
    );
}
export function decodePruneSelection(value: unknown): PruneSelection {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "commit_sha",
            "file_count",
            "logical_bytes",
            "manifest",
            "publication_generation",
            "publication_id",
            "tree",
        ]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["file_count"]: wireInteger(object["file_count"], "0", null),
            ["logical_bytes"]: wireInteger(object["logical_bytes"], "0", null),
            ["manifest"]: checked(
                wireString(object["manifest"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["publication_generation"]: wireInteger(
                object["publication_generation"],
                "1",
                null,
            ),
            ["publication_id"]: checked(
                wireString(object["publication_id"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["tree"]: checked(wireString(object["tree"], null, null, null), [
                "hfcache.models._archive_path",
            ]),
        });
    })(value);
}
export function decodePrunedRevision(value: unknown): PrunedRevision {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "commit_sha",
            "logical_bytes",
            "publication_generation",
        ]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["logical_bytes"]: wireInteger(object["logical_bytes"], "0", null),
            ["publication_generation"]: wireInteger(
                object["publication_generation"],
                "1",
                null,
            ),
        });
    })(value);
}
export function decodePrunedRevisionRecord(
    value: unknown,
): PrunedRevisionRecord {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "commit_sha",
                "file_count",
                "logical_bytes",
                "manifest_archived_at",
                "plan_id",
                "publication_generation",
                "publication_id",
                "pruned_at",
                "reason",
                "repository_id",
                "repository_type",
                "retained_after",
                "transaction_id",
                "tree",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["file_count"]: wireInteger(object["file_count"], "0", null),
                ["logical_bytes"]: wireInteger(
                    object["logical_bytes"],
                    "0",
                    null,
                ),
                ["manifest_archived_at"]: checked(
                    wireString(
                        object["manifest_archived_at"],
                        null,
                        null,
                        null,
                    ),
                    ["timestamp.serialized"],
                ),
                ["plan_id"]: checked(
                    wireString(object["plan_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["pruned_at"]: checked(
                    wireString(object["pruned_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["reason"]: wireUnion<
                    | "sixth_unique_revision_published"
                    | "operator_requested_repository_purge"
                >(object["reason"], [
                    (member: unknown) =>
                        wireLiteral(member, "sixth_unique_revision_published"),
                    (member: unknown) =>
                        wireLiteral(
                            member,
                            "operator_requested_repository_purge",
                        ),
                ]),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["retained_after"]: wireArray(
                    object["retained_after"],
                    (member: unknown) => decodeRevisionSummary(member),
                    null,
                    null,
                ),
                ["transaction_id"]: checked(
                    wireString(object["transaction_id"], null, null, null),
                    ["hfcache.identity.parse_transaction_id"],
                ),
                ["tree"]: checked(
                    wireString(object["tree"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
            });
        })(value),
        ["hfcache.models.VersionedModel._check_schema_version"],
    );
}
export function decodePublicationRefresh(value: unknown): PublicationRefresh {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "commit_sha",
                "publication_id",
                "publication_generation",
                "write_status",
                "observation_status",
                "observed_at",
                "manifest_digest",
                "error_code",
            ]);
            return Object.freeze({
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["write_status"]: wireUnion<"written" | "failed">(
                    object["write_status"],
                    [
                        (member: unknown) => wireLiteral(member, "written"),
                        (member: unknown) => wireLiteral(member, "failed"),
                    ],
                ),
                ["observation_status"]: wireUnion<
                    ("complete" | "partial" | "unsupported" | "failed") | null
                >(object["observation_status"], [
                    (member: unknown) =>
                        wireUnion<
                            "complete" | "partial" | "unsupported" | "failed"
                        >(member, [
                            (member: unknown) =>
                                wireLiteral(member, "complete"),
                            (member: unknown) => wireLiteral(member, "partial"),
                            (member: unknown) =>
                                wireLiteral(member, "unsupported"),
                            (member: unknown) => wireLiteral(member, "failed"),
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
                ["observed_at"]: wireUnion<string | null>(
                    object["observed_at"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "timestamp.serialized",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["manifest_digest"]: wireUnion<string | null>(
                    object["manifest_digest"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.models._parse_sha256",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["error_code"]: wireUnion<string | null>(object["error_code"], [
                    (member: unknown) =>
                        wireString(member, null, 32, "^HF[A-Z]{2,6}[0-9]{3}$"),
                    (member: unknown) => wireNull(member),
                ]),
            });
        })(value),
        ["hfcache.catalog_refresh_models.PublicationRefresh._coherent"],
    );
}
export function decodePurgePayload(value: unknown): PurgePayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["plans", "applied"]);
        return Object.freeze({
            ["plans"]: wireArray(
                object["plans"],
                (member: unknown) => decodePurgePlan(member),
                null,
                null,
            ),
            ["applied"]: wireArray(
                object["applied"],
                (member: unknown) => decodePrunedRevisionRecord(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodePurgePlan(value: unknown): PurgePlan {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "cache_revisions_to_delete",
                "current",
                "generated_at",
                "plan_id",
                "reason",
                "repository_id",
                "repository_type",
                "revisions",
                "unique_bytes_released_estimate",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["cache_revisions_to_delete"]: wireArray(
                    object["cache_revisions_to_delete"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    null,
                    null,
                ),
                ["current"]: decodeRevisionSummary(object["current"]),
                ["generated_at"]: checked(
                    wireString(object["generated_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["plan_id"]: checked(
                    wireString(object["plan_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["reason"]: wireLiteral(
                    object["reason"],
                    "operator_requested_repository_purge",
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["revisions"]: wireArray(
                    object["revisions"],
                    (member: unknown) => decodePruneSelection(member),
                    null,
                    null,
                ),
                ["unique_bytes_released_estimate"]: wireInteger(
                    object["unique_bytes_released_estimate"],
                    "0",
                    null,
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.models.PurgePlan._check",
        ],
    );
}
export function decodeQualifiedVariant(value: unknown): QualifiedVariant {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "commit_sha",
            "publication_id",
            "publication_generation",
            "variant",
        ]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["publication_id"]: checked(
                wireString(object["publication_id"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["publication_generation"]: wireInteger(
                object["publication_generation"],
                "1",
                null,
            ),
            ["variant"]: decodeModelVariant(object["variant"]),
        });
    })(value);
}
export function decodeQuarantineAppliedPayload(
    value: unknown,
): QuarantineAppliedPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "transaction_id",
            "repository",
            "quarantine_path",
            "recovery_transaction_id",
            "files",
            "directories",
            "logical_bytes",
            "already_absent",
            "removed_files",
            "removed_directories",
            "removed_logical_bytes",
        ]);
        return Object.freeze({
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
            ["repository"]: wireString(object["repository"], null, null, null),
            ["quarantine_path"]: checked(
                wireString(object["quarantine_path"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["recovery_transaction_id"]: checked(
                wireString(object["recovery_transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
            ["files"]: wireArray(
                object["files"],
                (member: unknown) => decodeQuarantineFilePayload(member),
                null,
                null,
            ),
            ["directories"]: wireArray(
                object["directories"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["logical_bytes"]: wireInteger(object["logical_bytes"], "0", null),
            ["already_absent"]: wireBoolean(object["already_absent"]),
            ["removed_files"]: wireInteger(object["removed_files"], "0", null),
            ["removed_directories"]: wireInteger(
                object["removed_directories"],
                "0",
                null,
            ),
            ["removed_logical_bytes"]: wireInteger(
                object["removed_logical_bytes"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeQuarantineFilePayload(
    value: unknown,
): QuarantineFilePayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "path",
            "size",
            "sha256",
            "retained_path",
        ]);
        return Object.freeze({
            ["path"]: wireString(object["path"], null, null, null),
            ["size"]: wireInteger(object["size"], "0", null),
            ["sha256"]: checked(
                wireString(object["sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["retained_path"]: checked(
                wireString(object["retained_path"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
        });
    })(value);
}
export function decodeQuarantinePayload(value: unknown): QuarantinePayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["plans", "applied"]);
        return Object.freeze({
            ["plans"]: wireArray(
                object["plans"],
                (member: unknown) => decodeQuarantinePlanPayload(member),
                null,
                null,
            ),
            ["applied"]: wireArray(
                object["applied"],
                (member: unknown) => decodeQuarantineAppliedPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeQuarantinePlanPayload(
    value: unknown,
): QuarantinePlanPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "transaction_id",
            "repository",
            "quarantine_path",
            "recovery_transaction_id",
            "files",
            "directories",
            "logical_bytes",
            "already_absent",
        ]);
        return Object.freeze({
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
            ["repository"]: wireString(object["repository"], null, null, null),
            ["quarantine_path"]: checked(
                wireString(object["quarantine_path"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["recovery_transaction_id"]: checked(
                wireString(object["recovery_transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
            ["files"]: wireArray(
                object["files"],
                (member: unknown) => decodeQuarantineFilePayload(member),
                null,
                null,
            ),
            ["directories"]: wireArray(
                object["directories"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["logical_bytes"]: wireInteger(object["logical_bytes"], "0", null),
            ["already_absent"]: wireBoolean(object["already_absent"]),
        });
    })(value);
}
export function decodeReachableArchivePayload(
    value: unknown,
): ReachableArchivePayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "archive_id",
            "root",
            "reachable",
            "verification",
            "available_bytes",
            "available_gib",
            "headroom_bytes",
            "reserve_bytes",
            "total_bytes",
            "deferred_cleanup",
            "findings",
            "unfinished_transactions",
            "unknown_entries",
            "quarantined_bytes",
        ]);
        return Object.freeze({
            ["archive_id"]: checked(
                wireString(object["archive_id"], null, null, null),
                ["hfcache.models._parse_archive_id"],
            ),
            ["root"]: wireString(object["root"], null, null, null),
            ["reachable"]: wireLiteral(object["reachable"], true),
            ["verification"]: decodeVerificationHealthPayload(
                object["verification"],
            ),
            ["available_bytes"]: wireInteger(
                object["available_bytes"],
                "0",
                null,
            ),
            ["available_gib"]: wireNumber(object["available_gib"], null, null),
            ["headroom_bytes"]: wireInteger(
                object["headroom_bytes"],
                null,
                null,
            ),
            ["reserve_bytes"]: wireInteger(object["reserve_bytes"], "0", null),
            ["total_bytes"]: wireInteger(object["total_bytes"], "0", null),
            ["deferred_cleanup"]: wireInteger(
                object["deferred_cleanup"],
                "0",
                null,
            ),
            ["findings"]: wireArray(
                object["findings"],
                (member: unknown) => decodeAreaFindingPayload(member),
                null,
                null,
            ),
            ["unfinished_transactions"]: wireInteger(
                object["unfinished_transactions"],
                "0",
                null,
            ),
            ["unknown_entries"]: wireArray(
                object["unknown_entries"],
                (member: unknown) => wireString(member, null, null, null),
                null,
                null,
            ),
            ["quarantined_bytes"]: wireInteger(
                object["quarantined_bytes"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeReadyHealthPayload(value: unknown): ReadyHealthPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["ready", "policy_valid", "archive"]);
        return Object.freeze({
            ["ready"]: wireLiteral(object["ready"], true),
            ["policy_valid"]: wireLiteral(object["policy_valid"], true),
            ["archive"]: decodeInspectionPayload(object["archive"]),
        });
    })(value);
}
export function decodeRecoveryAppliedPayload(
    value: unknown,
): RecoveryAppliedPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "actionable",
            "blocked",
            "plan",
            "applied",
            "report",
        ]);
        return Object.freeze({
            ["actionable"]: wireInteger(object["actionable"], "0", null),
            ["blocked"]: wireInteger(object["blocked"], "0", null),
            ["plan"]: wireArray(
                object["plan"],
                (member: unknown) => decodeRemediationPayload(member),
                null,
                null,
            ),
            ["applied"]: wireInteger(object["applied"], "0", null),
            ["report"]: checked(
                wireString(object["report"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
        });
    })(value);
}
export function decodeRecoveryPlanPayload(value: unknown): RecoveryPlanPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["actionable", "blocked", "plan"]);
        return Object.freeze({
            ["actionable"]: wireInteger(object["actionable"], "0", null),
            ["blocked"]: wireInteger(object["blocked"], "0", null),
            ["plan"]: wireArray(
                object["plan"],
                (member: unknown) => decodeRemediationPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeRecoveryReport(value: unknown): RecoveryReport {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "archive_id",
                "command",
                "completed_at",
                "config_fingerprint",
                "errors",
                "exit_code",
                "hostname",
                "huggingface_hub_version",
                "invocation_mode",
                "outcome",
                "python_version",
                "run_id",
                "started_at",
                "warnings",
                "remediations",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["archive_id"]: wireString(
                    object["archive_id"],
                    null,
                    null,
                    null,
                ),
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["config_fingerprint"]: checked(
                    wireString(object["config_fingerprint"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["hostname"]: wireString(object["hostname"], null, null, null),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["invocation_mode"]: wireUnion<"systemd" | "interactive">(
                    object["invocation_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "systemd"),
                        (member: unknown) => wireLiteral(member, "interactive"),
                    ],
                ),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["remediations"]: wireArray(
                    object["remediations"],
                    (member: unknown) => decodeRemediation(member),
                    null,
                    null,
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.reporting.RunEnvelope._check_envelope",
            "hfcache.reporting.RecoveryReport._check",
        ],
    );
}
export function decodeReference(value: unknown): Reference {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "commit_sha",
                "manifest",
                "publication_generation",
                "publication_id",
                "repository_id",
                "repository_type",
                "tree",
                "updated_at",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["manifest"]: checked(
                    wireString(object["manifest"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["tree"]: checked(
                    wireString(object["tree"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
                ["updated_at"]: checked(
                    wireString(object["updated_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
            });
        })(value),
        ["hfcache.models.VersionedModel._check_schema_version"],
    );
}
export function decodeReferencePayload(value: unknown): ReferencePayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["locator_base", "reference"]);
        return Object.freeze({
            ["locator_base"]: wireLiteral(object["locator_base"], "published/"),
            ["reference"]: decodeReference(object["reference"]),
        });
    })(value);
}
export function decodeRefreshCounts(value: unknown): RefreshCounts {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "repositories",
            "snapshots_written",
            "observations_written",
            "records_failed",
            "technical_incomplete",
            "technical_skipped",
        ]);
        return Object.freeze({
            ["repositories"]: wireInteger(object["repositories"], "0", "256"),
            ["snapshots_written"]: wireInteger(
                object["snapshots_written"],
                "0",
                "256",
            ),
            ["observations_written"]: wireInteger(
                object["observations_written"],
                "0",
                "512",
            ),
            ["records_failed"]: wireInteger(
                object["records_failed"],
                "0",
                "768",
            ),
            ["technical_incomplete"]: wireInteger(
                object["technical_incomplete"],
                "0",
                "512",
            ),
            ["technical_skipped"]: wireInteger(
                object["technical_skipped"],
                "0",
                "256",
            ),
        });
    })(value);
}
export function decodeRemediation(value: unknown): Remediation {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "evidence",
            "outcome",
            "reason",
            "remedy",
            "transaction_id",
        ]);
        return Object.freeze({
            ["evidence"]: wireJsonValue(object["evidence"], 32, 100000, true),
            ["outcome"]: wireUnion<"applied" | "blocked" | "pending">(
                object["outcome"],
                [
                    (member: unknown) => wireLiteral(member, "applied"),
                    (member: unknown) => wireLiteral(member, "blocked"),
                    (member: unknown) => wireLiteral(member, "pending"),
                ],
            ),
            ["reason"]: wireString(object["reason"], null, null, null),
            ["remedy"]: wireString(object["remedy"], null, null, null),
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
        });
    })(value);
}
export function decodeRemediationPayload(value: unknown): RemediationPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "last_checkpoint",
            "operation",
            "reason",
            "remedy",
            "state",
            "transaction_id",
        ]);
        return Object.freeze({
            ["last_checkpoint"]: wireUnion<string | null>(
                object["last_checkpoint"],
                [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["operation"]: wireString(object["operation"], null, null, null),
            ["reason"]: wireString(object["reason"], null, null, null),
            ["remedy"]: wireString(object["remedy"], null, null, null),
            ["state"]: wireString(object["state"], null, null, null),
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
        });
    })(value);
}
export function decodeRepairPayload(value: unknown): RepairPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "commit_sha",
            "grace_expires_at",
            "replacement_publication_id",
            "retired_publication_id",
            "retirement_record",
            "transaction_id",
            "verified",
        ]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["grace_expires_at"]: checked(
                wireString(object["grace_expires_at"], null, null, null),
                ["timestamp.wire"],
            ),
            ["replacement_publication_id"]: checked(
                wireString(
                    object["replacement_publication_id"],
                    null,
                    null,
                    null,
                ),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["retired_publication_id"]: checked(
                wireString(object["retired_publication_id"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["retirement_record"]: checked(
                wireString(object["retirement_record"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
            ["verified"]: wireLiteral(object["verified"], true),
        });
    })(value);
}
export function decodeRepairProvenance(value: unknown): RepairProvenance {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "reason",
            "repair_of",
            "repair_of_manifest",
            "repaired_at",
            "transaction_id",
        ]);
        return Object.freeze({
            ["reason"]: wireString(object["reason"], null, null, null),
            ["repair_of"]: checked(
                wireString(object["repair_of"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["repair_of_manifest"]: checked(
                wireString(object["repair_of_manifest"], null, null, null),
                ["hfcache.models._archive_path"],
            ),
            ["repaired_at"]: checked(
                wireString(object["repaired_at"], null, null, null),
                ["timestamp.serialized"],
            ),
            ["transaction_id"]: checked(
                wireString(object["transaction_id"], null, null, null),
                ["hfcache.identity.parse_transaction_id"],
            ),
        });
    })(value);
}
export function decodeReportPayload(value: unknown): ReportPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["report"]);
        return Object.freeze({
            ["report"]: wireUnion<
                RunReport | RecoveryReport | VerificationReport
            >(object["report"], [
                (member: unknown) => decodeRunReport(member),
                (member: unknown) => decodeRecoveryReport(member),
                (member: unknown) => decodeVerificationReport(member),
            ]),
        });
    })(value);
}
export function decodeRepositoriesPayload(value: unknown): RepositoriesPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["repositories"]);
        return Object.freeze({
            ["repositories"]: wireArray(
                object["repositories"],
                (member: unknown) => decodeRepositoryPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeRepositoryCardRead(value: unknown): RepositoryCardRead {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "kind",
                "archive_id",
                "repository_type",
                "repository_id",
                "commit_sha",
                "publication_id",
                "publication_generation",
                "manifest_path",
                "manifest_digest",
                "source_path",
                "expected_source_sha256",
                "captured_at",
                "presentation_version",
                "state",
                "markdown",
                "presentation_sha256",
                "diagnostics",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.card_models.RepositoryCardRead.strict_version"],
                ),
                ["kind"]: wireLiteral(object["kind"], "repository_card"),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["manifest_path"]: checked(
                    wireString(object["manifest_path"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
                ["manifest_digest"]: checked(
                    wireString(object["manifest_digest"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["source_path"]: wireUnion<"README.md" | null>(
                    object["source_path"],
                    [
                        (member: unknown) => wireLiteral(member, "README.md"),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["expected_source_sha256"]: wireUnion<string | null>(
                    object["expected_source_sha256"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.models._parse_sha256",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["captured_at"]: wireUnion<string | null>(
                    object["captured_at"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "timestamp.serialized",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["presentation_version"]: wireUnion<"markdown-1" | null>(
                    object["presentation_version"],
                    [
                        (member: unknown) => wireLiteral(member, "markdown-1"),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["state"]: wireUnion<
                    | (
                          | "present"
                          | "absent"
                          | "unsupported"
                          | "oversize"
                          | "unsafe"
                          | "failed"
                      )
                    | "not_captured"
                >(object["state"], [
                    (member: unknown) =>
                        wireUnion<
                            | "present"
                            | "absent"
                            | "unsupported"
                            | "oversize"
                            | "unsafe"
                            | "failed"
                        >(member, [
                            (member: unknown) => wireLiteral(member, "present"),
                            (member: unknown) => wireLiteral(member, "absent"),
                            (member: unknown) =>
                                wireLiteral(member, "unsupported"),
                            (member: unknown) =>
                                wireLiteral(member, "oversize"),
                            (member: unknown) => wireLiteral(member, "unsafe"),
                            (member: unknown) => wireLiteral(member, "failed"),
                        ]),
                    (member: unknown) => wireLiteral(member, "not_captured"),
                ]),
                ["markdown"]: wireUnion<string | null>(object["markdown"], [
                    (member: unknown) =>
                        wireString(member, null, 1048576, null),
                    (member: unknown) => wireNull(member),
                ]),
                ["presentation_sha256"]: wireUnion<string | null>(
                    object["presentation_sha256"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.models._parse_sha256",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["diagnostics"]: wireArray(
                    object["diagnostics"],
                    (member: unknown) =>
                        wireUnion<
                            | "readme_absent"
                            | "source_oversize"
                            | "presentation_oversize"
                            | "source_digest_mismatch"
                            | "source_changed"
                            | "invalid_utf8"
                            | "unsupported_markdown"
                            | "unsafe_content"
                            | "secret_suppressed"
                            | "work_limit"
                            | "read_failed"
                        >(member, [
                            (member: unknown) =>
                                wireLiteral(member, "readme_absent"),
                            (member: unknown) =>
                                wireLiteral(member, "source_oversize"),
                            (member: unknown) =>
                                wireLiteral(member, "presentation_oversize"),
                            (member: unknown) =>
                                wireLiteral(member, "source_digest_mismatch"),
                            (member: unknown) =>
                                wireLiteral(member, "source_changed"),
                            (member: unknown) =>
                                wireLiteral(member, "invalid_utf8"),
                            (member: unknown) =>
                                wireLiteral(member, "unsupported_markdown"),
                            (member: unknown) =>
                                wireLiteral(member, "unsafe_content"),
                            (member: unknown) =>
                                wireLiteral(member, "secret_suppressed"),
                            (member: unknown) =>
                                wireLiteral(member, "work_limit"),
                            (member: unknown) =>
                                wireLiteral(member, "read_failed"),
                        ]),
                    null,
                    11,
                ),
            });
        })(value),
        ["hfcache.card_models.RepositoryCardRead.coherent"],
    );
}
export function decodeRepositoryConfig(value: unknown): RepositoryConfig {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "id",
                "type",
                "revision",
                "enabled",
                "tags",
                "declared_dependencies",
            ]);
            return Object.freeze({
                ["id"]: checked(wireString(object["id"], null, null, null), [
                    "hfcache.identity.parse_repository_id",
                ]),
                ["type"]: wireUnion<"model" | "dataset">(object["type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ["revision"]: checked(
                    wireString(object["revision"], null, null, null),
                    ["hfcache.identity.parse_revision"],
                ),
                ["enabled"]: wireBoolean(object["enabled"]),
                ["tags"]: checked(
                    wireArray(
                        object["tags"],
                        (member: unknown) =>
                            wireString(member, null, null, null),
                        null,
                        64,
                    ),
                    ["hfcache.tags.normalize_tags"],
                ),
                ["declared_dependencies"]: wireArray(
                    object["declared_dependencies"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_repository_id",
                        ]),
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.config.RepositoryConfig._check"],
    );
}
export function decodeRepositoryPayload(value: unknown): RepositoryPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "current_commit_sha",
            "current_publication_id",
            "enabled",
            "managed",
            "repository_id",
            "repository_type",
            "retained_revisions",
        ]);
        return Object.freeze({
            ["current_commit_sha"]: wireUnion<string | null>(
                object["current_commit_sha"],
                [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["current_publication_id"]: wireUnion<string | null>(
                object["current_publication_id"],
                [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_publication_id",
                        ]),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["enabled"]: wireUnion<boolean | null>(object["enabled"], [
                (member: unknown) => wireBoolean(member),
                (member: unknown) => wireNull(member),
            ]),
            ["managed"]: wireBoolean(object["managed"]),
            ["repository_id"]: checked(
                wireString(object["repository_id"], null, null, null),
                ["hfcache.identity.parse_repository_id"],
            ),
            ["repository_type"]: checked(
                wireUnion<"model" | "dataset">(object["repository_type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ["hfcache.identity.parse_repository_type"],
            ),
            ["retained_revisions"]: wireInteger(
                object["retained_revisions"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeRepositoryRefresh(value: unknown): RepositoryRefresh {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "repository_type",
                "repository_id",
                "tag_status",
                "technical_status",
                "publications",
                "warnings",
                "errors",
            ]);
            return Object.freeze({
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["tag_status"]: wireUnion<
                    | "captured"
                    | "not_requested"
                    | "skipped_unconfigured"
                    | "failed"
                >(object["tag_status"], [
                    (member: unknown) => wireLiteral(member, "captured"),
                    (member: unknown) => wireLiteral(member, "not_requested"),
                    (member: unknown) =>
                        wireLiteral(member, "skipped_unconfigured"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["technical_status"]: wireUnion<
                    | "complete"
                    | "incomplete"
                    | "failed"
                    | "not_requested"
                    | "skipped_unpublished"
                >(object["technical_status"], [
                    (member: unknown) => wireLiteral(member, "complete"),
                    (member: unknown) => wireLiteral(member, "incomplete"),
                    (member: unknown) => wireLiteral(member, "failed"),
                    (member: unknown) => wireLiteral(member, "not_requested"),
                    (member: unknown) =>
                        wireLiteral(member, "skipped_unpublished"),
                ]),
                ["publications"]: wireArray(
                    object["publications"],
                    (member: unknown) => decodePublicationRefresh(member),
                    null,
                    512,
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) =>
                        wireString(member, null, 32, "^HF[A-Z]{2,6}[0-9]{3}$"),
                    null,
                    8,
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) =>
                        wireString(member, null, 32, "^HF[A-Z]{2,6}[0-9]{3}$"),
                    null,
                    8,
                ),
            });
        })(value),
        ["hfcache.catalog_refresh_models.RepositoryRefresh._coherent"],
    );
}
export function decodeRepositoryRunResult(value: unknown): RepositoryRunResult {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "downloaded_bytes",
                "duration_seconds",
                "errors",
                "file_count",
                "hashed_bytes",
                "publication_generation",
                "publication_id",
                "pruned",
                "repository_id",
                "repository_type",
                "requested_revision",
                "resolved_commit_sha",
                "reused_bytes",
                "status",
                "warnings",
            ]);
            return Object.freeze({
                ["downloaded_bytes"]: wireInteger(
                    object["downloaded_bytes"],
                    "0",
                    null,
                ),
                ["duration_seconds"]: wireNumber(
                    object["duration_seconds"],
                    "0.0",
                    null,
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["file_count"]: wireInteger(object["file_count"], "0", null),
                ["hashed_bytes"]: wireInteger(
                    object["hashed_bytes"],
                    "0",
                    null,
                ),
                ["publication_generation"]: wireUnion<number | null>(
                    object["publication_generation"],
                    [
                        (member: unknown) => wireInteger(member, "1", null),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["publication_id"]: wireUnion<string | null>(
                    object["publication_id"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.identity.parse_publication_id",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["pruned"]: wireUnion<PrunedRevision | null>(object["pruned"], [
                    (member: unknown) => decodePrunedRevision(member),
                    (member: unknown) => wireNull(member),
                ]),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["requested_revision"]: wireString(
                    object["requested_revision"],
                    null,
                    null,
                    null,
                ),
                ["resolved_commit_sha"]: wireUnion<string | null>(
                    object["resolved_commit_sha"],
                    [
                        (member: unknown) =>
                            checked(wireString(member, null, null, null), [
                                "hfcache.identity.parse_commit_sha",
                            ]),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["reused_bytes"]: wireInteger(
                    object["reused_bytes"],
                    "0",
                    null,
                ),
                ["status"]: wireUnion<
                    | "skipped"
                    | "ref_moved_to_retained_revision"
                    | "published"
                    | "completed_with_warnings"
                    | "failed"
                    | "disabled"
                >(object["status"], [
                    (member: unknown) => wireLiteral(member, "skipped"),
                    (member: unknown) =>
                        wireLiteral(member, "ref_moved_to_retained_revision"),
                    (member: unknown) => wireLiteral(member, "published"),
                    (member: unknown) =>
                        wireLiteral(member, "completed_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                    (member: unknown) => wireLiteral(member, "disabled"),
                ]),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
            });
        })(value),
        ["hfcache.reporting.RepositoryRunResult._check"],
    );
}
export function decodeRepositoryStatusPayload(
    value: unknown,
): RepositoryStatusPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "current_commit_sha",
            "current_publication_generation",
            "enabled",
            "last_run_status",
            "managed",
            "repository_id",
            "repository_type",
            "requested_revision",
            "retained_generations",
            "retained_revisions",
            "upstream_state",
            "verification_state",
        ]);
        return Object.freeze({
            ["current_commit_sha"]: wireUnion<string | null>(
                object["current_commit_sha"],
                [
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_commit_sha",
                        ]),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["current_publication_generation"]: wireUnion<number | null>(
                object["current_publication_generation"],
                [
                    (member: unknown) => wireInteger(member, "1", null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["enabled"]: wireUnion<boolean | null>(object["enabled"], [
                (member: unknown) => wireBoolean(member),
                (member: unknown) => wireNull(member),
            ]),
            ["last_run_status"]: wireUnion<string | null>(
                object["last_run_status"],
                [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["managed"]: wireBoolean(object["managed"]),
            ["repository_id"]: checked(
                wireString(object["repository_id"], null, null, null),
                ["hfcache.identity.parse_repository_id"],
            ),
            ["repository_type"]: checked(
                wireUnion<"model" | "dataset">(object["repository_type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ["hfcache.identity.parse_repository_type"],
            ),
            ["requested_revision"]: wireUnion<string | null>(
                object["requested_revision"],
                [
                    (member: unknown) => wireString(member, null, null, null),
                    (member: unknown) => wireNull(member),
                ],
            ),
            ["retained_generations"]: wireArray(
                object["retained_generations"],
                (member: unknown) => wireInteger(member, "1", null),
                null,
                null,
            ),
            ["retained_revisions"]: wireInteger(
                object["retained_revisions"],
                "0",
                null,
            ),
            ["upstream_state"]: wireLiteral(
                object["upstream_state"],
                "unknown",
            ),
            ["verification_state"]: wireUnion<
                "verified" | "unverified" | "failed"
            >(object["verification_state"], [
                (member: unknown) => wireLiteral(member, "verified"),
                (member: unknown) => wireLiteral(member, "unverified"),
                (member: unknown) => wireLiteral(member, "failed"),
            ]),
        });
    })(value);
}
export function decodeRequestCandidatePayload(
    value: unknown,
): RequestCandidatePayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["candidate"]);
        return Object.freeze({
            ["candidate"]: checked(
                wireString(object["candidate"], null, null, null),
                ["hfcache.api.command_models._candidate_text"],
            ),
        });
    })(value);
}
export function decodeRequestCatalogRefreshSubmission(
    value: unknown,
): RequestCatalogRefreshSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["selectors", "revision_scope", "tags", "technical"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  wireString(member, null, 201, null),
                              null,
                              256,
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "revision_scope")
                    ? {
                          ["revision_scope"]: wireUnion<"current" | "retained">(
                              object["revision_scope"],
                              [
                                  (member: unknown) =>
                                      wireLiteral(member, "current"),
                                  (member: unknown) =>
                                      wireLiteral(member, "retained"),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "tags")
                    ? { ["tags"]: wireBoolean(object["tags"]) }
                    : {}),
                ...(Object.hasOwn(object, "technical")
                    ? { ["technical"]: wireBoolean(object["technical"]) }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.CatalogRefreshSubmission.canonical"],
    );
}
export function decodeRequestConfigApplicationSubmission(
    value: unknown,
): RequestConfigApplicationSubmission {
    return ((input: unknown) => {
        const object = wireObject(input, ["managed", "preview"]);
        return Object.freeze({
            ["managed"]: decodeRequestManagedEditRequest(object["managed"]),
            ["preview"]: decodeRequestConfigPreviewReference(object["preview"]),
        });
    })(value);
}
export function decodeRequestConfigPreviewReference(
    value: unknown,
): RequestConfigPreviewReference {
    return ((input: unknown) => {
        const object = wireObject(input, ["operation_id", "key"]);
        return Object.freeze({
            ["operation_id"]: checked(
                wireString(object["operation_id"], null, null, null),
                ["hfcache.identity.parse_run_id"],
            ),
            ["key"]: checked(wireString(object["key"], null, null, null), [
                "hfcache.config_models._preview_key",
            ]),
        });
    })(value);
}
export function decodeRequestDiagnosticsSubmission(
    value: unknown,
): RequestDiagnosticsSubmission {
    return ((input: unknown) => {
        const object = wireObject(input, ["read_only"]);
        return Object.freeze({
            ["read_only"]: wireBoolean(object["read_only"]),
        });
    })(value);
}
export function decodeRequestFullVerification(
    value: unknown,
): RequestFullVerification {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["mode"],
                ["revision", "run_id"],
            );
            return Object.freeze({
                ["mode"]: wireLiteral(object["mode"], "full"),
                ...(Object.hasOwn(object, "revision")
                    ? { ["revision"]: wireNull(object["revision"]) }
                    : {}),
                ...(Object.hasOwn(object, "run_id")
                    ? { ["run_id"]: wireNull(object["run_id"]) }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.VerificationSubmission.scope"],
    );
}
export function decodeRequestInitializationSubmission(
    value: unknown,
): RequestInitializationSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "archive_root",
                "archive_id",
                "confirm",
            ]);
            return Object.freeze({
                ["archive_root"]: checked(
                    wireString(object["archive_root"], null, null, null),
                    ["hfcache.api.maintenance_models._archive_root"],
                ),
                ["archive_id"]: checked(
                    wireString(object["archive_id"], null, null, null),
                    ["hfcache.config._parse_archive_id"],
                ),
                ["confirm"]: wireBoolean(object["confirm"]),
            });
        })(value),
        [
            "hfcache.api.maintenance_models.InitializationSubmission.confirmation",
        ],
    );
}
export function decodeRequestInstalledPlan(
    value: unknown,
): RequestInstalledPlan {
    return decodeRequestSyncSubmission(value);
}
export function decodeRequestInstalledValidation(
    value: unknown,
): RequestInstalledValidation {
    return decodeRequestInstalledValidationSubmission(value);
}
export function decodeRequestInstalledValidationSubmission(
    value: unknown,
): RequestInstalledValidationSubmission {
    return ((input: unknown) => {
        wireObject(input, []);
        return Object.freeze({});
    })(value);
}
export function decodeRequestLiteralCandidatePlan(
    value: unknown,
): RequestLiteralCandidatePlan {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["candidate"],
                ["selectors"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  checked(wireString(member, null, 256, null), [
                                      "hfcache.api.command_models._selection",
                                  ]),
                              null,
                              100,
                          ),
                      }
                    : {}),
                ["candidate"]: checked(
                    wireString(object["candidate"], null, null, null),
                    ["hfcache.api.command_models._candidate_text"],
                ),
            });
        })(value),
        ["hfcache.api.command_models.SyncSubmission.canonical"],
    );
}
export function decodeRequestLiteralCandidateValidation(
    value: unknown,
): RequestLiteralCandidateValidation {
    return decodeRequestCandidatePayload(value);
}
export function decodeRequestManagedEditRequest(
    value: unknown,
): RequestManagedEditRequest {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, ["base_revision", "edits"]);
            return Object.freeze({
                ["base_revision"]: checked(
                    wireString(object["base_revision"], null, null, null),
                    ["hfcache.config_models._revision"],
                ),
                ["edits"]: wireArray(
                    object["edits"],
                    (member: unknown) =>
                        wireUnion<
                            | RequestRepositoryUpsert
                            | RequestRepositoryRemove
                            | RequestSettingsReplace
                        >(member, [
                            (member: unknown) =>
                                decodeRequestRepositoryUpsert(member),
                            (member: unknown) =>
                                decodeRequestRepositoryRemove(member),
                            (member: unknown) =>
                                decodeRequestSettingsReplace(member),
                        ]),
                    null,
                    256,
                ),
            });
        })(value),
        ["hfcache.config_models.ManagedEditRequest.unique_edits"],
    );
}
export function decodeRequestManagedPlanRequest(
    value: unknown,
): RequestManagedPlanRequest {
    return ((input: unknown) => {
        const object = wireRequestObject(input, ["managed"], ["selectors"]);
        return Object.freeze({
            ["managed"]: decodeRequestManagedEditRequest(object["managed"]),
            ...(Object.hasOwn(object, "selectors")
                ? {
                      ["selectors"]: wireArray(
                          object["selectors"],
                          (member: unknown) =>
                              wireString(member, null, null, null),
                          null,
                          0,
                      ),
                  }
                : {}),
        });
    })(value);
}
export function decodeRequestManagedValidationRequest(
    value: unknown,
): RequestManagedValidationRequest {
    return ((input: unknown) => {
        const object = wireObject(input, ["managed"]);
        return Object.freeze({
            ["managed"]: decodeRequestManagedEditRequest(object["managed"]),
        });
    })(value);
}
export function decodeRequestNewVerification(
    value: unknown,
): RequestNewVerification {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["mode"],
                ["revision", "run_id"],
            );
            return Object.freeze({
                ["mode"]: wireLiteral(object["mode"], "new"),
                ...(Object.hasOwn(object, "revision")
                    ? { ["revision"]: wireNull(object["revision"]) }
                    : {}),
                ...(Object.hasOwn(object, "run_id")
                    ? {
                          ["run_id"]: wireUnion<string | null>(
                              object["run_id"],
                              [
                                  (member: unknown) =>
                                      checked(
                                          wireString(member, null, null, null),
                                          ["hfcache.identity.parse_run_id"],
                                      ),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.VerificationSubmission.scope"],
    );
}
export function decodeRequestPlanSubmission(
    value: unknown,
): RequestPlanSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["selectors", "candidate", "managed"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  checked(wireString(member, null, 256, null), [
                                      "hfcache.api.command_models._selection",
                                  ]),
                              null,
                              100,
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "candidate")
                    ? {
                          ["candidate"]: wireUnion<string | null>(
                              object["candidate"],
                              [
                                  (member: unknown) =>
                                      checked(
                                          wireString(member, null, null, null),
                                          [
                                              "hfcache.api.command_models._candidate_text",
                                          ],
                                      ),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "managed")
                    ? {
                          ["managed"]:
                              wireUnion<RequestManagedEditRequest | null>(
                                  object["managed"],
                                  [
                                      (member: unknown) =>
                                          decodeRequestManagedEditRequest(
                                              member,
                                          ),
                                      (member: unknown) => wireNull(member),
                                  ],
                              ),
                      }
                    : {}),
            });
        })(value),
        [
            "hfcache.api.command_models.SyncSubmission.canonical",
            "hfcache.api.command_models.PlanSubmission.explicit_candidate",
        ],
    );
}
export function decodeRequestProbeDiagnostics(
    value: unknown,
): RequestProbeDiagnostics {
    return ((input: unknown) => {
        const object = wireObject(input, ["read_only"]);
        return Object.freeze({
            ["read_only"]: wireLiteral(object["read_only"], false),
        });
    })(value);
}
export function decodeRequestPruneSubmission(
    value: unknown,
): RequestPruneSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(input, [], ["selectors"]);
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  checked(wireString(member, null, 256, null), [
                                      "hfcache.api.command_models._selection",
                                  ]),
                              null,
                              100,
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.SyncSubmission.canonical"],
    );
}
export function decodeRequestPurgeSubmission(
    value: unknown,
): RequestPurgeSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["selectors", "all_unmanaged"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  checked(wireString(member, null, 256, null), [
                                      "hfcache.api.maintenance_models._whole_repository",
                                  ]),
                              null,
                              100,
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "all_unmanaged")
                    ? {
                          ["all_unmanaged"]: wireBoolean(
                              object["all_unmanaged"],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.maintenance_models.PurgeSubmission.scope"],
    );
}
export function decodeRequestQuarantineSubmission(
    value: unknown,
): RequestQuarantineSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, ["transaction_ids"]);
            return Object.freeze({
                ["transaction_ids"]: wireArray(
                    object["transaction_ids"],
                    (member: unknown) =>
                        checked(wireString(member, null, null, null), [
                            "hfcache.identity.parse_transaction_id",
                        ]),
                    1,
                    100,
                ),
            });
        })(value),
        ["hfcache.api.maintenance_models.QuarantineSubmission.canonical"],
    );
}
export function decodeRequestReadOnlyDiagnostics(
    value: unknown,
): RequestReadOnlyDiagnostics {
    return ((input: unknown) => {
        const object = wireObject(input, ["read_only"]);
        return Object.freeze({
            ["read_only"]: wireLiteral(object["read_only"], true),
        });
    })(value);
}
export function decodeRequestRecoverySubmission(
    value: unknown,
): RequestRecoverySubmission {
    return ((input: unknown) => {
        wireObject(input, []);
        return Object.freeze({});
    })(value);
}
export function decodeRequestRepairReplacement(
    value: unknown,
): RequestRepairReplacement {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["retired_instance_grace_hours"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "retired_instance_grace_hours")
                    ? {
                          ["retired_instance_grace_hours"]: wireUnion<
                              number | null
                          >(object["retired_instance_grace_hours"], [
                              (member: unknown) =>
                                  wireInteger(member, "168", "8760"),
                              (member: unknown) => wireNull(member),
                          ]),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config_models.SettingsTable.nonempty"],
    );
}
export function decodeRequestRepairSubmission(
    value: unknown,
): RequestRepairSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(input, ["revision"], ["reason"]);
            return Object.freeze({
                ["revision"]: wireString(object["revision"], null, 256, null),
                ...(Object.hasOwn(object, "reason")
                    ? {
                          ["reason"]: wireString(
                              object["reason"],
                              null,
                              2048,
                              null,
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.maintenance_models.RepairSubmission.scope"],
    );
}
export function decodeRequestRepositoryConfig(
    value: unknown,
): RequestRepositoryConfig {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["id", "type"],
                ["revision", "enabled", "tags", "declared_dependencies"],
            );
            return Object.freeze({
                ["id"]: checked(wireString(object["id"], null, null, null), [
                    "hfcache.identity.parse_repository_id",
                ]),
                ["type"]: wireUnion<"model" | "dataset">(object["type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ...(Object.hasOwn(object, "revision")
                    ? {
                          ["revision"]: checked(
                              wireString(object["revision"], null, null, null),
                              ["hfcache.identity.parse_revision"],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "enabled")
                    ? { ["enabled"]: wireBoolean(object["enabled"]) }
                    : {}),
                ...(Object.hasOwn(object, "tags")
                    ? {
                          ["tags"]: checked(
                              wireArray(
                                  object["tags"],
                                  (member: unknown) =>
                                      wireString(member, null, null, null),
                                  null,
                                  64,
                              ),
                              ["hfcache.tags.normalize_tags"],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "declared_dependencies")
                    ? {
                          ["declared_dependencies"]: wireArray(
                              object["declared_dependencies"],
                              (member: unknown) =>
                                  checked(
                                      wireString(member, null, null, null),
                                      ["hfcache.identity.parse_repository_id"],
                                  ),
                              null,
                              null,
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config.RepositoryConfig._check"],
    );
}
export function decodeRequestRepositoryRemove(
    value: unknown,
): RequestRepositoryRemove {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "kind",
            "repository_type",
            "repository_id",
        ]);
        return Object.freeze({
            ["kind"]: wireLiteral(object["kind"], "repository-remove"),
            ["repository_type"]: wireUnion<"model" | "dataset">(
                object["repository_type"],
                [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ],
            ),
            ["repository_id"]: checked(
                wireString(object["repository_id"], null, null, null),
                ["hfcache.identity.parse_repository_id"],
            ),
        });
    })(value);
}
export function decodeRequestRepositoryUpsert(
    value: unknown,
): RequestRepositoryUpsert {
    return ((input: unknown) => {
        const object = wireObject(input, ["kind", "repository"]);
        return Object.freeze({
            ["kind"]: wireLiteral(object["kind"], "repository-upsert"),
            ["repository"]: decodeRequestRepositoryConfig(object["repository"]),
        });
    })(value);
}
export function decodeRequestRevisionVerification(
    value: unknown,
): RequestRevisionVerification {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["mode", "revision"],
                ["run_id"],
            );
            return Object.freeze({
                ["mode"]: wireLiteral(object["mode"], "revision"),
                ["revision"]: wireString(object["revision"], null, 256, null),
                ...(Object.hasOwn(object, "run_id")
                    ? { ["run_id"]: wireNull(object["run_id"]) }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.VerificationSubmission.scope"],
    );
}
export function decodeRequestSettingsReplace(
    value: unknown,
): RequestSettingsReplace {
    return ((input: unknown) => {
        const object = wireObject(input, ["kind", "settings"]);
        return Object.freeze({
            ["kind"]: wireLiteral(object["kind"], "settings-replace"),
            ["settings"]: decodeRequestSettingsReplacement(object["settings"]),
        });
    })(value);
}
export function decodeRequestSettingsReplacement(
    value: unknown,
): RequestSettingsReplacement {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["storage", "sync", "verification", "repair"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "storage")
                    ? {
                          ["storage"]:
                              wireUnion<RequestStorageReplacement | null>(
                                  object["storage"],
                                  [
                                      (member: unknown) =>
                                          decodeRequestStorageReplacement(
                                              member,
                                          ),
                                      (member: unknown) => wireNull(member),
                                  ],
                              ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "sync")
                    ? {
                          ["sync"]: wireUnion<RequestSyncReplacement | null>(
                              object["sync"],
                              [
                                  (member: unknown) =>
                                      decodeRequestSyncReplacement(member),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "verification")
                    ? {
                          ["verification"]:
                              wireUnion<RequestVerificationReplacement | null>(
                                  object["verification"],
                                  [
                                      (member: unknown) =>
                                          decodeRequestVerificationReplacement(
                                              member,
                                          ),
                                      (member: unknown) => wireNull(member),
                                  ],
                              ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "repair")
                    ? {
                          ["repair"]:
                              wireUnion<RequestRepairReplacement | null>(
                                  object["repair"],
                                  [
                                      (member: unknown) =>
                                          decodeRequestRepairReplacement(
                                              member,
                                          ),
                                      (member: unknown) => wireNull(member),
                                  ],
                              ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config_models.SettingsTable.nonempty"],
    );
}
export function decodeRequestStorageReplacement(
    value: unknown,
): RequestStorageReplacement {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                [
                    "publication_mode",
                    "minimum_free_space_gib",
                    "minimum_free_space_percent",
                    "maximum_revisions",
                ],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "publication_mode")
                    ? {
                          ["publication_mode"]: wireUnion<
                              ("hardlink" | "copy") | null
                          >(object["publication_mode"], [
                              (member: unknown) =>
                                  wireUnion<"hardlink" | "copy">(member, [
                                      (member: unknown) =>
                                          wireLiteral(member, "hardlink"),
                                      (member: unknown) =>
                                          wireLiteral(member, "copy"),
                                  ]),
                              (member: unknown) => wireNull(member),
                          ]),
                      }
                    : {}),
                ...(Object.hasOwn(object, "minimum_free_space_gib")
                    ? {
                          ["minimum_free_space_gib"]: wireUnion<number | null>(
                              object["minimum_free_space_gib"],
                              [
                                  (member: unknown) =>
                                      wireInteger(member, "0", "1048576"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "minimum_free_space_percent")
                    ? {
                          ["minimum_free_space_percent"]: wireUnion<
                              number | null
                          >(object["minimum_free_space_percent"], [
                              (member: unknown) =>
                                  wireInteger(member, "0", "100"),
                              (member: unknown) => wireNull(member),
                          ]),
                      }
                    : {}),
                ...(Object.hasOwn(object, "maximum_revisions")
                    ? {
                          ["maximum_revisions"]: wireUnion<number | null>(
                              object["maximum_revisions"],
                              [
                                  (member: unknown) =>
                                      checked(wireInteger(member, null, null), [
                                          "hfcache.config_models._retention",
                                      ]),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config_models.SettingsTable.nonempty"],
    );
}
export function decodeRequestSyncReplacement(
    value: unknown,
): RequestSyncReplacement {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                [
                    "max_workers",
                    "lock_wait_seconds",
                    "continue_on_repository_error",
                    "dependency_policy",
                    "stale_staging_age_hours",
                ],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "max_workers")
                    ? {
                          ["max_workers"]: wireUnion<number | null>(
                              object["max_workers"],
                              [
                                  (member: unknown) =>
                                      wireInteger(member, "1", "32"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "lock_wait_seconds")
                    ? {
                          ["lock_wait_seconds"]: wireUnion<number | null>(
                              object["lock_wait_seconds"],
                              [
                                  (member: unknown) =>
                                      wireInteger(member, "0", "86400"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "continue_on_repository_error")
                    ? {
                          ["continue_on_repository_error"]: wireUnion<
                              boolean | null
                          >(object["continue_on_repository_error"], [
                              (member: unknown) => wireBoolean(member),
                              (member: unknown) => wireNull(member),
                          ]),
                      }
                    : {}),
                ...(Object.hasOwn(object, "dependency_policy")
                    ? {
                          ["dependency_policy"]: wireUnion<"warn" | null>(
                              object["dependency_policy"],
                              [
                                  (member: unknown) =>
                                      wireLiteral(member, "warn"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "stale_staging_age_hours")
                    ? {
                          ["stale_staging_age_hours"]: wireUnion<number | null>(
                              object["stale_staging_age_hours"],
                              [
                                  (member: unknown) =>
                                      wireInteger(member, "1", "8760"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config_models.SettingsTable.nonempty"],
    );
}
export function decodeRequestSyncSubmission(
    value: unknown,
): RequestSyncSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(input, [], ["selectors"]);
            return Object.freeze({
                ...(Object.hasOwn(object, "selectors")
                    ? {
                          ["selectors"]: wireArray(
                              object["selectors"],
                              (member: unknown) =>
                                  checked(wireString(member, null, 256, null), [
                                      "hfcache.api.command_models._selection",
                                  ]),
                              null,
                              100,
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.SyncSubmission.canonical"],
    );
}
export function decodeRequestValidationSubmission(
    value: unknown,
): RequestValidationSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                [],
                ["candidate", "managed"],
            );
            return Object.freeze({
                ...(Object.hasOwn(object, "candidate")
                    ? {
                          ["candidate"]: wireUnion<string | null>(
                              object["candidate"],
                              [
                                  (member: unknown) =>
                                      checked(
                                          wireString(member, null, null, null),
                                          [
                                              "hfcache.api.command_models._candidate_text",
                                          ],
                                      ),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "managed")
                    ? {
                          ["managed"]:
                              wireUnion<RequestManagedEditRequest | null>(
                                  object["managed"],
                                  [
                                      (member: unknown) =>
                                          decodeRequestManagedEditRequest(
                                              member,
                                          ),
                                      (member: unknown) => wireNull(member),
                                  ],
                              ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.ValidationSubmission.explicit_candidate"],
    );
}
export function decodeRequestVerificationReplacement(
    value: unknown,
): RequestVerificationReplacement {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(input, [], ["lock_wait_seconds"]);
            return Object.freeze({
                ...(Object.hasOwn(object, "lock_wait_seconds")
                    ? {
                          ["lock_wait_seconds"]: wireUnion<number | null>(
                              object["lock_wait_seconds"],
                              [
                                  (member: unknown) =>
                                      wireInteger(member, "0", "604800"),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.config_models.SettingsTable.nonempty"],
    );
}
export function decodeRequestVerificationSubmission(
    value: unknown,
): RequestVerificationSubmission {
    return checked(
        ((input: unknown) => {
            const object = wireRequestObject(
                input,
                ["mode"],
                ["revision", "run_id"],
            );
            return Object.freeze({
                ["mode"]: wireUnion<"new" | "full" | "revision">(
                    object["mode"],
                    [
                        (member: unknown) => wireLiteral(member, "new"),
                        (member: unknown) => wireLiteral(member, "full"),
                        (member: unknown) => wireLiteral(member, "revision"),
                    ],
                ),
                ...(Object.hasOwn(object, "revision")
                    ? {
                          ["revision"]: wireUnion<string | null>(
                              object["revision"],
                              [
                                  (member: unknown) =>
                                      wireString(member, null, 256, null),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
                ...(Object.hasOwn(object, "run_id")
                    ? {
                          ["run_id"]: wireUnion<string | null>(
                              object["run_id"],
                              [
                                  (member: unknown) =>
                                      checked(
                                          wireString(member, null, null, null),
                                          ["hfcache.identity.parse_run_id"],
                                      ),
                                  (member: unknown) => wireNull(member),
                              ],
                          ),
                      }
                    : {}),
            });
        })(value),
        ["hfcache.api.command_models.VerificationSubmission.scope"],
    );
}
export function decodeRevisionManifest(value: unknown): RevisionManifest {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "commit_sha",
                "dependencies",
                "download_completed_at",
                "download_started_at",
                "file_count",
                "files",
                "first_observed_at",
                "hub_endpoint",
                "huggingface_hub_version",
                "publication_generation",
                "publication_id",
                "publication_mode",
                "published_at",
                "python_version",
                "repair",
                "repository_id",
                "repository_type",
                "requested_revision",
                "total_bytes",
                "tree",
                "verification",
                "verified_at",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["commit_sha"]: checked(
                    wireString(object["commit_sha"], null, null, null),
                    ["hfcache.identity.parse_commit_sha"],
                ),
                ["dependencies"]: wireArray(
                    object["dependencies"],
                    (member: unknown) => decodeDependencyObservation(member),
                    null,
                    null,
                ),
                ["download_completed_at"]: checked(
                    wireString(
                        object["download_completed_at"],
                        null,
                        null,
                        null,
                    ),
                    ["timestamp.serialized"],
                ),
                ["download_started_at"]: checked(
                    wireString(object["download_started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["file_count"]: wireInteger(object["file_count"], "0", null),
                ["files"]: wireArray(
                    object["files"],
                    (member: unknown) => decodeFileEntry(member),
                    null,
                    null,
                ),
                ["first_observed_at"]: checked(
                    wireString(object["first_observed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["hub_endpoint"]: wireString(
                    object["hub_endpoint"],
                    null,
                    null,
                    null,
                ),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["publication_generation"]: wireInteger(
                    object["publication_generation"],
                    "1",
                    null,
                ),
                ["publication_id"]: checked(
                    wireString(object["publication_id"], null, null, null),
                    ["hfcache.identity.parse_publication_id"],
                ),
                ["publication_mode"]: wireUnion<"hardlink" | "copy">(
                    object["publication_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "hardlink"),
                        (member: unknown) => wireLiteral(member, "copy"),
                    ],
                ),
                ["published_at"]: checked(
                    wireString(object["published_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["repair"]: wireUnion<RepairProvenance | null>(
                    object["repair"],
                    [
                        (member: unknown) => decodeRepairProvenance(member),
                        (member: unknown) => wireNull(member),
                    ],
                ),
                ["repository_id"]: checked(
                    wireString(object["repository_id"], null, null, null),
                    ["hfcache.identity.parse_repository_id"],
                ),
                ["repository_type"]: checked(
                    wireUnion<"model" | "dataset">(object["repository_type"], [
                        (member: unknown) => wireLiteral(member, "model"),
                        (member: unknown) => wireLiteral(member, "dataset"),
                    ]),
                    ["hfcache.identity.parse_repository_type"],
                ),
                ["requested_revision"]: wireString(
                    object["requested_revision"],
                    null,
                    null,
                    null,
                ),
                ["total_bytes"]: wireInteger(object["total_bytes"], "0", null),
                ["tree"]: checked(
                    wireString(object["tree"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
                ["verification"]: decodeVerificationSummary(
                    object["verification"],
                ),
                ["verified_at"]: checked(
                    wireString(object["verified_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.manifests.RevisionManifest._check_arithmetic",
            "hfcache.manifests.RevisionManifest._check_paths",
            "hfcache.manifests.RevisionManifest._check_ordering",
            "hfcache.manifests.RevisionManifest._check_timeline",
        ],
    );
}
export function decodeRevisionPayload(value: unknown): RevisionPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "repository_id",
            "repository_type",
            "commit_sha",
            "file_count",
            "publication_generation",
            "publication_id",
            "published_at",
            "total_bytes",
            "verification_state",
        ]);
        return Object.freeze({
            ["repository_id"]: checked(
                wireString(object["repository_id"], null, null, null),
                ["hfcache.identity.parse_repository_id"],
            ),
            ["repository_type"]: checked(
                wireUnion<"model" | "dataset">(object["repository_type"], [
                    (member: unknown) => wireLiteral(member, "model"),
                    (member: unknown) => wireLiteral(member, "dataset"),
                ]),
                ["hfcache.identity.parse_repository_type"],
            ),
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["file_count"]: wireInteger(object["file_count"], "0", null),
            ["publication_generation"]: wireInteger(
                object["publication_generation"],
                "1",
                null,
            ),
            ["publication_id"]: checked(
                wireString(object["publication_id"], null, null, null),
                ["hfcache.identity.parse_publication_id"],
            ),
            ["published_at"]: checked(
                wireString(object["published_at"], null, null, null),
                ["timestamp.wire"],
            ),
            ["total_bytes"]: wireInteger(object["total_bytes"], "0", null),
            ["verification_state"]: wireUnion<
                "verified" | "unverified" | "failed"
            >(object["verification_state"], [
                (member: unknown) => wireLiteral(member, "verified"),
                (member: unknown) => wireLiteral(member, "unverified"),
                (member: unknown) => wireLiteral(member, "failed"),
            ]),
        });
    })(value);
}
export function decodeRevisionSummary(value: unknown): RevisionSummary {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "commit_sha",
            "publication_generation",
        ]);
        return Object.freeze({
            ["commit_sha"]: checked(
                wireString(object["commit_sha"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["publication_generation"]: wireInteger(
                object["publication_generation"],
                "1",
                null,
            ),
        });
    })(value);
}
export function decodeRevisionsPayload(value: unknown): RevisionsPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["revisions"]);
        return Object.freeze({
            ["revisions"]: wireArray(
                object["revisions"],
                (member: unknown) => decodeRevisionPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeRunReport(value: unknown): RunReport {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "archive_id",
                "command",
                "completed_at",
                "config_fingerprint",
                "errors",
                "exit_code",
                "hostname",
                "huggingface_hub_version",
                "invocation_mode",
                "outcome",
                "python_version",
                "run_id",
                "started_at",
                "warnings",
                "repositories",
                "totals",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["archive_id"]: wireString(
                    object["archive_id"],
                    null,
                    null,
                    null,
                ),
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["config_fingerprint"]: checked(
                    wireString(object["config_fingerprint"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["hostname"]: wireString(object["hostname"], null, null, null),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["invocation_mode"]: wireUnion<"systemd" | "interactive">(
                    object["invocation_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "systemd"),
                        (member: unknown) => wireLiteral(member, "interactive"),
                    ],
                ),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["repositories"]: wireArray(
                    object["repositories"],
                    (member: unknown) => decodeRepositoryRunResult(member),
                    null,
                    null,
                ),
                ["totals"]: decodeRunTotals(object["totals"]),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.reporting.RunEnvelope._check_envelope",
            "hfcache.reporting.RunReport._check",
        ],
    );
}
export function decodeRunResultPayload(value: unknown): RunResultPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "archive_id",
                "command",
                "completed_at",
                "config_fingerprint",
                "errors",
                "exit_code",
                "hostname",
                "huggingface_hub_version",
                "invocation_mode",
                "outcome",
                "python_version",
                "run_id",
                "started_at",
                "warnings",
                "repositories",
                "totals",
                "report",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["archive_id"]: wireString(
                    object["archive_id"],
                    null,
                    null,
                    null,
                ),
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["config_fingerprint"]: checked(
                    wireString(object["config_fingerprint"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["hostname"]: wireString(object["hostname"], null, null, null),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["invocation_mode"]: wireUnion<"systemd" | "interactive">(
                    object["invocation_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "systemd"),
                        (member: unknown) => wireLiteral(member, "interactive"),
                    ],
                ),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["repositories"]: wireArray(
                    object["repositories"],
                    (member: unknown) => decodeRepositoryRunResult(member),
                    null,
                    null,
                ),
                ["totals"]: decodeRunTotals(object["totals"]),
                ["report"]: checked(
                    wireString(object["report"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.reporting.RunEnvelope._check_envelope",
            "hfcache.reporting.RunReport._check",
        ],
    );
}
export function decodeRunTotals(value: unknown): RunTotals {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "downloaded_bytes",
            "hashed_bytes",
            "published_bytes",
            "pruned_logical_bytes",
            "reused_bytes",
            "xet_cache_peak_bytes",
        ]);
        return Object.freeze({
            ["downloaded_bytes"]: wireInteger(
                object["downloaded_bytes"],
                "0",
                null,
            ),
            ["hashed_bytes"]: wireInteger(object["hashed_bytes"], "0", null),
            ["published_bytes"]: wireInteger(
                object["published_bytes"],
                "0",
                null,
            ),
            ["pruned_logical_bytes"]: wireInteger(
                object["pruned_logical_bytes"],
                "0",
                null,
            ),
            ["reused_bytes"]: wireInteger(object["reused_bytes"], "0", null),
            ["xet_cache_peak_bytes"]: wireInteger(
                object["xet_cache_peak_bytes"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeRunsPayload(value: unknown): RunsPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["runs"]);
        return Object.freeze({
            ["runs"]: wireArray(
                object["runs"],
                (member: unknown) =>
                    checked(wireString(member, null, null, null), [
                        "hfcache.identity.parse_run_id",
                    ]),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeSourceObservation(value: unknown): SourceObservation {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "path",
                "sha256",
                "field",
                "values",
                "evidence",
            ]);
            return Object.freeze({
                ["path"]: checked(
                    wireString(object["path"], null, null, null),
                    ["hfcache.models._repository_path"],
                ),
                ["sha256"]: checked(
                    wireString(object["sha256"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["field"]: wireUnion<
                    | "task"
                    | "language"
                    | "license"
                    | "base_model"
                    | "upstream_tags"
                    | "dataset_config"
                    | "dataset_split"
                    | "dataset_feature"
                    | "format"
                >(object["field"], [
                    (member: unknown) => wireLiteral(member, "task"),
                    (member: unknown) => wireLiteral(member, "language"),
                    (member: unknown) => wireLiteral(member, "license"),
                    (member: unknown) => wireLiteral(member, "base_model"),
                    (member: unknown) => wireLiteral(member, "upstream_tags"),
                    (member: unknown) => wireLiteral(member, "dataset_config"),
                    (member: unknown) => wireLiteral(member, "dataset_split"),
                    (member: unknown) => wireLiteral(member, "dataset_feature"),
                    (member: unknown) => wireLiteral(member, "format"),
                ]),
                ["values"]: wireArray(
                    object["values"],
                    (member: unknown) => wireString(member, null, 2048, null),
                    null,
                    64,
                ),
                ["evidence"]: wireUnion<"declaration" | "header" | "filename">(
                    object["evidence"],
                    [
                        (member: unknown) => wireLiteral(member, "declaration"),
                        (member: unknown) => wireLiteral(member, "header"),
                        (member: unknown) => wireLiteral(member, "filename"),
                    ],
                ),
            });
        })(value),
        ["hfcache.catalog_models.SourceObservation.ordered"],
    );
}
export function decodeStatusPayload(value: unknown): StatusPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["archive", "repositories"]);
        return Object.freeze({
            ["archive"]: wireUnion<
                ReachableArchivePayload | UnreachableArchivePayload
            >(object["archive"], [
                (member: unknown) => decodeReachableArchivePayload(member),
                (member: unknown) => decodeUnreachableArchivePayload(member),
            ]),
            ["repositories"]: wireArray(
                object["repositories"],
                (member: unknown) => decodeRepositoryStatusPayload(member),
                null,
                null,
            ),
        });
    })(value);
}
export function decodeUiAdminPermission(value: unknown): UiAdminPermission {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "capability",
                "granted",
                "effective",
                "reason",
            ]);
            return Object.freeze({
                ["capability"]: wireUnion<
                    | "config-read"
                    | "config-write"
                    | "host-read"
                    | "observer-stop"
                    | "schedule-write"
                >(object["capability"], [
                    (member: unknown) => wireLiteral(member, "config-read"),
                    (member: unknown) => wireLiteral(member, "config-write"),
                    (member: unknown) => wireLiteral(member, "host-read"),
                    (member: unknown) => wireLiteral(member, "observer-stop"),
                    (member: unknown) => wireLiteral(member, "schedule-write"),
                ]),
                ["granted"]: wireBoolean(object["granted"]),
                ["effective"]: wireBoolean(object["effective"]),
                ["reason"]: wireUnion<
                    "allowed" | "not_granted" | "feature_unavailable"
                >(object["reason"], [
                    (member: unknown) => wireLiteral(member, "allowed"),
                    (member: unknown) => wireLiteral(member, "not_granted"),
                    (member: unknown) =>
                        wireLiteral(member, "feature_unavailable"),
                ]),
            });
        })(value),
        ["hfcache.ui_models.UiAdminPermission._permission"],
    );
}
export function decodeUiAssetManifest(value: unknown): UiAssetManifest {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "kind",
                "build",
                "entrypoint",
                "meta_identity",
                "members",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.ui_models._one"],
                ),
                ["kind"]: wireLiteral(object["kind"], "hfcache_web_assets"),
                ["build"]: decodeUiBuildMetadata(object["build"]),
                ["entrypoint"]: wireLiteral(object["entrypoint"], "index.html"),
                ["meta_identity"]: decodeUiHtmlMetaIdentity(
                    object["meta_identity"],
                ),
                ["members"]: wireArray(
                    object["members"],
                    (member: unknown) => decodeUiAssetMember(member),
                    1,
                    4096,
                ),
            });
        })(value),
        ["hfcache.ui_models.UiAssetManifest._members"],
    );
}
export function decodeUiAssetMember(value: unknown): UiAssetMember {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "path",
                "bytes",
                "sha256",
                "mime",
            ]);
            return Object.freeze({
                ["path"]: checked(
                    wireString(object["path"], null, null, null),
                    ["hfcache.ui_models._asset_path"],
                ),
                ["bytes"]: wireInteger(object["bytes"], "0", "8388608"),
                ["sha256"]: checked(
                    wireString(object["sha256"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["mime"]: wireUnion<
                    | "text/html"
                    | "text/css"
                    | "text/javascript"
                    | "application/json"
                    | "image/png"
                    | "image/webp"
                    | "font/woff2"
                    | "text/plain"
                >(object["mime"], [
                    (member: unknown) => wireLiteral(member, "text/html"),
                    (member: unknown) => wireLiteral(member, "text/css"),
                    (member: unknown) => wireLiteral(member, "text/javascript"),
                    (member: unknown) =>
                        wireLiteral(member, "application/json"),
                    (member: unknown) => wireLiteral(member, "image/png"),
                    (member: unknown) => wireLiteral(member, "image/webp"),
                    (member: unknown) => wireLiteral(member, "font/woff2"),
                    (member: unknown) => wireLiteral(member, "text/plain"),
                ]),
            });
        })(value),
        ["hfcache.ui_models.UiAssetMember._member"],
    );
}
export function decodeUiBootstrap(value: unknown): UiBootstrap {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "kind",
                "ui_contract_version",
                "rest_api_schema_version",
                "wire_source_digest",
                "instance_id",
                "authority_epoch",
                "configured_archive_id",
                "archive_identity_source",
                "config_fingerprint",
                "configured_origin",
                "paths",
                "user",
                "build",
            ]);
            return Object.freeze({
                ["schema_version"]: checked(
                    wireLiteral(object["schema_version"], 1),
                    ["hfcache.ui_models._one"],
                ),
                ["kind"]: wireLiteral(object["kind"], "hfcache_ui_bootstrap"),
                ["ui_contract_version"]: checked(
                    wireLiteral(object["ui_contract_version"], 1),
                    ["hfcache.ui_models._one"],
                ),
                ["rest_api_schema_version"]: checked(
                    wireLiteral(object["rest_api_schema_version"], 1),
                    ["hfcache.ui_models._one"],
                ),
                ["wire_source_digest"]: checked(
                    wireString(object["wire_source_digest"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["instance_id"]: checked(
                    wireString(object["instance_id"], null, null, null),
                    ["hfcache.ui_models._instance"],
                ),
                ["authority_epoch"]: checked(
                    wireString(object["authority_epoch"], null, null, null),
                    ["hfcache.ui_models._instance"],
                ),
                ["configured_archive_id"]: checked(
                    wireString(
                        object["configured_archive_id"],
                        null,
                        null,
                        null,
                    ),
                    ["hfcache.models._parse_archive_id"],
                ),
                ["archive_identity_source"]: wireLiteral(
                    object["archive_identity_source"],
                    "installed_policy",
                ),
                ["config_fingerprint"]: wireNull(object["config_fingerprint"]),
                ["configured_origin"]: checked(
                    wireString(object["configured_origin"], null, null, null),
                    ["hfcache.ui_models._origin"],
                ),
                ["paths"]: decodeUiPaths(object["paths"]),
                ["user"]: decodeUiUser(object["user"]),
                ["build"]: decodeUiBuildIdentity(object["build"]),
            });
        })(value),
        ["hfcache.ui_models.UiBootstrap._bootstrap"],
    );
}
export function decodeUiBuildIdentity(value: unknown): UiBuildIdentity {
    return ((input: unknown) => {
        const object = wireObject(input, ["asset_manifest_sha256", "metadata"]);
        return Object.freeze({
            ["asset_manifest_sha256"]: checked(
                wireString(object["asset_manifest_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["metadata"]: decodeUiBuildMetadata(object["metadata"]),
        });
    })(value);
}
export function decodeUiBuildMetadata(value: unknown): UiBuildMetadata {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "application_version",
            "source_commit",
            "source_snapshot_sha256",
            "source_dirty",
            "ui_contract_version",
            "rest_api_schema_version",
            "wire_source_digest",
            "pnpm_lock_sha256",
            "toolchain",
            "toolchain_sha256",
            "licenses_sha256",
            "notices_sha256",
        ]);
        return Object.freeze({
            ["application_version"]: checked(
                wireString(object["application_version"], null, 128, null),
                ["hfcache.ui_models._ascii"],
            ),
            ["source_commit"]: checked(
                wireString(object["source_commit"], null, null, null),
                ["hfcache.identity.parse_commit_sha"],
            ),
            ["source_snapshot_sha256"]: checked(
                wireString(object["source_snapshot_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["source_dirty"]: wireBoolean(object["source_dirty"]),
            ["ui_contract_version"]: checked(
                wireLiteral(object["ui_contract_version"], 1),
                ["hfcache.ui_models._one"],
            ),
            ["rest_api_schema_version"]: checked(
                wireLiteral(object["rest_api_schema_version"], 1),
                ["hfcache.ui_models._one"],
            ),
            ["wire_source_digest"]: checked(
                wireString(object["wire_source_digest"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["pnpm_lock_sha256"]: checked(
                wireString(object["pnpm_lock_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["toolchain"]: decodeUiToolchain(object["toolchain"]),
            ["toolchain_sha256"]: checked(
                wireString(object["toolchain_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["licenses_sha256"]: checked(
                wireString(object["licenses_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
            ["notices_sha256"]: checked(
                wireString(object["notices_sha256"], null, null, null),
                ["hfcache.models._parse_sha256"],
            ),
        });
    })(value);
}
export function decodeUiHtmlMetaIdentity(value: unknown): UiHtmlMetaIdentity {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "ui_base",
            "bootstrap_path",
            "asset_fingerprint",
            "ui_contract",
        ]);
        return Object.freeze({
            ["ui_base"]: wireLiteral(
                object["ui_base"],
                "__HFCACHE_UI_BASE_V1__",
            ),
            ["bootstrap_path"]: wireLiteral(
                object["bootstrap_path"],
                "__HFCACHE_UI_BOOTSTRAP_V1__",
            ),
            ["asset_fingerprint"]: wireLiteral(
                object["asset_fingerprint"],
                "__HFCACHE_UI_FINGERPRINT_V1__",
            ),
            ["ui_contract"]: wireLiteral(
                object["ui_contract"],
                "__HFCACHE_UI_CONTRACT_V1__",
            ),
        });
    })(value);
}
export function decodeUiPaths(value: unknown): UiPaths {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "public_prefix",
                "effective_prefix",
                "ui_base",
                "bootstrap",
                "api_base",
                "mcp_base",
            ]);
            return Object.freeze({
                ["public_prefix"]: checked(
                    wireString(object["public_prefix"], null, null, null),
                    ["hfcache.ui_models._prefix"],
                ),
                ["effective_prefix"]: checked(
                    wireString(object["effective_prefix"], null, null, null),
                    ["hfcache.ui_models._prefix"],
                ),
                ["ui_base"]: checked(
                    wireString(object["ui_base"], null, 3076, null),
                    ["hfcache.ui_models._ascii"],
                ),
                ["bootstrap"]: checked(
                    wireString(object["bootstrap"], null, 3090, null),
                    ["hfcache.ui_models._ascii"],
                ),
                ["api_base"]: checked(
                    wireString(object["api_base"], null, 3079, null),
                    ["hfcache.ui_models._ascii"],
                ),
                ["mcp_base"]: wireUnion<string | null>(object["mcp_base"], [
                    (member: unknown) =>
                        checked(wireString(member, null, 3077, null), [
                            "hfcache.ui_models._ascii",
                        ]),
                    (member: unknown) => wireNull(member),
                ]),
            });
        })(value),
        ["hfcache.ui_models.UiPaths._paths"],
    );
}
export function decodeUiToolchain(value: unknown): UiToolchain {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "node",
            "pnpm",
            "typescript",
            "vite",
        ]);
        return Object.freeze({
            ["node"]: checked(wireString(object["node"], null, 64, null), [
                "hfcache.ui_models._ascii",
            ]),
            ["pnpm"]: checked(wireString(object["pnpm"], null, 64, null), [
                "hfcache.ui_models._ascii",
            ]),
            ["typescript"]: checked(
                wireString(object["typescript"], null, 64, null),
                ["hfcache.ui_models._ascii"],
            ),
            ["vite"]: checked(wireString(object["vite"], null, 64, null), [
                "hfcache.ui_models._ascii",
            ]),
        });
    })(value);
}
export function decodeUiUser(value: unknown): UiUser {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "subject",
                "display_name",
                "authentication_method",
                "credential_class",
                "rest_capabilities",
                "admin_permissions",
            ]);
            return Object.freeze({
                ["subject"]: checked(
                    wireString(object["subject"], null, null, null),
                    ["hfcache.ui_models._subject"],
                ),
                ["display_name"]: checked(
                    wireString(object["display_name"], null, null, null),
                    ["hfcache.ui_models._subject"],
                ),
                ["authentication_method"]: wireLiteral(
                    object["authentication_method"],
                    "basic",
                ),
                ["credential_class"]: wireLiteral(
                    object["credential_class"],
                    "rest-writer",
                ),
                ["rest_capabilities"]: wireArray(
                    object["rest_capabilities"],
                    (member: unknown) =>
                        wireUnion<"read" | "write">(member, [
                            (member: unknown) => wireLiteral(member, "read"),
                            (member: unknown) => wireLiteral(member, "write"),
                        ]),
                    2,
                    2,
                ),
                ["admin_permissions"]: wireArray(
                    object["admin_permissions"],
                    (member: unknown) => decodeUiAdminPermission(member),
                    5,
                    5,
                ),
            });
        })(value),
        ["hfcache.ui_models.UiUser._user"],
    );
}
export function decodeUnavailableHealthPayload(
    value: unknown,
): UnavailableHealthPayload {
    return ((input: unknown) => {
        const object = wireObject(input, ["ready", "policy_valid", "archive"]);
        return Object.freeze({
            ["ready"]: wireLiteral(object["ready"], true),
            ["policy_valid"]: wireUnion<false | null>(object["policy_valid"], [
                (member: unknown) => wireLiteral(member, false),
                (member: unknown) => wireNull(member),
            ]),
            ["archive"]: wireNull(object["archive"]),
        });
    })(value);
}
export function decodeUnreachableArchivePayload(
    value: unknown,
): UnreachableArchivePayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "archive_id",
            "root",
            "reachable",
            "verification",
        ]);
        return Object.freeze({
            ["archive_id"]: checked(
                wireString(object["archive_id"], null, null, null),
                ["hfcache.models._parse_archive_id"],
            ),
            ["root"]: wireString(object["root"], null, null, null),
            ["reachable"]: wireLiteral(object["reachable"], false),
            ["verification"]: decodeVerificationHealthPayload(
                object["verification"],
            ),
        });
    })(value);
}
export function decodeUpstreamIdentifiers(value: unknown): UpstreamIdentifiers {
    return ((input: unknown) => {
        const object = wireObject(input, ["git_oid", "lfs_sha256", "xet_hash"]);
        return Object.freeze({
            ["git_oid"]: wireUnion<string | null>(object["git_oid"], [
                (member: unknown) => wireString(member, null, null, null),
                (member: unknown) => wireNull(member),
            ]),
            ["lfs_sha256"]: wireUnion<string | null>(object["lfs_sha256"], [
                (member: unknown) => wireString(member, null, null, null),
                (member: unknown) => wireNull(member),
            ]),
            ["xet_hash"]: wireUnion<string | null>(object["xet_hash"], [
                (member: unknown) => wireString(member, null, null, null),
                (member: unknown) => wireNull(member),
            ]),
        });
    })(value);
}
export function decodeVariantMember(value: unknown): VariantMember {
    return ((input: unknown) => {
        const object = wireObject(input, ["path", "size_bytes"]);
        return Object.freeze({
            ["path"]: checked(wireString(object["path"], null, null, null), [
                "hfcache.models._repository_path",
            ]),
            ["size_bytes"]: wireInteger(
                object["size_bytes"],
                "0",
                "9223372036854775807",
            ),
        });
    })(value);
}
export function decodeVerificationHealthPayload(
    value: unknown,
): VerificationHealthPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "degraded",
            "last_full_verification",
            "outstanding_failures",
        ]);
        return Object.freeze({
            ["degraded"]: wireBoolean(object["degraded"]),
            ["last_full_verification"]:
                wireUnion<FullVerificationSummary | null>(
                    object["last_full_verification"],
                    [
                        (member: unknown) =>
                            decodeFullVerificationSummary(member),
                        (member: unknown) => wireNull(member),
                    ],
                ),
            ["outstanding_failures"]: wireInteger(
                object["outstanding_failures"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeVerificationReport(value: unknown): VerificationReport {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "archive_id",
                "command",
                "completed_at",
                "config_fingerprint",
                "errors",
                "exit_code",
                "hostname",
                "huggingface_hub_version",
                "invocation_mode",
                "outcome",
                "python_version",
                "run_id",
                "started_at",
                "warnings",
                "findings",
                "mode",
                "scope",
                "throughput_bytes_per_second",
                "verification_outcome",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["archive_id"]: wireString(
                    object["archive_id"],
                    null,
                    null,
                    null,
                ),
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["config_fingerprint"]: checked(
                    wireString(object["config_fingerprint"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["hostname"]: wireString(object["hostname"], null, null, null),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["invocation_mode"]: wireUnion<"systemd" | "interactive">(
                    object["invocation_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "systemd"),
                        (member: unknown) => wireLiteral(member, "interactive"),
                    ],
                ),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["findings"]: wireArray(
                    object["findings"],
                    (member: unknown) => decodeFinding(member),
                    null,
                    null,
                ),
                ["mode"]: wireUnion<"new" | "full" | "revision">(
                    object["mode"],
                    [
                        (member: unknown) => wireLiteral(member, "new"),
                        (member: unknown) => wireLiteral(member, "full"),
                        (member: unknown) => wireLiteral(member, "revision"),
                    ],
                ),
                ["scope"]: decodeVerificationScope(object["scope"]),
                ["throughput_bytes_per_second"]: wireNumber(
                    object["throughput_bytes_per_second"],
                    "0.0",
                    null,
                ),
                ["verification_outcome"]: wireUnion<"clean" | "failed">(
                    object["verification_outcome"],
                    [
                        (member: unknown) => wireLiteral(member, "clean"),
                        (member: unknown) => wireLiteral(member, "failed"),
                    ],
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.reporting.RunEnvelope._check_envelope",
            "hfcache.reporting.VerificationReport._check",
        ],
    );
}
export function decodeVerificationResultPayload(
    value: unknown,
): VerificationResultPayload {
    return checked(
        ((input: unknown) => {
            const object = wireObject(input, [
                "schema_version",
                "application_version",
                "archive_id",
                "command",
                "completed_at",
                "config_fingerprint",
                "errors",
                "exit_code",
                "hostname",
                "huggingface_hub_version",
                "invocation_mode",
                "outcome",
                "python_version",
                "run_id",
                "started_at",
                "warnings",
                "findings",
                "mode",
                "scope",
                "throughput_bytes_per_second",
                "verification_outcome",
                "report",
            ]);
            return Object.freeze({
                ["schema_version"]: wireInteger(
                    object["schema_version"],
                    null,
                    null,
                ),
                ["application_version"]: wireString(
                    object["application_version"],
                    null,
                    null,
                    null,
                ),
                ["archive_id"]: wireString(
                    object["archive_id"],
                    null,
                    null,
                    null,
                ),
                ["command"]: wireString(object["command"], null, null, null),
                ["completed_at"]: checked(
                    wireString(object["completed_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["config_fingerprint"]: checked(
                    wireString(object["config_fingerprint"], null, null, null),
                    ["hfcache.models._parse_sha256"],
                ),
                ["errors"]: wireArray(
                    object["errors"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["exit_code"]: wireInteger(object["exit_code"], null, null),
                ["hostname"]: wireString(object["hostname"], null, null, null),
                ["huggingface_hub_version"]: wireString(
                    object["huggingface_hub_version"],
                    null,
                    null,
                    null,
                ),
                ["invocation_mode"]: wireUnion<"systemd" | "interactive">(
                    object["invocation_mode"],
                    [
                        (member: unknown) => wireLiteral(member, "systemd"),
                        (member: unknown) => wireLiteral(member, "interactive"),
                    ],
                ),
                ["outcome"]: wireUnion<
                    "success" | "success_with_warnings" | "failed"
                >(object["outcome"], [
                    (member: unknown) => wireLiteral(member, "success"),
                    (member: unknown) =>
                        wireLiteral(member, "success_with_warnings"),
                    (member: unknown) => wireLiteral(member, "failed"),
                ]),
                ["python_version"]: wireString(
                    object["python_version"],
                    null,
                    null,
                    null,
                ),
                ["run_id"]: checked(
                    wireString(object["run_id"], null, null, null),
                    ["hfcache.identity.parse_run_id"],
                ),
                ["started_at"]: checked(
                    wireString(object["started_at"], null, null, null),
                    ["timestamp.serialized"],
                ),
                ["warnings"]: wireArray(
                    object["warnings"],
                    (member: unknown) => wireString(member, null, null, null),
                    null,
                    null,
                ),
                ["findings"]: wireArray(
                    object["findings"],
                    (member: unknown) => decodeFinding(member),
                    null,
                    null,
                ),
                ["mode"]: wireUnion<"new" | "full" | "revision">(
                    object["mode"],
                    [
                        (member: unknown) => wireLiteral(member, "new"),
                        (member: unknown) => wireLiteral(member, "full"),
                        (member: unknown) => wireLiteral(member, "revision"),
                    ],
                ),
                ["scope"]: decodeVerificationScope(object["scope"]),
                ["throughput_bytes_per_second"]: wireNumber(
                    object["throughput_bytes_per_second"],
                    "0.0",
                    null,
                ),
                ["verification_outcome"]: wireUnion<"clean" | "failed">(
                    object["verification_outcome"],
                    [
                        (member: unknown) => wireLiteral(member, "clean"),
                        (member: unknown) => wireLiteral(member, "failed"),
                    ],
                ),
                ["report"]: checked(
                    wireString(object["report"], null, null, null),
                    ["hfcache.models._archive_path"],
                ),
            });
        })(value),
        [
            "hfcache.models.VersionedModel._check_schema_version",
            "hfcache.reporting.RunEnvelope._check_envelope",
            "hfcache.reporting.VerificationReport._check",
        ],
    );
}
export function decodeVerificationScope(value: unknown): VerificationScope {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "repositories",
            "revisions",
            "unique_bytes_read",
            "unique_objects_read",
        ]);
        return Object.freeze({
            ["repositories"]: wireInteger(object["repositories"], "0", null),
            ["revisions"]: wireInteger(object["revisions"], "0", null),
            ["unique_bytes_read"]: wireInteger(
                object["unique_bytes_read"],
                "0",
                null,
            ),
            ["unique_objects_read"]: wireInteger(
                object["unique_objects_read"],
                "0",
                null,
            ),
        });
    })(value);
}
export function decodeVerificationSummary(value: unknown): VerificationSummary {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "algorithm",
            "completeness_checked",
            "hashed_bytes",
            "hashed_objects",
            "outcome",
            "reused_digests",
            "verified_at",
        ]);
        return Object.freeze({
            ["algorithm"]: wireLiteral(object["algorithm"], "sha256"),
            ["completeness_checked"]: wireBoolean(
                object["completeness_checked"],
            ),
            ["hashed_bytes"]: wireInteger(object["hashed_bytes"], "0", null),
            ["hashed_objects"]: wireInteger(
                object["hashed_objects"],
                "0",
                null,
            ),
            ["outcome"]: wireLiteral(object["outcome"], "verified"),
            ["reused_digests"]: wireInteger(
                object["reused_digests"],
                "0",
                null,
            ),
            ["verified_at"]: checked(
                wireString(object["verified_at"], null, null, null),
                ["timestamp.serialized"],
            ),
        });
    })(value);
}
export function decodeVersionPayload(value: unknown): VersionPayload {
    return ((input: unknown) => {
        const object = wireObject(input, [
            "application",
            "huggingface_hub",
            "python",
            "transfer_backend",
        ]);
        return Object.freeze({
            ["application"]: wireString(
                object["application"],
                null,
                null,
                null,
            ),
            ["huggingface_hub"]: wireString(
                object["huggingface_hub"],
                null,
                null,
                null,
            ),
            ["python"]: wireString(object["python"], null, null, null),
            ["transfer_backend"]: wireString(
                object["transfer_backend"],
                null,
                null,
                null,
            ),
        });
    })(value);
}
export function decodeNamed(name: string, value: unknown): unknown {
    switch (name) {
        case "Acceptance":
            return decodeAcceptance(value);
        case "ApiProblem":
            return decodeApiProblem(value);
        case "AreaFindingPayload":
            return decodeAreaFindingPayload(value);
        case "CandidateInvalidPayload":
            return decodeCandidateInvalidPayload(value);
        case "CandidateValidPayload":
            return decodeCandidateValidPayload(value);
        case "Capabilities":
            return decodeCapabilities(value);
        case "CatalogCoverage":
            return decodeCatalogCoverage(value);
        case "CatalogDetailPayload":
            return decodeCatalogDetailPayload(value);
        case "CatalogEntry":
            return decodeCatalogEntry(value);
        case "CatalogFacetPayload":
            return decodeCatalogFacetPayload(value);
        case "CatalogFacetValue":
            return decodeCatalogFacetValue(value);
        case "CatalogRefreshResult":
            return decodeCatalogRefreshResult(value);
        case "CatalogSearchPayload":
            return decodeCatalogSearchPayload(value);
        case "CatalogVariantsPayload":
            return decodeCatalogVariantsPayload(value);
        case "ClientEvent":
            return decodeClientEvent(value);
        case "ClientEvents":
            return decodeClientEvents(value);
        case "ClientLinks":
            return decodeClientLinks(value);
        case "ClientOperation":
            return decodeClientOperation(value);
        case "ClientProblem":
            return decodeClientProblem(value);
        case "ClientRead":
            return decodeClientRead(value);
        case "ConfigApplicationOutcome":
            return decodeConfigApplicationOutcome(value);
        case "ConfigRead":
            return decodeConfigRead(value);
        case "DependencyObservation":
            return decodeDependencyObservation(value);
        case "DiagnosticCheckPayload":
            return decodeDiagnosticCheckPayload(value);
        case "DiagnosticsPayload":
            return decodeDiagnosticsPayload(value);
        case "EditableConfig":
            return decodeEditableConfig(value);
        case "EditableRepair":
            return decodeEditableRepair(value);
        case "EditableStorage":
            return decodeEditableStorage(value);
        case "EditableSync":
            return decodeEditableSync(value);
        case "EditableVerification":
            return decodeEditableVerification(value);
        case "EmptyPayload":
            return decodeEmptyPayload(value);
        case "Envelope":
            return decodeEnvelope(value);
        case "EnvelopeProblem":
            return decodeEnvelopeProblem(value);
        case "EstimatePayload":
            return decodeEstimatePayload(value);
        case "FileEntry":
            return decodeFileEntry(value);
        case "FileProvenance":
            return decodeFileProvenance(value);
        case "Finding":
            return decodeFinding(value);
        case "FullVerificationSummary":
            return decodeFullVerificationSummary(value);
        case "HashReuse":
            return decodeHashReuse(value);
        case "HealthPayload":
            return decodeHealthPayload(value);
        case "HostBinding":
            return decodeHostBinding(value);
        case "HostFacts":
            return decodeHostFacts(value);
        case "HostPermissionReasons":
            return decodeHostPermissionReasons(value);
        case "HostPermissions":
            return decodeHostPermissions(value);
        case "HostStatus":
            return decodeHostStatus(value);
        case "HostSyncSchedule":
            return decodeHostSyncSchedule(value);
        case "HostUnitState":
            return decodeHostUnitState(value);
        case "InitializationPayload":
            return decodeInitializationPayload(value);
        case "InspectionPayload":
            return decodeInspectionPayload(value);
        case "InstalledValidationPayload":
            return decodeInstalledValidationPayload(value);
        case "ManagedAssessment":
            return decodeManagedAssessment(value);
        case "ManagedValidation":
            return decodeManagedValidation(value);
        case "ManifestPayload":
            return decodeManifestPayload(value);
        case "ModelVariant":
            return decodeModelVariant(value);
        case "MountPayload":
            return decodeMountPayload(value);
        case "ObservationSummary":
            return decodeObservationSummary(value);
        case "OperationPayload":
            return decodeOperationPayload(value);
        case "OperationsPayload":
            return decodeOperationsPayload(value);
        case "PlanPayload":
            return decodePlanPayload(value);
        case "PlanResultPayload":
            return decodePlanResultPayload(value);
        case "PlannedRepositoryPayload":
            return decodePlannedRepositoryPayload(value);
        case "ProtectedField":
            return decodeProtectedField(value);
        case "PrunePayload":
            return decodePrunePayload(value);
        case "PrunePlan":
            return decodePrunePlan(value);
        case "PruneSelection":
            return decodePruneSelection(value);
        case "PrunedRevision":
            return decodePrunedRevision(value);
        case "PrunedRevisionRecord":
            return decodePrunedRevisionRecord(value);
        case "PublicationRefresh":
            return decodePublicationRefresh(value);
        case "PurgePayload":
            return decodePurgePayload(value);
        case "PurgePlan":
            return decodePurgePlan(value);
        case "QualifiedVariant":
            return decodeQualifiedVariant(value);
        case "QuarantineAppliedPayload":
            return decodeQuarantineAppliedPayload(value);
        case "QuarantineFilePayload":
            return decodeQuarantineFilePayload(value);
        case "QuarantinePayload":
            return decodeQuarantinePayload(value);
        case "QuarantinePlanPayload":
            return decodeQuarantinePlanPayload(value);
        case "ReachableArchivePayload":
            return decodeReachableArchivePayload(value);
        case "ReadyHealthPayload":
            return decodeReadyHealthPayload(value);
        case "RecoveryAppliedPayload":
            return decodeRecoveryAppliedPayload(value);
        case "RecoveryPlanPayload":
            return decodeRecoveryPlanPayload(value);
        case "RecoveryReport":
            return decodeRecoveryReport(value);
        case "Reference":
            return decodeReference(value);
        case "ReferencePayload":
            return decodeReferencePayload(value);
        case "RefreshCounts":
            return decodeRefreshCounts(value);
        case "Remediation":
            return decodeRemediation(value);
        case "RemediationPayload":
            return decodeRemediationPayload(value);
        case "RepairPayload":
            return decodeRepairPayload(value);
        case "RepairProvenance":
            return decodeRepairProvenance(value);
        case "ReportPayload":
            return decodeReportPayload(value);
        case "RepositoriesPayload":
            return decodeRepositoriesPayload(value);
        case "RepositoryCardRead":
            return decodeRepositoryCardRead(value);
        case "RepositoryConfig":
            return decodeRepositoryConfig(value);
        case "RepositoryPayload":
            return decodeRepositoryPayload(value);
        case "RepositoryRefresh":
            return decodeRepositoryRefresh(value);
        case "RepositoryRunResult":
            return decodeRepositoryRunResult(value);
        case "RepositoryStatusPayload":
            return decodeRepositoryStatusPayload(value);
        case "RequestCandidatePayload":
            return decodeRequestCandidatePayload(value);
        case "RequestCatalogRefreshSubmission":
            return decodeRequestCatalogRefreshSubmission(value);
        case "RequestConfigApplicationSubmission":
            return decodeRequestConfigApplicationSubmission(value);
        case "RequestConfigPreviewReference":
            return decodeRequestConfigPreviewReference(value);
        case "RequestDiagnosticsSubmission":
            return decodeRequestDiagnosticsSubmission(value);
        case "RequestFullVerification":
            return decodeRequestFullVerification(value);
        case "RequestInitializationSubmission":
            return decodeRequestInitializationSubmission(value);
        case "RequestInstalledPlan":
            return decodeRequestInstalledPlan(value);
        case "RequestInstalledValidation":
            return decodeRequestInstalledValidation(value);
        case "RequestInstalledValidationSubmission":
            return decodeRequestInstalledValidationSubmission(value);
        case "RequestLiteralCandidatePlan":
            return decodeRequestLiteralCandidatePlan(value);
        case "RequestLiteralCandidateValidation":
            return decodeRequestLiteralCandidateValidation(value);
        case "RequestManagedEditRequest":
            return decodeRequestManagedEditRequest(value);
        case "RequestManagedPlanRequest":
            return decodeRequestManagedPlanRequest(value);
        case "RequestManagedValidationRequest":
            return decodeRequestManagedValidationRequest(value);
        case "RequestNewVerification":
            return decodeRequestNewVerification(value);
        case "RequestPlanSubmission":
            return decodeRequestPlanSubmission(value);
        case "RequestProbeDiagnostics":
            return decodeRequestProbeDiagnostics(value);
        case "RequestPruneSubmission":
            return decodeRequestPruneSubmission(value);
        case "RequestPurgeSubmission":
            return decodeRequestPurgeSubmission(value);
        case "RequestQuarantineSubmission":
            return decodeRequestQuarantineSubmission(value);
        case "RequestReadOnlyDiagnostics":
            return decodeRequestReadOnlyDiagnostics(value);
        case "RequestRecoverySubmission":
            return decodeRequestRecoverySubmission(value);
        case "RequestRepairReplacement":
            return decodeRequestRepairReplacement(value);
        case "RequestRepairSubmission":
            return decodeRequestRepairSubmission(value);
        case "RequestRepositoryConfig":
            return decodeRequestRepositoryConfig(value);
        case "RequestRepositoryRemove":
            return decodeRequestRepositoryRemove(value);
        case "RequestRepositoryUpsert":
            return decodeRequestRepositoryUpsert(value);
        case "RequestRevisionVerification":
            return decodeRequestRevisionVerification(value);
        case "RequestSettingsReplace":
            return decodeRequestSettingsReplace(value);
        case "RequestSettingsReplacement":
            return decodeRequestSettingsReplacement(value);
        case "RequestStorageReplacement":
            return decodeRequestStorageReplacement(value);
        case "RequestSyncReplacement":
            return decodeRequestSyncReplacement(value);
        case "RequestSyncSubmission":
            return decodeRequestSyncSubmission(value);
        case "RequestValidationSubmission":
            return decodeRequestValidationSubmission(value);
        case "RequestVerificationReplacement":
            return decodeRequestVerificationReplacement(value);
        case "RequestVerificationSubmission":
            return decodeRequestVerificationSubmission(value);
        case "RevisionManifest":
            return decodeRevisionManifest(value);
        case "RevisionPayload":
            return decodeRevisionPayload(value);
        case "RevisionSummary":
            return decodeRevisionSummary(value);
        case "RevisionsPayload":
            return decodeRevisionsPayload(value);
        case "RunReport":
            return decodeRunReport(value);
        case "RunResultPayload":
            return decodeRunResultPayload(value);
        case "RunTotals":
            return decodeRunTotals(value);
        case "RunsPayload":
            return decodeRunsPayload(value);
        case "SourceObservation":
            return decodeSourceObservation(value);
        case "StatusPayload":
            return decodeStatusPayload(value);
        case "UiAdminPermission":
            return decodeUiAdminPermission(value);
        case "UiAssetManifest":
            return decodeUiAssetManifest(value);
        case "UiAssetMember":
            return decodeUiAssetMember(value);
        case "UiBootstrap":
            return decodeUiBootstrap(value);
        case "UiBuildIdentity":
            return decodeUiBuildIdentity(value);
        case "UiBuildMetadata":
            return decodeUiBuildMetadata(value);
        case "UiHtmlMetaIdentity":
            return decodeUiHtmlMetaIdentity(value);
        case "UiPaths":
            return decodeUiPaths(value);
        case "UiToolchain":
            return decodeUiToolchain(value);
        case "UiUser":
            return decodeUiUser(value);
        case "UnavailableHealthPayload":
            return decodeUnavailableHealthPayload(value);
        case "UnreachableArchivePayload":
            return decodeUnreachableArchivePayload(value);
        case "UpstreamIdentifiers":
            return decodeUpstreamIdentifiers(value);
        case "VariantMember":
            return decodeVariantMember(value);
        case "VerificationHealthPayload":
            return decodeVerificationHealthPayload(value);
        case "VerificationReport":
            return decodeVerificationReport(value);
        case "VerificationResultPayload":
            return decodeVerificationResultPayload(value);
        case "VerificationScope":
            return decodeVerificationScope(value);
        case "VerificationSummary":
            return decodeVerificationSummary(value);
        case "VersionPayload":
            return decodeVersionPayload(value);
        default:
            throw new WireError("schema");
    }
}
export const routeContracts = {
    ui_bootstrap_default: {
        method: "GET",
        path: "/ui/bootstrap.json",
        commands: [],
        bindingIds: ["ui.bootstrap"],
        responseKind: "ui_bootstrap",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeUiBootstrap,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: wireNull,
    },
    version_default: {
        method: "GET",
        path: "/api/v1/version",
        commands: ["version"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeVersionPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    capabilities_default: {
        method: "GET",
        path: "/api/v1/capabilities",
        commands: ["capabilities"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeCapabilities,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    health_default: {
        method: "GET",
        path: "/api/v1/health",
        commands: ["health"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeHealthPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    host_status_default: {
        method: "GET",
        path: "/api/v1/host/status",
        commands: ["host status"],
        bindingIds: ["host.status"],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeHostStatus,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    config_read_default: {
        method: "GET",
        path: "/api/v1/config",
        commands: ["config read"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeConfigRead,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    config_outcome_default: {
        method: "GET",
        path: "/api/v1/config/applications/{operation_id}",
        commands: ["config outcome"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): { readonly ["operation_id"]: string } =>
            ((input: unknown) => {
                const object = wireObject(input, ["operation_id"]);
                return Object.freeze({
                    ["operation_id"]: checked(
                        wireString(object["operation_id"], 1, 256, null),
                        ["hfcache.identity.parse_run_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeConfigApplicationOutcome,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    inspection_default: {
        method: "GET",
        path: "/api/v1/archive/inspection",
        commands: ["archive init"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeInspectionPayload,
        decodeFailure: (value: unknown): InspectionPayload | EmptyPayload =>
            wireUnion<InspectionPayload | EmptyPayload>(value, [
                decodeInspectionPayload,
                decodeEmptyPayload,
            ]),
        decodeBody: wireNull,
    },
    status_default: {
        method: "GET",
        path: "/api/v1/status",
        commands: ["status"],
        bindingIds: [],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
            readonly ["selector"]?: readonly string[];
            readonly ["type"]?: "model" | "dataset";
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["limit", "cursor", "selector", "type"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "selector")
                        ? {
                              ["selector"]: wireArray(
                                  object["selector"],
                                  (member: unknown) =>
                                      wireString(member, 0, 256, null),
                                  null,
                                  100,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "type")
                        ? {
                              ["type"]: wireUnion<"model" | "dataset">(
                                  object["type"],
                                  [
                                      (member: unknown) =>
                                          wireLiteral(member, "model"),
                                      (member: unknown) =>
                                          wireLiteral(member, "dataset"),
                                  ],
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: ["selector"],
        decodeSuccess: decodeStatusPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    repositories_default: {
        method: "GET",
        path: "/api/v1/repositories",
        commands: ["list"],
        bindingIds: [],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
            readonly ["selector"]?: readonly string[];
            readonly ["type"]?: "model" | "dataset";
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["limit", "cursor", "selector", "type"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "selector")
                        ? {
                              ["selector"]: wireArray(
                                  object["selector"],
                                  (member: unknown) =>
                                      wireString(member, 0, 256, null),
                                  null,
                                  100,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "type")
                        ? {
                              ["type"]: wireUnion<"model" | "dataset">(
                                  object["type"],
                                  [
                                      (member: unknown) =>
                                          wireLiteral(member, "model"),
                                      (member: unknown) =>
                                          wireLiteral(member, "dataset"),
                                  ],
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: ["selector"],
        decodeSuccess: decodeRepositoriesPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    revisions_default: {
        method: "GET",
        path: "/api/v1/repositories/revisions",
        commands: ["list"],
        bindingIds: [],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
            readonly ["selector"]?: readonly string[];
            readonly ["type"]?: "model" | "dataset";
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["limit", "cursor", "selector", "type"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "selector")
                        ? {
                              ["selector"]: wireArray(
                                  object["selector"],
                                  (member: unknown) =>
                                      wireString(member, 0, 256, null),
                                  null,
                                  100,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "type")
                        ? {
                              ["type"]: wireUnion<"model" | "dataset">(
                                  object["type"],
                                  [
                                      (member: unknown) =>
                                          wireLiteral(member, "model"),
                                      (member: unknown) =>
                                          wireLiteral(member, "dataset"),
                                  ],
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: ["selector"],
        decodeSuccess: decodeRevisionsPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    estimate_default: {
        method: "GET",
        path: "/api/v1/verification/estimate",
        commands: ["verify --estimate"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeEstimatePayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    runs_default: {
        method: "GET",
        path: "/api/v1/runs",
        commands: ["runs"],
        bindingIds: [],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): { readonly ["limit"]?: number; readonly ["cursor"]?: string } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["limit", "cursor"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: [],
        decodeSuccess: decodeRunsPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    report_default: {
        method: "GET",
        path: "/api/v1/runs/{run_id}",
        commands: ["runs read"],
        bindingIds: ["run.report"],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): { readonly ["run_id"]: string } =>
            ((input: unknown) => {
                const object = wireObject(input, ["run_id"]);
                return Object.freeze({
                    ["run_id"]: checked(
                        wireString(object["run_id"], 1, 256, null),
                        ["hfcache.identity.parse_run_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeReportPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    reference_default: {
        method: "GET",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/references/{revision}",
        commands: ["reference read"],
        bindingIds: ["publication.reference"],
        responseKind: "read",
        cursor: "none",
        decodePath: (
            value: unknown,
        ): {
            readonly ["repository_type"]: string;
            readonly ["namespace"]: string;
            readonly ["name"]: string;
            readonly ["revision"]: string;
        } =>
            ((input: unknown) => {
                const object = wireObject(input, [
                    "repository_type",
                    "namespace",
                    "name",
                    "revision",
                ]);
                return Object.freeze({
                    ["repository_type"]: checked(
                        wireString(object["repository_type"], 1, 256, null),
                        ["hfcache.identity.parse_repository_type"],
                    ),
                    ["namespace"]: wireString(
                        object["namespace"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["name"]: wireString(
                        object["name"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["revision"]: wireUnion<string>(object["revision"], [
                        (member: unknown) => wireLiteral(member, "current"),
                        (member: unknown) =>
                            checked(wireString(member, 1, 256, null), [
                                "hfcache.identity.parse_commit_sha",
                            ]),
                    ]),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeReferencePayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    manifest_default: {
        method: "GET",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}",
        commands: ["manifest read"],
        bindingIds: ["publication.manifest"],
        responseKind: "read",
        cursor: "none",
        decodePath: (
            value: unknown,
        ): {
            readonly ["repository_type"]: string;
            readonly ["namespace"]: string;
            readonly ["name"]: string;
            readonly ["commit_sha"]: string;
            readonly ["publication_id"]: string;
        } =>
            ((input: unknown) => {
                const object = wireObject(input, [
                    "repository_type",
                    "namespace",
                    "name",
                    "commit_sha",
                    "publication_id",
                ]);
                return Object.freeze({
                    ["repository_type"]: checked(
                        wireString(object["repository_type"], 1, 256, null),
                        ["hfcache.identity.parse_repository_type"],
                    ),
                    ["namespace"]: wireString(
                        object["namespace"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["name"]: wireString(
                        object["name"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["commit_sha"]: checked(
                        wireString(object["commit_sha"], 1, 256, null),
                        ["hfcache.identity.parse_commit_sha"],
                    ),
                    ["publication_id"]: checked(
                        wireString(object["publication_id"], 1, 256, null),
                        ["hfcache.identity.parse_publication_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeManifestPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    repository_card_default: {
        method: "GET",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card",
        commands: ["card read"],
        bindingIds: ["publication.card"],
        responseKind: "read",
        cursor: "none",
        decodePath: (
            value: unknown,
        ): {
            readonly ["repository_type"]: string;
            readonly ["namespace"]: string;
            readonly ["name"]: string;
            readonly ["commit_sha"]: string;
            readonly ["publication_id"]: string;
        } =>
            ((input: unknown) => {
                const object = wireObject(input, [
                    "repository_type",
                    "namespace",
                    "name",
                    "commit_sha",
                    "publication_id",
                ]);
                return Object.freeze({
                    ["repository_type"]: checked(
                        wireString(object["repository_type"], 1, 256, null),
                        ["hfcache.identity.parse_repository_type"],
                    ),
                    ["namespace"]: wireString(
                        object["namespace"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["name"]: wireString(
                        object["name"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["commit_sha"]: checked(
                        wireString(object["commit_sha"], 1, 256, null),
                        ["hfcache.identity.parse_commit_sha"],
                    ),
                    ["publication_id"]: checked(
                        wireString(object["publication_id"], 1, 256, null),
                        ["hfcache.identity.parse_publication_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeRepositoryCardRead,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    operations_default: {
        method: "GET",
        path: "/api/v1/operations",
        commands: ["operations list"],
        bindingIds: [],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): { readonly ["limit"]?: number; readonly ["cursor"]?: string } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["limit", "cursor"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: [],
        decodeSuccess: decodeOperationsPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    operation_lookup_default: {
        method: "GET",
        path: "/api/v1/operations/lookup",
        commands: ["operations lookup"],
        bindingIds: ["operation.identity"],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeOperationPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    operation_default: {
        method: "GET",
        path: "/api/v1/operations/{operation_id}",
        commands: ["operations show"],
        bindingIds: ["operation.identity"],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): { readonly ["operation_id"]: string } =>
            ((input: unknown) => {
                const object = wireObject(input, ["operation_id"]);
                return Object.freeze({
                    ["operation_id"]: checked(
                        wireString(object["operation_id"], 1, 256, null),
                        ["hfcache.identity.parse_run_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeOperationPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    operation_events_default: {
        method: "GET",
        path: "/api/v1/operations/{operation_id}/events",
        commands: ["operations events"],
        bindingIds: ["operation.events"],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): { readonly ["operation_id"]: string } =>
            ((input: unknown) => {
                const object = wireObject(input, ["operation_id"]);
                return Object.freeze({
                    ["operation_id"]: checked(
                        wireString(object["operation_id"], 1, 256, null),
                        ["hfcache.identity.parse_run_id"],
                    ),
                });
            })(value),
        decodeQuery: (
            value: unknown,
        ): { readonly ["after"]?: number; readonly ["limit"]?: number } =>
            ((input: unknown) => {
                const object = wireRequestObject(input, [], ["after", "limit"]);
                return Object.freeze({
                    ...(Object.hasOwn(object, "after")
                        ? {
                              ["after"]: wireInteger(
                                  object["after"],
                                  "0",
                                  "9999999999",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: [],
        decodeSuccess: decodeClientEvents,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    operation_result_by_original_operation: {
        method: "GET",
        path: "/api/v1/operations/{operation_id}/result",
        commands: [],
        bindingIds: ["operation.result"],
        responseKind: "operation_result",
        cursor: "none",
        decodePath: (value: unknown): { readonly ["operation_id"]: string } =>
            ((input: unknown) => {
                const object = wireObject(input, ["operation_id"]);
                return Object.freeze({
                    ["operation_id"]: checked(
                        wireString(object["operation_id"], 1, 256, null),
                        ["hfcache.identity.parse_run_id"],
                    ),
                });
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: wireNull,
    },
    catalog_search_default: {
        method: "GET",
        path: "/api/v1/catalog/search",
        commands: ["catalog.search"],
        bindingIds: ["catalog.response"],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["type"]?: "model" | "dataset";
            readonly ["q"]?: string;
            readonly ["tag_all"]?: readonly string[];
            readonly ["tag_any"]?: readonly string[];
            readonly ["tag_source"]?:
                "current_or_last_observed" | "current_only";
            readonly ["scope"]?: "archived" | "configured" | "all";
            readonly ["revision_scope"]?: "current" | "retained";
            readonly ["format"]?: string;
            readonly ["quantization"]?: string;
            readonly ["quantization_method"]?: string;
            readonly ["bits"]?: number;
            readonly ["max_variant_bytes"]?: number;
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    [
                        "type",
                        "q",
                        "tag_all",
                        "tag_any",
                        "tag_source",
                        "scope",
                        "revision_scope",
                        "format",
                        "quantization",
                        "quantization_method",
                        "bits",
                        "max_variant_bytes",
                        "limit",
                        "cursor",
                    ],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "type")
                        ? {
                              ["type"]: wireUnion<"model" | "dataset">(
                                  object["type"],
                                  [
                                      (member: unknown) =>
                                          wireLiteral(member, "model"),
                                      (member: unknown) =>
                                          wireLiteral(member, "dataset"),
                                  ],
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "q")
                        ? { ["q"]: wireString(object["q"], 0, 256, null) }
                        : {}),
                    ...(Object.hasOwn(object, "tag_all")
                        ? {
                              ["tag_all"]: wireArray(
                                  object["tag_all"],
                                  (member: unknown) =>
                                      wireString(member, 0, 128, null),
                                  null,
                                  64,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "tag_any")
                        ? {
                              ["tag_any"]: wireArray(
                                  object["tag_any"],
                                  (member: unknown) =>
                                      wireString(member, 0, 128, null),
                                  null,
                                  64,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "tag_source")
                        ? {
                              ["tag_source"]: wireUnion<
                                  "current_or_last_observed" | "current_only"
                              >(object["tag_source"], [
                                  (member: unknown) =>
                                      wireLiteral(
                                          member,
                                          "current_or_last_observed",
                                      ),
                                  (member: unknown) =>
                                      wireLiteral(member, "current_only"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "scope")
                        ? {
                              ["scope"]: wireUnion<
                                  "archived" | "configured" | "all"
                              >(object["scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "archived"),
                                  (member: unknown) =>
                                      wireLiteral(member, "configured"),
                                  (member: unknown) =>
                                      wireLiteral(member, "all"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "revision_scope")
                        ? {
                              ["revision_scope"]: wireUnion<
                                  "current" | "retained"
                              >(object["revision_scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "current"),
                                  (member: unknown) =>
                                      wireLiteral(member, "retained"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "format")
                        ? {
                              ["format"]: wireString(
                                  object["format"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "quantization")
                        ? {
                              ["quantization"]: wireString(
                                  object["quantization"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "quantization_method")
                        ? {
                              ["quantization_method"]: wireString(
                                  object["quantization_method"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "bits")
                        ? { ["bits"]: wireInteger(object["bits"], "1", "64") }
                        : {}),
                    ...(Object.hasOwn(object, "max_variant_bytes")
                        ? {
                              ["max_variant_bytes"]: wireInteger(
                                  object["max_variant_bytes"],
                                  "0",
                                  "9223372036854775807",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: ["tag_all", "tag_any"],
        decodeSuccess: decodeCatalogSearchPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    catalog_facets_default: {
        method: "GET",
        path: "/api/v1/catalog/facets",
        commands: ["catalog.facets"],
        bindingIds: ["catalog.response", "catalog.facet"],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["type"]?: "model" | "dataset";
            readonly ["q"]?: string;
            readonly ["tag_all"]?: readonly string[];
            readonly ["tag_any"]?: readonly string[];
            readonly ["tag_source"]?:
                "current_or_last_observed" | "current_only";
            readonly ["scope"]?: "archived" | "configured" | "all";
            readonly ["revision_scope"]?: "current" | "retained";
            readonly ["format"]?: string;
            readonly ["quantization"]?: string;
            readonly ["quantization_method"]?: string;
            readonly ["bits"]?: number;
            readonly ["max_variant_bytes"]?: number;
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
            readonly ["facet"]?:
                "tag" | "format" | "quantization_method" | "quantization";
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    [
                        "type",
                        "q",
                        "tag_all",
                        "tag_any",
                        "tag_source",
                        "scope",
                        "revision_scope",
                        "format",
                        "quantization",
                        "quantization_method",
                        "bits",
                        "max_variant_bytes",
                        "limit",
                        "cursor",
                        "facet",
                    ],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "type")
                        ? {
                              ["type"]: wireUnion<"model" | "dataset">(
                                  object["type"],
                                  [
                                      (member: unknown) =>
                                          wireLiteral(member, "model"),
                                      (member: unknown) =>
                                          wireLiteral(member, "dataset"),
                                  ],
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "q")
                        ? { ["q"]: wireString(object["q"], 0, 256, null) }
                        : {}),
                    ...(Object.hasOwn(object, "tag_all")
                        ? {
                              ["tag_all"]: wireArray(
                                  object["tag_all"],
                                  (member: unknown) =>
                                      wireString(member, 0, 128, null),
                                  null,
                                  64,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "tag_any")
                        ? {
                              ["tag_any"]: wireArray(
                                  object["tag_any"],
                                  (member: unknown) =>
                                      wireString(member, 0, 128, null),
                                  null,
                                  64,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "tag_source")
                        ? {
                              ["tag_source"]: wireUnion<
                                  "current_or_last_observed" | "current_only"
                              >(object["tag_source"], [
                                  (member: unknown) =>
                                      wireLiteral(
                                          member,
                                          "current_or_last_observed",
                                      ),
                                  (member: unknown) =>
                                      wireLiteral(member, "current_only"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "scope")
                        ? {
                              ["scope"]: wireUnion<
                                  "archived" | "configured" | "all"
                              >(object["scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "archived"),
                                  (member: unknown) =>
                                      wireLiteral(member, "configured"),
                                  (member: unknown) =>
                                      wireLiteral(member, "all"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "revision_scope")
                        ? {
                              ["revision_scope"]: wireUnion<
                                  "current" | "retained"
                              >(object["revision_scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "current"),
                                  (member: unknown) =>
                                      wireLiteral(member, "retained"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "format")
                        ? {
                              ["format"]: wireString(
                                  object["format"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "quantization")
                        ? {
                              ["quantization"]: wireString(
                                  object["quantization"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "quantization_method")
                        ? {
                              ["quantization_method"]: wireString(
                                  object["quantization_method"],
                                  0,
                                  64,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "bits")
                        ? { ["bits"]: wireInteger(object["bits"], "1", "64") }
                        : {}),
                    ...(Object.hasOwn(object, "max_variant_bytes")
                        ? {
                              ["max_variant_bytes"]: wireInteger(
                                  object["max_variant_bytes"],
                                  "0",
                                  "9223372036854775807",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "facet")
                        ? {
                              ["facet"]: wireUnion<
                                  | "tag"
                                  | "format"
                                  | "quantization_method"
                                  | "quantization"
                              >(object["facet"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "tag"),
                                  (member: unknown) =>
                                      wireLiteral(member, "format"),
                                  (member: unknown) =>
                                      wireLiteral(
                                          member,
                                          "quantization_method",
                                      ),
                                  (member: unknown) =>
                                      wireLiteral(member, "quantization"),
                              ]),
                          }
                        : {}),
                });
            })(value),
        repeated: ["tag_all", "tag_any"],
        decodeSuccess: decodeCatalogFacetPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    catalog_detail_default: {
        method: "GET",
        path: "/api/v1/catalog/repositories/{repository_type}/{namespace}/{name}",
        commands: ["catalog.detail"],
        bindingIds: ["catalog.response", "catalog.publication"],
        responseKind: "read",
        cursor: "none",
        decodePath: (
            value: unknown,
        ): {
            readonly ["repository_type"]: string;
            readonly ["namespace"]: string;
            readonly ["name"]: string;
        } =>
            ((input: unknown) => {
                const object = wireObject(input, [
                    "repository_type",
                    "namespace",
                    "name",
                ]);
                return Object.freeze({
                    ["repository_type"]: checked(
                        wireString(object["repository_type"], 1, 256, null),
                        ["hfcache.identity.parse_repository_type"],
                    ),
                    ["namespace"]: wireString(
                        object["namespace"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["name"]: wireString(
                        object["name"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                });
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["revision_scope"]?: "current" | "retained";
            readonly ["commit_sha"]?: string;
            readonly ["publication_id"]?: string;
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    ["revision_scope", "commit_sha", "publication_id"],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "revision_scope")
                        ? {
                              ["revision_scope"]: wireUnion<
                                  "current" | "retained"
                              >(object["revision_scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "current"),
                                  (member: unknown) =>
                                      wireLiteral(member, "retained"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "commit_sha")
                        ? {
                              ["commit_sha"]: checked(
                                  wireString(object["commit_sha"], 0, 64, null),
                                  ["hfcache.identity.parse_commit_sha"],
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "publication_id")
                        ? {
                              ["publication_id"]: checked(
                                  wireString(
                                      object["publication_id"],
                                      0,
                                      64,
                                      null,
                                  ),
                                  ["hfcache.identity.parse_publication_id"],
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: [],
        decodeSuccess: decodeCatalogDetailPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    catalog_variants_default: {
        method: "GET",
        path: "/api/v1/catalog/repositories/{repository_type}/{namespace}/{name}/variants",
        commands: ["catalog.variants"],
        bindingIds: ["catalog.response", "catalog.publication"],
        responseKind: "read",
        cursor: "opaque",
        decodePath: (
            value: unknown,
        ): {
            readonly ["repository_type"]: string;
            readonly ["namespace"]: string;
            readonly ["name"]: string;
        } =>
            ((input: unknown) => {
                const object = wireObject(input, [
                    "repository_type",
                    "namespace",
                    "name",
                ]);
                return Object.freeze({
                    ["repository_type"]: checked(
                        wireString(object["repository_type"], 1, 256, null),
                        ["hfcache.identity.parse_repository_type"],
                    ),
                    ["namespace"]: wireString(
                        object["namespace"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                    ["name"]: wireString(
                        object["name"],
                        1,
                        96,
                        "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    ),
                });
            })(value),
        decodeQuery: (
            value: unknown,
        ): {
            readonly ["revision_scope"]?: "current" | "retained";
            readonly ["commit_sha"]?: string;
            readonly ["publication_id"]?: string;
            readonly ["limit"]?: number;
            readonly ["cursor"]?: string;
        } =>
            ((input: unknown) => {
                const object = wireRequestObject(
                    input,
                    [],
                    [
                        "revision_scope",
                        "commit_sha",
                        "publication_id",
                        "limit",
                        "cursor",
                    ],
                );
                return Object.freeze({
                    ...(Object.hasOwn(object, "revision_scope")
                        ? {
                              ["revision_scope"]: wireUnion<
                                  "current" | "retained"
                              >(object["revision_scope"], [
                                  (member: unknown) =>
                                      wireLiteral(member, "current"),
                                  (member: unknown) =>
                                      wireLiteral(member, "retained"),
                              ]),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "commit_sha")
                        ? {
                              ["commit_sha"]: checked(
                                  wireString(object["commit_sha"], 0, 64, null),
                                  ["hfcache.identity.parse_commit_sha"],
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "publication_id")
                        ? {
                              ["publication_id"]: checked(
                                  wireString(
                                      object["publication_id"],
                                      0,
                                      64,
                                      null,
                                  ),
                                  ["hfcache.identity.parse_publication_id"],
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "limit")
                        ? {
                              ["limit"]: wireInteger(
                                  object["limit"],
                                  "1",
                                  "10000",
                              ),
                          }
                        : {}),
                    ...(Object.hasOwn(object, "cursor")
                        ? {
                              ["cursor"]: wireString(
                                  object["cursor"],
                                  0,
                                  256,
                                  null,
                              ),
                          }
                        : {}),
                });
            })(value),
        repeated: [],
        decodeSuccess: decodeCatalogVariantsPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: wireNull,
    },
    config_apply_default: {
        method: "POST",
        path: "/api/v1/config/applications",
        commands: ["config apply"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestConfigApplicationSubmission,
    },
    sync_default: {
        method: "POST",
        path: "/api/v1/syncs",
        commands: ["sync"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestSyncSubmission,
    },
    plan_installed: {
        method: "POST",
        path: "/api/v1/plans",
        commands: ["plan"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestInstalledPlan,
    },
    plan_literal_candidate: {
        method: "POST",
        path: "/api/v1/plans",
        commands: ["plan"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestLiteralCandidatePlan,
    },
    plan_managed: {
        method: "POST",
        path: "/api/v1/plans",
        commands: ["plan"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestManagedPlanRequest,
    },
    diagnostics_read_only: {
        method: "POST",
        path: "/api/v1/diagnostics",
        commands: ["doctor"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestReadOnlyDiagnostics,
    },
    diagnostics_probe: {
        method: "POST",
        path: "/api/v1/diagnostics",
        commands: ["doctor"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestProbeDiagnostics,
    },
    verification_new: {
        method: "POST",
        path: "/api/v1/verifications",
        commands: ["verify --new"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestNewVerification,
    },
    verification_full: {
        method: "POST",
        path: "/api/v1/verifications",
        commands: ["verify --full"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestFullVerification,
    },
    verification_revision: {
        method: "POST",
        path: "/api/v1/verifications",
        commands: ["verify --revision"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestRevisionVerification,
    },
    prune_preview_default: {
        method: "POST",
        path: "/api/v1/prune-plans",
        commands: ["prune --dry-run"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestPruneSubmission,
    },
    prune_apply_default: {
        method: "POST",
        path: "/api/v1/prunes",
        commands: ["prune --apply"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestPruneSubmission,
    },
    purge_preview_default: {
        method: "POST",
        path: "/api/v1/purge-plans",
        commands: ["purge --dry-run"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestPurgeSubmission,
    },
    purge_apply_default: {
        method: "POST",
        path: "/api/v1/purges",
        commands: ["purge --apply"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestPurgeSubmission,
    },
    recovery_preview_default: {
        method: "POST",
        path: "/api/v1/recovery-plans",
        commands: ["recover --dry-run"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestRecoverySubmission,
    },
    recovery_apply_default: {
        method: "POST",
        path: "/api/v1/recoveries",
        commands: ["recover --apply"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestRecoverySubmission,
    },
    quarantine_preview_default: {
        method: "POST",
        path: "/api/v1/quarantine-plans",
        commands: ["quarantine --dry-run"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestQuarantineSubmission,
    },
    quarantine_apply_default: {
        method: "POST",
        path: "/api/v1/quarantine-cleanups",
        commands: ["quarantine --apply"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestQuarantineSubmission,
    },
    repair_default: {
        method: "POST",
        path: "/api/v1/repairs",
        commands: ["repair"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestRepairSubmission,
    },
    initialization_default: {
        method: "POST",
        path: "/api/v1/archive/initializations",
        commands: ["archive init"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestInitializationSubmission,
    },
    catalog_refresh_default: {
        method: "POST",
        path: "/api/v1/catalog/refreshes",
        commands: ["catalog refresh"],
        bindingIds: [],
        responseKind: "acceptance",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeAcceptance,
        decodeFailure: (_value: unknown): never => {
            void _value;
            throw new WireError("schema");
        },
        decodeBody: decodeRequestCatalogRefreshSubmission,
    },
    config_validate_installed: {
        method: "POST",
        path: "/api/v1/config/validate",
        commands: ["config validate"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeInstalledValidationPayload,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: decodeRequestInstalledValidation,
    },
    config_validate_literal_candidate: {
        method: "POST",
        path: "/api/v1/config/validate",
        commands: ["config validate"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeCandidateValidPayload,
        decodeFailure: (value: unknown): CandidateInvalidPayload =>
            wireUnion<CandidateInvalidPayload>(value, [
                decodeCandidateInvalidPayload,
            ]),
        decodeBody: decodeRequestLiteralCandidateValidation,
    },
    config_validate_managed: {
        method: "POST",
        path: "/api/v1/config/validate",
        commands: ["config validate"],
        bindingIds: [],
        responseKind: "read",
        cursor: "none",
        decodePath: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        decodeQuery: (value: unknown): Readonly<Record<string, never>> =>
            ((input: unknown) => {
                wireObject(input, []);
                return Object.freeze({});
            })(value),
        repeated: [],
        decodeSuccess: decodeManagedValidation,
        decodeFailure: (value: unknown): EmptyPayload =>
            wireUnion<EmptyPayload>(value, [decodeEmptyPayload]),
        decodeBody: decodeRequestManagedValidationRequest,
    },
} as const;
export type OperationSuccess =
    | ConfigApplicationOutcome
    | RunResultPayload
    | PlanResultPayload
    | DiagnosticsPayload
    | VerificationResultPayload
    | PrunePayload
    | PurgePayload
    | RecoveryPlanPayload
    | RecoveryAppliedPayload
    | QuarantinePayload
    | RepairPayload
    | InitializationPayload
    | CatalogRefreshResult;
export type OperationFailure =
    | ConfigApplicationOutcome
    | EmptyPayload
    | RunResultPayload
    | PlanResultPayload
    | DiagnosticsPayload
    | VerificationResultPayload
    | VerificationReport
    | RecoveryPlanPayload
    | RecoveryAppliedPayload
    | InspectionPayload
    | CatalogRefreshResult;
export function decodeOriginalOperationPayload(
    origin: string,
    command: string,
    failed: false,
    value: unknown,
): OperationSuccess;
export function decodeOriginalOperationPayload(
    origin: string,
    command: string,
    failed: true,
    value: unknown,
): OperationFailure;
export function decodeOriginalOperationPayload(
    origin: string,
    command: string,
    failed: boolean,
    value: unknown,
): OperationSuccess | OperationFailure {
    if (
        origin === "/api/v1/config/applications" &&
        ["config apply"].includes(command)
    )
        return failed
            ? ((value: unknown): ConfigApplicationOutcome | EmptyPayload =>
                  wireUnion<ConfigApplicationOutcome | EmptyPayload>(value, [
                      decodeConfigApplicationOutcome,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeConfigApplicationOutcome(value);
    if (origin === "/api/v1/syncs" && ["sync"].includes(command))
        return failed
            ? ((value: unknown): RunResultPayload | EmptyPayload =>
                  wireUnion<RunResultPayload | EmptyPayload>(value, [
                      decodeRunResultPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeRunResultPayload(value);
    if (origin === "/api/v1/plans" && ["plan"].includes(command))
        return failed
            ? ((value: unknown): PlanResultPayload | EmptyPayload =>
                  wireUnion<PlanResultPayload | EmptyPayload>(value, [
                      decodePlanResultPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodePlanResultPayload(value);
    if (origin === "/api/v1/diagnostics" && ["doctor"].includes(command))
        return failed
            ? ((value: unknown): DiagnosticsPayload | EmptyPayload =>
                  wireUnion<DiagnosticsPayload | EmptyPayload>(value, [
                      decodeDiagnosticsPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeDiagnosticsPayload(value);
    if (
        origin === "/api/v1/verifications" &&
        ["verify --new"].includes(command)
    )
        return failed
            ? ((
                  value: unknown,
              ):
                  | VerificationResultPayload
                  | VerificationReport
                  | EmptyPayload =>
                  wireUnion<
                      | VerificationResultPayload
                      | VerificationReport
                      | EmptyPayload
                  >(value, [
                      decodeVerificationResultPayload,
                      decodeVerificationReport,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeVerificationResultPayload(value);
    if (
        origin === "/api/v1/verifications" &&
        ["verify --full"].includes(command)
    )
        return failed
            ? ((
                  value: unknown,
              ):
                  | VerificationResultPayload
                  | VerificationReport
                  | EmptyPayload =>
                  wireUnion<
                      | VerificationResultPayload
                      | VerificationReport
                      | EmptyPayload
                  >(value, [
                      decodeVerificationResultPayload,
                      decodeVerificationReport,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeVerificationResultPayload(value);
    if (
        origin === "/api/v1/verifications" &&
        ["verify --revision"].includes(command)
    )
        return failed
            ? ((
                  value: unknown,
              ):
                  | VerificationResultPayload
                  | VerificationReport
                  | EmptyPayload =>
                  wireUnion<
                      | VerificationResultPayload
                      | VerificationReport
                      | EmptyPayload
                  >(value, [
                      decodeVerificationResultPayload,
                      decodeVerificationReport,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeVerificationResultPayload(value);
    if (
        origin === "/api/v1/prune-plans" &&
        ["prune --dry-run"].includes(command)
    )
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodePrunePayload(value);
    if (origin === "/api/v1/prunes" && ["prune --apply"].includes(command))
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodePrunePayload(value);
    if (
        origin === "/api/v1/purge-plans" &&
        ["purge --dry-run"].includes(command)
    )
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodePurgePayload(value);
    if (origin === "/api/v1/purges" && ["purge --apply"].includes(command))
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodePurgePayload(value);
    if (
        origin === "/api/v1/recovery-plans" &&
        ["recover --dry-run"].includes(command)
    )
        return failed
            ? ((value: unknown): RecoveryPlanPayload | EmptyPayload =>
                  wireUnion<RecoveryPlanPayload | EmptyPayload>(value, [
                      decodeRecoveryPlanPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeRecoveryPlanPayload(value);
    if (
        origin === "/api/v1/recoveries" &&
        ["recover --apply"].includes(command)
    )
        return failed
            ? ((
                  value: unknown,
              ): RecoveryPlanPayload | RecoveryAppliedPayload | EmptyPayload =>
                  wireUnion<
                      | RecoveryPlanPayload
                      | RecoveryAppliedPayload
                      | EmptyPayload
                  >(value, [
                      decodeRecoveryPlanPayload,
                      decodeRecoveryAppliedPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeRecoveryAppliedPayload(value);
    if (
        origin === "/api/v1/quarantine-plans" &&
        ["quarantine --dry-run"].includes(command)
    )
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodeQuarantinePayload(value);
    if (
        origin === "/api/v1/quarantine-cleanups" &&
        ["quarantine --apply"].includes(command)
    )
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodeQuarantinePayload(value);
    if (origin === "/api/v1/repairs" && ["repair"].includes(command))
        return failed
            ? ((value: unknown): EmptyPayload =>
                  wireUnion<EmptyPayload>(value, [decodeEmptyPayload]))(value)
            : decodeRepairPayload(value);
    if (
        origin === "/api/v1/archive/initializations" &&
        ["archive init"].includes(command)
    )
        return failed
            ? ((value: unknown): InspectionPayload | EmptyPayload =>
                  wireUnion<InspectionPayload | EmptyPayload>(value, [
                      decodeInspectionPayload,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeInitializationPayload(value);
    if (
        origin === "/api/v1/catalog/refreshes" &&
        ["catalog refresh"].includes(command)
    )
        return failed
            ? ((value: unknown): CatalogRefreshResult | EmptyPayload =>
                  wireUnion<CatalogRefreshResult | EmptyPayload>(value, [
                      decodeCatalogRefreshResult,
                      decodeEmptyPayload,
                  ]))(value)
            : decodeCatalogRefreshResult(value);
    throw new WireError("semantic");
}
export const routeDefinitions = [
    {
        binding_ids: ["ui.bootstrap"],
        commands: [],
        cursor: "none",
        failure: [],
        id: "ui_bootstrap",
        method: "GET",
        mode: "default",
        path: "/ui/bootstrap.json",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "ui_bootstrap",
        success: "UiBootstrap",
    },
    {
        binding_ids: [],
        commands: ["version"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "version",
        method: "GET",
        mode: "default",
        path: "/api/v1/version",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "VersionPayload",
    },
    {
        binding_ids: [],
        commands: ["capabilities"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "capabilities",
        method: "GET",
        mode: "default",
        path: "/api/v1/capabilities",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "Capabilities",
    },
    {
        binding_ids: [],
        commands: ["health"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "health",
        method: "GET",
        mode: "default",
        path: "/api/v1/health",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "HealthPayload",
    },
    {
        binding_ids: ["host.status"],
        commands: ["host status"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "host_status",
        method: "GET",
        mode: "default",
        path: "/api/v1/host/status",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "HostStatus",
    },
    {
        binding_ids: [],
        commands: ["config read"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "config_read",
        method: "GET",
        mode: "default",
        path: "/api/v1/config",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "ConfigRead",
    },
    {
        binding_ids: [],
        commands: ["config outcome"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "config_outcome",
        method: "GET",
        mode: "default",
        path: "/api/v1/config/applications/{operation_id}",
        path_parameters: [
            {
                name: "operation_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_run_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "ConfigApplicationOutcome",
    },
    {
        binding_ids: [],
        commands: ["archive init"],
        cursor: "none",
        failure: ["InspectionPayload", "EmptyPayload"],
        id: "inspection",
        method: "GET",
        mode: "default",
        path: "/api/v1/archive/inspection",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "InspectionPayload",
    },
    {
        binding_ids: [],
        commands: ["status"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "status",
        method: "GET",
        mode: "default",
        path: "/api/v1/status",
        path_parameters: [],
        query_parameters: [
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "selector",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 256,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 100,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "type",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "model" },
                        { kind: "literal", semantic_ids: [], value: "dataset" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "StatusPayload",
    },
    {
        binding_ids: [],
        commands: ["list"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "repositories",
        method: "GET",
        mode: "default",
        path: "/api/v1/repositories",
        path_parameters: [],
        query_parameters: [
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "selector",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 256,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 100,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "type",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "model" },
                        { kind: "literal", semantic_ids: [], value: "dataset" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "RepositoriesPayload",
    },
    {
        binding_ids: [],
        commands: ["list"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "revisions",
        method: "GET",
        mode: "default",
        path: "/api/v1/repositories/revisions",
        path_parameters: [],
        query_parameters: [
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "selector",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 256,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 100,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "type",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "model" },
                        { kind: "literal", semantic_ids: [], value: "dataset" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "RevisionsPayload",
    },
    {
        binding_ids: [],
        commands: ["verify --estimate"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "estimate",
        method: "GET",
        mode: "default",
        path: "/api/v1/verification/estimate",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "EstimatePayload",
    },
    {
        binding_ids: [],
        commands: ["runs"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "runs",
        method: "GET",
        mode: "default",
        path: "/api/v1/runs",
        path_parameters: [],
        query_parameters: [
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "RunsPayload",
    },
    {
        binding_ids: ["run.report"],
        commands: ["runs read"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "report",
        method: "GET",
        mode: "default",
        path: "/api/v1/runs/{run_id}",
        path_parameters: [
            {
                name: "run_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_run_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "ReportPayload",
    },
    {
        binding_ids: ["publication.reference"],
        commands: ["reference read"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "reference",
        method: "GET",
        mode: "default",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/references/{revision}",
        path_parameters: [
            {
                name: "repository_type",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_repository_type"],
                },
            },
            {
                name: "namespace",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "name",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "revision",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "current" },
                        {
                            kind: "string",
                            max_codepoints: 256,
                            min_codepoints: 1,
                            pattern: null,
                            semantic_ids: ["hfcache.identity.parse_commit_sha"],
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "ReferencePayload",
    },
    {
        binding_ids: ["publication.manifest"],
        commands: ["manifest read"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "manifest",
        method: "GET",
        mode: "default",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/manifests/{commit_sha}/{publication_id}",
        path_parameters: [
            {
                name: "repository_type",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_repository_type"],
                },
            },
            {
                name: "namespace",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "name",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "commit_sha",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_commit_sha"],
                },
            },
            {
                name: "publication_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_publication_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "ManifestPayload",
    },
    {
        binding_ids: ["publication.card"],
        commands: ["card read"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "repository_card",
        method: "GET",
        mode: "default",
        path: "/api/v1/repositories/{repository_type}/{namespace}/{name}/publications/{commit_sha}/{publication_id}/card",
        path_parameters: [
            {
                name: "repository_type",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_repository_type"],
                },
            },
            {
                name: "namespace",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "name",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "commit_sha",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_commit_sha"],
                },
            },
            {
                name: "publication_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_publication_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "RepositoryCardRead",
    },
    {
        binding_ids: [],
        commands: ["operations list"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "operations",
        method: "GET",
        mode: "default",
        path: "/api/v1/operations",
        path_parameters: [],
        query_parameters: [
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "OperationsPayload",
    },
    {
        binding_ids: ["operation.identity"],
        commands: ["operations lookup"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "operation_lookup",
        method: "GET",
        mode: "default",
        path: "/api/v1/operations/lookup",
        path_parameters: [],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "OperationPayload",
    },
    {
        binding_ids: ["operation.identity"],
        commands: ["operations show"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "operation",
        method: "GET",
        mode: "default",
        path: "/api/v1/operations/{operation_id}",
        path_parameters: [
            {
                name: "operation_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_run_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "read",
        success: "OperationPayload",
    },
    {
        binding_ids: ["operation.events"],
        commands: ["operations events"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "operation_events",
        method: "GET",
        mode: "default",
        path: "/api/v1/operations/{operation_id}/events",
        path_parameters: [
            {
                name: "operation_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_run_id"],
                },
            },
        ],
        query_parameters: [
            {
                name: "after",
                node: {
                    kind: "integer",
                    maximum: "9999999999",
                    minimum: "0",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "ClientEvents",
    },
    {
        binding_ids: ["operation.result"],
        commands: [],
        cursor: "none",
        failure: [],
        id: "operation_result",
        method: "GET",
        mode: "by_original_operation",
        path: "/api/v1/operations/{operation_id}/result",
        path_parameters: [
            {
                name: "operation_id",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_run_id"],
                },
            },
        ],
        query_parameters: [],
        request_body: null,
        response_kind: "operation_result",
        success: null,
    },
    {
        binding_ids: ["catalog.response"],
        commands: ["catalog.search"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "catalog_search",
        method: "GET",
        mode: "default",
        path: "/api/v1/catalog/search",
        path_parameters: [],
        query_parameters: [
            {
                name: "type",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "model" },
                        { kind: "literal", semantic_ids: [], value: "dataset" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "q",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "tag_all",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 128,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 64,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "tag_any",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 128,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 64,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "tag_source",
                node: {
                    choices: [
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "current_or_last_observed",
                        },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "current_only",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "scope",
                node: {
                    choices: [
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "archived",
                        },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "configured",
                        },
                        { kind: "literal", semantic_ids: [], value: "all" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "revision_scope",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "current" },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "retained",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "format",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "quantization",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "quantization_method",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "bits",
                node: {
                    kind: "integer",
                    maximum: "64",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "max_variant_bytes",
                node: {
                    kind: "integer",
                    maximum: "9223372036854775807",
                    minimum: "0",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "CatalogSearchPayload",
    },
    {
        binding_ids: ["catalog.response", "catalog.facet"],
        commands: ["catalog.facets"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "catalog_facets",
        method: "GET",
        mode: "default",
        path: "/api/v1/catalog/facets",
        path_parameters: [],
        query_parameters: [
            {
                name: "type",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "model" },
                        { kind: "literal", semantic_ids: [], value: "dataset" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "q",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "tag_all",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 128,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 64,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "tag_any",
                node: {
                    items: {
                        kind: "string",
                        max_codepoints: 128,
                        min_codepoints: 0,
                        pattern: null,
                        semantic_ids: [],
                    },
                    kind: "array",
                    max_items: 64,
                    min_items: null,
                    semantic_ids: [],
                },
                repeated: true,
            },
            {
                name: "tag_source",
                node: {
                    choices: [
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "current_or_last_observed",
                        },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "current_only",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "scope",
                node: {
                    choices: [
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "archived",
                        },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "configured",
                        },
                        { kind: "literal", semantic_ids: [], value: "all" },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "revision_scope",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "current" },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "retained",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "format",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "quantization",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "quantization_method",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "bits",
                node: {
                    kind: "integer",
                    maximum: "64",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "max_variant_bytes",
                node: {
                    kind: "integer",
                    maximum: "9223372036854775807",
                    minimum: "0",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "facet",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "tag" },
                        { kind: "literal", semantic_ids: [], value: "format" },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "quantization_method",
                        },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "quantization",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "CatalogFacetPayload",
    },
    {
        binding_ids: ["catalog.response", "catalog.publication"],
        commands: ["catalog.detail"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "catalog_detail",
        method: "GET",
        mode: "default",
        path: "/api/v1/catalog/repositories/{repository_type}/{namespace}/{name}",
        path_parameters: [
            {
                name: "repository_type",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_repository_type"],
                },
            },
            {
                name: "namespace",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "name",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
        ],
        query_parameters: [
            {
                name: "revision_scope",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "current" },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "retained",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "commit_sha",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_commit_sha"],
                },
                repeated: false,
            },
            {
                name: "publication_id",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_publication_id"],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "CatalogDetailPayload",
    },
    {
        binding_ids: ["catalog.response", "catalog.publication"],
        commands: ["catalog.variants"],
        cursor: "opaque",
        failure: ["EmptyPayload"],
        id: "catalog_variants",
        method: "GET",
        mode: "default",
        path: "/api/v1/catalog/repositories/{repository_type}/{namespace}/{name}/variants",
        path_parameters: [
            {
                name: "repository_type",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 1,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_repository_type"],
                },
            },
            {
                name: "namespace",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
            {
                name: "name",
                node: {
                    kind: "string",
                    max_codepoints: 96,
                    min_codepoints: 1,
                    pattern: "^[A-Za-z0-9][A-Za-z0-9._-]*$",
                    semantic_ids: [],
                },
            },
        ],
        query_parameters: [
            {
                name: "revision_scope",
                node: {
                    choices: [
                        { kind: "literal", semantic_ids: [], value: "current" },
                        {
                            kind: "literal",
                            semantic_ids: [],
                            value: "retained",
                        },
                    ],
                    kind: "union",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "commit_sha",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_commit_sha"],
                },
                repeated: false,
            },
            {
                name: "publication_id",
                node: {
                    kind: "string",
                    max_codepoints: 64,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: ["hfcache.identity.parse_publication_id"],
                },
                repeated: false,
            },
            {
                name: "limit",
                node: {
                    kind: "integer",
                    maximum: "10000",
                    minimum: "1",
                    semantic_ids: [],
                },
                repeated: false,
            },
            {
                name: "cursor",
                node: {
                    kind: "string",
                    max_codepoints: 256,
                    min_codepoints: 0,
                    pattern: null,
                    semantic_ids: [],
                },
                repeated: false,
            },
        ],
        request_body: null,
        response_kind: "read",
        success: "CatalogVariantsPayload",
    },
    {
        binding_ids: [],
        commands: ["config apply"],
        cursor: "none",
        failure: [],
        id: "config_apply",
        method: "POST",
        mode: "default",
        path: "/api/v1/config/applications",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestConfigApplicationSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["sync"],
        cursor: "none",
        failure: [],
        id: "sync",
        method: "POST",
        mode: "default",
        path: "/api/v1/syncs",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestSyncSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["plan"],
        cursor: "none",
        failure: [],
        id: "plan",
        method: "POST",
        mode: "installed",
        path: "/api/v1/plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestInstalledPlan",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["plan"],
        cursor: "none",
        failure: [],
        id: "plan",
        method: "POST",
        mode: "literal_candidate",
        path: "/api/v1/plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestLiteralCandidatePlan",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["plan"],
        cursor: "none",
        failure: [],
        id: "plan",
        method: "POST",
        mode: "managed",
        path: "/api/v1/plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestManagedPlanRequest",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["doctor"],
        cursor: "none",
        failure: [],
        id: "diagnostics",
        method: "POST",
        mode: "read_only",
        path: "/api/v1/diagnostics",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestReadOnlyDiagnostics",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["doctor"],
        cursor: "none",
        failure: [],
        id: "diagnostics",
        method: "POST",
        mode: "probe",
        path: "/api/v1/diagnostics",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestProbeDiagnostics",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["verify --new"],
        cursor: "none",
        failure: [],
        id: "verification",
        method: "POST",
        mode: "new",
        path: "/api/v1/verifications",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestNewVerification",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["verify --full"],
        cursor: "none",
        failure: [],
        id: "verification",
        method: "POST",
        mode: "full",
        path: "/api/v1/verifications",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestFullVerification",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["verify --revision"],
        cursor: "none",
        failure: [],
        id: "verification",
        method: "POST",
        mode: "revision",
        path: "/api/v1/verifications",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestRevisionVerification",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["prune --dry-run"],
        cursor: "none",
        failure: [],
        id: "prune_preview",
        method: "POST",
        mode: "default",
        path: "/api/v1/prune-plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestPruneSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["prune --apply"],
        cursor: "none",
        failure: [],
        id: "prune_apply",
        method: "POST",
        mode: "default",
        path: "/api/v1/prunes",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestPruneSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["purge --dry-run"],
        cursor: "none",
        failure: [],
        id: "purge_preview",
        method: "POST",
        mode: "default",
        path: "/api/v1/purge-plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestPurgeSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["purge --apply"],
        cursor: "none",
        failure: [],
        id: "purge_apply",
        method: "POST",
        mode: "default",
        path: "/api/v1/purges",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestPurgeSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["recover --dry-run"],
        cursor: "none",
        failure: [],
        id: "recovery_preview",
        method: "POST",
        mode: "default",
        path: "/api/v1/recovery-plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestRecoverySubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["recover --apply"],
        cursor: "none",
        failure: [],
        id: "recovery_apply",
        method: "POST",
        mode: "default",
        path: "/api/v1/recoveries",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestRecoverySubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["quarantine --dry-run"],
        cursor: "none",
        failure: [],
        id: "quarantine_preview",
        method: "POST",
        mode: "default",
        path: "/api/v1/quarantine-plans",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestQuarantineSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["quarantine --apply"],
        cursor: "none",
        failure: [],
        id: "quarantine_apply",
        method: "POST",
        mode: "default",
        path: "/api/v1/quarantine-cleanups",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestQuarantineSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["repair"],
        cursor: "none",
        failure: [],
        id: "repair",
        method: "POST",
        mode: "default",
        path: "/api/v1/repairs",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestRepairSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["archive init"],
        cursor: "none",
        failure: [],
        id: "initialization",
        method: "POST",
        mode: "default",
        path: "/api/v1/archive/initializations",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestInitializationSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["catalog refresh"],
        cursor: "none",
        failure: [],
        id: "catalog_refresh",
        method: "POST",
        mode: "default",
        path: "/api/v1/catalog/refreshes",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestCatalogRefreshSubmission",
        response_kind: "acceptance",
        success: "Acceptance",
    },
    {
        binding_ids: [],
        commands: ["config validate"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "config_validate",
        method: "POST",
        mode: "installed",
        path: "/api/v1/config/validate",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestInstalledValidation",
        response_kind: "read",
        success: "InstalledValidationPayload",
    },
    {
        binding_ids: [],
        commands: ["config validate"],
        cursor: "none",
        failure: ["CandidateInvalidPayload"],
        id: "config_validate",
        method: "POST",
        mode: "literal_candidate",
        path: "/api/v1/config/validate",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestLiteralCandidateValidation",
        response_kind: "read",
        success: "CandidateValidPayload",
    },
    {
        binding_ids: [],
        commands: ["config validate"],
        cursor: "none",
        failure: ["EmptyPayload"],
        id: "config_validate",
        method: "POST",
        mode: "managed",
        path: "/api/v1/config/validate",
        path_parameters: [],
        query_parameters: [],
        request_body: "RequestManagedValidationRequest",
        response_kind: "read",
        success: "ManagedValidation",
    },
] as const;
export const operationResultDefinitions = [
    {
        binding_ids: ["operation.result"],
        commands: ["config apply"],
        failure: ["ConfigApplicationOutcome", "EmptyPayload"],
        origin_path: "/api/v1/config/applications",
        success: "ConfigApplicationOutcome",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["sync"],
        failure: ["RunResultPayload", "EmptyPayload"],
        origin_path: "/api/v1/syncs",
        success: "RunResultPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["plan"],
        failure: ["PlanResultPayload", "EmptyPayload"],
        origin_path: "/api/v1/plans",
        success: "PlanResultPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["doctor"],
        failure: ["DiagnosticsPayload", "EmptyPayload"],
        origin_path: "/api/v1/diagnostics",
        success: "DiagnosticsPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["verify --new"],
        failure: [
            "VerificationResultPayload",
            "VerificationReport",
            "EmptyPayload",
        ],
        origin_path: "/api/v1/verifications",
        success: "VerificationResultPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["verify --full"],
        failure: [
            "VerificationResultPayload",
            "VerificationReport",
            "EmptyPayload",
        ],
        origin_path: "/api/v1/verifications",
        success: "VerificationResultPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["verify --revision"],
        failure: [
            "VerificationResultPayload",
            "VerificationReport",
            "EmptyPayload",
        ],
        origin_path: "/api/v1/verifications",
        success: "VerificationResultPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["prune --dry-run"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/prune-plans",
        success: "PrunePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["prune --apply"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/prunes",
        success: "PrunePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["purge --dry-run"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/purge-plans",
        success: "PurgePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["purge --apply"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/purges",
        success: "PurgePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["recover --dry-run"],
        failure: ["RecoveryPlanPayload", "EmptyPayload"],
        origin_path: "/api/v1/recovery-plans",
        success: "RecoveryPlanPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["recover --apply"],
        failure: [
            "RecoveryPlanPayload",
            "RecoveryAppliedPayload",
            "EmptyPayload",
        ],
        origin_path: "/api/v1/recoveries",
        success: "RecoveryAppliedPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["quarantine --dry-run"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/quarantine-plans",
        success: "QuarantinePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["quarantine --apply"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/quarantine-cleanups",
        success: "QuarantinePayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["repair"],
        failure: ["EmptyPayload"],
        origin_path: "/api/v1/repairs",
        success: "RepairPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["archive init"],
        failure: ["InspectionPayload", "EmptyPayload"],
        origin_path: "/api/v1/archive/initializations",
        success: "InitializationPayload",
    },
    {
        binding_ids: ["operation.result"],
        commands: ["catalog refresh"],
        failure: ["CatalogRefreshResult", "EmptyPayload"],
        origin_path: "/api/v1/catalog/refreshes",
        success: "CatalogRefreshResult",
    },
] as const;
