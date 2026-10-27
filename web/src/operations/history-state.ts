/** Bounded, read-only history. Listing an ID never proves ownership of its key. */
import type { OriginalResultRead } from "../state/operation-observation";
import { canonicalHex } from "../api/identity";
import type { ReadResult } from "../api/types";
import type { QueryHandle, QuerySnapshot } from "../state/query-state";
import type { SessionController } from "../state/session-controller";
import type {
    ClientEvents,
    ClientOperation,
    EmptyPayload,
    OperationFailure,
    OperationPayload,
    OperationsPayload,
    OperationSuccess,
    ReportPayload,
    RunsPayload,
} from "../wire/generated";
import { WireError } from "../wire/json";

export const HISTORY_PAGE_SIZE = 25;
export const MAX_HISTORY_PAGES = 32;
export type HistoryPage<T, F = EmptyPayload> = QuerySnapshot<T, F>;
export type HistoryKind = "operations" | "runs";
export type HistoryNotice =
    | "authentication"
    | "page_limit"
    | "cursor_cycle"
    | "stale_cursor"
    | "capacity"
    | null;
export interface HistoryPagination {
    readonly pageIndex: number;
    readonly loadedExtent: number;
    readonly hasNext: boolean;
    readonly canPrevious: boolean;
}
export interface HistorySnapshot {
    readonly generation: number;
    readonly authGeneration: number;
    readonly connected: boolean;
    readonly notice: HistoryNotice;
    readonly operations: HistoryPage<OperationsPayload>;
    readonly runs: HistoryPage<RunsPayload>;
    readonly selectedOperationId: string | null;
    readonly selectedRunId: string | null;
    readonly operation: HistoryPage<OperationPayload>;
    readonly events: HistoryPage<ClientEvents>;
    readonly result: HistoryPage<OperationSuccess, OperationFailure>;
    readonly report: HistoryPage<ReportPayload>;
    readonly pagination: Readonly<Record<HistoryKind, HistoryPagination>>;
    readonly eventPages: number;
    readonly loadedEvents: number;
    readonly eventGaps: readonly {
        readonly from: number;
        readonly to: number;
    }[];
    readonly hasNextEvents: boolean;
}
type Controller = Pick<
    SessionController,
    "snapshot" | "subscribe" | "queries" | "apiReads" | "createPrivateSlot"
>;
interface Slot<S, F = EmptyPayload> {
    readonly handle: QueryHandle<S, F>;
    readonly unsubscribe: () => void;
}
interface Pager {
    cursors: (string | null)[];
    counts: number[];
    index: number;
}
const IDLE = Object.freeze({
    key: "",
    generation: 0,
    phase: "idle" as const,
    result: null,
    reason: null,
});
const pager = (): Pager => ({ cursors: [null], counts: [], index: 0 });
const ready = <S, F>(slot: Slot<S, F> | null): HistoryPage<S, F> =>
    slot?.handle.snapshot() ?? IDLE;
function payload<S, F>(slot: Slot<S, F> | null): S | null {
    const page = ready(slot);
    return page.phase === "ready" && page.result?.kind === "success"
        ? page.result.payload
        : null;
}
function drop<S, F>(slot: Slot<S, F> | null) {
    slot?.unsubscribe();
    slot?.handle.invalidate();
}
async function bounded<S>(
    read: Promise<ReadResult<S, EmptyPayload>>,
    count: (value: S) => number,
): Promise<ReadResult<S, EmptyPayload>> {
    const result = await read;
    return result.kind === "success" &&
        count(result.payload) > HISTORY_PAGE_SIZE
        ? { kind: "protocol_failure", reason: "bounds" }
        : result;
}

export function createHistoryStore(controller: Controller) {
    let authGeneration = controller.snapshot().generation;
    let connected = controller.snapshot().connection === "connected";
    let generation = 0,
        operationGeneration = 0,
        reportGeneration = 0,
        eventGeneration = 0;
    let disposed = false,
        notice: HistoryNotice = null;
    let selectedOperationId: string | null = null,
        selectedRunId: string | null = null;
    let operations: Slot<OperationsPayload> | null = null;
    let runs: Slot<RunsPayload> | null = null;
    let operation: Slot<OperationPayload> | null = null;
    let events: Slot<ClientEvents> | null = null;
    let result: Slot<OperationSuccess, OperationFailure> | null = null;
    let report: Slot<ReportPayload> | null = null;
    let positions = { operations: pager(), runs: pager() };
    let eventPages = 0,
        loadedEvents = 0,
        eventCursor = 0;
    let eventGaps: { from: number; to: number }[] = [];
    let eventPending: Promise<void> | null = null;
    let privateSlot = controller.createPrivateSlot();
    const listeners = new Set<() => void>();
    let snapshot: HistorySnapshot;
    function retain() {
        if (
            privateSlot.set({
                positions,
                eventPages,
                loadedEvents,
                eventCursor,
                eventGaps,
                selectedOperationId,
                selectedRunId,
            })
        )
            return true;
        notice = "capacity";
        return false;
    }
    function collection(
        kind: HistoryKind,
    ): HistoryPage<OperationsPayload | RunsPayload> {
        return kind === "operations" ? ready(operations) : ready(runs);
    }
    function pagination(kind: HistoryKind): HistoryPagination {
        const p = positions[kind];
        const state = collection(kind);
        const counts = p.counts.slice();
        if (state.phase === "ready" && state.result?.kind === "success") {
            const data = state.result.payload;
            // Query listeners publish ready before page() resumes its await.
            // Count the same ready rows even during that first notification.
            counts[p.index] =
                "operations" in data
                    ? data.operations.length
                    : data.runs.length;
        }
        return Object.freeze({
            pageIndex: p.index,
            loadedExtent: counts.reduce((sum, n) => sum + n, 0),
            canPrevious: p.index > 0,
            hasNext:
                state.phase === "ready" &&
                state.result?.kind === "success" &&
                state.result.response.next_cursor !== null,
        });
    }
    function publish() {
        if (disposed) return;
        const receipt = payload(operation)?.operation;
        snapshot = Object.freeze({
            generation,
            authGeneration,
            connected,
            notice,
            operations: ready(operations),
            runs: ready(runs),
            selectedOperationId,
            selectedRunId,
            operation: ready(operation),
            events: ready(events),
            result: ready(result),
            report: ready(report),
            pagination: Object.freeze({
                operations: pagination("operations"),
                runs: pagination("runs"),
            }),
            eventPages,
            loadedEvents,
            eventGaps: Object.freeze(
                eventGaps.map((row) => Object.freeze({ ...row })),
            ),
            hasNextEvents:
                eventPages > 0 &&
                eventPages < MAX_HISTORY_PAGES &&
                receipt !== undefined &&
                eventCursor < receipt.next_event_sequence - 1,
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* A detached view cannot strand reads. */
            }
        }
    }
    function attach<S, F>(handle: QueryHandle<S, F>): Slot<S, F> {
        return { handle, unsubscribe: handle.subscribe(publish) };
    }
    function clearSelection() {
        operationGeneration++;
        eventGeneration++;
        eventPending = null;
        reportGeneration++;
        drop(operation);
        drop(events);
        drop(result);
        drop(report);
        operation = events = result = report = null;
        selectedOperationId = selectedRunId = null;
        eventPages = loadedEvents = eventCursor = 0;
        eventGaps = [];
    }
    function clear() {
        generation++;
        clearSelection();
        drop(operations);
        drop(runs);
        operations = runs = null;
        positions = { operations: pager(), runs: pager() };
        privateSlot.clear();
    }
    async function page(kind: HistoryKind) {
        if (!connected || disposed) return;
        const own = generation,
            p = positions[kind],
            index = p.index;
        const cursor = p.cursors[index] ?? null;
        const query = {
            limit: HISTORY_PAGE_SIZE,
            ...(cursor === null ? {} : { cursor }),
        };
        const api = controller.apiReads;
        if (kind === "operations") {
            drop(operations);
            operations = attach(
                controller.queries.query(
                    { routeId: "operations_default", predicates: query },
                    (options) =>
                        bounded(
                            api.readOperations(query, options),
                            (value) => value.operations.length,
                        ),
                ),
            );
            await operations.handle.refresh();
        } else {
            drop(runs);
            runs = attach(
                controller.queries.query(
                    { routeId: "runs_default", predicates: query },
                    (options) =>
                        bounded(
                            api.readRuns(query, options),
                            (value) => value.runs.length,
                        ),
                ),
            );
            await runs.handle.refresh();
        }
        if (own !== generation || positions[kind] !== p || p.index !== index)
            return;
        const state = collection(kind);
        if (
            state.result?.kind === "api_problem" &&
            state.result.status === 409
        ) {
            positions[kind] = pager();
            notice = "stale_cursor";
        } else if (
            state.phase === "ready" &&
            state.result?.kind === "success"
        ) {
            const data = state.result.payload;
            p.counts[index] =
                "operations" in data
                    ? data.operations.length
                    : data.runs.length;
        }
        retain();
        publish();
    }
    async function move(kind: HistoryKind, direction: 1 | -1) {
        if (!connected || disposed) return;
        const p = positions[kind];
        const state = collection(kind);
        if (state.phase !== "ready" || state.result?.kind !== "success") return;
        if (direction === -1) {
            if (p.index === 0) return;
            p.index--;
        } else {
            const next = state.result.response.next_cursor;
            if (next === null) return;
            if (p.index + 1 >= MAX_HISTORY_PAGES) {
                notice = "page_limit";
                publish();
                return;
            }
            if (p.cursors.slice(0, p.index + 1).includes(next)) {
                notice = "cursor_cycle";
                publish();
                return;
            }
            if (p.cursors[p.index + 1] !== next) {
                p.cursors = p.cursors.slice(0, p.index + 1);
                p.counts = p.counts.slice(0, p.index + 1);
                p.cursors.push(next);
            }
            p.index++;
        }
        if (!retain()) {
            clear();
            notice = "capacity";
            publish();
            return;
        }
        notice = null;
        await page(kind);
    }
    async function loadEvents(receipt: ClientOperation, own: number) {
        if (eventPages >= MAX_HISTORY_PAGES) {
            notice = "page_limit";
            publish();
            return;
        }
        const ownEvent = ++eventGeneration;
        const after = eventCursor,
            api = controller.apiReads;
        drop(events);
        events = attach(
            controller.queries.query(
                {
                    routeId: "operation_events_default",
                    path: { operation_id: receipt.operation_id },
                    predicates: { after, limit: HISTORY_PAGE_SIZE },
                },
                (options) =>
                    bounded(
                        api.readOperationEvents(
                            receipt,
                            { after, limit: HISTORY_PAGE_SIZE },
                            options,
                        ),
                        (value) => value.events.length,
                    ),
            ),
        );
        await events.handle.refresh();
        if (own !== operationGeneration || ownEvent !== eventGeneration) return;
        const value = payload(events);
        if (value !== null) {
            if (value.oldest_sequence > after + 1)
                eventGaps.push({
                    from: after + 1,
                    to: value.oldest_sequence - 1,
                });
            loadedEvents += value.events.length;
            eventPages++;
            eventCursor = value.next_cursor;
            retain();
        }
        publish();
    }
    async function selectOperation(id: string | null) {
        if (id !== null && !canonicalHex(id, 32)) throw new WireError("schema");
        operationGeneration++;
        const own = operationGeneration;
        drop(operation);
        drop(events);
        drop(result);
        operation = events = result = null;
        selectedOperationId = id;
        eventPages = loadedEvents = eventCursor = 0;
        eventGaps = [];
        publish();
        if (id === null || !connected || disposed) return;
        if (!retain()) {
            selectedOperationId = null;
            publish();
            return;
        }
        const api = controller.apiReads;
        operation = attach(
            controller.queries.query(
                { routeId: "operation_default", path: { operation_id: id } },
                (options) => api.readOperation(id, options),
            ),
        );
        await operation.handle.refresh();
        if (own !== operationGeneration) return;
        const receipt = payload(operation)?.operation;
        if (receipt === undefined) return;
        await loadEvents(receipt, own);
        if (own !== operationGeneration) return;
        if (
            receipt.result_recorded &&
            ["succeeded", "failed"].includes(receipt.state)
        ) {
            result = attach(
                controller.queries.query(
                    {
                        routeId: "operation_result_by_original_operation",
                        path: { operation_id: id },
                    },
                    (options) => api.readOperationResult(receipt, options),
                ),
            );
            await result.handle.refresh();
        }
        if (own === operationGeneration) publish();
    }
    async function selectRun(id: string | null) {
        if (id !== null && !canonicalHex(id, 32)) throw new WireError("schema");
        reportGeneration++;
        const own = reportGeneration;
        drop(report);
        report = null;
        selectedRunId = id;
        publish();
        if (id === null || !connected || disposed) return;
        if (!retain()) {
            selectedRunId = null;
            publish();
            return;
        }
        const api = controller.apiReads;
        report = attach(
            controller.queries.query(
                { routeId: "report_default", path: { run_id: id } },
                (options) => api.readReport(id, options),
            ),
        );
        await report.handle.refresh();
        if (own === reportGeneration) publish();
    }
    const unsubscribe = controller.subscribe(() => {
        const next = controller.snapshot();
        if (
            next.generation !== authGeneration ||
            next.connection !== "connected"
        ) {
            clear();
            authGeneration = next.generation;
            privateSlot = controller.createPrivateSlot();
            notice = "authentication";
        }
        connected = next.connection === "connected";
        publish();
    });
    publish();
    return Object.freeze({
        snapshot: () => snapshot,
        subscribe(listener: () => void) {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        async refresh() {
            if (!connected || disposed) return;
            generation++;
            notice = null;
            positions = { operations: pager(), runs: pager() };
            const own = generation;
            await page("operations");
            if (own !== generation) return;
            await page("runs");
        },
        nextPage: (kind: HistoryKind) => move(kind, 1),
        previousPage: (kind: HistoryKind) => move(kind, -1),
        selectOperation,
        selectRun,
        async nextEventsPage() {
            if (eventPending !== null) return eventPending;
            const receipt = payload(operation)?.operation;
            if (receipt === undefined || !snapshot.hasNextEvents) return;
            const work = loadEvents(receipt, operationGeneration);
            eventPending = work;
            try {
                await work;
            } finally {
                if (eventPending === work) eventPending = null;
            }
        },
        pause() {
            clear();
            publish();
        },
        dispose() {
            clear();
            disposed = true;
            unsubscribe();
            listeners.clear();
        },
    });
}
export type HistoryStore = ReturnType<typeof createHistoryStore>;

export type ResultClassification =
    | "success"
    | "warning"
    | "busy"
    | "validation"
    | "preflight"
    | "partial"
    | "integrity"
    | "unsupported"
    | "failed"
    | "unknown";
export function classifyOperationResult(
    result: OriginalResultRead | null,
): ResultClassification {
    if (
        result === null ||
        (result.kind !== "success" && result.kind !== "domain_failure")
    )
        return "unknown";
    const envelope = result.response.envelope;
    if (envelope.errors.some((row) => row.code === "HFMNT010")) return "busy";
    switch (envelope.exit_code) {
        case 0:
            return envelope.outcome === "success_with_warnings"
                ? "warning"
                : "success";
        case 10:
            return "validation";
        case 20:
            return "preflight";
        case 30:
            return "partial";
        case 40:
            return "integrity";
        case 50:
            return "unsupported";
        default:
            return "failed";
    }
}
