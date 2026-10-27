import { useEffect, useId, useState, useSyncExternalStore } from "react";
import type { JobsStore } from "../operations/jobs-state";
import type { SessionSnapshot } from "../state/session-controller";
import { decodeDiagnosticsPayload } from "../wire/generated";
import type { DiagnosticCheckPayload } from "../wire/generated";
import { Panel } from "../primitives";
import { OperationResult } from "./OperationResult";
import { ReportCollection } from "./RunReport";

function display(value: string, limit: number): string {
    return value.length <= limit
        ? value
        : value.slice(0, limit) + "… (display truncated)";
}

/** Explicit existing jobs; mounting or choosing an option never submits work. */
export function AdministrationDiagnostics({
    store,
    session,
}: {
    store: JobsStore;
    session: SessionSnapshot;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const [probesReviewed, setProbesReviewed] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const id = useId();
    useEffect(
        () => () => {
            store.pause();
        },
        [store],
    );
    const connected = session.connection === "connected";
    const available = (capability: "read" | "write") =>
        connected &&
        session.canSubmit &&
        state.pending === null &&
        session.bootstrap.user.rest_capabilities.includes(capability);
    function submit(readOnly: boolean) {
        if (!available(readOnly ? "read" : "write")) return;
        if (!readOnly && !probesReviewed) return;
        setProbesReviewed(false);
        setMessage(null);
        if (store.setForm({ kind: "diagnostics", readOnly }))
            void store.submit();
        else
            setMessage(
                "Diagnostics were not submitted. The shared job input or current authority is unavailable; preserve original handles.",
            );
    }
    const diagnostic =
        state.lastAction === "readOnlyDiagnostics" ||
        state.lastAction === "probeDiagnostics";
    const observation = diagnostic ? state.observation : null;
    const result = observation?.result ?? null;
    let checks: readonly DiagnosticCheckPayload[] | null = null;
    if (
        observation?.receipt?.route === "/api/v1/diagnostics" &&
        (result?.kind === "success" || result?.kind === "domain_failure")
    ) {
        try {
            checks = decodeDiagnosticsPayload(result.payload).checks;
        } catch {
            // A failed command may have no partial checks. Never invent them.
        }
    }
    return (
        <Panel title="Diagnostics">
            <p>
                Run one explicit diagnostic job against the installed
                configuration. Both modes may contact Hugging Face and create an
                original operation receipt. Opening or refreshing Administration
                does not run diagnostics.
            </p>
            <div className="administration-diagnostic-actions">
                <div>
                    <h3>Read-only checks</h3>
                    <p>
                        Skip archive write probes and the archive lock. A
                        successful job describes these checks; it does not
                        establish snapshot integrity or current writable
                        storage.
                    </p>
                    <button
                        type="button"
                        disabled={!available("read")}
                        onClick={() => {
                            submit(true);
                        }}
                    >
                        Run read-only diagnostics
                    </button>
                </div>
                <div>
                    <h3>Temporary archive probes</h3>
                    <p>
                        Contact Hugging Face and perform temporary archive
                        health probes under the existing archive lock. Server
                        policy, guard and storage checks remain authoritative;
                        this does not synchronize repositories.
                    </p>
                    <label htmlFor={id + "-probes"}>
                        <input
                            id={id + "-probes"}
                            type="checkbox"
                            checked={probesReviewed}
                            disabled={!available("write")}
                            onChange={(event) => {
                                setProbesReviewed(event.currentTarget.checked);
                            }}
                        />
                        I understand these probes can write temporary archive
                        data.
                    </label>
                    <button
                        type="button"
                        disabled={!available("write") || !probesReviewed}
                        onClick={() => {
                            submit(false);
                        }}
                    >
                        Run temporary archive probes
                    </button>
                </div>
            </div>
            {!session.canSubmit && (
                <p role="status">
                    New jobs require current authority and resolved original
                    outcomes. Use Original operation recovery; no job is
                    retried.
                </p>
            )}
            {message !== null && <p role="alert">{message}</p>}
            {diagnostic && state.lastRecordId !== null && (
                <section aria-label="Original diagnostic job">
                    <p>
                        Original diagnostic recovery record:{" "}
                        <code>{state.lastRecordId}</code>. Connection loss and
                        stopping browser observation do not cancel accepted
                        work.
                    </p>
                    {state.submission?.kind === "accepted" && (
                        <p>HTTP 202 acknowledges admission, not completion.</p>
                    )}
                    {state.submission?.kind === "api_problem" && (
                        <p role="alert">
                            Diagnostic admission refused: HTTP{" "}
                            {state.submission.status},{" "}
                            {state.submission.problem.code}. No alternate
                            request was sent.
                        </p>
                    )}
                    {state.submission?.kind === "uncertain" && (
                        <p role="alert">
                            Admission is uncertain. Observe this original
                            recovery record; do not submit again to discover its
                            outcome.
                        </p>
                    )}
                    {checks !== null && (
                        <section aria-label="Diagnostic checks">
                            <h3>Diagnostic checks</h3>
                            <p>
                                Skipped checks are not passes. Failed or partial
                                command outcomes remain visible below.
                            </p>
                            <ReportCollection
                                values={checks}
                                name="diagnostic checks"
                                identity={state.lastRecordId}
                                render={(check) => (
                                    <dl>
                                        <dt>{display(check.name, 256)}</dt>
                                        <dd>
                                            <strong>{check.outcome}</strong>:{" "}
                                            {display(check.detail, 4096)}
                                        </dd>
                                    </dl>
                                )}
                            />
                        </section>
                    )}
                    <OperationResult
                        result={result}
                        {...(observation?.receipt == null
                            ? {}
                            : { operation: observation.receipt })}
                    />
                </section>
            )}
        </Panel>
    );
}
