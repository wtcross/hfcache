import { expect, test, vi } from "vitest";
import { createQueryStore } from "../src/state/query-state";
import {
    createReadCoordinator,
    createRetentionBudget,
    encodedBytes,
} from "../src/state/retention-budget";
import { session, versionResult, deferred } from "./state-fixtures";
import type { VersionResult } from "./state-fixtures";
import { problemWire } from "./read-fixtures";
import { WireError } from "../src/wire/json";

function setup() {
    const retention = createRetentionBudget(),
        reads = createReadCoordinator(),
        onUnauthorized = vi.fn();
    const store = createQueryStore({
        session,
        retention,
        reads,
        onUnauthorized,
    });
    return { store, retention, reads, onUnauthorized };
}

test("typed handle keeps classified evidence and releases encoded retention on disposal", async () => {
    const { store, retention } = setup();
    const value = await versionResult("first");
    const query = store.query({ routeId: "version_default" }, () =>
        Promise.resolve(value),
    );
    expect(query.snapshot().phase).toBe("idle");
    await query.refresh();
    expect(query.snapshot()).toMatchObject({ phase: "ready", result: value });
    expect(retention.usedBytes).toBeGreaterThan(0);
    expect(Object.isFrozen(query.snapshot())).toBe(true);
    query.invalidate();
    expect(query.snapshot()).toMatchObject({ phase: "stale", result: value });
    store.dispose();
    expect(query.snapshot().result).toBeNull();
    expect(retention.usedBytes).toBe(0);
});

test("one handle coalesces reads; relogin permanently retires captured-client handles", async () => {
    const { store, reads } = setup();
    const first = deferred<VersionResult>();
    const oldLoader = vi.fn().mockReturnValue(first.promise);
    const oldQuery = store.query({ routeId: "version_default" }, oldLoader);
    const old = oldQuery.refresh();
    const originalKey = oldQuery.snapshot().key;
    expect(oldQuery.refresh()).toBe(old);
    await vi.waitFor(() => {
        expect(oldLoader).toHaveBeenCalledOnce();
    });
    store.setSession({ ...session, authGeneration: 2 });
    expect(oldQuery.snapshot().result).toBeNull();
    await oldQuery.refresh();
    expect(oldLoader).toHaveBeenCalledOnce();
    expect(oldQuery.snapshot().key).toBe(originalKey);
    const value = await versionResult("new");
    const loader = vi.fn().mockResolvedValue(value);
    const query = store.query({ routeId: "version_default" }, loader);
    const fresh = query.refresh();
    await Promise.resolve();
    expect(reads.active).toBe(2);
    first.resolve(await versionResult("old-private"));
    await old;
    await fresh;
    expect(oldQuery.snapshot().result).toBeNull();
    expect(query.snapshot()).toMatchObject({ phase: "ready", result: value });
    expect(query.snapshot().key).not.toBe(originalKey);
    expect(loader).toHaveBeenCalledOnce();
    store.dispose();
});

test("401 clears all private queries synchronously and blocks refresh until authenticated session", async () => {
    const { store, retention, onUnauthorized } = setup();
    let unauthorized = false;
    const value = await versionResult();
    const first = store.query({ routeId: "version_default" }, () =>
        Promise.resolve(value),
    );
    const second = store.query({ routeId: "capabilities_default" }, () =>
        Promise.resolve(
            unauthorized
                ? { kind: "api_problem", status: 401, problem: problemWire() }
                : value,
        ),
    );
    await first.refresh();
    unauthorized = true;
    await second.refresh();
    expect(first.snapshot().result).toBeNull();
    expect(second.snapshot().result).toBeNull();
    expect(retention.usedBytes).toBe(0);
    expect(onUnauthorized).toHaveBeenCalledOnce();
    await first.refresh();
    expect(first.snapshot().reason).toBe("authentication");
    store.setSession({ ...session, authGeneration: 2 });
    await first.refresh();
    expect(first.snapshot().reason).toBe("authentication");
    const fresh = store.query({ routeId: "version_default" }, () =>
        Promise.resolve(value),
    );
    await fresh.refresh();
    expect(fresh.snapshot().phase).toBe("ready");
    store.dispose();
});

test("tag-only explicit invalidation fences prior response without relying on operational fingerprint", async () => {
    const { store } = setup();
    const old = deferred<VersionResult>();
    const newer = await versionResult("new-tags");
    const loader = vi
        .fn()
        .mockReturnValueOnce(old.promise)
        .mockResolvedValue(newer);
    const query = store.query({ routeId: "catalog_search_default" }, loader);
    const pending = query.refresh();
    await vi.waitFor(() => {
        expect(loader).toHaveBeenCalledOnce();
    });
    store.invalidate((d) => d.routeId === "catalog_search_default");
    const fresh = query.refresh();
    old.resolve(await versionResult("old-tags"));
    await pending;
    await fresh;
    expect(query.snapshot().result).toEqual(newer);
});

test("query predicates/exact publication are part of key; POST routes and mismatched pairs refuse", () => {
    const { store } = setup();
    const read = () => versionResult();
    const a = store.query(
        { routeId: "catalog_search_default", predicates: { limit: 1 } },
        read,
    );
    const b = store.query(
        { routeId: "catalog_search_default", predicates: { limit: 2 } },
        read,
    );
    expect(a.snapshot().key).not.toBe(b.snapshot().key);
    expect(() =>
        store.query({ routeId: "config_validate_installed" }, read),
    ).toThrow();
    expect(() =>
        store.query(
            {
                routeId: "repository_card_default",
                path: {
                    repository_type: "model",
                    namespace: "org",
                    name: "repo",
                    commit_sha: "a".repeat(40),
                    publication_id: "b".repeat(32),
                },
            },
            read,
        ),
    ).toThrow();
});

test("bounded entries preserve active data and evicted handle drops body then visibly readmits", async () => {
    const { store, retention } = setup();
    const value = await versionResult();
    const first = store.query({ routeId: "version_default" }, () =>
        Promise.resolve(value),
    );
    await first.refresh();
    const held = [];
    for (let i = 0; i < 32; i++) {
        const q = store.query(
            { routeId: "catalog_search_default", predicates: { limit: i + 1 } },
            () => Promise.resolve(value),
        );
        held.push(q.subscribe(() => {}));
    }
    expect(first.snapshot().result).toBeNull();
    await first.refresh();
    expect(first.snapshot()).toMatchObject({
        phase: "unavailable",
        reason: "capacity",
        result: null,
    });
    held[0]?.();
    await first.refresh();
    expect(first.snapshot().phase).toBe("ready");
    store.dispose();
    expect(retention.usedBytes).toBe(0);
});

test.each(["network", "domain", "protocol", "aborted"])(
    "preserves read classification %s",
    async (kind) => {
        const { store } = setup();
        const base = await versionResult();
        if (base.kind !== "success") throw new Error("fixture refused");
        const result: VersionResult =
            kind === "network"
                ? { kind: "transport_failure", reason: "network" }
                : kind === "protocol"
                  ? { kind: "protocol_failure", reason: "schema" }
                  : kind === "aborted"
                    ? { kind: "aborted" }
                    : {
                          kind: "domain_failure",
                          response: {
                              ...base.response,
                              envelope: { ...base.response.envelope, data: {} },
                          },
                          payload: {},
                      };
        const query = store.query({ routeId: "version_default" }, () =>
            Promise.resolve(result),
        );
        await query.refresh();
        expect(query.snapshot().phase).toBe(
            kind === "network"
                ? "unavailable"
                : kind === "aborted"
                  ? "idle"
                  : "failed",
        );
        if (kind !== "aborted") expect(query.snapshot().result).toEqual(result);
    },
);

test("byte capacity refuses before read and no private body hides in evicted closures", async () => {
    const retention = createRetentionBudget(1024);
    const store = createQueryStore({
        session,
        retention,
        reads: createReadCoordinator(),
        onUnauthorized: () => {},
    });
    const load = vi.fn(() => versionResult());
    const query = store.query({ routeId: "version_default" }, load);
    await query.refresh();
    expect(load).not.toHaveBeenCalled();
    expect(query.snapshot().reason).toBe("capacity");
    expect(retention.usedBytes).toBe(0);
    expect(encodedBytes("😺")).toBe(6);
});

test("auth clear is atomic across entries before any subscriber can peek", async () => {
    const { store } = setup();
    const value = await versionResult("private");
    const a = store.query({ routeId: "version_default" }, () =>
        Promise.resolve(value),
    );
    const b = store.query({ routeId: "capabilities_default" }, () =>
        Promise.resolve(value),
    );
    await a.refresh();
    await b.refresh();
    const peeks: unknown[] = [];
    a.subscribe(() => {
        peeks.push(b.snapshot().result);
    });
    b.subscribe(() => {
        peeks.push(a.snapshot().result);
    });
    store.clearPrivate("authentication");
    expect(peeks).toEqual([]);
    expect(a.snapshot().result).toBeNull();
    expect(b.snapshot().result).toBeNull();
    await Promise.resolve();
    expect(peeks).toEqual([null, null]);
    store.dispose();
});

test.each([new WireError("schema"), new Error("private transport detail")])(
    "thrown adapter failure is classified and charged without exposing exception text",
    async (error) => {
        const { store, retention } = setup();
        const query = store.query({ routeId: "version_default" }, () =>
            Promise.reject(error),
        );
        await query.refresh();
        expect(query.snapshot().result).toEqual(
            error instanceof WireError
                ? { kind: "protocol_failure", reason: "schema" }
                : { kind: "transport_failure", reason: "network" },
        );
        expect(retention.usedBytes).toBeGreaterThan(0);
        expect(JSON.stringify(query.snapshot())).not.toContain(
            "private transport detail",
        );
        store.dispose();
    },
);

test("subscriber failure cannot block remaining views or convert a healthy read into a failure", async () => {
    const { store } = setup();
    const query = store.query({ routeId: "version_default" }, () =>
        versionResult(),
    );
    const notified = vi.fn();
    query.subscribe(() => {
        throw new Error("broken view");
    });
    query.subscribe(notified);
    await query.refresh();
    expect(query.snapshot().phase).toBe("ready");
    store.clearPrivate();
    await Promise.resolve();
    expect(query.snapshot().result).toBeNull();
    expect(notified).toHaveBeenCalledTimes(3);
    store.dispose();
    expect(() =>
        store.query({ routeId: "version_default" }, () => versionResult()),
    ).toThrow();
});

test("duplicate active ownership handle refuses visibly and a failed reservation releases prior payload", async () => {
    const { store, retention } = setup();
    const first = store.query({ routeId: "version_default" }, () =>
        versionResult(),
    );
    const held = first.subscribe(() => {});
    await first.refresh();
    const duplicate = store.query({ routeId: "version_default" }, () =>
        versionResult(),
    );
    expect(duplicate.snapshot().reason).toBe("capacity");
    await duplicate.refresh();
    expect(duplicate.snapshot().result).toBeNull();
    expect(first.snapshot().result?.kind).toBe("success");
    expect(
        retention.claim(
            "other-evidence",
            32 * 1024 * 1024 - retention.usedBytes,
        ),
    ).toBe(true);
    await first.refresh();
    expect(first.snapshot()).toMatchObject({
        reason: "capacity",
        result: null,
    });
    held();
    retention.release("other-evidence");
    store.dispose();
});
