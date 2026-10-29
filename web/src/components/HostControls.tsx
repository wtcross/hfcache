import { useEffect, useId, useSyncExternalStore } from "react";
import type { HostControlsStore } from "../administration/host-controls-state";
import {
    JOURNAL_PAGE_SIZE,
    MAX_JOURNAL_PAGES,
} from "../administration/host-controls-state";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import { Notice, Panel } from "../primitives";
import { OperationResult } from "./OperationResult";

/** Fixed host controls; mount and source selection never submit or replay work. */
export function HostControls({
    store,
    session,
}: {
    readonly store: HostControlsStore;
    readonly controller: SessionController;
    readonly session: SessionSnapshot;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const id = useId();
    useEffect(() => {
        store.setPageActive(true);
        return () => {
            store.setPageActive(false);
        };
    }, [store]);
    const host =
        state.host?.phase === "ready" && state.host.result?.kind === "success"
            ? state.host.result.payload
            : null;
    const observer =
        state.observer?.phase === "ready" &&
        state.observer.result?.kind === "success"
            ? state.observer.result.payload
            : null;
    const schedule = host?.facts?.sync_schedule;
    const validation =
        state.validation?.kind === "success" ? state.validation.payload : null;
    const journal =
        state.journal?.phase === "ready" &&
        state.journal.result?.kind === "success"
            ? state.journal.result.payload
            : null;
    const original =
        state.recordId === null
            ? null
            : session.registry.records.find(
                  (r) => r.recordId === state.recordId,
              );
    const effect =
        state.outcome?.kind === "outcome" &&
        state.outcome.result.kind === "success"
            ? state.outcome.result.payload
            : null;
    const applyLabel =
        state.scheduleReview?.action === "pause"
            ? "Pause sync timer"
            : state.scheduleReview?.action === "resume"
              ? "Resume sync timer"
              : state.scheduleReview?.action === "reset"
                ? "Reset to shipped schedule"
                : "Apply reviewed schedule";
    return (
        <div className="host-controls" role="group" aria-label="Host controls">
            <Panel title="Sync schedule">
                <p>
                    Basic authentication and protected host permissions are
                    separate. Reads are observations; the server checks current
                    authority again before any effect.
                </p>
                <button
                    type="button"
                    disabled={!state.canRead || state.pending !== null}
                    onClick={() => {
                        void store.readHost();
                    }}
                >
                    Read schedule and observer
                </button>
                {state.pending === "read" && (
                    <p role="status">Reading current host evidence.</p>
                )}
                {schedule?.state === "observed" ? (
                    <dl>
                        <dt>Current calendar</dt>
                        <dd>
                            <code>{schedule.on_calendar}</code>
                        </dd>
                        <dt>Current randomized delay</dt>
                        <dd>
                            {schedule.randomized_delay_sec ?? "Not specified"}
                        </dd>
                        <dt>Schedule source</dt>
                        <dd>
                            {schedule.source === "default"
                                ? "Shipped schedule"
                                : "Managed schedule"}
                        </dd>
                        <dt>Expected schedule revision</dt>
                        <dd>
                            <code>{schedule.revision}</code>
                        </dd>
                    </dl>
                ) : (
                    <p>
                        Current schedule is unavailable. Read host evidence
                        before reviewing a change.
                    </p>
                )}
                <p>
                    Schedule permission:{" "}
                    {observer === null
                        ? "Not established"
                        : observer.permissions.schedule
                          ? "Granted"
                          : `Denied (${observer.permission_reasons.schedule})`}
                    .
                </p>
                <p>
                    Calendar and next-event text use the server/systemd timezone
                    interpretation. Include an explicit timezone such as UTC in
                    the expression when needed; these values are not converted
                    to browser time.
                </p>
                <button
                    type="button"
                    disabled={!state.canSchedule}
                    onClick={store.edit}
                >
                    Edit sync schedule
                </button>
                {state.editing && (
                    <form
                        aria-label="Sync schedule draft"
                        onSubmit={(event) => {
                            event.preventDefault();
                            void store.validate();
                        }}
                    >
                        <label htmlFor={id + "-calendar"}>
                            OnCalendar expression
                        </label>
                        <input
                            id={id + "-calendar"}
                            type="text"
                            maxLength={4096}
                            autoComplete="off"
                            spellCheck={false}
                            value={state.draft.calendar}
                            onChange={(e) => {
                                store.setDraft(
                                    "calendar",
                                    e.currentTarget.value,
                                );
                            }}
                        />
                        <label htmlFor={id + "-delay"}>
                            Randomized delay (optional)
                        </label>
                        <input
                            id={id + "-delay"}
                            type="text"
                            maxLength={256}
                            autoComplete="off"
                            spellCheck={false}
                            value={state.draft.delay}
                            onChange={(e) => {
                                store.setDraft("delay", e.currentTarget.value);
                            }}
                        />
                        <p>
                            One bounded printable line per field. Every edit
                            retires validation and confirmation.
                        </p>
                        <button type="submit" disabled={!state.canValidate}>
                            Validate schedule
                        </button>
                        <button type="button" onClick={store.discard}>
                            Discard schedule draft
                        </button>
                    </form>
                )}
                {state.pending === "validation" && (
                    <p role="status">Validating with server/systemd.</p>
                )}
                {validation && (
                    <section aria-label="Validated schedule">
                        <h3>Validated schedule</h3>
                        <dl>
                            <dt>Normalized calendar</dt>
                            <dd>
                                <code>{validation.normalized_on_calendar}</code>
                            </dd>
                            <dt>Normalized randomized delay</dt>
                            <dd>
                                {validation.normalized_randomized_delay_sec ??
                                    "Not specified"}
                            </dd>
                            <dt>Next event (server/systemd)</dt>
                            <dd>
                                {validation.next_elapse ??
                                    "No next-event description was returned."}
                            </dd>
                        </dl>
                        <p>
                            Validation does not install a schedule or reserve
                            permission for a later action.
                        </p>
                    </section>
                )}
                <div className="button-row">
                    <button
                        type="button"
                        disabled={!state.canSchedule || !validation}
                        onClick={() => {
                            store.reviewSchedule("replace");
                        }}
                    >
                        Review replacement
                    </button>
                    <button
                        type="button"
                        disabled={!state.canSchedule}
                        onClick={() => {
                            store.reviewSchedule("pause");
                        }}
                    >
                        Review pause
                    </button>
                    <button
                        type="button"
                        disabled={!state.canSchedule}
                        onClick={() => {
                            store.reviewSchedule("resume");
                        }}
                    >
                        Review resume
                    </button>
                    <button
                        type="button"
                        disabled={!state.canSchedule}
                        onClick={() => {
                            store.reviewSchedule("reset");
                        }}
                    >
                        Review reset
                    </button>
                </div>
                <p>
                    Pause stops only the sync timer. Accepted backend work
                    continues. Resume may trigger a Persistent catch-up run.
                    Replacement or reset restarts only a previously active timer
                    and leaves an inactive timer inactive. Enablement never
                    changes; reset restores the shipped schedule.
                </p>
                {state.scheduleReview && (
                    <section aria-label="Reviewed schedule change">
                        <h3>
                            Reviewed schedule change:{" "}
                            {state.scheduleReview.action}
                        </h3>
                        <dl>
                            <dt>Original expected revision</dt>
                            <dd>
                                <code>
                                    {
                                        state.scheduleReview.request
                                            .expected_revision
                                    }
                                </code>
                            </dd>
                            {state.scheduleReview.action === "replace" && (
                                <>
                                    <dt>Exact submitted calendar</dt>
                                    <dd>
                                        <code>
                                            {
                                                state.scheduleReview.request
                                                    .on_calendar
                                            }
                                        </code>
                                    </dd>
                                    <dt>Exact submitted delay</dt>
                                    <dd>
                                        {state.scheduleReview.request
                                            .randomized_delay_sec ??
                                            "Not specified"}
                                    </dd>
                                </>
                            )}
                        </dl>
                        <label>
                            <input
                                type="checkbox"
                                checked={state.scheduleConfirmed}
                                onChange={(e) => {
                                    store.confirmSchedule(
                                        e.currentTarget.checked,
                                    );
                                }}
                            />
                            Confirm reviewed schedule change
                        </label>
                        <button
                            type="button"
                            disabled={!state.canApply}
                            onClick={() => {
                                void store.applySchedule();
                            }}
                        >
                            {applyLabel}
                        </button>
                        <p>
                            This review is consumed once. Conflict, uncertainty
                            or permission refusal requires a new explicit read
                            and review.
                        </p>
                    </section>
                )}
            </Panel>
            <Panel title="Original sync observer">
                <p>
                    Stopping the original observer does not cancel its accepted
                    backend operation. Keep its original pending handle and
                    observe backend completion separately.
                </p>
                <p>
                    Observer state: {observer?.state ?? "Not established"}.{" "}
                    {observer?.reason ?? ""}
                </p>
                <p>
                    Observer-stop permission:{" "}
                    {observer === null
                        ? "Not established"
                        : observer.permissions.observer
                          ? "Granted"
                          : `Denied (${observer.permission_reasons.observer})`}
                    . Schedule authority is independent.
                </p>
                {observer?.expected && (
                    <dl>
                        <dt>Original boot ID</dt>
                        <dd>
                            <code>{observer.expected.boot_id}</code>
                        </dd>
                        <dt>Original invocation ID</dt>
                        <dd>
                            <code>{observer.expected.invocation_id}</code>
                        </dd>
                        <dt>Original MainPID</dt>
                        <dd>{observer.expected.main_pid}</dd>
                        <dt>Original start ticks</dt>
                        <dd>{observer.expected.start_ticks}</dd>
                    </dl>
                )}
                <button
                    type="button"
                    disabled={!state.canReviewObserver}
                    onClick={store.reviewObserver}
                >
                    Review original observer
                </button>
                {state.observerReview && (
                    <section aria-label="Reviewed original observer">
                        <h3>Reviewed original observer</h3>
                        <p>
                            Stop only invocation{" "}
                            <code>
                                {state.observerReview.expected.invocation_id}
                            </code>
                            , MainPID {state.observerReview.expected.main_pid},
                            start ticks{" "}
                            {state.observerReview.expected.start_ticks}, boot{" "}
                            <code>{state.observerReview.expected.boot_id}</code>
                            .
                        </p>
                        <label>
                            <input
                                type="checkbox"
                                checked={state.observerConfirmed}
                                onChange={(e) => {
                                    store.confirmObserver(
                                        e.currentTarget.checked,
                                    );
                                }}
                            />
                            Confirm original observer
                        </label>
                        <button
                            type="button"
                            disabled={!state.canStop}
                            onClick={() => {
                                void store.stopObserver();
                            }}
                        >
                            Stop original sync observer
                        </button>
                    </section>
                )}
            </Panel>
            <Panel title="Verification timer (read-only)">
                {host?.facts ? (
                    <dl>
                        <dt>Verification timer state</dt>
                        <dd>
                            {host.facts.units["hfcache-verify.timer"].active}
                        </dd>
                        <dt>Verification timer installation</dt>
                        <dd>
                            {host.facts.units["hfcache-verify.timer"].unit_file}
                        </dd>
                    </dl>
                ) : (
                    <p>Verification timer observation is unavailable.</p>
                )}
                <p>
                    This view never starts, stops, resets or changes the
                    verification timer.
                </p>
            </Panel>
            {state.recordId !== null && (
                <Panel title="Original host action">
                    <dl>
                        <dt>Original browser recovery handle</dt>
                        <dd>
                            <code>{state.recordId}</code>
                        </dd>
                        <dt>Recovery state</dt>
                        <dd>{original?.state ?? "Unavailable"}</dd>
                        <dt>API receipt state</dt>
                        <dd>
                            {state.operation?.receipt?.state ??
                                "Not yet observed"}
                        </dd>
                    </dl>
                    <button
                        type="button"
                        disabled={!state.canRead || state.pending !== null}
                        onClick={() => {
                            void store.observeOutcome();
                        }}
                    >
                        Observe original host outcome
                    </button>
                    {effect && (
                        <dl>
                            <dt>Protected host effect state</dt>
                            <dd>{effect.state}</dd>
                            <dt>Protected host pending</dt>
                            <dd>{String(effect.pending)}</dd>
                            {"file_state" in effect && (
                                <>
                                    <dt>Stored schedule file</dt>
                                    <dd>{effect.file_state}</dd>
                                    <dt>Manager acknowledgement</dt>
                                    <dd>{effect.manager_state}</dd>
                                </>
                            )}
                            {"stop_state" in effect && (
                                <>
                                    <dt>Original observer stop</dt>
                                    <dd>{effect.stop_state}</dd>
                                </>
                            )}
                        </dl>
                    )}
                    <p>
                        API receipt, protected effect outcome and current host
                        observations are separate evidence. An interrupted or
                        failed receipt alone never clears unknown host effects.
                    </p>
                    {state.operation && (
                        <OperationResult
                            {...(state.operation.receipt === null
                                ? {}
                                : { operation: state.operation.receipt })}
                            result={state.operation.result}
                        />
                    )}
                </Panel>
            )}
            <Panel title="Diagnostic journals">
                <p>
                    Escaped diagnostic log text, not operation results or a
                    complete audit. At most {JOURNAL_PAGE_SIZE} entries per page
                    and {MAX_JOURNAL_PAGES} explicit cursor positions in this
                    view.
                </p>
                <fieldset>
                    <legend>Journal source</legend>
                    <label>
                        <input
                            type="radio"
                            name={id + "-source"}
                            checked={state.journalSource === "sync-observer"}
                            onChange={() => {
                                store.setJournalSource("sync-observer");
                            }}
                        />
                        Sync observer
                    </label>
                    <label>
                        <input
                            type="radio"
                            name={id + "-source"}
                            checked={state.journalSource === "verify-observer"}
                            onChange={() => {
                                store.setJournalSource("verify-observer");
                            }}
                        />
                        Verification observer
                    </label>
                </fieldset>
                <p>Changing source performs no read. Read a page explicitly.</p>
                <button
                    type="button"
                    disabled={
                        !state.canRead || state.journal?.phase === "loading"
                    }
                    onClick={() => {
                        void store.readJournal();
                    }}
                >
                    Read diagnostic journal
                </button>
                {state.journal?.phase === "loading" && (
                    <p role="status">Reading diagnostic journal.</p>
                )}
                {journal && (
                    <section aria-label="Loaded diagnostic journal">
                        <p>
                            Loaded journal page {state.journalPage}; source{" "}
                            {journal.source}.
                        </p>
                        {journal.gap && (
                            <Notice>
                                Journal history has a gap. Earlier diagnostics
                                may be unavailable.
                            </Notice>
                        )}
                        {journal.truncated && (
                            <Notice>
                                Journal output was truncated. This page omits
                                diagnostics.
                            </Notice>
                        )}
                        <ol>
                            {journal.entries.map((entry, index) => (
                                <li key={index}>
                                    <span>
                                        {entry.at ?? "Time unavailable"}
                                    </span>{" "}
                                    <code>{entry.message}</code>
                                </li>
                            ))}
                        </ol>
                        {journal.entries.length === 0 && (
                            <p>
                                No diagnostic entries were returned in this
                                bounded page.
                            </p>
                        )}
                    </section>
                )}
                {state.journal &&
                    state.journal.phase !== "loading" &&
                    state.journal.result?.kind !== "success" && (
                        <p role="alert">
                            Journal unavailable or cursor expired. Read the
                            first page explicitly; no operation outcome was
                            inferred.
                        </p>
                    )}
                <button
                    type="button"
                    disabled={!state.canPreviousJournal}
                    onClick={() => {
                        void store.previousJournal();
                    }}
                >
                    Previous journal page
                </button>
                <button
                    type="button"
                    disabled={!state.canNextJournal}
                    onClick={() => {
                        void store.nextJournal();
                    }}
                >
                    Next journal page
                </button>
            </Panel>
            {state.pending === "submit" && (
                <p role="status">Submitting one original host intent.</p>
            )}
            {state.pending === "outcome" && (
                <p role="status">Observing the original host outcome.</p>
            )}
            {state.notice && <Notice>{state.notice}</Notice>}
        </div>
    );
}
