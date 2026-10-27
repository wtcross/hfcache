import { useEffect, useSyncExternalStore } from "react";
import type { ReactNode } from "react";
import type { AdministrationReadStore } from "../administration/administration-read-state";
import { warningGuidance } from "../administration/warnings";
import type { AdministrationDestination } from "../administration/warnings";
import { Panel } from "../primitives";
import type { QuerySnapshot } from "../state/query-state";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import type {
    EmptyPayload,
    EnvelopeProblem,
    VerificationHealthPayload,
} from "../wire/generated";
import { ReportCollection } from "./RunReport";

function ReadNotice<T>({
    name,
    page,
}: {
    name: string;
    page: QuerySnapshot<T, EmptyPayload>;
}) {
    if (page.phase === "ready") return null;
    if (page.phase === "stale")
        return (
            <p role="status">
                {name} is stale. Previously observed facts are shown while a
                fresh read is pending or required.
            </p>
        );
    const result = page.result;
    return (
        <p role={page.phase === "failed" ? "alert" : "status"}>
            {page.reason === "authentication"
                ? `Reconnect to read ${name.toLowerCase()}.`
                : page.reason === "capacity"
                  ? `${name} is unavailable because browser read capacity is full.`
                  : page.phase === "idle"
                    ? `${name} has not been read.`
                    : page.phase === "loading"
                      ? `Reading ${name.toLowerCase()}.`
                      : result?.kind === "api_problem"
                        ? `${name} was refused or unavailable. Diagnostic code: ${result.problem.code}.`
                        : result?.kind === "domain_failure"
                          ? `${name} returned a failed domain outcome; no successful facts were inferred.`
                          : result?.kind === "protocol_failure"
                            ? `${name} could not be validated.`
                            : `${name} is unavailable. No missing facts were treated as healthy or zero.`}
        </p>
    );
}
function Fact({ name, children }: { name: string; children: ReactNode }) {
    return (
        <div>
            <dt>{name}</dt>
            <dd>{children}</dd>
        </div>
    );
}
function Verification({ value }: { value: VerificationHealthPayload }) {
    const last = value.last_full_verification;
    return (
        <section aria-label="Verification health">
            <h3>Verification health</h3>
            <p>
                {value.degraded
                    ? "Verification is degraded."
                    : "No degraded verification state was reported."}{" "}
                Outstanding failures: {value.outstanding_failures}.
            </p>
            {last === null ? (
                <p>No full verification has been observed.</p>
            ) : (
                <dl>
                    <Fact name="Last full verification">{last.outcome}</Fact>
                    <Fact name="Completed">{last.completed_at}</Fact>
                    <Fact name="Verified unique bytes">
                        {last.unique_bytes}
                    </Fact>
                    <Fact name="Verified unique objects">
                        {last.unique_objects}
                    </Fact>
                    <Fact name="Verification report">
                        <code>{last.report}</code>
                    </Fact>
                </dl>
            )}
            <p>
                This is recorded verification history. Archive reachability and
                metadata coverage do not verify current file contents.
            </p>
        </section>
    );
}
function Warnings({
    values,
    name,
    identity,
    onNavigate,
}: {
    values: readonly EnvelopeProblem[];
    name: string;
    identity: string;
    onNavigate?: ((destination: AdministrationDestination) => void) | undefined;
}) {
    return (
        <ReportCollection
            values={values}
            name={name}
            identity={identity}
            render={(warning) => {
                const guidance = warningGuidance(warning.code);
                return (
                    <>
                        <p>
                            <code>{warning.code}</code>: {guidance.meaning}.
                        </p>
                        <p>{warning.message}</p>
                        {warning.repository !== null && (
                            <p>Repository: {warning.repository}</p>
                        )}
                        <p>{guidance.response}</p>
                        {onNavigate !== undefined &&
                            guidance.destination !== null && (
                                <button
                                    type="button"
                                    onClick={() => {
                                        if (guidance.destination !== null)
                                            onNavigate(guidance.destination);
                                    }}
                                >
                                    {guidance.actionLabel}
                                </button>
                            )}
                    </>
                );
            }}
        />
    );
}
function ReadDiagnostics<T>({
    name,
    page,
    onNavigate,
}: {
    name: string;
    page: QuerySnapshot<T, EmptyPayload>;
    onNavigate?: ((destination: AdministrationDestination) => void) | undefined;
}) {
    const result = page.result;
    if (result?.kind !== "success" && result?.kind !== "domain_failure")
        return null;
    const identity = page.key + ":" + String(page.generation);
    return (
        <>
            <Warnings
                values={result.response.envelope.warnings}
                name={name + " warnings"}
                identity={identity}
                onNavigate={onNavigate}
            />
            <ReportCollection
                values={result.response.envelope.errors}
                name={name + " errors"}
                identity={identity}
                render={(error) => (
                    <span>
                        <code>{error.code}</code>: {error.message}
                    </span>
                )}
            />
        </>
    );
}

export function AdministrationReadView({
    store,
    controller,
    session,
    onNavigate,
}: {
    store: AdministrationReadStore;
    controller: SessionController;
    session: SessionSnapshot;
    onNavigate?: ((destination: AdministrationDestination) => void) | undefined;
}) {
    const state = useSyncExternalStore(store.subscribe, store.snapshot);
    const hostQuery = controller.hostStatus;
    const host = useSyncExternalStore(hostQuery.subscribe, hostQuery.snapshot);
    useEffect(() => {
        store.setPageActive(true);
        return () => {
            store.setPageActive(false);
        };
    }, [store]);
    const status =
        state.status.result?.kind === "success"
            ? state.status.result.payload
            : null;
    const health =
        state.health.result?.kind === "success"
            ? state.health.result.payload
            : null;
    const version =
        state.version.result?.kind === "success"
            ? state.version.result.payload
            : null;
    const binding =
        host.result?.kind === "success" ? host.result.payload.binding : null;
    const ui = session.bootstrap.build.metadata;
    const reading = [state.status, state.health, state.version].some(
        (page) => page.phase === "loading",
    );
    return (
        <div className="administration-read-view">
            <Panel title="Archive health">
                <p>
                    These are independent read observations. Refreshing them
                    does not run diagnostics, verification or maintenance.
                </p>
                {!state.connected && (
                    <p role="status">
                        Reconnect to read current archive facts.
                    </p>
                )}
                <ReadNotice name="Archive status" page={state.status} />
                {status !== null && (
                    <>
                        <p>
                            Archive:{" "}
                            {status.archive.reachable
                                ? "Reachable"
                                : "Unreachable"}
                            .
                        </p>
                        <dl>
                            <Fact name="Archive identity">
                                <code>{status.archive.archive_id}</code>
                            </Fact>
                            <Fact name="Archive location">
                                <code>{status.archive.root}</code>
                            </Fact>
                            <Fact name="Available bytes">
                                {status.archive.reachable
                                    ? status.archive.available_bytes
                                    : "Unavailable"}
                            </Fact>
                            <Fact name="Configured reserve bytes">
                                {status.archive.reachable
                                    ? status.archive.reserve_bytes
                                    : "Unavailable"}
                            </Fact>
                            <Fact name="Headroom bytes">
                                {status.archive.reachable
                                    ? status.archive.headroom_bytes
                                    : "Unavailable"}
                            </Fact>
                            <Fact name="Total bytes">
                                {status.archive.reachable
                                    ? status.archive.total_bytes
                                    : "Unavailable"}
                            </Fact>
                        </dl>
                        {status.archive.reachable ? (
                            <>
                                <dl>
                                    <Fact name="Unfinished transactions">
                                        {status.archive.unfinished_transactions}
                                    </Fact>
                                    <Fact name="Deferred cleanup">
                                        {status.archive.deferred_cleanup}
                                    </Fact>
                                    <Fact name="Quarantined bytes">
                                        {status.archive.quarantined_bytes}
                                    </Fact>
                                </dl>
                                <ReportCollection
                                    name="archive area findings"
                                    identity={
                                        state.status.key +
                                        String(state.status.generation)
                                    }
                                    values={status.archive.findings}
                                    render={(finding) => (
                                        <span>
                                            {finding.area}:{" "}
                                            <code>{finding.path}</code>;
                                            transaction{" "}
                                            <code>
                                                {finding.transaction_id}
                                            </code>
                                            ;{" "}
                                            {finding.stale
                                                ? "stale"
                                                : "not stale"}
                                            ; age {finding.age_hours} hours.
                                        </span>
                                    )}
                                />
                                <ReportCollection
                                    name="unknown archive entries"
                                    identity={
                                        state.status.key +
                                        String(state.status.generation)
                                    }
                                    values={status.archive.unknown_entries}
                                    render={(entry) => <code>{entry}</code>}
                                />
                            </>
                        ) : (
                            <p>
                                Capacity and cleanup facts are unavailable.
                                Verification history below does not establish
                                present archive integrity.
                            </p>
                        )}
                        <Verification value={status.archive.verification} />
                    </>
                )}
                <ReadDiagnostics
                    name="Archive status"
                    page={state.status}
                    onNavigate={onNavigate}
                />
                <button
                    type="button"
                    disabled={!state.connected || reading}
                    onClick={() => {
                        void store.refresh();
                    }}
                >
                    Refresh administration status
                </button>
            </Panel>
            <Panel title="API readiness">
                <ReadNotice name="API health" page={state.health} />
                {health !== null && (
                    <>
                        <p>API daemon: Ready.</p>
                        <p>
                            Installed policy:{" "}
                            {health.policy_valid === true
                                ? "Valid"
                                : health.policy_valid === false
                                  ? "Invalid"
                                  : "Unknown"}
                            .
                        </p>
                        <p>
                            Archive inspection:{" "}
                            {health.archive === null
                                ? "Unavailable"
                                : health.archive.state}
                            .
                        </p>
                        <p>
                            Daemon readiness does not establish archive health
                            or permission to change it.
                        </p>
                    </>
                )}
                <ReadDiagnostics
                    name="API health"
                    page={state.health}
                    onNavigate={onNavigate}
                />
            </Panel>
            <Panel title="Software identities">
                <ReadNotice name="API version" page={state.version} />
                <dl className="administration-identities">
                    <Fact name="UI application version">
                        {ui.application_version}
                    </Fact>
                    <Fact name="UI source commit">
                        <code>{ui.source_commit}</code>
                        {ui.source_dirty ? " (modified source)" : ""}
                    </Fact>
                    <Fact name="UI source snapshot">
                        <code>{ui.source_snapshot_sha256}</code>
                    </Fact>
                    <Fact name="API instance">
                        <code>{session.bootstrap.instance_id}</code>
                    </Fact>
                    <Fact name="Configured archive identity">
                        <code>{session.bootstrap.configured_archive_id}</code>
                    </Fact>
                    <Fact name="API application version">
                        {version?.application ?? "Unavailable"}
                    </Fact>
                    <Fact name="API Python version">
                        {version?.python ?? "Unavailable"}
                    </Fact>
                    <Fact name="API Hugging Face library version">
                        {version?.huggingface_hub ?? "Unavailable"}
                    </Fact>
                    <Fact name="API transfer backend">
                        {version?.transfer_backend ?? "Unavailable"}
                    </Fact>
                    <Fact name="Installed host release">
                        {binding?.release_version ?? "Unavailable"}
                    </Fact>
                    {binding !== null && (
                        <>
                            <Fact name="Installed source commit">
                                <code>{binding.source_commit}</code>
                                {binding.source_dirty
                                    ? " (modified source)"
                                    : ""}
                            </Fact>
                            <Fact name="Installed source snapshot">
                                <code>{binding.source_snapshot_sha256}</code>
                            </Fact>
                            <Fact name="Installed deployment identity">
                                <code>{binding.deployment_sha256}</code>
                            </Fact>
                            <Fact name="Installed policy identity">
                                <code>{binding.policy_sha256}</code>
                            </Fact>
                        </>
                    )}
                </dl>
                {host.phase === "stale" && (
                    <p role="status">Installed host identities are stale.</p>
                )}
                {version !== null &&
                    (version.application !== ui.application_version ||
                        (binding !== null &&
                            binding.release_version !==
                                version.application)) && (
                        <p role="status">
                            Version observations differ. Check the intended API,
                            UI and host installation before changing
                            configuration or schedules.
                        </p>
                    )}
                <p>
                    These identities describe separately observed software.
                    Matching versions do not prove archive health or a completed
                    rollout.
                </p>
                <ReadDiagnostics
                    name="API version"
                    page={state.version}
                    onNavigate={onNavigate}
                />
            </Panel>
        </div>
    );
}
