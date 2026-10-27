/** Three bounded read owners; no host permission or operation ownership is inferred. */
import type { QueryHandle, QuerySnapshot } from "../state/query-state";
import type { SessionController } from "../state/session-controller";
import type {
    EmptyPayload,
    HealthPayload,
    StatusPayload,
    VersionPayload,
} from "../wire/generated";

export interface AdministrationReadSnapshot {
    readonly generation: number;
    readonly authGeneration: number;
    readonly connected: boolean;
    readonly active: boolean;
    readonly status: QuerySnapshot<StatusPayload, EmptyPayload>;
    readonly health: QuerySnapshot<HealthPayload, EmptyPayload>;
    readonly version: QuerySnapshot<VersionPayload, EmptyPayload>;
}
type Controller = Pick<
    SessionController,
    "snapshot" | "subscribe" | "queries" | "apiReads"
>;
interface Slot<T> {
    readonly handle: QueryHandle<T, EmptyPayload>;
    readonly unsubscribe: () => void;
}
const IDLE = Object.freeze({
    key: "",
    generation: 0,
    phase: "idle" as const,
    result: null,
    reason: null,
});
const state = <T>(slot: Slot<T> | null): QuerySnapshot<T, EmptyPayload> =>
    slot?.handle.snapshot() ?? IDLE;

export function createAdministrationReadStore(controller: Controller) {
    let authGeneration = controller.snapshot().generation;
    let connected = controller.snapshot().connection === "connected";
    let active = false,
        disposed = false,
        generation = 0;
    let status: Slot<StatusPayload> | null = null;
    let health: Slot<HealthPayload> | null = null;
    let version: Slot<VersionPayload> | null = null;
    let pending: Promise<void> | null = null;
    let snapshot: AdministrationReadSnapshot;
    const listeners = new Set<() => void>();
    function publish() {
        if (disposed) return;
        snapshot = Object.freeze({
            generation,
            authGeneration,
            connected,
            active,
            status: state(status),
            health: state(health),
            version: state(version),
        });
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                // A detached view cannot prevent private evidence clearing.
            }
        }
    }
    function attach<T>(handle: QueryHandle<T, EmptyPayload>): Slot<T> {
        return { handle, unsubscribe: handle.subscribe(publish) };
    }
    function retire() {
        generation++;
        pending = null;
        const owned = [status, health, version];
        status = health = version = null;
        for (const slot of owned) slot?.unsubscribe();
        for (const slot of owned) slot?.handle.invalidate();
    }
    function current(own: number) {
        return !disposed && active && connected && generation === own;
    }
    async function load(own: number) {
        if (!current(own)) return;
        const api = controller.apiReads;
        status ??= attach(
            controller.queries.query(
                { routeId: "status_default", predicates: { limit: 25 } },
                (options) => api.readStatus(options, { limit: 25 }),
            ),
        );
        await status.handle.refresh();
        if (!current(own)) return;
        health ??= attach(
            controller.queries.query({ routeId: "health_default" }, (options) =>
                api.readHealth(options),
            ),
        );
        await health.handle.refresh();
        if (!current(own)) return;
        version ??= attach(
            controller.queries.query(
                { routeId: "version_default" },
                (options) => api.readVersion(options),
            ),
        );
        await version.handle.refresh();
    }
    function refresh(): Promise<void> {
        if (disposed || !active || !connected) return Promise.resolve();
        if (pending !== null) return pending;
        const own = generation;
        // Publish guards may synchronously pause/disconnect this owner. The
        // deferred task checks that fence before creating a handle or reading.
        const work = Promise.resolve().then(() => load(own));
        pending = work;
        void work.finally(() => {
            if (pending === work) pending = null;
        });
        return work;
    }
    const unsubscribe = controller.subscribe(() => {
        if (disposed) return;
        const next = controller.snapshot();
        const changed =
            next.generation !== authGeneration ||
            (next.connection === "connected") !== connected;
        if (changed) retire();
        authGeneration = next.generation;
        connected = next.connection === "connected";
        publish();
        if (changed && connected && active) void refresh();
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
        setPageActive(value: boolean) {
            if (disposed || active === value) return;
            active = value;
            if (!value) retire();
            publish();
            if (value) void refresh();
        },
        refresh,
        dispose() {
            if (disposed) return;
            active = false;
            retire();
            publish();
            disposed = true;
            unsubscribe();
            listeners.clear();
        },
    });
}
export type AdministrationReadStore = ReturnType<
    typeof createAdministrationReadStore
>;
