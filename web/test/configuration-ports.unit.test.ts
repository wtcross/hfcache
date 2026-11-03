/** Real typed HTTP boundaries; these units do not claim installed helper effects. */
import { afterEach, expect, test, vi } from "vitest";
import { createAuthSession } from "../src/state/authority";
import {
    createOperationRegistry,
    OPERATION_STORAGE_KEY,
} from "../src/state/operation-registry";
import type { OperationStorage } from "../src/state/operation-registry";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import {
    SESSION_RESPONSE_BYTES,
    StateCapacityError,
} from "../src/state/retention-budget";
import { decodeConfigApplicationOutcome } from "../src/wire/generated";
import type {
    ConfigApplicationOutcome,
    RequestManagedValidationRequest,
    UiBootstrap,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import {
    deferred,
    OPERATION_ID,
    operationResponse,
    receipt,
    session,
} from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const key = "owned-original-application-key";
const baseRevision = "a".repeat(64),
    candidateRevision = "b".repeat(64);
const request: RequestManagedValidationRequest = {
    managed: { base_revision: baseRevision, edits: [] },
};
const controllers = new Set<SessionController>();
afterEach(() => {
    for (const controller of controllers) controller.dispose();
    controllers.clear();
    vi.unstubAllGlobals();
});

class MemoryStorage implements OperationStorage {
    saved: string | null = null;
    writes = 0;
    getItem(name: string): string | null {
        expect(name).toBe(OPERATION_STORAGE_KEY);
        return this.saved;
    }
    setItem(name: string, value: string): void {
        expect(name).toBe(OPERATION_STORAGE_KEY);
        this.saved = value;
        this.writes++;
    }
}
function outcome(changes: Partial<ConfigApplicationOutcome> = {}) {
    return decodeConfigApplicationOutcome(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                operation_id: OPERATION_ID,
                request_digest: "e".repeat(64),
                base_revision: baseRevision,
                candidate_revision: candidateRevision,
                config_fingerprint: "2".repeat(64),
                state: "confirmed",
                pending: false,
                ...changes,
            }),
        ),
    );
}
function applicationReceipt(state = "interrupted") {
    const terminal = ["succeeded", "failed", "interrupted"].includes(state);
    return receipt({
        route: "/api/v1/config/applications",
        state,
        completed_at: terminal ? "2026-10-20T12:00:01.000000Z" : null,
        result_recorded: state === "succeeded" || state === "failed",
    });
}
function registryProof(state = "interrupted", storage = new MemoryStorage()) {
    const registry = createOperationRegistry({ storage });
    const record = registry.importHandle(
        {
            kind: "basic-key",
            key,
            operationId: OPERATION_ID,
            originalScope: session.scope,
        },
        session,
    );
    const auth = registry.authorizeObservation(record.recordId, session);
    registry.observed(auth, applicationReceipt(state));
    return {
        registry,
        storage,
        record,
        auth: registry.authorizeObservation(record.recordId, session),
    };
}
function bootstrap(read = true, write = true): UiBootstrap {
    const original = uiBootstrapFixture();
    return {
        ...original,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...original.user,
            admin_permissions: original.user.admin_permissions.map((row) => {
                const allowed =
                    row.capability === "config-read"
                        ? read
                        : row.capability === "config-write"
                          ? write
                          : false;
                return {
                    ...row,
                    effective: allowed,
                    granted: allowed,
                    reason: allowed ? "allowed" : "not_granted",
                };
            }),
        },
    };
}
function controller(
    fetcher: typeof fetch,
    initial = bootstrap(),
    storage = new MemoryStorage(),
) {
    const value = createSessionController({
        bootstrap: initial,
        fetcher,
        storage,
        reconnect: () => Promise.resolve(initial),
    });
    controllers.add(value);
    return { value, storage };
}
function importApplication(value: SessionController) {
    return value.importHandle({
        kind: "basic-key",
        key,
        operationId: OPERATION_ID,
        originalScope: value.originalScope(),
    });
}
function urlOf(value: RequestInfo | URL): URL {
    return new URL(
        typeof value === "string"
            ? value
            : value instanceof URL
              ? value.href
              : value.url,
    );
}
function validationResponse() {
    return jsonResponse(
        operationResponse("config validate", {
            schema_version: 1,
            archive_id: ARCHIVE_ID,
            base_revision: baseRevision,
            candidate_revision: candidateRevision,
            required_selectors: [],
            valid: true,
        }),
    );
}
function outcomeFetcher(
    value: ConfigApplicationOutcome = outcome(),
    state = "interrupted",
) {
    return vi.fn<typeof fetch>().mockImplementation((url, options) => {
        expect(options?.method).toBe("GET");
        expect(new Headers(options?.headers).get("Idempotency-Key")).toBe(key);
        const path = urlOf(url).pathname;
        if (path === "/api/v1/operations/lookup")
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations lookup", {
                        operation: applicationReceipt(state),
                    }),
                ),
            );
        expect(path).toBe("/api/v1/config/applications/" + OPERATION_ID);
        return Promise.resolve(
            jsonResponse(operationResponse("config outcome", value)),
        );
    });
}

test("hidden original configuration outcome reads require explicit Observe after return", async () => {
    const fetcher = outcomeFetcher(),
        { value } = controller(fetcher),
        record = importApplication(value);
    value.setPageHidden(true);
    await expect(
        value.observeConfigurationOutcome(record.recordId),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
    value.setPageHidden(false);
    expect(fetcher).not.toHaveBeenCalled();
    expect(
        (await value.observeConfigurationOutcome(record.recordId)).kind,
    ).toBe("outcome");
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(
        fetcher.mock.calls.filter(
            ([input]) => urlOf(input).pathname === "/api/v1/operations/intent",
        ),
    ).toHaveLength(1);
});

test.each(["lookup", "outcome"])(
    "hide and return fences a late configuration %s without donating proof",
    async (stage) => {
        const late = deferred<Response>();
        let signal: AbortSignal | null | undefined;
        const fetcher = vi.fn<typeof fetch>((input, options) => {
            if (urlOf(input).pathname === "/api/v1/operations/intent")
                return Promise.resolve(
                    jsonResponse({
                        schema_version: 1,
                        archive_id: ARCHIVE_ID,
                        state: "unknown",
                        operation: null,
                        disposition: null,
                    }),
                );
            const lookup =
                urlOf(input).pathname === "/api/v1/operations/lookup";
            if ((stage === "lookup") === lookup) {
                signal = options?.signal;
                return late.promise;
            }
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations lookup", {
                        operation: applicationReceipt(),
                    }),
                ),
            );
        });
        const { value } = controller(fetcher),
            record = importApplication(value);
        const observing = value.observeConfigurationOutcome(record.recordId),
            rejection = expect(observing).rejects.toThrow();
        await vi.waitFor(() => {
            expect(fetcher).toHaveBeenCalledTimes(stage === "lookup" ? 1 : 2);
        });
        value.setPageHidden(true);
        expect(signal?.aborted).toBe(true);
        value.setPageHidden(false);
        late.resolve(
            jsonResponse(
                stage === "lookup"
                    ? operationResponse("operations lookup", {
                          operation: applicationReceipt(),
                      })
                    : operationResponse("config outcome", outcome()),
            ),
        );
        await rejection;
        expect(fetcher).toHaveBeenCalledTimes(stage === "lookup" ? 2 : 3);
        expect(
            fetcher.mock.calls.filter(
                ([input]) =>
                    urlOf(input).pathname === "/api/v1/operations/intent",
            ),
        ).toHaveLength(1);
        expect(value.snapshot().canSubmit).toBe(false);
        expect(value.snapshot().registry.records[0]?.handles).toMatchObject({
            key,
            operationId: OPERATION_ID,
        });
    },
);

test.each(["succeeded", "failed", "interrupted"])(
    "fresh confirmed host evidence settles effects after API %s without rewriting its stored receipt",
    (state) => {
        const { registry, storage, record, auth } = registryProof(state);
        const saved = storage.saved,
            writes = storage.writes,
            snapshot = registry.snapshot().records;
        expect(registry.canSubmit(session)).toBe(false);
        registry.configurationOutcome(auth, outcome());
        expect(registry.canSubmit(session)).toBe(true);
        expect(storage.saved).toBe(saved);
        expect(storage.writes).toBe(writes);
        expect(registry.snapshot().records).toStrictEqual(snapshot);
        expect(registry.snapshot().records[0]?.state).toBe("observing");
        expect(registry.snapshot().records[0]?.handles.operationId).toBe(
            OPERATION_ID,
        );
        expect(record.terminal).toBeNull();
    },
);

test("unchanged is also a known zero-change outcome, without claiming API success", () => {
    const { registry, auth } = registryProof();
    registry.configurationOutcome(auth, outcome({ state: "unchanged" }));
    expect(registry.canSubmit(session)).toBe(true);
    expect(registry.snapshot().records[0]?.terminal).toBeNull();
});

test.each([
    ["confirmed", true],
    ["unchanged", true],
    ["staged", false],
    ["installed_unconfirmed", false],
    ["conflict", false],
    ["unknown", false],
] as const)(
    "host state %s pending=%s preserves the unresolved original handle",
    (state, pending) => {
        const { registry, auth } = registryProof();
        registry.configurationOutcome(auth, outcome({ state, pending }));
        expect(registry.canSubmit(session)).toBe(false);
    },
);

test.each(["queued", "running"])(
    "a confirmed host record cannot finish a still-%s API operation",
    (state) => {
        const { registry, auth } = registryProof(state);
        registry.configurationOutcome(auth, outcome());
        expect(registry.canSubmit(session)).toBe(false);
    },
);

test("host confirmation must match the freshly verified original operation and archive", () => {
    const { registry, auth } = registryProof();
    for (const invalid of [
        outcome({ operation_id: "c".repeat(32) }),
        outcome({ archive_id: "12345678-1234-1234-1234-123456789abc" }),
    ]) {
        expect(() => {
            registry.configurationOutcome(auth, invalid);
        }).toThrow();
        expect(registry.canSubmit(session)).toBe(false);
    }
    expect(() => {
        registry.configurationOutcome({ ...auth }, outcome());
    }).toThrow();
    expect(registry.canSubmit(session)).toBe(false);
});

test("a stored Basic association alone cannot authorize host confirmation before fresh original-key proof", () => {
    const registry = createOperationRegistry({ storage: new MemoryStorage() });
    const record = registry.importHandle(
        {
            kind: "basic-key",
            key,
            operationId: OPERATION_ID,
            originalScope: session.scope,
        },
        session,
    );
    const auth = registry.authorizeObservation(record.recordId, session);
    expect(auth.locator.kind).toBe("key");
    expect(() => {
        registry.configurationOutcome(auth, outcome());
    }).toThrow();
    expect(registry.canSubmit(session)).toBe(false);
});

test("confirmed effect proof disappears on restore and auth change; original-key lookup is required again", () => {
    const { registry, auth, record, storage } = registryProof();
    registry.configurationOutcome(auth, outcome());
    expect(registry.canSubmit(session)).toBe(true);
    const restored = createOperationRegistry({ storage });
    expect(restored.canSubmit(session)).toBe(false);
    expect(
        restored.authorizeObservation(record.recordId, session).locator,
    ).toEqual({ kind: "key", key });
    registry.invalidateObservations();
    const next = createAuthSession({ scope: session.scope, authGeneration: 2 });
    expect(registry.canSubmit(next)).toBe(false);
    expect(() => {
        registry.configurationOutcome(auth, outcome());
    }).toThrow();
    expect(
        registry.authorizeObservation(record.recordId, next).locator,
    ).toEqual({ kind: "key", key });
});

test("read-only configuration authority uses exactly original-key lookup then outcome GET and never requires host/write grants", async () => {
    const fetcher = outcomeFetcher(),
        { value, storage } = controller(fetcher, bootstrap(true, false));
    const record = importApplication(value);
    expect(value.snapshot().canSubmit).toBe(false);
    const observed = await value.observeConfigurationOutcome(record.recordId, {
        baseRevision,
        candidateRevision,
    });
    expect(observed.kind).toBe("outcome");
    expect(fetcher.mock.calls.map(([url]) => urlOf(url).pathname)).toEqual([
        "/api/v1/operations/lookup",
        "/api/v1/config/applications/" + OPERATION_ID,
    ]);
    expect(value.snapshot().canSubmit).toBe(true);
    expect(value.snapshot().registry.records[0]?.state).toBe("observing");
    expect(storage.saved).not.toContain("request_digest");
    expect(storage.saved).not.toContain(candidateRevision);
    expect(
        value
            .snapshot()
            .bootstrap.user.admin_permissions.filter((row) => row.effective)
            .map((row) => row.capability),
    ).toEqual(["config-read"]);
});

test("configuration read and validation grants are independent and refuse before fetch", async () => {
    const fetcher = vi.fn<typeof fetch>(),
        { value } = controller(fetcher, bootstrap(false, true));
    const record = importApplication(value);
    await expect(
        value.observeConfigurationOutcome(record.recordId),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
    fetcher.mockResolvedValue(validationResponse());
    expect((await value.validateConfiguration(request)).kind).toBe("success");
    expect(fetcher).toHaveBeenCalledTimes(1);
    const readOnly = controller(vi.fn<typeof fetch>(), bootstrap(true, false));
    await expect(
        readOnly.value.validateConfiguration(request),
    ).rejects.toThrow();
});

test("mismatched expected candidate cannot unlock the lane even after valid original-key lookup", async () => {
    const { value } = controller(outcomeFetcher()),
        record = importApplication(value);
    await expect(
        value.observeConfigurationOutcome(record.recordId, {
            baseRevision,
            candidateRevision: "c".repeat(64),
        }),
    ).rejects.toThrow();
    expect(value.snapshot().canSubmit).toBe(false);
});

test.each([
    ["confirmed", true],
    ["installed_unconfirmed", false],
    ["unknown", false],
] as const)(
    "typed observation of %s pending=%s keeps submission blocked",
    async (state, pending) => {
        const { value } = controller(
            outcomeFetcher(outcome({ state, pending })),
        );
        const record = importApplication(value);
        await value.observeConfigurationOutcome(record.recordId);
        expect(value.snapshot().canSubmit).toBe(false);
    },
);

test("original-key not found returns its real lookup failure without outcome GET or POST", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI005", 40), 404));
    const { value } = controller(fetcher),
        record = importApplication(value);
    const result = await value.observeConfigurationOutcome(record.recordId);
    expect(result.kind).toBe("lookup");
    expect(fetcher).toHaveBeenCalledTimes(1);
    const called = fetcher.mock.calls[0];
    if (called === undefined) throw new Error("Missing original-key lookup");
    expect(urlOf(called[0]).pathname).toBe("/api/v1/operations/lookup");
    expect(value.snapshot().canSubmit).toBe(false);
});

test("an auth change aborts outcome observation and a late confirmed response cannot release the new session", async () => {
    const late = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn<typeof fetch>().mockImplementation((url, options) => {
        if (urlOf(url).pathname.endsWith("/lookup"))
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations lookup", {
                        operation: applicationReceipt(),
                    }),
                ),
            );
        signal = options?.signal;
        return late.promise;
    });
    const { value } = controller(fetcher),
        record = importApplication(value);
    const observing = value.observeConfigurationOutcome(record.recordId);
    const rejection = expect(observing).rejects.toThrow();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    value.disconnect();
    expect(signal?.aborted).toBe(true);
    await value.reconnect();
    late.resolve(jsonResponse(operationResponse("config outcome", outcome())));
    await rejection;
    expect(value.snapshot().canSubmit).toBe(false);
    expect(value.snapshot().registry.records[0]?.handles.operationId).toBe(
        OPERATION_ID,
    );
});

test("managed validation is one bounded unkeyed request and never persists candidate/draft state", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(validationResponse());
    const { value, storage } = controller(fetcher, bootstrap(false, true));
    const before = storage.saved;
    const result = await value.validateConfiguration(request);
    expect(result.kind).toBe("success");
    expect(fetcher).toHaveBeenCalledTimes(1);
    const called = fetcher.mock.calls[0];
    if (called === undefined) throw new Error("Missing managed validation");
    const [url, options] = called;
    expect(urlOf(url).pathname).toBe("/api/v1/config/validate");
    expect(options?.method).toBe("POST");
    if (typeof options?.body !== "string") throw new Error("Missing JSON body");
    expect(JSON.parse(options.body)).toEqual(request);
    expect(new Headers(options.headers).has("Idempotency-Key")).toBe(false);
    expect(storage.saved).toBe(before);
    expect(value.snapshot().registry.records).toEqual([]);
});

test("caller cancellation aborts validation without creating an application handle", async () => {
    let signal: AbortSignal | null | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            signal = options?.signal;
            return new Promise((_resolve, reject) => {
                signal?.addEventListener(
                    "abort",
                    () => {
                        reject(new DOMException("Stopped", "AbortError"));
                    },
                    { once: true },
                );
            });
        });
    const { value } = controller(fetcher),
        cancel = new AbortController();
    const validation = value.validateConfiguration(request, {
        signal: cancel.signal,
    });
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(1);
    });
    cancel.abort();
    expect((await validation).kind).toBe("aborted");
    expect(signal?.aborted).toBe(true);
    expect(value.snapshot().registry.records).toEqual([]);
});

test("late successful validation from a previous auth generation is withheld", async () => {
    const late = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            signal = options?.signal;
            return late.promise;
        });
    const { value } = controller(fetcher);
    const validation = value.validateConfiguration(request);
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(1);
    });
    value.disconnect();
    expect(signal?.aborted).toBe(true);
    await value.reconnect();
    late.resolve(validationResponse());
    expect((await validation).kind).toBe("aborted");
    expect(value.snapshot().registry.records).toEqual([]);
});

test("private drafts share query/read retention capacity and release on clear or auth change", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(validationResponse());
    const { value, storage } = controller(fetcher);
    const before = storage.saved;
    const chunk = "x".repeat(7 * 1024 * 1024 - 2);
    const slots = Array.from({ length: 4 }, () => value.createPrivateSlot());
    for (const slot of slots) expect(slot.set(chunk)).toBe(true);
    await expect(value.validateConfiguration(request)).rejects.toBeInstanceOf(
        StateCapacityError,
    );
    expect(fetcher).not.toHaveBeenCalled();
    const first = slots[0],
        second = slots[1];
    if (first === undefined || second === undefined)
        throw new Error("Missing private slots");
    first.clear();
    expect((await value.validateConfiguration(request)).kind).toBe("success");
    const oversized = value.createPrivateSlot();
    expect(oversized.set("x".repeat(SESSION_RESPONSE_BYTES))).toBe(false);
    value.disconnect();
    await value.reconnect();
    expect(second.set("old-generation")).toBe(false);
    const fresh = value.createPrivateSlot();
    expect(fresh.set("x".repeat(SESSION_RESPONSE_BYTES - 2))).toBe(true);
    fresh.clear();
    expect(storage.saved).toBe(before);
});
