import { afterEach, expect, test, vi } from "vitest";
import { ApiClient } from "../src/api/client";
import {
    createOperationObserver,
    mergeEventWindow,
} from "../src/state/operation-observation";
import type { OperationObserverOptions } from "../src/state/operation-observation";
import {
    createReadCoordinator,
    createRetentionBudget,
    READ_RESERVATION_BYTES,
} from "../src/state/retention-budget";
import { receiptIdentity } from "../src/state/authority";
import { createOperationRegistry } from "../src/state/operation-registry";
import { createQueryStore } from "../src/state/query-state";
import { jsonResponse, problemWire } from "./read-fixtures";
import {
    authorized,
    reauthorize,
    terminal,
    receipt,
    events,
    operationResponse,
    resultResponse,
    scope,
    session,
    OPERATION_ID,
    deferred,
    versionResult,
} from "./state-fixtures";

function setup(overrides: Partial<OperationObserverOptions> = {}) {
    const retention = createRetentionBudget(),
        reads = createReadCoordinator();
    const onReceipt = vi.fn(reauthorize),
        onResult = vi
            .fn<OperationObserverOptions["onResult"]>()
            .mockReturnValue("known"),
        onUnauthorized = vi.fn();
    const observer = createOperationObserver({
        retention,
        reads,
        onReceipt,
        onResult,
        onUnauthorized,
        ...overrides,
    });
    return { observer, retention, reads, onReceipt, onResult, onUnauthorized };
}
function path(input: Parameters<typeof fetch>[0]): string {
    return input instanceof URL
        ? input.pathname
        : typeof input === "string"
          ? new URL(input).pathname
          : new URL(input.url).pathname;
}
function terminalClient() {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((input) =>
            Promise.resolve(
                jsonResponse(
                    path(input).endsWith("/result")
                        ? resultResponse()
                        : operationResponse(
                              path(input).endsWith("lookup")
                                  ? "operations lookup"
                                  : "operations show",
                              { operation: terminal() },
                          ),
                ),
            ),
        );
    return { fetcher, client: new ApiClient({ scope, fetcher }) };
}
afterEach(() => {
    vi.useRealTimers();
});

test("hidden observation attempts stay read-free until an explicit visible Observe", async () => {
    const state = setup(),
        auth = authorized(),
        { fetcher, client } = terminalClient();
    state.observer.setHidden(true);
    await state.observer.observe(auth, client);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "paused",
        pauseReason: "hidden",
    });
    expect(fetcher).not.toHaveBeenCalled();
    state.observer.setHidden(false);
    await Promise.resolve();
    expect(fetcher).not.toHaveBeenCalled();
    await state.observer.observe(auth, client);
    expect(state.observer.snapshot(auth.recordId).phase).toBe("settled");
    expect(fetcher).toHaveBeenCalledTimes(2);
    state.observer.dispose();
});

test("hiding fences a transport that ignores abort and releases owned timers", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized(),
        late = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn<typeof fetch>((_input, options) => {
        signal = options?.signal;
        return late.promise;
    });
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    await vi.advanceTimersByTimeAsync(0);
    expect(fetcher).toHaveBeenCalledOnce();
    const activeTimers = vi.getTimerCount();
    const pendingBytes = state.retention.usedBytes;
    state.observer.setHidden(true);
    expect(signal?.aborted).toBe(true);
    // The uncooperative transport retains its own finite read timeout until
    // settlement; the observer's session deadline is retired immediately.
    expect(vi.getTimerCount()).toBeLessThan(activeTimers);
    state.observer.setHidden(false);
    late.resolve(
        jsonResponse(
            operationResponse("operations lookup", { operation: terminal() }),
        ),
    );
    await pending;
    expect(vi.getTimerCount()).toBe(0);
    expect(state.onReceipt).not.toHaveBeenCalled();
    expect(state.onResult).not.toHaveBeenCalled();
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "paused",
        pauseReason: "hidden",
        receipt: null,
        result: null,
    });
    expect(pendingBytes - state.retention.usedBytes).toBe(
        READ_RESERVATION_BYTES,
    );
    expect(fetcher).toHaveBeenCalledOnce();
    state.observer.dispose();
});

test("hiding cancels the retry delay without restarting it on return", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI019", 20), 503));
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    await vi.advanceTimersByTimeAsync(0);
    expect(fetcher).toHaveBeenCalledOnce();
    state.observer.setHidden(true);
    await pending;
    expect(vi.getTimerCount()).toBe(0);
    state.observer.setHidden(false);
    await vi.advanceTimersByTimeAsync(7000);
    expect(fetcher).toHaveBeenCalledOnce();
    expect(state.observer.snapshot(auth.recordId).pauseReason).toBe("hidden");
    state.observer.dispose();
});

test("original-key-first then actual typed result, no POST and controller owns resolution", async () => {
    const state = setup(),
        { fetcher, client } = terminalClient();
    const auth = authorized();
    await state.observer.observe(auth, client);
    const result = state.observer.snapshot(auth.recordId);
    expect(result.phase).toBe("settled");
    expect(result.receipt?.operation_id).toBe(OPERATION_ID);
    expect(result.result?.kind).toBe("success");
    expect(state.onReceipt.mock.calls[0]?.[0]).toBe(auth);
    expect(state.onResult).toHaveBeenCalledOnce();
    expect(fetcher.mock.calls.map(([request]) => path(request))).toEqual([
        "/api/v1/operations/lookup",
        `/api/v1/operations/${OPERATION_ID}/result`,
    ]);
    expect(
        fetcher.mock.calls.every(([, options]) => options?.method === "GET"),
    ).toBe(true);
    state.observer.dispose();
    expect(state.retention.usedBytes).toBe(0);
});

test("real registry-issued authorization identity is retained through lookup and reauthorization", async () => {
    let stored: string | null = null;
    const registry = createOperationRegistry({
        storage: {
            getItem: () => stored,
            setItem: (_key, value) => {
                stored = value;
            },
        },
    });
    const record = registry.importHandle(
        { kind: "basic-key", key: "owned-original-key", originalScope: scope },
        session,
    );
    const initial = registry.authorizeObservation(record.recordId, session);
    const state = setup({
        onReceipt: (auth, value) => {
            registry.observed(auth, value);
            return registry.authorizeObservation(auth.recordId, session);
        },
    });
    await state.observer.observe(initial, terminalClient().client);
    expect(state.observer.snapshot(record.recordId).phase).toBe("settled");
    expect(registry.canSubmit(session)).toBe(false); // Observer never resolves registry itself.
    state.observer.dispose();
});

test("unknown effects retain full result and cannot be labelled settled", async () => {
    const state = setup({ onResult: () => "unknown-effects" });
    const auth = authorized();
    await state.observer.observe(auth, terminalClient().client);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "unknown",
        pauseReason: "unknown_effects",
        result: { kind: "success" },
    });
    state.observer.dispose();
});

test.each(["interrupted", "missing-result", "missing-history"])(
    "%s keeps original observation unknown without result fabrication",
    async (fault) => {
        const state = setup(),
            auth = authorized();
        const fetcher = vi.fn<typeof fetch>().mockImplementation((input) => {
            if (fault === "missing-history" || path(input).endsWith("/result"))
                return Promise.resolve(
                    jsonResponse(problemWire("HFAPI007", 10), 404),
                );
            const operation =
                fault === "interrupted"
                    ? receipt({
                          state: "interrupted",
                          completed_at: "2026-10-20T12:00:01.000000Z",
                      })
                    : terminal();
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations lookup", { operation }),
                ),
            );
        });
        await state.observer.observe(auth, new ApiClient({ scope, fetcher }));
        expect(state.observer.snapshot(auth.recordId).phase).toBe("unknown");
        expect(state.onResult).not.toHaveBeenCalled();
        expect(fetcher.mock.calls.every(([, o]) => o?.method === "GET")).toBe(
            true,
        );
        state.observer.dispose();
    },
);

test("initial read plus three1/2/4-second retries then visible pause", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
            Promise.resolve(jsonResponse(problemWire("HFAPI019", 20), 503)),
        );
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    await vi.advanceTimersByTimeAsync(0);
    expect(fetcher).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(999);
    expect(fetcher).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(fetcher).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(2000);
    expect(fetcher).toHaveBeenCalledTimes(3);
    await vi.advanceTimersByTimeAsync(4000);
    await pending;
    expect(fetcher).toHaveBeenCalledTimes(4);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "unknown",
        pauseReason: "retry_limit",
    });
    state.observer.dispose();
});

test("successful status cannot reset repeated events failure budget", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input) =>
        Promise.resolve(
            path(input).endsWith("/events")
                ? jsonResponse(problemWire("HFAPI019", 20), 503)
                : jsonResponse(
                      operationResponse("operations lookup", {
                          operation: receipt(),
                      }),
                  ),
        ),
    );
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    await vi.advanceTimersByTimeAsync(7000);
    await pending;
    expect(
        fetcher.mock.calls.filter(([r]) => path(r).endsWith("/events")),
    ).toHaveLength(4);
    expect(
        fetcher.mock.calls.filter(([r]) => path(r).endsWith("lookup")),
    ).toHaveLength(1);
    state.observer.dispose();
});

test("120-cycle limit is finite and navigation subscriber removal does not stop operation observation", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    let first = true;
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input) => {
        if (path(input).endsWith("/events"))
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations events", events([])),
                ),
            );
        const command = first ? "operations lookup" : "operations show";
        first = false;
        return Promise.resolve(
            jsonResponse(operationResponse(command, { operation: receipt() })),
        );
    });
    const unsubscribe = state.observer.subscribe(auth.recordId, () => {});
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    unsubscribe();
    await vi.advanceTimersByTimeAsync(240000);
    await pending;
    expect(fetcher).toHaveBeenCalledTimes(240);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "paused",
        pauseReason: "session_limit",
    });
    state.observer.dispose();
});

test("late completion after clearPrivate cannot refill state;401 clears other private observations", async () => {
    const state = setup(),
        auth = authorized();
    await state.observer.observe(auth, terminalClient().client);
    const delayed = deferred<Response>();
    const client = new ApiClient({ scope, fetcher: () => delayed.promise });
    const pending = state.observer.observe(auth, client);
    await vi.waitFor(() => {
        expect(state.reads.active).toBe(1);
    });
    state.observer.clearPrivate();
    expect(state.observer.snapshot(auth.recordId).result).toBeNull();
    delayed.resolve(
        jsonResponse(
            operationResponse("operations lookup", { operation: terminal() }),
        ),
    );
    await pending;
    expect(state.observer.snapshot(auth.recordId).result).toBeNull();
    const denied = new ApiClient({
        scope,
        fetcher: () =>
            Promise.resolve(jsonResponse(problemWire("HFAPI001", 10), 401)),
    });
    await state.observer.observe(auth, denied);
    expect(state.onUnauthorized).toHaveBeenCalledOnce();
    expect(state.observer.snapshot(auth.recordId).receipt).toBeNull();
    state.observer.dispose();
});

test("global capacity refuses before GET and full result cannot silently fall out of retention", async () => {
    const state = setup({ retention: createRetentionBudget(1024) }),
        { fetcher, client } = terminalClient();
    const auth = authorized();
    await state.observer.observe(auth, client);
    expect(fetcher).not.toHaveBeenCalled();
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "unknown",
        pauseReason: "capacity",
        result: null,
    });
    state.observer.dispose();
});

test("events preserve server gaps, bounded local omissions, duplicates and conflicts", () => {
    const empty = { rows: [], cursor: 0, gaps: [], omitted: 0 };
    const gap = mergeEventWindow(
        empty,
        events([10, 11], { oldest_sequence: 10, truncated: true }),
        OPERATION_ID,
    );
    expect(gap.gaps).toEqual([{ from: 1, to: 9, reason: "server_retention" }]);
    expect(mergeEventWindow(gap, events([10, 11]), OPERATION_ID).rows).toEqual(
        gap.rows,
    );
    const conflicting = events([11], {
        events: [{ ...events([11]).events[0], message: "changed" }],
    });
    expect(() => mergeEventWindow(gap, conflicting, OPERATION_ID)).toThrow();
    const first = mergeEventWindow(
        empty,
        events(Array.from({ length: 32 }, (_, i) => i + 1)),
        OPERATION_ID,
    );
    const second = mergeEventWindow(
        first,
        events(Array.from({ length: 32 }, (_, i) => i + 33)),
        OPERATION_ID,
    );
    expect(second.rows).toHaveLength(32);
    expect(second.cursor).toBe(64);
    expect(second.omitted).toBe(32);
    const huge = mergeEventWindow(
        empty,
        events([1], {
            events: [{ ...events([1]).events[0], message: "x".repeat(70000) }],
        }),
        OPERATION_ID,
    );
    expect(huge.rows).toHaveLength(0);
    expect(huge.cursor).toBe(1);
    expect(huge.omitted).toBe(1);
});

test("controller same-stack clear of both stores precedes cross-store subscriber peeks", async () => {
    const state = setup(),
        auth = authorized();
    const queries = createQueryStore({
        session,
        retention: state.retention,
        reads: state.reads,
        onUnauthorized: () => {},
    });
    const query = queries.query({ routeId: "version_default" }, () =>
        versionResult("private-query"),
    );
    await query.refresh();
    await state.observer.observe(auth, terminalClient().client);
    const peeks: unknown[] = [];
    state.observer.subscribe(auth.recordId, () => {
        peeks.push(query.snapshot().result);
    });
    query.subscribe(() => {
        peeks.push(state.observer.snapshot(auth.recordId).result);
    });
    state.observer.clearPrivate();
    queries.clearPrivate("authentication");
    expect(peeks).toEqual([]);
    await Promise.resolve();
    expect(peeks).toEqual([null, null]);
    state.observer.dispose();
    queries.dispose();
});

test.each([
    "scope",
    "identity",
    "registry-error",
    "contradictory-reauthorization",
])("%s cannot settle or fetch original result", async (fault) => {
    const state = setup({
        onReceipt: (auth, value) => {
            if (fault === "scope") return null;
            if (fault === "registry-error")
                throw new Error("private registry detail");
            return fault === "contradictory-reauthorization"
                ? { ...reauthorize(auth, value), recordId: "different-record" }
                : reauthorize(auth, value);
        },
    });
    const initial = authorized();
    const auth =
        fault === "identity"
            ? {
                  ...initial,
                  expectedSafeReceiptIdentity: receiptIdentity(
                      receipt({ created_at: "2026-10-19T12:00:00.000000Z" }),
                  ),
              }
            : initial;
    const { client, fetcher } = terminalClient();
    await state.observer.observe(auth, client);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "unknown",
        result: null,
    });
    expect(fetcher).toHaveBeenCalledOnce();
    expect(state.onResult).not.toHaveBeenCalled();
    expect(
        JSON.stringify(state.observer.snapshot(auth.recordId)),
    ).not.toContain("private registry detail");
    state.observer.dispose();
});

test("five-minute deadline clears pending authority and late original result cannot resolve", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    const delayed = deferred<Response>();
    const client = new ApiClient({ scope, fetcher: () => delayed.promise });
    const pending = state.observer.observe(auth, client);
    await vi.advanceTimersByTimeAsync(300000);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "paused",
        pauseReason: "session_limit",
    });
    delayed.resolve(
        jsonResponse(
            operationResponse("operations lookup", { operation: terminal() }),
        ),
    );
    await pending;
    expect(state.onReceipt).not.toHaveBeenCalled();
    expect(state.observer.snapshot(auth.recordId).receipt).toBeNull();
    state.observer.dispose();
});

test("clock deadline before first read is bounded and observer disposal refuses new work", async () => {
    const clock = vi.fn().mockReturnValueOnce(0).mockReturnValue(300000);
    const state = setup({ clock }),
        auth = authorized();
    const { client, fetcher } = terminalClient();
    await state.observer.observe(auth, client);
    expect(fetcher).not.toHaveBeenCalled();
    expect(state.observer.snapshot(auth.recordId).pauseReason).toBe(
        "session_limit",
    );
    state.observer.dispose();
    expect(() => state.observer.observe(auth, client)).toThrow();
    expect(() => state.observer.snapshot("never-admitted")).toThrow();
});

test("explicit pause aborts retry sleep without additional reads", async () => {
    vi.useFakeTimers();
    const state = setup(),
        auth = authorized();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
            Promise.resolve(jsonResponse(problemWire("HFAPI019", 20), 503)),
        );
    const pending = state.observer.observe(
        auth,
        new ApiClient({ scope, fetcher }),
    );
    await vi.advanceTimersByTimeAsync(0);
    state.observer.pause(auth.recordId, "offline");
    await pending;
    await vi.advanceTimersByTimeAsync(7000);
    expect(fetcher).toHaveBeenCalledOnce();
    expect(state.observer.snapshot(auth.recordId).pauseReason).toBe("offline");
    state.observer.dispose();
});

test("bounded observer entries preserve subscribed original handles and evict only inactive evidence", () => {
    const state = setup();
    const subscriptions = [];
    for (let i = 0; i < 32; i++)
        subscriptions.push(
            state.observer.subscribe("original-" + String(i), () => {}),
        );
    expect(() => state.observer.snapshot("overflow")).toThrow();
    subscriptions[0]?.();
    expect(state.observer.snapshot("overflow").phase).toBe("idle");
    expect(() => state.observer.snapshot("")).toThrow();
    const auth = authorized();
    expect(() =>
        state.observer.observe(
            { ...auth, recordId: "" },
            terminalClient().client,
        ),
    ).toThrow();
    expect(() =>
        state.observer.observe(
            { ...auth, target: { ...scope, subject: "other" } },
            terminalClient().client,
        ),
    ).toThrow();
    state.observer.dispose();
});

test("subscriber and classification callback failures retain original result as unknown", async () => {
    const state = setup({
            onResult: () => {
                throw new Error("private classifier detail");
            },
        }),
        auth = authorized();
    const listener = vi.fn();
    state.observer.subscribe(auth.recordId, () => {
        throw new Error("broken view");
    });
    state.observer.subscribe(auth.recordId, listener);
    await state.observer.observe(auth, terminalClient().client);
    expect(state.observer.snapshot(auth.recordId)).toMatchObject({
        phase: "unknown",
        pauseReason: "registry",
        result: { kind: "success" },
    });
    state.observer.clearPrivate();
    await Promise.resolve();
    expect(state.observer.snapshot(auth.recordId).result).toBeNull();
    expect(listener).toHaveBeenCalled();
    state.observer.dispose();
});
