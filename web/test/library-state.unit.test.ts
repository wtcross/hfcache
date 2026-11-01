/** Owned HTTP wires exercise the real client/session query store; no effect-adapter acceptance. */
import { afterEach, expect, test, vi } from "vitest";
import {
    createLibraryStore,
    MAX_LIBRARY_PAGES,
} from "../src/library/library-state";
import type { LibraryStore } from "../src/library/library-state";
import { normalizeLibraryFilters } from "../src/library/filters";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import type { CatalogEntry } from "../src/wire/generated";
import {
    jsonResponse,
    readWire,
    problemWire,
    ARCHIVE_ID,
    statusPayload,
} from "./read-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import { deferred } from "./state-fixtures";

const fingerprint = "2".repeat(64),
    identity = "a".repeat(64);
const entries: readonly CatalogEntry[] = [
    {
        repository_type: "dataset",
        repository_id: "owner/shared",
        tags: ["historical"],
        tag_origin: "last_observed",
        tag_observed_at: "2026-10-20T12:00:00.000000Z",
        curation_fingerprint: null,
        configured: false,
        enabled: null,
        archived: true,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: ["parquet"],
    },
    {
        repository_type: "model",
        repository_id: "owner/shared",
        tags: [],
        tag_origin: "configured",
        tag_observed_at: null,
        curation_fingerprint: null,
        configured: true,
        enabled: false,
        archived: false,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: [],
    },
];
function coverage(rows: readonly CatalogEntry[], incomplete = false) {
    const publications = incomplete
        ? Math.max(1, rows.filter((row) => row.archived).length)
        : rows.filter((row) => row.archived).length;
    return {
        repositories: incomplete ? Math.max(1, rows.length) : rows.length,
        tags_known: incomplete && rows.length === 0 ? 0 : rows.length,
        tags_unknown: incomplete && rows.length === 0 ? 1 : 0,
        publications,
        usable: incomplete ? 0 : publications,
        partial: 0,
        unsupported: 0,
        failed: 0,
        missing: incomplete ? publications : 0,
        technical_required: false,
        incomplete,
    };
}
function wrapper(
    command: string,
    data: unknown,
    next_cursor: string | null = null,
) {
    const incomplete =
        typeof data === "object" &&
        data !== null &&
        "coverage" in data &&
        typeof data.coverage === "object" &&
        data.coverage !== null &&
        "incomplete" in data.coverage &&
        data.coverage.incomplete === true;
    const value = readWire(command, data);
    return {
        ...value,
        envelope: incomplete
            ? {
                  ...value.envelope,
                  outcome: "success_with_warnings",
                  warnings: [
                      {
                          code: "HFWRN011",
                          message: "Incomplete metadata",
                          context: {},
                          repository: null,
                      },
                  ],
              }
            : value.envelope,
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
        next_cursor,
    };
}
function catalog(
    rows: readonly CatalogEntry[] = entries,
    options: {
        cursor?: string | null;
        identity?: string;
        incomplete?: boolean;
        total?: number;
    } = {},
) {
    return wrapper(
        "catalog.search",
        {
            schema_version: 1,
            catalog_identity: options.identity ?? identity,
            coverage: {
                ...coverage(rows, options.incomplete),
                ...(options.total === undefined
                    ? {}
                    : {
                          repositories: options.total,
                          tags_known: options.total,
                      }),
            },
            total_matches: options.total ?? rows.length,
            entries: rows,
        },
        options.cursor ?? null,
    );
}
function defaultResponse(
    url: URL,
    rows: readonly CatalogEntry[] = entries,
    catalogIdentity = identity,
    incomplete = false,
    total?: number,
): Response {
    if (url.pathname === "/api/v1/catalog/search")
        return jsonResponse(catalog(rows, { identity: catalogIdentity }));
    if (url.pathname === "/api/v1/catalog/facets")
        return jsonResponse(
            wrapper("catalog.facets", {
                schema_version: 1,
                catalog_identity: catalogIdentity,
                coverage: {
                    ...coverage(rows, incomplete),
                    ...(total === undefined
                        ? {}
                        : { repositories: total, tags_known: total }),
                },
                facet: url.searchParams.get("facet"),
                total_matches: 0,
                entries: [],
            }),
        );
    const ordered = [...rows].reverse();
    if (url.pathname === "/api/v1/repositories")
        return jsonResponse(
            wrapper("list", {
                repositories: ordered.map((row) => ({
                    repository_type: row.repository_type,
                    repository_id: row.repository_id,
                    managed: row.configured,
                    enabled: row.enabled,
                    current_commit_sha: row.archived ? "c".repeat(40) : null,
                    current_publication_id: row.archived
                        ? "d".repeat(32)
                        : null,
                    retained_revisions: row.archived ? 1 : 0,
                })),
            }),
        );
    if (url.pathname === "/api/v1/status")
        return jsonResponse(
            wrapper("status", {
                ...statusPayload(true),
                repositories: ordered.map((row) => ({
                    repository_type: row.repository_type,
                    repository_id: row.repository_id,
                    managed: row.configured,
                    enabled: row.enabled,
                    current_commit_sha: row.archived ? "c".repeat(40) : null,
                    current_publication_generation: row.archived ? 1 : null,
                    retained_generations: row.archived ? [1] : [],
                    retained_revisions: row.archived ? 1 : 0,
                    requested_revision: row.configured ? "main" : null,
                    upstream_state: "unknown",
                    verification_state: "unverified",
                    last_run_status: null,
                })),
            }),
        );
    if (url.pathname === "/api/v1/repositories/revisions")
        return jsonResponse(
            wrapper("list", {
                revisions: rows
                    .filter((row) => row.archived)
                    .map((row) => ({
                        repository_type: row.repository_type,
                        repository_id: row.repository_id,
                        commit_sha: "c".repeat(40),
                        publication_id: "d".repeat(32),
                        publication_generation: 1,
                        published_at: "2026-10-20T12:00:00.000000Z",
                        total_bytes: 17,
                        file_count: 1,
                        verification_state: "unverified",
                    })),
            }),
        );
    throw new Error("Unexpected owned endpoint");
}
const owned: { store: LibraryStore; controller: SessionController }[] = [];
afterEach(() => {
    for (const item of owned.splice(0)) {
        item.store.dispose();
        item.controller.dispose();
    }
    vi.useRealTimers();
});
function setup(
    handler?: (
        url: URL,
        options: RequestInit | undefined,
    ) => Response | Promise<Response>,
) {
    const requests: URL[] = [],
        methods: string[] = [];
    let active = 0,
        peak = 0;
    let bootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: "https://state.invalid",
        configured_archive_id: ARCHIVE_ID,
    };
    const controller = createSessionController({
        bootstrap,
        storage: { getItem: () => null, setItem: () => {} },
        reconnect: () => Promise.resolve(bootstrap),
        fetcher: async (input, options) => {
            const url =
                input instanceof URL
                    ? input
                    : new URL(typeof input === "string" ? input : input.url);
            requests.push(url);
            methods.push(options?.method ?? "GET");
            active++;
            peak = Math.max(peak, active);
            try {
                return await (handler?.(url, options) ?? defaultResponse(url));
            } finally {
                active--;
            }
        },
    });
    const store = createLibraryStore(controller);
    owned.push({ store, controller });
    return {
        store,
        controller,
        requests,
        methods,
        peak: () => peak,
        setInstance() {
            bootstrap = {
                ...bootstrap,
                instance_id: "9".repeat(32),
                authority_epoch: "9".repeat(32),
            };
        },
    };
}

test("zero constructor reads, one bounded page plus explicit facets and keyed loaded-page supplements", async () => {
    const state = setup();
    expect(state.requests).toHaveLength(0);
    expect(state.store.snapshot().phase).toBe("idle");
    const first = state.store.refresh();
    expect(state.store.refresh()).toBe(first);
    await first;
    const view = state.store.snapshot();
    expect(view.phase).toBe("ready");
    expect(view.rows.map((row) => row.key)).toEqual([
        "dataset:owner/shared",
        "model:owner/shared",
    ]);
    expect(view.inventory.result).toMatchObject({ kind: "success" });
    expect(view.status.result).toMatchObject({ kind: "success" });
    expect(view.revisions.result).toMatchObject({ kind: "success" });
    expect(view.rows[0]?.currentRevision?.total_bytes).toBe(17);
    expect(view.rows[1]?.inventory?.retained_revisions).toBe(0);
    expect(view.rows.every((row) => row.enrichment === "complete")).toBe(true);
    expect(Object.values(view.facetCompatible)).toEqual([
        true,
        true,
        true,
        true,
    ]);
    expect(state.requests).toHaveLength(8);
    expect(state.methods.every((method) => method === "GET")).toBe(true);
    expect(state.peak()).toBeLessThanOrEqual(2);
    for (const url of state.requests.filter((url) =>
        [
            "/api/v1/repositories",
            "/api/v1/status",
            "/api/v1/repositories/revisions",
        ].includes(url.pathname),
    )) {
        expect(url.searchParams.getAll("selector")).toEqual([
            "dataset:owner/shared",
            "model:owner/shared",
        ]);
        expect(url.searchParams.get("limit")).toBe("100");
        expect(url.searchParams.has("cursor")).toBe(false);
    }
    expect(state.store.snapshot()).toBe(view);
});

test.each([false, true])(
    "zero known matches preserves incomplete coverage=%s and never starts unscoped supplements",
    async (incomplete) => {
        const state = setup((url) =>
            url.pathname === "/api/v1/catalog/search"
                ? jsonResponse(catalog([], { incomplete }))
                : defaultResponse(url, [], identity, incomplete),
        );
        await state.store.refresh();
        const view = state.store.snapshot();
        expect(view.phase).toBe(incomplete ? "partial_empty" : "empty");
        expect(view.rows).toEqual([]);
        expect(state.requests).toHaveLength(5);
    },
);

test.each([413, 503])(
    "catalog HTTP%s failure remains classified, never no matches",
    async (status) => {
        const state = setup(() =>
            jsonResponse(problemWire("HFAPI005", 20), status),
        );
        await state.store.refresh();
        expect(state.store.snapshot().phase).not.toMatch(/empty/u);
        expect(state.store.snapshot().catalog.result).toMatchObject({
            kind: "api_problem",
            status,
        });
        expect(state.requests).toHaveLength(1);
    },
);

test("malformed catalog page refuses instead of fabricating empty rows", async () => {
    const state = setup(() => jsonResponse({ ...catalog(), extra: true }));
    await state.store.refresh();
    expect(state.store.snapshot()).toMatchObject({
        phase: "failed",
        rows: [],
        catalog: { result: { kind: "protocol_failure" } },
    });
    expect(state.requests).toHaveLength(1);
});

test("opaque next/previous pages are explicit and filter changes reset captured cursor/query intent", async () => {
    const seen: string[] = [];
    const state = setup((url) => {
        if (url.pathname === "/api/v1/catalog/search") {
            seen.push(url.search);
            const cursor = url.searchParams.get("cursor");
            return jsonResponse(
                catalog(entries, {
                    cursor: cursor === null ? "page-2" : null,
                    total: 4,
                }),
            );
        }
        return defaultResponse(url, entries, identity, false, 4);
    });
    await state.store.refresh();
    await state.store.nextPage();
    expect(state.store.snapshot().pageIndex).toBe(1);
    await state.store.previousPage();
    expect(state.store.snapshot().pageIndex).toBe(0);
    await state.store.nextPage();
    await state.store.setFilters(
        normalizeLibraryFilters({ q: "literal", limit: 50 }),
    );
    expect(state.store.snapshot().pageIndex).toBe(0);
    expect(seen.at(-1)).toContain("q=literal");
    expect(seen.at(-1)).not.toContain("cursor");
});

test("curation409 resets whole walk once, a second refusal stays failed and visible", async () => {
    let search = 0;
    const state = setup((url) =>
        url.pathname === "/api/v1/catalog/search"
            ? ++search === 1
                ? jsonResponse(
                      catalog(entries, { cursor: "old-page", total: 4 }),
                  )
                : jsonResponse(problemWire("HFAPI007", 10), 409)
            : defaultResponse(url, entries, identity, false, 4),
    );
    await state.store.refresh();
    await state.store.nextPage();
    expect(search).toBe(3);
    expect(state.store.snapshot()).toMatchObject({
        pageIndex: 0,
        phase: "failed",
        notice: "stale_cursor",
    });
    expect(state.store.snapshot().catalog.result).toMatchObject({
        kind: "api_problem",
        status: 409,
    });
});

test("independent facet source drift retries finitely and preserves compatibility as explicit false", async () => {
    const state = setup((url) =>
        defaultResponse(
            url,
            entries,
            url.pathname === "/api/v1/catalog/facets"
                ? "b".repeat(64)
                : identity,
        ),
    );
    await state.store.refresh();
    expect(
        state.requests.filter(
            (url) => url.pathname === "/api/v1/catalog/search",
        ),
    ).toHaveLength(2);
    expect(state.store.snapshot()).toMatchObject({
        phase: "ready",
        notice: "catalog_changed",
    });
    expect(Object.values(state.store.snapshot().facetCompatible)).toEqual([
        false,
        false,
        false,
        false,
    ]);
});

test("authentication clears aggregate rows synchronously and late old response cannot refill new session", async () => {
    const delayed = deferred<Response>();
    let hold = false;
    const state = setup((url) =>
        hold && url.pathname === "/api/v1/catalog/search"
            ? delayed.promise
            : defaultResponse(url),
    );
    await state.store.refresh();
    expect(state.store.snapshot().rows).toHaveLength(2);
    hold = true;
    const old = state.store.refresh();
    await vi.waitFor(() => {
        expect(
            state.requests.filter(
                (url) => url.pathname === "/api/v1/catalog/search",
            ),
        ).toHaveLength(2);
    });
    state.controller.disconnect();
    expect(state.store.snapshot()).toMatchObject({
        connected: false,
        rows: [],
        phase: "unavailable",
    });
    state.setInstance();
    await state.controller.reconnect();
    hold = false;
    const fresh = state.store.refresh();
    delayed.resolve(
        defaultResponse(new URL("https://state.invalid/api/v1/catalog/search")),
    );
    await old;
    await fresh;
    expect(state.store.snapshot().connected).toBe(true);
    expect(state.store.snapshot().rows).toHaveLength(2);
});

test("inactive page ownership fences queued and explicit reads while retaining filter intent", async () => {
    const state = setup();
    const queued = state.store.refresh();
    state.store.setPageActive(false);
    const generation = state.store.snapshot().generation;
    state.store.setPageActive(false);
    await queued;
    await state.store.setFilters(
        normalizeLibraryFilters({ q: "owned return" }),
    );
    await state.store.refresh();
    await state.store.nextFacetPage("tag");
    expect(state.requests).toHaveLength(0);
    expect(state.store.snapshot()).toMatchObject({
        pageActive: false,
        filters: { q: "owned return" },
    });
    expect(state.store.snapshot().generation).toBe(generation + 1);
    state.store.setPageActive(true);
    expect(state.requests).toHaveLength(0);
    await state.store.refresh();
    expect(state.requests.length).toBeGreaterThan(0);
    expect(state.requests[0]?.searchParams.get("q")).toBe("owned return");
    expect(state.methods.every((method) => method === "GET")).toBe(true);
});

test("route pause aborts only owned reads and preserves validated same-session cache", async () => {
    const delayed = deferred<Response>();
    let hold = false,
        signal: AbortSignal | null | undefined;
    const state = setup((url, options) => {
        if (hold && url.pathname === "/api/v1/catalog/search") {
            signal = options?.signal;
            return delayed.promise;
        }
        return defaultResponse(url);
    });
    await state.store.refresh();
    hold = true;
    const old = state.store.refresh();
    await vi.waitFor(() => {
        expect(signal).toBeDefined();
    });
    state.store.pause();
    expect(signal?.aborted).toBe(true);
    expect(state.store.snapshot().rows).toHaveLength(2);
    delayed.resolve(
        defaultResponse(new URL("https://state.invalid/api/v1/catalog/search")),
    );
    await old;
    hold = false;
    await state.store.refresh();
    expect(state.store.snapshot().phase).toBe("ready");
});

test("cursor history has a finite explicit boundary and duplicate cursor stops without another read", async () => {
    let number = 0;
    const state = setup((url) =>
        url.pathname === "/api/v1/catalog/search"
            ? jsonResponse(
                  catalog(entries, {
                      cursor: "page-" + String(++number),
                      total: 1000,
                  }),
              )
            : defaultResponse(url, entries, identity, false, 1000),
    );
    await state.store.refresh();
    for (let i = 1; i < MAX_LIBRARY_PAGES; i++) await state.store.nextPage();
    expect(state.store.snapshot()).toMatchObject({
        pageIndex: 31,
        hasNext: false,
        notice: "page_limit",
    });
    const count = state.requests.length;
    await state.store.nextPage();
    expect(state.requests).toHaveLength(count);
    await state.store.previousPage();
    expect(state.store.snapshot().hasPrevious).toBe(true);
});

test("facet pagination replaces just its explicit page and a budget refusal does not restart the catalog", async () => {
    let refuse = false;
    const state = setup((url) => {
        if (
            url.pathname === "/api/v1/catalog/facets" &&
            url.searchParams.get("facet") === "tag"
        ) {
            if (url.searchParams.has("cursor") && refuse)
                return jsonResponse(problemWire("HFAPI005", 20), 413);
            return jsonResponse(
                wrapper(
                    "catalog.facets",
                    {
                        schema_version: 1,
                        catalog_identity: identity,
                        coverage: coverage(entries),
                        facet: "tag",
                        total_matches: 2,
                        entries: [
                            {
                                value: url.searchParams.has("cursor")
                                    ? "vision"
                                    : "text",
                                repository_count: 1,
                            },
                        ],
                    },
                    url.searchParams.has("cursor") ? null : "next-tag",
                ),
            );
        }
        return defaultResponse(url);
    });
    await state.store.refresh();
    const before = state.requests.length;
    await state.store.nextFacetPage("tag");
    expect(state.requests).toHaveLength(before + 1);
    const value = state.store.snapshot().facets.tag.result;
    expect(value).toMatchObject({
        kind: "success",
        payload: { entries: [{ value: "vision" }] },
    });
    expect(state.store.snapshot().facetCompatible.tag).toBe(true);
    await state.store.nextFacetPage("tag");
    expect(state.requests).toHaveLength(before + 1);
    await state.store.setFilters(normalizeLibraryFilters({ q: "new" }));
    refuse = true;
    const searchBefore = state.requests.filter(
        (url) => url.pathname === "/api/v1/catalog/search",
    ).length;
    await state.store.nextFacetPage("tag");
    expect(state.store.snapshot().facets.tag.result).toMatchObject({
        kind: "api_problem",
        status: 413,
    });
    expect(
        state.requests.filter(
            (url) => url.pathname === "/api/v1/catalog/search",
        ),
    ).toHaveLength(searchBefore);
});

test("stale facet continuation restarts from actual first-page closures once", async () => {
    const state = setup((url) => {
        if (
            url.pathname === "/api/v1/catalog/facets" &&
            url.searchParams.get("facet") === "tag"
        ) {
            if (url.searchParams.has("cursor"))
                return jsonResponse(problemWire("HFAPI007", 10), 409);
            return jsonResponse(
                wrapper(
                    "catalog.facets",
                    {
                        schema_version: 1,
                        catalog_identity: identity,
                        coverage: coverage(entries),
                        facet: "tag",
                        total_matches: 2,
                        entries: [{ value: "text", repository_count: 1 }],
                    },
                    "stale-tag",
                ),
            );
        }
        return defaultResponse(url);
    });
    await state.store.refresh();
    await state.store.nextFacetPage("tag");
    expect(state.store.snapshot().notice).toBe("stale_cursor");
    const tags = state.requests.filter(
        (url) => url.searchParams.get("facet") === "tag",
    );
    expect(tags.map((url) => url.searchParams.get("cursor"))).toEqual([
        null,
        "stale-tag",
        null,
    ]);
    expect(
        state.requests.filter(
            (url) => url.pathname === "/api/v1/catalog/search",
        ),
    ).toHaveLength(2);
});

test("malformed ancillary duplicates withhold enrichment while preserving real catalog matches", async () => {
    const state = setup((url) => {
        if (url.pathname === "/api/v1/repositories")
            return jsonResponse(
                wrapper("list", {
                    repositories: [1, 2].map(() => ({
                        repository_type: "model",
                        repository_id: "owner/shared",
                        managed: true,
                        enabled: false,
                        current_commit_sha: null,
                        current_publication_id: null,
                        retained_revisions: 0,
                    })),
                }),
            );
        return defaultResponse(url);
    });
    await state.store.refresh();
    expect(state.store.snapshot()).toMatchObject({
        phase: "ready",
        notice: "join_unavailable",
    });
    expect(state.store.snapshot().rows).toHaveLength(2);
    expect(
        state.store
            .snapshot()
            .rows.every((row) => row.enrichment === "unavailable"),
    ).toBe(true);
});

test("invalid filters refuse before any network and disposal clears all facade evidence", async () => {
    const state = setup();
    expect(() =>
        state.store.setFilters(normalizeLibraryFilters({ cursor: "foreign" })),
    ).toThrow();
    expect(state.requests).toHaveLength(0);
    await state.store.refresh();
    const view = state.store.snapshot();
    expect(view.rows).toHaveLength(2);
    const before = state.requests.length;
    await state.store.setFilters(view.filters);
    expect(state.requests).toHaveLength(before);
    const observed = vi.fn();
    state.store.subscribe(() => {
        throw new Error("broken view");
    });
    state.store.subscribe(observed);
    state.store.dispose();
    expect(state.store.snapshot()).toMatchObject({
        connected: false,
        rows: [],
        phase: "unavailable",
    });
    await state.store.refresh();
    await state.store.nextPage();
    await state.store.previousPage();
    expect(state.requests).toHaveLength(before);
    expect(observed).toHaveBeenCalled();
});

test("pause before queued work performs no hidden request and interrupted enrichment leaves main stale for resume", async () => {
    const delayed = deferred<Response>();
    let hold = true;
    const state = setup((url) =>
        url.pathname === "/api/v1/repositories" && hold
            ? delayed.promise
            : defaultResponse(url),
    );
    const neverStarted = state.store.refresh();
    state.store.pause();
    await neverStarted;
    expect(state.requests).toHaveLength(0);
    const pending = state.store.refresh();
    await vi.waitFor(() => {
        expect(
            state.requests.some(
                (url) => url.pathname === "/api/v1/repositories",
            ),
        ).toBe(true);
    });
    expect(state.store.snapshot().phase).toBe("ready");
    state.store.pause();
    expect(state.store.snapshot().phase).toBe("stale");
    delayed.resolve(
        defaultResponse(new URL("https://state.invalid/api/v1/repositories")),
    );
    await pending;
    const stoppedCount = state.requests.length;
    await Promise.resolve();
    expect(state.requests).toHaveLength(stoppedCount);
    hold = false;
    await state.store.refresh();
    expect(state.store.snapshot().phase).toBe("ready");
    expect(
        Object.values(state.store.snapshot().facetCompatible).every(Boolean),
    ).toBe(true);
});

test("superseding a read during supplemental work never republishes cached previous aggregate evidence", async () => {
    const delayed = deferred<Response>();
    let hold = false;
    const state = setup((url) => {
        if (url.searchParams.get("q") === "new")
            return url.pathname === "/api/v1/catalog/search"
                ? jsonResponse(catalog([]))
                : defaultResponse(url, []);
        if (url.pathname === "/api/v1/repositories" && hold)
            return delayed.promise;
        return defaultResponse(url);
    });
    await state.store.refresh();
    const old = state.store.snapshot();
    expect(old.rows).toHaveLength(2);
    hold = true;
    const replacing = state.store.refresh();
    await vi.waitFor(() => {
        expect(
            state.requests.filter(
                (url) => url.pathname === "/api/v1/repositories",
            ),
        ).toHaveLength(2);
    });
    const fresh = state.store.setFilters(normalizeLibraryFilters({ q: "new" }));
    expect(state.store.snapshot().rows).toEqual([]);
    await fresh;
    expect(state.store.snapshot()).toMatchObject({ phase: "empty", rows: [] });
    delayed.resolve(
        defaultResponse(new URL("https://state.invalid/api/v1/repositories")),
    );
    await replacing;
    expect(state.store.snapshot()).toMatchObject({ phase: "empty", rows: [] });
    expect(state.store.snapshot()).not.toBe(old);
});
