/** Explicit ports of decision153's finite public configuration vocabulary. */
import { canonicalHex, repositorySegments } from "../api/identity";
import { WireError } from "./json";
import { isRecord } from "./runtime";

function check(value: boolean): void {
    if (!value) throw new WireError("semantic");
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
function list(value: unknown): readonly unknown[] {
    if (!Array.isArray(value)) throw new WireError("semantic");
    return value;
}
function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}
function unique(values: readonly unknown[]): void {
    check(new Set(values).size === values.length);
}
function repositoryKey(value: unknown): string {
    const row = record(value);
    return text(row.type) + ":" + text(row.id);
}
const editableFields = [
    "storage.publication_mode",
    "storage.minimum_free_space_gib",
    "storage.minimum_free_space_percent",
    "storage.maximum_revisions",
    "sync.max_workers",
    "sync.lock_wait_seconds",
    "sync.continue_on_repository_error",
    "sync.dependency_policy",
    "sync.stale_staging_age_hours",
    "verification.lock_wait_seconds",
    "repair.retired_instance_grace_hours",
    "repositories",
];
const protectedFields = [
    [
        "storage.archive_root",
        "Archive root is fixed by installed deployment authority.",
    ],
    [
        "storage.archive_id",
        "Archive identity is fixed by installed deployment authority.",
    ],
    ["hub", "Hub endpoint and credential authority are preserved privately."],
    ["verification.algorithm", "The verification algorithm is fixed."],
    ["verification.hash_new_content", "Hashing new content is required."],
    [
        "server",
        "Server policy and credentials are managed outside archive configuration.",
    ],
];

export function normalizeManagedTags(value: unknown): readonly string[] {
    const values = list(value);
    check(values.length <= 64);
    const normalized = values.map((item) => {
        const source = text(item);
        check(Array.from(source).length <= 128);
        const tag = source
            .replace(/^ +| +$/gu, "")
            .replace(/[A-Z]/gu, (letter) => letter.toLowerCase());
        check(/[a-z0-9][a-z0-9._:/-]{0,63}/u.exec(tag)?.[0] === tag);
        return tag;
    });
    return [...new Set(normalized)].sort();
}

export const configSemanticIds: readonly string[] = [
    "hfcache.config_models._one",
    "hfcache.config_models._revision",
    "hfcache.config_models._preview_key",
    "hfcache.config_models.ConfigApplicationOutcome.coherent_identity",
    "hfcache.config_models._whole_selector",
    "hfcache.config_models._retention",
    "hfcache.config_models.EditableConfig.unique_repositories",
    "hfcache.config_models.SettingsTable.nonempty",
    "hfcache.config_models.ManagedEditRequest.unique_edits",
    "hfcache.config_models.ProtectedField.fixed_description",
    "hfcache.config_models.ConfigRead.fixed_fields",
    "hfcache.config_models.ManagedValidation.strict_valid",
    "hfcache.config_models.ManagedValidation.unique_scope",
    "hfcache.config_models.ManagedAssessment.complete_scope",
    "hfcache.config.RepositoryConfig._check",
    "hfcache.identity.parse_revision",
    "hfcache.tags.normalize_tags",
];

export function applyConfigSemantic(id: string, value: unknown): void {
    switch (id) {
        case "hfcache.config_models._one":
            check(value === 1);
            return;
        case "hfcache.config_models._revision":
            check(canonicalHex(text(value), 64));
            return;
        case "hfcache.config_models._preview_key": {
            const source = text(value);
            check(/^[A-Za-z0-9._~+-]{1,128}$/u.exec(source)?.[0] === source);
            return;
        }
        case "hfcache.config_models.ConfigApplicationOutcome.coherent_identity": {
            const row = record(value),
                known = [
                    row.base_revision,
                    row.candidate_revision,
                    row.config_fingerprint,
                ].map((item) => item !== null);
            check(
                (known.every(Boolean) || known.every((item) => !item)) &&
                    (row.state === "unknown" || known.every(Boolean)),
            );
            return;
        }
        case "hfcache.config_models._whole_selector": {
            const source = text(value),
                colon = source.indexOf(":");
            check(colon > 0 && !source.includes("@"));
            repositorySegments(source.slice(0, colon), source.slice(colon + 1));
            return;
        }
        case "hfcache.config_models._retention":
            check(value === 3 || value === 5);
            return;
        case "hfcache.config_models.EditableConfig.unique_repositories":
            unique(list(record(value).repositories).map(repositoryKey));
            return;
        case "hfcache.config_models.SettingsTable.nonempty": {
            const values = Object.values(record(value));
            check(values.length > 0 && values.every((item) => item !== null));
            return;
        }
        case "hfcache.config_models.ManagedEditRequest.unique_edits": {
            const edits = list(record(value).edits).map(record);
            check(
                edits.filter((row) => row.kind === "settings-replace").length <=
                    1,
            );
            unique(
                edits
                    .filter((row) => row.kind !== "settings-replace")
                    .map((row) =>
                        row.kind === "repository-upsert"
                            ? repositoryKey(row.repository)
                            : text(row.repository_type) +
                              ":" +
                              text(row.repository_id),
                    ),
            );
            return;
        }
        case "hfcache.config_models.ProtectedField.fixed_description": {
            const row = record(value);
            check(
                protectedFields.some(
                    ([field, description]) =>
                        field === row.field && description === row.description,
                ),
            );
            return;
        }
        case "hfcache.config_models.ConfigRead.fixed_fields": {
            const row = record(value);
            check(
                JSON.stringify(row.editable_fields) ===
                    JSON.stringify(editableFields),
            );
            const projected = list(row.protected_fields).map((item) => {
                const field = record(item);
                return [field.field, field.description];
            });
            check(
                JSON.stringify(projected) === JSON.stringify(protectedFields),
            );
            return;
        }
        case "hfcache.config_models.ManagedValidation.strict_valid":
            check(record(value).valid === true);
            return;
        case "hfcache.config_models.ManagedValidation.unique_scope":
            unique(list(record(value).required_selectors));
            return;
        case "hfcache.config_models.ManagedAssessment.complete_scope": {
            const row = record(value),
                required = list(row.required_selectors);
            unique(required);
            if (required.length === 0) {
                check(row.sizing === null);
                return;
            }
            if (row.sizing === null) {
                check(row.complete === false);
                return;
            }
            const repositories = list(record(row.sizing).repositories).map(
                record,
            );
            const selectors = repositories.map(
                (item) =>
                    text(item.repository_type) + ":" + text(item.repository_id),
            );
            unique(selectors);
            check(
                selectors.length === required.length &&
                    selectors.every((item) => required.includes(item)),
            );
            if (row.complete === true)
                for (const item of repositories) {
                    check(
                        item.enabled === true &&
                            item.upstream_state === "available",
                    );
                    check(
                        [
                            item.resolved_commit_sha,
                            item.estimated_new_bytes,
                            item.file_count,
                            item.logical_bytes,
                            item.projected_publication_bytes,
                        ].every((part) => part !== null),
                    );
                }
            return;
        }
        case "hfcache.config.RepositoryConfig._check":
            unique(list(record(value).declared_dependencies ?? []));
            return;
        case "hfcache.identity.parse_revision": {
            const source = text(value);
            if (canonicalHex(source, 40)) return;
            check(
                !/[0-9a-fA-F]{4,40}/u.exec(source)?.[0] ||
                    /[0-9a-fA-F]{4,40}/u.exec(source)?.[0] !== source,
            );
            check(
                /[A-Za-z0-9._/-]{1,255}/u.exec(source)?.[0] === source &&
                    !source.startsWith("-") &&
                    !source.startsWith("/") &&
                    !source.endsWith("/") &&
                    !source.endsWith(".lock") &&
                    !source.includes("//") &&
                    !source.includes(".."),
            );
            return;
        }
        case "hfcache.tags.normalize_tags":
            check(
                JSON.stringify(value) ===
                    JSON.stringify(normalizeManagedTags(value)),
            );
            return;
        default:
            throw new WireError("semantic");
    }
}
