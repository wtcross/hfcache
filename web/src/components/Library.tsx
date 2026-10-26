import {
    useCallback,
    useEffect,
    useRef,
    useState,
    useSyncExternalStore,
} from "react";
import type { FormEvent, MouseEvent } from "react";
import { Notice, Panel } from "../primitives";
import {
    libraryFragment,
    normalizeLibraryFilters,
    parseLibraryFragment,
    setLibraryType,
    updateLibraryFilters,
} from "../library/filters";
import type { LibraryFilterPatch, LibraryFilters } from "../library/filters";
import type {
    LibraryFacet,
    LibrarySnapshot,
    LibraryStore,
} from "../library/library-state";
import type { LibraryRow } from "../library/joins";
import type { CatalogCoverage } from "../wire/generated";
import { repositoryFragment, repositoryPath } from "../repository/routes";
import type { RepositoryTarget, RepositoryView } from "../repository/routes";

export type RepositoryNavigation = (
    event: MouseEvent<HTMLAnchorElement>,
    target: RepositoryTarget,
    view: RepositoryView,
) => void;

function count(value: number): string {
    return value.toLocaleString("en-US");
}
function logicalBytes(value: number): string {
    const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    let amount = value,
        unit = 0;
    while (amount >= 1024 && unit < units.length - 1) {
        amount /= 1024;
        unit++;
    }
    return `${amount.toLocaleString("en-US", { maximumFractionDigits: unit === 0 ? 0 : 1 })} ${units[unit] ?? "B"}`;
}
function upstream(row: LibraryRow): string {
    return (
        "https://huggingface.co/" +
        (row.entry.repository_type === "dataset" ? "datasets/" : "") +
        row.entry.repository_id.split("/").map(encodeURIComponent).join("/")
    );
}
function numeric(value: FormDataEntryValue | null): number | undefined {
    if (value === null || value === "") return undefined;
    if (typeof value !== "string" || !/^(?:0|[1-9][0-9]*)$/u.test(value))
        throw new Error("Invalid numeric filter.");
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed))
        throw new Error("Unsafe numeric filter.");
    return parsed;
}
const notices: Readonly<
    Record<Exclude<LibrarySnapshot["notice"], null>, string>
> = {
    authentication:
        "Reconnect to read the Library for the current authenticated archive.",
    session_changed:
        "The authenticated session changed. Previous private read evidence was cleared.",
    stale_cursor:
        "The catalog changed while paging. The read restarted at its first page once.",
    catalog_changed:
        "Catalog evidence changed between reads. Refresh to join current pages; incompatible facet counts are withheld.",
    page_limit:
        "This browser reached its 32-page limit. Narrow the filters or refresh from the first page.",
    cursor_cycle:
        "The server returned a repeated continuation. Paging stopped; refresh before continuing.",
    join_unavailable:
        "Some inventory or snapshot enrichment is unavailable. Missing evidence is shown as unknown.",
};

function Coverage({ coverage }: { coverage: CatalogCoverage }) {
    return (
        <Panel title="Know your coverage">
            <p>
                Technical observations describe the chosen publication scope.
                They do not establish archive integrity.
            </p>
            <dl className="coverage-facts">
                <dt>Usable observations</dt>
                <dd>{count(coverage.usable)}</dd>
                <dt>Partial observations</dt>
                <dd>{count(coverage.partial)}</dd>
                <dt>Unsupported observations</dt>
                <dd>{count(coverage.unsupported)}</dd>
                <dt>Failed observations</dt>
                <dd>{count(coverage.failed)}</dd>
                <dt>Missing observations</dt>
                <dd>{count(coverage.missing)}</dd>
                <dt>Repositories with known tags</dt>
                <dd>{count(coverage.tags_known)}</dd>
                <dt>Repositories with unknown tags</dt>
                <dd>{count(coverage.tags_unknown)}</dd>
            </dl>
            <p
                className={
                    coverage.incomplete ? "library-warning" : "library-muted"
                }
            >
                {coverage.incomplete
                    ? "Coverage is incomplete. Zero known matches does not prove absence."
                    : "Coverage is complete for this read scope."}
            </p>
        </Panel>
    );
}

function Row({
    row,
    selected,
    toggle,
    basePath,
    onOpenRepository,
}: {
    row: LibraryRow;
    selected: boolean;
    toggle: () => void;
    basePath: string;
    onOpenRepository: RepositoryNavigation | undefined;
}) {
    const entry = row.entry,
        variant = entry.representative_variant?.variant;
    const parts = entry.repository_id.split("/");
    const target = {
        repositoryType: entry.repository_type,
        repositoryId: entry.repository_id,
    };
    const currentView: RepositoryView = { pair: null, tab: "overview" };
    return (
        <tr>
            <td>
                <input
                    type="checkbox"
                    checked={selected}
                    onChange={toggle}
                    aria-label={`Select ${entry.repository_type} ${entry.repository_id}`}
                />
            </td>
            <th scope="row">
                <div className="library-repository">
                    <span
                        className={`repository-icon ${entry.repository_type}`}
                        aria-hidden="true"
                    >
                        {entry.repository_type === "model" ? "◇" : "▤"}
                    </span>
                    <div>
                        <span className="library-muted">{parts[0]}</span>
                        <strong>
                            <a
                                href={
                                    repositoryPath(target, basePath) +
                                    repositoryFragment(currentView)
                                }
                                onClick={(event) => {
                                    onOpenRepository?.(
                                        event,
                                        target,
                                        currentView,
                                    );
                                }}
                            >
                                {parts[1]}
                            </a>
                        </strong>
                        <small>
                            {entry.repository_type === "model"
                                ? "Model"
                                : "Dataset"}
                        </small>
                        <div className="repository-tags">
                            {entry.tags.map((tag) => (
                                <span key={tag}>{tag}</span>
                            ))}
                        </div>
                        <small>
                            {entry.tag_origin === "configured"
                                ? entry.tags.length === 0
                                    ? "Configured tags: none"
                                    : "Configured tags"
                                : entry.tag_origin === "last_observed"
                                  ? "Last-observed tags"
                                  : "Tags not observed"}
                        </small>
                        {entry.tag_origin === "last_observed" &&
                            entry.tag_observed_at !== null && (
                                <small>Observed {entry.tag_observed_at}</small>
                            )}
                        <a
                            href={upstream(row)}
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Open {entry.repository_type} on Hugging Face{" "}
                            <span aria-hidden="true">↗</span>
                        </a>
                    </div>
                </div>
            </th>
            <td>
                {entry.repository_type === "dataset" ? (
                    <>
                        <strong>
                            {entry.dataset_formats.length === 0
                                ? "Not observed"
                                : entry.dataset_formats.join(", ")}
                        </strong>
                        <small>Static format declarations</small>
                    </>
                ) : variant === undefined ? (
                    <>
                        <strong>Not observed</strong>
                        <small>No eligible primary variant was observed</small>
                    </>
                ) : (
                    <>
                        <strong>{variant.format}</strong>
                        <small>
                            {[
                                variant.quantization_method,
                                variant.quantization,
                                variant.bits === null
                                    ? null
                                    : `${String(variant.bits)}-bit declaration`,
                            ]
                                .filter((value) => value !== null)
                                .join(" · ") || "Complete primary variant"}
                        </small>
                        <small>
                            {count(entry.matching_variant_count)} matching
                            variants
                        </small>
                        {entry.representative_variant !== null && (
                            <details>
                                <summary>Matching variant publication</summary>
                                <code>
                                    {entry.representative_variant.commit_sha}
                                </code>
                                <br />
                                <code>
                                    {
                                        entry.representative_variant
                                            .publication_id
                                    }
                                </code>
                                <small>
                                    Publication generation{" "}
                                    {
                                        entry.representative_variant
                                            .publication_generation
                                    }
                                </small>
                                <small>
                                    Matching evidence may describe a retained
                                    publication.
                                </small>
                                <a
                                    href={
                                        repositoryPath(target, basePath) +
                                        repositoryFragment({
                                            pair: {
                                                commitSha:
                                                    entry.representative_variant
                                                        .commit_sha,
                                                publicationId:
                                                    entry.representative_variant
                                                        .publication_id,
                                            },
                                            tab: "details",
                                        })
                                    }
                                    onClick={(event) => {
                                        const representative =
                                            entry.representative_variant;
                                        if (representative !== null)
                                            onOpenRepository?.(event, target, {
                                                pair: {
                                                    commitSha:
                                                        representative.commit_sha,
                                                    publicationId:
                                                        representative.publication_id,
                                                },
                                                tab: "details",
                                            });
                                    }}
                                >
                                    Inspect matching publication
                                </a>
                            </details>
                        )}
                    </>
                )}
            </td>
            <td>
                <span
                    className={`archive-badge ${entry.archived ? (entry.configured ? "archived" : "unmanaged") : "unpublished"}`}
                >
                    {entry.archived
                        ? entry.configured
                            ? "Archived"
                            : "Unmanaged archive"
                        : "Not archived"}
                </span>
                <small>
                    {entry.configured
                        ? entry.enabled === true
                            ? "Sync enabled"
                            : entry.enabled === false
                              ? "Sync disabled"
                              : "Enablement unknown"
                        : "Outside current configuration"}
                </small>
                {row.status?.last_run_status !== null &&
                    row.status?.last_run_status !== undefined && (
                        <small>Last run: {row.status.last_run_status}</small>
                    )}
            </td>
            <td>
                {row.currentRevision === null ? (
                    <strong>
                        {!entry.archived ||
                        row.inventory?.current_publication_id === null
                            ? "No current snapshot"
                            : "Snapshot not joined"}
                    </strong>
                ) : (
                    <>
                        <strong>
                            {logicalBytes(row.currentRevision.total_bytes)}
                        </strong>
                        <small>
                            {count(row.currentRevision.file_count)} files ·
                            logical size
                        </small>
                        <small>
                            Verification:{" "}
                            {row.currentRevision.verification_state}
                        </small>
                        <details>
                            <summary>Exact publication</summary>
                            <code>{row.currentRevision.commit_sha}</code>
                            <br />
                            <code>{row.currentRevision.publication_id}</code>
                        </details>
                    </>
                )}
                <small>
                    {row.inventory === null
                        ? "Retained revision count not observed"
                        : `${count(row.inventory.retained_revisions)} retained revisions`}
                </small>
                {row.enrichment !== "complete" && (
                    <small className="library-warning">
                        {row.enrichment === "changed"
                            ? "Snapshot changed across reads; refresh to rejoin evidence"
                            : "Some enrichment is not observed on this bounded page"}
                    </small>
                )}
            </td>
        </tr>
    );
}

export function Library({
    store,
    basePath = "/ui/",
    onOpenRepository,
}: {
    store: LibraryStore;
    basePath?: string;
    onOpenRepository?: RepositoryNavigation;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const form = useRef<HTMLFormElement>(null);
    const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [filterError, setFilterError] = useState<string | null>(null);
    const [announcement, setAnnouncement] = useState<string | null>(null);
    const [selected, setSelected] = useState<{
        generation: number;
        keys: readonly string[];
    }>({ generation: state.generation, keys: [] });
    const [tagGroup, setTagGroup] = useState<"tag_all" | "tag_any">("tag_all");
    const catalog =
        state.catalog.result?.kind === "success"
            ? state.catalog.result.payload
            : null;
    const visibleSelection =
        selected.generation === state.generation
            ? selected.keys.filter((key) =>
                  state.rows.some((row) => row.key === key),
              )
            : [];
    const filters = state.filters;

    function cancelSearch() {
        if (searchTimer.current !== null) clearTimeout(searchTimer.current);
        searchTimer.current = null;
    }
    function syncForm(next: LibraryFilters) {
        const values: Readonly<Record<string, string>> = {
            q: next.q ?? "",
            tag_all: (next.tag_all ?? []).join(", "),
            tag_any: (next.tag_any ?? []).join(", "),
            format: next.format ?? "",
            quantization: next.quantization ?? "",
            quantization_method: next.quantization_method ?? "",
            bits: next.bits === undefined ? "" : String(next.bits),
            max_variant_bytes:
                next.max_variant_bytes === undefined
                    ? ""
                    : String(next.max_variant_bytes),
        };
        for (const [key, value] of Object.entries(values)) {
            const field = form.current?.elements.namedItem(key);
            if (field instanceof HTMLInputElement) field.value = value;
        }
    }
    const readFilters = useCallback(
        (next: LibraryFilters): Promise<void> => {
            const pending = store.setFilters(next);
            const current = store.snapshot();
            // Start/coalesce while this view owns the read. A settled old promise
            // must never restart requests after unmount has paused this owner.
            return current.connected &&
                ["idle", "stale"].includes(current.catalog.phase)
                ? store.refresh()
                : pending;
        },
        [store],
    );
    function replace(next: LibraryFilters, announce: string | null = null) {
        try {
            const fragment = libraryFragment(next);
            if (location.hash !== fragment)
                window.history.pushState(
                    null,
                    "",
                    window.location.pathname + fragment,
                );
            setFilterError(null);
            setAnnouncement(announce);
            void readFilters(next).catch(() => {
                setFilterError(
                    "The Library filters could not be applied. Refresh after checking the current connection.",
                );
            });
            return next;
        } catch {
            setFilterError(
                "These filters are invalid or exceed the supported bounds. The last valid filters remain in effect.",
            );
            return null;
        }
    }
    function apply(patch: LibraryFilterPatch) {
        try {
            const changed = updateLibraryFilters(
                store.snapshot().filters,
                patch,
            );
            return replace(changed.filters, changed.announcement);
        } catch {
            setFilterError(
                "These filters are invalid or exceed the supported bounds. The last valid filters remain in effect.",
            );
            return null;
        }
    }
    useEffect(() => {
        let active = true;
        const readLocation = () => {
            if (!active) return;
            cancelSearch();
            try {
                const next = parseLibraryFragment(window.location.hash);
                syncForm(next);
                setFilterError(null);
                setAnnouncement(null);
                if (state.connected)
                    void readFilters(next).catch(() => {
                        if (active)
                            setFilterError(
                                "The Library filters could not be applied. Refresh after checking the current connection.",
                            );
                    });
            } catch {
                store.pause();
                setFilterError(
                    "This Library address has invalid or unsupported filters. Clear filters to load a bounded Library page.",
                );
            }
        };
        queueMicrotask(readLocation);
        window.addEventListener("hashchange", readLocation);
        window.addEventListener("popstate", readLocation);
        return () => {
            active = false;
            cancelSearch();
            window.removeEventListener("hashchange", readLocation);
            window.removeEventListener("popstate", readLocation);
            store.pause();
        };
    }, [store, state.authGeneration, state.connected, readFilters]);
    function search(value: string) {
        cancelSearch();
        searchTimer.current = setTimeout(() => {
            apply({ q: value === "" ? undefined : value });
        }, 350);
    }
    function submitFilters(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        cancelSearch();
        try {
            const data = new FormData(event.currentTarget);
            const text = (name: string) => {
                const value = data.get(name);
                return typeof value === "string" && value !== ""
                    ? value
                    : undefined;
            };
            const tags = (name: string) => {
                const value = text(name);
                return value === undefined ? [] : value.split(",");
            };
            const next = apply({
                q: text("q"),
                tag_all: tags("tag_all"),
                tag_any: tags("tag_any"),
                format: text("format"),
                quantization: text("quantization"),
                quantization_method: text("quantization_method"),
                bits: numeric(data.get("bits")),
                max_variant_bytes: numeric(data.get("max_variant_bytes")),
            });
            if (next !== null) syncForm(next);
        } catch {
            setFilterError(
                "Bits and maximum variant bytes must be exact whole numbers within the supported bounds. The last valid filters remain in effect.",
            );
        }
    }
    function chooseType(type: "model" | "dataset" | undefined) {
        cancelSearch();
        const changed = setLibraryType(store.snapshot().filters, type);
        const next = replace(changed.filters, changed.announcement);
        if (next !== null) syncForm(next);
    }
    function clearFilters() {
        cancelSearch();
        const next = normalizeLibraryFilters({});
        syncForm(next);
        replace(next);
    }
    function toggle(key: string) {
        setSelected((previous) => {
            const loaded =
                previous.generation === state.generation
                    ? previous.keys.filter((value) =>
                          state.rows.some((row) => row.key === value),
                      )
                    : [];
            const keys = loaded.includes(key)
                ? loaded.filter((value) => value !== key)
                : [...loaded, key].slice(0, 100);
            return { generation: state.generation, keys };
        });
    }
    async function copySelection() {
        try {
            await navigator.clipboard.writeText(visibleSelection.join("\n"));
            setAnnouncement("Loaded repository selectors copied.");
        } catch {
            setAnnouncement(
                "Copy is unavailable. Select the canonical repository selectors shown below.",
            );
        }
    }
    function facet(facet: LibraryFacet) {
        const result = state.facets[facet].result;
        return state.facetCompatible[facet] && result?.kind === "success"
            ? result.payload
            : null;
    }
    const tagFacet = facet("tag");
    const mainFailure = state.catalog.result;
    const failureCode =
        mainFailure?.kind === "api_problem"
            ? mainFailure.problem.code
            : mainFailure?.kind === "domain_failure"
              ? mainFailure.response.envelope.errors[0]?.code
              : undefined;

    return (
        <section className="library" aria-label="Repository library">
            <div className="library-toolbar">
                <p>
                    Find retained models and datasets using local metadata. No
                    Hub requests are made by filtering.
                </p>
                <button
                    type="button"
                    onClick={() => {
                        void store.refresh().catch(() => {
                            setFilterError(
                                "The Library read could not be started. Check the current connection and filters.",
                            );
                        });
                    }}
                    disabled={
                        !state.connected ||
                        state.refreshing ||
                        filterError !== null
                    }
                >
                    Refresh library
                </button>
            </div>
            <div
                className="library-summaries"
                role="group"
                aria-label="Library read scope"
            >
                <div>
                    <span>Known matching repositories</span>
                    <strong>
                        {catalog === null
                            ? "Not loaded"
                            : count(catalog.total_matches)}
                    </strong>
                    <small>
                        {catalog === null
                            ? "Awaiting validated catalog evidence"
                            : `${String(state.rows.length)} rows loaded on this page`}
                    </small>
                </div>
                <div>
                    <span>Scoped repositories</span>
                    <strong>
                        {catalog === null
                            ? "Not loaded"
                            : count(catalog.coverage.repositories)}
                    </strong>
                    <small>Before text, tag and technical matching</small>
                </div>
                <div>
                    <span>Scoped publications</span>
                    <strong>
                        {catalog === null
                            ? "Not loaded"
                            : count(catalog.coverage.publications)}
                    </strong>
                    <small>
                        {filters.revision_scope === "current"
                            ? "Current publication evidence"
                            : "Retained publication evidence"}
                    </small>
                </div>
                <div>
                    <span>Technical metadata</span>
                    <strong>
                        {catalog === null
                            ? "Not loaded"
                            : `${count(catalog.coverage.usable)} / ${count(catalog.coverage.publications)}`}
                    </strong>
                    <small>
                        {catalog?.coverage.incomplete === true
                            ? "Incomplete coverage; unknown evidence remains"
                            : catalog === null
                              ? "Availability is separate from integrity"
                              : "Usable observations in this read scope"}
                    </small>
                </div>
            </div>
            <form
                ref={form}
                onSubmit={submitFilters}
                className="library-filters"
                aria-label="Library filters"
            >
                <div className="library-search-row">
                    <label className="library-search">
                        Find repositories
                        <input
                            name="q"
                            type="search"
                            defaultValue={filters.q ?? ""}
                            placeholder="Repository ID or operator tag"
                            onChange={(event) => {
                                search(event.target.value);
                            }}
                            autoComplete="off"
                        />
                    </label>
                    <label>
                        Repository scope
                        <select
                            value={filters.scope}
                            onChange={(event) => {
                                apply({
                                    scope:
                                        event.target.value === "archived"
                                            ? "archived"
                                            : event.target.value ===
                                                "configured"
                                              ? "configured"
                                              : "all",
                                });
                            }}
                        >
                            <option value="all">
                                All: archived and configured
                            </option>
                            <option value="archived">Archived</option>
                            <option value="configured">Configured</option>
                        </select>
                    </label>
                </div>
                <div
                    className="library-tabs"
                    role="group"
                    aria-label="Repository type"
                >
                    {([undefined, "model", "dataset"] as const).map((type) => (
                        <button
                            key={type ?? "all"}
                            type="button"
                            aria-pressed={filters.type === type}
                            onClick={() => {
                                chooseType(type);
                            }}
                        >
                            {type === "model"
                                ? "Models"
                                : type === "dataset"
                                  ? "Datasets"
                                  : "All repositories"}
                        </button>
                    ))}
                </div>
                <div className="library-filter-grid">
                    <label>
                        Publication scope
                        <select
                            value={filters.revision_scope}
                            onChange={(event) => {
                                apply({
                                    revision_scope:
                                        event.target.value === "retained"
                                            ? "retained"
                                            : "current",
                                });
                            }}
                        >
                            <option value="current">
                                Current publications
                            </option>
                            <option value="retained">
                                Retained publications
                            </option>
                        </select>
                    </label>
                    <label>
                        Tag provenance
                        <select
                            value={filters.tag_source}
                            onChange={(event) => {
                                apply({
                                    tag_source:
                                        event.target.value === "current_only"
                                            ? "current_only"
                                            : "current_or_last_observed",
                                });
                            }}
                        >
                            <option value="current_or_last_observed">
                                Current or last observed
                            </option>
                            <option value="current_only">
                                Current configuration only
                            </option>
                        </select>
                    </label>
                    <label>
                        Require all tags
                        <input
                            name="tag_all"
                            defaultValue={(filters.tag_all ?? []).join(", ")}
                            placeholder="task:chat, team:research"
                        />
                    </label>
                    <label>
                        Match any tags
                        <input
                            name="tag_any"
                            defaultValue={(filters.tag_any ?? []).join(", ")}
                            placeholder="stage:evaluation, tier:prod"
                        />
                    </label>
                    <label>
                        Format
                        <input
                            name="format"
                            defaultValue={filters.format ?? ""}
                            list="library-formats"
                        />
                        <datalist id="library-formats">
                            {facet("format")?.entries.map((entry) => (
                                <option key={entry.value} value={entry.value} />
                            ))}
                        </datalist>
                    </label>
                    <label>
                        Quantization method
                        <input
                            name="quantization_method"
                            defaultValue={filters.quantization_method ?? ""}
                            disabled={filters.type === "dataset"}
                            list="library-methods"
                        />
                        <datalist id="library-methods">
                            {facet("quantization_method")?.entries.map(
                                (entry) => (
                                    <option
                                        key={entry.value}
                                        value={entry.value}
                                    />
                                ),
                            )}
                        </datalist>
                    </label>
                    <label>
                        Quantization scheme
                        <input
                            name="quantization"
                            defaultValue={filters.quantization ?? ""}
                            disabled={filters.type === "dataset"}
                            list="library-schemes"
                        />
                        <datalist id="library-schemes">
                            {facet("quantization")?.entries.map((entry) => (
                                <option key={entry.value} value={entry.value} />
                            ))}
                        </datalist>
                    </label>
                    <label>
                        Bits
                        <input
                            name="bits"
                            inputMode="numeric"
                            defaultValue={filters.bits}
                            disabled={filters.type === "dataset"}
                        />
                    </label>
                    <label>
                        Maximum variant bytes
                        <input
                            name="max_variant_bytes"
                            inputMode="numeric"
                            defaultValue={filters.max_variant_bytes}
                            disabled={filters.type === "dataset"}
                        />
                    </label>
                    <label>
                        Rows per page
                        <select
                            value={filters.limit}
                            onChange={(event) => {
                                apply({ limit: Number(event.target.value) });
                            }}
                        >
                            {[...new Set([25, 50, 100, filters.limit])]
                                .sort((a, b) => a - b)
                                .map((limit) => (
                                    <option key={limit} value={limit}>
                                        {limit}
                                    </option>
                                ))}
                        </select>
                    </label>
                </div>
                <p className="library-muted">
                    Text search is debounced. Apply tag and technical fields
                    together. Tags use commas; groups combine with AND.
                    Technical predicates must match one complete primary
                    variant.
                </p>
                <div className="library-filter-actions">
                    <button type="submit">Apply filters</button>
                    <button type="button" onClick={clearFilters}>
                        Clear filters
                    </button>
                </div>
            </form>
            {filterError !== null && (
                <div role="alert" className="library-warning">
                    {filterError}
                </div>
            )}
            {announcement !== null && <p role="status">{announcement}</p>}
            {state.notice !== null && <Notice>{notices[state.notice]}</Notice>}
            {state.refreshing && (
                <p role="status">
                    Updating the Library. Any displayed page is the last
                    validated evidence.
                </p>
            )}
            {filters.type === undefined &&
                (filters.bits !== undefined ||
                    filters.quantization !== undefined ||
                    filters.quantization_method !== undefined ||
                    filters.max_variant_bytes !== undefined) && (
                    <Notice>
                        Model-only technical predicates select models. Dataset
                        rows do not acquire model fields.
                    </Notice>
                )}
            <div className="library-content">
                <div>
                    {catalog === null ? (
                        <Panel title="Library results">
                            {filterError !== null ? (
                                <p>
                                    Filters have not been applied. Clear or
                                    correct them to load the Library.
                                </p>
                            ) : state.phase === "loading" ||
                              state.phase === "idle" ? (
                                <p role="status">
                                    Loading a bounded Library page.
                                </p>
                            ) : (
                                <p role="alert">
                                    {!state.connected
                                        ? "Reconnect to read the current archive."
                                        : "The Library read is unavailable or failed. Narrow the repository type or scope, then refresh."}
                                    {failureCode === undefined
                                        ? ""
                                        : ` Diagnostic code: ${failureCode}.`}
                                </p>
                            )}
                        </Panel>
                    ) : (
                        <div className="library-results">
                            {state.phase === "partial_empty" ? (
                                <div className="library-empty">
                                    <h2>
                                        No known matches; metadata coverage is
                                        incomplete
                                    </h2>
                                    <p>
                                        Missing observations can hide matches.
                                        Narrow the scope or review metadata
                                        coverage; this is not proof of absence.
                                    </p>
                                </div>
                            ) : state.phase === "empty" ? (
                                <div className="library-empty">
                                    <h2>No known matches for these filters</h2>
                                    <p>
                                        Try a different ID or operator tag.
                                        Search does not read README text or
                                        contact the Hub.
                                    </p>
                                </div>
                            ) : (
                                <>
                                    <div className="library-selection">
                                        <label>
                                            <input
                                                type="checkbox"
                                                checked={
                                                    state.rows.length > 0 &&
                                                    visibleSelection.length ===
                                                        state.rows.length
                                                }
                                                onChange={(event) => {
                                                    setSelected({
                                                        generation:
                                                            state.generation,
                                                        keys: event.target
                                                            .checked
                                                            ? state.rows.map(
                                                                  (row) =>
                                                                      row.key,
                                                              )
                                                            : [],
                                                    });
                                                }}
                                            />
                                            Select loaded page
                                        </label>
                                        <span>
                                            {visibleSelection.length} selected
                                            from {state.rows.length} loaded rows
                                        </span>
                                    </div>
                                    <div
                                        className="library-table-scroll"
                                        tabIndex={0}
                                        role="region"
                                        aria-label="Repository table, scroll horizontally on narrow screens"
                                    >
                                        <table className="library-table">
                                            <thead>
                                                <tr>
                                                    <th scope="col">Select</th>
                                                    <th scope="col">
                                                        Repository
                                                    </th>
                                                    <th scope="col">
                                                        Available content
                                                    </th>
                                                    <th scope="col">
                                                        Archive state
                                                    </th>
                                                    <th scope="col">
                                                        Current snapshot
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {state.rows.map((row) => (
                                                    <Row
                                                        key={row.key}
                                                        row={row}
                                                        selected={visibleSelection.includes(
                                                            row.key,
                                                        )}
                                                        toggle={() => {
                                                            toggle(row.key);
                                                        }}
                                                        basePath={basePath}
                                                        onOpenRepository={
                                                            onOpenRepository
                                                        }
                                                    />
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )}
                            <div className="library-pagination">
                                <span>
                                    Page {state.pageIndex + 1} ·{" "}
                                    {state.rows.length} loaded rows ·{" "}
                                    {count(catalog.total_matches)} known matches
                                </span>
                                <div>
                                    <button
                                        type="button"
                                        disabled={
                                            !state.hasPrevious ||
                                            state.refreshing
                                        }
                                        onClick={() => {
                                            void store.previousPage();
                                        }}
                                    >
                                        Previous page
                                    </button>
                                    <button
                                        type="button"
                                        disabled={
                                            !state.hasNext || state.refreshing
                                        }
                                        onClick={() => {
                                            void store.nextPage();
                                        }}
                                    >
                                        Next page
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                    {visibleSelection.length > 0 && (
                        <Panel title="Review loaded repository selection">
                            <p>
                                This selection contains explicit canonical
                                repository identities from the loaded page.
                            </p>
                            <pre className="library-selectors">
                                {visibleSelection.join("\n")}
                            </pre>
                            <button
                                type="button"
                                onClick={() => {
                                    void copySelection();
                                }}
                            >
                                Copy selectors
                            </button>
                        </Panel>
                    )}
                </div>
                <aside
                    className="library-sidebar"
                    aria-label="Library evidence and tag suggestions"
                >
                    <Panel title="Operator tags">
                        <p>
                            Your configuration labels are separate from upstream
                            metadata. Historical labels remain attributed.
                        </p>
                        <label>
                            Facet selection group
                            <select
                                value={tagGroup}
                                onChange={(event) => {
                                    setTagGroup(
                                        event.target.value === "tag_any"
                                            ? "tag_any"
                                            : "tag_all",
                                    );
                                }}
                            >
                                <option value="tag_all">
                                    Require all selected tags
                                </option>
                                <option value="tag_any">
                                    Match any selected tags
                                </option>
                            </select>
                        </label>
                        {tagFacet === null ? (
                            <p>
                                Tag suggestions are unavailable. Manual tag
                                filters remain available.
                            </p>
                        ) : (
                            <>
                                <div className="library-facet-tags">
                                    {tagFacet.entries.map((entry) => (
                                        <label key={entry.value}>
                                            <input
                                                type="checkbox"
                                                checked={(
                                                    filters[tagGroup] ?? []
                                                ).includes(entry.value)}
                                                onChange={(event) => {
                                                    const current =
                                                        filters[tagGroup] ?? [];
                                                    const next = apply({
                                                        [tagGroup]: event.target
                                                            .checked
                                                            ? [
                                                                  ...current,
                                                                  entry.value,
                                                              ]
                                                            : current.filter(
                                                                  (tag) =>
                                                                      tag !==
                                                                      entry.value,
                                                              ),
                                                    });
                                                    if (next !== null)
                                                        syncForm(next);
                                                }}
                                            />
                                            <span>{entry.value}</span>
                                            <small>
                                                {count(entry.repository_count)}
                                            </small>
                                        </label>
                                    ))}
                                </div>
                                <p className="library-muted">
                                    {tagFacet.entries.length} values on this
                                    page of {count(tagFacet.total_matches)}{" "}
                                    known matching values. Counts are matching
                                    repositories, not archive-wide totals.
                                </p>
                                <button
                                    type="button"
                                    disabled={
                                        state.facets.tag.result?.kind !==
                                            "success" ||
                                        state.facets.tag.result.response
                                            .next_cursor === null ||
                                        state.refreshing
                                    }
                                    onClick={() => {
                                        void store.nextFacetPage("tag");
                                    }}
                                >
                                    Load more tags
                                </button>
                            </>
                        )}
                    </Panel>
                    {catalog !== null && (
                        <Coverage coverage={catalog.coverage} />
                    )}
                </aside>
            </div>
            <Notice>
                <strong>Availability is not integrity.</strong> Technical
                observations describe retained content. Current snapshot sizes
                are logical file bytes, not physical disk usage; enrichment
                pages may be incomplete.
            </Notice>
        </section>
    );
}
