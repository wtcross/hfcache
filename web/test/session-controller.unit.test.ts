import { readFileSync } from "node:fs";
import { afterEach, expect, test, vi } from "vitest";
import { ApiClient } from "../src/api/client";
import { bootstrapScope } from "../src/bootstrap";
import {
    createSessionController,
    resultCertainty,
} from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import type { SubmissionIntent } from "../src/state/session-controller";
import { OPERATION_STORAGE_KEY } from "../src/state/operation-registry";
import type { OperationStorage } from "../src/state/operation-registry";
import {
    decodeClientOperation,
    decodeRequestManagedPlanRequest,
} from "../src/wire/generated";
import type { ClientOperation, UiBootstrap } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { isRecord } from "../src/wire/runtime";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
} from "./read-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const fingerprint = "2".repeat(64),
    operationId = "a".repeat(32),
    runId = "3".repeat(32);
const at = "2026-10-20T12:00:00.000001Z";
const bootstrap: UiBootstrap = {
    ...uiBootstrapFixture(),
    configured_archive_id: ARCHIVE_ID,
};
const raw: unknown = JSON.parse(
    readFileSync(
        new URL("../../tests/fixtures/web_wire/config.json", import.meta.url),
        "utf8",
    ),
);
if (!isRecord(raw))
    throw new Error("Independent configuration wire fixture missing");
const fixtures = raw;
const managedRequest = decodeRequestManagedPlanRequest(
    parseWireJson(JSON.stringify(fixtures.request)),
);
const controllers = new Set<SessionController>();
afterEach(() => {
    for (const controller of controllers) controller.dispose();
    controllers.clear();
    vi.unstubAllGlobals();
});

class MemoryStorage implements OperationStorage {
    saved: string | null = null;
    fail = false;
    getItem(key: string): string | null {
        expect(key).toBe(OPERATION_STORAGE_KEY);
        return this.saved;
    }
    setItem(key: string, value: string): void {
        expect(key).toBe(OPERATION_STORAGE_KEY);
        if (this.fail) throw new Error("Simulated private storage quota");
        this.saved = value;
    }
}

function controller(
    fetcher: typeof fetch,
    storage = new MemoryStorage(),
    reconnect = () => Promise.resolve(bootstrap),
) {
    const value = createSessionController({
        bootstrap,
        fetcher,
        storage,
        reconnect,
    });
    controllers.add(value);
    return { value, storage };
}
function receipt(changes: Partial<ClientOperation> = {}): ClientOperation {
    return decodeClientOperation(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                operation_id: operationId,
                principal: "rest-writer",
                route: "/api/v1/plans",
                archive_id: ARCHIVE_ID,
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
function acceptance(row = receipt()): Response {
    const status = "/api/v1/operations/" + row.operation_id;
    return new Response(
        JSON.stringify({
            schema_version: 1,
            request_id: "f".repeat(32),
            archive_id: ARCHIVE_ID,
            config_fingerprint: fingerprint,
            created: true,
            operation: row,
            links: {
                status,
                result: status + "/result",
                events: status + "/events",
            },
        }),
        {
            status: 202,
            headers: { "Content-Type": "application/json", Location: status },
        },
    );
}
function operationRead(row: ClientOperation): Response {
    return jsonResponse({
        ...readWire("operations show", { operation: row }),
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
    });
}
function planResult(warning = false): Response {
    const result = readWire("plan", fixtures.assessment);
    return jsonResponse({
        ...result,
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
        envelope: {
            ...result.envelope,
            outcome: warning ? "success_with_warnings" : "success",
            warnings: warning
                ? [
                      {
                          code: "HFWRN011",
                          message: "Incomplete supplemental metadata",
                          context: {},
                          repository: null,
                      },
                  ]
                : [],
        },
    });
}
function deferred<T>() {
    let resolve: ((value: T) => void) | undefined;
    const promise = new Promise<T>((done) => {
        resolve = done;
    });
    return {
        promise,
        resolve: (value: T) => {
            if (resolve === undefined) throw new Error("Missing resolver");
            resolve(value);
        },
    };
}
function requestUrl(value: RequestInfo | URL | undefined): string {
    if (value === undefined) throw new Error("Expected request URL missing");
    if (typeof value === "string") return value;
    return value instanceof URL ? value.href : value.url;
}

test("actual typed-client POST sees the persisted original key before transmission and 202 stays unresolved", async () => {
    const storage = new MemoryStorage();
    let submittedKey = "";
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url, options) => {
        if (options?.method === "POST") {
            submittedKey =
                new Headers(options.headers).get("Idempotency-Key") ?? "";
            expect(submittedKey).not.toBe("");
            expect(storage.saved).toContain(submittedKey);
            return Promise.resolve(acceptance());
        }
        expect(requestUrl(url)).toContain("/operations/" + operationId);
        return Promise.resolve(jsonResponse(problemWire("HFAPI013", 20), 404));
    });
    const { value } = controller(fetcher, storage);
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("accepted");
    expect(value.snapshot().canSubmit).toBe(false);
    expect(value.snapshot().registry.records[0]?.handles.operationId).toBe(
        operationId,
    );
    await expect(
        value.submit({ action: "installedPlan", request: {} }),
    ).rejects.toThrow();
    expect(
        fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(1);
    await vi.waitFor(() => {
        expect(value.observer.snapshot(submitted.recordId).phase).toBe(
            "unknown",
        );
    });
    expect(value.observer.snapshot(submitted.recordId).pauseReason).toBe(
        "history_missing",
    );
});

test("storage quota prevents any fetch and preserves a blocked original handle", async () => {
    const storage = new MemoryStorage();
    storage.fail = true;
    const fetcher = vi.fn<typeof fetch>(),
        { value } = controller(fetcher, storage);
    await expect(
        value.submit({ action: "managedPlan", request: managedRequest }),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
    expect(value.snapshot().registry.records).toHaveLength(1);
    expect(value.snapshot().pendingSubmission).toBe(false);
    expect(value.snapshot().canSubmit).toBe(false);
});

test("real request validation refusal before fetch releases only its own prepared row", async () => {
    const fetcher = vi.fn<typeof fetch>(),
        { value, storage } = controller(fetcher);
    const submitted = await value.submit({
        action: "sync",
        request: { selectors: ["invalid selector"] },
    });
    expect(submitted.result.kind).toBe("refused");
    expect(fetcher).not.toHaveBeenCalled();
    expect(value.snapshot().registry.records).toHaveLength(0);
    expect(value.snapshot().canSubmit).toBe(true);
    expect(value.snapshot().notice).toContain("Not submitted");
    expect(storage.saved).toBe('{"schemaVersion":1,"records":[]}');
});

test("lost acknowledgment is one POST, and explicit observation only looks up its original key", async () => {
    let originalKey: string | null = null;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            const headers = new Headers(options?.headers);
            if (options?.method === "POST") {
                originalKey = headers.get("Idempotency-Key");
                return Promise.reject(
                    new TypeError("lost network acknowledgment"),
                );
            }
            expect(headers.get("Idempotency-Key")).toBe(originalKey);
            return Promise.resolve(
                jsonResponse(problemWire("HFAPI013", 20), 404),
            );
        });
    const { value } = controller(fetcher);
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("uncertain");
    value.observe(submitted.recordId);
    await vi.waitFor(() => {
        expect(value.observer.snapshot(submitted.recordId).phase).toBe(
            "unknown",
        );
    });
    expect(
        fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(1);
    expect(requestUrl(fetcher.mock.calls[1]?.[0])).toContain(
        "/operations/lookup",
    );
    expect(value.snapshot().canSubmit).toBe(false);
});

test("real key/receipt/result decoding resolves the original handle and retains legitimate warnings", async () => {
    const terminal = receipt({
        state: "succeeded",
        completed_at: at,
        domain_run_id: runId,
        result_recorded: true,
    });
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((url, options) =>
            Promise.resolve(
                options?.method === "POST"
                    ? acceptance()
                    : requestUrl(url).endsWith("/result")
                      ? planResult(true)
                      : operationRead(terminal),
            ),
        );
    const { value } = controller(fetcher);
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    await vi.waitFor(() => {
        expect(value.observer.snapshot(submitted.recordId).phase).toBe(
            "settled",
        );
    });
    expect(value.snapshot().registry.records[0]?.state).toBe("terminal");
    expect(value.snapshot().registry.records[0]?.terminal?.code).toBe(
        "HFWRN011",
    );
    expect(value.snapshot().canSubmit).toBe(true);
    expect(
        fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(1);
});

test("late accepted acknowledgment after disconnect retains ID without private observation or replay", async () => {
    const response = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>().mockReturnValue(response.promise);
    const { value } = controller(fetcher);
    const pending = value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    value.disconnect();
    response.resolve(acceptance());
    const submitted = await pending;
    expect(submitted.result.kind).toBe("accepted");
    expect(value.snapshot().connection).toBe("disconnected");
    expect(value.snapshot().registry.records[0]?.handles.operationId).toBe(
        operationId,
    );
    expect(value.snapshot().canSubmit).toBe(false);
    expect(fetcher).toHaveBeenCalledOnce();
});

test("late accepted acknowledgment after disposal persists recovery identity without restarting observation", async () => {
    const response = deferred<Response>(),
        storage = new MemoryStorage();
    const fetcher = vi.fn<typeof fetch>().mockReturnValue(response.promise);
    const { value } = controller(fetcher, storage);
    const pending = value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    value.dispose();
    response.resolve(acceptance());
    expect((await pending).result.kind).toBe("accepted");
    expect(storage.saved).toContain(operationId);
    expect(fetcher).toHaveBeenCalledOnce();
});

test("a disconnect supersedes an in-flight reconnect instead of restoring stale authentication", async () => {
    const response = deferred<UiBootstrap>(),
        fetcher = vi.fn<typeof fetch>();
    const { value } = controller(
        fetcher,
        new MemoryStorage(),
        () => response.promise,
    );
    const pending = value.reconnect();
    expect(value.snapshot().connection).toBe("reconnecting");
    value.disconnect();
    const generation = value.snapshot().generation;
    response.resolve(bootstrap);
    await pending;
    expect(value.snapshot().connection).toBe("disconnected");
    expect(value.snapshot().generation).toBe(generation);
    expect(fetcher).not.toHaveBeenCalled();
});

test("subscriber failures cannot strand submission or change original result", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
    const { value } = controller(fetcher);
    value.subscribe(() => {
        throw new Error("detached view");
    });
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("api_problem");
    expect(value.snapshot().pendingSubmission).toBe(false);
    expect(value.snapshot().registry.records).toHaveLength(1);
    expect(value.snapshot().canSubmit).toBe(false);
});

test.each([
    ["confirmed", false, "known"],
    ["unchanged", false, "known"],
    ["confirmed", true, "unknown-effects"],
    ["staged", true, "unknown-effects"],
    ["installed_unconfirmed", true, "unknown-effects"],
    ["conflict", false, "unknown-effects"],
    ["unknown", false, "unknown-effects"],
] as const)(
    "configuration outcome %s pending=%s gates effect certainty independently of a terminal receipt",
    async (state, pending, expected) => {
        if (!isRecord(fixtures.application_outcome))
            throw new Error("Outcome fixture missing");
        const terminal = receipt({
            route: "/api/v1/config/applications",
            state: "succeeded",
            completed_at: at,
            domain_run_id: runId,
            result_recorded: true,
        });
        const body = {
            ...fixtures.application_outcome,
            operation_id: operationId,
            config_fingerprint: fingerprint,
            state,
            pending,
        };
        const wrapper = readWire("config apply", body);
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            jsonResponse({
                ...wrapper,
                archive_id: ARCHIVE_ID,
                config_fingerprint: fingerprint,
            }),
        );
        const api = new ApiClient({
            scope: bootstrapScope(bootstrap),
            fetcher,
        });
        const result = await api.readOperationResult(terminal);
        expect(result.kind).toBe("success");
        expect(resultCertainty(terminal, result)).toBe(expected);
        expect(fetcher).toHaveBeenCalledOnce();
    },
);

const dispatchIntents: readonly SubmissionIntent[] = [
    { action: "sync", request: { selectors: ["model:org/name"] } },
    { action: "installedPlan", request: {} },
    { action: "candidatePlan", request: { candidate: "schema_version=1" } },
    { action: "managedPlan", request: managedRequest },
    {
        action: "configurationApplication",
        request: {
            managed: managedRequest.managed,
            preview: { operation_id: "b".repeat(32), key: "original-preview" },
        },
    },
    { action: "readOnlyDiagnostics", request: { read_only: true } },
    { action: "probeDiagnostics", request: { read_only: false } },
    { action: "newVerification", request: { mode: "new" } },
    { action: "fullVerification", request: { mode: "full" } },
    {
        action: "revisionVerification",
        request: {
            mode: "revision",
            revision: "model:org/name@" + "b".repeat(40),
        },
    },
    { action: "prunePreview", request: {} },
    { action: "pruneApply", request: {} },
    { action: "purgePreview", request: { all_unmanaged: true } },
    { action: "purgeApply", request: { selectors: ["model:org/name"] } },
    { action: "recoveryPreview", request: {} },
    { action: "recoveryApply", request: {} },
    {
        action: "quarantinePreview",
        request: { transaction_ids: [operationId] },
    },
    { action: "quarantineApply", request: { transaction_ids: [operationId] } },
    {
        action: "repair",
        request: { revision: "model:org/name@" + "b".repeat(40) },
    },
    { action: "catalogRefresh", request: {} },
];
test.each(dispatchIntents)(
    "named controller dispatch $action reaches only its validated original POST",
    async (intent) => {
        const fetcher = vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
        const { value, storage } = controller(fetcher);
        const submitted = await value.submit(intent);
        expect(submitted.result.kind).toBe("api_problem");
        expect(fetcher).toHaveBeenCalledOnce();
        const call = fetcher.mock.calls[0];
        if (call === undefined) throw new Error("Original POST missing");
        expect(call[1]?.method).toBe("POST");
        expect(requestUrl(call[0])).toContain(
            value.snapshot().registry.records[0]?.route,
        );
        expect(storage.saved).toContain(
            new Headers(call[1]?.headers).get("Idempotency-Key"),
        );
        expect(value.snapshot().canSubmit).toBe(false);
    },
);

test("post-admission quota loss preserves learned original ID through controller observation", async () => {
    const storage = new MemoryStorage();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            if (options?.method === "POST") {
                storage.fail = true;
                return Promise.resolve(acceptance());
            }
            return Promise.resolve(
                jsonResponse(problemWire("HFAPI013", 20), 404),
            );
        });
    const { value } = controller(fetcher, storage);
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("accepted");
    expect(value.snapshot().registry.storage).toBe("unavailable");
    expect(value.snapshot().registry.records[0]?.handles.operationId).toBe(
        operationId,
    );
    expect(value.snapshot().canSubmit).toBe(false);
});

test("an actual typed authentication refusal clears private state without discarding unresolved handles", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire(), 401));
    const { value } = controller(fetcher);
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("api_problem");
    expect(value.snapshot().connection).toBe("disconnected");
    expect(value.snapshot().generation).toBe(2);
    expect(value.snapshot().registry.records).toHaveLength(1);
    expect(value.snapshot().canSubmit).toBe(false);
    expect(fetcher).toHaveBeenCalledOnce();
});

test("reconnect failure and a changed release remain explicit without another submission", async () => {
    const fetcher = vi.fn<typeof fetch>();
    const failed = controller(fetcher, new MemoryStorage(), () =>
        Promise.reject(new Error("private connect error")),
    ).value;
    await failed.reconnect();
    expect(failed.snapshot().connection).toBe("disconnected");
    expect(failed.snapshot().notice).not.toContain("private connect error");
    const changed = controller(fetcher, new MemoryStorage(), () =>
        Promise.resolve({
            ...bootstrap,
            build: {
                ...bootstrap.build,
                asset_manifest_sha256: "f".repeat(64),
            },
        }),
    ).value;
    await changed.reconnect();
    expect(changed.snapshot().connection).toBe("update_required");
    expect(changed.snapshot().canSubmit).toBe(false);
    expect(fetcher).not.toHaveBeenCalled();
});

test("reconnected authority requires explicit original-key observation and never replays POST", async () => {
    const terminal = receipt({
        state: "succeeded",
        completed_at: at,
        domain_run_id: runId,
        result_recorded: true,
    });
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url, options) => {
        if (options?.method === "POST")
            return Promise.reject(new TypeError("lost acknowledgment"));
        if (requestUrl(url).endsWith("/result"))
            return Promise.resolve(planResult());
        const wrapper = readWire(
            requestUrl(url).includes("/lookup")
                ? "operations lookup"
                : "operations show",
            { operation: terminal },
        );
        return Promise.resolve(
            jsonResponse({
                ...wrapper,
                archive_id: ARCHIVE_ID,
                config_fingerprint: fingerprint,
            }),
        );
    });
    const { value } = controller(fetcher, new MemoryStorage(), () =>
        Promise.resolve({
            ...bootstrap,
            instance_id: "b".repeat(32),
            authority_epoch: "b".repeat(32),
        }),
    );
    const submitted = await value.submit({
        action: "managedPlan",
        request: managedRequest,
    });
    expect(submitted.result.kind).toBe("uncertain");
    value.disconnect();
    await value.reconnect();
    expect(value.snapshot().connection).toBe("connected");
    expect(value.snapshot().canSubmit).toBe(false);
    expect(fetcher).toHaveBeenCalledOnce();
    value.observe(submitted.recordId);
    await vi.waitFor(() => {
        expect(value.observer.snapshot(submitted.recordId).phase).toBe(
            "settled",
        );
    });
    expect(value.snapshot().canSubmit).toBe(true);
    expect(
        fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(1);
    expect(requestUrl(fetcher.mock.calls[1]?.[0])).toContain(
        "/operations/lookup",
    );
});

test("manual legacy reference remains nonblocking while stop-observing sends no effect request", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
    const { value } = controller(fetcher);
    const reference = value.importHandle({
        kind: "legacy-key",
        key: "old-cockpit-original",
        credentialClass: "rest-writer",
    });
    expect(value.snapshot().canSubmit).toBe(true);
    expect(() => {
        value.observe(reference.recordId);
    }).toThrow();
    value.stopObserving(reference.recordId);
    expect(fetcher).not.toHaveBeenCalled();
    value.disconnect();
    expect(() => value.importHandle({ kind: "id", operationId })).toThrow();
    expect(() => {
        value.observe(reference.recordId);
    }).toThrow();
    await expect(
        value.submit({ action: "managedPlan", request: managedRequest }),
    ).rejects.toThrow();
});
