/** WEB011 typed handles survive view mounts within one AuthSession, never a reconnect. */
import { queryIdentity } from "../api/identity";
import type { ExactPublication } from "../api/identity";
import type { ReadOptions, ReadResult } from "../api/types";
import { serializeRequestJson } from "../api/request";
import { routeContracts } from "../wire/generated";
import { parseWireJson, WireError } from "../wire/json";
import { createAuthSession } from "./authority";
import type { AuthSession } from "./authority";
import {
    encodedBytes,
    READ_RESERVATION_BYTES,
    SESSION_RESPONSE_BYTES,
    StateCapacityError,
} from "./retention-budget";
import type { ReadCoordinator, RetentionBudget } from "./retention-budget";

export type QueryPhase =
    "idle" | "loading" | "ready" | "stale" | "unavailable" | "failed";
export interface QueryDescriptor {
    readonly routeId: keyof typeof routeContracts;
    readonly path?: Readonly<Record<string, string>>;
    readonly predicates?: Readonly<Record<string, unknown>>;
    readonly publication?: ExactPublication;
}
export interface QuerySnapshot<S, F> {
    readonly key: string;
    readonly generation: number;
    readonly phase: QueryPhase;
    readonly result: ReadResult<S, F> | null;
    readonly reason: "capacity" | "authentication" | null;
}
export interface QueryHandle<S, F> {
    readonly snapshot: () => QuerySnapshot<S, F>;
    readonly subscribe: (listener: () => void) => () => void;
    readonly refresh: () => Promise<void>;
    readonly invalidate: () => void;
}
export interface QueryStoreOptions {
    readonly session: AuthSession;
    readonly retention: RetentionBudget;
    readonly reads: ReadCoordinator;
    readonly onUnauthorized: () => void;
}
interface Entry {
    readonly owner: string;
    readonly descriptor: QueryDescriptor;
    key(): string;
    active(): boolean;
    clear(authentication: boolean): void;
    retire(): void;
    invalidate(): void;
}
let nextStore = 0;

function queryParts(descriptor: QueryDescriptor): {
    route: string;
    predicates: readonly (readonly [string, string])[];
    publication: ExactPublication | undefined;
} {
    const contract = routeContracts[descriptor.routeId];
    if (
        contract.method !== "GET" ||
        (contract.responseKind !== "read" &&
            contract.responseKind !== "operation_result")
    )
        throw new WireError("schema");
    const path = contract.decodePath(
        parseWireJson(serializeRequestJson(descriptor.path ?? {})),
    );
    const pathFields: Readonly<Record<string, unknown>> = path;
    const query = contract.decodeQuery(
        parseWireJson(serializeRequestJson(descriptor.predicates ?? {})),
    );
    const predicates: (readonly [string, string])[] = [];
    for (const [prefix, fields] of [
        ["path", path],
        ["query", query],
    ] satisfies readonly (readonly [string, object])[]) {
        for (const [key, value] of Object.entries(fields).sort(([a], [b]) =>
            a.localeCompare(b),
        ))
            predicates.push([prefix + ":" + key, serializeRequestJson(value)]);
    }
    if (
        contract.path.includes("{commit_sha}") &&
        contract.path.includes("{publication_id}")
    ) {
        const selected = descriptor.publication;
        if (
            selected === undefined ||
            pathFields.commit_sha !== selected.commitSha ||
            pathFields.publication_id !== selected.publicationId ||
            pathFields.repository_type !== selected.repositoryType ||
            typeof pathFields.namespace !== "string" ||
            typeof pathFields.name !== "string" ||
            pathFields.namespace + "/" + pathFields.name !==
                selected.repositoryId
        )
            throw new WireError("semantic");
    }
    return {
        route: contract.path,
        predicates,
        publication:
            descriptor.publication === undefined
                ? undefined
                : Object.freeze({ ...descriptor.publication }),
    };
}

/** Count one logical response, not the payload alias duplicated by ReadResult. */
export function retainedReadBytes<S, F>(result: ReadResult<S, F>): number {
    return encodedBytes(
        result.kind === "success" || result.kind === "domain_failure"
            ? { kind: result.kind, response: result.response }
            : result,
    );
}

export function createQueryStore(options: QueryStoreOptions) {
    const name = "queries:" + String(++nextStore);
    const entries = new Map<string, Entry>();
    let session = createAuthSession(options.session);
    let epoch = 0;
    let serial = 0;
    let authenticated = true;
    let disposed = false;
    let clearing = false;
    const notifications = new Set<() => void>();
    let notificationQueued = false;
    function notify(listener: () => void) {
        if (!clearing) {
            listener();
            return;
        }
        notifications.add(listener);
        if (!notificationQueued) {
            notificationQueued = true;
            queueMicrotask(() => {
                notificationQueued = false;
                const pending = [...notifications];
                notifications.clear();
                for (const callback of pending) callback();
            });
        }
    }

    function drop(entry: Entry) {
        entries.delete(entry.owner);
        entry.clear(false);
    }
    function evict(except: Entry) {
        for (const entry of entries.values()) {
            if (entry !== except && !entry.active()) {
                drop(entry);
                return true;
            }
        }
        return false;
    }
    function admit(entry: Entry): boolean {
        if (entries.has(entry.owner)) return true;
        const duplicate = [...entries.values()].find(
            (item) => item.key() === entry.key(),
        );
        if (duplicate !== undefined) {
            if (duplicate.active()) return false;
            drop(duplicate);
        }
        while (entries.size >= 32 && evict(entry)) {
            /* inactive data only */
        }
        if (entries.size >= 32) return false;
        entries.set(entry.owner, entry);
        return true;
    }
    function clearPrivate(
        reason: "authentication" | "authority" | "logout" = "authentication",
    ) {
        epoch++;
        authenticated = reason === "authority";
        const previous = clearing;
        clearing = true;
        try {
            for (const entry of entries.values()) entry.clear(!authenticated);
        } finally {
            clearing = previous;
        }
    }

    return Object.freeze({
        query<S, F>(
            descriptor: QueryDescriptor,
            load: (options: ReadOptions) => Promise<ReadResult<S, F>>,
        ): QueryHandle<S, F> {
            if (disposed) throw new StateCapacityError();
            const normalized = queryParts(descriptor);
            const ownedSession = session;
            const ownedEpoch = epoch;
            const owner = name + ":" + String(++serial);
            const listeners = new Set<() => void>();
            let generation = 0;
            let retired = false;
            let jobs = 0;
            let controller: AbortController | null = null;
            let pending: Promise<void> | null = null;
            const key = () =>
                JSON.stringify([
                    ownedSession.authGeneration,
                    ownedEpoch,
                    queryIdentity(
                        ownedSession.scope,
                        normalized.route,
                        normalized.predicates,
                        normalized.publication,
                    ),
                ]);
            if (encodedBytes(key()) > 8192) throw new StateCapacityError();
            let snapshot: QuerySnapshot<S, F> = Object.freeze({
                key: key(),
                generation,
                phase: "idle",
                result: null,
                reason: null,
            });
            function notifyListeners() {
                for (const listener of listeners) {
                    try {
                        listener();
                    } catch {
                        // A view failure must not interrupt other private-state updates.
                    }
                }
            }
            function publish(
                phase: QueryPhase,
                result: ReadResult<S, F> | null,
                reason: QuerySnapshot<S, F>["reason"] = null,
            ) {
                snapshot = Object.freeze({
                    key: key(),
                    generation,
                    phase,
                    result,
                    reason,
                });
                notify(notifyListeners);
            }
            function clear(authentication: boolean) {
                generation++;
                controller?.abort();
                controller = null;
                pending = null;
                options.retention.release(owner);
                publish(
                    authentication ? "unavailable" : "idle",
                    null,
                    authentication ? "authentication" : null,
                );
            }
            function invalidate() {
                generation++;
                controller?.abort();
                controller = null;
                pending = null;
                publish(
                    snapshot.result === null ? "idle" : "stale",
                    snapshot.result,
                );
            }
            const entry: Entry = {
                owner,
                descriptor,
                key,
                active: () => listeners.size > 0 || jobs > 0,
                clear,
                retire() {
                    retired = true;
                    clear(true);
                },
                invalidate,
            };
            if (!admit(entry)) publish("unavailable", null, "capacity");
            return Object.freeze({
                snapshot: () => snapshot,
                subscribe(listener: () => void) {
                    listeners.add(listener);
                    return () => {
                        listeners.delete(listener);
                    };
                },
                invalidate,
                refresh(): Promise<void> {
                    if (pending !== null) return pending;
                    if (disposed || retired || !authenticated) {
                        publish("unavailable", null, "authentication");
                        return Promise.resolve();
                    }
                    if (!admit(entry)) {
                        clear(false);
                        publish("unavailable", null, "capacity");
                        return Promise.resolve();
                    }
                    const current = ++generation;
                    const authEpoch = epoch;
                    const abort = new AbortController();
                    controller = abort;
                    const reservation = owner + ":pending:" + String(current);
                    while (
                        !options.retention.claim(
                            reservation,
                            READ_RESERVATION_BYTES,
                        ) &&
                        evict(entry)
                    ) {
                        /* reserve before read */
                    }
                    if (
                        !options.retention.claim(
                            reservation,
                            READ_RESERVATION_BYTES,
                        )
                    ) {
                        publish("unavailable", null, "capacity");
                        options.retention.release(owner);
                        controller = null;
                        return Promise.resolve();
                    }
                    jobs++;
                    const work = async () => {
                        try {
                            const result = await options.reads.run(
                                owner,
                                abort.signal,
                                () =>
                                    load({
                                        signal: abort.signal,
                                        responseByteLimit:
                                            SESSION_RESPONSE_BYTES,
                                    }),
                            );
                            if (
                                disposed ||
                                authEpoch !== epoch ||
                                current !== generation ||
                                abort.signal.aborted
                            )
                                return;
                            if (
                                result.kind === "api_problem" &&
                                result.status === 401
                            ) {
                                clearPrivate("authentication");
                                options.onUnauthorized();
                                return;
                            }
                            options.retention.release(reservation);
                            if (
                                !options.retention.claim(
                                    owner,
                                    retainedReadBytes(result),
                                )
                            ) {
                                options.retention.release(owner);
                                publish("unavailable", null, "capacity");
                                return;
                            }
                            if (result.kind === "aborted") {
                                options.retention.release(owner);
                                publish("idle", null);
                            } else
                                publish(
                                    result.kind === "success"
                                        ? "ready"
                                        : result.kind === "transport_failure" ||
                                            (result.kind === "api_problem" &&
                                                (result.status >= 500 ||
                                                    result.status === 429))
                                          ? "unavailable"
                                          : "failed",
                                    Object.freeze(result),
                                );
                        } catch (error) {
                            if (
                                authEpoch === epoch &&
                                current === generation &&
                                !abort.signal.aborted
                            ) {
                                options.retention.release(reservation);
                                options.retention.release(owner);
                                if (error instanceof StateCapacityError)
                                    publish("unavailable", null, "capacity");
                                else {
                                    const failure: ReadResult<S, F> =
                                        error instanceof WireError
                                            ? {
                                                  kind: "protocol_failure",
                                                  reason: error.reason,
                                              }
                                            : {
                                                  kind: "transport_failure",
                                                  reason: "network",
                                              };
                                    if (
                                        options.retention.claim(
                                            owner,
                                            retainedReadBytes(failure),
                                        )
                                    )
                                        publish(
                                            error instanceof WireError
                                                ? "failed"
                                                : "unavailable",
                                            failure,
                                        );
                                    else
                                        publish(
                                            "unavailable",
                                            null,
                                            "capacity",
                                        );
                                }
                            }
                        } finally {
                            options.retention.release(reservation);
                            jobs--;
                            if (current === generation) {
                                pending = null;
                                controller = null;
                            }
                        }
                    };
                    const task = Promise.resolve().then(work);
                    pending = task;
                    publish(
                        snapshot.result === null ? "loading" : "stale",
                        snapshot.result,
                    );
                    return task;
                },
            });
        },
        setSession(next: AuthSession) {
            const checked = createAuthSession(next);
            const previous = clearing;
            clearing = true;
            try {
                clearPrivate("authority");
                for (const entry of entries.values()) entry.retire();
                entries.clear();
                session = checked;
            } finally {
                clearing = previous;
            }
        },
        clearPrivate,
        invalidate(
            predicate: (descriptor: QueryDescriptor) => boolean = () => true,
        ) {
            for (const entry of entries.values())
                if (predicate(entry.descriptor)) entry.invalidate();
        },
        dispose() {
            clearPrivate("logout");
            disposed = true;
            entries.clear();
        },
    });
}
