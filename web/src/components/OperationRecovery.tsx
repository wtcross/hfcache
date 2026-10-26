import { useId, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import { Notice, Panel } from "../primitives";
import type { RecoveryRecord } from "../state/operation-registry";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";

function RecoveryEntry({
    record,
    controller,
}: {
    readonly record: RecoveryRecord;
    readonly controller: SessionController;
}) {
    const observation = useSyncExternalStore(
        (listener) => controller.observer.subscribe(record.recordId, listener),
        () => controller.observer.snapshot(record.recordId),
    );
    const [message, setMessage] = useState<string | null>(null);
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
            <h3>{record.action ?? "Imported original handle"}</h3>
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
                          ? "Imported Cockpit authority; key namespace remains separate"
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
                    Outcome is unconfirmed until authenticated original
                    observation establishes it. Do not repeat the operation to
                    recover a missing response.
                </p>
            )}
            {record.terminal !== null && (
                <p>
                    Saved result: {record.terminal.command} ·{" "}
                    {record.terminal.outcome} · exit {record.terminal.exitCode}.{" "}
                    {record.state === "terminal"
                        ? "Verified in this session."
                        : "Saved history requires current authenticated verification."}
                </p>
            )}
            <div className="recovery-actions">
                <button
                    type="button"
                    onClick={observe}
                    disabled={observation.phase === "observing"}
                >
                    Observe original operation
                </button>
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
            </div>
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
                    <p>Read classification: {observation.result.kind}.</p>
                    {(observation.result.kind === "success" ||
                        observation.result.kind === "domain_failure") && (
                        <dl className="recovery-facts">
                            <dt>Request ID</dt>
                            <dd>
                                <code>
                                    {observation.result.response.request_id}
                                </code>
                            </dd>
                            <dt>Command</dt>
                            <dd>
                                {observation.result.response.envelope.command}
                            </dd>
                            <dt>Outcome</dt>
                            <dd>
                                {observation.result.response.envelope.outcome}
                            </dd>
                            <dt>Exit code</dt>
                            <dd>
                                {observation.result.response.envelope.exit_code}
                            </dd>
                            <dt>Domain run ID</dt>
                            <dd>
                                <code>
                                    {
                                        observation.result.response.envelope
                                            .run_id
                                    }
                                </code>
                            </dd>
                        </dl>
                    )}
                </details>
            )}
            {message !== null && <p role="status">{message}</p>}
        </article>
    );
}

export function OperationRecovery({
    controller,
    session,
}: {
    readonly controller: SessionController;
    readonly session: SessionSnapshot;
}) {
    const choiceId = useId();
    const [kind, setKind] = useState<"id" | "basic-key" | "legacy-key">("id");
    const [value, setValue] = useState("");
    const [legacyClass, setLegacyClass] = useState<
        "rest-reader" | "rest-writer"
    >("rest-writer");
    const [message, setMessage] = useState<string | null>(null);
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
            setMessage(
                "Original handle saved. Choose Observe original operation to read its current evidence.",
            );
        } catch {
            setMessage(
                "The handle could not be saved. Check its exact value, current authority and recovery storage. No operation was submitted.",
            );
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
                        />
                    ))
                )}
            </Panel>
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
                                Legacy Cockpit key reference
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
                              : "A Cockpit bearer key has a different namespace. Keep the original profile and use its original lookup; this Basic session cannot convert it."}
                    </p>
                    <button
                        type="submit"
                        disabled={session.connection !== "connected"}
                    >
                        Save original handle
                    </button>
                </form>
                {message !== null && <p role="status">{message}</p>}
            </Panel>
        </div>
    );
}
