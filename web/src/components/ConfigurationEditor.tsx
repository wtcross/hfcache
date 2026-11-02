import {
    useEffect,
    useId,
    useRef,
    useState,
    useSyncExternalStore,
} from "react";
import type { FormEvent, ReactNode } from "react";
import { Notice } from "../primitives";
import { ChoiceControl } from "./ChoiceControl";
import type {
    ConfigurationSnapshot,
    ConfigurationStore,
    ReloadReview,
} from "../configuration/configuration-state";
import { MAX_DRAFT_BYTES } from "../configuration/draft";
import { normalizeManagedTags } from "../wire/config-semantics";
import { decodeRepositoryConfig } from "../wire/generated";
import type { EditableConfig, RepositoryConfig } from "../wire/generated";
import type { ReadResult } from "../api/types";
import type { ObservationSnapshot } from "../state/operation-observation";

const PAGE_SIZE = 25;
type RepositoryForm = {
    kind: "repository";
    existing: boolean;
    historical: boolean;
    type: "model" | "dataset";
    id: string;
    revision: string;
    enabled: boolean;
    tags: string;
    dependencies: string;
};
const NUMBERS = [
    { key: "minimum_free_space_gib", label: "Minimum free space (GiB)" },
    { key: "minimum_free_space_percent", label: "Minimum free space (%)" },
    { key: "max_workers", label: "Maximum sync workers" },
    { key: "lock_wait_seconds", label: "Sync lock wait (seconds)" },
    { key: "stale_staging_age_hours", label: "Stale staging age (hours)" },
    { key: "verification_wait", label: "Verification lock wait (seconds)" },
    {
        key: "retired_instance_grace_hours",
        label: "Retired instance grace (hours)",
    },
] as const;
type SettingsForm = {
    kind: "settings";
    publication_mode: "hardlink" | "copy";
    maximum_revisions: number;
    continue_on_repository_error: boolean;
} & Record<(typeof NUMBERS)[number]["key"], string>;
type LocalForm = RepositoryForm | SettingsForm | { kind: "json"; text: string };

function lines(value: string): string[] {
    return value === "" ? [] : value.split("\n");
}
function configuredTagSuggestions(
    repositories: readonly RepositoryConfig[],
): readonly string[] {
    const tags = new Set<string>();
    let work = 0;
    outer: for (const repository of repositories) {
        if (++work > 4096) break;
        for (const tag of repository.tags) {
            if (++work > 4096 || tags.size >= 64) break outer;
            tags.add(tag);
        }
    }
    return [...tags].sort();
}
function whole(value: string): number {
    if (
        !/^(?:0|[1-9][0-9]{0,15})$/u.test(value) ||
        !Number.isSafeInteger(Number(value))
    )
        throw new Error("configuration-number");
    return Number(value);
}
function settingsForm(value: EditableConfig): SettingsForm {
    return {
        kind: "settings",
        publication_mode: value.storage.publication_mode,
        maximum_revisions: value.storage.maximum_revisions,
        minimum_free_space_gib: String(value.storage.minimum_free_space_gib),
        minimum_free_space_percent: String(
            value.storage.minimum_free_space_percent,
        ),
        max_workers: String(value.sync.max_workers),
        lock_wait_seconds: String(value.sync.lock_wait_seconds),
        continue_on_repository_error: value.sync.continue_on_repository_error,
        stale_staging_age_hours: String(value.sync.stale_staging_age_hours),
        verification_wait: String(value.verification.lock_wait_seconds),
        retired_instance_grace_hours: String(
            value.repair.retired_instance_grace_hours,
        ),
    };
}
function Page<T>({
    items,
    name,
    render,
}: {
    items: readonly T[];
    name: string;
    render: (item: T, index: number) => ReactNode;
}) {
    const [requested, setRequested] = useState(0);
    const last = Math.max(0, Math.ceil(items.length / PAGE_SIZE) - 1);
    const page = Math.min(requested, last);
    return (
        <div className="configuration-list">
            <p>
                {items.length} {name}; page {page + 1} of {last + 1}, at most25
                shown.
            </p>
            {items.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE).map(render)}
            {last > 0 && (
                <div className="configuration-toolbar">
                    <button
                        type="button"
                        disabled={page === 0}
                        onClick={() => {
                            setRequested(page - 1);
                        }}
                    >
                        Previous {name}
                    </button>
                    <button
                        type="button"
                        disabled={page === last}
                        onClick={() => {
                            setRequested(page + 1);
                        }}
                    >
                        Next {name}
                    </button>
                </div>
            )}
        </div>
    );
}
function Failure({ result }: { result: ReadResult<unknown, unknown> | null }) {
    if (result === null || result.kind === "success") return null;
    const codes =
        result.kind === "domain_failure"
            ? result.response.envelope.errors.map((error) => error.code)
            : result.kind === "api_problem"
              ? [result.problem.code]
              : result.kind === "protocol_failure"
                ? (result.preserved?.errors.map((error) => error.code) ?? [])
                : [];
    return (
        <p role="alert">
            Configuration evidence failed ({result.kind}).
            {codes.length > 0
                ? " Diagnostic codes: " + codes.slice(0, 25).join(", ") + "."
                : ""}
            {result.kind === "api_problem" && result.status === 409
                ? " The installed base changed. Compare, reload explicitly and review a new draft; no automatic merge is performed."
                : ""}
            No installation is confirmed by this response.
        </p>
    );
}
function Observation({
    title,
    observation,
}: {
    title: string;
    observation: ObservationSnapshot | null;
}) {
    if (observation === null) return null;
    return (
        <div className="configuration-facts">
            <h3>{title}</h3>
            <p>
                Observation: {observation.phase}.{" "}
                {observation.pauseReason === null
                    ? ""
                    : "Reason: " + observation.pauseReason + "."}
            </p>
            {observation.receipt !== null && (
                <p>
                    Original operation{" "}
                    <code>{observation.receipt.operation_id}</code>:{" "}
                    {observation.receipt.state}. API receipt state is separate
                    from installed configuration.
                </p>
            )}
            <Failure result={observation.failure} />
            {observation.result !== null && (
                <Failure result={observation.result} />
            )}
        </div>
    );
}

function ApplicationEvidence({
    state,
    onObserve,
}: {
    state: ConfigurationSnapshot;
    onObserve: () => void;
}) {
    const outcome =
        state.outcome?.kind === "outcome" &&
        state.outcome.result.kind === "success"
            ? state.outcome.result.payload
            : null;
    return (
        <>
            <Observation
                title="Original configuration application"
                observation={state.applicationObservation}
            />
            {state.applicationRecordId !== null && (
                <p>
                    Saved application record{" "}
                    <code>{state.applicationRecordId}</code>. An accepted or
                    succeeded API receipt alone is not installed success.
                </p>
            )}
            <button
                type="button"
                disabled={
                    !state.canRead ||
                    state.pending !== null ||
                    state.applicationRecordId === null
                }
                onClick={onObserve}
            >
                Observe original application outcome
            </button>
            {state.outcome !== null && (
                <Failure result={state.outcome.result} />
            )}
            {outcome !== null && (
                <div className="configuration-facts">
                    <p>
                        Host outcome: {outcome.state}; pending:{" "}
                        {outcome.pending ? "true" : "false"}. Original operation{" "}
                        <code>{outcome.operation_id}</code>.
                    </p>
                    <p>
                        {outcome.state === "confirmed" && !outcome.pending
                            ? "Installed configuration confirmed. The exact host outcome is independent of the API receipt."
                            : "Installation is not confirmed. Preserve original handles; do not resubmit Apply to discover an outcome."}
                    </p>
                </div>
            )}
        </>
    );
}

export function ConfigurationEditor({ store }: { store: ConfigurationStore }) {
    const state = useSyncExternalStore(
        store.subscribe,
        store.snapshot,
        store.snapshot,
    );
    return (
        <section
            className="configuration-editor"
            aria-label="Configuration and tags"
        >
            <EditorSession
                key={
                    String(state.authGeneration) +
                    ":" +
                    String(state.editorRevision)
                }
                store={store}
                state={state}
            />
        </section>
    );
}
function EditorSession({
    store,
    state,
}: {
    store: ConfigurationStore;
    state: ConfigurationSnapshot;
}) {
    const id = useId();
    const [form, setForm] = useState<LocalForm | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showTagSuggestions, setShowTagSuggestions] = useState(false);
    const [reloadReview, setReloadReview] = useState<ReloadReview | null>(null);
    const keepEditing = useRef<HTMLButtonElement>(null);
    const replaceDraft = useRef<HTMLButtonElement>(null);
    const reloadButton = useRef<HTMLButtonElement>(null);
    const activeReloadReview =
        reloadReview !== null &&
        reloadReview.generation === state.generation &&
        reloadReview.authGeneration === state.authGeneration
            ? reloadReview
            : null;
    useEffect(() => {
        if (reloadReview === null) return;
        if (activeReloadReview === null) {
            store.cancelReload(reloadReview);
            reloadButton.current?.focus();
        } else keepEditing.current?.focus();
    }, [reloadReview, activeReloadReview, store]);
    const live = useRef(true);
    useEffect(() => {
        live.current = true;
        return () => {
            live.current = false;
        };
    }, []);
    const editable = state.prepared?.editable ?? null;
    const suggestedTags =
        showTagSuggestions && state.base !== null
            ? configuredTagSuggestions(state.base.editable.repositories)
            : [];
    const busy = state.pending !== null;
    const mayStart = state.canEdit && !busy && !state.editing;
    function request(work: () => Promise<unknown>) {
        const authGeneration = state.authGeneration;
        setError(null);
        const refused = () => {
            if (
                live.current &&
                store.snapshot().authGeneration === authGeneration
            )
                setError(
                    "Configuration evidence is unavailable. Preserve original operation handles; no request was retried.",
                );
        };
        try {
            void work().catch(refused);
        } catch {
            refused();
        }
    }
    function change(next: LocalForm) {
        if (!store.setEditing(true, next)) {
            setError(
                "The local form exceeds the supported draft limit. No readiness was retained.",
            );
            return;
        }
        setForm(next);
        setError(null);
    }
    function text(
        value: string,
        limit: number,
        next: (value: string) => LocalForm,
    ) {
        if (value.length > limit) {
            store.setEditing(true, form);
            setError(
                "This field exceeds its supported local editing limit. No readiness was retained.",
            );
            return;
        }
        change(next(value));
    }
    function close() {
        setForm(null);
        setError(null);
    }
    function cancelReload() {
        if (reloadReview !== null) store.cancelReload(reloadReview);
        setReloadReview(null);
        reloadButton.current?.focus();
    }
    function repository(
        entry: RepositoryConfig | null,
        historical = false,
        target = "",
    ) {
        change({
            kind: "repository",
            existing: entry !== null,
            historical,
            type: entry?.type ?? state.intent?.repositoryType ?? "model",
            id: entry?.id ?? target,
            revision: entry?.revision ?? "main",
            enabled: entry?.enabled ?? true,
            tags: (entry?.tags ?? []).join("\n"),
            dependencies: (entry?.declared_dependencies ?? []).join("\n"),
        });
    }
    function updateRepository(event: FormEvent) {
        event.preventDefault();
        if (form?.kind !== "repository") return;
        try {
            if (
                !form.existing &&
                editable?.repositories.some(
                    (entry) => entry.type === form.type && entry.id === form.id,
                )
            ) {
                setError(
                    "This repository is already configured. Edit its complete existing entry instead of replacing it with new defaults.",
                );
                return;
            }
            const entry = decodeRepositoryConfig({
                type: form.type,
                id: form.id,
                revision: form.revision,
                enabled: form.enabled,
                tags: normalizeManagedTags(lines(form.tags)),
                declared_dependencies: lines(form.dependencies),
            });
            if (store.upsert(entry)) close();
        } catch {
            setError(
                "Repository fields are invalid. Check the repository identity, revision, tags and declared dependencies. The prior valid draft is preserved.",
            );
        }
    }
    function updateSettings(event: FormEvent) {
        event.preventDefault();
        if (form?.kind !== "settings" || editable === null) return;
        try {
            if (
                store.replaceEditable({
                    ...editable,
                    storage: {
                        ...editable.storage,
                        publication_mode: form.publication_mode,
                        maximum_revisions: form.maximum_revisions,
                        minimum_free_space_gib: whole(
                            form.minimum_free_space_gib,
                        ),
                        minimum_free_space_percent: whole(
                            form.minimum_free_space_percent,
                        ),
                    },
                    sync: {
                        ...editable.sync,
                        max_workers: whole(form.max_workers),
                        lock_wait_seconds: whole(form.lock_wait_seconds),
                        continue_on_repository_error:
                            form.continue_on_repository_error,
                        stale_staging_age_hours: whole(
                            form.stale_staging_age_hours,
                        ),
                    },
                    verification: {
                        ...editable.verification,
                        lock_wait_seconds: whole(form.verification_wait),
                    },
                    repair: {
                        ...editable.repair,
                        retired_instance_grace_hours: whole(
                            form.retired_instance_grace_hours,
                        ),
                    },
                })
            )
                close();
        } catch {
            setError(
                "Settings require exact whole numbers within the supported limits. The prior valid draft is preserved.",
            );
        }
    }
    return (
        <div className="panel">
            {activeReloadReview !== null && (
                <div className="draft-navigation-overlay">
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby={id + "-reload-title"}
                        aria-describedby={id + "-reload-description"}
                        className="draft-navigation-dialog"
                        onKeyDown={(event) => {
                            if (event.key === "Escape") {
                                event.preventDefault();
                                cancelReload();
                            } else if (event.key === "Tab") {
                                event.preventDefault();
                                if (
                                    document.activeElement ===
                                    keepEditing.current
                                )
                                    replaceDraft.current?.focus();
                                else keepEditing.current?.focus();
                            }
                        }}
                    >
                        <h2 id={id + "-reload-title"}>
                            Replace unsaved configuration?
                        </h2>
                        <p id={id + "-reload-description"}>
                            Reload replaces your draft and form edits only after
                            a successful read. A failed read keeps them
                            available for editing. Validation and preview
                            readiness retire when the read starts; original
                            operation handles remain.
                        </p>
                        <button
                            ref={keepEditing}
                            type="button"
                            onClick={cancelReload}
                        >
                            Keep editing
                        </button>
                        <button
                            ref={replaceDraft}
                            type="button"
                            onClick={() => {
                                const reviewed = activeReloadReview;
                                setReloadReview(null);
                                request(() => store.reload(reviewed));
                            }}
                        >
                            Reload and replace draft
                        </button>
                    </div>
                </div>
            )}
            <header className="panel-heading">
                <h2>Configuration and tags</h2>
            </header>
            <div className="panel-body">
                <p>
                    One private browser draft changes supported settings and
                    complete configured repository entries. Protected storage,
                    Hub credentials and server authority remain with the host.
                    Removing or disabling configuration does not purge archived
                    bytes; retention changes do not delete content immediately.
                </p>
                <div className="configuration-toolbar">
                    <button
                        type="button"
                        disabled={!state.canRead || busy || state.dirty}
                        onClick={() => {
                            request(() => store.load());
                        }}
                    >
                        Read installed configuration
                    </button>
                    <button
                        type="button"
                        disabled={!state.canRead || busy || state.base === null}
                        onClick={() => {
                            request(() => store.compare());
                        }}
                    >
                        Compare installed configuration
                    </button>
                    <button
                        ref={reloadButton}
                        type="button"
                        disabled={!state.canRead || busy || state.base === null}
                        onClick={() => {
                            if (state.dirty)
                                setReloadReview(store.reviewReload());
                            else request(() => store.reload());
                        }}
                    >
                        Reload installed configuration
                    </button>
                    <button
                        type="button"
                        disabled={busy || !state.dirty}
                        onClick={() => {
                            store.discard();
                            close();
                        }}
                    >
                        Discard draft
                    </button>
                </div>
                {state.notice !== null && <Notice>{state.notice}</Notice>}
                {busy && (
                    <p role="status">
                        Configuration {state.pending} is pending. Admission is
                        not installed success.
                    </p>
                )}
                {error !== null && <p role="alert">{error}</p>}
                <Failure result={state.readResult} />
                {!state.canRead && (
                    <p role="alert">
                        Configuration read permission or connection is
                        unavailable. Original operation handles remain in
                        Operations.
                    </p>
                )}
                {state.base === null || editable === null ? (
                    <p>Installed editable configuration has not been loaded.</p>
                ) : (
                    <>
                        <dl className="configuration-facts">
                            <dt>Exact draft base revision</dt>
                            <dd>
                                <code>{state.base.base_revision}</code>
                            </dd>
                            <dt>Archive identity</dt>
                            <dd>
                                <code>{state.base.archive_id}</code>
                            </dd>
                        </dl>
                        <p>
                            {state.dirty
                                ? "Unsaved draft changes remain in this browser."
                                : "The editable draft matches its installed base."}{" "}
                            Raw draft text is not stored in localStorage.
                        </p>
                        {!state.canEdit && state.pending !== "read" && (
                            <Notice>
                                Configuration is read-only for this session.
                                Host-read permission does not grant
                                configuration editing.
                            </Notice>
                        )}
                        {state.editing && form === null && (
                            <p role="alert">
                                Unfinished form edits are not available in this
                                view. Discard the draft explicitly before
                                starting another form.
                            </p>
                        )}
                        <details>
                            <summary>
                                Protected fields and manual authority changes
                            </summary>
                            <p>
                                These values are withheld. This editor never
                                submits redaction markers or edits host
                                authority. Provision authority changes manually
                                through the documented host workflow.
                            </p>
                            <ul>
                                {state.base.protected_fields.map((field) => (
                                    <li key={field.field}>
                                        <code>{field.field}</code>:{" "}
                                        {field.description}
                                    </li>
                                ))}
                            </ul>
                        </details>
                        {state.intent !== null && (
                            <Notice>
                                Requested {state.intent.repositoryType}:
                                <code>{state.intent.repositoryId}</code>.
                                {state.intent.historical
                                    ? " Historical labels are read-only observations. Reconfiguration starts from defaults and empty tags when no current entry exists."
                                    : " Configured values come from the installed editable projection and this draft, never catalog declarations."}
                                <button
                                    type="button"
                                    disabled={!mayStart}
                                    onClick={() => {
                                        const intent = state.intent;
                                        if (intent === null) return;
                                        repository(
                                            editable.repositories.find(
                                                (row) =>
                                                    row.type ===
                                                        intent.repositoryType &&
                                                    row.id ===
                                                        intent.repositoryId,
                                            ) ?? null,
                                            intent.historical,
                                            intent.repositoryId,
                                        );
                                        store.clearIntent();
                                    }}
                                >
                                    Edit requested repository
                                </button>
                            </Notice>
                        )}
                        <div className="configuration-toolbar">
                            <button
                                type="button"
                                disabled={!mayStart}
                                onClick={() => {
                                    repository(null);
                                }}
                            >
                                Add repository
                            </button>
                            <button
                                type="button"
                                disabled={!mayStart}
                                onClick={() => {
                                    change(settingsForm(editable));
                                }}
                            >
                                Edit global settings
                            </button>
                            <button
                                type="button"
                                disabled={!mayStart}
                                onClick={() => {
                                    change({
                                        kind: "json",
                                        text: JSON.stringify(editable, null, 2),
                                    });
                                }}
                            >
                                Supported JSON view
                            </button>
                        </div>
                        {form?.kind === "repository" && (
                            <form
                                className="configuration-form"
                                aria-label="Repository draft"
                                onSubmit={updateRepository}
                            >
                                <fieldset disabled={!state.canEdit || busy}>
                                    <legend>Repository entry</legend>
                                    {form.historical && !form.existing && (
                                        <p>
                                            Historical tags were not copied.
                                            Review this new default
                                            configuration explicitly.
                                        </p>
                                    )}
                                    <fieldset disabled={form.existing}>
                                        <legend>Repository type</legend>
                                        {(["model", "dataset"] as const).map(
                                            (type) => (
                                                <label key={type}>
                                                    <input
                                                        type="radio"
                                                        name={
                                                            id +
                                                            "-repository-type"
                                                        }
                                                        checked={
                                                            form.type === type
                                                        }
                                                        onChange={() => {
                                                            change({
                                                                ...form,
                                                                type,
                                                            });
                                                        }}
                                                    />
                                                    {type === "model"
                                                        ? "Model"
                                                        : "Dataset"}
                                                </label>
                                            ),
                                        )}
                                    </fieldset>
                                    <label>
                                        Repository ID
                                        <input
                                            value={form.id}
                                            maxLength={193}
                                            disabled={form.existing}
                                            onChange={(event) => {
                                                text(
                                                    event.target.value,
                                                    193,
                                                    (value) => ({
                                                        ...form,
                                                        id: value,
                                                    }),
                                                );
                                            }}
                                        />
                                    </label>
                                    <p>
                                        Existing type/ID is fixed. Add a
                                        separate entry and remove the old
                                        configuration to change identity.
                                    </p>
                                    <label>
                                        Requested revision
                                        <input
                                            value={form.revision}
                                            maxLength={1024}
                                            onChange={(event) => {
                                                text(
                                                    event.target.value,
                                                    1024,
                                                    (value) => ({
                                                        ...form,
                                                        revision: value,
                                                    }),
                                                );
                                            }}
                                        />
                                    </label>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={form.enabled}
                                            onChange={(event) => {
                                                change({
                                                    ...form,
                                                    enabled:
                                                        event.target.checked,
                                                });
                                            }}
                                        />
                                        Enabled
                                    </label>
                                    <label>
                                        Tags (one per line)
                                        <textarea
                                            value={form.tags}
                                            maxLength={8255}
                                            onChange={(event) => {
                                                text(
                                                    event.target.value,
                                                    8255,
                                                    (value) => ({
                                                        ...form,
                                                        tags: value,
                                                    }),
                                                );
                                            }}
                                        />
                                    </label>
                                    <p>
                                        At most64 raw tags,128 raw characters
                                        each; ASCII spaces trim, ASCII letters
                                        lowercase, duplicates collapse. Empty
                                        tag lines are invalid.
                                    </p>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowTagSuggestions(true);
                                        }}
                                    >
                                        Show configured tag suggestions
                                    </button>
                                    {showTagSuggestions && (
                                        <div
                                            className="configuration-tag-suggestions"
                                            aria-label="Configured tag suggestions"
                                            role="region"
                                            tabIndex={0}
                                        >
                                            <p>
                                                At most64 unique suggestions
                                                from the already loaded
                                                installed base, with at most4096
                                                inspected entries/tags. These
                                                are current configured labels,
                                                not historical catalog tags or a
                                                complete tag search; showing
                                                them performs no request and
                                                does not change the draft.
                                            </p>
                                            {suggestedTags.length === 0 ? (
                                                <p>
                                                    No configured tags found
                                                    within this bounded base
                                                    lookup.
                                                </p>
                                            ) : (
                                                <ul>
                                                    {suggestedTags.map(
                                                        (tag) => (
                                                            <li key={tag}>
                                                                <code>
                                                                    {tag}
                                                                </code>
                                                            </li>
                                                        ),
                                                    )}
                                                </ul>
                                            )}
                                        </div>
                                    )}
                                    <label>
                                        Declared dependencies (one per line)
                                        <textarea
                                            value={form.dependencies}
                                            maxLength={MAX_DRAFT_BYTES}
                                            onChange={(event) => {
                                                text(
                                                    event.target.value,
                                                    MAX_DRAFT_BYTES,
                                                    (value) => ({
                                                        ...form,
                                                        dependencies: value,
                                                    }),
                                                );
                                            }}
                                        />
                                    </label>
                                    <button type="submit">
                                        Update draft repository
                                    </button>
                                </fieldset>
                            </form>
                        )}
                        {form?.kind === "settings" && (
                            <form
                                className="configuration-form"
                                aria-label="Global settings draft"
                                onSubmit={updateSettings}
                            >
                                <fieldset disabled={!state.canEdit || busy}>
                                    <legend>Supported global settings</legend>
                                    <ChoiceControl
                                        label="Publication mode"
                                        disabled={!state.canEdit || busy}
                                        value={form.publication_mode}
                                        options={[
                                            {
                                                value: "hardlink",
                                                label: "Hardlink",
                                            },
                                            { value: "copy", label: "Copy" },
                                        ]}
                                        onChange={(publication_mode) => {
                                            change({
                                                ...form,
                                                publication_mode,
                                            });
                                        }}
                                    />
                                    <ChoiceControl
                                        label="Maximum retained revisions"
                                        disabled={!state.canEdit || busy}
                                        value={form.maximum_revisions}
                                        options={[
                                            { value: 3, label: "3" },
                                            { value: 5, label: "5" },
                                        ]}
                                        onChange={(maximum_revisions) => {
                                            change({
                                                ...form,
                                                maximum_revisions,
                                            });
                                        }}
                                    />
                                    {NUMBERS.map((field) => (
                                        <label key={field.key}>
                                            {field.label}
                                            <input
                                                value={form[field.key]}
                                                inputMode="numeric"
                                                maxLength={16}
                                                onChange={(event) => {
                                                    text(
                                                        event.target.value,
                                                        16,
                                                        (value) => ({
                                                            ...form,
                                                            [field.key]: value,
                                                        }),
                                                    );
                                                }}
                                            />
                                        </label>
                                    ))}
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={
                                                form.continue_on_repository_error
                                            }
                                            onChange={(event) => {
                                                change({
                                                    ...form,
                                                    continue_on_repository_error:
                                                        event.target.checked,
                                                });
                                            }}
                                        />
                                        Continue after repository error
                                    </label>
                                    <label>
                                        Dependency policy
                                        <input
                                            value="warn"
                                            readOnly
                                            aria-readonly="true"
                                        />
                                    </label>
                                    <button type="submit">
                                        Update draft settings
                                    </button>
                                </fieldset>
                            </form>
                        )}
                        {form?.kind === "json" && (
                            <form
                                className="configuration-form"
                                aria-label="Supported JSON draft"
                                onSubmit={(event) => {
                                    event.preventDefault();
                                    if (store.replaceJson(form.text)) close();
                                }}
                            >
                                <label>
                                    Editable configuration JSON
                                    <textarea
                                        className="configuration-json"
                                        value={form.text}
                                        maxLength={MAX_DRAFT_BYTES}
                                        disabled={!state.canEdit || busy}
                                        onChange={(event) => {
                                            text(
                                                event.target.value,
                                                MAX_DRAFT_BYTES,
                                                (value) => ({
                                                    kind: "json",
                                                    text: value,
                                                }),
                                            );
                                        }}
                                    />
                                </label>
                                <p>
                                    Only the complete supported editable JSON
                                    projection is accepted. Unknown/protected
                                    fields, TOML, duplicate identities and
                                    reordered existing entries refuse; no
                                    browser TOML reconstruction is performed.
                                </p>
                                <button
                                    type="submit"
                                    disabled={!state.canEdit || busy}
                                >
                                    Use JSON as draft
                                </button>
                            </form>
                        )}
                        {form !== null && (
                            <button
                                type="button"
                                disabled={busy}
                                onClick={() => {
                                    store.setEditing(false);
                                    close();
                                }}
                            >
                                Cancel form edits
                            </button>
                        )}
                        <h3>Configured draft repositories</h3>
                        <Page
                            key={state.base.base_revision}
                            items={editable.repositories}
                            name="repositories"
                            render={(entry) => (
                                <article
                                    key={entry.type + ":" + entry.id}
                                    className="configuration-entry"
                                >
                                    <h4>
                                        {entry.type}:<code>{entry.id}</code>
                                    </h4>
                                    <p>
                                        {entry.enabled ? "Enabled" : "Disabled"}
                                        ; requested revision{" "}
                                        <code>{entry.revision}</code>.{" "}
                                        {entry.tags.length} normalized tags;{" "}
                                        {entry.declared_dependencies.length}{" "}
                                        declared dependencies.
                                    </p>
                                    <p>
                                        Current draft tags:{" "}
                                        {entry.tags.length === 0
                                            ? "none"
                                            : entry.tags.join(", ")}
                                    </p>
                                    <button
                                        type="button"
                                        disabled={!mayStart}
                                        onClick={() => {
                                            repository(entry);
                                        }}
                                    >
                                        Edit {entry.type} {entry.id}
                                    </button>
                                    <button
                                        type="button"
                                        disabled={!mayStart}
                                        onClick={() => {
                                            if (
                                                store.remove(
                                                    entry.type,
                                                    entry.id,
                                                )
                                            )
                                                close();
                                        }}
                                    >
                                        Remove {entry.type} {entry.id}
                                    </button>
                                </article>
                            )}
                        />
                        <h3>Reviewed draft changes</h3>
                        <p>
                            Review the exact editable intent before validation,
                            sizing preview and Apply. Hidden protected values
                            remain server-side.
                        </p>
                        <Page
                            key={
                                state.base.base_revision +
                                ":" +
                                String(state.prepared?.diff.length)
                            }
                            items={state.prepared?.diff ?? []}
                            name="changes"
                            render={(row, index) => (
                                <div key={index} className="configuration-diff">
                                    <h4>
                                        {row.kind === "setting"
                                            ? row.field
                                            : row.repositoryType +
                                              ":" +
                                              row.repositoryId}
                                    </h4>
                                    <p>Before</p>
                                    <pre>
                                        {JSON.stringify(row.before, null, 2)}
                                    </pre>
                                    <p>After</p>
                                    <pre>
                                        {JSON.stringify(row.after, null, 2)}
                                    </pre>
                                    {row.kind === "repository" &&
                                        row.after === null && (
                                            <p>
                                                Configuration removal only;
                                                archived bytes are retained.
                                            </p>
                                        )}
                                </div>
                            )}
                        />
                        <div className="configuration-toolbar">
                            <button
                                type="button"
                                disabled={!state.canValidate}
                                onClick={() => {
                                    request(() => store.validate());
                                }}
                            >
                                Validate draft
                            </button>
                            <button
                                type="button"
                                disabled={!state.canPreview}
                                onClick={() => {
                                    request(() => store.preview());
                                }}
                            >
                                Preview sizing
                            </button>
                            <button
                                type="button"
                                disabled={!state.canApply}
                                onClick={() => {
                                    request(() => store.apply());
                                }}
                            >
                                Apply reviewed changes
                            </button>
                        </div>
                        <Failure result={state.validation} />
                        {state.validation?.kind === "success" && (
                            <p>
                                Validated exact base{" "}
                                <code>
                                    {state.validation.payload.base_revision}
                                </code>
                                ; candidate revision{" "}
                                <code>
                                    {
                                        state.validation.payload
                                            .candidate_revision
                                    }
                                </code>
                                .{" "}
                                {
                                    state.validation.payload.required_selectors
                                        .length
                                }{" "}
                                repositories require sizing.
                            </p>
                        )}
                        <Observation
                            title="Original sizing preview"
                            observation={state.previewObservation}
                        />
                        {state.previewRecordId !== null && (
                            <p>
                                Saved preview record{" "}
                                <code>{state.previewRecordId}</code>. Observe
                                its original operation in Operations if
                                admission or results are uncertain.
                            </p>
                        )}
                        {state.assessment !== null && (
                            <div className="configuration-facts">
                                <p>
                                    Complete sizing assessment for base{" "}
                                    <code>
                                        {state.assessment.base_revision}
                                    </code>{" "}
                                    and candidate{" "}
                                    <code>
                                        {state.assessment.candidate_revision}
                                    </code>
                                    . Empty required scope still uses an
                                    original preview.
                                </p>
                                <Page
                                    items={state.assessment.required_selectors}
                                    name="required selectors"
                                    render={(selector) => (
                                        <p key={selector}>
                                            <code>{selector}</code>
                                        </p>
                                    )}
                                />
                                {state.assessment.sizing !== null && (
                                    <Page
                                        items={
                                            state.assessment.sizing.repositories
                                        }
                                        name="sizing rows"
                                        render={(row) => (
                                            <article
                                                key={
                                                    row.repository_type +
                                                    ":" +
                                                    row.repository_id
                                                }
                                                className="configuration-entry"
                                            >
                                                <h4>
                                                    {row.repository_type}:
                                                    <code>
                                                        {row.repository_id}
                                                    </code>
                                                </h4>
                                                <p>
                                                    Requested revision{" "}
                                                    <code>
                                                        {row.requested_revision}
                                                    </code>
                                                    ; resolved SHA{" "}
                                                    <code>
                                                        {row.resolved_commit_sha ??
                                                            "Unknown"}
                                                    </code>
                                                    . Upstream:{" "}
                                                    {row.upstream_state};
                                                    publication mode:{" "}
                                                    {row.publication_mode}.
                                                </p>
                                                <dl className="configuration-facts">
                                                    <dt>Files</dt>
                                                    <dd>
                                                        {row.file_count ??
                                                            "Unknown"}
                                                    </dd>
                                                    <dt>Logical bytes</dt>
                                                    <dd>
                                                        {row.logical_bytes ??
                                                            "Unknown"}
                                                    </dd>
                                                    <dt>Estimated new bytes</dt>
                                                    <dd>
                                                        {row.estimated_new_bytes ??
                                                            "Unknown"}
                                                    </dd>
                                                    <dt>
                                                        Projected publication
                                                        bytes
                                                    </dt>
                                                    <dd>
                                                        {row.projected_publication_bytes ??
                                                            "Unknown"}
                                                    </dd>
                                                </dl>
                                            </article>
                                        )}
                                    />
                                )}
                            </div>
                        )}
                        {state.comparison !== null && (
                            <div className="configuration-facts">
                                <h3>Observed installed comparison</h3>
                                <p>
                                    Original draft base{" "}
                                    <code>{state.base.base_revision}</code>;
                                    observed installed revision{" "}
                                    <code>
                                        {state.comparison.base_revision}
                                    </code>
                                    .{" "}
                                    {state.comparison.base_revision ===
                                    state.base.base_revision
                                        ? "The exact base is unchanged."
                                        : "The installed base changed. Reload explicitly, then re-edit and review; no automatic merge or overwrite occurred."}
                                </p>
                                <p>
                                    {
                                        state.comparison.editable.repositories
                                            .length
                                    }{" "}
                                    currently configured entries. A confirmed
                                    successful reload replaces this browser
                                    draft.
                                </p>
                            </div>
                        )}
                    </>
                )}
                <ApplicationEvidence
                    state={state}
                    onObserve={() => {
                        request(() => store.observeOutcome());
                    }}
                />
            </div>
        </div>
    );
}
