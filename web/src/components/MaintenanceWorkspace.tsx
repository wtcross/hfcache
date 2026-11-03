import { useEffect, useId, useState, useSyncExternalStore } from "react";
import { Notice, Panel } from "../primitives";
import { defaultMaintenanceForm } from "../operations/maintenance-state";
import type {
    MaintenanceForm,
    MaintenanceIssue,
    MaintenanceStore,
    PairedReview,
    RepairFindingIntent,
} from "../operations/maintenance-state";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import type { OriginalResultRead } from "../state/operation-observation";
import type { ExactPublication } from "../api/identity";
import type { PruneSelection, RepairPayload } from "../wire/generated";
import { decodeRepairPayload } from "../wire/generated";
import { ChoiceControl } from "./ChoiceControl";
import { SessionHostAdministration } from "./HostStatusPanel";
import { OperationRecovery } from "./OperationRecovery";
import { OperationResult } from "./OperationResult";
import { ReportCollection } from "./RunReport";

const choices: readonly { value: MaintenanceForm["kind"]; label: string }[] = [
    { value: "prune", label: "Prune retained revisions" },
    { value: "purge", label: "Purge unmanaged repositories" },
    { value: "recovery", label: "Recover unfinished transactions" },
    { value: "quarantine", label: "Clean proven quarantine" },
    { value: "repair", label: "Repair from an integrity finding" },
];
const issues: Readonly<Record<MaintenanceIssue, string>> = {
    invalid:
        "The maintenance fields are invalid. Check the exact selectors, transaction IDs or repair finding. Confirmation has been retired.",
    bounds: "The input exceeds a supported bound. The last admitted input is preserved; confirmation has been retired.",
    scope: "Choose an explicit supported scope. Repository selectors name whole repositories; quarantine accepts transaction IDs, never paths.",
    capacity:
        "Shared browser capacity is unavailable. Preserve original handles; confirmation has been retired and no request is retried.",
    unavailable:
        "Maintenance is unavailable. Restore the connection or observe original work before making a new explicit intent.",
};
function Revision({ value }: { value: PruneSelection }) {
    return (
        <dl className="recovery-facts">
            <dt>Commit SHA</dt>
            <dd>
                <code>{value.commit_sha}</code>
            </dd>
            <dt>Publication ID</dt>
            <dd>
                <code>{value.publication_id}</code>
            </dd>
            <dt>Publication generation</dt>
            <dd>{value.publication_generation}</dd>
            <dt>Files / logical bytes</dt>
            <dd>
                {value.file_count} / {value.logical_bytes}
            </dd>
            <dt>Manifest evidence</dt>
            <dd>
                <code>{value.manifest}</code>
            </dd>
            <dt>Tree evidence</dt>
            <dd>
                <code>{value.tree}</code>
            </dd>
        </dl>
    );
}
function MaintenanceReview({
    review,
    identity,
}: {
    review: PairedReview;
    identity: string;
}) {
    switch (review.kind) {
        case "prune":
            return (
                <ReportCollection
                    values={review.payload.plans}
                    name="prune plans"
                    identity={identity}
                    render={(plan) => (
                        <article>
                            <h4>
                                {plan.repository_type}:{plan.repository_id}
                            </h4>
                            <p>
                                One eligible non-current revision is selected
                                for this round.
                            </p>
                            <p>
                                Protected current:{" "}
                                <code>{plan.current.commit_sha}</code>,
                                generation {plan.current.publication_generation}
                                .
                            </p>
                            <p>
                                Recorded policy reason:{" "}
                                <code>{plan.reason}</code>. This historical
                                reason name does not imply a fixed retention
                                limit of five.
                            </p>
                            <Revision value={plan.selected} />
                            <p>
                                Estimated unique bytes released:{" "}
                                {plan.unique_bytes_released_estimate}. Shared
                                content may remain.
                            </p>
                            <ReportCollection
                                values={plan.retained}
                                name="retained revision evidence"
                                identity={identity + plan.plan_id}
                                render={(row) => (
                                    <span>
                                        <code>{row.commit_sha}</code> ·
                                        generation {row.publication_generation}
                                    </span>
                                )}
                            />
                        </article>
                    )}
                />
            );
        case "purge":
            return (
                <ReportCollection
                    values={review.payload.plans}
                    name="purge plans"
                    identity={identity}
                    render={(plan) => (
                        <article>
                            <h4>
                                {plan.repository_type}:{plan.repository_id}
                            </h4>
                            <p>
                                Whole unmanaged repository removal includes its
                                current reference:{" "}
                                <code>{plan.current.commit_sha}</code>. Audit
                                evidence remains.
                            </p>
                            <p>
                                Reason: <code>{plan.reason}</code>. Estimated
                                unique bytes released:{" "}
                                {plan.unique_bytes_released_estimate}.
                            </p>
                            <ReportCollection
                                values={plan.revisions}
                                name="purge revision evidence"
                                identity={identity + plan.plan_id}
                                render={(row) => <Revision value={row} />}
                            />
                        </article>
                    )}
                />
            );
        case "recovery":
            return (
                <>
                    <p>
                        Actionable transactions: {review.payload.actionable}.
                        Blocked transactions: {review.payload.blocked}.
                    </p>
                    <ReportCollection
                        values={review.payload.plan}
                        name="recovery plans"
                        identity={identity}
                        render={(plan) => (
                            <article>
                                <h4>
                                    Transaction{" "}
                                    <code>{plan.transaction_id}</code>
                                </h4>
                                <dl className="recovery-facts">
                                    <dt>Operation</dt>
                                    <dd>{plan.operation}</dd>
                                    <dt>State</dt>
                                    <dd>{plan.state}</dd>
                                    <dt>Last checkpoint</dt>
                                    <dd>
                                        {plan.last_checkpoint ??
                                            "Not established"}
                                    </dd>
                                    <dt>Proposed remedy</dt>
                                    <dd>{plan.remedy}</dd>
                                    <dt>Reason</dt>
                                    <dd>{plan.reason}</dd>
                                </dl>
                            </article>
                        )}
                    />
                </>
            );
        case "quarantine":
            return (
                <ReportCollection
                    values={review.payload.plans}
                    name="quarantine plans"
                    identity={identity}
                    render={(plan) => (
                        <article>
                            <h4>
                                Transaction <code>{plan.transaction_id}</code>
                            </h4>
                            <p>
                                Repository: {plan.repository}. Recovery
                                transaction:{" "}
                                <code>{plan.recovery_transaction_id}</code>.
                            </p>
                            <p>
                                {plan.already_absent
                                    ? "Already absent; this named entry is a no-op."
                                    : "Proven redundant staging is eligible for cleanup."}{" "}
                                Logical bytes: {plan.logical_bytes}.
                            </p>
                            <p>
                                Quarantine evidence:{" "}
                                <code>{plan.quarantine_path}</code>. This is not
                                an editable path selector.
                            </p>
                            <ReportCollection
                                values={plan.files}
                                name="quarantine file proof"
                                identity={identity + plan.transaction_id}
                                render={(file) => (
                                    <dl className="recovery-facts">
                                        <dt>Path</dt>
                                        <dd>
                                            <code>{file.path}</code>
                                        </dd>
                                        <dt>Size</dt>
                                        <dd>{file.size}</dd>
                                        <dt>Expected SHA256</dt>
                                        <dd>
                                            <code>{file.sha256}</code>
                                        </dd>
                                        <dt>Retained replacement evidence</dt>
                                        <dd>
                                            <code>{file.retained_path}</code>
                                        </dd>
                                    </dl>
                                )}
                            />
                            <ReportCollection
                                values={plan.directories}
                                name="quarantine directory evidence"
                                identity={identity + plan.transaction_id}
                                render={(directory) => <code>{directory}</code>}
                            />
                        </article>
                    )}
                />
            );
    }
}
function RepairOutcome({
    result,
    reviewed,
    finding,
}: {
    result: OriginalResultRead | null;
    reviewed: ExactPublication | null;
    finding: RepairFindingIntent | null;
}) {
    if (result?.kind !== "success") return null;
    let value: RepairPayload;
    try {
        value = decodeRepairPayload(result.payload);
    } catch {
        return null;
    }
    return (
        <section aria-label="Actual repair identities">
            <h3>Actual repair identities</h3>
            <dl className="recovery-facts">
                <dt>Reviewed finding run</dt>
                <dd>
                    <code>
                        {finding?.source.runId ??
                            "Not retained in this browser"}
                    </code>
                </dd>
                <dt>Reviewed finding publication</dt>
                <dd>
                    <code>
                        {finding?.finding.publication_id ??
                            "Not retained in this browser"}
                    </code>
                </dd>
                <dt>Fresh publication reviewed for this repair</dt>
                <dd>
                    <code>
                        {reviewed?.publicationId ??
                            "Not retained in this browser"}
                    </code>
                </dd>
                <dt>Returned commit SHA</dt>
                <dd>
                    <code>{value.commit_sha}</code>
                </dd>
                <dt>Actual retired publication</dt>
                <dd>
                    <code>{value.retired_publication_id}</code>
                </dd>
                <dt>New verified publication</dt>
                <dd>
                    <code>{value.replacement_publication_id}</code>
                </dd>
                <dt>Grace expires</dt>
                <dd>{value.grace_expires_at}</dd>
                <dt>Repair transaction</dt>
                <dd>
                    <code>{value.transaction_id}</code>
                </dd>
                <dt>Retirement evidence</dt>
                <dd>
                    <code>{value.retirement_record}</code>
                </dd>
            </dl>
            {(reviewed === null ||
                reviewed.publicationId !== value.retired_publication_id ||
                reviewed.commitSha !== value.commit_sha) && (
                <Notice>
                    The server repaired a different retained instance from the
                    reviewed finding. Preserve this valid result and read fresh
                    exact verification evidence; do not claim the old finding
                    was repaired or repeat the request.
                </Notice>
            )}
            <p>
                The original manifest expectations and generation are preserved.
                The old locator remains for at least 168 hours; post-grace
                evidence is quarantined, without automatic deletion.
            </p>
        </section>
    );
}

export function MaintenanceWorkspace({
    store,
    controller,
    session,
    onReadReport,
}: {
    store: MaintenanceStore;
    controller: SessionController;
    session: SessionSnapshot;
    onReadReport?: (runId: string) => void;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    useEffect(() => {
        void store.recheckReadiness();
    }, [store, state.authGeneration]);
    const id = useId();
    const [permissionEvidence, setPermissionEvidence] = useState(false);
    useEffect(
        () => () => {
            store.pause();
        },
        [store],
    );
    const form = state.form,
        busy = state.pending !== null;
    const finding = state.finding,
        fresh = state.freshPublication;
    const preview = state.previewObservation,
        effect = state.effectObservation;
    return (
        <div className="maintenance-workspace">
            <Panel title="Maintenance permissions">
                <p>
                    Previews are keyed control-state jobs and require protected
                    host control permission. Archive effects require archive
                    permission. REST capability alone does not grant host
                    permission; the server checks current policy and locks
                    again.
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
                    Read maintenance permission evidence
                </button>
                {permissionEvidence && (
                    <SessionHostAdministration controller={controller} />
                )}
            </Panel>
            <Panel title="Guarded maintenance">
                <p>
                    Preview the current scope, review identities and effects,
                    then confirm one explicit action. A preview is evidence, not
                    deletion authority. Leaving this view never cancels accepted
                    work.
                </p>
                <form
                    className="maintenance-form"
                    aria-label="Maintenance request"
                    onSubmit={(event) => {
                        event.preventDefault();
                        if (form.kind === "repair") void store.checkRepair();
                        else void store.preview();
                    }}
                >
                    <ChoiceControl
                        label="Maintenance action"
                        value={form.kind}
                        options={choices}
                        disabled={busy}
                        onChange={(kind) => {
                            store.setForm(defaultMaintenanceForm(kind));
                        }}
                    />
                    {(form.kind === "prune" || form.kind === "purge") && (
                        <>
                            <fieldset disabled={busy}>
                                <legend>Repository scope</legend>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-scope"}
                                        checked={form.scope === "selected"}
                                        onChange={() => {
                                            store.setForm({
                                                ...form,
                                                scope: "selected",
                                            });
                                        }}
                                    />
                                    Selected whole repositories
                                </label>
                                <label>
                                    <input
                                        type="radio"
                                        name={id + "-scope"}
                                        checked={form.scope !== "selected"}
                                        onChange={() => {
                                            store.setForm({
                                                ...form,
                                                scope:
                                                    form.kind === "prune"
                                                        ? "all"
                                                        : "all_unmanaged",
                                                selectors: "",
                                            });
                                        }}
                                    />
                                    {form.kind === "prune"
                                        ? "All configured repositories"
                                        : "All currently unmanaged repositories"}
                                </label>
                            </fieldset>
                            <label htmlFor={id + "-selectors"}>
                                Repository selectors (one per line)
                            </label>
                            <textarea
                                id={id + "-selectors"}
                                rows={4}
                                maxLength={25800}
                                value={form.selectors}
                                disabled={busy || form.scope !== "selected"}
                                onChange={(event) => {
                                    store.setForm({
                                        ...form,
                                        selectors: event.currentTarget.value,
                                    });
                                }}
                            />
                            <p>
                                At most 100 whole selectors such as{" "}
                                <code>model:owned/example</code> or{" "}
                                <code>dataset:owned/example</code>. Revision
                                suffixes are refused.
                            </p>
                            {form.kind === "prune" ? (
                                <p>
                                    One round removes at most one eligible
                                    non-current revision per repository. Current
                                    is protected. Lowering retention or editing
                                    configuration alone deletes nothing; lower
                                    limits may require separately reviewed
                                    rounds. Over-retention is safer than
                                    unexplained deletion.
                                </p>
                            ) : (
                                <Notice>
                                    Whole unmanaged repository purge removes its
                                    retained revisions and current reference,
                                    preserving audit. Enabled and disabled
                                    configured repositories remain managed and
                                    ineligible. Removing configuration and
                                    purging are separate decisions.
                                    All-unmanaged scope is resolved afresh at
                                    Apply and may differ from this preview.
                                </Notice>
                            )}
                        </>
                    )}
                    {form.kind === "recovery" && (
                        <p>
                            The server derives unfinished transactions from its
                            journals. Recovery uses durable checkpoints and
                            current evidence. Unknown or ambiguous state is
                            preserved; a blocked plan cannot be applied here.
                            Review the recovery runbook before further work.
                        </p>
                    )}
                    {form.kind === "quarantine" && (
                        <>
                            <label htmlFor={id + "-transactions"}>
                                Quarantine transaction IDs (one per line)
                            </label>
                            <textarea
                                id={id + "-transactions"}
                                rows={4}
                                maxLength={3300}
                                value={form.transactionIds}
                                disabled={busy}
                                onChange={(event) => {
                                    store.setForm({
                                        ...form,
                                        transactionIds:
                                            event.currentTarget.value,
                                    });
                                }}
                            />
                            <p>
                                Choose 1–100 exact 32-character hexadecimal
                                transaction IDs. The server proves the complete
                                named batch is redundant staging with verified
                                retained replacement bytes. Repair evidence,
                                unexplained files and unfinished work remain
                                protected. There is no all-entry or path
                                selector.
                            </p>
                        </>
                    )}
                    {form.kind === "repair" && (
                        <>
                            {finding === null ? (
                                <Notice>
                                    Open an exact verification run report in
                                    Operations and choose Review repair from
                                    this finding. Repair is unavailable without
                                    an attributed finding; there is no blind
                                    revision input.
                                </Notice>
                            ) : (
                                <section aria-label="Original repair finding">
                                    <h3>Original repair finding</h3>
                                    <dl className="recovery-facts">
                                        <dt>Archive / verification run</dt>
                                        <dd>
                                            <code>
                                                {finding.source.archiveId}
                                            </code>{" "}
                                            /{" "}
                                            <code>{finding.source.runId}</code>
                                        </dd>
                                        <dt>Report completed</dt>
                                        <dd>{finding.source.completedAt}</dd>
                                        <dt>Repository</dt>
                                        <dd>
                                            {finding.finding.repository_type}:
                                            {finding.finding.repository_id}
                                        </dd>
                                        <dt>Commit SHA</dt>
                                        <dd>
                                            <code>
                                                {finding.finding.commit_sha}
                                            </code>
                                        </dd>
                                        <dt>Finding publication</dt>
                                        <dd>
                                            <code>
                                                {finding.finding.publication_id}
                                            </code>
                                        </dd>
                                        <dt>Finding / path</dt>
                                        <dd>
                                            {finding.finding.kind} /{" "}
                                            {finding.finding.path ??
                                                "Not attributed"}
                                        </dd>
                                        <dt>Expected</dt>
                                        <dd>
                                            {finding.finding.expected ??
                                                "Not available"}
                                        </dd>
                                        <dt>Observed</dt>
                                        <dd>
                                            {finding.finding.observed ??
                                                "Not available"}
                                        </dd>
                                    </dl>
                                </section>
                            )}
                            <label htmlFor={id + "-reason"}>
                                Repair reason
                            </label>
                            <textarea
                                id={id + "-reason"}
                                rows={3}
                                maxLength={2048}
                                value={form.reason}
                                disabled={busy}
                                onChange={(event) => {
                                    store.setForm({
                                        ...form,
                                        reason: event.currentTarget.value,
                                    });
                                }}
                            />
                            <p>
                                Repair downloads the whole immutable SHA into an
                                isolated cache and must reproduce the original
                                manifest expectations. It is not a file patch.
                                The server requires archive permission; Hub
                                access is independently enforced by installed
                                policy.
                            </p>
                            <button
                                type="submit"
                                disabled={!state.canCheckRepair}
                            >
                                Check repair evidence
                            </button>
                            <p role="status">
                                Repair evidence: {state.repairProof}.
                            </p>
                            {fresh !== null && (
                                <section aria-label="Fresh repair evidence">
                                    <h3>Fresh repair evidence</h3>
                                    <p>
                                        Retained{" "}
                                        <code>
                                            {fresh.repositoryType}:
                                            {fresh.repositoryId}@
                                            {fresh.commitSha}
                                        </code>
                                        ; publication{" "}
                                        <code>{fresh.publicationId}</code>,
                                        generation{" "}
                                        {state.freshPublicationGeneration}.
                                    </p>
                                    <Notice>
                                        This is a fresh observation, not an
                                        atomic publication precondition. The
                                        repair API sends the SHA and reason; the
                                        server rederives its retained instance
                                        under lock. Compare the actual retired
                                        and replacement publication IDs in the
                                        result.
                                    </Notice>
                                </section>
                            )}
                            {state.repairProof === "changed" && (
                                <Notice>
                                    The exact finding publication changed or
                                    vanished. Stop and obtain fresh exact
                                    findings; no current/latest fallback is
                                    used.
                                </Notice>
                            )}
                        </>
                    )}
                    {form.kind !== "repair" && (
                        <>
                            <p
                                id="maintenance-preview-availability"
                                role="status"
                            >
                                {state.previewAvailability}
                            </p>
                            <button
                                type="button"
                                disabled={state.readinessPhase === "checking"}
                                onClick={() => {
                                    void store.recheckReadiness();
                                }}
                            >
                                Recheck maintenance readiness
                            </button>
                            <button
                                type="submit"
                                aria-describedby="maintenance-preview-availability"
                                disabled={!state.canPreview}
                            >
                                Preview maintenance
                            </button>
                        </>
                    )}
                    <button
                        type="button"
                        disabled={busy}
                        onClick={() => {
                            store.reset();
                        }}
                    >
                        Clear maintenance input
                    </button>
                </form>
                {state.formIssue !== null && (
                    <Notice>{issues[state.formIssue]}</Notice>
                )}
                {state.notice !== null && <Notice>{state.notice}</Notice>}
                {state.review !== null && (
                    <section aria-label="Maintenance preview review">
                        <h3>Review current preview</h3>
                        <MaintenanceReview
                            review={state.review}
                            identity={String(state.reviewGeneration)}
                        />
                        <Notice>
                            Apply reconstructs current scope and evidence under
                            the original server locks. This preview does not
                            freeze its deletion list. Prune, purge and repair
                            may first reconcile known unfinished transactions;
                            quarantine refuses unfinished work.
                        </Notice>
                    </section>
                )}
                {form.kind !== "repair" &&
                    state.eligibility === "nothing_eligible" && (
                        <p role="status">
                            Nothing eligible. No Apply is available.
                        </p>
                    )}
                {form.kind !== "repair" && state.eligibility === "blocked" && (
                    <Notice>
                        Apply is blocked. Preserve unknown or refused evidence
                        and follow the recovery runbook; do not repeat work to
                        discover its outcome.
                    </Notice>
                )}
                <section aria-label="Explicit maintenance confirmation">
                    <p>
                        Confirmation applies once to the currently reviewed
                        scope and effects. Editing, navigation, connection
                        changes or an Apply attempt retires it. The backend
                        remains authoritative.
                    </p>
                    <button
                        type="button"
                        disabled={!state.canConfirm || state.confirmed}
                        onClick={() => {
                            store.confirm(state.reviewGeneration);
                        }}
                    >
                        {form.kind === "repair"
                            ? "Confirm reviewed repair"
                            : "Confirm reviewed maintenance"}
                    </button>
                    <button
                        type="button"
                        disabled={!state.confirmed}
                        onClick={() => {
                            store.clearConfirmation();
                        }}
                    >
                        Clear confirmation
                    </button>
                    <p role="status">
                        {state.confirmed
                            ? "Current review confirmed for one attempt."
                            : "Current review is not confirmed."}
                    </p>
                    <p id="maintenance-apply-availability" role="status">
                        {state.applyAvailability}
                    </p>
                    <button
                        type="button"
                        aria-describedby="maintenance-apply-availability"
                        disabled={
                            form.kind === "repair"
                                ? !state.canRepair
                                : !state.canApply
                        }
                        onClick={() => {
                            if (form.kind === "repair") void store.repair();
                            else void store.apply();
                        }}
                    >
                        {form.kind === "repair"
                            ? "Repair reviewed revision"
                            : "Apply maintenance"}
                    </button>
                </section>
            </Panel>
            {preview !== null && (
                <Panel title="Original preview operation">
                    <p>
                        Preview observation: {preview.phase}. Admission and
                        events alone cannot arm Apply.
                    </p>
                    <OperationResult
                        result={preview.result}
                        {...(preview.receipt === null
                            ? {}
                            : { operation: preview.receipt })}
                    />
                </Panel>
            )}
            {effect !== null && (
                <Panel title="Original maintenance operation">
                    <p>
                        Observation: {effect.phase}. Preserve the original key
                        and operation ID if the response is lost. No Apply or
                        repair is replayed.
                    </p>
                    <OperationResult
                        result={effect.result}
                        {...(effect.receipt === null
                            ? {}
                            : { operation: effect.receipt })}
                        {...(onReadReport === undefined
                            ? {}
                            : { onReadReport })}
                    />
                    {effect.receipt?.route === "/api/v1/repairs" && (
                        <RepairOutcome
                            result={effect.result}
                            reviewed={state.effectPublication}
                            finding={state.effectFinding}
                        />
                    )}
                </Panel>
            )}
            <OperationRecovery
                controller={controller}
                session={session}
                {...(onReadReport === undefined ? {} : { onReadReport })}
            />
        </div>
    );
}
