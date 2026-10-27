/** WEB013: bounded exact-publication composition over the shared read/query owner. */
import type { ExactPublication } from "../api/identity";
import type { ReadOptions, ReadResponse, ReadResult } from "../api/types";
import type {
    QueryDescriptor,
    QueryHandle,
    QuerySnapshot,
} from "../state/query-state";
import type { SessionController } from "../state/session-controller";
import type {
    CatalogDetailPayload,
    CatalogVariantsPayload,
    EmptyPayload,
    ManifestPayload,
    ReferencePayload,
    RepositoriesPayload,
    RepositoryCardRead,
    ReportPayload,
    RevisionPayload,
    RevisionsPayload,
    RunsPayload,
    StatusPayload,
} from "../wire/generated";
import { exactPublication, isRepositoryTab } from "./routes";
import type {
    PublicationPair,
    RepositoryTarget,
    RepositoryTab,
    RepositoryView,
} from "./routes";

export const MAX_REPOSITORY_PAGES = 32;
export const REPOSITORY_PAGE_SIZE = 25;
export type RepositoryPage<T> = QuerySnapshot<T, EmptyPayload>;
export type RepositoryPhase =
    | "invalid"
    | "idle"
    | "loading"
    | "ready"
    | "unpublished"
    | "unavailable"
    | "failed";
export type RepositoryNotice =
    | "invalid"
    | "authentication"
    | "session_changed"
    | "publication_changed"
    | "page_limit"
    | "cursor_cycle"
    | "stale_cursor"
    | "join_unavailable"
    | null;
export interface RepositoryPagination {
    readonly pageIndex: number;
    readonly hasNext: boolean;
}
export interface RepositorySnapshot {
    readonly generation: number;
    readonly authGeneration: number;
    readonly connected: boolean;
    readonly target: RepositoryTarget | null;
    readonly view: RepositoryView;
    readonly selected: ExactPublication | null;
    readonly publicationGeneration: number | null;
    readonly phase: RepositoryPhase;
    readonly refreshing: boolean;
    readonly notice: RepositoryNotice;
    readonly current: RepositoryPage<ReferencePayload>;
    readonly selectedReference: RepositoryPage<ReferencePayload>;
    readonly retained: boolean | null;
    readonly manifest: RepositoryPage<ManifestPayload>;
    readonly catalog: RepositoryPage<CatalogDetailPayload>;
    readonly card: RepositoryPage<RepositoryCardRead>;
    readonly variants: RepositoryPage<CatalogVariantsPayload>;
    readonly revisions: RepositoryPage<RevisionsPayload>;
    readonly runs: RepositoryPage<RunsPayload>;
    readonly report: RepositoryPage<ReportPayload>;
    readonly currentFacts: {
        readonly inventory: RepositoryPage<RepositoriesPayload>;
        readonly status: RepositoryPage<StatusPayload>;
    };
    readonly selectedRevision: RevisionPayload | null;
    readonly manifestDigest: string | null;
    readonly reportRunId: string | null;
    readonly pagination: Readonly<
        Record<"variants" | "revisions" | "runs", RepositoryPagination>
    >;
}
type Controller = Pick<
    SessionController,
    "snapshot" | "subscribe" | "queries" | "apiReads"
>;
interface Slot<T> {
    readonly handle: QueryHandle<T, EmptyPayload>;
    readonly unsubscribe: () => void;
}
interface Pager {
    cursor: string | null;
    index: number;
    seen: Set<string>;
    identity: string | null;
}
type Panel = "variants" | "revisions" | "runs";
const IDLE: RepositoryPage<never> = Object.freeze({
    key: "",
    generation: 0,
    phase: "idle",
    result: null,
    reason: null,
});
const UNAVAILABLE: RepositoryPage<never> = Object.freeze({
    ...IDLE,
    phase: "unavailable",
    reason: "authentication",
});
function response<T>(value: RepositoryPage<T>): ReadResponse<T> | undefined {
    return value.phase === "ready" && value.result?.kind === "success"
        ? value.result.response
        : undefined;
}
async function boundedPage<T>(
    loading: Promise<ReadResult<T, EmptyPayload>>,
    count: (payload: T) => number,
): Promise<ReadResult<T, EmptyPayload>> {
    const result = await loading;
    return result.kind === "success" &&
        count(result.payload) > REPOSITORY_PAGE_SIZE
        ? { kind: "protocol_failure", reason: "bounds" }
        : result;
}
function missing<T>(value: RepositoryPage<T>) {
    return (
        value.phase === "failed" &&
        value.result?.kind === "api_problem" &&
        value.result.status === 404
    );
}
function stale(value: RepositoryPage<unknown>) {
    return value.result?.kind === "api_problem" && value.result.status === 409;
}
function newPager(): Pager {
    return { cursor: null, index: 0, seen: new Set(), identity: null };
}
function samePair(a: PublicationPair | null, b: PublicationPair | null) {
    return a === null || b === null
        ? a === b
        : a.commitSha === b.commitSha && a.publicationId === b.publicationId;
}

export function createRepositoryStore(controller: Controller) {
    let api = controller.apiReads,
        authGeneration = controller.snapshot().generation;
    let connected = controller.snapshot().connection === "connected",
        disposed = false;
    let target: RepositoryTarget | null = null;
    let view: RepositoryView = Object.freeze({ pair: null, tab: "overview" });
    let selected: ExactPublication | null = null,
        generation = 0;
    let expectedGeneration: number | null = null;
    let invalid = false,
        notice: RepositoryNotice = null,
        pending: Promise<void> | null = null;
    let currentRef: Slot<ReferencePayload> | null = null,
        manifest: Slot<ManifestPayload> | null = null;
    let selectedRef: Slot<ReferencePayload> | null = null;
    let catalog: Slot<CatalogDetailPayload> | null = null,
        card: Slot<RepositoryCardRead> | null = null;
    let variants: Slot<CatalogVariantsPayload> | null = null,
        revisions: Slot<RevisionsPayload> | null = null;
    let runs: Slot<RunsPayload> | null = null,
        report: Slot<ReportPayload> | null = null;
    let inventory: Slot<RepositoriesPayload> | null = null,
        status: Slot<StatusPayload> | null = null;
    let reportRunId: string | null = null;
    let pagers = {
        variants: newPager(),
        revisions: newPager(),
        runs: newPager(),
    };
    const listeners = new Set<() => void>();
    let cached: RepositorySnapshot | null = null,
        cachedSources: readonly unknown[] = [];
    function emit() {
        // Release aggregate aliases before QueryStore can replace/release their encoded charge.
        cached = null;
        cachedSources = [];
        for (const listener of listeners)
            try {
                listener();
            } catch {
                /* Detached views own no read authority. */
            }
    }
    function slot<T>(
        descriptor: QueryDescriptor,
        load: (options: ReadOptions) => Promise<ReadResult<T, EmptyPayload>>,
    ): Slot<T> {
        const handle = controller.queries.query(descriptor, load);
        return { handle, unsubscribe: handle.subscribe(emit) };
    }
    function allSlots() {
        return [
            currentRef,
            selectedRef,
            manifest,
            catalog,
            card,
            variants,
            revisions,
            runs,
            report,
            inventory,
            status,
        ];
    }
    function forget(
        value: {
            readonly unsubscribe: () => void;
            readonly handle: { invalidate(): void };
        } | null,
    ) {
        value?.unsubscribe();
        value?.handle.invalidate();
    }
    function resetDerived() {
        for (const value of [
            selectedRef,
            manifest,
            catalog,
            card,
            variants,
            revisions,
            runs,
            report,
        ])
            forget(value);
        manifest = null;
        selectedRef = null;
        catalog = null;
        card = null;
        variants = null;
        revisions = null;
        runs = null;
        report = null;
        reportRunId = null;
        expectedGeneration = null;
        pagers = {
            variants: newPager(),
            revisions: newPager(),
            runs: newPager(),
        };
    }
    function retire() {
        resetDerived();
        for (const value of [currentRef, inventory, status]) forget(value);
        currentRef = null;
        inventory = null;
        status = null;
        selected = null;
        cached = null;
        cachedSources = [];
    }
    function abortLoading() {
        for (const value of allSlots())
            if (
                value?.handle.snapshot().phase === "loading" ||
                value?.handle.snapshot().phase === "stale"
            )
                value.handle.invalidate();
    }
    function retireInactivePanels(tab: RepositoryTab) {
        // Leave inactive caching to QueryStore; retain no private aggregate aliases or subscriptions.
        if (tab !== "overview" && tab !== "details") {
            forget(catalog);
            catalog = null;
        }
        if (tab !== "details") {
            resetPanel("variants");
            pagers.variants = newPager();
        }
        if (tab !== "revisions" && tab !== "integrity") {
            resetPanel("revisions");
            pagers.revisions = newPager();
        }
        if (tab !== "activity") {
            resetPanel("runs");
            pagers.runs = newPager();
            forget(report);
            report = null;
            reportRunId = null;
        }
    }
    function sessionChanged() {
        if (disposed) return;
        const state = controller.snapshot(),
            port = controller.apiReads,
            available = state.connection === "connected";
        if (
            state.generation === authGeneration &&
            port === api &&
            available === connected
        )
            return;
        generation++;
        pending = null;
        retire();
        authGeneration = state.generation;
        api = port;
        connected = available;
        notice = available ? "session_changed" : "authentication";
        emit();
    }
    const unsubscribeController = controller.subscribe(sessionChanged);
    function page<T>(value: Slot<T> | null): RepositoryPage<T> {
        return (
            value?.handle.snapshot() ??
            (connected && !disposed ? IDLE : UNAVAILABLE)
        );
    }
    function compatible<T>(
        value: RepositoryPage<T>,
        check: (data: T) => boolean,
    ): RepositoryPage<T> {
        const read = response(value);
        if (read === undefined || check(read.envelope.data)) return value;
        return Object.freeze({ ...value, phase: "failed", result: null });
    }
    function pagination<T>(
        name: Panel,
        value: RepositoryPage<T>,
    ): RepositoryPagination {
        const cursor = response(value)?.next_cursor ?? null,
            pager = pagers[name];
        return Object.freeze({
            pageIndex: pager.index,
            hasNext:
                connected &&
                !disposed &&
                cursor !== null &&
                pager.index + 1 < MAX_REPOSITORY_PAGES &&
                !pager.seen.has(cursor),
        });
    }
    function snapshot(): RepositorySnapshot {
        sessionChanged();
        const current = page(currentRef),
            selectedReference = page(selectedRef),
            manifestPage = page(manifest),
            catalogPage = page(catalog),
            cardPage = page(card);
        const variantsPage = page(variants),
            revisionsPage = page(revisions),
            runsPage = page(runs),
            reportPage = page(report);
        const inventoryPage = page(inventory),
            statusPage = page(status);
        const sources = [
            generation,
            authGeneration,
            connected,
            disposed,
            invalid,
            target,
            view,
            selected,
            expectedGeneration,
            notice,
            pending,
            reportRunId,
            current,
            selectedReference,
            manifestPage,
            catalogPage,
            cardPage,
            variantsPage,
            revisionsPage,
            runsPage,
            reportPage,
            inventoryPage,
            statusPage,
            pagers.variants.index,
            pagers.revisions.index,
            pagers.runs.index,
        ];
        if (
            cached !== null &&
            sources.length === cachedSources.length &&
            sources.every((v, i) => v === cachedSources[i])
        )
            return cached;
        const coherentManifest = compatible(
            manifestPage,
            (data) =>
                expectedGeneration === null ||
                data.manifest.publication_generation === expectedGeneration,
        );
        const authoritative =
            response(coherentManifest)?.envelope.data.manifest;
        const publicationGeneration =
            authoritative?.publication_generation ?? null;
        const reference = response(selectedReference)?.envelope.data.reference;
        const retained =
            selected === null
                ? null
                : reference === undefined
                  ? missing(selectedReference)
                      ? false
                      : null
                  : reference.commit_sha === selected.commitSha &&
                    reference.publication_id === selected.publicationId &&
                    (expectedGeneration === null ||
                        reference.publication_generation ===
                            expectedGeneration);
        const agrees = (item: {
            commit_sha: string;
            publication_id: string;
            publication_generation: number;
        }) =>
            selected !== null &&
            retained === true &&
            authoritative !== undefined &&
            item.commit_sha === selected.commitSha &&
            item.publication_id === selected.publicationId &&
            item.publication_generation === publicationGeneration;
        const coherentCatalog = compatible(
            catalogPage,
            (data) =>
                selected === null ||
                (retained === true &&
                    authoritative !== undefined &&
                    data.observations.every(agrees)),
        );
        const coherentCard = compatible(cardPage, agrees);
        const coherentVariants = compatible(
            variantsPage,
            (data) =>
                retained === true &&
                authoritative !== undefined &&
                data.entries.every(agrees),
        );
        const joined =
            response(revisionsPage)?.envelope.data.revisions.filter(
                (item) =>
                    target !== null &&
                    item.repository_type === target.repositoryType &&
                    item.repository_id === target.repositoryId &&
                    agrees(item),
            ) ?? [];
        const selectedRevision =
            joined.length === 1 ? (joined[0] ?? null) : null;
        let phase: RepositoryPhase = invalid
            ? "invalid"
            : target === null
              ? "idle"
              : !connected || disposed
                ? "unavailable"
                : "idle";
        if (!invalid && target !== null && connected && !disposed) {
            const source =
                selected === null
                    ? current
                    : retained === true
                      ? coherentManifest
                      : selectedReference;
            phase =
                source.phase === "loading" ||
                (source.phase === "stale" && pending !== null)
                    ? "loading"
                    : source.phase === "ready"
                      ? "ready"
                      : source.phase === "unavailable"
                        ? "unavailable"
                        : source.phase === "failed"
                          ? "failed"
                          : "idle";
            if (selected === null && missing(current)) phase = "unpublished";
            else if (selected !== null && missing(manifestPage))
                phase = "unavailable";
            if (selected !== null && retained === false) phase = "unavailable";
        }
        const currentPair = response(current)?.envelope.data.reference;
        const changed =
            selected !== null &&
            currentPair !== undefined &&
            (currentPair.commit_sha !== selected.commitSha ||
                currentPair.publication_id !== selected.publicationId);
        const incompatible =
            coherentManifest !== manifestPage ||
            coherentCatalog !== catalogPage ||
            coherentCard !== cardPage ||
            coherentVariants !== variantsPage ||
            joined.length > 1;
        cached = Object.freeze({
            generation,
            authGeneration,
            connected: connected && !disposed,
            target,
            view,
            selected,
            publicationGeneration,
            phase,
            refreshing: pending !== null,
            notice: incompatible
                ? "join_unavailable"
                : (notice ?? (changed ? "publication_changed" : null)),
            current,
            selectedReference,
            retained,
            manifest: coherentManifest,
            catalog: coherentCatalog,
            card: coherentCard,
            variants: coherentVariants,
            revisions: revisionsPage,
            runs: runsPage,
            report: reportPage,
            currentFacts: Object.freeze({
                inventory: inventoryPage,
                status: statusPage,
            }),
            selectedRevision,
            manifestDigest:
                response(coherentCard)?.envelope.data.manifest_digest ?? null,
            reportRunId,
            pagination: Object.freeze({
                variants: pagination("variants", coherentVariants),
                revisions: pagination("revisions", revisionsPage),
                runs: pagination("runs", runsPage),
            }),
        });
        cachedSources = sources;
        return cached;
    }
    function current(value: number) {
        return !disposed && connected && generation === value;
    }
    async function read(value: Slot<unknown>, force: boolean) {
        if (force || value.handle.snapshot().phase !== "ready")
            await value.handle.refresh();
    }
    function paths(value: RepositoryTarget) {
        const [namespace, name] = value.repositoryId.split("/");
        // exactPublication validates the repository grammar before any slot is created.
        return {
            repository_type: value.repositoryType,
            namespace: namespace ?? "",
            name: name ?? "",
        };
    }
    function ensureCommon() {
        if (target === null) return;
        const owned = target,
            port = api,
            path = paths(owned),
            query = {
                selector: [owned.repositoryType + ":" + owned.repositoryId],
                limit: 1,
            };
        currentRef ??= slot(
            {
                routeId: "reference_default",
                path: { ...path, revision: "current" },
            },
            (options) =>
                port.readReference(
                    owned.repositoryType,
                    owned.repositoryId,
                    "current",
                    options,
                ),
        );
        inventory ??= slot(
            { routeId: "repositories_default", predicates: query },
            (options) => port.readRepositories(query, options),
        );
        status ??= slot(
            { routeId: "status_default", predicates: query },
            (options) => port.readStatus(options, query),
        );
        if (selected === null && view.pair !== null)
            selected = exactPublication(owned, view.pair);
        if (selected !== null && manifest === null) {
            const publication = selected;
            selectedRef ??= slot(
                {
                    routeId: "reference_default",
                    path: { ...path, revision: publication.commitSha },
                    publication,
                },
                (options) =>
                    port.readReference(
                        publication.repositoryType,
                        publication.repositoryId,
                        publication.commitSha,
                        options,
                    ),
            );
            manifest = slot(
                {
                    routeId: "manifest_default",
                    path: {
                        ...path,
                        commit_sha: publication.commitSha,
                        publication_id: publication.publicationId,
                    },
                    publication,
                },
                (options) => port.readManifest(publication, options),
            );
        }
    }
    function pinCurrent() {
        if (target === null || selected !== null) return;
        const reference = response(page(currentRef))?.envelope.data.reference;
        if (reference === undefined) return;
        const pair = Object.freeze({
            commitSha: reference.commit_sha,
            publicationId: reference.publication_id,
        });
        selected = exactPublication(target, pair);
        expectedGeneration = reference.publication_generation;
        view = Object.freeze({ ...view, pair });
        ensureCommon();
        emit();
    }
    function ensureCatalog() {
        if (catalog !== null || target === null) return;
        const owned = target,
            port = api,
            publication = selected;
        const query =
            publication === null
                ? {}
                : {
                      commit_sha: publication.commitSha,
                      publication_id: publication.publicationId,
                  };
        catalog = slot(
            {
                routeId: "catalog_detail_default",
                path: paths(owned),
                predicates: query,
                ...(publication === null ? {} : { publication }),
            },
            (options) =>
                port.readCatalogDetail(
                    owned.repositoryType,
                    owned.repositoryId,
                    query,
                    options,
                ),
        );
    }
    function pinExpectedFromCurrent() {
        const reference = response(page(currentRef))?.envelope.data.reference;
        if (
            selected !== null &&
            expectedGeneration === null &&
            reference !== undefined &&
            reference.commit_sha === selected.commitSha &&
            reference.publication_id === selected.publicationId
        )
            expectedGeneration = reference.publication_generation;
    }
    function acceptSelectedReference(): boolean {
        const reference = response(page(selectedRef))?.envelope.data.reference;
        if (
            reference === undefined ||
            selected === null ||
            reference.commit_sha !== selected.commitSha ||
            reference.publication_id !== selected.publicationId
        )
            return false;
        expectedGeneration ??= reference.publication_generation;
        return reference.publication_generation === expectedGeneration;
    }
    function ensureCard() {
        if (card !== null || selected === null) return;
        const publication = selected,
            port = api;
        card = slot(
            {
                routeId: "repository_card_default",
                path: {
                    ...paths(publication),
                    commit_sha: publication.commitSha,
                    publication_id: publication.publicationId,
                },
                publication,
            },
            (options) => port.readRepositoryCard(publication, options),
        );
    }
    function ensurePanel(name: Panel) {
        if (target === null) return;
        const port = api,
            owned = target,
            publication = selected,
            pager = pagers[name];
        const base = {
            limit: REPOSITORY_PAGE_SIZE,
            ...(pager.cursor === null ? {} : { cursor: pager.cursor }),
        };
        if (
            name === "variants" &&
            variants === null &&
            publication !== null &&
            owned.repositoryType === "model"
        ) {
            const query = {
                ...base,
                commit_sha: publication.commitSha,
                publication_id: publication.publicationId,
            };
            variants = slot(
                {
                    routeId: "catalog_variants_default",
                    path: paths(owned),
                    predicates: query,
                    publication,
                },
                (options) =>
                    boundedPage(
                        port.readCatalogVariants(
                            owned.repositoryType,
                            owned.repositoryId,
                            query,
                            options,
                        ),
                        (data) => data.entries.length,
                    ),
            );
        } else if (name === "revisions" && revisions === null) {
            const query = {
                ...base,
                selector: [owned.repositoryType + ":" + owned.repositoryId],
            };
            revisions = slot(
                { routeId: "revisions_default", predicates: query },
                (options) =>
                    boundedPage(
                        port.readRevisions(query, options),
                        (data) => data.revisions.length,
                    ),
            );
        } else if (name === "runs" && runs === null) {
            runs = slot(
                { routeId: "runs_default", predicates: base },
                (options) =>
                    boundedPage(
                        port.readRuns(base, options),
                        (data) => data.runs.length,
                    ),
            );
        }
    }
    function panel(name: Panel) {
        return name === "variants"
            ? variants
            : name === "revisions"
              ? revisions
              : runs;
    }
    function resetPanel(name: Panel) {
        forget(panel(name));
        if (name === "variants") variants = null;
        else if (name === "revisions") revisions = null;
        else runs = null;
    }
    function cursor(name: Panel): string | null {
        if (name === "variants")
            return response(page(variants))?.next_cursor ?? null;
        if (name === "revisions")
            return response(page(revisions))?.next_cursor ?? null;
        return response(page(runs))?.next_cursor ?? null;
    }
    function panelChanged(name: Panel): boolean {
        const value = panel(name);
        if (value === null) return false;
        if (stale(value.handle.snapshot())) return true;
        if (name === "variants") {
            const identity = response(page(variants))?.envelope.data
                .catalog_identity;
            if (identity !== undefined) {
                const previous = pagers.variants.identity;
                pagers.variants.identity = identity;
                return (
                    previous !== null &&
                    previous !== identity &&
                    pagers.variants.index > 0
                );
            }
        }
        return false;
    }
    async function loadPanel(name: Panel, force: boolean, resetAllowed = true) {
        ensurePanel(name);
        const value = panel(name),
            started = generation;
        if (value === null) return;
        await read(value, force);
        if (!current(started)) return;
        if (panelChanged(name)) {
            notice = "stale_cursor";
            if (resetAllowed) {
                resetPanel(name);
                pagers[name] = newPager();
                await loadPanel(name, false, false);
            }
        }
        emit();
    }
    async function load(force = false, revalidateSelected = false) {
        if (target === null || disposed || !connected || invalid) return;
        ensureCommon();
        const started = generation;
        if (currentRef === null) return;
        // An explicit bookmark never adopts current; an unqualified route resolves it once.
        await read(currentRef, force);
        if (!current(started)) return;
        if (selected === null) pinCurrent();
        pinExpectedFromCurrent();
        if (selected !== null && selectedRef !== null) {
            await read(selectedRef, force || revalidateSelected);
            if (!current(started)) return;
            if (!acceptSelectedReference()) return;
        }
        if (selected !== null && manifest !== null) await read(manifest, force);
        if (!current(started)) return;
        const manifestGeneration = response(page(manifest))?.envelope.data
            .manifest.publication_generation;
        if (expectedGeneration === null && manifestGeneration !== undefined)
            expectedGeneration = manifestGeneration;
        const authoritative =
            manifestGeneration !== undefined &&
            manifestGeneration === expectedGeneration;
        if (inventory !== null && status !== null)
            await Promise.all([read(inventory, force), read(status, force)]);
        if (!current(started)) return;
        // A failed exact publication is never replaced by an unqualified metadata read.
        if (!authoritative && selected !== null) return;
        if (selected === null && !missing(page(currentRef))) return;
        if (view.tab === "overview" || view.tab === "details") {
            ensureCatalog();
            if (view.tab === "overview" && authoritative) ensureCard();
            if (catalog !== null) {
                if (view.tab === "overview" && card !== null)
                    await Promise.all([
                        read(catalog, force),
                        read(card, force),
                    ]);
                else await read(catalog, force);
            }
            if (!current(started)) return;
            if (
                view.tab === "details" &&
                authoritative &&
                target.repositoryType === "model"
            )
                await loadPanel("variants", force);
        } else if (view.tab === "files") {
            if (authoritative) {
                ensureCard();
                if (card !== null) await read(card, force);
            }
        } else if (view.tab === "revisions" || view.tab === "integrity")
            await loadPanel("revisions", force);
        else await loadPanel("runs", force);
    }
    async function rejoinSelected(): Promise<boolean> {
        if (selected === null) return true;
        const proof = selectedRef,
            started = generation;
        if (proof === null) return false;
        await read(proof, true);
        return current(started) && acceptSelectedReference();
    }
    function run(work: () => Promise<void>): Promise<void> {
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
    function open(
        nextTarget: RepositoryTarget,
        nextView: RepositoryView,
    ): Promise<void> {
        sessionChanged();
        let checked: ExactPublication;
        try {
            if (!isRepositoryTab(nextView.tab)) throw new Error("invalid");
            checked = exactPublication(
                nextTarget,
                nextView.pair ?? {
                    commitSha: "0".repeat(40),
                    publicationId: "0".repeat(32),
                },
            );
        } catch {
            generation++;
            pending = null;
            retire();
            target = null;
            invalid = true;
            notice = "invalid";
            emit();
            return Promise.resolve();
        }
        const sameTarget =
            target?.repositoryType === checked.repositoryType &&
            target.repositoryId === checked.repositoryId;
        const sameSelection = sameTarget && samePair(view.pair, nextView.pair);
        if (sameSelection && view.tab === nextView.tab && !invalid) {
            if (pending !== null) return pending;
            return snapshot().phase === "idle"
                ? run(() => load())
                : Promise.resolve();
        }
        generation++;
        pending = null;
        abortLoading();
        if (!sameTarget) retire();
        else if (!sameSelection) resetDerived();
        target = Object.freeze({
            repositoryType: checked.repositoryType,
            repositoryId: checked.repositoryId,
        });
        view = Object.freeze({
            tab: nextView.tab,
            pair:
                nextView.pair === null
                    ? null
                    : Object.freeze({
                          commitSha: checked.commitSha,
                          publicationId: checked.publicationId,
                      }),
        });
        selected = nextView.pair === null ? null : checked;
        if (nextView.pair === null) currentRef?.handle.invalidate();
        invalid = false;
        notice = null;
        retireInactivePanels(nextView.tab);
        emit();
        return run(() => load(false, true));
    }
    return Object.freeze({
        snapshot,
        subscribe(listener: () => void) {
            listeners.add(listener);
            return () => {
                listeners.delete(listener);
            };
        },
        open,
        refresh(): Promise<void> {
            sessionChanged();
            if (disposed || !connected || target === null)
                return Promise.resolve();
            generation++;
            pending = null;
            abortLoading();
            notice = null;
            for (const name of ["variants", "revisions", "runs"] as const) {
                resetPanel(name);
                pagers[name] = newPager();
            }
            return run(() => load(true));
        },
        selectCurrent(): Promise<void> {
            sessionChanged();
            if (target === null || disposed || !connected)
                return Promise.resolve();
            generation++;
            pending = null;
            abortLoading();
            resetDerived();
            selected = null;
            view = Object.freeze({ tab: view.tab, pair: null });
            currentRef?.handle.invalidate();
            notice = null;
            return run(() => load());
        },
        selectPublication(pair: PublicationPair): Promise<void> {
            return target === null
                ? Promise.resolve()
                : open(target, { tab: view.tab, pair });
        },
        setTab(tab: RepositoryTab): Promise<void> {
            return target === null
                ? Promise.resolve()
                : open(target, { tab, pair: view.pair });
        },
        nextVariantsPage(): Promise<void> {
            return next("variants");
        },
        nextRevisionsPage(): Promise<void> {
            return next("revisions");
        },
        nextRunsPage(): Promise<void> {
            return next("runs");
        },
        openReport(runId: string): Promise<void> {
            if (disposed || !connected || pending !== null)
                return Promise.resolve();
            if (!response(page(runs))?.envelope.data.runs.includes(runId)) {
                notice = "invalid";
                emit();
                return Promise.resolve();
            }
            forget(report);
            const port = api;
            reportRunId = runId;
            const value = slot(
                { routeId: "report_default", path: { run_id: runId } },
                (options) => port.readReport(runId, options),
            );
            report = value;
            return run(async () => {
                if (await rejoinSelected()) await read(value, false);
            });
        },
        pause() {
            generation++;
            pending = null;
            // A full route unmount releases active query owners and aggregate
            // aliases. The exact target/view bookmark survives for a fresh open.
            retire();
            emit();
        },
        dispose() {
            disposed = true;
            generation++;
            pending = null;
            unsubscribeController();
            retire();
            connected = false;
            emit();
            listeners.clear();
        },
    });
    function next(name: Panel): Promise<void> {
        if (disposed || !connected || pending !== null)
            return Promise.resolve();
        const nextCursor = cursor(name),
            pager = pagers[name];
        if (nextCursor === null) return Promise.resolve();
        if (
            pager.index + 1 >= MAX_REPOSITORY_PAGES ||
            pager.seen.has(nextCursor)
        ) {
            notice = pager.seen.has(nextCursor) ? "cursor_cycle" : "page_limit";
            emit();
            return Promise.resolve();
        }
        pager.seen.add(nextCursor);
        pager.cursor = nextCursor;
        pager.index++;
        resetPanel(name);
        notice = null;
        return run(async () => {
            if (await rejoinSelected()) await loadPanel(name, false);
        });
    }
}
export type RepositoryStore = ReturnType<typeof createRepositoryStore>;
