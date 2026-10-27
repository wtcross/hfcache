import { useId, useRef, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import { ChoiceControl } from "./ChoiceControl";
import {
    defaultJobForm,
    MAX_CANDIDATE_FILE_BYTES,
    MAX_JOB_REQUEST_BYTES,
} from "../operations/jobs-state";
import type {
    JobForm,
    JobIssue,
    JobKind,
    JobSubmissionIntent,
    JobsStore,
} from "../operations/jobs-state";

const options: readonly { value: JobKind; label: string }[] = [
    { value: "installedPlan", label: "Installed sizing" },
    { value: "sync", label: "Sync" },
    { value: "candidatePlan", label: "Candidate file sizing" },
    { value: "verification", label: "Verification" },
    { value: "diagnostics", label: "Diagnostics" },
    { value: "catalogRefresh", label: "Refresh offline metadata" },
];
const issues: Readonly<Record<JobIssue, string>> = {
    invalid:
        "The job fields do not match the supported request. Check exact selectors, run ID and revision scope.",
    bounds: "The input exceeds a supported file, selector or encoded request limit. The last admitted input is preserved.",
    scope: "Choose one explicit scope. Selected scope needs repository selectors; unused verification fields must be empty and refresh needs at least one metadata category.",
    candidate:
        "Choose a nonempty candidate TOML file for sizing. Its contents are never displayed or saved in browser storage.",
    utf8: "The candidate file is not strict UTF-8. No request was submitted and the previous admitted file is preserved.",
    capacity:
        "Shared browser capacity is unavailable. The previous admitted input and original operation handles are preserved.",
    unavailable:
        "This action is unavailable. Observe original work or restore the connection; no request was retried.",
};
const actionLabels: Readonly<Record<JobSubmissionIntent["action"], string>> = {
    sync: "Sync",
    installedPlan: "Installed sizing",
    candidatePlan: "Candidate file sizing",
    readOnlyDiagnostics: "Read-only diagnostics",
    probeDiagnostics: "Temporary archive probes",
    newVerification: "New publications verification",
    fullVerification: "All retained publications verification",
    revisionVerification: "Exact revision verification",
    catalogRefresh: "Refresh offline metadata",
};
function number(value: number) {
    return value.toLocaleString("en-US");
}

export function JobForms({
    store,
    onOpenConfiguration,
}: {
    store: JobsStore;
    onOpenConfiguration?: () => void;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const id = useId(),
        input = useRef<HTMLInputElement>(null);
    const form = state.form,
        busy = state.pending !== null;
    function change(next: JobForm) {
        store.setForm(next);
    }
    function request(event: FormEvent) {
        event.preventDefault();
        void store.submit();
    }
    function scope(value: "all" | "selected") {
        if ("scope" in form)
            change({
                ...form,
                scope: value,
                selectors: value === "all" ? "" : form.selectors,
            });
    }
    const result = state.submission,
        observed = state.observation;
    const estimate = state.estimate?.result;
    return (
        <section className="panel job-forms" aria-label="Jobs">
            <header className="panel-heading">
                <h2>Jobs</h2>
            </header>
            <div className="panel-body">
                <p>
                    Submit one explicit server job. Leaving this view or
                    stopping observation does not cancel accepted work. Original
                    handles remain in Operations; no POST is retried.
                </p>
                <form
                    className="job-form"
                    aria-label="Job request"
                    onSubmit={request}
                    key={state.authGeneration}
                >
                    <ChoiceControl
                        label="Job"
                        value={form.kind}
                        options={options}
                        disabled={busy}
                        onChange={(kind) => {
                            change(defaultJobForm(kind));
                        }}
                    />
                    {"scope" in form && (
                        <>
                            <fieldset disabled={busy}>
                                <legend>Repository scope</legend>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-scope"}
                                        checked={form.scope === "all"}
                                        onChange={() => {
                                            scope("all");
                                        }}
                                    />
                                    {form.kind === "candidatePlan"
                                        ? "All candidate repositories"
                                        : form.kind === "catalogRefresh"
                                          ? "All configured and archived repositories"
                                          : "All configured repositories"}
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-scope"}
                                        checked={form.scope === "selected"}
                                        onChange={() => {
                                            scope("selected");
                                        }}
                                    />
                                    Selected repositories
                                </label>
                            </fieldset>
                            <label htmlFor={id + "-selectors"}>
                                Repository selectors (one per line)
                            </label>
                            <textarea
                                id={id + "-selectors"}
                                rows={4}
                                value={form.selectors}
                                disabled={busy || form.scope !== "selected"}
                                maxLength={25800}
                                onChange={(event) => {
                                    change({
                                        ...form,
                                        selectors: event.currentTarget.value,
                                    });
                                }}
                            />
                            <p>
                                At most 100 explicit selectors, each at most 256
                                characters, such as{" "}
                                <code>model:owned/example</code> or{" "}
                                <code>dataset:owned/example</code>. Full scope
                                is resolved by the server from{" "}
                                {form.kind === "candidatePlan"
                                    ? "the candidate configuration"
                                    : form.kind === "catalogRefresh"
                                      ? "configured and archived repositories"
                                      : "the installed policy"}
                                ; the browser performs no hidden repository
                                walk.
                            </p>
                        </>
                    )}
                    {form.kind === "candidatePlan" && (
                        <div className="job-file">
                            <label htmlFor={id + "-candidate"}>
                                Candidate TOML file for sizing
                            </label>
                            <input
                                ref={input}
                                id={id + "-candidate"}
                                type="file"
                                disabled={busy}
                                onChange={(event) => {
                                    const element = event.currentTarget,
                                        file = element.files?.[0];
                                    if (file === undefined) return;
                                    void store
                                        .selectCandidate(file)
                                        .finally(() => {
                                            element.value = "";
                                        });
                                }}
                            />
                            <p>
                                The file stays in RAM for sizing only. Its
                                contents are not rendered, edited, installed,
                                exported or stored in localStorage. Valid TOML
                                can still be incompatible with the installed
                                archive or Hub authority.
                            </p>
                            <p>
                                Limits: {number(MAX_CANDIDATE_FILE_BYTES)} UTF-8
                                source bytes and {number(MAX_JOB_REQUEST_BYTES)}{" "}
                                encoded JSON request bytes. Escaping and
                                selectors count toward the request limit.
                            </p>
                            {state.candidateFile !== null && (
                                <p>
                                    Selected file:{" "}
                                    <code>{state.candidateFile.name}</code>;{" "}
                                    {number(state.candidateFile.bytes)} bytes.
                                </p>
                            )}
                            <button
                                type="button"
                                disabled={busy || state.candidateFile === null}
                                onClick={() => {
                                    store.clearCandidate();
                                    if (input.current !== null)
                                        input.current.value = "";
                                }}
                            >
                                Clear selected file
                            </button>
                        </div>
                    )}
                    {form.kind === "verification" && (
                        <>
                            <fieldset disabled={busy}>
                                <legend>Verification scope</legend>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-verify"}
                                        checked={form.mode === "new"}
                                        onChange={() => {
                                            change({
                                                ...form,
                                                mode: "new",
                                                revision: "",
                                            });
                                        }}
                                    />
                                    New publications
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-verify"}
                                        checked={form.mode === "full"}
                                        onChange={() => {
                                            change({
                                                ...form,
                                                mode: "full",
                                                revision: "",
                                                runId: "",
                                            });
                                        }}
                                    />
                                    All retained publications
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-verify"}
                                        checked={form.mode === "revision"}
                                        onChange={() => {
                                            change({
                                                ...form,
                                                mode: "revision",
                                                runId: "",
                                            });
                                        }}
                                    />
                                    Exact revision
                                </label>
                            </fieldset>
                            {form.mode === "new" && (
                                <>
                                    <label htmlFor={id + "-run"}>
                                        Original sync run ID (optional)
                                    </label>
                                    <input
                                        id={id + "-run"}
                                        value={form.runId}
                                        maxLength={32}
                                        disabled={busy}
                                        onChange={(event) => {
                                            change({
                                                ...form,
                                                runId: event.currentTarget
                                                    .value,
                                            });
                                        }}
                                    />
                                    <p>
                                        This is the 32-character domain run ID
                                        of an original sync, not a request or
                                        operation ID. Empty uses the server's
                                        existing new-publication selection.
                                    </p>
                                </>
                            )}
                            {form.mode === "revision" && (
                                <>
                                    <label htmlFor={id + "-revision"}>
                                        Exact revision (TYPE:namespace/name@SHA)
                                    </label>
                                    <input
                                        id={id + "-revision"}
                                        value={form.revision}
                                        maxLength={512}
                                        disabled={busy}
                                        onChange={(event) => {
                                            change({
                                                ...form,
                                                revision:
                                                    event.currentTarget.value,
                                            });
                                        }}
                                    />
                                    <p>
                                        Use <code>model:</code> or{" "}
                                        <code>dataset:</code> and the complete
                                        immutable 40-character commit SHA. This
                                        does not choose a filesystem path.
                                    </p>
                                </>
                            )}
                        </>
                    )}
                    {form.kind === "diagnostics" && (
                        <fieldset disabled={busy}>
                            <legend>Diagnostic effects</legend>
                            <label>
                                <input
                                    type="radio"
                                    name={id + "-doctor"}
                                    checked={form.readOnly}
                                    onChange={() => {
                                        change({ ...form, readOnly: true });
                                    }}
                                />
                                Read-only checks
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name={id + "-doctor"}
                                    checked={!form.readOnly}
                                    onChange={() => {
                                        change({ ...form, readOnly: false });
                                    }}
                                />
                                Temporary archive probes
                            </label>
                        </fieldset>
                    )}
                    {form.kind === "catalogRefresh" && (
                        <>
                            <fieldset disabled={busy}>
                                <legend>Metadata publication scope</legend>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-refresh"}
                                        checked={
                                            form.revisionScope === "current"
                                        }
                                        onChange={() => {
                                            change({
                                                ...form,
                                                revisionScope: "current",
                                            });
                                        }}
                                    />
                                    Current publications
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-refresh"}
                                        checked={
                                            form.revisionScope === "retained"
                                        }
                                        onChange={() => {
                                            change({
                                                ...form,
                                                revisionScope: "retained",
                                            });
                                        }}
                                    />
                                    Retained publications
                                </label>
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={form.tags}
                                        onChange={(event) => {
                                            change({
                                                ...form,
                                                tags: event.currentTarget
                                                    .checked,
                                            });
                                        }}
                                    />
                                    Refresh configured tags
                                </label>
                                <label>
                                    <input
                                        type="checkbox"
                                        checked={form.technical}
                                        onChange={(event) => {
                                            change({
                                                ...form,
                                                technical:
                                                    event.currentTarget.checked,
                                            });
                                        }}
                                    />
                                    Refresh technical metadata
                                </label>
                            </fieldset>
                        </>
                    )}
                    <div
                        className="job-effects"
                        aria-label="Selected job effects"
                    >
                        <p>{state.description.scope}</p>
                        <p>{state.description.effects}</p>
                        <p>
                            Required REST capability:{" "}
                            <strong>{state.description.capability}</strong>.
                            Current REST capability:{" "}
                            <strong>
                                {state.capabilityAvailable
                                    ? "available"
                                    : "unavailable"}
                            </strong>
                            .
                        </p>
                        <p>
                            Fresh server host-policy, scope, storage and lock
                            checks remain authoritative at admission and
                            execution. These explanations do not grant
                            permission or prove writable storage.
                        </p>
                    </div>
                    {state.issue !== null && (
                        <p role="alert">{issues[state.issue]}</p>
                    )}
                    {state.notice !== null && (
                        <p role="status">{state.notice}</p>
                    )}
                    <button type="submit" disabled={!state.canSubmit}>
                        Submit job
                    </button>
                    <button
                        type="button"
                        disabled={state.pending === "submission"}
                        onClick={() => {
                            store.reset();
                        }}
                    >
                        Clear local job input
                    </button>
                </form>
                <button
                    type="button"
                    disabled={onOpenConfiguration === undefined || busy}
                    onClick={onOpenConfiguration}
                >
                    Plan configuration draft
                </button>
                <p>
                    Managed configuration sizing is available in Configuration
                    and tags after an explicit installed read, edit and
                    validation. No candidate file is transferred to that editor.
                </p>
                {state.lastRecordId !== null && (
                    <section
                        className="job-result"
                        aria-label="Latest job admission"
                    >
                        <h3>Latest original job</h3>
                        <p>
                            Action:{" "}
                            {state.lastAction === null
                                ? "Not yet observed"
                                : actionLabels[state.lastAction]}
                            . Browser recovery record:{" "}
                            <code>{state.lastRecordId}</code>.
                        </p>
                        {result?.kind === "accepted" && (
                            <p>
                                202 admitted. Original operation ID:{" "}
                                <code>
                                    {result.acceptance.operation.operation_id}
                                </code>
                                . This is not domain completion.
                            </p>
                        )}
                        {result?.kind === "uncertain" && (
                            <p>
                                Admission is uncertain ({result.reason}). Keep
                                the original handle and use authenticated
                                observation; do not submit again to discover an
                                outcome.
                            </p>
                        )}
                        {result?.kind === "api_problem" && (
                            <p>
                                Admission refused: HTTP {result.status},{" "}
                                <code>{result.problem.code}</code>. No alternate
                                request was sent.
                            </p>
                        )}
                        {result?.kind === "refused" && (
                            <p>Not submitted: {result.reason}.</p>
                        )}
                        {observed !== null && (
                            <p>
                                Observation: {observed.phase}. Original backend
                                receipt state:{" "}
                                {observed.receipt?.state ?? "not yet observed"}.
                            </p>
                        )}
                        <p>
                            Use the original recovery record below for exact
                            events, classified results and reports. Missing or
                            interrupted history never proves nonexecution. There
                            is no executor cancellation control.
                        </p>
                    </section>
                )}
                <section
                    className="job-estimate"
                    aria-label="Verification estimate"
                >
                    <h3>Verification estimate</h3>
                    <p>
                        This GET neither hashes archive content nor submits a
                        job. It does not establish verification, writable
                        storage or a repair outcome.
                    </p>
                    <button
                        type="button"
                        disabled={!state.canEstimate}
                        onClick={() => {
                            void store.estimate();
                        }}
                    >
                        Read verification estimate
                    </button>
                    {state.estimate !== null && (
                        <p>
                            Estimate read: {state.estimate.phase}
                            {estimate === null || estimate === undefined
                                ? ""
                                : " / " + estimate.kind}
                            .
                        </p>
                    )}
                    {estimate?.kind === "success" && (
                        <dl className="job-identity">
                            <dt>Repositories</dt>
                            <dd>{number(estimate.payload.repositories)}</dd>
                            <dt>Revisions</dt>
                            <dd>{number(estimate.payload.revisions)}</dd>
                            <dt>Unique objects</dt>
                            <dd>{number(estimate.payload.unique_objects)}</dd>
                            <dt>Unique bytes</dt>
                            <dd>{number(estimate.payload.unique_bytes)}</dd>
                            <dt>Unreadable objects</dt>
                            <dd>
                                {number(estimate.payload.unreadable_objects)}
                            </dd>
                            <dt>Estimated seconds</dt>
                            <dd>
                                {estimate.payload.estimated_duration_seconds ===
                                null
                                    ? "Unknown"
                                    : number(
                                          estimate.payload
                                              .estimated_duration_seconds,
                                      )}
                            </dd>
                            <dt>Measured bytes per second</dt>
                            <dd>
                                {estimate.payload
                                    .measured_throughput_bytes_per_second ===
                                null
                                    ? "Unknown"
                                    : number(
                                          estimate.payload
                                              .measured_throughput_bytes_per_second,
                                      )}
                            </dd>
                            <dt>Storage maintenance</dt>
                            <dd>Undetectable; no safety inference.</dd>
                        </dl>
                    )}
                    {estimate?.kind === "api_problem" && (
                        <p>
                            Estimate unavailable: HTTP {estimate.status},{" "}
                            <code>{estimate.problem.code}</code>.
                        </p>
                    )}
                    {estimate !== null &&
                        estimate !== undefined &&
                        estimate.kind !== "success" &&
                        estimate.kind !== "api_problem" && (
                            <p>
                                Estimate is unavailable ({estimate.kind}); no
                                empty estimate was invented.
                            </p>
                        )}
                </section>
            </div>
        </section>
    );
}
