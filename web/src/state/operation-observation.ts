/** WEB011: finite GET-only observation; registry/controller owns namespace and effect certainty. */
import type { ApiClient } from "../api/client";
import type { ReadResult } from "../api/types";
import { validateOperationTransition } from "../api/bindings";
import type {
    ClientEvent,
    ClientEvents,
    ClientOperation,
} from "../wire/generated";
import { WireError } from "../wire/json";
import {
    createAuthSession,
    sameApiScope,
    receiptIdentity,
    sameReceiptIdentity,
} from "./authority";
import type { AuthorizedObservation, RecordId } from "./authority";
import {
    encodedBytes,
    logicalReadEvidence,
    READ_RESERVATION_BYTES,
    SESSION_RESPONSE_BYTES,
    StateCapacityError,
} from "./retention-budget";
import type { ReadCoordinator, RetentionBudget } from "./retention-budget";

export type OperationReadPort = Pick<
    ApiClient,
    | "scope"
    | "lookupOperation"
    | "readOperation"
    | "readOperationEvents"
    | "readOperationResult"
>;
export type OriginalResultRead = Awaited<
    ReturnType<ApiClient["readOperationResult"]>
>;
export type ObservationFailure = Exclude<
    ReadResult<unknown, unknown>,
    { readonly kind: "success" }
>;
export type PauseReason =
    | "user"
    | "hidden"
    | "offline"
    | "authentication"
    | "session_limit"
    | "retry_limit"
    | "capacity"
    | "scope"
    | "protocol"
    | "history_missing"
    | "result_unknown"
    | "unknown_effects"
    | "interrupted"
    | "registry";
export interface EventGap {
    readonly from: number;
    readonly to: number;
    readonly reason: "server_retention" | "local_limit";
}
export interface EventWindow {
    readonly rows: readonly ClientEvent[];
    readonly cursor: number;
    readonly gaps: readonly EventGap[];
    readonly omitted: number;
}
export interface ObservationSnapshot {
    readonly recordId: RecordId;
    readonly generation: number;
    readonly phase: "idle" | "observing" | "paused" | "unknown" | "settled";
    readonly receipt: ClientOperation | null;
    readonly result: OriginalResultRead | null;
    readonly failure: ObservationFailure | null;
    readonly events: EventWindow;
    readonly pauseReason: PauseReason | null;
}
export interface OperationObserverOptions {
    readonly retention: RetentionBudget;
    readonly reads: ReadCoordinator;
    readonly onReceipt: (
        auth: AuthorizedObservation,
        receipt: ClientOperation,
    ) => AuthorizedObservation | null;
    readonly onResult: (
        auth: AuthorizedObservation,
        receipt: ClientOperation,
        result: OriginalResultRead,
    ) => "known" | "unknown-effects" | Promise<"known" | "unknown-effects">;
    readonly onUnauthorized: () => void;
    readonly clock?: () => number;
}
const EMPTY_EVENTS: EventWindow = Object.freeze({
    rows: Object.freeze([]),
    cursor: 0,
    gaps: Object.freeze([]),
    omitted: 0,
});

/** Retain no unbounded event detail and never turn missing/contradictory sequences into progress. */
export function mergeEventWindow(
    previous: EventWindow,
    reply: ClientEvents,
    operationId: string,
): EventWindow {
    if (
        reply.operation_id !== operationId ||
        reply.next_cursor < previous.cursor
    )
        throw new WireError("semantic");
    const rows = [...previous.rows],
        gaps = [...previous.gaps];
    let omitted = previous.omitted;
    const addGap = (gap: EventGap) => {
        gaps.push(Object.freeze(gap));
        if (gaps.length > 32) gaps.shift();
    };
    if (reply.truncated && reply.oldest_sequence > previous.cursor + 1)
        addGap({
            from: previous.cursor + 1,
            to: reply.oldest_sequence - 1,
            reason: "server_retention",
        });
    for (const event of reply.events) {
        if (event.sequence <= previous.cursor) {
            const prior = rows.find((row) => row.sequence === event.sequence);
            if (
                prior === undefined ||
                JSON.stringify(prior) !== JSON.stringify(event)
            )
                throw new WireError("semantic");
            continue;
        }
        if (encodedBytes(event) > 64 * 1024) {
            omitted++;
            addGap({
                from: event.sequence,
                to: event.sequence,
                reason: "local_limit",
            });
            continue;
        }
        rows.push(event);
        while (rows.length > 32 || encodedBytes(rows) > 64 * 1024) {
            rows.shift();
            omitted++;
        }
    }
    return Object.freeze({
        rows: Object.freeze(rows),
        cursor: reply.next_cursor,
        gaps: Object.freeze(gaps),
        omitted,
    });
}

function sleep(milliseconds: number, signal: AbortSignal): Promise<void> {
    if (signal.aborted)
        return Promise.reject(
            new DOMException("Observation stopped.", "AbortError"),
        );
    return new Promise((resolve, reject) => {
        const abort = () => {
            clearTimeout(timer);
            reject(new DOMException("Observation stopped.", "AbortError"));
        };
        const timer = setTimeout(() => {
            signal.removeEventListener("abort", abort);
            resolve();
        }, milliseconds);
        signal.addEventListener("abort", abort, { once: true });
    });
}
function retryable(result: ReadResult<unknown, unknown>): boolean {
    return (
        result.kind === "transport_failure" ||
        (result.kind === "api_problem" &&
            (result.status === 429 || result.status >= 500))
    );
}
function validateAuthorization(
    auth: AuthorizedObservation,
): AuthorizedObservation {
    const session = createAuthSession({
        scope: auth.target,
        authGeneration: auth.authGeneration,
    });
    if (auth.recordId.length < 1 || auth.recordId.length > 128)
        throw new WireError("schema");
    if (!sameApiScope(session.scope, auth.target))
        throw new WireError("semantic");
    // Registry-issued frozen objects are opaque local authorizations. Preserve
    // identity for observed()/resolved(); never mint a substitute local token.
    return auth;
}
interface Entry {
    readonly owner: string;
    readonly listeners: Set<() => void>;
    snapshot: ObservationSnapshot;
    generation: number;
    abort: AbortController | null;
    authorization: AuthorizedObservation | null;
    promise: Promise<void> | null;
}
let nextObserver = 0;

export function createOperationObserver(options: OperationObserverOptions) {
    const name = "observer:" + String(++nextObserver);
    const entries = new Map<RecordId, Entry>();
    const clock = options.clock ?? (() => performance.now());
    let disposed = false;
    let hidden = false;
    let clearing = false;
    const notifications = new Set<Entry>();
    let notificationQueued = false;
    function notifyListeners(entry: Entry) {
        for (const listener of entry.listeners) {
            try {
                listener();
            } catch {
                // A view failure must not interrupt other private-state updates.
            }
        }
    }
    function notify(entry: Entry) {
        if (!clearing) {
            notifyListeners(entry);
            return;
        }
        notifications.add(entry);
        if (!notificationQueued) {
            notificationQueued = true;
            queueMicrotask(() => {
                notificationQueued = false;
                const pending = [...notifications];
                notifications.clear();
                for (const item of pending) notifyListeners(item);
            });
        }
    }
    function publish(
        entry: Entry,
        patch: Partial<ObservationSnapshot>,
    ): boolean {
        let next = Object.freeze({
            ...entry.snapshot,
            ...patch,
            generation: entry.generation,
        });
        const bytes = encodedBytes({
            receipt: next.receipt,
            events: next.events,
            result:
                next.result === null ? null : logicalReadEvidence(next.result),
            failure:
                next.failure === null
                    ? null
                    : logicalReadEvidence(next.failure),
        });
        const retained = options.retention.claim(entry.owner, bytes);
        if (!retained) {
            options.retention.release(entry.owner);
            next = Object.freeze({
                ...next,
                phase: "unknown",
                pauseReason: "capacity",
                receipt: null,
                result: null,
                failure: null,
                events: EMPTY_EVENTS,
            });
        }
        entry.snapshot = next;
        notify(entry);
        return retained;
    }
    function pauseEntry(entry: Entry, reason: PauseReason, clear = false) {
        entry.generation++;
        entry.abort?.abort();
        entry.abort = null;
        entry.promise = null;
        if (clear) {
            entry.authorization = null;
            options.retention.release(entry.owner);
            entry.snapshot = Object.freeze({
                recordId: entry.snapshot.recordId,
                generation: entry.generation,
                phase: "paused",
                receipt: null,
                result: null,
                failure: null,
                events: EMPTY_EVENTS,
                pauseReason: reason,
            });
            notify(entry);
        } else publish(entry, { phase: "paused", pauseReason: reason });
    }
    function get(id: RecordId): Entry {
        const previous = entries.get(id);
        if (previous !== undefined) return previous;
        if (disposed || id.length < 1 || id.length > 128)
            throw new StateCapacityError();
        if (entries.size >= 32) {
            const inactive = [...entries.values()].find(
                (entry) => entry.listeners.size === 0 && entry.abort === null,
            );
            if (inactive === undefined) throw new StateCapacityError();
            pauseEntry(inactive, "user", true);
            entries.delete(inactive.snapshot.recordId);
        }
        const entry: Entry = {
            owner: name + ":" + id,
            listeners: new Set(),
            generation: 0,
            abort: null,
            authorization: null,
            promise: null,
            snapshot: Object.freeze({
                recordId: id,
                generation: 0,
                phase: "idle",
                receipt: null,
                result: null,
                failure: null,
                events: EMPTY_EVENTS,
                pauseReason: null,
            }),
        };
        entries.set(id, entry);
        return entry;
    }
    function clearPrivate() {
        const previous = clearing;
        clearing = true;
        try {
            for (const entry of entries.values())
                pauseEntry(entry, "authentication", true);
        } finally {
            clearing = previous;
        }
    }

    return Object.freeze({
        snapshot: (id: RecordId) => get(id).snapshot,
        subscribe(id: RecordId, listener: () => void) {
            const entry = get(id);
            entry.listeners.add(listener);
            return () => {
                entry.listeners.delete(listener);
            };
        },
        pause(id: RecordId, reason: PauseReason = "user") {
            pauseEntry(get(id), reason);
        },
        setHidden(value: boolean) {
            if (disposed || hidden === value) return;
            hidden = value;
            if (hidden)
                for (const entry of entries.values())
                    if (entry.abort !== null) pauseEntry(entry, "hidden");
        },
        clearPrivate,
        observe(
            authorization: AuthorizedObservation,
            client: OperationReadPort,
        ): Promise<void> {
            if (disposed) throw new StateCapacityError();
            let auth = validateAuthorization(authorization);
            if (!sameApiScope(auth.target, client.scope))
                throw new WireError("semantic");
            const entry = get(auth.recordId);
            const same =
                entry.authorization !== null &&
                entry.authorization.authGeneration === auth.authGeneration &&
                sameApiScope(entry.authorization.target, auth.target);
            if (hidden) {
                pauseEntry(entry, "hidden", !same);
                return Promise.resolve();
            }
            pauseEntry(entry, "user", !same);
            const generation = ++entry.generation;
            const abort = new AbortController();
            entry.abort = abort;
            entry.authorization = auth;
            const started = clock();
            let reads = 0;
            const live = () =>
                !disposed &&
                !hidden &&
                generation === entry.generation &&
                !abort.signal.aborted;
            const deadline = setTimeout(
                () => {
                    if (live()) pauseEntry(entry, "session_limit");
                },
                5 * 60 * 1000,
            );
            const clearDeadline = () => {
                clearTimeout(deadline);
            };
            abort.signal.addEventListener("abort", clearDeadline, {
                once: true,
            });
            function stop(
                reason: PauseReason,
                failure: ObservationFailure | null = null,
            ) {
                if (live())
                    publish(entry, {
                        phase: "unknown",
                        pauseReason: reason,
                        failure,
                    });
            }
            async function read<T extends ReadResult<unknown, unknown>>(
                call: () => Promise<T>,
            ): Promise<T | null> {
                for (let retry = 0; retry <= 3; retry++) {
                    if (!live()) return null;
                    if (clock() - started >= 5 * 60 * 1000) {
                        pauseEntry(entry, "session_limit");
                        return null;
                    }
                    const reservation =
                        entry.owner +
                        ":pending:" +
                        String(generation) +
                        ":" +
                        String(++reads);
                    if (
                        !options.retention.claim(
                            reservation,
                            READ_RESERVATION_BYTES,
                        )
                    ) {
                        stop("capacity");
                        return null;
                    }
                    let result: T;
                    try {
                        result = await options.reads.run(
                            entry.owner,
                            abort.signal,
                            call,
                        );
                    } catch (error) {
                        if (!live()) return null;
                        if (error instanceof StateCapacityError) {
                            stop("capacity");
                            return null;
                        }
                        stop("protocol");
                        return null;
                    } finally {
                        options.retention.release(reservation);
                    }
                    if (!live()) return null;
                    if (
                        result.kind === "api_problem" &&
                        result.status === 401
                    ) {
                        clearPrivate();
                        options.onUnauthorized();
                        return null;
                    }
                    if (!retryable(result) || result.kind === "success")
                        return result;
                    if (
                        !publish(entry, { failure: result, phase: "observing" })
                    )
                        return null;
                    if (retry === 3) {
                        stop("retry_limit", result);
                        return null;
                    }
                    await sleep(1000 * 2 ** retry, abort.signal);
                }
                return null;
            }
            const requestOptions = {
                signal: abort.signal,
                responseByteLimit: SESSION_RESPONSE_BYTES,
            };
            const work = async () => {
                try {
                    if (
                        !publish(entry, {
                            phase: "observing",
                            pauseReason: null,
                            failure: null,
                            result: null,
                        })
                    )
                        return;
                    for (let cycle = 0; cycle < 120 && live(); cycle++) {
                        const status = await read(() =>
                            auth.locator.kind === "key"
                                ? client.lookupOperation(
                                      auth.locator.key,
                                      requestOptions,
                                  )
                                : client.readOperation(
                                      auth.locator.operationId,
                                      requestOptions,
                                  ),
                        );
                        if (status === null) return;
                        if (status.kind !== "success") {
                            stop(
                                status.kind === "api_problem" &&
                                    status.status === 404
                                    ? "history_missing"
                                    : "protocol",
                                status,
                            );
                            return;
                        }
                        const receipt = status.payload.operation;
                        if (
                            auth.expectedSafeReceiptIdentity !== null &&
                            !sameReceiptIdentity(
                                auth.expectedSafeReceiptIdentity,
                                receiptIdentity(receipt),
                            )
                        )
                            throw new WireError("semantic");
                        validateOperationTransition(
                            entry.snapshot.receipt ?? undefined,
                            receipt,
                        );
                        if (!publish(entry, { receipt, failure: null })) return;
                        if (!live()) return;
                        const next = options.onReceipt(auth, receipt);
                        if (!live()) return;
                        if (next === null) {
                            stop("scope");
                            return;
                        }
                        const nextAuth = validateAuthorization(next);
                        if (
                            nextAuth.recordId !== auth.recordId ||
                            nextAuth.authGeneration !== auth.authGeneration ||
                            !sameApiScope(nextAuth.target, auth.target) ||
                            nextAuth.locator.kind !== "id" ||
                            nextAuth.locator.operationId !==
                                receipt.operation_id
                        )
                            throw new WireError("semantic");
                        auth = nextAuth;
                        entry.authorization = auth;
                        if (receipt.state === "interrupted") {
                            stop("interrupted");
                            return;
                        }
                        if (
                            receipt.state === "succeeded" ||
                            receipt.state === "failed"
                        ) {
                            const result = await read(() =>
                                client.readOperationResult(
                                    receipt,
                                    requestOptions,
                                ),
                            );
                            if (result === null) return;
                            if (
                                result.kind !== "success" &&
                                result.kind !== "domain_failure"
                            ) {
                                stop("result_unknown", result);
                                return;
                            }
                            if (
                                !publish(entry, {
                                    result: Object.freeze(result),
                                    failure: null,
                                })
                            )
                                return;
                            if (!live()) return;
                            const certainty = await options.onResult(
                                auth,
                                receipt,
                                result,
                            );
                            if (live())
                                publish(entry, {
                                    phase:
                                        certainty === "known"
                                            ? "settled"
                                            : "unknown",
                                    pauseReason:
                                        certainty === "known"
                                            ? null
                                            : "unknown_effects",
                                });
                            return;
                        }
                        const events = await read(() =>
                            client.readOperationEvents(
                                receipt,
                                {
                                    after: entry.snapshot.events.cursor,
                                    limit: 32,
                                },
                                requestOptions,
                            ),
                        );
                        if (events === null) return;
                        if (events.kind !== "success") {
                            stop("protocol", events);
                            return;
                        }
                        if (
                            !publish(entry, {
                                events: mergeEventWindow(
                                    entry.snapshot.events,
                                    events.payload,
                                    receipt.operation_id,
                                ),
                                failure: null,
                            })
                        )
                            return;
                        if (cycle === 119) {
                            pauseEntry(entry, "session_limit");
                            return;
                        }
                        await sleep(2000, abort.signal);
                    }
                } catch (error) {
                    if (live())
                        stop(
                            error instanceof WireError
                                ? "protocol"
                                : "registry",
                        );
                } finally {
                    clearTimeout(deadline);
                    abort.signal.removeEventListener("abort", clearDeadline);
                    if (generation === entry.generation) {
                        entry.abort = null;
                        entry.promise = null;
                    }
                }
            };
            entry.promise = Promise.resolve().then(work);
            return entry.promise;
        },
        dispose() {
            disposed = true;
            clearPrivate();
        },
    });
}
