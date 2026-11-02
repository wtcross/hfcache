/** Owned HTTP wires exercise the real client/session query store; no effect-adapter acceptance. */
import { afterEach, expect, test, vi } from "vitest";
import {
    createLibraryStore,
    LIBRARY_FACETS,
    MAX_LIBRARY_PAGES,
} from "../src/library/library-state";
import type { LibraryStore } from "../src/library/library-state";
import { normalizeLibraryFilters } from "../src/library/filters";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import type { CatalogCoverage, CatalogEntry } from "../src/wire/generated";
import {
    jsonResponse,
    readWire,
    problemWire,
    ARCHIVE_ID,
    statusPayload,
} from "./read-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import { deferred } from "./state-fixtures";
import { isRecord } from "../src/wire/runtime";

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

const pagingCoverage: CatalogCoverage = {
    ...coverage(entries),
    repositories: 4,
    tags_known: 4,
};
function pagingResponse(
    url: URL,
    options: {
        identity?: string;
        coverage?: CatalogCoverage;
        fingerprint?: string;
        tagCursor?: string | null;
        tagValue?: string;
        rows?: readonly CatalogEntry[];
    } = {},
): Response {
    const common = {
        schema_version: 1,
        catalog_identity: options.identity ?? identity,
        coverage: options.coverage ?? pagingCoverage,
    };
    if (url.pathname === "/api/v1/catalog/search")
        return jsonResponse({
            ...wrapper(
                "catalog.search",
                {
                    ...common,
                    total_matches: 4,
                    entries: options.rows ?? entries,
                },
                url.searchParams.has("cursor") ? null : "main-next",
            ),
            config_fingerprint: options.fingerprint ?? fingerprint,
        });
    if (url.pathname === "/api/v1/catalog/facets") {
        const tag = url.searchParams.get("facet") === "tag";
        return jsonResponse({
            ...wrapper(
                "catalog.facets",
                {
                    ...common,
                    facet: url.searchParams.get("facet"),
                    total_matches: tag ? 3 : 0,
                    entries: tag
                        ? [
                              {
                                  value: options.tagValue ?? "historical",
                                  repository_count: 1,
                              },
                          ]
                        : [],
                },
                tag ? (options.tagCursor ?? null) : null,
            ),
            config_fingerprint: options.fingerprint ?? fingerprint,
        });
    }
    return defaultResponse(url);
}
const pageReadPaths = [
    "/api/v1/catalog/search",
    "/api/v1/repositories",
    "/api/v1/status",
    "/api/v1/repositories/revisions",
];
function expectPageReads(
    state: ReturnType<typeof setup>,
    from: number,
    facets: number,
) {
    const requested = state.requests.slice(from);
    expect(requested).toHaveLength(4 + facets);
    expect(requested.slice(0, 4).map((url) => url.pathname)).toEqual(
        pageReadPaths,
    );
    expect(
        requested.filter((url) => url.pathname === "/api/v1/catalog/facets"),
    ).toHaveLength(facets);
    expect(state.methods.slice(from).every((method) => method === "GET")).toBe(
        true,
    );
    expect(
        requested.every((url) => url.origin === "https://state.invalid"),
    ).toBe(true);
    expect(state.peak()).toBeLessThanOrEqual(2);
}

test("fresh main qualifies existing charged facet pages: initial8 Next4 Previous4 and explicit Refresh8", async () => {
    const state = setup((url) => pagingResponse(url));
    await state.store.refresh();
    expectPageReads(state, 0, 4);
    const first = state.store.snapshot();
    expect(first.facets.tag.result).toMatchObject({
        kind: "success",
        payload: { total_matches: 3, entries: [{ repository_count: 1 }] },
    });
    let from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 0);
    expect(state.store.snapshot().pageIndex).toBe(1);
    for (const name of LIBRARY_FACETS)
        expect(state.store.snapshot().facets[name]).toBe(first.facets[name]);
    expect(state.store.snapshot().rows[0]?.currentRevision?.total_bytes).toBe(
        17,
    );
    from = state.requests.length;
    await state.store.previousPage();
    expectPageReads(state, from, 0);
    from = state.requests.length;
    await state.store.refresh();
    expectPageReads(state, from, 4);
    expect(state.store.snapshot().facets.tag.result).not.toBe(
        first.facets.tag.result,
    );
});

test("no reuse decision starts before the fresh main response arrives", async () => {
    const later = deferred<Response>();
    let hold = false;
    const state = setup((url) =>
        hold && url.pathname === "/api/v1/catalog/search"
            ? later.promise
            : pagingResponse(url),
    );
    await state.store.refresh();
    const first = state.store.snapshot().facets;
    hold = true;
    const from = state.requests.length;
    const paging = state.store.nextPage();
    await vi.waitFor(() => {
        expect(state.requests).toHaveLength(from + 1);
    });
    expect(state.requests[from]?.pathname).toBe("/api/v1/catalog/search");
    later.resolve(
        pagingResponse(
            new URL(
                "https://state.invalid/api/v1/catalog/search?cursor=main-next",
            ),
        ),
    );
    await paging;
    expectPageReads(state, from, 0);
    for (const name of LIBRARY_FACETS)
        expect(state.store.snapshot().facets[name]).toBe(first[name]);
});

test.each([
    { q: "new literal" },
    { limit: 50 },
    { scope: "configured" },
    { revision_scope: "retained" },
    { tag_source: "current_only" },
    { tag_all: ["historical"] },
    { format: "parquet" },
])(
    "changed normalized filters %j obtain all fresh facets despite identical catalog evidence",
    async (patch) => {
        const state = setup((url) => pagingResponse(url));
        await state.store.refresh();
        const before = state.store.snapshot().facets.tag.result;
        const from = state.requests.length;
        await state.store.setFilters(normalizeLibraryFilters(patch));
        expectPageReads(state, from, 4);
        expect(state.store.snapshot().facets.tag.result).not.toBe(before);
    },
);

test.each(LIBRARY_FACETS)(
    "a failed %s facet alone is reread while three compatible pages are reused",
    async (name) => {
        let fail = true;
        const state = setup((url) =>
            fail &&
            url.pathname === "/api/v1/catalog/facets" &&
            url.searchParams.get("facet") === name
                ? jsonResponse(problemWire("HFAPI005", 20), 503)
                : pagingResponse(url),
        );
        await state.store.refresh();
        const before = state.store.snapshot().facets;
        expect(before[name].result).toMatchObject({
            kind: "api_problem",
            status: 503,
        });
        expect(state.store.snapshot().facetCompatible[name]).toBe(false);
        fail = false;
        const from = state.requests.length;
        await state.store.nextPage();
        expectPageReads(state, from, 1);
        expect(state.requests.at(-1)?.searchParams.get("facet")).toBe(name);
        for (const other of LIBRARY_FACETS)
            if (other !== name)
                expect(state.store.snapshot().facets[other]).toBe(
                    before[other],
                );
        expect(state.store.snapshot().facetCompatible[name]).toBe(true);
    },
);

test.each(LIBRARY_FACETS)(
    "an invalidated %s facet is missing fresh evidence and must be reacquired",
    async (name) => {
        const state = setup((url) => pagingResponse(url));
        await state.store.refresh();
        state.controller.queries.invalidate(
            (descriptor) =>
                descriptor.routeId === "catalog_facets_default" &&
                descriptor.predicates?.facet === name,
        );
        expect(state.store.snapshot().facetCompatible[name]).toBe(false);
        const from = state.requests.length;
        await state.store.nextPage();
        expectPageReads(state, from, 1);
        expect(state.requests.at(-1)?.searchParams.get("facet")).toBe(name);
    },
);

const incompleteCoverage: CatalogCoverage = {
    repositories: 50,
    tags_known: 50,
    tags_unknown: 0,
    publications: 50,
    usable: 25,
    partial: 0,
    unsupported: 0,
    failed: 0,
    missing: 25,
    technical_required: false,
    incomplete: true,
};
test.each([
    ["repositories", { repositories: 51, tags_known: 51 }],
    ["tag coverage", { tags_known: 49, tags_unknown: 1 }],
    ["publications", { publications: 51, missing: 26 }],
    ["usable", { usable: 24, missing: 26 }],
    ["partial", { partial: 1, missing: 24 }],
    ["unsupported", { unsupported: 1, missing: 24 }],
    ["failed", { failed: 1, missing: 24 }],
    ["missing", { missing: 24, usable: 26 }],
    ["technical requirement", { technical_required: true }],
    ["incomplete", { incomplete: false, missing: 0, usable: 50 }],
] as const)(
    "changed whole scoped %s evidence obtains all fresh facets even with the same catalog identity",
    async (_name, patch) => {
        let changed = false;
        const state = setup((url) =>
            pagingResponse(url, {
                coverage: changed
                    ? { ...incompleteCoverage, ...patch }
                    : incompleteCoverage,
            }),
        );
        await state.store.refresh();
        changed = true;
        const from = state.requests.length;
        await state.store.nextPage();
        expectPageReads(state, from, 4);
        expect(
            Object.values(state.store.snapshot().facetCompatible).every(
                Boolean,
            ),
        ).toBe(true);
        const main = state.store.snapshot().catalog.result;
        expect(main).toMatchObject({
            kind: "success",
            payload: { coverage: { ...incompleteCoverage, ...patch } },
        });
    },
);

test("manual tag pages and continuation history survive compatible Next and Previous, then changed fingerprints retire them", async () => {
    let changed = false;
    const state = setup((url) =>
        pagingResponse(url, {
            fingerprint: changed ? "b".repeat(64) : fingerprint,
            tagCursor: url.searchParams.has("cursor") ? "tag-last" : "tag-next",
            tagValue:
                url.searchParams.get("facet") === "tag" &&
                url.searchParams.get("cursor") === "tag-next"
                    ? "later"
                    : "historical",
        }),
    );
    await state.store.refresh();
    await state.store.nextFacetPage("tag");
    const manual = state.store.snapshot().facets.tag;
    expect(manual.result).toMatchObject({
        kind: "success",
        payload: { entries: [{ value: "later", repository_count: 1 }] },
        response: { next_cursor: "tag-last" },
    });
    let from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 0);
    expect(state.store.snapshot().facets.tag).toBe(manual);
    from = state.requests.length;
    await state.store.previousPage();
    expectPageReads(state, from, 0);
    expect(state.store.snapshot().facets.tag).toBe(manual);
    changed = true;
    from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 4);
    const rereadTag = state.requests
        .slice(from)
        .find((url) => url.searchParams.get("facet") === "tag");
    expect(rereadTag?.searchParams.has("cursor")).toBe(false);
    const newFrom = state.requests.length;
    await state.store.nextFacetPage("tag");
    expect(state.requests).toHaveLength(newFrom + 1);
    expect(state.requests.at(-1)?.searchParams.get("cursor")).toBe("tag-next");
});

test("tag-only catalog identity drift with an unchanged policy fingerprint keeps the bounded restart and reacquires facets", async () => {
    let changed = false;
    const state = setup((url) =>
        pagingResponse(url, {
            identity: changed ? "b".repeat(64) : identity,
            rows: changed
                ? entries.map((entry) => ({
                      ...entry,
                      tags: entry.configured ? ["curated"] : entry.tags,
                  }))
                : entries,
        }),
    );
    await state.store.refresh();
    changed = true;
    const from = state.requests.length;
    await state.store.nextPage();
    const requested = state.requests.slice(from);
    expect(requested).toHaveLength(9);
    expect(
        requested.filter((url) => url.pathname === "/api/v1/catalog/search"),
    ).toHaveLength(2);
    expect(
        requested.filter((url) => url.pathname === "/api/v1/catalog/facets"),
    ).toHaveLength(4);
    expect(state.store.snapshot()).toMatchObject({
        pageIndex: 0,
        notice: "catalog_changed",
    });
    expect(
        state.store.snapshot().rows.find((row) => row.entry.configured)?.entry
            .tags,
    ).toEqual(["curated"]);
    expect(
        Object.values(state.store.snapshot().facetCompatible).every(Boolean),
    ).toBe(true);
});

test("a changed facet wrapper fingerprint withholds its counts and retries finitely even when API scope has no pinned fingerprint", async () => {
    let changed = true;
    const state = setup((url) =>
        pagingResponse(url, {
            fingerprint:
                changed && url.searchParams.get("facet") === "tag"
                    ? "b".repeat(64)
                    : fingerprint,
        }),
    );
    expect(state.controller.apiReads.scope.configFingerprint).toBeNull();
    await state.store.refresh();
    expect(state.store.snapshot().notice).toBe("catalog_changed");
    expect(state.store.snapshot().facetCompatible.tag).toBe(false);
    expect(
        state.requests.filter(
            (url) => url.pathname === "/api/v1/catalog/search",
        ),
    ).toHaveLength(2);
    changed = false;
    const from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 1);
    expect(state.store.snapshot().facetCompatible.tag).toBe(true);
});

test("a facet with foreign archive proof stays failed and is individually reacquired", async () => {
    let foreign = true;
    const state = setup(async (url) => {
        if (foreign && url.searchParams.get("facet") === "tag") {
            const wire: unknown = await pagingResponse(url).json();
            if (!isRecord(wire)) throw new Error("Missing owned wire");
            return jsonResponse({
                ...wire,
                archive_id: "00000000-0000-4000-8000-000000000000",
            });
        }
        return pagingResponse(url);
    });
    await state.store.refresh();
    expect(state.store.snapshot().facets.tag.result).toMatchObject({
        kind: "protocol_failure",
    });
    expect(state.store.snapshot().facetCompatible.tag).toBe(false);
    foreign = false;
    const from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 1);
});

test("explicit Refresh rereads a compatible manually loaded tag page, while paging preserves its cursor-cycle fence", async () => {
    const state = setup((url) =>
        pagingResponse(url, {
            tagCursor: "repeat-tag",
            tagValue: url.searchParams.has("cursor") ? "later" : "historical",
        }),
    );
    await state.store.refresh();
    await state.store.nextFacetPage("tag");
    const manual = state.store.snapshot().facets.tag;
    let from = state.requests.length;
    await state.store.nextPage();
    expectPageReads(state, from, 0);
    expect(state.store.snapshot().facets.tag).toBe(manual);
    await state.store.nextFacetPage("tag");
    expect(state.requests).toHaveLength(from + 4);
    expect(state.store.snapshot().notice).toBe("cursor_cycle");
    from = state.requests.length;
    await state.store.refresh();
    expectPageReads(state, from, 4);
    expect(
        state.requests
            .slice(from)
            .find((url) => url.searchParams.get("facet") === "tag")
            ?.searchParams.get("cursor"),
    ).toBe("repeat-tag");
    expect(state.store.snapshot().facets.tag.result).not.toBe(manual.result);
});

async function replacedPublicationResponse(url: URL): Promise<Response> {
    const wire: unknown = await defaultResponse(url).json();
    if (
        !isRecord(wire) ||
        !isRecord(wire.envelope) ||
        !isRecord(wire.envelope.data)
    )
        throw new Error("Missing owned enrichment wire");
    const data = wire.envelope.data;
    const key = url.pathname.endsWith("/revisions")
        ? "revisions"
        : "repositories";
    const records = data[key];
    if (!Array.isArray(records)) throw new Error("Missing owned records");
    const next = records.map((row: unknown) => {
        if (!isRecord(row)) throw new Error("Missing owned row");
        if (row.repository_type !== "dataset") return row;
        if (key === "revisions")
            return {
                ...row,
                publication_id: "e".repeat(32),
                publication_generation: 2,
            };
        if (url.pathname === "/api/v1/status")
            return {
                ...row,
                current_publication_generation: 2,
                retained_generations: [2],
            };
        return { ...row, current_publication_id: "e".repeat(32) };
    });
    return jsonResponse({
        ...wire,
        envelope: { ...wire.envelope, data: { ...data, [key]: next } },
    });
}
test("same-SHA replacement publication changes catalog identity, obtains fresh facets and joins only the new publication generation", async () => {
    let repaired = false;
    const state = setup((url) => {
        if (repaired && pageReadPaths.slice(1).includes(url.pathname))
            return replacedPublicationResponse(url);
        return pagingResponse(url, {
            identity: repaired ? "b".repeat(64) : identity,
        });
    });
    await state.store.refresh();
    const original = state.store.snapshot().rows[0]?.currentRevision;
    expect(original?.publication_id).toBe("d".repeat(32));
    repaired = true;
    const from = state.requests.length;
    await state.store.nextPage();
    expect(state.requests.slice(from)).toHaveLength(9);
    expect(
        state.requests
            .slice(from)
            .filter((url) => url.pathname === "/api/v1/catalog/facets"),
    ).toHaveLength(4);
    const current = state.store.snapshot().rows[0]?.currentRevision;
    expect(current).toMatchObject({
        commit_sha: "c".repeat(40),
        publication_id: "e".repeat(32),
        publication_generation: 2,
        total_bytes: 17,
    });
    expect(current?.commit_sha).toBe(original?.commit_sha);
    expect(current).not.toBe(original);
});

test.each(["disconnect", "departure", "dispose"] as const)(
    "late main response on a reusable page cannot launch enrichment or facets after %s",
    async (action) => {
        const later = deferred<Response>();
        let hold = false;
        const state = setup((url) =>
            hold && url.pathname === "/api/v1/catalog/search"
                ? later.promise
                : pagingResponse(url),
        );
        await state.store.refresh();
        hold = true;
        const from = state.requests.length;
        const pending = state.store.nextPage();
        await vi.waitFor(() => {
            expect(state.requests).toHaveLength(from + 1);
        });
        if (action === "disconnect") state.controller.disconnect();
        else if (action === "departure") state.store.setPageActive(false);
        else state.store.dispose();
        later.resolve(
            pagingResponse(
                new URL(
                    "https://state.invalid/api/v1/catalog/search?cursor=main-next",
                ),
            ),
        );
        await pending;
        expect(state.requests).toHaveLength(from + 1);
        expect(state.store.snapshot().refreshing).toBe(false);
        if (action !== "departure")
            expect(state.store.snapshot().rows).toHaveLength(0);
        else {
            hold = false;
            state.store.setPageActive(true);
            const returned = state.requests.length;
            await state.store.refresh();
            expectPageReads(state, returned, 4);
        }
    },
);

test("new filter intent during a reusable-page main read replaces all facets and fences the late page", async () => {
    const later = deferred<Response>();
    let hold = false;
    const state = setup((url) =>
        hold &&
        url.pathname === "/api/v1/catalog/search" &&
        !url.searchParams.has("q")
            ? later.promise
            : pagingResponse(url),
    );
    await state.store.refresh();
    hold = true;
    const from = state.requests.length;
    const pending = state.store.nextPage();
    await vi.waitFor(() => {
        expect(state.requests).toHaveLength(from + 1);
    });
    const changed = state.requests.length;
    await state.store.setFilters(normalizeLibraryFilters({ q: "new" }));
    expectPageReads(state, changed, 4);
    const current = state.store.snapshot();
    later.resolve(
        pagingResponse(
            new URL(
                "https://state.invalid/api/v1/catalog/search?cursor=main-next",
            ),
        ),
    );
    await pending;
    expect(state.store.snapshot()).toBe(current);
    expect(state.requests).toHaveLength(changed + 8);
    expect(state.store.snapshot().filters.q).toBe("new");
});

test("reconnect changes API port and authentication generation and obtains all facets freshly", async () => {
    const state = setup((url) => pagingResponse(url));
    await state.store.refresh();
    const first = state.store.snapshot();
    const port = state.controller.apiReads;
    state.controller.disconnect();
    state.setInstance();
    await state.controller.reconnect();
    expect(state.controller.apiReads).not.toBe(port);
    const from = state.requests.length;
    await state.store.refresh();
    expectPageReads(state, from, 4);
    expect(state.store.snapshot().authGeneration).not.toBe(
        first.authGeneration,
    );
    for (const name of LIBRARY_FACETS)
        expect(state.store.snapshot().facets[name].result).not.toBe(
            first.facets[name].result,
        );
});
