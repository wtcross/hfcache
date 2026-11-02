/** WEB012: one bounded displayed read chain; all transport and retention stay in QueryStore. */
import type { ReadResponse, ReadOptions, ReadResult } from "../api/types";
import type {
    QueryHandle,
    QuerySnapshot,
    QueryPhase,
} from "../state/query-state";
import type { SessionController } from "../state/session-controller";
import type {
    CatalogSearchPayload,
    CatalogFacetPayload,
    EmptyPayload,
    RepositoriesPayload,
    StatusPayload,
    RevisionsPayload,
} from "../wire/generated";
import {
    DEFAULT_LIBRARY_FILTERS,
    normalizeLibraryFilters,
    LibraryFilterError,
} from "./filters";
import type { LibraryFilters } from "./filters";
import { joinLibraryRows, libraryRepositoryKey } from "./joins";
import type { LibraryRow, ScopedLibraryRead } from "./joins";

export const LIBRARY_FACETS = [
    "tag",
    "format",
    "quantization_method",
    "quantization",
] as const;
export const MAX_LIBRARY_PAGES = 32;
export type LibraryFacet = (typeof LIBRARY_FACETS)[number];
export type LibraryPhase = QueryPhase | "empty" | "partial_empty";
export type LibraryNotice =
    | "authentication"
    | "session_changed"
    | "stale_cursor"
    | "catalog_changed"
    | "page_limit"
    | "cursor_cycle"
    | "join_unavailable"
    | null;
type Page<T> = QuerySnapshot<T, EmptyPayload>;
type Handle<T> = QueryHandle<T, EmptyPayload>;
type Controller = Pick<
    SessionController,
    "snapshot" | "subscribe" | "queries" | "apiReads"
>;
export interface LibrarySnapshot {
    readonly generation: number;
    readonly authGeneration: number;
    readonly connected: boolean;
    readonly pageActive: boolean;
    readonly filters: LibraryFilters;
    readonly phase: LibraryPhase;
    readonly refreshing: boolean;
    readonly catalog: Page<CatalogSearchPayload>;
    readonly facets: Readonly<Record<LibraryFacet, Page<CatalogFacetPayload>>>;
    readonly facetCompatible: Readonly<Record<LibraryFacet, boolean>>;
    readonly inventory: Page<RepositoriesPayload>;
    readonly status: Page<StatusPayload>;
    readonly revisions: Page<RevisionsPayload>;
    readonly rows: readonly LibraryRow[];
    readonly notice: LibraryNotice;
    readonly pageIndex: number;
    readonly hasNext: boolean;
    readonly hasPrevious: boolean;
}
interface Slot<T> {
    readonly handle: Handle<T>;
    readonly unsubscribe: () => void;
}
interface FacetSlot extends Slot<CatalogFacetPayload> {
    readonly filters: LibraryFilters;
    readonly authGeneration: number;
    readonly port: Controller["apiReads"];
}
interface Supplements {
    readonly signature: string;
    readonly inventory: Slot<RepositoriesPayload>;
    readonly status: Slot<StatusPayload>;
    readonly revisions: Slot<RevisionsPayload>;
}
const IDLE: Page<never> = Object.freeze({
    key: "",
    generation: 0,
    phase: "idle",
    result: null,
    reason: null,
});
const UNAVAILABLE: Page<never> = Object.freeze({
    ...IDLE,
    phase: "unavailable",
    reason: "authentication",
});
function success<T>(page: Page<T>, fresh = false): ReadResponse<T> | undefined {
    return (!fresh || page.phase === "ready") && page.result?.kind === "success"
        ? page.result.response
        : undefined;
}
function sameCatalogSource(
    main: CatalogSearchPayload,
    facet: CatalogFacetPayload,
): boolean {
    return (
        main.catalog_identity === facet.catalog_identity &&
        JSON.stringify(main.coverage) === JSON.stringify(facet.coverage)
    );
}
function stale<T>(page: Page<T>): boolean {
    return page.result?.kind === "api_problem" && page.result.status === 409;
}
function normalized(input: LibraryFilters): LibraryFilters {
    const value = normalizeLibraryFilters(input);
    if (value.cursor !== undefined) throw new LibraryFilterError("invalid");
    return value;
}

export function createLibraryStore(controller: Controller) {
    let filters = DEFAULT_LIBRARY_FILTERS;
    let api = controller.apiReads;
    let authGeneration = controller.snapshot().generation;
    let connected = controller.snapshot().connection === "connected";
    let generation = 0,
        pageIndex = 0;
    let cursors: (string | undefined)[] = [undefined];
    let catalogIdentity: string | null = null;
    let notice: LibraryNotice = null;
    let disposed = false,
        pageActive = true;
    let pending: Promise<void> | null = null;
    let catalog: Slot<CatalogSearchPayload> | null = null;
    let facets: Partial<Record<LibraryFacet, FacetSlot>> = {};
    let supplements: Supplements | null = null;
    let supplementVisible = false;
    let facetCursors: Partial<Record<LibraryFacet, string>> = {};
    let facetSeen: Record<LibraryFacet, Set<string>> = {
        tag: new Set(),
        format: new Set(),
        quantization_method: new Set(),
        quantization: new Set(),
    };
    const listeners = new Set<() => void>();
    let cached: LibrarySnapshot | null = null,
        cachedSources: readonly unknown[] = [];

    function emit() {
        // QueryStore may have released the previous response's charge already.
        // Keep no aggregate alias to replaced evidence between view reads.
        cached = null;
        cachedSources = [];
        for (const listener of listeners) {
            try {
                listener();
            } catch {
                /* Detached views cannot interrupt private-state clearing. */
            }
        }
    }
    function slot<T>(
        routeId: Parameters<Controller["queries"]["query"]>[0]["routeId"],
        query: Readonly<Record<string, unknown>>,
        load: (options: ReadOptions) => Promise<ReadResult<T, EmptyPayload>>,
    ): Slot<T> {
        const handle = controller.queries.query(
            { routeId, predicates: query },
            load,
        );
        return { handle, unsubscribe: handle.subscribe(emit) };
    }
    function forget(
        value:
            | {
                  readonly unsubscribe: () => void;
                  readonly handle: { readonly invalidate: () => void };
              }
            | null
            | undefined,
    ) {
        value?.unsubscribe();
        value?.handle.invalidate();
    }
    function forgetSupplements() {
        if (supplements !== null)
            for (const value of [
                supplements.inventory,
                supplements.status,
                supplements.revisions,
            ])
                forget(value);
        supplements = null;
        supplementVisible = false;
    }
    function retire() {
        forget(catalog);
        catalog = null;
        for (const value of Object.values(facets)) forget(value);
        facets = {};
        forgetSupplements();
        cached = null;
        cachedSources = [];
    }
    function resetPages() {
        pageIndex = 0;
        cursors = [undefined];
        catalogIdentity = null;
        facetCursors = {};
        facetSeen = {
            tag: new Set(),
            format: new Set(),
            quantization_method: new Set(),
            quantization: new Set(),
        };
    }
    function createCatalog() {
        const query = normalizeLibraryFilters({
            ...filters,
            ...(cursors[pageIndex] === undefined
                ? {}
                : { cursor: cursors[pageIndex] }),
        });
        const port = api;
        catalog = slot("catalog_search_default", query, (options) =>
            port.readCatalogSearch(query, options),
        );
    }
    function createFacet(facet: LibraryFacet) {
        const query = Object.freeze({
            ...filters,
            facet,
            ...(facetCursors[facet] === undefined
                ? {}
                : { cursor: facetCursors[facet] }),
        });
        const port = api;
        facets[facet] = {
            ...slot("catalog_facets_default", query, (options) =>
                port.readCatalogFacets(query, options),
            ),
            filters,
            authGeneration,
            port,
        };
    }
    function ensure() {
        if (catalog === null) createCatalog();
        for (const facet of LIBRARY_FACETS)
            if (facets[facet] === undefined) createFacet(facet);
    }
    function sessionChanged() {
        if (disposed) return;
        const current = controller.snapshot(),
            port = controller.apiReads;
        const available = current.connection === "connected";
        if (
            current.generation === authGeneration &&
            port === api &&
            available === connected
        )
            return;
        generation++;
        pending = null;
        retire();
        resetPages();
        api = port;
        authGeneration = current.generation;
        connected = available;
        notice = available ? "session_changed" : "authentication";
        emit();
    }
    const unsubscribeController = controller.subscribe(sessionChanged);
    function scoped<T>(
        page: Page<T>,
        fresh = true,
    ): ScopedLibraryRead<T> | undefined {
        const response = success(page, fresh);
        return response === undefined
            ? undefined
            : { scope: api.scope, response };
    }
    function compatibleFacet(
        main: ReadResponse<CatalogSearchPayload>,
        name: LibraryFacet,
    ): boolean {
        const value = facets[name];
        const response =
            value === undefined
                ? undefined
                : success(value.handle.snapshot(), true);
        return (
            value !== undefined &&
            response !== undefined &&
            value.filters === filters &&
            value.authGeneration === authGeneration &&
            value.port === api &&
            main.archive_id !== null &&
            main.archive_id === api.scope.archiveId &&
            main.config_fingerprint !== null &&
            (api.scope.configFingerprint === null ||
                main.config_fingerprint === api.scope.configFingerprint) &&
            main.archive_id === response.archive_id &&
            main.config_fingerprint === response.config_fingerprint &&
            sameCatalogSource(main.envelope.data, response.envelope.data)
        );
    }
    function snapshot(): LibrarySnapshot {
        sessionChanged();
        const empty = connected && !disposed ? IDLE : UNAVAILABLE;
        const main = catalog?.handle.snapshot() ?? empty;
        const facetPages = {
            tag: facets.tag?.handle.snapshot() ?? empty,
            format: facets.format?.handle.snapshot() ?? empty,
            quantization_method:
                facets.quantization_method?.handle.snapshot() ?? empty,
            quantization: facets.quantization?.handle.snapshot() ?? empty,
        };
        const inventory = supplementVisible
            ? (supplements?.inventory.handle.snapshot() ?? empty)
            : empty;
        const status = supplementVisible
            ? (supplements?.status.handle.snapshot() ?? empty)
            : empty;
        const revisions = supplementVisible
            ? (supplements?.revisions.handle.snapshot() ?? empty)
            : empty;
        const sources = [
            generation,
            authGeneration,
            connected,
            pageActive,
            disposed,
            filters,
            notice,
            pageIndex,
            pending,
            main,
            inventory,
            status,
            revisions,
            ...LIBRARY_FACETS.map((facet) => facetPages[facet]),
        ];
        if (
            cached !== null &&
            sources.length === cachedSources.length &&
            sources.every((source, index) => source === cachedSources[index])
        )
            return cached;
        const mainResponse = success(main);
        let rows: readonly LibraryRow[] = [];
        let viewNotice = notice;
        let joinFailed = false;
        if (mainResponse !== undefined) {
            try {
                const inventoryRead = scoped(inventory),
                    statusRead = scoped(status),
                    revisionRead = scoped(revisions);
                rows = joinLibraryRows(
                    { scope: api.scope, response: mainResponse },
                    {
                        ...(inventoryRead === undefined
                            ? {}
                            : { inventory: inventoryRead }),
                        ...(statusRead === undefined
                            ? {}
                            : { status: statusRead }),
                        ...(revisionRead === undefined
                            ? {}
                            : { revisions: revisionRead }),
                    },
                );
            } catch {
                viewNotice = "join_unavailable";
                try {
                    rows = joinLibraryRows({
                        scope: api.scope,
                        response: mainResponse,
                    });
                } catch {
                    joinFailed = true;
                }
            }
        }
        let phase: LibraryPhase = joinFailed ? "failed" : main.phase;
        if (
            mainResponse !== undefined &&
            main.phase === "ready" &&
            mainResponse.envelope.data.total_matches === 0
        )
            phase = mainResponse.envelope.data.coverage.incomplete
                ? "partial_empty"
                : "empty";
        const compatible = (facet: LibraryFacet) => {
            return (
                mainResponse !== undefined &&
                compatibleFacet(mainResponse, facet)
            );
        };
        const compatibility = {
            tag: compatible("tag"),
            format: compatible("format"),
            quantization_method: compatible("quantization_method"),
            quantization: compatible("quantization"),
        };
        const next =
            main.result?.kind === "success"
                ? main.result.response.next_cursor
                : null;
        cached = Object.freeze({
            generation,
            authGeneration,
            connected: connected && !disposed,
            pageActive: pageActive && !disposed,
            filters,
            phase,
            refreshing: pending !== null,
            catalog: main,
            facets: Object.freeze(facetPages),
            facetCompatible: Object.freeze(compatibility),
            inventory,
            status,
            revisions,
            rows,
            notice: viewNotice,
            pageIndex,
            hasPrevious: pageIndex > 0 && connected && !disposed,
            hasNext:
                next !== null &&
                pageIndex + 1 < MAX_LIBRARY_PAGES &&
                notice !== "cursor_cycle" &&
                connected &&
                !disposed,
        });
        cachedSources = sources;
        return cached;
    }
    function supplementSignature(
        entries: CatalogSearchPayload["entries"],
    ): string {
        return JSON.stringify(entries.map(libraryRepositoryKey).sort());
    }
    function prepareSupplements(entries: CatalogSearchPayload["entries"]) {
        const signature = supplementSignature(entries);
        if (supplements?.signature !== signature) {
            forgetSupplements();
            const selector = Object.freeze(
                entries.map(libraryRepositoryKey).sort(),
            );
            const query = Object.freeze({ selector, limit: 100 });
            const port = api;
            supplements = {
                signature,
                inventory: slot("repositories_default", query, (options) =>
                    port.readRepositories(query, options),
                ),
                status: slot("status_default", query, (options) =>
                    port.readStatus(options, query),
                ),
                revisions: slot("revisions_default", query, (options) =>
                    port.readRevisions(query, options),
                ),
            };
        }
        supplementVisible = true;
    }
    function current(value: number) {
        return !disposed && pageActive && connected && generation === value;
    }
    function prepareMain(
        main: Slot<CatalogSearchPayload>,
        resetAllowed: boolean,
    ): "loaded" | "missing" | "stale_cursor" | "catalog_changed" {
        const page = main.handle.snapshot();
        if (stale(page) && resetAllowed) return "stale_cursor";
        const response = success(page, true);
        if (response === undefined) return "missing";
        if (
            catalogIdentity !== null &&
            catalogIdentity !== response.envelope.data.catalog_identity &&
            pageIndex > 0 &&
            resetAllowed
        )
            return "catalog_changed";
        if (
            catalogIdentity !== null &&
            catalogIdentity !== response.envelope.data.catalog_identity
        )
            notice = "catalog_changed";
        catalogIdentity = response.envelope.data.catalog_identity;
        if (
            response.next_cursor !== null &&
            cursors.slice(0, pageIndex + 1).includes(response.next_cursor)
        )
            notice = "cursor_cycle";
        if (response.next_cursor !== null && pageIndex + 1 >= MAX_LIBRARY_PAGES)
            notice = "page_limit";
        const entries = response.envelope.data.entries;
        if (entries.length > 0) prepareSupplements(entries);
        else supplementVisible = false;
        return "loaded";
    }
    function facetChange(
        main: Slot<CatalogSearchPayload>,
        selected?: LibraryFacet,
    ): "stale_cursor" | "catalog_changed" | null {
        const response = success(main.handle.snapshot(), true);
        if (response === undefined) return null;
        for (const name of selected === undefined
            ? LIBRARY_FACETS
            : [selected]) {
            const page = facets[name]?.handle.snapshot() ?? IDLE;
            if (stale(page)) return "stale_cursor";
            const facet = success(page, true);
            if (facet !== undefined && !compatibleFacet(response, name))
                return "catalog_changed";
        }
        return null;
    }
    function nextCursor<T>(value: Slot<T> | null | undefined): string | null {
        return value === null || value === undefined
            ? null
            : (success(value.handle.snapshot(), true)?.next_cursor ?? null);
    }
    async function load(
        resetAllowed: boolean,
        reuseFacets = false,
    ): Promise<void> {
        if (disposed || !pageActive || !connected) return;
        ensure();
        const currentGeneration = generation,
            main = catalog;
        if (main === null) return;
        await main.handle.refresh();
        if (!current(currentGeneration)) return;
        const prepared = prepareMain(main, resetAllowed);
        if (prepared === "missing") return;
        if (prepared !== "loaded") {
            await restart(prepared);
            return;
        }
        const mainResponse = success(main.handle.snapshot(), true);
        if (mainResponse === undefined) return;
        // ADR145: only a fresh main read can qualify existing charged facet slots.
        const needed = LIBRARY_FACETS.filter((facet) => {
            const compatible = compatibleFacet(mainResponse, facet);
            if (compatible && reuseFacets) return false;
            if (!compatible) {
                forget(facets[facet]);
                Reflect.deleteProperty(facets, facet);
                Reflect.deleteProperty(facetCursors, facet);
                facetSeen[facet].clear();
                cached = null;
                cachedSources = [];
                createFacet(facet);
            }
            return true;
        });
        if (supplementVisible && supplements !== null) {
            const bundle = supplements;
            await Promise.all([
                bundle.inventory.handle.refresh(),
                bundle.status.handle.refresh(),
            ]);
            if (!current(currentGeneration)) return;
            await bundle.revisions.handle.refresh();
            if (!current(currentGeneration)) return;
        }
        // At most two calls are queued together: each QueryStore read reserves its bounded response first.
        for (const pair of [
            LIBRARY_FACETS.slice(0, 2),
            LIBRARY_FACETS.slice(2),
        ]) {
            await Promise.all(
                pair.map((facet) =>
                    !needed.includes(facet)
                        ? Promise.resolve()
                        : (facets[facet]?.handle.refresh() ??
                          Promise.resolve()),
                ),
            );
            if (!current(currentGeneration)) return;
        }
        const changed = facetChange(main);
        if (changed !== null) {
            if (resetAllowed) await restart(changed);
            else notice = changed;
        }
    }
    async function restart(reason: LibraryNotice) {
        generation++;
        notice = reason;
        forget(catalog);
        catalog = null;
        for (const facet of LIBRARY_FACETS) forget(facets[facet]);
        facets = {};
        supplementVisible = false;
        resetPages();
        await load(false);
    }
    function run(work: () => Promise<void>): Promise<void> {
        if (disposed || !pageActive || !connected) return Promise.resolve();
        if (pending !== null) return pending;
        const started = generation;
        const task = Promise.resolve()
            .then(() => (current(started) ? work() : undefined))
            .finally(() => {
                if (pending === task) {
                    pending = null;
                    emit();
                }
            });
        pending = task;
        emit();
        return task;
    }
    function pause() {
        const unfinished = pending !== null;
        generation++;
        pending = null;
        const active = [
            catalog,
            ...Object.values(facets),
            ...(supplements === null
                ? []
                : [
                      supplements.inventory,
                      supplements.status,
                      supplements.revisions,
                  ]),
        ];
        for (const value of active) {
            const phase = value?.handle.snapshot().phase;
            if (
                phase === "loading" ||
                phase === "stale" ||
                (unfinished && value === catalog)
            )
                value?.handle.invalidate();
        }
        emit();
    }
    return Object.freeze({
        snapshot,
        subscribe(listener: () => void) {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        setFilters(next: LibraryFilters): Promise<void> {
            const checked = normalized(next);
            if (JSON.stringify(checked) === JSON.stringify(filters))
                return Promise.resolve();
            generation++;
            pending = null;
            forget(catalog);
            catalog = null;
            for (const facet of LIBRARY_FACETS) {
                forget(facets[facet]);
            }
            facets = {};
            supplementVisible = false;
            if (supplements !== null)
                for (const value of [
                    supplements.inventory,
                    supplements.status,
                    supplements.revisions,
                ])
                    value.handle.invalidate();
            filters = checked;
            notice = null;
            resetPages();
            cached = null;
            emit();
            return run(() => load(true));
        },
        refresh(): Promise<void> {
            sessionChanged();
            if (disposed || !connected) return Promise.resolve();
            notice = null;
            return run(() => load(true));
        },
        nextPage(): Promise<void> {
            if (pending !== null || disposed || !connected)
                return Promise.resolve();
            const cursor = nextCursor(catalog);
            if (cursor === null) return Promise.resolve();
            if (pageIndex + 1 >= MAX_LIBRARY_PAGES) {
                notice = "page_limit";
                emit();
                return Promise.resolve();
            }
            if (cursors.slice(0, pageIndex + 1).includes(cursor)) {
                notice = "cursor_cycle";
                emit();
                return Promise.resolve();
            }
            cursors = [...cursors.slice(0, pageIndex + 1), cursor];
            pageIndex++;
            generation++;
            notice = null;
            forget(catalog);
            catalog = null;
            supplementVisible = false;
            return run(() => load(true, true));
        },
        previousPage(): Promise<void> {
            if (pending !== null || pageIndex === 0 || disposed || !connected)
                return Promise.resolve();
            pageIndex--;
            generation++;
            notice = null;
            forget(catalog);
            catalog = null;
            supplementVisible = false;
            return run(() => load(true, true));
        },
        nextFacetPage(facet: LibraryFacet): Promise<void> {
            if (pending !== null || disposed || !connected)
                return Promise.resolve();
            const next = nextCursor(facets[facet]);
            if (next === null) return Promise.resolve();
            if (facetSeen[facet].size >= MAX_LIBRARY_PAGES - 1) {
                notice = "page_limit";
                emit();
                return Promise.resolve();
            }
            if (facetSeen[facet].has(next)) {
                notice = "cursor_cycle";
                emit();
                return Promise.resolve();
            }
            facetSeen[facet].add(next);
            facetCursors[facet] = next;
            forget(facets[facet]);
            createFacet(facet);
            return run(async () => {
                const currentGeneration = generation;
                await facets[facet]?.handle.refresh();
                if (!current(currentGeneration)) return;
                const change =
                    catalog === null ? null : facetChange(catalog, facet);
                if (change !== null) await restart(change);
            });
        },
        pause,
        setPageActive(value: boolean) {
            if (disposed || pageActive === value) return;
            pageActive = value;
            if (!value) pause();
            else {
                // The mounted route parses its current fragment before reading.
                catalog?.handle.invalidate();
                emit();
            }
        },
        dispose() {
            disposed = true;
            generation++;
            pending = null;
            unsubscribeController();
            retire();
            resetPages();
            connected = false;
            notice = "authentication";
            emit();
            listeners.clear();
        },
    });
}
export type LibraryStore = ReturnType<typeof createLibraryStore>;
