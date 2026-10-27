/** Actual controller/client/query boundary; only HTTP response bodies are fixtures. */
import { afterEach, expect, test, vi } from "vitest";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { createSessionController } from "../src/state/session-controller";
import { uiBootstrapFixture } from "./ui-fixtures";
import {
    ARCHIVE_ID,
    jsonResponse,
    readWire,
    statusPayload,
    versionPayload,
    problemWire,
} from "./read-fixtures";
import { deferred } from "./state-fixtures";

const disposers: (() => void)[] = [];
afterEach(() => {
    disposers
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    vi.unstubAllGlobals();
});
function path(input: RequestInfo | URL) {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    ).pathname;
}
function response(url: string) {
    return jsonResponse(
        url.endsWith("/status")
            ? readWire("status", statusPayload(true))
            : url.endsWith("/health")
              ? readWire("health", {
                    ready: true,
                    policy_valid: null,
                    archive: null,
                })
              : readWire("version", versionPayload),
    );
}
function setup(
    router: (
        url: string,
        init?: RequestInit,
    ) => Response | Promise<Response> = response,
) {
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal("location", new URL(bootstrap.configured_origin));
    const fetcher = vi.fn<typeof fetch>((input, init) =>
        Promise.resolve(router(path(input), init)),
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
    const store = createAdministrationReadStore(controller);
    disposers.push(() => {
        store.dispose();
        controller.dispose();
    });
    return { store, controller, fetcher };
}
test("construction and inactive refresh read nothing; activation owns exactly three GETs and no host query", async () => {
    const { store, controller, fetcher } = setup();
    await store.refresh();
    expect(fetcher).not.toHaveBeenCalled();
    store.setPageActive(true);
    await store.refresh();
    expect(fetcher.mock.calls.map(([input]) => path(input))).toEqual([
        "/api/v1/status",
        "/api/v1/health",
        "/api/v1/version",
    ]);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
    expect(store.snapshot().status.phase).toBe("ready");
    expect(store.snapshot().health.result).toMatchObject({
        kind: "success",
        payload: { ready: true, policy_valid: null, archive: null },
    });
    expect(controller.hostStatus.snapshot().phase).toBe("idle");
    expect(controller.snapshot().registry.records).toEqual([]);
});
test("concurrent refresh and repeated activation coalesce the same finite sequence", async () => {
    const { store, fetcher } = setup();
    store.setPageActive(true);
    const first = store.refresh(),
        second = store.refresh();
    store.setPageActive(true);
    expect(first).toBe(second);
    await first;
    expect(fetcher).toHaveBeenCalledTimes(3);
});
test("pause clears ready aggregate references and permits a fresh owner of the same query", async () => {
    const { store, controller, fetcher } = setup();
    store.setPageActive(true);
    await store.refresh();
    store.setPageActive(false);
    expect(store.snapshot().status.result).toBeNull();
    expect(store.snapshot().health.result).toBeNull();
    expect(store.snapshot().version.result).toBeNull();
    const api = controller.apiReads;
    const other = controller.queries.query(
        { routeId: "status_default", predicates: { limit: 25 } },
        (options) => api.readStatus(options, { limit: 25 }),
    );
    await other.refresh();
    expect(other.snapshot().phase).toBe("ready");
    expect(fetcher).toHaveBeenCalledTimes(4);
    other.invalidate();
    store.setPageActive(true);
    await store.refresh();
    expect(store.snapshot().status.phase).toBe("ready");
    expect(fetcher).toHaveBeenCalledTimes(7);
});
test("pause during a slow status read fences its late result and subsequent health/version reads", async () => {
    const slow = deferred<Response>();
    const { store, fetcher } = setup(() => slow.promise);
    store.setPageActive(true);
    const work = store.refresh();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    store.setPageActive(false);
    slow.resolve(response("/status"));
    await work;
    expect(store.snapshot().status.result).toBeNull();
    expect(fetcher).toHaveBeenCalledOnce();
});
test("a subscriber pause at the first loading notification prevents even the first transmission", async () => {
    const { store, fetcher } = setup();
    store.subscribe(() => {
        if (store.snapshot().status.phase === "loading")
            store.setPageActive(false);
    });
    store.setPageActive(true);
    await store.refresh();
    await Promise.resolve();
    expect(fetcher).not.toHaveBeenCalled();
    expect(store.snapshot().active).toBe(false);
});
test("disconnect clears every published private fact synchronously and active reconnect recreates fresh handles", async () => {
    const { store, controller, fetcher } = setup();
    store.setPageActive(true);
    await store.refresh();
    controller.disconnect();
    expect(store.snapshot().connected).toBe(false);
    expect(store.snapshot().status.result).toBeNull();
    await controller.reconnect();
    await store.refresh();
    expect(store.snapshot().connected).toBe(true);
    expect(store.snapshot().authGeneration).toBe(
        controller.snapshot().generation,
    );
    expect(store.snapshot().status.phase).toBe("ready");
    expect(fetcher).toHaveBeenCalledTimes(6);
});
test("authentication expiry stops the pipeline without a retry or successful empty archive", async () => {
    const { store, controller, fetcher } = setup(() =>
        jsonResponse(problemWire("HFAPI002"), 401),
    );
    store.setPageActive(true);
    await store.refresh();
    expect(controller.snapshot().connection).toBe("disconnected");
    expect(store.snapshot().status.result).toBeNull();
    expect(fetcher).toHaveBeenCalledOnce();
});
test("an old authentication generation cannot replace fresh status or continue its old pipeline", async () => {
    const slow = deferred<Response>();
    let statusReads = 0;
    const { store, controller, fetcher } = setup((url) => {
        if (url.endsWith("/status")) {
            statusReads++;
            return statusReads === 1
                ? slow.promise
                : jsonResponse(readWire("status", statusPayload(false)));
        }
        return response(url);
    });
    store.setPageActive(true);
    const old = store.refresh();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    controller.disconnect();
    await controller.reconnect();
    await store.refresh();
    slow.resolve(response("/status"));
    await old;
    expect(store.snapshot().status.result).toMatchObject({
        kind: "success",
        payload: { archive: { reachable: false } },
    });
    expect(fetcher).toHaveBeenCalledTimes(4);
});
test.each(["transport", "protocol", "domain"])(
    "%s failure remains classified independently from successful subsequent observations",
    async (failure) => {
        const { store, fetcher } = setup((url) => {
            if (!url.endsWith("/status")) return response(url);
            if (failure === "transport")
                return Promise.reject(new TypeError("owned offline"));
            if (failure === "protocol")
                return jsonResponse({ unexpected: true });
            return jsonResponse(readWire("status", {}, true));
        });
        store.setPageActive(true);
        await store.refresh();
        expect(store.snapshot().status.result?.kind).toBe(
            failure === "transport"
                ? "transport_failure"
                : failure === "protocol"
                  ? "protocol_failure"
                  : "domain_failure",
        );
        expect(store.snapshot().version.phase).toBe("ready");
        expect(fetcher).toHaveBeenCalledTimes(3);
    },
);
test("shared retention exhaustion refuses reads without fabricating observations", async () => {
    const { store, controller, fetcher } = setup();
    const owners = Array.from({ length: 4 }, () =>
        controller.createPrivateSlot(),
    );
    for (const owner of owners)
        expect(owner.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    store.setPageActive(true);
    await store.refresh();
    expect(fetcher).not.toHaveBeenCalled();
    expect(store.snapshot().status.reason).toBe("capacity");
    expect(store.snapshot().version.result).toBeNull();
    for (const owner of owners) owner.clear();
    await store.refresh();
    expect(store.snapshot().version.phase).toBe("ready");
});
test("disposal aborts owned reads, clears aggregate references and cannot reactivate", async () => {
    const { store, fetcher } = setup();
    store.setPageActive(true);
    await store.refresh();
    store.dispose();
    expect(store.snapshot().status.result).toBeNull();
    store.setPageActive(true);
    await store.refresh();
    expect(fetcher).toHaveBeenCalledTimes(3);
});
test("a failing detached listener cannot suppress health reads or another subscriber", async () => {
    const { store } = setup();
    const heard = vi.fn();
    store.subscribe(() => {
        throw new Error("detached view");
    });
    store.subscribe(heard);
    store.setPageActive(true);
    await store.refresh();
    expect(heard).toHaveBeenCalled();
    expect(store.snapshot().version.phase).toBe("ready");
});
