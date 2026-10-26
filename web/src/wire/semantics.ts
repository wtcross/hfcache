/** Explicit ports of audited Python invariants, applied to reconstructed values. */
import { WireError } from "./json";
import { isRecord } from "./runtime";
import {
    canonicalArchiveId,
    canonicalHex,
    repositorySegments,
} from "../api/identity";
import { applyCatalogSemantic, catalogSemanticIds } from "./catalog-semantics";
import {
    applyManifestSemantic,
    manifestSemanticIds,
} from "./manifest-semantics";
import { contextSemanticIds } from "../api/bindings";
import { applyHostSemantic, hostSemanticIds } from "./host-semantics";
import { applyConfigSemantic, configSemanticIds } from "./config-semantics";
import { applyCardSemantic, cardSemanticIds } from "./card-semantics";
import { pythonIsPrintable } from "./unicode";
import {
    applyUiSemantic,
    uiSemanticIds,
    uiContextSemanticIds,
} from "./ui-semantics";

function check(condition: boolean): void {
    if (!condition) throw new WireError("semantic");
}
function record(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new WireError("semantic");
    return value;
}
function text(value: unknown): string {
    if (typeof value !== "string") throw new WireError("semantic");
    return value;
}
function integer(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value))
        throw new WireError("semantic");
    return value;
}
function list(value: unknown): readonly unknown[] {
    if (!Array.isArray(value)) throw new WireError("semantic");
    const result: unknown[] = value;
    return result;
}
function strings(value: unknown): readonly string[] {
    return list(value).map(text);
}
function items(value: unknown): readonly Record<string, unknown>[] {
    return list(value).map(record);
}

export function compareCodePoints(left: string, right: string): number {
    const a = Array.from(left, (item) => item.codePointAt(0) ?? 0);
    const b = Array.from(right, (item) => item.codePointAt(0) ?? 0);
    for (let index = 0; index < Math.min(a.length, b.length); index++) {
        const x = a[index],
            y = b[index];
        if (x !== undefined && y !== undefined && x !== y)
            return x < y ? -1 : 1;
    }
    return a.length === b.length ? 0 : a.length < b.length ? -1 : 1;
}

function ordered(values: readonly string[], unique: boolean): void {
    for (let index = 1; index < values.length; index++) {
        const left = values[index - 1],
            right = values[index];
        if (left === undefined || right === undefined)
            throw new WireError("semantic");
        const comparison = compareCodePoints(left, right);
        check(comparison < 0 || (!unique && comparison === 0));
    }
}

function orderedRecords(
    values: readonly Record<string, unknown>[],
    fields: readonly string[],
    unique: boolean,
): void {
    const keys = values.map((value) =>
        fields.map((field) =>
            value[field] === null ? "" : text(value[field]),
        ),
    );
    for (let index = 1; index < keys.length; index++) {
        const left = keys[index - 1],
            right = keys[index];
        if (left === undefined || right === undefined)
            throw new WireError("semantic");
        let comparison = 0;
        for (let part = 0; part < fields.length; part++) {
            const a = left[part],
                b = right[part];
            if (a === undefined || b === undefined)
                throw new WireError("semantic");
            comparison = compareCodePoints(a, b);
            if (comparison !== 0) break;
        }
        check(comparison < 0 || (!unique && comparison === 0));
    }
}

export function timestampParts(
    value: unknown,
    serialized = false,
): readonly number[] {
    const source = text(value);
    const match =
        /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/u.exec(
            source,
        );
    if (match === null || match[0] !== source) throw new WireError("semantic");
    const year = Number(match[1]),
        month = Number(match[2]),
        day = Number(match[3]);
    const hour = Number(match[4]),
        minute = Number(match[5]),
        second = Number(match[6]);
    const fraction = match[7] ?? "";
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][
        month - 1
    ];
    check(
        year >= 1 &&
            year <= 9999 &&
            days !== undefined &&
            day >= 1 &&
            day <= days &&
            hour < 24 &&
            minute < 60 &&
            second < 60 &&
            (!serialized || fraction.length === 6),
    );
    return [
        year,
        month,
        day,
        hour,
        minute,
        second,
        Number(fraction.padEnd(6, "0")),
    ];
}

export function compareTimestamps(left: unknown, right: unknown): number {
    const a = timestampParts(left),
        b = timestampParts(right);
    for (let index = 0; index < a.length; index++) {
        const x = a[index],
            y = b[index];
        if (x !== undefined && y !== undefined && x !== y)
            return x < y ? -1 : 1;
    }
    return 0;
}

function selector(
    value: unknown,
    requireRevision: boolean,
    forbidRevision: boolean,
): void {
    const source = text(value),
        colon = source.indexOf(":"),
        at = source.indexOf("@");
    const identity =
        at < 0 ? source.slice(colon + 1) : source.slice(colon + 1, at);
    check(colon > 0);
    repositorySegments(source.slice(0, colon), identity);
    check((!requireRevision || at >= 0) && (!forbidRevision || at < 0));
    if (at >= 0) check(canonicalHex(source.slice(at + 1), 40));
}

const jobs = new Set(
    [
        "syncs",
        "plans",
        "verifications",
        "diagnostics",
        "prune-plans",
        "prunes",
        "purge-plans",
        "purges",
        "recovery-plans",
        "recoveries",
        "quarantine-plans",
        "quarantine-cleanups",
        "repairs",
        "archive/initializations",
        "catalog/refreshes",
        "config/applications",
    ].map((item) => "/api/v1/" + item),
);
const exitCodes = new Set([0, 10, 20, 30, 40, 50]);
function envelope(value: Record<string, unknown>, invocation: boolean): void {
    const exit = integer(value.exit_code),
        outcome = text(value.outcome),
        warnings = list(value.warnings);
    check(
        exitCodes.has(exit) &&
            (exit === 0) ===
                ["success", "success_with_warnings"].includes(outcome),
    );
    if (outcome !== "failed")
        check((outcome === "success_with_warnings") === warnings.length > 0);
    if (invocation)
        check(
            integer(value.schema_version) === 1 &&
                (outcome !== "failed" || list(value.errors).length > 0),
        );
    else check(compareTimestamps(value.completed_at, value.started_at) >= 0);
}

export const ownSemanticIds: readonly string[] = [
    "hfcache.client_models.ClientRead.coherent_envelope",
    "hfcache.client_models.ClientRead.required_envelope_version",
    "hfcache.client_models.exact_version",
    "hfcache.client_models._archive_id",
    "hfcache.client_models.Acceptance.identity",
    "hfcache.client_models.ClientOperation.evidence",
    "hfcache.client_models.Capabilities.permissions",
    "hfcache.client_models.ClientEvent.timestamp",
    "hfcache.identity.parse_run_id",
    "hfcache.identity.parse_transaction_id",
    "hfcache.identity.parse_publication_id",
    "hfcache.identity.parse_commit_sha",
    "hfcache.identity.parse_repository_type",
    "hfcache.identity.parse_repository_id",
    "hfcache.models._parse_archive_id",
    "hfcache.config._parse_archive_id",
    "hfcache.models._parse_sha256",
    "hfcache.models.VersionedModel._check_schema_version",
    "timestamp.serialized",
    "timestamp.wire",
    "hfcache.reporting.Envelope._check",
    "hfcache.reporting.RunEnvelope._check_envelope",
    "hfcache.reporting.RunReport._check",
    "hfcache.reporting.RepositoryRunResult._check",
    "hfcache.reporting.VerificationReport._check",
    "hfcache.reporting.Finding._check",
    "hfcache.reporting.RecoveryReport._check",
    "hfcache.models.PrunePlan._check",
    "hfcache.models.PurgePlan._check",
    "hfcache.api.command_models._selection",
    "hfcache.api.command_models._candidate_text",
    "hfcache.api.command_models.SyncSubmission.canonical",
    "hfcache.api.command_models.PlanSubmission.explicit_candidate",
    "hfcache.api.command_models.ValidationSubmission.explicit_candidate",
    "hfcache.api.command_models.VerificationSubmission.scope",
    "hfcache.api.command_models.CatalogRefreshSubmission.canonical",
    "hfcache.api.maintenance_models._whole_repository",
    "hfcache.api.maintenance_models.PurgeSubmission.scope",
    "hfcache.api.maintenance_models.QuarantineSubmission.canonical",
    "hfcache.api.maintenance_models.RepairSubmission.scope",
    "hfcache.api.maintenance_models.InitializationSubmission.confirmation",
    "hfcache.api.maintenance_models._archive_root",
];
export const implementedSemanticIds: readonly string[] = [
    ...ownSemanticIds,
    ...catalogSemanticIds,
    ...manifestSemanticIds,
    ...contextSemanticIds,
    ...uiSemanticIds,
    ...uiContextSemanticIds,
    ...hostSemanticIds,
    ...configSemanticIds,
    ...cardSemanticIds,
];

export function applySemantic(id: string, value: unknown): void {
    if (cardSemanticIds.includes(id)) {
        applyCardSemantic(id, value);
        return;
    }
    if (configSemanticIds.includes(id)) {
        applyConfigSemantic(id, value);
        return;
    }
    if (hostSemanticIds.includes(id)) {
        applyHostSemantic(id, value);
        return;
    }
    if (uiSemanticIds.includes(id)) {
        applyUiSemantic(id, value);
        return;
    }
    if (catalogSemanticIds.includes(id)) {
        applyCatalogSemantic(id, value);
        return;
    }
    if (manifestSemanticIds.includes(id)) {
        applyManifestSemantic(id, value);
        return;
    }
    switch (id) {
        case "timestamp.serialized":
            timestampParts(value, true);
            return;
        case "timestamp.wire":
            timestampParts(value);
            return;
        case "hfcache.client_models.exact_version":
            check(integer(value) === 1);
            return;
        case "hfcache.models.VersionedModel._check_schema_version":
            check(record(value).schema_version === 1);
            return;
        case "hfcache.client_models._archive_id":
        case "hfcache.models._parse_archive_id":
        case "hfcache.config._parse_archive_id":
            check(canonicalArchiveId(text(value)));
            return;
        case "hfcache.identity.parse_run_id":
        case "hfcache.identity.parse_transaction_id":
        case "hfcache.identity.parse_publication_id":
            check(canonicalHex(text(value), 32));
            return;
        case "hfcache.identity.parse_commit_sha":
            check(canonicalHex(text(value), 40));
            return;
        case "hfcache.models._parse_sha256":
            check(canonicalHex(text(value), 64));
            return;
        case "hfcache.identity.parse_repository_type":
            check(value === "model" || value === "dataset");
            return;
        case "hfcache.identity.parse_repository_id":
            repositorySegments("model", text(value));
            return;
        case "hfcache.client_models.ClientEvent.timestamp":
            timestampParts(record(value).at);
            return;
        case "hfcache.client_models.ClientRead.required_envelope_version":
            check(record(record(value).envelope).schema_version === 1);
            return;
        case "hfcache.client_models.ClientRead.coherent_envelope": {
            const data = record(record(value).envelope);
            check(
                compareTimestamps(data.completed_at, data.started_at) >= 0 &&
                    !(data.exit_code === 0 && list(data.errors).length > 0),
            );
            return;
        }
        case "hfcache.client_models.Acceptance.identity": {
            const data = record(value),
                operation = record(data.operation);
            check(
                data.archive_id === operation.archive_id &&
                    data.config_fingerprint === operation.config_fingerprint,
            );
            return;
        }
        case "hfcache.client_models.Capabilities.permissions": {
            const data = record(value),
                capabilities = strings(data.capabilities);
            const expected =
                data.credential_class === "rest-writer"
                    ? ["read", "write"]
                    : ["read"];
            check(
                new Set(capabilities).size === capabilities.length &&
                    capabilities.length === expected.length &&
                    expected.every((item) => capabilities.includes(item)),
            );
            return;
        }
        case "hfcache.client_models.ClientOperation.evidence": {
            const data = record(value),
                state = text(data.state),
                active = ["queued", "waiting_lock", "running"].includes(state),
                terminal = ["succeeded", "failed"].includes(state);
            check(
                jobs.has(text(data.route)) &&
                    compareTimestamps(data.updated_at, data.created_at) >= 0,
            );
            if (data.completed_at !== null)
                check(
                    compareTimestamps(data.completed_at, data.created_at) >=
                        0 &&
                        compareTimestamps(data.completed_at, data.updated_at) <=
                            0,
                );
            check(
                !(
                    active &&
                    (data.completed_at !== null ||
                        data.result_recorded === true)
                ) &&
                    !(!active && data.completed_at === null) &&
                    !(
                        terminal &&
                        (data.result_recorded !== true ||
                            data.domain_run_id === null)
                    ) &&
                    !(state === "interrupted" && data.result_recorded === true),
            );
            return;
        }
        case "hfcache.reporting.Envelope._check":
            envelope(record(value), true);
            return;
        case "hfcache.reporting.RunEnvelope._check_envelope":
            envelope(record(value), false);
            return;
        case "hfcache.reporting.RunReport._check":
            orderedRecords(
                items(record(value).repositories),
                ["repository_type", "repository_id"],
                true,
            );
            return;
        case "hfcache.reporting.RepositoryRunResult._check": {
            const data = record(value);
            check(
                !(
                    data.status === "published" && data.publication_id === null
                ) &&
                    !(
                        data.status === "failed" &&
                        list(data.errors).length === 0
                    ) &&
                    !(
                        data.status === "completed_with_warnings" &&
                        list(data.warnings).length === 0
                    ),
            );
            return;
        }
        case "hfcache.reporting.VerificationReport._check": {
            const data = record(value),
                findings = items(data.findings);
            check(
                (data.verification_outcome === "failed") ===
                    findings.length > 0,
            );
            orderedRecords(
                findings,
                [
                    "repository_type",
                    "repository_id",
                    "commit_sha",
                    "path",
                    "kind",
                ],
                false,
            );
            return;
        }
        case "hfcache.reporting.Finding._check": {
            const data = record(value);
            check(
                data.commit_sha !== null ||
                    (data.kind === "ref_invalid" &&
                        data.publication_id === null &&
                        data.path === null),
            );
            return;
        }
        case "hfcache.reporting.RecoveryReport._check":
            ordered(
                items(record(value).remediations).map((item) =>
                    text(item.transaction_id),
                ),
                true,
            );
            return;
        case "hfcache.models.PrunePlan._check": {
            const data = record(value),
                selected = record(data.selected),
                held = items(data.retained).map((item) =>
                    integer(item.publication_generation),
                );
            check(
                new Set(held).size === held.length &&
                    selected.publication_generation ===
                        held.reduce(
                            (minimum, generation) =>
                                Math.min(minimum, generation),
                            held[0] ?? 0,
                        ) &&
                    selected.commit_sha !== record(data.current).commit_sha,
            );
            return;
        }
        case "hfcache.models.PurgePlan._check": {
            const data = record(value),
                revisions = items(data.revisions),
                generations = revisions.map((item) =>
                    integer(item.publication_generation),
                ),
                commits = revisions.map((item) => text(item.commit_sha)),
                current = record(data.current);
            check(
                revisions.length > 0 &&
                    generations.every(
                        (item, index) =>
                            index === 0 ||
                            item > (generations[index - 1] ?? item),
                    ) &&
                    new Set(commits).size === commits.length,
            );
            check(
                JSON.stringify(strings(data.cache_revisions_to_delete)) ===
                    JSON.stringify(commits),
            );
            const selected = revisions.filter(
                (item) => item.commit_sha === current.commit_sha,
            );
            check(
                selected.length === 1 &&
                    selected[0]?.publication_generation ===
                        current.publication_generation &&
                    BigInt(integer(data.unique_bytes_released_estimate)) ===
                        revisions.reduce(
                            (sum, item) =>
                                sum + BigInt(integer(item.logical_bytes)),
                            0n,
                        ),
            );
            return;
        }
        case "hfcache.api.command_models._selection":
        case "hfcache.api.maintenance_models._whole_repository":
            selector(value, false, true);
            return;
        case "hfcache.api.command_models._candidate_text": {
            const bytes = new TextEncoder().encode(text(value)).length;
            check(bytes > 0 && bytes <= 1048576);
            return;
        }
        case "hfcache.api.command_models.SyncSubmission.canonical":
            ordered(strings(record(value).selectors ?? []), true);
            return;
        case "hfcache.api.command_models.PlanSubmission.explicit_candidate":
        case "hfcache.api.command_models.ValidationSubmission.explicit_candidate": {
            const row = record(value);
            check(row.candidate !== null && row.managed !== null);
            if (row.managed !== undefined) {
                check(row.candidate === undefined);
                check(list(row.selectors ?? []).length === 0);
            }
            return;
        }
        case "hfcache.api.command_models.VerificationSubmission.scope": {
            const data = record(value),
                revision = data.revision ?? null,
                run = data.run_id ?? null;
            check(
                (data.mode === "revision") === (revision !== null) &&
                    !(run !== null && data.mode !== "new"),
            );
            if (revision !== null) selector(revision, true, false);
            return;
        }
        case "hfcache.api.command_models.CatalogRefreshSubmission.canonical": {
            const data = record(value),
                selectors = strings(data.selectors ?? []);
            selectors.forEach((item) => {
                selector(item, false, true);
            });
            ordered(selectors, true);
            check(
                (data.tags ?? true) === true ||
                    (data.technical ?? true) === true,
            );
            return;
        }
        case "hfcache.api.maintenance_models.PurgeSubmission.scope": {
            const data = record(value),
                selectors = strings(data.selectors ?? []);
            check(selectors.length > 0 !== (data.all_unmanaged ?? false));
            ordered(selectors, true);
            return;
        }
        case "hfcache.api.maintenance_models.QuarantineSubmission.canonical":
            ordered(strings(record(value).transaction_ids), true);
            return;
        case "hfcache.api.maintenance_models.RepairSubmission.scope":
            selector(record(value).revision, true, false);
            return;
        case "hfcache.api.maintenance_models.InitializationSubmission.confirmation":
            check(record(value).confirm === true);
            return;
        case "hfcache.api.maintenance_models._archive_root": {
            const root = text(value);
            check(
                root.startsWith("/") &&
                    new TextEncoder().encode(root).length <= 4096 &&
                    !root.includes("\\") &&
                    !root
                        .split("/")
                        .some((part) => part === "." || part === "..") &&
                    pythonIsPrintable(root),
            );
            return;
        }
        default:
            throw new WireError("semantic");
    }
}
