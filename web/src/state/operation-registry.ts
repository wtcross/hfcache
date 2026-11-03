/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Derived from hfcache recovery registry Git blob
 * 4f45ac71d44a96cb2b43b8ef8c3b4e0673e2223f, preserving its algorithm and license.
 * Browser adaptation uses typed REST evidence without process-bridge authority.
 */

import type { SubmissionResult } from "../api/client";
import type { ApiScope } from "../api/identity";
import { canonicalArchiveId, canonicalHex } from "../api/identity";
import {
    decodeClientOperation,
    decodePublicIntentDisposition,
    decodeConfigApplicationOutcome,
    decodeScheduleChangeOutcome,
    decodeObserverStopOutcome,
    operationResultDefinitions,
} from "../wire/generated";
import type {
    ClientOperation,
    PublicIntentDisposition,
    ConfigApplicationOutcome,
    ScheduleChangeOutcome,
    ObserverStopOutcome,
} from "../wire/generated";
import { numberSource, parseWireJson, WireError } from "../wire/json";
import { isRecord, wireObject } from "../wire/runtime";
import { timestampParts } from "../wire/semantics";
import {
    createAuthSession,
    decodeApiScope,
    receiptIdentity,
    sameApiScope,
    sameAuthSession,
    sameReceiptIdentity,
    sameStableAuthority,
    stableAuthorityIdentity,
} from "./authority";
import type {
    AuthSession,
    AuthorizedObservation,
    RecordId,
    SafeReceiptIdentity,
} from "./authority";

export const ACTION_ROUTES = Object.freeze({
    sync: "/api/v1/syncs",
    installedPlan: "/api/v1/plans",
    candidatePlan: "/api/v1/plans",
    managedPlan: "/api/v1/plans",
    configurationApplication: "/api/v1/config/applications",
    scheduleChange: "/api/v1/host/sync-schedule/changes",
    observerStop: "/api/v1/host/sync-observer/stops",
    readOnlyDiagnostics: "/api/v1/diagnostics",
    probeDiagnostics: "/api/v1/diagnostics",
    newVerification: "/api/v1/verifications",
    fullVerification: "/api/v1/verifications",
    revisionVerification: "/api/v1/verifications",
    prunePreview: "/api/v1/prune-plans",
    pruneApply: "/api/v1/prunes",
    purgePreview: "/api/v1/purge-plans",
    purgeApply: "/api/v1/purges",
    recoveryPreview: "/api/v1/recovery-plans",
    recoveryApply: "/api/v1/recoveries",
    quarantinePreview: "/api/v1/quarantine-plans",
    quarantineApply: "/api/v1/quarantine-cleanups",
    repair: "/api/v1/repairs",
    catalogRefresh: "/api/v1/catalog/refreshes",
} as const);

export function refusalExplanation(
    reason: PublicIntentDisposition["reason"],
): string {
    switch (reason) {
        case "permission_denied":
            return "The required job permission was denied.";
        case "storage_read_only":
            return "The required archive storage is read-only.";
        case "executor_unavailable":
            return "The job executor is unavailable.";
        case "admission_unavailable":
            return "Job admission is unavailable.";
        case "invalid_policy":
            return "The installed policy is invalid.";
        case null:
            return "The request was refused before admission.";
    }
}

export type Action = keyof typeof ACTION_ROUTES;
export type OperationRoute = (typeof ACTION_ROUTES)[Action];
export const OPERATION_STORAGE_KEY = "hfcache.web.operations.v1";
export const MAX_OPERATION_RECORDS = 32;
export const MAX_OPERATION_STORAGE_BYTES = 64 * 1024;
export const OPERATION_GROWTH_RESERVE_BYTES = 1024;

// Existing recovery records retain their original serialized discriminators.
export type OriginalAuthority =
    | { readonly kind: "web"; readonly scope: ApiScope }
    | {
          readonly kind: "cockpit";
          readonly host: string;
          readonly profile: string;
          readonly endpoint: string;
          readonly credentialClass: "rest-reader" | "rest-writer";
          readonly archiveId: string | null;
          readonly authorityFingerprint: string;
      }
    | { readonly kind: "unknown" };

export type RecoveryHandles =
    | {
          readonly kind: "basic-key";
          readonly key: string;
          readonly operationId: string | null;
      }
    | {
          readonly kind: "imported";
          readonly operationId: string | null;
          readonly legacyKey: {
              readonly value: string;
              readonly credentialClass: "rest-reader" | "rest-writer";
          } | null;
      };

export type RecoveryState =
    | "prepared"
    | "uncertain"
    | "accepted"
    | "observing"
    | "missing"
    | "unavailable"
    | "conflict"
    | "unverified"
    | "terminal"
    | "reference"
    | "not_admitted"
    | "retired_unknown";

export interface SafeTerminalSummary {
    readonly command: string;
    readonly exitCode: 0 | 10 | 20 | 30 | 40 | 50;
    readonly outcome: "success" | "success_with_warnings" | "failed";
    readonly runId: string;
    readonly code: string | null;
}

export interface RecoveryRecord {
    readonly schemaVersion: 2;
    readonly recordId: RecordId;
    readonly handles: RecoveryHandles;
    readonly originalAuthority: OriginalAuthority;
    readonly observationTarget: ApiScope;
    readonly source: "web" | "cockpit" | "manual";
    readonly action: Action | null;
    readonly route: OperationRoute | null;
    readonly receiptIdentity: SafeReceiptIdentity | null;
    readonly createdAt: number;
    readonly updatedAt: number;
    readonly state: RecoveryState;
    readonly terminal: SafeTerminalSummary | null;
    readonly disposition: PublicIntentDisposition | null;
}

export type ManualImport =
    | {
          readonly kind: "id";
          readonly operationId: string;
          readonly source?: "cockpit" | "manual";
          readonly originalAuthority?: OriginalAuthority;
          readonly legacyKey?: {
              readonly value: string;
              readonly credentialClass: "rest-reader" | "rest-writer";
          };
      }
    | {
          readonly kind: "legacy-key";
          readonly key: string;
          readonly credentialClass: "rest-reader" | "rest-writer";
          readonly originalAuthority?: OriginalAuthority;
      }
    | {
          readonly kind: "basic-key";
          readonly key: string;
          readonly operationId?: string;
          readonly originalScope: ApiScope;
      };

export type RegistryProblem =
    | "storage"
    | "capacity"
    | "blocked"
    | "scope"
    | "invalid"
    | "missing"
    | "conflict"
    | "namespace"
    | "observation";

export type UnknownReason =
    | "missing"
    | "unavailable"
    | "interrupted"
    | "scope"
    | "conflict"
    | "unknown-effects";

export interface RegistrySnapshot {
    readonly records: readonly RecoveryRecord[];
    readonly storage: "ready" | "unavailable" | "corrupt" | "full";
    readonly error: RegistryProblem | null;
}

export interface OperationStorage {
    getItem(key: string): string | null;
    setItem(key: string, value: string): void;
}

export interface RegistryOptions {
    readonly storage: OperationStorage | null;
    readonly keyFactory?: () => string;
    readonly recordIdFactory?: () => string;
    readonly clock?: () => number;
}

export interface OperationRegistry {
    snapshot(): RegistrySnapshot;
    exportMetadata(): string | null;
    subscribe(listener: () => void): () => void;
    prepare(action: Action, session: AuthSession): RecoveryRecord;
    importHandle(input: ManualImport, session: AuthSession): RecoveryRecord;
    submitted(
        id: RecordId,
        result: SubmissionResult,
        session: AuthSession,
    ): RecoveryRecord | null;
    authorizeObservation(
        id: RecordId,
        session: AuthSession,
        options?: {
            readonly reconnect?: boolean;
            readonly requireKey?: boolean;
        },
    ): AuthorizedObservation;
    isObservationCurrent(auth: AuthorizedObservation): boolean;
    observed(
        auth: AuthorizedObservation,
        receipt: ClientOperation,
    ): RecoveryRecord;
    resolved(
        auth: AuthorizedObservation,
        summary: SafeTerminalSummary,
        certainty: "known" | "unknown-effects",
    ): RecoveryRecord;
    configurationOutcome(
        auth: AuthorizedObservation,
        outcome: ConfigApplicationOutcome,
    ): void;
    hostActionOutcome(
        auth: AuthorizedObservation,
        outcome: ScheduleChangeOutcome | ObserverStopOutcome,
    ): void;
    unknown(id: RecordId, reason: UnknownReason): RecoveryRecord;
    disposition(
        auth: AuthorizedObservation,
        input: PublicIntentDisposition,
        causal?: boolean,
    ): RecoveryRecord;
    invalidateObservations(): void;
    canSubmit(session: AuthSession): boolean;
}

const MESSAGES: Readonly<Record<RegistryProblem, string>> = {
    storage:
        "Operation recovery storage is unavailable. Preserve original handles before another submission.",
    capacity:
        "Operation recovery storage is full. Unresolved original handles are preserved.",
    blocked:
        "An unresolved operation blocks another submission in this authority.",
    scope: "The original authority is unconfirmed or changed. Preserve its original handles.",
    invalid:
        "Operation recovery metadata is invalid. Preserve it for operator review.",
    missing:
        "The original recovery record is unavailable. No replacement was submitted.",
    conflict:
        "Observed operation identity conflicts with the original retained handles.",
    namespace:
        "A legacy bearer key cannot be looked up as this Basic subject. Supply the original operation ID.",
    observation:
        "Authenticate and observe the original operation before resolving this record.",
};

export class OperationRegistryError extends Error {
    readonly reason: RegistryProblem;
    constructor(reason: RegistryProblem) {
        super(MESSAGES[reason]);
        this.name = "OperationRegistryError";
        this.reason = reason;
    }
}

function invalid(): never {
    throw new OperationRegistryError("invalid");
}

function isAction(value: unknown): value is Action {
    return typeof value === "string" && Object.hasOwn(ACTION_ROUTES, value);
}

function isRoute(value: unknown): value is OperationRoute {
    return Object.values(ACTION_ROUTES).some((route) => route === value);
}

function integer(value: unknown): number {
    const source = numberSource(value);
    const checked =
        source === undefined
            ? value
            : /^\d+$/u.test(source)
              ? Number(source)
              : NaN;
    if (
        typeof checked !== "number" ||
        !Number.isSafeInteger(checked) ||
        checked < 0
    )
        invalid();
    return checked;
}

function timestamp(value: unknown): number {
    const checked = integer(value);
    if (checked > 8_640_000_000_000_000) invalid();
    return checked;
}

function text(value: unknown, maximum: number): string {
    if (
        typeof value !== "string" ||
        value.length === 0 ||
        value.length > maximum ||
        /[\u0000-\u001f\u007f-\u009f\ud800-\udfff]/u.test(value)
    )
        invalid();
    return value;
}

function originalKey(value: unknown): string {
    const checked = text(value, 128);
    if (
        /^[A-Za-z0-9._~+-]+$/u.exec(checked)?.[0] !== checked ||
        /hf_[A-Za-z0-9]{8,}/iu.test(checked)
    )
        invalid();
    return checked;
}

function operationId(value: unknown): string {
    const checked = text(value, 32);
    if (!canonicalHex(checked, 32)) invalid();
    return checked;
}

function credential(value: unknown): "rest-reader" | "rest-writer" {
    if (value !== "rest-reader" && value !== "rest-writer") invalid();
    return value;
}

function decodeOriginalAuthority(value: unknown): OriginalAuthority {
    if (!isRecord(value)) invalid();
    switch (value.kind) {
        case "unknown":
            wireObject(value, ["kind"]);
            return Object.freeze({ kind: "unknown" });
        case "web": {
            const row = wireObject(value, ["kind", "scope"]);
            return Object.freeze({
                kind: "web",
                scope: decodeApiScope(row.scope),
            });
        }
        case "cockpit": {
            const row = wireObject(value, [
                "kind",
                "host",
                "profile",
                "endpoint",
                "credentialClass",
                "archiveId",
                "authorityFingerprint",
            ]);
            const host = text(row.host, 255),
                profile = text(row.profile, 64),
                endpoint = text(row.endpoint, 2048),
                fingerprint = text(row.authorityFingerprint, 64);
            if (
                !/^[A-Za-z0-9][A-Za-z0-9._:@+-]*$/u.test(host) ||
                !canonicalHex(profile, 64) ||
                !canonicalHex(fingerprint, 64)
            )
                invalid();
            if (endpoint.startsWith("unix:")) {
                const path = endpoint.slice(5);
                if (
                    !/^\/[A-Za-z0-9._/-]+$/u.test(path) ||
                    path.includes("//") ||
                    path.endsWith("/") ||
                    path
                        .split("/")
                        .some((part) => part === "." || part === "..")
                )
                    invalid();
            } else {
                let parsed: URL;
                try {
                    parsed = new URL(endpoint);
                } catch {
                    return invalid();
                }
                if (
                    parsed.username !== "" ||
                    parsed.password !== "" ||
                    parsed.search !== "" ||
                    parsed.hash !== "" ||
                    /[?#\\\s]/u.test(endpoint) ||
                    !(
                        parsed.protocol === "https:" ||
                        (parsed.protocol === "http:" &&
                            ["localhost", "127.0.0.1", "[::1]"].includes(
                                parsed.hostname,
                            ))
                    )
                )
                    invalid();
            }
            const archiveId =
                row.archiveId === null ? null : text(row.archiveId, 36);
            if (archiveId !== null && !canonicalArchiveId(archiveId)) invalid();
            return Object.freeze({
                kind: "cockpit",
                host,
                profile,
                endpoint,
                credentialClass: credential(row.credentialClass),
                archiveId,
                authorityFingerprint: fingerprint,
            });
        }
        default:
            return invalid();
    }
}

function decodeLegacyKey(
    value: unknown,
): NonNullable<Extract<RecoveryHandles, { kind: "imported" }>["legacyKey"]> {
    const row = wireObject(value, ["value", "credentialClass"]);
    return Object.freeze({
        value: originalKey(row.value),
        credentialClass: credential(row.credentialClass),
    });
}

function decodeHandles(value: unknown): RecoveryHandles {
    if (!isRecord(value)) invalid();
    if (value.kind === "basic-key") {
        const row = wireObject(value, ["kind", "key", "operationId"]);
        return Object.freeze({
            kind: "basic-key",
            key: originalKey(row.key),
            operationId:
                row.operationId === null ? null : operationId(row.operationId),
        });
    }
    if (value.kind === "imported") {
        const row = wireObject(value, ["kind", "operationId", "legacyKey"]);
        if (row.operationId === null && row.legacyKey === null) invalid();
        return Object.freeze({
            kind: "imported",
            operationId:
                row.operationId === null ? null : operationId(row.operationId),
            legacyKey:
                row.legacyKey === null ? null : decodeLegacyKey(row.legacyKey),
        });
    }
    return invalid();
}

function decodeReceiptIdentity(value: unknown): SafeReceiptIdentity {
    const row = wireObject(value, [
        "operation_id",
        "principal",
        "route",
        "archive_id",
        "config_fingerprint",
        "created_at",
    ]);
    if (!isRoute(row.route)) invalid();
    const archive = text(row.archive_id, 36),
        fingerprint = text(row.config_fingerprint, 64),
        created = text(row.created_at, 32);
    if (!canonicalArchiveId(archive) || !canonicalHex(fingerprint, 64))
        invalid();
    timestampParts(created);
    return Object.freeze({
        operation_id: operationId(row.operation_id),
        principal: credential(row.principal),
        route: row.route,
        archive_id: archive,
        config_fingerprint: fingerprint,
        created_at: created,
    });
}

function decodeSummary(
    value: unknown,
    route: OperationRoute | null,
): SafeTerminalSummary {
    const row = wireObject(value, [
        "command",
        "exitCode",
        "outcome",
        "runId",
        "code",
    ]);
    const exitCode = integer(row.exitCode),
        command = text(row.command, 64);
    if (
        exitCode !== 0 &&
        exitCode !== 10 &&
        exitCode !== 20 &&
        exitCode !== 30 &&
        exitCode !== 40 &&
        exitCode !== 50
    )
        invalid();
    if (
        (exitCode === 0 &&
            row.outcome !== "success" &&
            row.outcome !== "success_with_warnings") ||
        (exitCode !== 0 && row.outcome !== "failed")
    )
        invalid();
    if (
        row.outcome !== "success" &&
        row.outcome !== "success_with_warnings" &&
        row.outcome !== "failed"
    )
        invalid();
    if (
        !operationResultDefinitions.some(
            (entry) =>
                entry.origin_path === route &&
                entry.commands.some((allowed) => allowed === command),
        )
    )
        invalid();
    const code = row.code === null ? null : text(row.code, 9);
    if (
        code !== null &&
        /^(?:HFAPI|HFARG|HFCFG|HFHUB|HFMNT|HFVER|HFSYN|HFTXN|HFRET|HFWRN|HFDEP)[0-9]{3}$/u.exec(
            code,
        )?.[0] !== code
    )
        invalid();
    return Object.freeze({
        command,
        exitCode,
        outcome: row.outcome,
        runId: operationId(row.runId),
        code,
    });
}

const STATES: readonly RecoveryState[] = [
    "prepared",
    "uncertain",
    "accepted",
    "observing",
    "missing",
    "unavailable",
    "conflict",
    "unverified",
    "terminal",
    "reference",
    "not_admitted",
    "retired_unknown",
];

function isState(value: unknown): value is RecoveryState {
    return STATES.some((state) => state === value);
}

function terminalInvalidDisposition(
    value: PublicIntentDisposition,
    archive: string | null,
    route: string | null,
): boolean {
    try {
        timestampParts(value.created_at);
    } catch {
        return true;
    }
    return (
        value.archive_id !== archive ||
        (value.state === "not_admitted"
            ? value.reason === null ||
              value.route === null ||
              (route !== null && value.route !== route) ||
              value.review_sha256 !== null
            : value.reason !== null ||
              value.route !== null ||
              value.review_sha256 === null)
    );
}

/** Reconstruct only safe metadata; unknown flags/fields are never migration hints. */
export function decodeRecoveryRecord(value: unknown): RecoveryRecord {
    const legacy = isRecord(value) && integer(value.schemaVersion) === 1;
    const row = wireObject(value, [
        ...(legacy ? [] : ["disposition"]),
        "schemaVersion",
        "recordId",
        "handles",
        "originalAuthority",
        "observationTarget",
        "source",
        "action",
        "route",
        "receiptIdentity",
        "createdAt",
        "updatedAt",
        "state",
        "terminal",
    ]);
    if (
        ![1, 2].includes(integer(row.schemaVersion)) ||
        !isState(row.state) ||
        (row.source !== "web" &&
            row.source !== "cockpit" &&
            row.source !== "manual")
    )
        invalid();
    const action =
        row.action === null
            ? null
            : isAction(row.action)
              ? row.action
              : invalid();
    const route =
        row.route === null ? null : isRoute(row.route) ? row.route : invalid();
    const handles = decodeHandles(row.handles),
        originalAuthority = decodeOriginalAuthority(row.originalAuthority),
        target = decodeApiScope(row.observationTarget),
        identity =
            row.receiptIdentity === null
                ? null
                : decodeReceiptIdentity(row.receiptIdentity);
    const created = timestamp(row.createdAt),
        updated = timestamp(row.updatedAt);
    if (
        updated < created ||
        (action !== null && ACTION_ROUTES[action] !== route) ||
        (handles.kind === "basic-key" && originalAuthority.kind !== "web") ||
        (row.source === "web" &&
            (handles.kind !== "basic-key" || action === null))
    )
        invalid();
    if (
        identity !== null &&
        (identity.operation_id !== handles.operationId ||
            identity.route !== route ||
            identity.archive_id !== target.archiveId)
    )
        invalid();
    const disposition =
        legacy || row.disposition === null
            ? null
            : decodePublicIntentDisposition(row.disposition);
    if (
        disposition !== null &&
        (handles.kind !== "basic-key" ||
            (disposition.state === "not_admitted" &&
                (identity !== null || handles.operationId !== null)) ||
            terminalInvalidDisposition(disposition, target.archiveId, route))
    )
        invalid();
    if (
        (row.state === "not_admitted" || row.state === "retired_unknown") &&
        disposition?.state !== row.state
    )
        invalid();
    const terminal =
        row.terminal === null ? null : decodeSummary(row.terminal, route);
    if (row.state === "terminal" && (terminal === null || identity === null))
        invalid();
    if (
        row.state === "prepared" &&
        (row.source !== "web" ||
            handles.operationId !== null ||
            identity !== null ||
            terminal !== null)
    )
        invalid();
    if (
        row.state === "reference" &&
        (handles.kind !== "imported" ||
            handles.operationId !== null ||
            identity !== null ||
            terminal !== null)
    )
        invalid();
    return Object.freeze({
        schemaVersion: 2,
        recordId: operationId(row.recordId),
        handles,
        originalAuthority,
        observationTarget: target,
        source: row.source,
        action,
        route,
        receiptIdentity: identity,
        createdAt: created,
        updatedAt: updated,
        state: row.state,
        terminal,
        disposition,
    });
}

function encoded(records: readonly RecoveryRecord[]): string {
    return JSON.stringify({ schemaVersion: 2, records });
}

function bytes(value: string): number {
    return new TextEncoder().encode(value).length;
}

interface ObservationProof {
    readonly session: AuthSession;
    readonly receipt: SafeReceiptIdentity;
    readonly state: ClientOperation["state"];
    readonly domainRunId: string | null;
    readonly keyVerified: boolean;
    readonly resolved: boolean;
    readonly configurationKnown?: boolean;
    readonly hostActionKnown?: boolean;
}

export function createOperationRegistry(
    options: RegistryOptions,
): OperationRegistry {
    const listeners = new Set<() => void>();
    const proofs = new Map<RecordId, ObservationProof>();
    const prepared = new Map<RecordId, AuthSession>();
    const causalRefusals = new Map<RecordId, AuthSession>();
    const dispositionProofs = new Map<RecordId, AuthSession>();
    let issued = new WeakSet<AuthorizedObservation>();
    let issuedDispositions = new WeakMap<
        AuthorizedObservation,
        string | null
    >();
    let activeSession: AuthSession | null = null;
    let snapshot: RegistrySnapshot = Object.freeze({
        records: Object.freeze([]),
        storage: "ready",
        error: null,
    });
    let writable = false,
        lastPersisted: string | null = null;
    let safeExport: string | null = null;
    const clock = options.clock ?? Date.now;
    const keyFactory = options.keyFactory ?? (() => crypto.randomUUID());
    const idFactory =
        options.recordIdFactory ??
        (() => crypto.randomUUID().replaceAll("-", ""));
    const publish = (
        records: readonly RecoveryRecord[],
        storage: RegistrySnapshot["storage"],
        error: RegistryProblem | null,
    ): void => {
        snapshot = Object.freeze({
            records: Object.freeze([...records]),
            storage,
            error,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* Views cannot change recovery evidence. */
            }
        }
    };
    try {
        if (options.storage === null)
            throw new OperationRegistryError("storage");
        const saved = options.storage.getItem(OPERATION_STORAGE_KEY);
        lastPersisted = saved;
        if (saved !== null) {
            if (bytes(saved) > MAX_OPERATION_STORAGE_BYTES) invalid();
            const top = wireObject(
                parseWireJson(saved, {
                    maxBytes: MAX_OPERATION_STORAGE_BYTES,
                    maxDepth: 12,
                    maxTokens: 8192,
                    maxKeys: 4096,
                    maxNumberCharacters: 32,
                }),
                ["schemaVersion", "records"],
            );
            if (
                ![1, 2].includes(integer(top.schemaVersion)) ||
                !Array.isArray(top.records) ||
                top.records.length > MAX_OPERATION_RECORDS
            )
                invalid();
            const rawRecords: readonly unknown[] = top.records;
            const records = rawRecords.map((value) => {
                if (
                    !isRecord(value) ||
                    integer(value.schemaVersion) !== integer(top.schemaVersion)
                )
                    invalid();
                return decodeRecoveryRecord(value);
            });
            if (
                new Set(records.map((record) => record.recordId)).size !==
                records.length
            )
                invalid();
            const originalKeys = records
                .filter((record) => record.handles.kind === "basic-key")
                .map((record) =>
                    JSON.stringify([
                        record.originalAuthority.kind === "web"
                            ? stableAuthorityIdentity(
                                  record.originalAuthority.scope,
                              )
                            : record.originalAuthority,
                        record.handles.kind === "basic-key"
                            ? record.handles.key
                            : null,
                    ]),
                );
            if (new Set(originalKeys).size !== originalKeys.length) invalid();
            safeExport = saved;
            if (integer(top.schemaVersion) === 1) {
                const migrated = encoded(records);
                if (
                    bytes(migrated) +
                        records.filter((record) => record.state !== "terminal")
                            .length *
                            OPERATION_GROWTH_RESERVE_BYTES >
                    MAX_OPERATION_STORAGE_BYTES
                )
                    throw new OperationRegistryError("storage");
                if (options.storage.getItem(OPERATION_STORAGE_KEY) !== saved)
                    throw new OperationRegistryError("storage");
                options.storage.setItem(OPERATION_STORAGE_KEY, migrated);
                let confirmed: string | null;
                try {
                    confirmed = options.storage.getItem(OPERATION_STORAGE_KEY);
                } catch {
                    // Never replace a concurrent tab's history or an unknown
                    // current document. Exact old bytes remain in safeExport.
                    let current: string | null = null;
                    try {
                        current = options.storage.getItem(
                            OPERATION_STORAGE_KEY,
                        );
                    } catch {
                        /* Current storage is unproved. */
                    }
                    if (current === migrated)
                        options.storage.setItem(OPERATION_STORAGE_KEY, saved);
                    throw new OperationRegistryError("storage");
                }
                if (confirmed !== migrated)
                    throw new OperationRegistryError("storage");
                lastPersisted = migrated;
                safeExport = migrated;
            }
            publish(
                records.map((record) =>
                    record.state === "prepared" ||
                    record.state === "terminal" ||
                    record.disposition !== null
                        ? Object.freeze({ ...record, state: "unverified" })
                        : record,
                ),
                "ready",
                null,
            );
        }
        writable = true;
    } catch (error) {
        const corrupt =
            error instanceof WireError ||
            (error instanceof OperationRegistryError &&
                error.reason === "invalid") ||
            error instanceof SyntaxError;
        publish(
            [],
            corrupt ? "corrupt" : "unavailable",
            corrupt ? "invalid" : "storage",
        );
    }
    const now = (): number => timestamp(clock());
    const find = (id: RecordId): RecoveryRecord => {
        const record = snapshot.records.find((item) => item.recordId === id);
        if (record === undefined) throw new OperationRegistryError("missing");
        return record;
    };
    const persist = (records: readonly RecoveryRecord[]): boolean => {
        if (!writable || options.storage === null) {
            publish(records, snapshot.storage, snapshot.error);
            return false;
        }
        const payload = encoded(records);
        if (bytes(payload) > MAX_OPERATION_STORAGE_BYTES) {
            publish(records, "full", "capacity");
            return false;
        }
        try {
            if (
                options.storage.getItem(OPERATION_STORAGE_KEY) !== lastPersisted
            ) {
                writable = false;
                publish(records, "corrupt", "invalid");
                return false;
            }
            options.storage.setItem(OPERATION_STORAGE_KEY, payload);
            if (options.storage.getItem(OPERATION_STORAGE_KEY) !== payload)
                throw new OperationRegistryError("storage");
            lastPersisted = payload;
            safeExport = payload;
            publish(records, "ready", null);
            return true;
        } catch {
            publish(records, "unavailable", "storage");
            return false;
        }
    };
    const update = (
        record: RecoveryRecord,
        patch: Partial<RecoveryRecord>,
    ): RecoveryRecord => {
        const changed = decodeRecoveryRecord({
            ...record,
            ...patch,
            updatedAt: Math.max(record.updatedAt, now()),
        });
        persist(
            snapshot.records.map((item) =>
                item.recordId === record.recordId ? changed : item,
            ),
        );
        return changed;
    };
    const proofFor = (
        id: RecordId,
        session: AuthSession,
    ): ObservationProof | undefined => {
        const proof = proofs.get(id);
        return proof !== undefined && sameAuthSession(proof.session, session)
            ? proof
            : undefined;
    };
    const blocks = (record: RecoveryRecord, session: AuthSession): boolean => {
        if (record.handles.kind === "basic-key") {
            if (
                record.originalAuthority.kind !== "web" ||
                !sameStableAuthority(
                    record.originalAuthority.scope,
                    session.scope,
                )
            )
                return false;
            const dispositionProof = dispositionProofs.get(record.recordId);
            if (
                dispositionProof !== undefined &&
                sameAuthSession(dispositionProof, session) &&
                ![
                    "/api/v1/config/applications",
                    "/api/v1/host/sync-schedule/changes",
                    "/api/v1/host/sync-observer/stops",
                ].includes(record.route ?? "")
            )
                return false;
            return (
                proofFor(record.recordId, session)?.configurationKnown !==
                    true &&
                proofFor(record.recordId, session)?.hostActionKnown !== true &&
                (record.state !== "terminal" ||
                    proofFor(record.recordId, session)?.resolved !== true)
            );
        }
        // An unbound foreign key is only a reference. Once an ID has actually
        // been observed, restored summaries cannot release its lane by themselves.
        return (
            record.handles.operationId !== null &&
            record.receiptIdentity !== null &&
            sameStableAuthority(record.observationTarget, session.scope) &&
            (record.state !== "terminal" ||
                proofFor(record.recordId, session)?.resolved !== true)
        );
    };
    const activate = (session: AuthSession): void => {
        if (
            activeSession !== null &&
            session.authGeneration < activeSession.authGeneration
        )
            throw new OperationRegistryError("scope");
        if (
            activeSession === null ||
            !sameAuthSession(activeSession, session)
        ) {
            proofs.clear();
            dispositionProofs.clear();
            causalRefusals.clear();
            issued = new WeakSet();
            issuedDispositions = new WeakMap();
            activeSession = session;
        }
    };
    const canSubmit = (raw: AuthSession): boolean => {
        const session = createAuthSession(raw);
        return (
            session.scope.archiveId !== null &&
            snapshot.storage === "ready" &&
            !snapshot.records.some((record) => blocks(record, session))
        );
    };
    const add = (record: RecoveryRecord): RecoveryRecord => {
        let records = [...snapshot.records, record];
        const size = (): number =>
            bytes(encoded(records)) +
            records.filter((item) => item.state !== "terminal").length *
                OPERATION_GROWTH_RESERVE_BYTES;
        while (
            records.length > MAX_OPERATION_RECORDS ||
            size() > MAX_OPERATION_STORAGE_BYTES
        ) {
            const oldest = records
                .filter(
                    (item) =>
                        item.state === "terminal" &&
                        proofs.get(item.recordId)?.resolved === true,
                )
                .sort((left, right) => left.updatedAt - right.updatedAt)[0];
            if (oldest === undefined) {
                publish(snapshot.records, "full", "capacity");
                throw new OperationRegistryError("capacity");
            }
            records = records.filter(
                (item) => item.recordId !== oldest.recordId,
            );
        }
        if (!persist(records)) throw new OperationRegistryError("storage");
        return record;
    };
    const newId = (): string => {
        const id = operationId(idFactory());
        if (snapshot.records.some((record) => record.recordId === id))
            invalid();
        return id;
    };
    const conflict = (record: RecoveryRecord): RecoveryRecord => {
        proofs.delete(record.recordId);
        dispositionProofs.delete(record.recordId);
        causalRefusals.delete(record.recordId);
        return update(record, { state: "conflict" });
    };
    const authorizeObservation = (
        id: RecordId,
        raw: AuthSession,
        settings: {
            readonly reconnect?: boolean;
            readonly requireKey?: boolean;
        } = {},
    ): AuthorizedObservation => {
        const session = createAuthSession(raw),
            record = find(id);
        activate(session);
        if (record.state === "conflict")
            throw new OperationRegistryError("conflict");
        if (
            !sameStableAuthority(record.observationTarget, session.scope) ||
            (record.handles.kind === "basic-key" &&
                (record.originalAuthority.kind !== "web" ||
                    !sameStableAuthority(
                        record.originalAuthority.scope,
                        session.scope,
                    )))
        )
            throw new OperationRegistryError("scope");
        const proof = proofFor(id, session);
        if (
            !sameApiScope(record.observationTarget, session.scope) &&
            settings.reconnect !== true &&
            proof === undefined
        )
            throw new OperationRegistryError("scope");
        let locator: AuthorizedObservation["locator"];
        if (record.handles.kind === "basic-key") {
            locator =
                settings.requireKey !== true &&
                proof?.keyVerified === true &&
                record.handles.operationId !== null
                    ? { kind: "id", operationId: record.handles.operationId }
                    : { kind: "key", key: record.handles.key };
        } else {
            if (record.handles.operationId === null)
                throw new OperationRegistryError("namespace");
            locator = { kind: "id", operationId: record.handles.operationId };
        }
        const auth: AuthorizedObservation = Object.freeze({
            recordId: id,
            target: session.scope,
            authGeneration: session.authGeneration,
            locator: Object.freeze(locator),
            expectedSafeReceiptIdentity: record.receiptIdentity,
        });
        issued.add(auth);
        issuedDispositions.set(
            auth,
            record.disposition?.disposition_id ?? null,
        );
        return auth;
    };
    const authorized = (
        auth: AuthorizedObservation,
    ): { record: RecoveryRecord; session: AuthSession } => {
        if (
            !issued.has(auth) ||
            activeSession === null ||
            !sameAuthSession(activeSession, {
                scope: auth.target,
                authGeneration: auth.authGeneration,
            })
        )
            throw new OperationRegistryError("observation");
        const record = find(auth.recordId),
            session = createAuthSession({
                scope: auth.target,
                authGeneration: auth.authGeneration,
            });
        if (
            issuedDispositions.get(auth) !==
            (record.disposition?.disposition_id ?? null)
        )
            throw new OperationRegistryError("observation");
        if (
            record.state === "conflict" ||
            !sameStableAuthority(record.observationTarget, session.scope)
        )
            throw new OperationRegistryError("scope");
        return { record, session };
    };
    const observed = (
        auth: AuthorizedObservation,
        input: ClientOperation,
    ): RecoveryRecord => {
        const { record, session } = authorized(auth);
        if (record.disposition !== null) return conflict(record);
        const receipt = decodeClientOperation(
                parseWireJson(JSON.stringify(input)),
            ),
            identity = receiptIdentity(receipt);
        if (
            !isRoute(receipt.route) ||
            receipt.archive_id !== session.scope.archiveId ||
            (record.handles.operationId !== null &&
                record.handles.operationId !== receipt.operation_id) ||
            (record.route !== null && record.route !== receipt.route) ||
            (record.receiptIdentity !== null &&
                !sameReceiptIdentity(record.receiptIdentity, identity)) ||
            (record.handles.kind === "basic-key" &&
                auth.locator.kind === "key" &&
                (auth.locator.key !== record.handles.key ||
                    receipt.principal !== session.scope.credentialClass))
        )
            return conflict(record);
        if (
            auth.locator.kind === "id" &&
            auth.locator.operationId !== receipt.operation_id
        )
            return conflict(record);
        const previous = proofFor(record.recordId, session);
        if (
            record.handles.kind === "basic-key" &&
            auth.locator.kind !== "key" &&
            previous?.keyVerified !== true
        )
            throw new OperationRegistryError("observation");
        const resolved =
            record.state === "terminal" && previous?.resolved === true;
        proofs.set(record.recordId, {
            session,
            receipt: identity,
            state: receipt.state,
            domainRunId: receipt.domain_run_id,
            keyVerified: record.handles.kind === "basic-key",
            resolved,
            configurationKnown: previous?.configurationKnown === true,
            hostActionKnown: previous?.hostActionKnown === true,
        });
        return update(record, {
            handles: Object.freeze({
                ...record.handles,
                operationId: receipt.operation_id,
            }),
            route: receipt.route,
            receiptIdentity: identity,
            state: resolved ? "terminal" : "observing",
        });
    };
    return {
        snapshot: () => snapshot,
        exportMetadata: () => safeExport,
        subscribe: (listener) => {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        canSubmit,
        prepare: (action, raw) => {
            const session = createAuthSession(raw);
            activate(session);
            if (!isAction(action)) invalid();
            if (!canSubmit(session))
                throw new OperationRegistryError(
                    snapshot.storage === "ready" ? "blocked" : "storage",
                );
            const key = originalKey(keyFactory());
            if (
                snapshot.records.some(
                    (record) =>
                        record.handles.kind === "basic-key" &&
                        record.handles.key === key,
                )
            )
                invalid();
            const at = now();
            const record = decodeRecoveryRecord({
                schemaVersion: 2,
                recordId: newId(),
                handles: { kind: "basic-key", key, operationId: null },
                originalAuthority: { kind: "web", scope: session.scope },
                observationTarget: session.scope,
                source: "web",
                action,
                route: ACTION_ROUTES[action],
                receiptIdentity: null,
                createdAt: at,
                updatedAt: at,
                state: "prepared",
                terminal: null,
                disposition: null,
            });
            add(record);
            prepared.set(record.recordId, session);
            return record;
        },
        importHandle: (input, raw) => {
            const session = createAuthSession(raw);
            activate(session);
            if (session.scope.archiveId === null)
                throw new OperationRegistryError("scope");
            if (snapshot.storage !== "ready")
                throw new OperationRegistryError("storage");
            let handles: RecoveryHandles,
                authority: OriginalAuthority,
                source: RecoveryRecord["source"];
            switch (input.kind) {
                case "basic-key":
                    handles = decodeHandles({
                        kind: "basic-key",
                        key: input.key,
                        operationId: input.operationId ?? null,
                    });
                    authority = decodeOriginalAuthority({
                        kind: "web",
                        scope: input.originalScope,
                    });
                    source = "manual";
                    break;
                case "id":
                    handles = decodeHandles({
                        kind: "imported",
                        operationId: input.operationId,
                        legacyKey: input.legacyKey ?? null,
                    });
                    authority = decodeOriginalAuthority(
                        input.originalAuthority ?? { kind: "unknown" },
                    );
                    source = input.source ?? "manual";
                    break;
                case "legacy-key":
                    handles = decodeHandles({
                        kind: "imported",
                        operationId: null,
                        legacyKey: {
                            value: input.key,
                            credentialClass: input.credentialClass,
                        },
                    });
                    authority = decodeOriginalAuthority(
                        input.originalAuthority ?? { kind: "unknown" },
                    );
                    source = "cockpit";
                    break;
            }
            if (
                handles.kind === "basic-key" &&
                snapshot.records.some(
                    (record) =>
                        record.handles.kind === "basic-key" &&
                        record.handles.key === handles.key &&
                        record.originalAuthority.kind === "web" &&
                        authority.kind === "web" &&
                        sameStableAuthority(
                            record.originalAuthority.scope,
                            authority.scope,
                        ),
                )
            )
                invalid();
            const at = now();
            return add(
                decodeRecoveryRecord({
                    schemaVersion: 2,
                    recordId: newId(),
                    handles,
                    originalAuthority: authority,
                    observationTarget: session.scope,
                    source,
                    action: null,
                    route: null,
                    receiptIdentity: null,
                    createdAt: at,
                    updatedAt: at,
                    state:
                        handles.operationId === null &&
                        handles.kind === "imported"
                            ? "reference"
                            : "unverified",
                    terminal: null,
                    disposition: null,
                }),
            );
        },
        submitted: (id, result, raw) => {
            const record = find(id),
                session = createAuthSession(raw),
                preparation = prepared.get(id);
            if (
                record.source !== "web" ||
                record.handles.kind !== "basic-key" ||
                preparation === undefined ||
                !sameAuthSession(preparation, session)
            )
                throw new OperationRegistryError("observation");
            prepared.delete(id);
            if (result.kind === "refused") {
                if (record.state !== "prepared")
                    throw new OperationRegistryError("observation");
                if (
                    activeSession === null ||
                    !sameAuthSession(activeSession, session)
                )
                    return update(record, { state: "uncertain" });
                if (
                    persist(
                        snapshot.records.filter((item) => item.recordId !== id),
                    )
                )
                    return null;
                // Failed removal must retain the original key in RAM even if
                // setItem actually wrote before its readback failed.
                publish(
                    snapshot.records.some((item) => item.recordId === id)
                        ? snapshot.records
                        : [...snapshot.records, record],
                    snapshot.storage,
                    snapshot.error,
                );
                return record;
            }
            if (result.kind !== "accepted") {
                if (
                    result.kind === "api_problem" &&
                    result.intentClosed === true &&
                    activeSession !== null &&
                    sameAuthSession(activeSession, session)
                )
                    causalRefusals.set(id, session);
                return update(record, { state: "uncertain" });
            }
            if (
                result.idempotencyKey !== record.handles.key ||
                result.route !== record.route
            )
                return conflict(record);
            const receipt = decodeClientOperation(
                parseWireJson(JSON.stringify(result.acceptance.operation)),
            );
            if (
                receipt.route !== record.route ||
                receipt.archive_id !== session.scope.archiveId ||
                receipt.principal !== session.scope.credentialClass ||
                (session.scope.configFingerprint !== null &&
                    receipt.config_fingerprint !==
                        session.scope.configFingerprint)
            )
                return conflict(record);
            const identity = receiptIdentity(receipt);
            if (
                activeSession !== null &&
                sameAuthSession(activeSession, session)
            )
                proofs.set(id, {
                    session,
                    receipt: identity,
                    state: receipt.state,
                    domainRunId: receipt.domain_run_id,
                    keyVerified: true,
                    resolved: false,
                });
            return update(record, {
                handles: {
                    ...record.handles,
                    operationId: receipt.operation_id,
                },
                receiptIdentity: identity,
                state: "accepted",
            });
        },
        authorizeObservation,
        isObservationCurrent: (auth) => {
            try {
                authorized(auth);
                return true;
            } catch {
                return false;
            }
        },
        disposition: (auth, input, causal = false) => {
            const { record, session } = authorized(auth);
            const disposition = decodePublicIntentDisposition(
                parseWireJson(JSON.stringify(input)),
            );
            if (
                record.handles.kind !== "basic-key" ||
                auth.locator.kind !== "key" ||
                auth.locator.key !== record.handles.key ||
                (disposition.state === "not_admitted" &&
                    (record.receiptIdentity !== null ||
                        record.handles.operationId !== null ||
                        record.terminal !== null)) ||
                terminalInvalidDisposition(
                    disposition,
                    session.scope.archiveId,
                    record.route,
                )
            )
                return conflict(record);
            if (
                disposition.state === "not_admitted" &&
                !(
                    causal &&
                    record.source === "web" &&
                    causalRefusals.get(record.recordId) !== undefined &&
                    sameAuthSession(
                        causalRefusals.get(record.recordId) ?? session,
                        session,
                    )
                ) &&
                record.disposition?.disposition_id !==
                    disposition.disposition_id
            )
                return update(record, { state: "uncertain" });
            if (
                record.disposition !== null &&
                JSON.stringify(record.disposition) !==
                    JSON.stringify(disposition)
            ) {
                // A refusal may acquire a reviewed historical retirement once.
                if (
                    record.disposition.state !== "not_admitted" ||
                    disposition.state !== "retired_unknown"
                )
                    return conflict(record);
            }
            const saved = update(record, {
                disposition,
                state: disposition.state,
            });
            proofs.delete(record.recordId);
            causalRefusals.delete(record.recordId);
            if (
                snapshot.storage === "ready" &&
                activeSession !== null &&
                sameAuthSession(activeSession, session)
            )
                dispositionProofs.set(record.recordId, session);
            publish(snapshot.records, snapshot.storage, snapshot.error);
            return saved;
        },
        observed,
        resolved: (auth, input, certainty) => {
            const { record, session } = authorized(auth),
                proof = proofFor(record.recordId, session);
            if (
                proof === undefined ||
                (proof.state !== "succeeded" && proof.state !== "failed")
            )
                throw new OperationRegistryError("observation");
            const summary = decodeSummary(input, record.route);
            if (
                summary.runId !== proof.domainRunId ||
                (summary.exitCode === 0) !== (proof.state === "succeeded")
            )
                return conflict(record);
            if (
                record.terminal !== null &&
                JSON.stringify(record.terminal) !== JSON.stringify(summary)
            )
                return conflict(record);
            const known = certainty === "known";
            proofs.set(record.recordId, { ...proof, resolved: known });
            return update(record, {
                state: known ? "terminal" : "uncertain",
                terminal: summary,
            });
        },
        configurationOutcome: (auth, input) => {
            const { record, session } = authorized(auth);
            const outcome = decodeConfigApplicationOutcome(
                parseWireJson(JSON.stringify(input)),
            );
            const proof = proofFor(record.recordId, session);
            if (
                record.handles.kind !== "basic-key" ||
                record.route !== "/api/v1/config/applications" ||
                proof?.keyVerified !== true ||
                outcome.operation_id !== proof.receipt.operation_id ||
                outcome.archive_id !== session.scope.archiveId
            )
                throw new OperationRegistryError("observation");
            // ADR154: fresh host evidence may settle effects of an interrupted
            // API receipt. Keep that receipt and all stored handles unchanged.
            const known =
                ["succeeded", "failed", "interrupted"].includes(proof.state) &&
                !outcome.pending &&
                (outcome.state === "confirmed" ||
                    outcome.state === "unchanged");
            proofs.set(record.recordId, {
                ...proof,
                configurationKnown: known,
            });
            publish(snapshot.records, snapshot.storage, snapshot.error);
        },
        hostActionOutcome: (auth, input) => {
            const { record, session } = authorized(auth);
            const schedule =
                record.route === "/api/v1/host/sync-schedule/changes";
            if (
                !schedule &&
                record.route !== "/api/v1/host/sync-observer/stops"
            )
                throw new OperationRegistryError("observation");
            const outcome = schedule
                ? decodeScheduleChangeOutcome(
                      parseWireJson(JSON.stringify(input)),
                  )
                : decodeObserverStopOutcome(
                      parseWireJson(JSON.stringify(input)),
                  );
            const proof = proofFor(record.recordId, session);
            if (
                record.handles.kind !== "basic-key" ||
                proof?.keyVerified !== true ||
                outcome.operation_id !== proof.receipt.operation_id ||
                outcome.archive_id !== session.scope.archiveId
            )
                throw new OperationRegistryError("observation");
            const known =
                ["succeeded", "failed", "interrupted"].includes(proof.state) &&
                !outcome.pending &&
                (outcome.state === "confirmed" ||
                    outcome.state === "unchanged");
            proofs.set(record.recordId, { ...proof, hostActionKnown: known });
            publish(snapshot.records, snapshot.storage, snapshot.error);
        },
        unknown: (id, reason) => {
            const record = find(id);
            dispositionProofs.delete(id);
            if (record.state === "conflict") return record;
            if (reason === "conflict") return conflict(record);
            const state =
                reason === "missing"
                    ? "missing"
                    : reason === "unavailable" || reason === "scope"
                      ? "unavailable"
                      : "uncertain";
            const proof = proofs.get(id);
            if (proof !== undefined)
                proofs.set(id, { ...proof, resolved: false });
            return update(record, { state });
        },
        invalidateObservations: () => {
            proofs.clear();
            dispositionProofs.clear();
            causalRefusals.clear();
            issued = new WeakSet();
            issuedDispositions = new WeakMap();
            activeSession = null;
            const records = snapshot.records.map((record) =>
                record.state === "terminal" || record.disposition !== null
                    ? Object.freeze({ ...record, state: "unverified" as const })
                    : record,
            );
            publish(records, snapshot.storage, snapshot.error);
        },
    };
}
