import { useId, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import { Notice, Panel } from "../primitives";
import { refusalExplanation } from "../state/operation-registry";
import type { RecoveryRecord } from "../state/operation-registry";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import type { ConfigurationStore } from "../configuration/configuration-state";
import type { RepairFindingIntent } from "../operations/maintenance-state";
import { OperationResult } from "./OperationResult";
import { HostActionRecovery } from "./HostActionRecovery";

function ConfigurationRecovery({
    store,
    record,
}: {
    store: ConfigurationStore;
    record: RecoveryRecord;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const outcome =
        state.outcomeRecordId === record.recordId ? state.outcome : null;
    return (
        <section aria-label="Original configuration outcome">
            <button
                type="button"
                disabled={!state.canRead || state.pending !== null}
                onClick={() => {
                    void store.observeOutcome(record.recordId);
                }}
            >
                Observe original configuration outcome
            </button>
            <p>
                This reads the original application key. Host confirmation is
                separate from the API receipt; no application is submitted.
            </p>
            {outcome !== null && (
                <>
                    <p>Outcome read classification: {outcome.result.kind}.</p>
                    {outcome.kind === "outcome" && (
                        <p>
                            Original API receipt state: {outcome.receipt.state}.
                        </p>
                    )}
                    {outcome.kind === "outcome" &&
                        outcome.result.kind === "success" && (
                            <>
                                <dl className="recovery-facts">
                                    <dt>Protected host outcome</dt>
                                    <dd>{outcome.result.payload.state}</dd>
                                    <dt>Pending protected work</dt>
                                    <dd>
                                        {outcome.result.payload.pending
                                            ? "Yes"
                                            : "No"}
                                    </dd>
                                    <dt>Original application ID</dt>
                                    <dd>
                                        <code>
                                            {
                                                outcome.result.payload
                                                    .operation_id
                                            }
                                        </code>
                                    </dd>
                                </dl>
                                <p>
                                    {!outcome.result.payload.pending &&
                                    outcome.result.payload.state === "confirmed"
                                        ? "Installed configuration confirmed. The original API receipt is unchanged."
                                        : !outcome.result.payload.pending &&
                                            outcome.result.payload.state ===
                                                "unchanged"
                                          ? "The application is known unchanged; installation of the requested edit is not confirmed."
                                          : "Protected effects remain unresolved. Preserve original handles and evidence; do not repeat Apply."}
                                </p>
                            </>
                        )}
                </>
            )}
            {state.outcomeRecordId === record.recordId &&
                state.notice !== null && <p role="status">{state.notice}</p>}
        </section>
    );
}

function RecoveryEntry({
    record,
    controller,
    configuration,
    onReadReport,
    onRepairFinding,
}: {
    readonly record: RecoveryRecord;
    readonly controller: SessionController;
    readonly configuration: ConfigurationStore | undefined;
    readonly onReadReport: ((runId: string) => void) | undefined;
    readonly onRepairFinding:
        ((intent: RepairFindingIntent) => void) | undefined;
}) {
    const observation = useSyncExternalStore(
        (listener) => controller.observer.subscribe(record.recordId, listener),
        () => controller.observer.snapshot(record.recordId),
    );
    const [message, setMessage] = useState<string | null>(null);
    const [reviewing, setReviewing] = useState(false);
    const [pending, setPending] = useState(false);
    const handles = JSON.stringify(
        {
            recordId: record.recordId,
            handles: record.handles,
            originalAuthority: record.originalAuthority,
            route: record.route,
        },
        null,
        2,
    );
    async function copy() {
        try {
            await navigator.clipboard.writeText(handles);
            setMessage("Recovery handles copied.");
        } catch {
            setMessage(
                "Copy is unavailable. Select and copy the recovery handles below.",
            );
        }
    }
    function observe() {
        try {
            controller.observe(record.recordId);
            setMessage(null);
        } catch {
            setMessage(
                "Observation is unavailable for this authority or handle. Preserve the original handles and check the reconnect guide.",
            );
        }
    }
    return (
        <article
            className="recovery-entry"
            aria-label={`Recovery record ${record.recordId}`}
        >
            <h3>
                {record.action === "catalogRefresh"
                    ? "Refresh metadata"
                    : record.action === "sync"
                      ? "Sync"
                      : (record.action?.replace(/([A-Z])/gu, " $1") ??
                        "Imported original request")}
            </h3>
            <p role="status">
                {record.state === "not_admitted"
                    ? [
                          "/api/v1/config/applications",
                          "/api/v1/host/sync-schedule/changes",
                          "/api/v1/host/sync-observer/stops",
                      ].includes(record.route ?? "")
                        ? "Not admitted. Independent protected effects still need their original outcome review."
                        : `Not admitted. This request was refused before admission. ${refusalExplanation(record.disposition?.reason ?? null)} Recheck job readiness before considering a distinct new job.`
                    : record.state === "retired_unknown"
                      ? [
                            "/api/v1/config/applications",
                            "/api/v1/host/sync-schedule/changes",
                            "/api/v1/host/sync-observer/stops",
                        ].includes(record.route ?? "")
                          ? "Historical outcome unknown; request retired. Independent protected effects still need their original outcome review."
                          : "Historical outcome unknown; request retired. You may start a new job."
                      : record.state === "conflict"
                        ? "Needs review. Original request evidence conflicts with retained admission. Preserve original handles and ask an operator to compare the original key and receipt; do not submit a replacement."
                        : record.state === "terminal"
                          ? record.terminal?.outcome === "failed"
                              ? "Failed. The original admitted job result is preserved."
                              : "Completed. The original job result is preserved."
                          : observation.receipt?.state === "running"
                            ? "Running. Follow the original job result."
                            : ["accepted", "observing"].includes(record.state)
                              ? "Submitted. Waiting for the original job result."
                              : "Needs review. The original request outcome is unknown; do not repeat it."}
            </p>
            <details>
                <summary>Advanced diagnostics and original handles</summary>
                <dl className="recovery-facts">
                    <dt>Recovery state</dt>
                    <dd>{record.state}</dd>
                    <dt>Original operation ID</dt>
                    <dd>
                        <code>
                            {record.handles.operationId ?? "Not yet recovered"}
                        </code>
                    </dd>
                    <dt>Original authority</dt>
                    <dd>
                        {record.originalAuthority.kind === "web"
                            ? `${record.originalAuthority.scope.origin}${record.originalAuthority.scope.publicPrefix} · ${record.originalAuthority.scope.subject}`
                            : record.originalAuthority.kind === "cockpit"
                              ? "Imported predecessor authority; key namespace remains separate"
                              : "Creator unknown; ID observation does not prove key ownership"}
                    </dd>
                    <dt>Saved locally</dt>
                    <dd>{new Date(record.createdAt).toISOString()}</dd>
                    <dt>Browser observation</dt>
                    <dd>
                        {observation.phase}
                        {observation.pauseReason === null
                            ? ""
                            : ` · ${observation.pauseReason.replaceAll("_", " ")}`}
                    </dd>
                    <dt>Last observed backend state</dt>
                    <dd>
                        {observation.receipt?.state ??
                            "Not observed in this authenticated session"}
                    </dd>
                    {observation.receipt !== null && (
                        <>
                            <dt>Server updated</dt>
                            <dd>{observation.receipt.updated_at}</dd>
                            <dt>Domain run ID</dt>
                            <dd>
                                <code>
                                    {observation.receipt.domain_run_id ??
                                        "Not assigned"}
                                </code>
                            </dd>
                        </>
                    )}
                </dl>
                {record.state !== "terminal" && (
                    <p className="recovery-unknown">
                        Outcome is unconfirmed for the API receipt until
                        authenticated original observation establishes it.
                        Protected host effects are shown separately when
                        available. Do not repeat the operation to recover a
                        missing response.
                    </p>
                )}
                {record.terminal !== null && (
                    <p>
                        Saved result: {record.terminal.command} ·{" "}
                        {record.terminal.outcome} · exit{" "}
                        {record.terminal.exitCode}.{" "}
                        {record.state === "terminal"
                            ? "Verified in this session."
                            : "Saved history requires current authenticated verification."}
                    </p>
                )}
            </details>
            <div className="recovery-actions">
                <button
                    type="button"
                    onClick={() => {
                        if (controller.canReviewOriginal(record.recordId)) {
                            setReviewing(true);
                            return;
                        }
                        if (record.handles.kind === "basic-key")
                            void controller.reconcileOriginal(record.recordId);
                        else observe();
                    }}
                    disabled={pending || observation.phase === "observing"}
                >
                    {controller.canReviewOriginal(record.recordId)
                        ? "Review original request"
                        : "Recheck original request"}
                </button>
                <details>
                    <summary>Observation and export controls</summary>
                    <button
                        type="button"
                        onClick={() => {
                            controller.stopObserving(record.recordId);
                        }}
                        disabled={observation.phase !== "observing"}
                    >
                        Stop observing in this browser
                    </button>
                    <button
                        type="button"
                        onClick={() => {
                            void copy();
                        }}
                    >
                        Copy recovery handles
                    </button>
                </details>
            </div>
            {reviewing && (
                <section aria-label="Review original request">
                    <p>
                        The historical outcome is unknown. Review asks the
                        server to verify that no original work or unresolved
                        protected effects remain and permanently retire this
                        original request. It cannot retry or cancel work.
                        Starting a distinct new job remains a separate decision.
                    </p>
                    <button
                        type="button"
                        disabled={
                            pending ||
                            !controller.canReviewOriginal(record.recordId)
                        }
                        onClick={() => {
                            setPending(true);
                            void controller
                                .reviewOriginal(record.recordId)
                                .catch(() => {
                                    setMessage(
                                        "Fresh review is unavailable. Recheck the original request before confirming.",
                                    );
                                })
                                .finally(() => {
                                    setPending(false);
                                    setReviewing(false);
                                });
                        }}
                    >
                        Confirm review and retire original request
                    </button>
                    <button
                        type="button"
                        disabled={pending}
                        onClick={() => {
                            setReviewing(false);
                        }}
                    >
                        Keep original request
                    </button>
                </section>
            )}
            {configuration !== undefined &&
                record.handles.kind === "basic-key" &&
                record.route === "/api/v1/config/applications" && (
                    <ConfigurationRecovery
                        store={configuration}
                        record={record}
                    />
                )}
            {record.handles.kind === "basic-key" &&
                (record.route === "/api/v1/host/sync-schedule/changes" ||
                    record.route === "/api/v1/host/sync-observer/stops") && (
                    <HostActionRecovery
                        controller={controller}
                        record={record}
                    />
                )}
            <details>
                <summary>Original recovery handles</summary>
                <pre className="recovery-handles">{handles}</pre>
            </details>
            {observation.events.gaps.length > 0 && (
                <p>
                    Event history has gaps. Missing events do not prove
                    completion.
                </p>
            )}
            {observation.events.omitted > 0 && (
                <p>
                    {observation.events.omitted} event rows were omitted by the
                    browser retention limit.
                </p>
            )}
            {observation.events.rows.length > 0 && (
                <details>
                    <summary>
                        Recent validated events (
                        {observation.events.rows.length})
                    </summary>
                    <pre>
                        {JSON.stringify(observation.events.rows, null, 2)}
                    </pre>
                </details>
            )}
            {observation.result !== null && (
                <details>
                    <summary>Validated original result</summary>
                    <OperationResult
                        result={observation.result}
                        {...(observation.receipt === null
                            ? {}
                            : { operation: observation.receipt })}
                        {...(onReadReport === undefined
                            ? {}
                            : { onReadReport })}
                        {...(onRepairFinding === undefined
                            ? {}
                            : { onRepairFinding })}
                    />
                </details>
            )}
            {message !== null && <p role="status">{message}</p>}
        </article>
    );
}

export function OperationRecovery({
    controller,
    session,
    configuration,
    onReadReport,
    onRepairFinding,
}: {
    readonly controller: SessionController;
    readonly session: SessionSnapshot;
    readonly configuration?: ConfigurationStore;
    readonly onReadReport?: (runId: string) => void;
    readonly onRepairFinding?: (intent: RepairFindingIntent) => void;
}) {
    const choiceId = useId();
    const [kind, setKind] = useState<"id" | "basic-key" | "legacy-key">("id");
    const [value, setValue] = useState("");
    const [legacyClass, setLegacyClass] = useState<
        "rest-reader" | "rest-writer"
    >("rest-writer");
    const [message, setMessage] = useState<{
        kind: "success" | "error";
        text: string;
    } | null>(null);
    function importHandle(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        try {
            if (kind === "id")
                controller.importHandle({ kind, operationId: value });
            else if (kind === "basic-key")
                controller.importHandle({
                    kind,
                    key: value,
                    originalScope: controller.originalScope(),
                });
            else
                controller.importHandle({
                    kind,
                    key: value,
                    credentialClass: legacyClass,
                });
            setValue("");
            setMessage({
                kind: "success",
                text: "Original handle saved. Choose Observe original operation to read its current evidence.",
            });
        } catch {
            setMessage({
                kind: "error",
                text: "The handle could not be saved. Check its exact value, current authority and recovery storage. No operation was submitted.",
            });
        }
    }
    return (
        <div className="recovery-workspace">
            <Notice>
                Connection loss and stopping browser observation do not cancel
                accepted work. Recover the original handle; a new submission
                cannot establish the old outcome.
            </Notice>
            <Panel title="Original operation recovery">
                <p>
                    Browser recovery storage:{" "}
                    <strong>{session.registry.storage}</strong>.{" "}
                    {session.canSubmit
                        ? "No unresolved record currently blocks this authority."
                        : "New submissions are blocked until the current authority and original outcomes are established."}
                </p>
                {session.registry.error !== null && (
                    <p role="alert">
                        {session.registry.error}. Preserve the original handles
                        shown below.
                    </p>
                )}
                {session.registry.records.length === 0 ? (
                    <p>
                        No saved operation handles. Import an original handle to
                        observe existing work.
                    </p>
                ) : (
                    session.registry.records.map((record) => (
                        <RecoveryEntry
                            key={record.recordId}
                            record={record}
                            controller={controller}
                            configuration={configuration}
                            onReadReport={onReadReport}
                            onRepairFinding={onRepairFinding}
                        />
                    ))
                )}
            </Panel>
            {controller.exportRecoveryMetadata() !== null && (
                <details>
                    <summary>Advanced recovery metadata export</summary>
                    <p>
                        Validated nonsecret saved metadata. This export supplies
                        no fresh outcome proof.
                    </p>
                    <pre className="recovery-handles">
                        {controller.exportRecoveryMetadata()}
                    </pre>
                </details>
            )}
            <Panel title="Import original handle">
                <form onSubmit={importHandle} className="recovery-import">
                    <fieldset className="recovery-choice-fieldset">
                        <legend>Handle type</legend>
                        <div className="recovery-choice-options">
                            <label>
                                <input
                                    type="radio"
                                    name={choiceId + "-handle-type"}
                                    value="id"
                                    checked={kind === "id"}
                                    onChange={() => {
                                        setKind("id");
                                    }}
                                />
                                Original operation ID
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name={choiceId + "-handle-type"}
                                    value="basic-key"
                                    checked={kind === "basic-key"}
                                    onChange={() => {
                                        setKind("basic-key");
                                    }}
                                />
                                Original key for this Basic user
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name={choiceId + "-handle-type"}
                                    value="legacy-key"
                                    checked={kind === "legacy-key"}
                                    onChange={() => {
                                        setKind("legacy-key");
                                    }}
                                />
                                Legacy bearer key reference
                            </label>
                        </div>
                    </fieldset>
                    <label>
                        Original handle
                        <input
                            required
                            maxLength={128}
                            autoComplete="off"
                            spellCheck={false}
                            value={value}
                            onChange={(event) => {
                                setValue(event.target.value);
                            }}
                        />
                    </label>
                    {kind === "legacy-key" && (
                        <fieldset className="recovery-choice-fieldset">
                            <legend>Original credential class</legend>
                            <div className="recovery-choice-options">
                                <label>
                                    <input
                                        type="radio"
                                        name={choiceId + "-credential-class"}
                                        value="rest-writer"
                                        checked={legacyClass === "rest-writer"}
                                        onChange={() => {
                                            setLegacyClass("rest-writer");
                                        }}
                                    />
                                    REST writer
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={choiceId + "-credential-class"}
                                        value="rest-reader"
                                        checked={legacyClass === "rest-reader"}
                                        onChange={() => {
                                            setLegacyClass("rest-reader");
                                        }}
                                    />
                                    REST reader
                                </label>
                            </div>
                        </fieldset>
                    )}
                    <p>
                        {kind === "id"
                            ? "An imported ID is observation-only; its original creator is unknown."
                            : kind === "basic-key"
                              ? "Use only a key originally submitted by this signed-in Basic user against this archive. An authenticated key lookup must establish its operation ID."
                              : "A legacy bearer key has a different namespace. Keep the original profile and use its original lookup; this Basic session cannot convert it."}
                    </p>
                    <button
                        type="submit"
                        disabled={session.connection !== "connected"}
                    >
                        Save original handle
                    </button>
                </form>
                {message !== null && (
                    <p role={message.kind === "error" ? "alert" : "status"}>
                        {message.text}
                    </p>
                )}
            </Panel>
        </div>
    );
}
