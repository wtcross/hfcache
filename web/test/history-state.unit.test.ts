import { isRecord } from "../src/wire/runtime";
/** Real ApiClient + shared query owner; owned HTTP literals are not executor acceptance. */
import { afterEach, expect, test, vi } from "vitest";
import { readFileSync } from "node:fs";
import {
    createHistoryStore,
    MAX_HISTORY_PAGES,
} from "../src/operations/history-state";
import { createSessionController } from "../src/state/session-controller";
import { uiBootstrapFixture } from "./ui-fixtures";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import {
    receipt,
    terminal,
    events,
    deferred,
    operationResponse,
    resultResponse,
    OPERATION_ID,
} from "./state-fixtures";

const cleanups: (() => void)[] = [];
afterEach(() => {
    cleanups
        .splice(0)
        .reverse()
        .forEach((fn) => {
            fn();
        });
    vi.unstubAllGlobals();
});
const reportValue: unknown = JSON.parse(
    readFileSync(
        new URL(
            "../../tests/fixtures/schemas/run-report.json",
            import.meta.url,
        ),
        "utf8",
    ),
);
if (!isRecord(reportValue)) throw new Error("Invalid owned report fixture");
const report = reportValue;
const runId = String(report.run_id);
function wire(command: string, data: unknown, cursor: string | null = null) {
    return { ...operationResponse(command, data), next_cursor: cursor };
}
function urlOf(input: RequestInfo | URL): URL {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    );
}
function setup(
    router: (
        url: URL,
        init: RequestInit | undefined,
    ) => Response | Promise<Response>,
) {
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal("location", new URL(bootstrap.configured_origin));
    const fetcher = vi.fn<typeof fetch>((input, init) =>
        Promise.resolve(router(urlOf(input), init)),
    );
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: null,
        reconnect: () =>
            Promise.resolve({
                ...bootstrap,
                authority_epoch: "f".repeat(32),
                instance_id: "e".repeat(32),
            }),
    });
    const store = createHistoryStore(controller);
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    return { store, controller, fetcher };
}
const empty = (url: URL) =>
    jsonResponse(
        wire(
            url.pathname.endsWith("/runs") ? "runs" : "operations list",
            url.pathname.endsWith("/runs") ? { runs: [] } : { operations: [] },
        ),
    );

test("refresh requests exactly two finite GET pages without importing IDs or creating a recovery record", async () => {
    const { store, controller, fetcher } = setup((url) => empty(url));
    await store.refresh();
    expect(fetcher.mock.calls.map(([url]) => urlOf(url).pathname)).toEqual([
        "/api/v1/operations",
        "/api/v1/runs",
    ]);
    for (const [url, init] of fetcher.mock.calls) {
        expect(urlOf(url).searchParams.get("limit")).toBe("25");
        expect(init?.method).toBe("GET");
    }
    expect(store.snapshot().pagination.operations.loadedExtent).toBe(0);
    expect(store.snapshot().operations.phase).toBe("ready");
    expect(controller.snapshot().registry.records).toEqual([]);
});

test("next and previous replace the visible page and retain only known loaded extent", async () => {
    const { store, fetcher } = setup((url) =>
        url.pathname.endsWith("/runs")
            ? empty(url)
            : jsonResponse(
                  wire(
                      "operations list",
                      {
                          operations: [
                              receipt({
                                  operation_id: url.searchParams.has("cursor")
                                      ? "b".repeat(32)
                                      : OPERATION_ID,
                              }),
                          ],
                      },
                      url.searchParams.has("cursor") ? null : "owned-next",
                  ),
              ),
    );
    await store.refresh();
    await store.nextPage("operations");
    expect(store.snapshot().pagination.operations).toEqual({
        pageIndex: 1,
        loadedExtent: 2,
        hasNext: false,
        canPrevious: true,
    });
    const selected = store.snapshot().operations.result;
    expect(
        selected?.kind === "success"
            ? selected.payload.operations[0]?.operation_id
            : null,
    ).toBe("b".repeat(32));
    await store.previousPage("operations");
    expect(store.snapshot().pagination.operations.pageIndex).toBe(0);
    expect(store.snapshot().pagination.operations.loadedExtent).toBe(2);
    expect(fetcher).toHaveBeenCalledTimes(4);
});

test("every published ready history page includes its rows in the known loaded extent", async () => {
    let refreshed = false;
    const { store, fetcher } = setup((url) => {
        const runs = url.pathname.endsWith("/runs"),
            next = url.searchParams.has("cursor");
        const count = refreshed
            ? runs
                ? 1
                : 2
            : next
              ? runs
                  ? 3
                  : 1
              : runs
                ? 2
                : 3;
        const ids = Array.from({ length: count }, (_, index) =>
            (index + (next ? 10 : 1)).toString(16).padStart(32, "0"),
        );
        return jsonResponse(
            wire(
                runs ? "runs" : "operations list",
                runs
                    ? { runs: ids }
                    : {
                          operations: ids.map((operation_id) =>
                              receipt({ operation_id }),
                          ),
                      },
                next || refreshed ? null : "owned-next",
            ),
        );
    });
    const seen = new Map<string, Map<number, number>>();
    const published: {
        kind: "operations" | "runs";
        stage: string;
        page: number;
        rows: number;
        actual: number;
        expected: number;
    }[] = [];
    let stage = "first";
    store.subscribe(() => {
        const snapshot = store.snapshot();
        for (const kind of ["operations", "runs"] as const) {
            const read = snapshot[kind];
            if (read.phase !== "ready" || read.result?.kind !== "success")
                continue;
            const data = read.result.payload;
            const rows =
                "operations" in data
                    ? data.operations.length
                    : data.runs.length;
            const page = snapshot.pagination[kind];
            const key = String(snapshot.generation) + ":" + kind;
            const counts = seen.get(key) ?? new Map<number, number>();
            counts.set(page.pageIndex, rows);
            seen.set(key, counts);
            published.push({
                kind,
                stage,
                page: page.pageIndex,
                rows,
                actual: page.loadedExtent,
                expected: [...counts.values()].reduce(
                    (sum, count) => sum + count,
                    0,
                ),
            });
        }
    });
    await store.refresh();
    stage = "next";
    await store.nextPage("operations");
    await store.nextPage("runs");
    stage = "previous";
    await store.previousPage("operations");
    await store.previousPage("runs");
    stage = "refresh";
    refreshed = true;
    await store.refresh();
    // Assertions happen outside the subscriber: view-listener exceptions are
    // intentionally isolated and must not hide this regression.
    for (const sample of published) {
        expect(sample.actual, JSON.stringify(sample)).toBeGreaterThanOrEqual(
            sample.rows,
        );
        expect(sample.actual, JSON.stringify(sample)).toBe(sample.expected);
    }
    for (const [kind, first, total, reset] of [
        ["operations", 3, 4, 2],
        ["runs", 2, 5, 1],
    ] as const) {
        expect(published).toContainEqual(
            expect.objectContaining({
                kind,
                stage: "first",
                page: 0,
                actual: first,
            }),
        );
        expect(published).toContainEqual(
            expect.objectContaining({
                kind,
                stage: "next",
                page: 1,
                actual: total,
            }),
        );
        expect(published).toContainEqual(
            expect.objectContaining({
                kind,
                stage: "previous",
                page: 0,
                actual: total,
            }),
        );
        expect(published).toContainEqual(
            expect.objectContaining({
                kind,
                stage: "refresh",
                page: 0,
                actual: reset,
            }),
        );
    }
    expect(fetcher).toHaveBeenCalledTimes(8);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});

test("server pages beyond the requested25 are protocol failures, never ready history", async () => {
    const { store } = setup((url) =>
        url.pathname.endsWith("/runs")
            ? empty(url)
            : jsonResponse(
                  wire("operations list", {
                      operations: Array.from({ length: 26 }, (_, n) =>
                          receipt({
                              operation_id: n.toString(16).padStart(32, "0"),
                          }),
                      ),
                  }),
              ),
    );
    await store.refresh();
    expect(store.snapshot().operations.result).toEqual({
        kind: "protocol_failure",
        reason: "bounds",
    });
    expect(store.snapshot().pagination.operations.loadedExtent).toBe(0);
});

test("repeated cursor stops without a hidden walk", async () => {
    const { store, fetcher } = setup((url) =>
        url.pathname.endsWith("/runs")
            ? empty(url)
            : jsonResponse(wire("operations list", { operations: [] }, "same")),
    );
    await store.refresh();
    await store.nextPage("operations");
    await store.nextPage("operations");
    expect(store.snapshot().notice).toBe("cursor_cycle");
    expect(fetcher).toHaveBeenCalledTimes(3);
});

test("cursor history stops at32 positions, independent of a server claiming more", async () => {
    let sequence = 0;
    const { store, fetcher } = setup((url) =>
        url.pathname.endsWith("/runs")
            ? empty(url)
            : jsonResponse(
                  wire(
                      "operations list",
                      { operations: [] },
                      "page-" + String(++sequence),
                  ),
              ),
    );
    await store.refresh();
    for (let i = 0; i < MAX_HISTORY_PAGES; i++)
        await store.nextPage("operations");
    expect(store.snapshot().notice).toBe("page_limit");
    expect(fetcher).toHaveBeenCalledTimes(MAX_HISTORY_PAGES + 1);
});

test("409 continuation remains a visible failed read until explicit refresh, with no automatic retry", async () => {
    const { store, fetcher } = setup((url) =>
        url.searchParams.has("cursor")
            ? jsonResponse(problemWire("HFAPI006"), 409)
            : url.pathname.endsWith("/runs")
              ? empty(url)
              : jsonResponse(
                    wire("operations list", { operations: [] }, "old"),
                ),
    );
    await store.refresh();
    await store.nextPage("operations");
    expect(store.snapshot().notice).toBe("stale_cursor");
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(store.snapshot().operations.result?.kind).toBe("api_problem");
    await store.nextPage("operations");
    expect(fetcher).toHaveBeenCalledTimes(3);
    await store.refresh();
    expect(fetcher).toHaveBeenCalledTimes(5);
    expect(store.snapshot().notice).toBe(null);
});

test("selected recorded original result and events use exact operation identity and no key claim", async () => {
    const { store, controller, fetcher } = setup((url) =>
        jsonResponse(
            url.pathname.endsWith("/events")
                ? wire("operations events", events([]))
                : url.pathname.endsWith("/result")
                  ? resultResponse()
                  : wire("operations show", { operation: terminal() }),
        ),
    );
    await store.selectOperation(OPERATION_ID);
    expect(fetcher.mock.calls.map(([url]) => urlOf(url).pathname)).toEqual([
        "/api/v1/operations/" + OPERATION_ID,
        "/api/v1/operations/" + OPERATION_ID + "/events",
        "/api/v1/operations/" + OPERATION_ID + "/result",
    ]);
    expect(store.snapshot().result.result?.kind).toBe("success");
    expect(controller.snapshot().registry.records).toEqual([]);
});

test.each(["queued", "waiting_lock", "running", "interrupted"] as const)(
    "%s receipt is not presented as a completed result",
    async (state) => {
        const row = receipt({
            state,
            updated_at: "2026-10-20T12:00:03.000000Z",
            completed_at:
                state === "interrupted" ? "2026-10-20T12:00:02.000000Z" : null,
            domain_run_id: state === "queued" ? null : "3".repeat(32),
        });
        const { store, fetcher } = setup((url) =>
            jsonResponse(
                url.pathname.endsWith("/events")
                    ? wire("operations events", events([]))
                    : wire("operations show", { operation: row }),
            ),
        );
        await store.selectOperation(OPERATION_ID);
        expect(store.snapshot().result.result).toBe(null);
        expect(fetcher).toHaveBeenCalledTimes(2);
    },
);

test("event continuation preserves dropped-prefix gaps and loads only an explicit next25", async () => {
    const { store, fetcher } = setup((url) =>
        jsonResponse(
            url.pathname.endsWith("/events")
                ? wire(
                      "operations events",
                      events(
                          url.searchParams.get("after") === "0" ? [3, 4] : [5],
                          {
                              oldest_sequence: 3,
                              truncated: url.searchParams.get("after") === "0",
                          },
                      ),
                  )
                : wire("operations show", {
                      operation: receipt({ next_event_sequence: 6 }),
                  }),
        ),
    );
    await store.selectOperation(OPERATION_ID);
    expect(store.snapshot().eventGaps).toEqual([{ from: 1, to: 2 }]);
    expect(store.snapshot().hasNextEvents).toBe(true);
    await store.nextEventsPage();
    expect(store.snapshot().loadedEvents).toBe(3);
    expect(store.snapshot().eventPages).toBe(2);
    expect(store.snapshot().hasNextEvents).toBe(false);
    expect(fetcher).toHaveBeenCalledTimes(3);
});

test("a late replaced selection cannot publish the old receipt or start its events/result readers", async () => {
    const slow = deferred<Response>();
    const { store, fetcher } = setup((url) =>
        url.pathname.endsWith(OPERATION_ID)
            ? slow.promise
            : Promise.resolve(
                  jsonResponse(
                      wire("operations show", {
                          operation: receipt({ operation_id: "b".repeat(32) }),
                      }),
                  ),
              ),
    );
    const old = store.selectOperation(OPERATION_ID);
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(1);
    });
    await store.selectOperation(null);
    slow.resolve(
        jsonResponse(wire("operations show", { operation: terminal() })),
    );
    await old;
    expect(store.snapshot().selectedOperationId).toBe(null);
    expect(store.snapshot().operation.result).toBe(null);
    expect(fetcher).toHaveBeenCalledTimes(1);
});

test("pause during the first collection read prevents a late second GET", async () => {
    const slow = deferred<Response>();
    const { store, fetcher } = setup(() => slow.promise);
    const loading = store.refresh();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(1);
    });
    store.pause();
    slow.resolve(empty(new URL("https://owned.invalid/operations")));
    await loading;
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(store.snapshot().operations.result).toBe(null);
});

test("reconnect clears all private selected history and old read handles", async () => {
    const { store, controller, fetcher } = setup((url) => empty(url));
    await store.refresh();
    await controller.reconnect();
    expect(store.snapshot().operations.result).toBe(null);
    expect(store.snapshot().notice).toBe("authentication");
    expect(fetcher).toHaveBeenCalledTimes(2);
});

test("exact report reads bind current read metadata while retaining historical report policy", async () => {
    const { store } = setup(() =>
        jsonResponse({
            ...wire("runs read", { report }),
            config_fingerprint: "2".repeat(64),
            envelope: {
                ...wire("runs read", { report }).envelope,
                run_id: runId,
            },
        }),
    );
    await store.selectRun(runId);
    expect(store.snapshot().report.result?.kind).toBe("success");
});

test.each(["run", "archive"])(
    "report %s mismatch is refused without fallback",
    async (mismatch) => {
        const changed = {
            ...report,
            ...(mismatch === "run"
                ? { run_id: "f".repeat(32) }
                : { archive_id: "6d4da06d-6b0c-4c21-8e45-1fffa19db1e6" }),
        };
        const { store, fetcher } = setup(() =>
            jsonResponse({
                ...wire("runs read", { report: changed }),
                config_fingerprint: "2".repeat(64),
                envelope: {
                    ...wire("runs read", { report: changed }).envelope,
                    run_id: runId,
                },
            }),
        );
        await store.selectRun(runId);
        expect(store.snapshot().report.result?.kind).toBe("protocol_failure");
        expect(fetcher).toHaveBeenCalledTimes(1);
    },
);

test("missing stored result preserves history failure instead of inventing success", async () => {
    const { store } = setup((url) =>
        url.pathname.endsWith("/result")
            ? jsonResponse(problemWire("HFAPI003"), 404)
            : jsonResponse(
                  url.pathname.endsWith("/events")
                      ? wire("operations events", events([]))
                      : wire("operations show", { operation: terminal() }),
              ),
    );
    await store.selectOperation(OPERATION_ID);
    expect(store.snapshot().result.result?.kind).toBe("api_problem");
});

test("malformed IDs fail before any request and disposal permits no further readers", async () => {
    const { store, fetcher } = setup((url) => empty(url));
    await expect(store.selectRun("../escape")).rejects.toThrow();
    await expect(store.selectOperation("f".repeat(31))).rejects.toThrow();
    store.dispose();
    await store.refresh();
    expect(fetcher).not.toHaveBeenCalled();
});

test("event-read failure cannot substitute for or suppress a recorded exact command result", async () => {
    const { store } = setup((url) =>
        url.pathname.endsWith("/events")
            ? jsonResponse(problemWire("HFAPI016", 20), 503)
            : jsonResponse(
                  url.pathname.endsWith("/result")
                      ? resultResponse()
                      : wire("operations show", { operation: terminal() }),
              ),
    );
    await store.selectOperation(OPERATION_ID);
    expect(store.snapshot().events.result?.kind).toBe("api_problem");
    expect(store.snapshot().result.result?.kind).toBe("success");
});

test("shared private-capacity refusal prevents history transmission without evicting private owners", async () => {
    const { store, controller, fetcher } = setup((url) => empty(url));
    const slots = Array.from({ length: 4 }, () =>
        controller.createPrivateSlot(),
    );
    for (const slot of slots)
        expect(slot.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    await store.refresh();
    expect(fetcher).not.toHaveBeenCalled();
    expect(store.snapshot().notice).toBe("capacity");
    for (const slot of slots) slot.clear();
    await store.refresh();
    expect(store.snapshot().operations.phase).toBe("ready");
});

test("a detached throwing subscriber cannot suppress other view notifications or report reads", async () => {
    const { store } = setup(() =>
        jsonResponse({
            ...wire("runs read", { report }),
            config_fingerprint: "2".repeat(64),
            envelope: {
                ...wire("runs read", { report }).envelope,
                run_id: runId,
            },
        }),
    );
    const heard = vi.fn();
    store.subscribe(() => {
        throw new Error("detached");
    });
    store.subscribe(heard);
    await store.selectRun(runId);
    expect(heard).toHaveBeenCalled();
    expect(store.snapshot().report.phase).toBe("ready");
    await store.selectRun(null);
    expect(store.snapshot().report.result).toBe(null);
});

test("overlapping event continuation coalesces one read and accounts each sequence once", async () => {
    const slow = deferred<Response>();
    let continuations = 0;
    const { store } = setup((url) => {
        if (!url.pathname.endsWith("/events"))
            return jsonResponse(
                wire("operations show", {
                    operation: receipt({ next_event_sequence: 4 }),
                }),
            );
        const after = url.searchParams.get("after");
        if (after === "0")
            return jsonResponse(wire("operations events", events([1])));
        continuations++;
        return continuations === 1
            ? slow.promise
            : jsonResponse(wire("operations events", events([2, 3])));
    });
    await store.selectOperation(OPERATION_ID);
    const first = store.nextEventsPage();
    await vi.waitFor(() => {
        expect(continuations).toBe(1);
    });
    expect(store.snapshot().hasNextEvents).toBe(true);
    expect(store.snapshot().operation.phase).toBe("ready");
    const second = store.nextEventsPage();
    expect(continuations).toBe(1);
    slow.resolve(jsonResponse(wire("operations events", events([2, 3]))));
    await Promise.all([first, second]);
    expect(store.snapshot().events.result).toMatchObject({ kind: "success" });
    expect(store.snapshot().loadedEvents).toBe(3);
    expect(store.snapshot().eventPages).toBe(2);
});
