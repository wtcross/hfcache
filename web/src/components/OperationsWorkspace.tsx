import { useEffect, useState, useSyncExternalStore } from "react";
import { Notice, Panel } from "../primitives";
import type { HistoryKind, HistoryStore } from "../operations/history-state";
import type { JobsStore } from "../operations/jobs-state";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import type { ConfigurationStore } from "../configuration/configuration-state";
import type { QuerySnapshot } from "../state/query-state";
import { JobForms } from "./JobForms";
import { OperationRecovery } from "./OperationRecovery";
import { OperationResult } from "./OperationResult";
import { RunReport } from "./RunReport";
import { SessionHostAdministration } from "./HostStatusPanel";

function payload<S, F>(page: QuerySnapshot<S, F>): S | null {
    return page.phase === "ready" && page.result?.kind === "success"
        ? page.result.payload
        : null;
}
function ReadStatus<S, F>({
    page,
    name,
}: {
    page: QuerySnapshot<S, F>;
    name: string;
}) {
    const result = page.result;
    return (
        <p role="status">
            {name}: {page.phase}.
            {result !== null &&
                result.kind !== "success" &&
                ` Read classification: ${result.kind}.`}
            {result?.kind === "api_problem" &&
                ` Diagnostic code: ${result.problem.code}.`}
            {page.reason === "capacity" &&
                " The private response budget is full; loaded evidence is bounded."}
            {result?.kind === "api_problem" &&
                (result.status === 404 || result.status === 410) &&
                " Missing or expired history does not prove that work never ran. Preserve original handles."}
        </p>
    );
}

export function OperationsWorkspace({
    controller,
    session,
    jobs,
    history,
    configuration,
    onOpenConfiguration,
}: {
    controller: SessionController;
    session: SessionSnapshot;
    jobs: JobsStore;
    history: HistoryStore;
    configuration?: ConfigurationStore;
    onOpenConfiguration?: () => void;
}) {
    const state = useSyncExternalStore(history.subscribe, history.snapshot);
    const [permissionEvidence, setPermissionEvidence] = useState(false);
    useEffect(
        () => () => {
            jobs.pause();
            history.pause();
        },
        [jobs, history],
    );
    const operations = payload(state.operations)?.operations;
    const runs = payload(state.runs)?.runs;
    const receipt = payload(state.operation)?.operation;
    const events = payload(state.events);
    const report = payload(state.report)?.report;
    function pagination(kind: HistoryKind) {
        const page = state.pagination[kind];
        const loading =
            state[kind].phase === "loading" || state[kind].phase === "stale";
        return (
            <div className="history-pagination">
                <p>
                    Page {page.pageIndex + 1} · {page.loadedExtent}{" "}
                    {kind === "runs" ? "run IDs" : "operation receipts"} in the
                    known loaded extent. This is not a complete audit.
                </p>
                <button
                    type="button"
                    disabled={!state.connected || loading || !page.canPrevious}
                    onClick={() => {
                        void history.previousPage(kind);
                    }}
                >
                    Previous {kind}
                </button>
                <button
                    type="button"
                    disabled={!state.connected || loading || !page.hasNext}
                    onClick={() => {
                        void history.nextPage(kind);
                    }}
                >
                    Next {kind}
                </button>
            </div>
        );
    }
    const readReport = (runId: string) => {
        void history.selectRun(runId);
    };
    return (
        <div className="operations-workspace">
            <Panel title="Job permissions">
                <p>
                    REST capability and protected host permissions are separate.
                    Read current host evidence to inspect archive and Hub
                    grants, denied reasons and guard state. A prior observation
                    cannot authorize a job; the server checks again at admission
                    and execution.
                </p>
                <button
                    type="button"
                    disabled={
                        session.connection !== "connected" ||
                        !session.bootstrap.user.admin_permissions.some(
                            (permission) =>
                                permission.capability === "host-read" &&
                                permission.effective,
                        )
                    }
                    onClick={() => {
                        setPermissionEvidence(true);
                        void controller.hostStatus.refresh();
                    }}
                >
                    Read job permission evidence
                </button>
                {permissionEvidence && (
                    <SessionHostAdministration controller={controller} />
                )}
            </Panel>
            <JobForms
                store={jobs}
                {...(onOpenConfiguration === undefined
                    ? {}
                    : { onOpenConfiguration })}
            />
            <OperationRecovery
                controller={controller}
                session={session}
                {...(configuration === undefined ? {} : { configuration })}
                onReadReport={readReport}
            />
            <Panel title="Operation and run history">
                <p>
                    History reads never submit a job. An HTTP 202 acknowledges
                    admission; the recorded command result establishes its
                    outcome. Request IDs, operation IDs and domain run IDs
                    identify different things.
                </p>
                <button
                    type="button"
                    disabled={
                        !state.connected ||
                        state.operations.phase === "loading" ||
                        state.runs.phase === "loading"
                    }
                    onClick={() => {
                        void history.refresh();
                    }}
                >
                    Read history
                </button>
                {state.notice !== null && (
                    <Notice>
                        {state.notice === "stale_cursor"
                            ? "This history cursor expired. Read history explicitly to return to the first page; loaded history is not silently restarted."
                            : `History notice: ${state.notice}.`}
                    </Notice>
                )}
                <section aria-label="Operation history">
                    <h3>Operation receipts</h3>
                    {operations === undefined ? (
                        <ReadStatus
                            page={state.operations}
                            name="Operation history"
                        />
                    ) : (
                        <>
                            {operations.length === 0 && (
                                <p>No operations in this loaded page.</p>
                            )}
                            <ul className="history-list">
                                {operations.map((operation) => (
                                    <li key={operation.operation_id}>
                                        <code>{operation.operation_id}</code>{" "}
                                        <span>{operation.state}</span>{" "}
                                        <span>{operation.route}</span>
                                        <button
                                            type="button"
                                            disabled={!state.connected}
                                            onClick={() => {
                                                void history.selectOperation(
                                                    operation.operation_id,
                                                );
                                            }}
                                        >
                                            Inspect operation{" "}
                                            {operation.operation_id}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                    {pagination("operations")}
                </section>
                <section aria-label="Run history">
                    <h3>Archive run reports</h3>
                    {runs === undefined ? (
                        <ReadStatus page={state.runs} name="Run history" />
                    ) : (
                        <>
                            {runs.length === 0 && (
                                <p>No run IDs in this loaded page.</p>
                            )}
                            <ul className="history-list">
                                {runs.map((runId) => (
                                    <li key={runId}>
                                        <code>{runId}</code>
                                        <button
                                            type="button"
                                            disabled={!state.connected}
                                            onClick={() => {
                                                readReport(runId);
                                            }}
                                        >
                                            Read run report {runId}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </>
                    )}
                    {pagination("runs")}
                </section>
            </Panel>
            {state.selectedOperationId !== null && (
                <Panel title="Selected operation">
                    <p>
                        Read-only selection does not prove ownership of an
                        original submission key.
                    </p>
                    <button
                        type="button"
                        disabled={!state.connected}
                        onClick={() => {
                            void history.selectOperation(
                                state.selectedOperationId,
                            );
                        }}
                    >
                        Refresh selected operation
                    </button>
                    {receipt === undefined ? (
                        <ReadStatus
                            page={state.operation}
                            name="Selected operation"
                        />
                    ) : (
                        <>
                            <OperationResult
                                result={state.result.result}
                                operation={receipt}
                                onReadReport={readReport}
                            />
                            {receipt.state === "interrupted" && (
                                <Notice>
                                    Execution was interrupted or could not be
                                    reconciled. Preserve the original handles;
                                    do not resubmit to discover the outcome.
                                </Notice>
                            )}
                            {events === null ? (
                                <ReadStatus
                                    page={state.events}
                                    name="Event page"
                                />
                            ) : (
                                <section aria-label="Selected operation events">
                                    <h3>Validated event page</h3>
                                    <p>
                                        {state.loadedEvents} events loaded
                                        across {state.eventPages} bounded pages.
                                        Events are diagnostic evidence, separate
                                        from the original result.
                                    </p>
                                    {(events.truncated ||
                                        state.eventGaps.length > 0) && (
                                        <Notice>
                                            Event history has gaps or a dropped
                                            prefix. Missing events do not prove
                                            completion.
                                        </Notice>
                                    )}
                                    {state.eventGaps.map((gap) => (
                                        <p key={gap.from}>
                                            Missing event sequence {gap.from}–
                                            {gap.to}.
                                        </p>
                                    ))}
                                    <ol className="operation-events">
                                        {events.events.map((event) => (
                                            <li key={event.sequence}>
                                                <code>{event.sequence}</code>{" "}
                                                {event.message}
                                            </li>
                                        ))}
                                    </ol>
                                    <button
                                        type="button"
                                        disabled={
                                            !state.connected ||
                                            !state.hasNextEvents ||
                                            state.events.phase === "loading"
                                        }
                                        onClick={() => {
                                            void history.nextEventsPage();
                                        }}
                                    >
                                        Next events
                                    </button>
                                </section>
                            )}
                        </>
                    )}
                </Panel>
            )}
            {state.selectedRunId !== null && (
                <Panel title="Selected run report">
                    <p>
                        Domain run ID: <code>{state.selectedRunId}</code>.
                        Historical report policy may differ from the installed
                        policy.
                    </p>
                    {report === undefined ? (
                        <ReadStatus page={state.report} name="Run report" />
                    ) : (
                        <RunReport report={report} />
                    )}
                </Panel>
            )}
        </div>
    );
}
