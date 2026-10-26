import { readFileSync } from "node:fs";
import { expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import type { SubmissionResult } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import {
    createAuthSession,
    decodeApiScope,
    sameApiScope,
    sameStableAuthority,
} from "../src/state/authority";
import {
    ACTION_ROUTES,
    createOperationRegistry,
    decodeRecoveryRecord,
    MAX_OPERATION_RECORDS,
    MAX_OPERATION_STORAGE_BYTES,
    OPERATION_STORAGE_KEY,
} from "../src/state/operation-registry";
import type {
    Action,
    OperationRegistry,
    OperationStorage,
    RecoveryRecord,
    SafeTerminalSummary,
} from "../src/state/operation-registry";
import { decodeAcceptance, decodeClientOperation } from "../src/wire/generated";
import type { ClientOperation } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { wireObject } from "../src/wire/runtime";

const archive = "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90";
const fingerprint = "c".repeat(64),
    id = "a".repeat(32),
    run = "d".repeat(32);
const at = "2026-10-26T12:00:00Z";
const scope = createApiScope({
    origin: "https://archive.invalid",
    publicPrefix: "",
    authorityEpoch: "e".repeat(32),
    subject: "administrator-v1",
    credentialClass: "rest-writer",
    instanceId: "e".repeat(32),
    archiveId: archive,
    configFingerprint: fingerprint,
});
const session = createAuthSession({ scope, authGeneration: 1 });

class MemoryStorage implements OperationStorage {
    value: string | null = null;
    failWrite = false;
    failRead = false;
    dropWrite = false;
    writes = 0;
    getItem(key: string): string | null {
        expect(key).toBe(OPERATION_STORAGE_KEY);
        if (this.failRead) throw new Error("private storage failure details");
        return this.value;
    }
    setItem(key: string, value: string): void {
        expect(key).toBe(OPERATION_STORAGE_KEY);
        this.writes++;
        if (this.failWrite) throw new Error("private quota failure details");
        if (!this.dropWrite) this.value = value;
    }
}

function registry(storage = new MemoryStorage()) {
    let next = 0;
    const value = createOperationRegistry({
        storage,
        keyFactory: () => "key-" + String(next + 1),
        recordIdFactory: () => (++next).toString(16).padStart(32, "0"),
        clock: () => 100,
    });
    return { value, storage };
}

function operation(changes: Partial<ClientOperation> = {}): ClientOperation {
    return decodeClientOperation(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                operation_id: id,
                principal: "rest-writer",
                route: "/api/v1/syncs",
                archive_id: archive,
                config_fingerprint: fingerprint,
                state: "queued",
                created_at: at,
                updated_at: at,
                completed_at: null,
                domain_run_id: null,
                transaction_ids: [],
                next_event_sequence: 1,
                result_recorded: false,
                ...changes,
            }),
        ),
    );
}

function accepted(
    record: RecoveryRecord,
    receipt = operation(),
): SubmissionResult {
    const status = "/api/v1/operations/" + receipt.operation_id;
    return {
        kind: "accepted",
        idempotencyKey:
            record.handles.kind === "basic-key"
                ? record.handles.key
                : "invalid",
        route: record.route ?? "invalid",
        acceptance: decodeAcceptance(
            parseWireJson(
                JSON.stringify({
                    schema_version: 1,
                    request_id: "f".repeat(32),
                    archive_id: receipt.archive_id,
                    config_fingerprint: receipt.config_fingerprint,
                    operation: receipt,
                    created: true,
                    links: {
                        status,
                        result: status + "/result",
                        events: status + "/events",
                    },
                }),
            ),
        ),
    };
}

function terminal(changes: Partial<ClientOperation> = {}): ClientOperation {
    return operation({
        state: "succeeded",
        completed_at: at,
        domain_run_id: run,
        result_recorded: true,
        ...changes,
    });
}
const summary: SafeTerminalSummary = {
    command: "sync",
    exitCode: 0,
    outcome: "success",
    runId: run,
    code: null,
};

function complete(
    value: OperationRegistry,
    record: RecoveryRecord,
    current = session,
): void {
    value.submitted(record.recordId, accepted(record), current);
    const auth = value.authorizeObservation(record.recordId, current);
    value.observed(auth, terminal());
    value.resolved(auth, summary, "known");
}

const actionRoutes: readonly (readonly [Action, string])[] = [
    ["sync", "/api/v1/syncs"],
    ["installedPlan", "/api/v1/plans"],
    ["candidatePlan", "/api/v1/plans"],
    ["managedPlan", "/api/v1/plans"],
    ["configurationApplication", "/api/v1/config/applications"],
    ["readOnlyDiagnostics", "/api/v1/diagnostics"],
    ["probeDiagnostics", "/api/v1/diagnostics"],
    ["newVerification", "/api/v1/verifications"],
    ["fullVerification", "/api/v1/verifications"],
    ["revisionVerification", "/api/v1/verifications"],
    ["prunePreview", "/api/v1/prune-plans"],
    ["pruneApply", "/api/v1/prunes"],
    ["purgePreview", "/api/v1/purge-plans"],
    ["purgeApply", "/api/v1/purges"],
    ["recoveryPreview", "/api/v1/recovery-plans"],
    ["recoveryApply", "/api/v1/recoveries"],
    ["quarantinePreview", "/api/v1/quarantine-plans"],
    ["quarantineApply", "/api/v1/quarantine-cleanups"],
    ["repair", "/api/v1/repairs"],
    ["catalogRefresh", "/api/v1/catalog/refreshes"],
];

test.each(actionRoutes)(
    "%s saves its original key and exact route before transmission",
    (action, route) => {
        const { value, storage } = registry();
        const record = value.prepare(action, session);
        expect(record.route).toBe(route);
        expect(record.handles).toEqual({
            kind: "basic-key",
            key: "key-1",
            operationId: null,
        });
        expect(storage.value).toContain('"key":"key-1"');
        expect(value.canSubmit(session)).toBe(false);
        expect(Object.keys(ACTION_ROUTES).sort()).toEqual(
            actionRoutes.map(([name]) => name).sort(),
        );
    },
);

test("stable immutable snapshots and subscribers cannot alter evidence", () => {
    const { value } = registry();
    const original = value.snapshot(),
        listener = vi.fn(),
        detach = value.subscribe(listener);
    value.subscribe(() => {
        throw new Error("detached view");
    });
    expect(value.snapshot()).toBe(original);
    const record = value.prepare("sync", session);
    expect(listener).toHaveBeenCalledOnce();
    expect(Object.isFrozen(value.snapshot().records)).toBe(true);
    expect(Object.isFrozen(record.handles)).toBe(true);
    expect(Object.isFrozen(record.originalAuthority)).toBe(true);
    expect(Object.isFrozen(record.observationTarget)).toBe(true);
    detach();
    value.unknown(record.recordId, "missing");
    expect(listener).toHaveBeenCalledOnce();
});

test.each(["throw", "readback"])(
    "pre-POST storage %s failure blocks the client",
    (kind) => {
        const { value, storage } = registry();
        storage.failWrite = kind === "throw";
        storage.dropWrite = kind === "readback";
        const transmit = vi.fn();
        expect(() => {
            value.prepare("sync", session);
            transmit();
        }).toThrow();
        expect(transmit).not.toHaveBeenCalled();
        expect(value.snapshot().records[0]?.handles).toMatchObject({
            key: "key-1",
        });
        expect(value.canSubmit(session)).toBe(false);
        expect(JSON.stringify(value.snapshot())).not.toContain("private");
    },
);

test("only actual current-session pre-fetch refusal removes its own prepared record", async () => {
    const { value, storage } = registry();
    const record = value.prepare("sync", session),
        fetcher = vi.fn<typeof fetch>();
    const api = createApiClient({ scope, fetcher });
    const abort = new AbortController();
    abort.abort();
    const result = await api.submitSync(
        {},
        { idempotencyKey: "key-1", signal: abort.signal },
    );
    expect(result).toEqual({ kind: "refused", reason: "schema" });
    expect(fetcher).not.toHaveBeenCalled();
    expect(value.submitted(record.recordId, result, session)).toBeNull();
    expect(value.snapshot().records).toEqual([]);
    expect(value.canSubmit(session)).toBe(true);
    expect(storage.value).toBe('{"schemaVersion":1,"records":[]}');
    expect(registry(storage).value.canSubmit(session)).toBe(true);
});

test("failed persistence of a no-transmission removal retains key in memory and blocks", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    storage.failWrite = true;
    expect(
        value.submitted(
            record.recordId,
            { kind: "refused", reason: "authority" },
            session,
        ),
    ).toEqual(record);
    expect(value.snapshot().records).toEqual([record]);
    expect(value.canSubmit(session)).toBe(false);
    expect(storage.value).toContain("key-1");
});

test.each(["network", "timeout", "aborted", "protocol"] as const)(
    "%s uncertainty preserves the original handle without another preparation",
    (reason) => {
        const { value } = registry(),
            record = value.prepare("sync", session);
        value.submitted(
            record.recordId,
            {
                kind: "uncertain",
                idempotencyKey: "key-1",
                route: "/api/v1/syncs",
                reason,
            },
            session,
        );
        expect(value.snapshot().records[0]?.state).toBe("uncertain");
        expect(() => value.prepare("installedPlan", session)).toThrow();
        expect(
            value.authorizeObservation(record.recordId, session).locator,
        ).toEqual({ kind: "key", key: "key-1" });
    },
);

test("post-transmission API problems preserve uncertainty and never persist arbitrary text", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    value.submitted(
        record.recordId,
        {
            kind: "api_problem",
            status: 503,
            problem: {
                request_id: "f".repeat(32),
                code: "HFAPI014",
                exit_code: 10,
                message: "private request secret",
            },
        },
        session,
    );
    expect(value.canSubmit(session)).toBe(false);
    expect(storage.value).not.toContain("private request secret");
});

test("post-admission storage loss retains learned ID and blocks fresh work", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    storage.failWrite = true;
    const learned = value.submitted(record.recordId, accepted(record), session);
    expect(learned?.handles.operationId).toBe(id);
    expect(value.snapshot().records[0]?.handles.operationId).toBe(id);
    expect(
        value.authorizeObservation(record.recordId, session).locator,
    ).toEqual({ kind: "id", operationId: id });
    expect(value.canSubmit(session)).toBe(false);
});

test("reload always authenticates original key before trusting even a saved operation ID", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const restored = registry(storage).value;
    const auth = restored.authorizeObservation(record.recordId, session);
    expect(auth.locator).toEqual({ kind: "key", key: "key-1" });
    restored.observed(auth, operation());
    expect(
        restored.authorizeObservation(record.recordId, session).locator,
    ).toEqual({ kind: "id", operationId: id });
});

test("forged saved key-to-ID association conflicts without overwriting original evidence", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const restored = registry(storage).value;
    const auth = restored.authorizeObservation(record.recordId, session);
    const conflict = restored.observed(
        auth,
        operation({ operation_id: "b".repeat(32) }),
    );
    expect(conflict.state).toBe("conflict");
    expect(conflict.handles.operationId).toBe(id);
    expect(conflict.receiptIdentity?.operation_id).toBe(id);
    expect(() =>
        restored.authorizeObservation(record.recordId, session),
    ).toThrow();
    expect(restored.canSubmit(session)).toBe(false);
});

test("restored terminal summaries stay blocked until key, receipt and exact result revalidate", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    complete(value, record);
    expect(value.canSubmit(session)).toBe(true);
    const restored = registry(storage).value;
    expect(restored.snapshot().records[0]?.state).toBe("unverified");
    expect(restored.canSubmit(session)).toBe(false);
    const auth = restored.authorizeObservation(record.recordId, session);
    restored.observed(auth, terminal());
    expect(restored.canSubmit(session)).toBe(false);
    restored.resolved(
        restored.authorizeObservation(record.recordId, session),
        summary,
        "known",
    );
    expect(restored.canSubmit(session)).toBe(true);
});

test("a typed terminal report with unknown effect certainty keeps the lane blocked", () => {
    const { value } = registry(),
        record = value.prepare("configurationApplication", session);
    const receipt = terminal({ route: "/api/v1/config/applications" });
    value.submitted(
        record.recordId,
        accepted(record, operation({ route: receipt.route })),
        session,
    );
    const auth = value.authorizeObservation(record.recordId, session);
    value.observed(auth, receipt);
    value.resolved(
        auth,
        { ...summary, command: "config apply" },
        "unknown-effects",
    );
    expect(value.snapshot().records[0]?.state).toBe("uncertain");
    expect(value.snapshot().records[0]?.terminal?.command).toBe("config apply");
    expect(value.canSubmit(session)).toBe(false);
});

test("interruption and missing history never fabricate a terminal result", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const auth = value.authorizeObservation(record.recordId, session);
    value.observed(auth, operation({ state: "interrupted", completed_at: at }));
    expect(() => value.resolved(auth, summary, "known")).toThrow();
    value.unknown(record.recordId, "missing");
    expect(value.snapshot().records[0]?.terminal).toBeNull();
    expect(value.snapshot().records[0]?.handles.operationId).toBe(id);
    expect(value.canSubmit(session)).toBe(false);
});

test.each([
    { origin: "https://other.invalid" },
    { publicPrefix: "/other" },
    { subject: "other-admin" },
    { credentialClass: "rest-reader" as const },
    { archiveId: "4f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90" },
])(
    "changed stable authority cannot silently rebind an original handle",
    (changes) => {
        const different = createAuthSession({
            scope: createApiScope({ ...scope, ...changes }),
            authGeneration: 2,
        });
        const { value } = registry(),
            record = value.prepare("sync", session);
        expect(sameStableAuthority(scope, different.scope)).toBe(false);
        expect(() =>
            value.authorizeObservation(record.recordId, different, {
                reconnect: true,
            }),
        ).toThrow();
        expect(value.snapshot().records[0]?.originalAuthority).toEqual({
            kind: "web",
            scope,
        });
    },
);

test("same-subject API restart explicitly reconnects through original key and preserves historical fingerprint", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const fresh = createAuthSession({
        scope: createApiScope({
            ...scope,
            instanceId: "b".repeat(32),
            authorityEpoch: "b".repeat(32),
            configFingerprint: "f".repeat(64),
        }),
        authGeneration: 2,
    });
    expect(sameStableAuthority(scope, fresh.scope)).toBe(true);
    expect(sameApiScope(scope, fresh.scope)).toBe(false);
    const restored = registry(storage).value;
    expect(() =>
        restored.authorizeObservation(record.recordId, fresh),
    ).toThrow();
    const auth = restored.authorizeObservation(record.recordId, fresh, {
        reconnect: true,
    });
    expect(auth.locator.kind).toBe("key");
    restored.observed(auth, terminal());
    expect(
        restored.authorizeObservation(record.recordId, fresh).locator,
    ).toEqual({
        kind: "id",
        operationId: id,
    });
    restored.resolved(auth, summary, "known");
    expect(
        restored.snapshot().records[0]?.receiptIdentity?.config_fingerprint,
    ).toBe(fingerprint);
    expect(restored.snapshot().records[0]?.observationTarget).toEqual(scope);
    expect(restored.canSubmit(fresh)).toBe(true);
});

test("local auth invalidation rejects stale callbacks and forces original key relookup", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const old = value.authorizeObservation(record.recordId, session);
    value.invalidateObservations();
    expect(() => value.observed(old, terminal())).toThrow();
    const fresh = createAuthSession({ scope, authGeneration: 2 });
    expect(
        value.authorizeObservation(record.recordId, fresh).locator.kind,
    ).toBe("key");
    expect(() => value.observed(old, terminal())).toThrow();
});

test("legacy key-only import is an unbound reference, never a Basic namespace lookup or permanent lane block", () => {
    const { value } = registry();
    const imported = value.importHandle(
        {
            kind: "legacy-key",
            key: "old-cockpit-key",
            credentialClass: "rest-writer",
        },
        session,
    );
    expect(imported.originalAuthority).toEqual({ kind: "unknown" });
    expect(imported.state).toBe("reference");
    expect(value.canSubmit(session)).toBe(true);
    expect(() =>
        value.authorizeObservation(imported.recordId, session),
    ).toThrow(/legacy bearer key/u);
});

test("manual ID import observes only its own record and never authenticates another saved key", () => {
    const { value } = registry(),
        own = value.prepare("sync", session);
    value.submitted(
        own.recordId,
        {
            kind: "uncertain",
            idempotencyKey: "key-1",
            route: "/api/v1/syncs",
            reason: "network",
        },
        session,
    );
    const imported = value.importHandle(
        {
            kind: "id",
            operationId: id,
            legacyKey: { value: "old-key", credentialClass: "rest-writer" },
        },
        session,
    );
    const auth = value.authorizeObservation(imported.recordId, session);
    expect(auth.locator).toEqual({ kind: "id", operationId: id });
    value.observed(auth, terminal());
    value.resolved(auth, summary, "known");
    expect(
        value.snapshot().records.find((item) => item.recordId === own.recordId)
            ?.handles.operationId,
    ).toBeNull();
    expect(value.canSubmit(session)).toBe(false);
    expect(value.authorizeObservation(own.recordId, session).locator.kind).toBe(
        "key",
    );
});

test("an actually observed imported pending ID remains blocked after reload until original result observation", () => {
    const { value, storage } = registry();
    const imported = value.importHandle(
        { kind: "id", operationId: id },
        session,
    );
    expect(value.canSubmit(session)).toBe(true);
    value.observed(
        value.authorizeObservation(imported.recordId, session),
        operation(),
    );
    expect(value.canSubmit(session)).toBe(false);
    const restored = registry(storage).value;
    expect(restored.canSubmit(session)).toBe(false);
    const auth = restored.authorizeObservation(imported.recordId, session);
    restored.observed(auth, terminal());
    restored.resolved(auth, summary, "known");
    expect(restored.canSubmit(session)).toBe(true);
});

test("manual Basic key import uses original namespace and cannot duplicate a retained key", () => {
    const { value } = registry();
    const imported = value.importHandle(
        { kind: "basic-key", key: "original-basic-key", originalScope: scope },
        session,
    );
    expect(value.canSubmit(session)).toBe(false);
    expect(
        value.authorizeObservation(imported.recordId, session).locator,
    ).toEqual({ kind: "key", key: "original-basic-key" });
    expect(() =>
        value.importHandle(
            {
                kind: "basic-key",
                key: "original-basic-key",
                originalScope: scope,
            },
            session,
        ),
    ).toThrow();
});

test("count capacity never evicts any unresolved imported reference", () => {
    const { value, storage } = registry();
    for (let index = 0; index < MAX_OPERATION_RECORDS; index++)
        value.importHandle(
            {
                kind: "legacy-key",
                key: "old-" + String(index),
                credentialClass: "rest-writer",
            },
            session,
        );
    const saved = storage.value;
    expect(value.snapshot().records).toHaveLength(32);
    expect(() =>
        value.importHandle({ kind: "id", operationId: id }, session),
    ).toThrow();
    expect(storage.value).toBe(saved);
    expect(value.snapshot().records).toHaveLength(32);
    expect(value.snapshot().storage).toBe("full");
});

test("byte capacity includes UTF-8 and learned-identity growth reserve without deleting unknown records", () => {
    const { value, storage } = registry();
    const large = createAuthSession({
        scope: createApiScope({
            ...scope,
            publicPrefix: "/" + "界".repeat(600),
        }),
        authGeneration: 1,
    });
    let acceptedCount = 0;
    for (let index = 0; index < 32; index++) {
        try {
            value.importHandle(
                {
                    kind: "legacy-key",
                    key: "old-" + String(index),
                    credentialClass: "rest-writer",
                },
                large,
            );
            acceptedCount++;
        } catch {
            break;
        }
    }
    expect(acceptedCount).toBeGreaterThan(0);
    expect(acceptedCount).toBeLessThan(32);
    expect(
        new TextEncoder().encode(storage.value ?? "").length,
    ).toBeLessThanOrEqual(MAX_OPERATION_STORAGE_BYTES);
    expect(value.snapshot().records).toHaveLength(acceptedCount);
    expect(value.snapshot().storage).toBe("full");
});

test("only current-session authenticated terminal summaries can make capacity room", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    complete(value, record);
    for (let index = 0; index < 31; index++)
        value.importHandle(
            {
                kind: "legacy-key",
                key: "old-" + String(index),
                credentialClass: "rest-writer",
            },
            session,
        );
    value.importHandle(
        { kind: "legacy-key", key: "last", credentialClass: "rest-writer" },
        session,
    );
    expect(value.snapshot().records).toHaveLength(32);
    expect(
        value
            .snapshot()
            .records.some((item) => item.recordId === record.recordId),
    ).toBe(false);
    expect(storage.value).not.toContain('"terminal":{');
});

test("external storage changes are preserved while learned handles remain available in memory", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    storage.value = "foreign storage evidence";
    value.submitted(record.recordId, accepted(record), session);
    expect(storage.value).toBe("foreign storage evidence");
    expect(value.snapshot().storage).toBe("corrupt");
    expect(value.snapshot().records[0]?.handles.operationId).toBe(id);
    expect(value.canSubmit(session)).toBe(false);
});

test.each([
    "{",
    '{"schemaVersion":1,"schemaVersion":1,"records":[]}',
    '{"schemaVersion":2,"records":[]}',
    '{"schemaVersion":1,"records":[],"body":"secret"}',
    "x".repeat(MAX_OPERATION_STORAGE_BYTES + 1),
])("corrupt or oversized storage remains byte-for-byte preserved", (saved) => {
    const storage = new MemoryStorage();
    storage.value = saved;
    const value = registry(storage).value;
    expect(value.snapshot().storage).toBe("corrupt");
    expect(value.snapshot().records).toEqual([]);
    expect(value.canSubmit(session)).toBe(false);
    expect(storage.value).toBe(saved);
    expect(storage.writes).toBe(0);
});

test("golden recovery metadata round-trips without persisting payloads or forged resolution flags", () => {
    const golden = readFileSync(
        new URL("./fixtures/operation-registry-v1.json", import.meta.url),
        "utf8",
    );
    const top = wireObject(parseWireJson(golden), ["schemaVersion", "records"]);
    if (!Array.isArray(top.records))
        throw new Error("golden record array missing");
    const raw: readonly unknown[] = top.records;
    const record = decodeRecoveryRecord(raw[0]);
    const { value, storage } = registry();
    expect(value.prepare("sync", session)).toEqual(record);
    expect(JSON.parse(storage.value ?? "null")).toEqual(JSON.parse(golden));
    for (const change of [
        { state: "not_submitted" },
        { candidate: "private TOML" },
        { terminal: { command: "secret", exitCode: 0 } },
    ]) {
        const forged = JSON.stringify({
            schemaVersion: 1,
            records: [{ ...record, ...change }],
        });
        const saved = new MemoryStorage();
        saved.value = forged;
        expect(registry(saved).value.snapshot().storage).toBe("corrupt");
        expect(saved.value).toBe(forged);
    }
});

test.each([
    { subject: 7 },
    { archiveId: false },
    { origin: 3 },
    { origin: "invalid-url" },
    { credentialClass: "mcp-reader" },
    { instanceId: 1 },
    { configFingerprint: [] },
])(
    "authority reconstruction rejects malformed restored scalar fields",
    (change) => {
        expect(() => decodeApiScope({ ...scope, ...change })).toThrow();
    },
);

test.each([-1, 0.5, Number.MAX_SAFE_INTEGER + 1])(
    "invalid local auth generation %s has no authority",
    (authGeneration) => {
        expect(() => createAuthSession({ scope, authGeneration })).toThrow();
    },
);

test.each([
    { schemaVersion: "1" },
    { schemaVersion: true },
    { recordId: "invalid" },
    { source: "future" },
    { action: "future" },
    { action: "managedPlan" },
    { route: "/api/v1/future" },
    { createdAt: -1 },
    { createdAt: Number.MAX_SAFE_INTEGER, updatedAt: Number.MAX_SAFE_INTEGER },
    { updatedAt: 99 },
    { handles: { kind: "future" } },
    { handles: { kind: "imported", operationId: null, legacyKey: null } },
    { originalAuthority: { kind: "future" } },
    { state: "terminal" },
    { state: "reference" },
    { handles: { kind: "basic-key", key: "key-1", operationId: id } },
])(
    "incoherent restored metadata is refused before overwriting its evidence",
    (change) => {
        const { value } = registry(),
            original = value.prepare("sync", session);
        const storage = new MemoryStorage();
        const saved = JSON.stringify({
            schemaVersion: 1,
            records: [{ ...original, ...change }],
        });
        storage.value = saved;
        expect(registry(storage).value.snapshot().storage).toBe("corrupt");
        expect(storage.value).toBe(saved);
        expect(storage.writes).toBe(0);
    },
);

test.each([
    { operation_id: "invalid" },
    { principal: "mcp-reader" },
    { route: "/api/v1/future" },
    { archive_id: "invalid" },
    { config_fingerprint: "invalid" },
    { created_at: "2026-02-30T12:00:00Z" },
])(
    "stored receipt identity is strict and cannot invent historical authority",
    (change) => {
        const { value } = registry(),
            original = value.prepare("sync", session);
        value.submitted(original.recordId, accepted(original), session);
        const saved = value.snapshot().records[0];
        if (saved === undefined || saved.receiptIdentity === null)
            throw new Error("test receipt missing");
        expect(() =>
            decodeRecoveryRecord({
                ...saved,
                receiptIdentity: { ...saved.receiptIdentity, ...change },
            }),
        ).toThrow();
    },
);

test.each([
    { command: "private arbitrary text" },
    { exitCode: 7 },
    { exitCode: 10 },
    { outcome: "failed" },
    { outcome: "future" },
    { code: "credential" },
    { runId: "invalid" },
])(
    "restored terminal summary cannot carry arbitrary text or contradictory results",
    (change) => {
        const { value } = registry(),
            original = value.prepare("sync", session);
        complete(value, original);
        const saved = value.snapshot().records[0];
        if (saved === undefined) throw new Error("test record missing");
        expect(() =>
            decodeRecoveryRecord({
                ...saved,
                terminal: { ...summary, ...change },
            }),
        ).toThrow();
    },
);

const cockpitAuthority = {
    kind: "cockpit" as const,
    host: "owned-host",
    profile: "b".repeat(64),
    endpoint: "unix:/run/hfcache/api.sock",
    credentialClass: "rest-writer" as const,
    archiveId: archive,
    authorityFingerprint: "f".repeat(64),
};
test.each([
    "unix:/run/hfcache/api.sock",
    "https://archive.invalid/api",
    "http://127.0.0.1:8000/api",
    "http://[::1]:8000/api",
])(
    "original Cockpit authority %s is retained separately from browser observation",
    (endpoint) => {
        const { value, storage } = registry();
        const record = value.importHandle(
            {
                kind: "id",
                operationId: id,
                source: "cockpit",
                originalAuthority: { ...cockpitAuthority, endpoint },
            },
            session,
        );
        expect(record.originalAuthority).toEqual({
            ...cockpitAuthority,
            endpoint,
        });
        expect(record.observationTarget).toEqual(scope);
        expect(registry(storage).value.snapshot().records).toEqual([record]);
    },
);
test.each([
    { endpoint: "invalid-url" },
    { endpoint: "unix:/run/../private" },
    { endpoint: "unix:/run//api.sock" },
    { endpoint: "http://remote.invalid/api" },
    { endpoint: "https://user:password@archive.invalid/api" },
    { endpoint: "https://archive.invalid/api?credential=secret" },
    { host: "unsafe host" },
    { profile: "unknown" },
    { archiveId: "invalid" },
])(
    "unsafe Cockpit authority never becomes persisted browser authority",
    (change) => {
        const { value, storage } = registry();
        expect(() =>
            value.importHandle(
                {
                    kind: "id",
                    operationId: id,
                    originalAuthority: { ...cockpitAuthority, ...change },
                },
                session,
            ),
        ).toThrow();
        expect(storage.value).toBeNull();
    },
);

test.each(["", "key with spaces", "hf_abcdefghijk", "x".repeat(129)])(
    "invalid or credential-looking generated keys cannot be transmitted",
    (key) => {
        const storage = new MemoryStorage();
        const value = createOperationRegistry({
            storage,
            keyFactory: () => key,
        });
        expect(() => value.prepare("sync", session)).toThrow();
        expect(storage.value).toBeNull();
    },
);

test("default factories use a real safe key, distinct local identity and monotonic integer time", () => {
    const storage = new MemoryStorage(),
        value = createOperationRegistry({ storage });
    const record = value.prepare("sync", session);
    expect(record.recordId).toMatch(/^[0-9a-f]{32}$/u);
    if (record.handles.kind !== "basic-key")
        throw new Error("test key missing");
    expect(record.handles.key).toMatch(/^[0-9a-f-]{36}$/u);
    expect(record.updatedAt).toBeGreaterThan(0);
    expect(record.recordId).not.toBe(record.handles.operationId);
});

test("storage absence/read denial remains unavailable and cannot prepare or import", () => {
    const storage = new MemoryStorage();
    storage.failRead = true;
    for (const source of [storage, null]) {
        const value = createOperationRegistry({ storage: source });
        expect(value.snapshot().storage).toBe("unavailable");
        expect(() => value.prepare("sync", session)).toThrow();
        expect(() =>
            value.importHandle({ kind: "id", operationId: id }, session),
        ).toThrow();
    }
});

test("unknown archive cannot prepare or import, and duplicate local identity cannot overwrite", () => {
    const { value } = registry();
    const unknown = createAuthSession({
        scope: createApiScope({ ...scope, archiveId: null }),
        authGeneration: 1,
    });
    expect(value.canSubmit(unknown)).toBe(false);
    expect(() =>
        value.importHandle({ kind: "id", operationId: id }, unknown),
    ).toThrow();
    const same = createOperationRegistry({
        storage: new MemoryStorage(),
        recordIdFactory: () => id,
    });
    same.importHandle({ kind: "id", operationId: id }, session);
    expect(() =>
        same.importHandle({ kind: "id", operationId: run }, session),
    ).toThrow();
});

test("duplicate restored records/keys are refused without deleting any raw storage", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    for (const duplicate of [record, { ...record, recordId: id }]) {
        const storage = new MemoryStorage();
        storage.value = JSON.stringify({
            schemaVersion: 1,
            records: [record, duplicate],
        });
        const saved = storage.value;
        expect(registry(storage).value.snapshot().storage).toBe("corrupt");
        expect(storage.value).toBe(saved);
    }
});

test.each(["key", "route", "principal", "archive", "fingerprint"])(
    "mismatched accepted %s preserves a conflicting original",
    (kind) => {
        const { value } = registry(),
            record = value.prepare("sync", session);
        const receipt = operation({
            ...(kind === "principal" ? { principal: "rest-reader" } : {}),
            ...(kind === "archive"
                ? { archive_id: "4f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90" }
                : {}),
            ...(kind === "fingerprint"
                ? { config_fingerprint: "f".repeat(64) }
                : {}),
        });
        const result = accepted(record, receipt);
        if (result.kind !== "accepted")
            throw new Error("test acceptance missing");
        value.submitted(
            record.recordId,
            {
                ...result,
                ...(kind === "key" ? { idempotencyKey: "another-key" } : {}),
                ...(kind === "route" ? { route: "/api/v1/plans" } : {}),
            },
            session,
        );
        expect(value.snapshot().records[0]?.state).toBe("conflict");
        expect(value.snapshot().records[0]?.handles.operationId).toBeNull();
    },
);

test("only issued observations and the actual original terminal result can resolve", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const auth = value.authorizeObservation(record.recordId, session);
    expect(() => value.observed({ ...auth }, operation())).toThrow();
    value.observed(auth, terminal());
    value.resolved(auth, { ...summary, runId: "b".repeat(32) }, "known");
    expect(value.snapshot().records[0]?.state).toBe("conflict");
    expect(value.unknown(record.recordId, "missing").state).toBe("conflict");
});

test("a contradictory reconfirmed terminal summary cannot overwrite stored original evidence", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    complete(value, record);
    const auth = value.authorizeObservation(record.recordId, session);
    value.resolved(
        auth,
        { ...summary, outcome: "success_with_warnings" },
        "known",
    );
    expect(value.snapshot().records[0]?.state).toBe("conflict");
    expect(value.snapshot().records[0]?.terminal).toEqual(summary);
});

test("legitimate bounded warning codes survive safe terminal summary and reload", () => {
    const { value, storage } = registry(),
        record = value.prepare("sync", session);
    value.submitted(record.recordId, accepted(record), session);
    const auth = value.authorizeObservation(record.recordId, session);
    value.observed(auth, terminal());
    value.resolved(
        auth,
        { ...summary, outcome: "success_with_warnings", code: "HFWRN011" },
        "known",
    );
    expect(value.canSubmit(session)).toBe(true);
    expect(registry(storage).value.snapshot().records[0]?.terminal?.code).toBe(
        "HFWRN011",
    );
});

test.each(["HFSYN001", "HFTXN001", "HFRET001", "HFDEP001"])(
    "existing diagnostic family %s remains representable without arbitrary messages",
    (code) => {
        const { value } = registry(),
            record = value.prepare("sync", session);
        complete(value, record);
        const saved = value.snapshot().records[0];
        if (saved === undefined)
            throw new Error("test terminal record missing");
        expect(
            decodeRecoveryRecord({ ...saved, terminal: { ...summary, code } })
                .terminal?.code,
        ).toBe(code);
    },
);

test("auth loss during a client refusal cannot erase a previously prepared unresolved handle", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    value.invalidateObservations();
    expect(
        value.submitted(
            record.recordId,
            { kind: "refused", reason: "schema" },
            session,
        )?.state,
    ).toBe("uncertain");
    expect(value.canSubmit(session)).toBe(false);
    expect(() =>
        value.submitted(
            record.recordId,
            { kind: "refused", reason: "schema" },
            session,
        ),
    ).toThrow();
});

test("restored byte-saturated valid metadata retains a learned ID when its post-observation update cannot fit", () => {
    const { value } = registry(),
        record = value.prepare("sync", session);
    const room =
        Math.floor(
            (MAX_OPERATION_STORAGE_BYTES -
                new TextEncoder().encode(
                    JSON.stringify({ schemaVersion: 1, records: [record] }),
                ).length) /
                2,
        ) - 2;
    const largeScope = createApiScope({
        ...scope,
        publicPrefix: "/" + "x".repeat(room),
    });
    const storage = new MemoryStorage();
    storage.value = JSON.stringify({
        schemaVersion: 1,
        records: [
            {
                ...record,
                originalAuthority: { kind: "web", scope: largeScope },
                observationTarget: largeScope,
            },
        ],
    });
    const restored = registry(storage).value,
        saved = storage.value;
    const current = createAuthSession({ scope: largeScope, authGeneration: 1 });
    restored.observed(
        restored.authorizeObservation(record.recordId, current),
        operation(),
    );
    expect(restored.snapshot().storage).toBe("full");
    expect(restored.snapshot().records[0]?.handles.operationId).toBe(id);
    expect(storage.value).toBe(saved);
});
