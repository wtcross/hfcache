import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
    useSyncExternalStore,
} from "react";
import type { ReactNode } from "react";
import { Notice, Panel } from "../primitives";
import { ReadmeCard } from "../readme/ReadmeCard";
import {
    parseRepositoryFragment,
    repositoryFragment,
    repositoryPath,
    REPOSITORY_TABS,
} from "../repository/routes";
import type {
    PublicationPair,
    RepositoryTarget,
    RepositoryTab,
    RepositoryView,
} from "../repository/routes";
import type {
    RepositoryNotice,
    RepositoryPage,
    RepositorySnapshot,
    RepositoryStore,
} from "../repository/repository-state";
import type {
    CatalogEntry,
    FileEntry,
    ModelVariant,
    ObservationSummary,
    ReportPayload,
    SourceObservation,
} from "../wire/generated";

function payload<T>(page: RepositoryPage<T>): T | null {
    return page.result?.kind === "success" ? page.result.payload : null;
}
function number(value: number): string {
    return value.toLocaleString("en-US");
}
function bytes(value: number): string {
    const units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"];
    let amount = value,
        index = 0;
    while (amount >= 1024 && index < units.length - 1) {
        amount /= 1024;
        index++;
    }
    return `${amount.toLocaleString("en-US", { maximumFractionDigits: index === 0 ? 0 : 1 })} ${units[index] ?? "B"}`;
}
function label(
    tab: RepositoryTab,
    type: RepositoryTarget["repositoryType"],
): string {
    switch (tab) {
        case "overview":
            return "Overview";
        case "details":
            return type === "model" ? "Variants" : "Dataset details";
        case "files":
            return "Files & manifest";
        case "revisions":
            return "Revisions";
        case "integrity":
            return "Integrity";
        case "activity":
            return "Activity";
    }
}
const messages: Readonly<Record<Exclude<RepositoryNotice, null>, string>> = {
    invalid:
        "The repository address is invalid. Correct the address or select current publication explicitly.",
    authentication:
        "Reconnect to read repository evidence for the current authenticated archive.",
    session_changed:
        "The authenticated session changed. Previous private repository evidence was cleared.",
    publication_changed:
        "Publication evidence changed between reads. The selected identity was not replaced with another publication.",
    page_limit:
        "This browser reached its 32-page bound. Refresh the selected publication to restart the bounded pages.",
    cursor_cycle:
        "The server repeated a continuation. Paging stopped; refresh before continuing.",
    stale_cursor:
        "The metadata page changed. Its cursor was restarted once; repeated refusal remains visible.",
    join_unavailable:
        "Some evidence could not be joined to the selected publication. Contradictory supplemental fields are withheld.",
};
function ReadState<T>({
    page,
    name,
}: {
    page: RepositoryPage<T>;
    name: string;
}) {
    const value = page.result;
    const code =
        value?.kind === "api_problem"
            ? value.problem.code
            : value?.kind === "domain_failure"
              ? value.response.envelope.errors[0]?.code
              : undefined;
    return (
        <p
            role={
                page.phase === "loading" || page.phase === "idle"
                    ? "status"
                    : "alert"
            }
        >
            {page.phase === "loading"
                ? `Loading bounded ${name}.`
                : page.phase === "idle"
                  ? `${name} has not been loaded for this tab.`
                  : `${name} is unavailable or could not be validated.`}
            {code === undefined ? "" : ` Diagnostic code: ${code}.`}
        </p>
    );
}
function Fact({ name, children }: { name: string; children: ReactNode }) {
    return (
        <div className="repository-fact">
            <dt>{name}</dt>
            <dd>{children}</dd>
        </div>
    );
}
function LocalCollection<T>({
    items,
    identity,
    name,
    render,
}: {
    items: readonly T[];
    identity: string;
    name: string;
    render: (visible: readonly T[], offset: number) => ReactNode;
}) {
    const [position, setPosition] = useState({ identity, index: 0 });
    const last = Math.max(0, Math.ceil(items.length / 25) - 1);
    const index =
        position.identity === identity ? Math.min(position.index, last) : 0;
    const start = index * 25;
    return (
        <>
            {render(items.slice(start, start + 25), start)}
            <div className="repository-local-pages">
                <span>
                    {items.length === 0
                        ? "0"
                        : `${number(start + 1)}–${number(Math.min(start + 25, items.length))}`}{" "}
                    of {number(items.length)} {name} in this loaded artifact
                </span>
                {items.length > 25 && (
                    <div>
                        <button
                            type="button"
                            disabled={index === 0}
                            onClick={() => {
                                setPosition({ identity, index: index - 1 });
                            }}
                        >
                            Previous {name}
                        </button>
                        <button
                            type="button"
                            disabled={index >= last}
                            onClick={() => {
                                setPosition({ identity, index: index + 1 });
                            }}
                        >
                            Next {name}
                        </button>
                    </div>
                )}
            </div>
        </>
    );
}
const sourceLabels: Readonly<Record<SourceObservation["field"], string>> = {
    task: "Task",
    language: "Language",
    license: "License",
    base_model: "Base model",
    upstream_tags: "Upstream tags",
    dataset_config: "Dataset configuration",
    dataset_split: "Dataset split",
    dataset_feature: "Dataset feature",
    format: "Format",
};
function Declarations({
    observations,
    identity,
    datasetOnly = false,
}: {
    observations: readonly ObservationSummary[];
    identity: string;
    datasetOnly?: boolean;
}) {
    const sources = observations.flatMap((observation) =>
        observation.sources
            .filter(
                (source) =>
                    !datasetOnly ||
                    source.field.startsWith("dataset_") ||
                    source.field === "format",
            )
            .map((source) => ({ source, observation })),
    );
    return (
        <>
            <p>
                These are static upstream declarations with their captured
                source identity. They do not establish integrity, row counts or
                hardware suitability.
            </p>
            {sources.length === 0 ? (
                <p>
                    No attributed declarations were observed for this selected
                    publication.
                </p>
            ) : (
                <LocalCollection
                    items={sources}
                    identity={identity}
                    name="declarations"
                    render={(visible) => (
                        <div
                            className="repository-table-scroll"
                            tabIndex={0}
                            role="region"
                            aria-label="Attributed declarations table"
                        >
                            <table aria-label="Attributed declarations">
                                <thead>
                                    <tr>
                                        <th>Field</th>
                                        <th>Declared values</th>
                                        <th>Source and capture</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {visible.map(
                                        ({ source, observation }, index) => (
                                            <tr
                                                key={`${source.path}:${source.field}:${String(index)}`}
                                            >
                                                <th scope="row">
                                                    {sourceLabels[source.field]}
                                                </th>
                                                <td>
                                                    {source.values.length === 0
                                                        ? "Not observed"
                                                        : source.values.join(
                                                              ", ",
                                                          )}
                                                </td>
                                                <td>
                                                    <code>{source.path}</code>
                                                    <small>
                                                        SHA256{" "}
                                                        <code>
                                                            {source.sha256}
                                                        </code>
                                                    </small>
                                                    <small>
                                                        {source.evidence} ·{" "}
                                                        {
                                                            observation.extractor_version
                                                        }
                                                    </small>
                                                    <time
                                                        dateTime={
                                                            observation.observed_at
                                                        }
                                                    >
                                                        {
                                                            observation.observed_at
                                                        }
                                                    </time>
                                                </td>
                                            </tr>
                                        ),
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                />
            )}
            {observations.map((observation) => (
                <div
                    className="repository-observation"
                    key={observation.commit_sha + observation.publication_id}
                >
                    <strong>
                        Metadata observation status: {observation.status}
                    </strong>
                    <small>
                        Publication generation{" "}
                        {observation.publication_generation} · extractor{" "}
                        {observation.extractor_version}
                    </small>
                    <small>Observed {observation.observed_at}</small>
                    {observation.diagnostics.length > 0 && (
                        <p>Diagnostics: {observation.diagnostics.join(", ")}</p>
                    )}
                </div>
            ))}
        </>
    );
}
function OperatorTags({ entry }: { entry: CatalogEntry | null }) {
    return (
        <Panel title="Operator tags">
            {entry === null ? (
                <p>Tag provenance has not been observed.</p>
            ) : (
                <>
                    <div className="repository-tags">
                        {entry.tags.map((tag) => (
                            <span key={tag}>{tag}</span>
                        ))}
                    </div>
                    <p>
                        {entry.tag_origin === "configured"
                            ? entry.tags.length === 0
                                ? "Configured tags: none"
                                : "Current configuration tags"
                            : entry.tag_origin === "last_observed"
                              ? "Last-observed tags"
                              : "Tags not observed"}
                    </p>
                    {entry.tag_observed_at !== null && (
                        <small>Observed {entry.tag_observed_at}</small>
                    )}
                    <p>
                        Operator labels are separate from upstream declarations.
                        Tags grant no access and establish no integrity.
                    </p>
                </>
            )}
        </Panel>
    );
}
function Variant({
    variant,
    identity,
}: {
    variant: ModelVariant;
    identity: string;
}) {
    return (
        <article className="repository-variant">
            <h3>
                {variant.format} · {variant.encoding ?? "Encoding not observed"}
            </h3>
            <dl className="repository-facts">
                <Fact name="Variant ID">
                    <code>{variant.variant_id}</code>
                </Fact>
                <Fact name="Role">{variant.role}</Fact>
                <Fact name="Completeness">{variant.completeness}</Fact>
                <Fact name="Quantization method">
                    {variant.quantization_method ?? "Not observed"}
                </Fact>
                <Fact name="Quantization scheme">
                    {variant.quantization ?? "Not observed"}
                </Fact>
                <Fact name="Bits">
                    {variant.bits === null
                        ? "Not observed"
                        : number(variant.bits)}
                </Fact>
                <Fact name="Group size">
                    {variant.group_size === null
                        ? "Not observed"
                        : number(variant.group_size)}
                </Fact>
                <Fact name="Logical weight bytes">
                    {variant.total_bytes === null
                        ? "Not observed"
                        : `${bytes(variant.total_bytes)} (${number(variant.total_bytes)} bytes)`}
                </Fact>
                <Fact name="Evidence">{variant.evidence}</Fact>
            </dl>
            <p>
                Source paths:{" "}
                {variant.source_paths.length === 0
                    ? "Not observed"
                    : variant.source_paths.join(", ")}
            </p>
            {variant.diagnostics.length > 0 && (
                <p>Diagnostics: {variant.diagnostics.join(", ")}</p>
            )}
            <details>
                <summary>
                    Declared variant members ({number(variant.members.length)})
                </summary>
                <LocalCollection
                    items={variant.members}
                    identity={identity + variant.variant_id}
                    name="members"
                    render={(visible) => (
                        <table
                            aria-label={`Members for variant ${variant.variant_id}`}
                        >
                            <thead>
                                <tr>
                                    <th>Path</th>
                                    <th>Logical bytes</th>
                                </tr>
                            </thead>
                            <tbody>
                                {visible.map((member) => (
                                    <tr key={member.path}>
                                        <th scope="row">
                                            <code>{member.path}</code>
                                        </th>
                                        <td>{number(member.size_bytes)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                />
            </details>
        </article>
    );
}
function FileDetails({ file }: { file: FileEntry }) {
    return (
        <details>
            <summary>Hashes and provenance</summary>
            <dl className="repository-facts">
                <Fact name="Expected SHA256">
                    <code>{file.sha256}</code>
                </Fact>
                <Fact name="Source">{file.provenance.source}</Fact>
                <Fact name="Cache root">{file.provenance.cache_root}</Fact>
                <Fact name="Hashed during ingestion">
                    {file.provenance.hashed ? "Yes" : "No"}
                </Fact>
                <Fact name="Reused digest from">
                    {file.provenance.hash_reused_from === null ? (
                        "None"
                    ) : (
                        <>
                            <code>
                                {file.provenance.hash_reused_from.commit_sha}
                            </code>
                            <br />
                            <code>
                                {
                                    file.provenance.hash_reused_from
                                        .publication_id
                                }
                            </code>
                        </>
                    )}
                </Fact>
                <Fact name="Upstream Git object">
                    {file.upstream.git_oid ?? "Not observed"}
                </Fact>
                <Fact name="Upstream LFS SHA256">
                    {file.upstream.lfs_sha256 ?? "Not observed"}
                </Fact>
                <Fact name="Upstream Xet hash">
                    {file.upstream.xet_hash ?? "Not observed"}
                </Fact>
            </dl>
        </details>
    );
}
function Diagnostics({
    values,
    identity,
    name,
    kind,
}: {
    values: readonly string[];
    identity: string;
    name: string;
    kind: "Warning" | "Error";
}) {
    if (values.length === 0) return null;
    return (
        <LocalCollection
            items={values}
            identity={identity}
            name={name}
            render={(visible) => (
                <ul aria-label={name}>
                    {visible.map((value, index) => (
                        <li key={index}>
                            {kind}: {value}
                        </li>
                    ))}
                </ul>
            )}
        />
    );
}
function Report({
    value,
    selected,
    generation,
}: {
    value: ReportPayload["report"];
    selected: RepositorySnapshot["selected"];
    generation: number | null;
}) {
    const matches =
        "repositories" in value && selected !== null
            ? value.repositories.filter(
                  (row) =>
                      row.repository_type === selected.repositoryType &&
                      row.repository_id === selected.repositoryId &&
                      row.resolved_commit_sha === selected.commitSha &&
                      row.publication_id === selected.publicationId &&
                      row.publication_generation === generation,
              )
            : [];
    const identity =
        value.run_id +
        ":" +
        (selected?.commitSha ?? "none") +
        ":" +
        (selected?.publicationId ?? "none") +
        ":" +
        String(generation);
    return (
        <article className="repository-report">
            <h3>
                Loaded report <code>{value.run_id}</code>
            </h3>
            <dl className="repository-facts">
                <Fact name="Command">{value.command}</Fact>
                <Fact name="Outcome">{value.outcome}</Fact>
                <Fact name="Exit code">{number(value.exit_code)}</Fact>
                <Fact name="Started">{value.started_at}</Fact>
                <Fact name="Completed">{value.completed_at}</Fact>
            </dl>
            <p>
                This is one loaded archive report. Its historical policy
                fingerprint is separate from current configuration.
            </p>
            {"repositories" in value ? (
                <>
                    <p>
                        {number(matches.length)} loaded repository entries match
                        the selected type, ID, SHA, publication ID and
                        generation.
                    </p>
                    <LocalCollection
                        items={matches}
                        identity={identity}
                        name="qualified report entries"
                        render={(visible, offset) =>
                            visible.map((row, index) => {
                                const entryIdentity =
                                    identity +
                                    ":entry:" +
                                    String(offset + index);
                                return (
                                    <div key={entryIdentity}>
                                        <strong>{row.status}</strong>
                                        <small>
                                            Publication generation{" "}
                                            {row.publication_generation ??
                                                "Not observed"}
                                        </small>
                                        <p>
                                            {number(row.file_count)} files ·{" "}
                                            {bytes(row.downloaded_bytes)}{" "}
                                            downloaded ·{" "}
                                            {bytes(row.hashed_bytes)} hashed
                                        </p>
                                        <Diagnostics
                                            values={row.warnings}
                                            identity={
                                                entryIdentity + ":warnings"
                                            }
                                            name="entry warnings"
                                            kind="Warning"
                                        />
                                        <Diagnostics
                                            values={row.errors}
                                            identity={entryIdentity + ":errors"}
                                            name="entry errors"
                                            kind="Error"
                                        />
                                    </div>
                                );
                            })
                        }
                    />
                </>
            ) : (
                <p>
                    This report is a bounded recovery or verification report; no
                    unqualified findings are treated as selected-publication
                    integrity.
                </p>
            )}
            <Diagnostics
                values={value.warnings}
                identity={identity + ":warnings"}
                name="report warnings"
                kind="Warning"
            />
            <Diagnostics
                values={value.errors}
                identity={identity + ":errors"}
                name="report errors"
                kind="Error"
            />
        </article>
    );
}

export function RepositoryDetail({
    store,
    target,
    basePath,
}: {
    store: RepositoryStore;
    target: RepositoryTarget;
    basePath: string;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const stableTarget = useMemo(
        () => ({
            repositoryType: target.repositoryType,
            repositoryId: target.repositoryId,
        }),
        [target.repositoryType, target.repositoryId],
    );
    const live = useRef(false);
    const element = useRef<HTMLElement>(null);
    const pendingTabFocus = useRef<{
        owner: string;
        tab: RepositoryTab;
    } | null>(null);
    const [addressError, setAddressError] = useState<string | null>(null);
    const [announcement, setAnnouncement] = useState<string | null>(null);
    const owner =
        target.repositoryType +
        ":" +
        target.repositoryId +
        ":" +
        String(state.authGeneration);
    const [validatedOwner, setValidatedOwner] = useState<string | null>(null);
    const ownerValidated = validatedOwner === owner && addressError === null;
    const sameTarget =
        state.target?.repositoryType === target.repositoryType &&
        state.target.repositoryId === target.repositoryId;
    const selected =
        sameTarget && validatedOwner === owner && addressError === null
            ? state.selected
            : null;
    const qualified =
        sameTarget &&
        validatedOwner === owner &&
        addressError === null &&
        state.retained === true &&
        state.phase === "ready";
    const manifest = qualified
        ? (payload(state.manifest)?.manifest ?? null)
        : null;
    const catalog =
        sameTarget &&
        ownerValidated &&
        (qualified || state.phase === "unpublished")
            ? payload(state.catalog)
            : null;
    const entry = catalog?.entry ?? null;
    const inventory =
        sameTarget && ownerValidated
            ? (payload(state.currentFacts.inventory)?.repositories.find(
                  (row) =>
                      row.repository_type === target.repositoryType &&
                      row.repository_id === target.repositoryId,
              ) ?? null)
            : null;
    const status =
        sameTarget && ownerValidated
            ? (payload(state.currentFacts.status)?.repositories.find(
                  (row) =>
                      row.repository_type === target.repositoryType &&
                      row.repository_id === target.repositoryId,
              ) ?? null)
            : null;
    const reference = qualified
        ? (payload(state.selectedReference)?.reference ?? null)
        : null;
    const card = qualified ? payload(state.card) : null;
    const identity =
        selected === null
            ? target.repositoryType + ":" + target.repositoryId
            : `${String(state.authGeneration)}:${selected.repositoryType}:${selected.repositoryId}:${selected.commitSha}:${selected.publicationId}`;
    const view = sameTarget
        ? state.view
        : { pair: null, tab: "overview" as const };
    const tab = view.tab;
    const archiveTree = manifest?.tree ?? null;
    const publishedTree =
        reference !== null && archiveTree === "published/" + reference.tree
            ? reference.tree
            : null;
    const manifestPath =
        card?.manifest_path ??
        (reference === null ? null : "published/" + reference.manifest);
    const observations = catalog?.observations ?? [];
    const selectedReport = qualified ? payload(state.report) : null;
    const current = sameTarget
        ? (payload(state.current)?.reference ?? null)
        : null;
    const isCurrent =
        qualified &&
        current !== null &&
        selected !== null &&
        current.commit_sha === selected.commitSha &&
        current.publication_id === selected.publicationId &&
        current.publication_generation === state.publicationGeneration;
    const upstream =
        "https://huggingface.co/" +
        (target.repositoryType === "dataset" ? "datasets/" : "") +
        target.repositoryId.split("/").map(encodeURIComponent).join("/");

    const open = useCallback(
        (next: RepositoryView) => {
            const pending = store.open(stableTarget, next);
            const now = store.snapshot();
            return now.connected &&
                !now.refreshing &&
                (now.phase === "idle" || now.phase === "loading")
                ? store.refresh()
                : pending;
        },
        [store, stableTarget],
    );
    function request(operation: () => Promise<void>) {
        setAddressError(null);
        setValidatedOwner(owner);
        try {
            const pending = operation();
            const generation = store.snapshot().generation;
            void pending.catch(() => {
                if (live.current && store.snapshot().generation === generation)
                    setAddressError(
                        "Repository evidence could not be loaded. Check the current connection and selected address.",
                    );
            });
        } catch {
            setAddressError(
                "The selected repository address could not be applied.",
            );
        }
    }
    function writeAddress(next: RepositoryView, replace = false) {
        const path =
            repositoryPath(stableTarget, basePath) + repositoryFragment(next);
        if (window.location.pathname + window.location.hash !== path) {
            if (replace) window.history.replaceState(null, "", path);
            else window.history.pushState(null, "", path);
        }
    }
    useEffect(() => {
        live.current = true;
        let active = true;
        function readLocation() {
            if (!active) return;
            if (
                window.location.pathname !==
                repositoryPath(stableTarget, basePath)
            ) {
                setValidatedOwner(null);
                store.pause();
                return;
            }
            try {
                if (window.location.search !== "") throw new Error("invalid");
                const next = parseRepositoryFragment(window.location.hash);
                setValidatedOwner(owner);
                setAddressError(null);
                setAnnouncement(null);
                void open(next).catch(() => {
                    if (active)
                        setAddressError(
                            "Repository evidence could not be loaded. Check the connection and selected address.",
                        );
                });
            } catch {
                store.pause();
                setValidatedOwner(null);
                setAddressError(
                    "This repository address has invalid or unsupported selection fields. Select current publication to start a new explicit selection.",
                );
            }
        }
        queueMicrotask(readLocation);
        window.addEventListener("hashchange", readLocation);
        window.addEventListener("popstate", readLocation);
        return () => {
            active = false;
            live.current = false;
            pendingTabFocus.current = null;
            window.removeEventListener("hashchange", readLocation);
            window.removeEventListener("popstate", readLocation);
            store.pause();
        };
    }, [
        store,
        open,
        state.authGeneration,
        state.connected,
        stableTarget,
        basePath,
        owner,
    ]);
    useEffect(() => {
        if (
            !sameTarget ||
            selected === null ||
            state.retained !== true ||
            addressError !== null
        )
            return;
        if (
            window.location.pathname !==
                repositoryPath(stableTarget, basePath) ||
            window.location.search !== "" ||
            store.snapshot().generation !== state.generation
        )
            return;
        try {
            const requested = parseRepositoryFragment(window.location.hash);
            if (
                requested.tab !== state.view.tab ||
                (requested.pair !== null &&
                    (requested.pair.commitSha !== selected.commitSha ||
                        requested.pair.publicationId !==
                            selected.publicationId))
            )
                return;
        } catch {
            return;
        }
        // Resolving current pins a complete pair without adding a second history entry.
        const next = {
            pair: {
                commitSha: selected.commitSha,
                publicationId: selected.publicationId,
            },
            tab: state.view.tab,
        };
        const path =
            repositoryPath(stableTarget, basePath) + repositoryFragment(next);
        if (window.location.pathname + window.location.hash !== path)
            window.history.replaceState(null, "", path);
    }, [
        sameTarget,
        selected,
        state.retained,
        state.view.tab,
        stableTarget,
        basePath,
        addressError,
        store,
        state.generation,
    ]);
    useEffect(() => {
        const pending = pendingTabFocus.current;
        if (
            pending === null ||
            !qualified ||
            manifest === null ||
            state.refreshing
        )
            return;
        pendingTabFocus.current = null;
        if (pending.owner !== owner || pending.tab !== tab) return;
        // Revalidating the selected reference temporarily removes the panels.
        // Restore the requested tab after it returns, unless the user has moved
        // focus to another control while the read was pending.
        if (document.activeElement === document.body)
            element.current
                ?.querySelector<HTMLButtonElement>(
                    `#repository-tab-${pending.tab}`,
                )
                ?.focus();
    }, [qualified, manifest, owner, tab, state.refreshing]);
    function chooseTab(nextTab: RepositoryTab) {
        pendingTabFocus.current = { owner, tab: nextTab };
        const pair =
            selected === null
                ? view.pair
                : {
                      commitSha: selected.commitSha,
                      publicationId: selected.publicationId,
                  };
        writeAddress({ pair, tab: nextTab });
        request(() =>
            sameTarget ? store.setTab(nextTab) : open({ pair, tab: nextTab }),
        );
    }
    function choosePublication(pair: PublicationPair) {
        pendingTabFocus.current = null;
        writeAddress({ pair, tab });
        request(() =>
            sameTarget ? store.selectPublication(pair) : open({ pair, tab }),
        );
    }
    function chooseCurrent() {
        pendingTabFocus.current = null;
        writeAddress({ pair: null, tab });
        request(() =>
            sameTarget ? store.selectCurrent() : open({ pair: null, tab }),
        );
    }
    async function copy(value: string, name: string) {
        try {
            await navigator.clipboard.writeText(value);
            setAnnouncement(`${name} copied.`);
        } catch {
            setAnnouncement(
                `Copy is unavailable. Select and copy the displayed ${name.toLowerCase()}.`,
            );
        }
    }
    const content = () => {
        if (manifest === null) return null;
        switch (tab) {
            case "overview":
                return (
                    <>
                        {selected !== null &&
                            (card === null ? (
                                <Panel title="Archived README">
                                    <ReadState
                                        page={state.card}
                                        name="Archived README"
                                    />
                                </Panel>
                            ) : (
                                <ReadmeCard
                                    key={
                                        identity +
                                        ":" +
                                        (card.presentation_sha256 ?? card.state)
                                    }
                                    card={card}
                                    identity={selected}
                                    publicationGeneration={
                                        manifest.publication_generation
                                    }
                                />
                            ))}
                        <Panel title="Attributed upstream declarations">
                            {catalog === null ? (
                                <ReadState
                                    page={state.catalog}
                                    name="Technical metadata"
                                />
                            ) : (
                                <Declarations
                                    observations={observations}
                                    identity={identity}
                                />
                            )}
                            <Notice>
                                Upstream declarations and publication ingestion
                                are separate from current offline verification.
                                Unknown specifications remain unknown.
                            </Notice>
                            <details>
                                <summary>Publication provenance</summary>
                                <dl className="repository-facts">
                                    <Fact name="Upstream endpoint">
                                        {manifest.hub_endpoint}
                                    </Fact>
                                    <Fact name="First observed">
                                        {manifest.first_observed_at}
                                    </Fact>
                                    <Fact name="Download started">
                                        {manifest.download_started_at}
                                    </Fact>
                                    <Fact name="Download completed">
                                        {manifest.download_completed_at}
                                    </Fact>
                                    <Fact name="Ingestion verified">
                                        {manifest.verified_at}
                                    </Fact>
                                    <Fact name="Publishing application">
                                        {manifest.application_version}
                                    </Fact>
                                    <Fact name="Publishing Python">
                                        {manifest.python_version}
                                    </Fact>
                                    <Fact name="Publishing Hub client">
                                        {manifest.huggingface_hub_version}
                                    </Fact>
                                </dl>
                            </details>
                            {manifest.dependencies.length > 0 && (
                                <details>
                                    <summary>
                                        Declared dependencies (
                                        {number(manifest.dependencies.length)})
                                    </summary>
                                    <p>
                                        These are captured metadata
                                        observations. Dependencies are not
                                        automatically downloaded or executed.
                                    </p>
                                    <LocalCollection
                                        items={manifest.dependencies}
                                        identity={identity}
                                        name="dependencies"
                                        render={(visible) => (
                                            <dl className="repository-facts">
                                                {visible.map(
                                                    (dependency, index) => (
                                                        <Fact
                                                            key={index}
                                                            name={
                                                                dependency.detected_id
                                                            }
                                                        >
                                                            {dependency.declared
                                                                ? "Explicitly declared"
                                                                : "Detected declaration"}{" "}
                                                            ·{" "}
                                                            {
                                                                dependency.confidence
                                                            }{" "}
                                                            confidence ·{" "}
                                                            {dependency.managed
                                                                ? "Configured dependency"
                                                                : "Outside current managed scope"}
                                                            <small>
                                                                <code>
                                                                    {
                                                                        dependency.source_file
                                                                    }
                                                                </code>{" "}
                                                                ·{" "}
                                                                {
                                                                    dependency.source_field
                                                                }
                                                            </small>
                                                        </Fact>
                                                    ),
                                                )}
                                            </dl>
                                        )}
                                    />
                                </details>
                            )}
                        </Panel>
                    </>
                );
            case "details":
                if (target.repositoryType === "dataset")
                    return (
                        <Panel title="Dataset declarations">
                            <p>
                                {"Observed dataset formats: " +
                                    ([
                                        ...new Set(
                                            observations.flatMap(
                                                (observation) =>
                                                    observation.dataset_formats,
                                            ),
                                        ),
                                    ].join(", ") || "Not observed")}
                            </p>
                            {catalog === null ? (
                                <ReadState
                                    page={state.catalog}
                                    name="Dataset metadata"
                                />
                            ) : (
                                <Declarations
                                    observations={observations}
                                    identity={identity}
                                    datasetOnly
                                />
                            )}
                            <Notice>
                                Configuration, split, feature and format names
                                are static declarations. No dataset loader or
                                sample is executed; row counts are not inferred.
                            </Notice>
                        </Panel>
                    );
                return (
                    <Panel title="Model variants">
                        <p>
                            All exposed roles and completeness states remain
                            inspectable. These are discovery declarations, not
                            partial download choices or hardware-fit estimates.
                        </p>
                        {payload(state.variants) === null ? (
                            <ReadState
                                page={state.variants}
                                name="Model variants"
                            />
                        ) : (
                            <>
                                {payload(state.variants)?.entries.map(
                                    (item) => (
                                        <Variant
                                            key={item.variant.variant_id}
                                            variant={item.variant}
                                            identity={identity}
                                        />
                                    ),
                                )}
                                <p>
                                    {number(
                                        payload(state.variants)?.entries
                                            .length ?? 0,
                                    )}{" "}
                                    loaded variants ·{" "}
                                    {number(
                                        payload(state.variants)
                                            ?.total_matches ?? 0,
                                    )}{" "}
                                    known matching variants · page{" "}
                                    {state.pagination.variants.pageIndex + 1}
                                </p>
                                <button
                                    type="button"
                                    disabled={
                                        state.refreshing ||
                                        !state.pagination.variants.hasNext
                                    }
                                    onClick={() => {
                                        request(() => store.nextVariantsPage());
                                    }}
                                >
                                    Load more variants
                                </button>
                            </>
                        )}
                    </Panel>
                );
            case "files":
                return (
                    <Panel title="Files & manifest">
                        <p>
                            The whole manifest was read under the existing
                            artifact limit. These local table pages do not
                            reduce that read limit. Files are metadata; this
                            interface serves no file payload.
                        </p>
                        <LocalCollection
                            items={manifest.files}
                            identity={identity}
                            name="files"
                            render={(visible) => (
                                <div
                                    className="repository-table-scroll"
                                    tabIndex={0}
                                    role="region"
                                    aria-label="Manifest file table, scroll horizontally on narrow screens"
                                >
                                    <table aria-label="Manifest files">
                                        <thead>
                                            <tr>
                                                <th>Path</th>
                                                <th>Logical bytes</th>
                                                <th>Evidence</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {visible.map((file) => (
                                                <tr key={file.path}>
                                                    <th scope="row">
                                                        <code>{file.path}</code>
                                                    </th>
                                                    <td>{number(file.size)}</td>
                                                    <td>
                                                        <FileDetails
                                                            file={file}
                                                        />
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}
                        />
                        <dl className="repository-facts">
                            <Fact name="Manifest path (archive-root-relative)">
                                <code>{manifestPath ?? "Not observed"}</code>
                            </Fact>
                            <Fact name="Manifest file SHA256">
                                <code>
                                    {state.manifestDigest ?? "Not observed"}
                                </code>
                            </Fact>
                        </dl>
                        <p>
                            Manifest-file digest comes from the exact manifest
                            read boundary exposed by card provenance. It is not
                            a digest of reserialized HTTP JSON.
                        </p>
                    </Panel>
                );
            case "revisions":
                return (
                    <Panel title="Retained publications">
                        <p>
                            These are the loaded authoritative revision records
                            for this repository. A same-SHA repair has a
                            different publication ID.
                        </p>
                        {payload(state.revisions) === null ? (
                            <ReadState
                                page={state.revisions}
                                name="Retained publications"
                            />
                        ) : (
                            <>
                                <div
                                    className="repository-table-scroll"
                                    tabIndex={0}
                                    role="region"
                                    aria-label="Retained publications table"
                                >
                                    <table aria-label="Retained publications">
                                        <thead>
                                            <tr>
                                                <th>Exact identity</th>
                                                <th>
                                                    Generation and publication
                                                </th>
                                                <th>Snapshot</th>
                                                <th>Offline verification</th>
                                                <th>Select</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {payload(
                                                state.revisions,
                                            )?.revisions.map((row) => (
                                                <tr
                                                    key={
                                                        row.commit_sha +
                                                        row.publication_id
                                                    }
                                                >
                                                    <th scope="row">
                                                        <code>
                                                            {row.commit_sha}
                                                        </code>
                                                        <small>
                                                            <code>
                                                                {
                                                                    row.publication_id
                                                                }
                                                            </code>
                                                        </small>
                                                    </th>
                                                    <td>
                                                        {
                                                            row.publication_generation
                                                        }
                                                        <small>
                                                            {row.published_at}
                                                        </small>
                                                    </td>
                                                    <td>
                                                        {number(row.file_count)}{" "}
                                                        files
                                                        <small>
                                                            {bytes(
                                                                row.total_bytes,
                                                            )}{" "}
                                                            logical
                                                        </small>
                                                    </td>
                                                    <td>
                                                        {row.verification_state}
                                                    </td>
                                                    <td>
                                                        <button
                                                            type="button"
                                                            disabled={
                                                                state.refreshing
                                                            }
                                                            onClick={() => {
                                                                choosePublication(
                                                                    {
                                                                        commitSha:
                                                                            row.commit_sha,
                                                                        publicationId:
                                                                            row.publication_id,
                                                                    },
                                                                );
                                                            }}
                                                        >
                                                            View publication{" "}
                                                            {row.publication_id}
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                <p>
                                    {number(
                                        payload(state.revisions)?.revisions
                                            .length ?? 0,
                                    )}{" "}
                                    loaded publications · page{" "}
                                    {state.pagination.revisions.pageIndex + 1}
                                </p>
                                <button
                                    type="button"
                                    disabled={
                                        state.refreshing ||
                                        !state.pagination.revisions.hasNext
                                    }
                                    onClick={() => {
                                        request(() =>
                                            store.nextRevisionsPage(),
                                        );
                                    }}
                                >
                                    Load more revisions
                                </button>
                            </>
                        )}
                    </Panel>
                );
            case "integrity":
                return (
                    <Panel title="Selected publication integrity">
                        <dl className="repository-facts">
                            <Fact name="Selected publication offline verification">
                                {state.selectedRevision?.verification_state ??
                                    "Not observed in the loaded exact revision evidence"}
                            </Fact>
                            <Fact name="Publication ingestion verification">
                                {manifest.verification.outcome} ·{" "}
                                {manifest.verification.verified_at}
                            </Fact>
                            <Fact name="Ingestion completeness check">
                                {manifest.verification.completeness_checked
                                    ? "Complete manifest set checked"
                                    : "Not established"}
                            </Fact>
                            <Fact name="Ingestion hashed objects">
                                {number(manifest.verification.hashed_objects)}
                            </Fact>
                            <Fact name="Ingestion hashed bytes">
                                {number(manifest.verification.hashed_bytes)}
                            </Fact>
                            <Fact name="Ingestion reused digests">
                                {number(manifest.verification.reused_digests)}
                            </Fact>
                            <Fact name="Current inventory verification">
                                {status?.verification_state ?? "Not observed"} —
                                separate current-only evidence
                            </Fact>
                            <Fact name="Metadata observation status">
                                {observations[0]?.status ?? "Not observed"}
                            </Fact>
                        </dl>
                        <Notice>
                            Ingestion checks, README source checks, metadata
                            completeness and API health do not establish current
                            offline integrity for this selected publication.
                            Current inventory cannot qualify another retained
                            publication.
                        </Notice>
                        {manifest.repair !== null && (
                            <dl className="repository-facts">
                                <Fact name="Repair predecessor publication">
                                    <code>{manifest.repair.repair_of}</code>
                                </Fact>
                                <Fact name="Repair predecessor manifest">
                                    <code>
                                        {manifest.repair.repair_of_manifest}
                                    </code>
                                </Fact>
                                <Fact name="Repair time">
                                    {manifest.repair.repaired_at}
                                </Fact>
                                <Fact name="Repair transaction">
                                    <code>
                                        {manifest.repair.transaction_id}
                                    </code>
                                </Fact>
                                <Fact name="Repair reason">
                                    {manifest.repair.reason}
                                </Fact>
                            </dl>
                        )}
                    </Panel>
                );
            case "activity":
                return (
                    <Panel title="Loaded archive history">
                        <p>
                            This bounded list contains archive run IDs. It is
                            not filtered into a complete repository audit.
                            Inspect a loaded report explicitly to find qualified
                            repository/publication entries.
                        </p>
                        {payload(state.runs) === null ? (
                            <ReadState
                                page={state.runs}
                                name="Archive run history"
                            />
                        ) : (
                            <>
                                {payload(state.runs)?.runs.length === 0 && (
                                    <p>
                                        No runs are present in this loaded
                                        history page.
                                    </p>
                                )}
                                <ul className="repository-runs">
                                    {payload(state.runs)?.runs.map((runId) => (
                                        <li key={runId}>
                                            <code>{runId}</code>
                                            <button
                                                type="button"
                                                disabled={state.refreshing}
                                                onClick={() => {
                                                    request(() =>
                                                        store.openReport(runId),
                                                    );
                                                }}
                                            >
                                                Inspect report {runId}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                                <p>
                                    {number(
                                        payload(state.runs)?.runs.length ?? 0,
                                    )}{" "}
                                    loaded run IDs · page{" "}
                                    {state.pagination.runs.pageIndex + 1}
                                </p>
                                <button
                                    type="button"
                                    disabled={
                                        state.refreshing ||
                                        !state.pagination.runs.hasNext
                                    }
                                    onClick={() => {
                                        request(() => store.nextRunsPage());
                                    }}
                                >
                                    Load more runs
                                </button>
                            </>
                        )}
                        {state.reportRunId !== null &&
                            (selectedReport === null ? (
                                <ReadState
                                    page={state.report}
                                    name="Selected report"
                                />
                            ) : (
                                <Report
                                    value={selectedReport.report}
                                    selected={selected}
                                    generation={state.publicationGeneration}
                                />
                            ))}
                    </Panel>
                );
        }
    };
    return (
        <section
            ref={element}
            className="repository-detail"
            aria-label="Repository details"
        >
            <div className="repository-heading">
                <div>
                    <span
                        className={`repository-type ${target.repositoryType}`}
                    >
                        {target.repositoryType === "model"
                            ? "Model"
                            : "Dataset"}
                    </span>
                    <h2>{target.repositoryId}</h2>
                </div>
                <a href={upstream} target="_blank" rel="noopener noreferrer">
                    Open on Hugging Face ↗
                </a>
            </div>
            <div className="repository-actions">
                <button
                    type="button"
                    disabled={!state.connected || state.refreshing}
                    onClick={chooseCurrent}
                >
                    Select current publication
                </button>
                <button
                    type="button"
                    disabled={
                        !state.connected ||
                        state.refreshing ||
                        addressError !== null ||
                        !sameTarget
                    }
                    onClick={() => {
                        request(() => store.refresh());
                    }}
                >
                    Refresh selected publication
                </button>
            </div>
            {addressError !== null && (
                <p role="alert" className="repository-warning">
                    {addressError}
                </p>
            )}
            {announcement !== null && <p role="status">{announcement}</p>}
            {sameTarget && state.notice !== null && (
                <Notice>{messages[state.notice]}</Notice>
            )}
            {sameTarget && state.refreshing && (
                <p role="status">
                    Loading repository evidence. The selected identity remains
                    explicit.
                </p>
            )}
            {selected !== null && (
                <section
                    aria-label="Selected publication"
                    className="repository-selection"
                >
                    <p>
                        {isCurrent
                            ? "Selected current publication"
                            : "Selected exact publication"}{" "}
                        · generation{" "}
                        {state.publicationGeneration ?? "Not observed"}
                    </p>
                    <div>
                        <strong>Commit SHA</strong>
                        <code>{selected.commitSha}</code>
                        <button
                            type="button"
                            onClick={() => {
                                void copy(selected.commitSha, "Commit SHA");
                            }}
                        >
                            Copy commit SHA
                        </button>
                    </div>
                    <div>
                        <strong>Publication ID</strong>
                        <code>{selected.publicationId}</code>
                        <button
                            type="button"
                            onClick={() => {
                                void copy(
                                    selected.publicationId,
                                    "Publication ID",
                                );
                            }}
                        >
                            Copy publication ID
                        </button>
                    </div>
                </section>
            )}
            {manifest === null ? (
                <Panel title="Publication evidence">
                    {addressError !== null ? (
                        <p>
                            Correct the address before loading publication
                            evidence.
                        </p>
                    ) : !sameTarget ||
                      !ownerValidated ||
                      state.phase === "idle" ||
                      state.phase === "loading" ? (
                        <p role="status">Loading selected publication.</p>
                    ) : state.phase === "unpublished" ? (
                        <p>
                            No current publication is available for this
                            repository. Configuration is intent, not proof of
                            archived bytes.
                        </p>
                    ) : state.phase === "unavailable" ? (
                        <p role="alert">
                            Selected publication is unavailable. Its reference
                            may have been removed or replaced. No latest
                            fallback was selected.
                        </p>
                    ) : (
                        <p role="alert">
                            Publication evidence could not be loaded or
                            verified. No latest fallback was selected. Check the
                            connection and exact identity before retrying.
                        </p>
                    )}
                </Panel>
            ) : (
                <>
                    <div
                        className="repository-summaries"
                        role="group"
                        aria-label="Selected publication evidence summary"
                    >
                        <div>
                            <span>Archive snapshot</span>
                            <strong>{number(manifest.file_count)} files</strong>
                            <small>
                                {bytes(manifest.total_bytes)} logical · selected
                                publication
                            </small>
                            <small>
                                {inventory === null
                                    ? "Retained count not observed"
                                    : `${number(inventory.retained_revisions)} retained revisions in current inventory`}
                            </small>
                        </div>
                        <div>
                            <span>Selected offline integrity</span>
                            <strong>
                                {state.selectedRevision?.verification_state ??
                                    "Not observed"}
                            </strong>
                            <small>
                                Exact selected SHA/publication evidence
                            </small>
                        </div>
                        <div>
                            <span>Technical metadata</span>
                            <strong>
                                {observations[0]?.status ?? "Not observed"}
                            </strong>
                            <small>
                                {observations[0]?.extractor_version ??
                                    "No observation source joined"}
                            </small>
                            <small>Separate from archive integrity</small>
                        </div>
                    </div>
                    <div
                        className="repository-tabs"
                        role="tablist"
                        aria-label="Repository evidence tabs"
                    >
                        {REPOSITORY_TABS.map((item) => (
                            <button
                                key={item}
                                type="button"
                                role="tab"
                                tabIndex={tab === item ? 0 : -1}
                                aria-selected={tab === item}
                                aria-controls="repository-active-panel"
                                id={`repository-tab-${item}`}
                                onKeyDown={(event) => {
                                    if (
                                        event.altKey ||
                                        event.ctrlKey ||
                                        event.metaKey
                                    )
                                        return;
                                    const index = REPOSITORY_TABS.indexOf(item);
                                    const nextIndex =
                                        event.key === "ArrowRight"
                                            ? (index + 1) %
                                              REPOSITORY_TABS.length
                                            : event.key === "ArrowLeft"
                                              ? (index +
                                                    REPOSITORY_TABS.length -
                                                    1) %
                                                REPOSITORY_TABS.length
                                              : event.key === "Home"
                                                ? 0
                                                : event.key === "End"
                                                  ? REPOSITORY_TABS.length - 1
                                                  : null;
                                    if (nextIndex === null) return;
                                    const next = REPOSITORY_TABS[nextIndex];
                                    if (next === undefined) return;
                                    event.preventDefault();
                                    chooseTab(next);
                                    event.currentTarget.parentElement
                                        ?.querySelector<HTMLButtonElement>(
                                            `#repository-tab-${next}`,
                                        )
                                        ?.focus();
                                }}
                                onClick={() => {
                                    chooseTab(item);
                                }}
                            >
                                {label(item, target.repositoryType)}
                            </button>
                        ))}
                    </div>
                    <div className="repository-content">
                        <div
                            role="tabpanel"
                            id="repository-active-panel"
                            aria-labelledby={`repository-tab-${tab}`}
                        >
                            {content()}
                        </div>
                        <aside aria-label="Selected publication facts">
                            <Panel title="Archived publication">
                                <dl className="repository-facts">
                                    <Fact name="Repository type">
                                        {target.repositoryType}
                                    </Fact>
                                    <Fact name="Requested revision">
                                        {manifest.requested_revision}
                                    </Fact>
                                    <Fact name="Published">
                                        {manifest.published_at}
                                    </Fact>
                                    <Fact name="Publication mode">
                                        {manifest.publication_mode}
                                    </Fact>
                                    <Fact name="Archive-relative tree">
                                        <code>{archiveTree}</code>
                                    </Fact>
                                    <Fact name="Published-relative tree">
                                        <code>
                                            {publishedTree ?? "Not joined"}
                                        </code>
                                    </Fact>
                                    <Fact name="Manifest path (archive-root-relative)">
                                        <code>
                                            {manifestPath ?? "Not observed"}
                                        </code>
                                    </Fact>
                                    <Fact name="Manifest file SHA256">
                                        <code>
                                            {state.manifestDigest ??
                                                "Not observed"}
                                        </code>
                                    </Fact>
                                </dl>
                                {archiveTree !== null && (
                                    <button
                                        type="button"
                                        onClick={() => {
                                            void copy(
                                                archiveTree,
                                                "Archive-relative tree",
                                            );
                                        }}
                                    >
                                        Copy archive-relative tree
                                    </button>
                                )}
                                {publishedTree !== null && (
                                    <button
                                        type="button"
                                        onClick={() => {
                                            void copy(
                                                publishedTree,
                                                "Published-relative tree",
                                            );
                                        }}
                                    >
                                        Copy published-relative tree
                                    </button>
                                )}
                                <p>
                                    Archive-relative locators start at the
                                    archive root; published-relative locators
                                    start at the consumer's read-only published/
                                    mount. These are not HTTP download links.
                                </p>
                                {card !== null && (
                                    <p>
                                        Archived README capture: {card.state}.{" "}
                                        {card.captured_at === null
                                            ? "Capture time not observed."
                                            : `Captured ${card.captured_at}.`}
                                    </p>
                                )}
                            </Panel>
                            <OperatorTags entry={entry} />
                            <Panel title="Metadata coverage">
                                {catalog === null ? (
                                    <ReadState
                                        page={state.catalog}
                                        name="Metadata coverage"
                                    />
                                ) : (
                                    <>
                                        <dl className="repository-facts">
                                            <Fact name="Scoped repositories">
                                                {number(
                                                    catalog.coverage
                                                        .repositories,
                                                )}
                                            </Fact>
                                            <Fact name="Scoped publications">
                                                {number(
                                                    catalog.coverage
                                                        .publications,
                                                )}
                                            </Fact>
                                            <Fact name="Usable observations">
                                                {number(
                                                    catalog.coverage.usable,
                                                )}
                                            </Fact>
                                            <Fact name="Partial observations">
                                                {number(
                                                    catalog.coverage.partial,
                                                )}
                                            </Fact>
                                            <Fact name="Unsupported observations">
                                                {number(
                                                    catalog.coverage
                                                        .unsupported,
                                                )}
                                            </Fact>
                                            <Fact name="Failed observations">
                                                {number(
                                                    catalog.coverage.failed,
                                                )}
                                            </Fact>
                                            <Fact name="Missing observations">
                                                {number(
                                                    catalog.coverage.missing,
                                                )}
                                            </Fact>
                                            <Fact name="Known tag sources">
                                                {number(
                                                    catalog.coverage.tags_known,
                                                )}
                                            </Fact>
                                            <Fact name="Unknown tag sources">
                                                {number(
                                                    catalog.coverage
                                                        .tags_unknown,
                                                )}
                                            </Fact>
                                        </dl>
                                        <p>
                                            {catalog.coverage.incomplete
                                                ? "Metadata coverage is incomplete; missing declarations remain unknown."
                                                : "Metadata coverage is complete for this selected scope."}
                                        </p>
                                    </>
                                )}
                            </Panel>
                        </aside>
                    </div>
                </>
            )}
            {manifest === null &&
                sameTarget &&
                ownerValidated &&
                state.phase === "unpublished" && <OperatorTags entry={entry} />}
            <Notice>
                Availability, supplemental metadata and exact-publication
                integrity are different facts. This view transfers no archive
                payload and performs no model or dataset execution.
            </Notice>
        </section>
    );
}
