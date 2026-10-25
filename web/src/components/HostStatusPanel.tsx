import { useEffect, useMemo, useState } from "react";
import type { ApiClient } from "../api/client";
import { createApiClient } from "../api/client";
import type { ApiScope } from "../api/identity";
import type { ReadResult } from "../api/types";
import { Panel } from "../primitives";
import { bootstrapScope } from "../bootstrap";
import type {
    EmptyPayload,
    HostPermissionReasons,
    HostPermissions,
    HostStatus,
    UiBootstrap,
} from "../wire/generated";

const actions: readonly (keyof HostPermissions)[] = [
    "archive",
    "hub",
    "control",
    "schedule",
    "configuration",
    "observer",
];
const labels: Readonly<Record<keyof HostPermissions, string>> = {
    archive: "Archive changes",
    hub: "Hugging Face access",
    control: "Control operations",
    schedule: "Schedule changes",
    configuration: "Configuration changes",
    observer: "Stop observation",
};
const permissionReasons: Readonly<
    Record<HostPermissionReasons["archive"], string>
> = {
    granted: "Granted by the installed policy.",
    "policy-denied": "The installed policy denies this action.",
    "guard-held": "The archive guard blocks archive changes.",
    "profile-unproved":
        "This deployment profile has not established this authority.",
    "authority-unknown": "Current host authority could not be established.",
    "helper-unavailable": "The protected host helper is unavailable.",
};
const reasons: Readonly<Record<Exclude<HostStatus["reason"], null>, string>> = {
    "helper-disabled":
        "The protected host helper is disabled in this deployment.",
    "helper-unavailable": "The protected host helper is unavailable.",
    "helper-timeout":
        "The protected host helper did not complete within its time limit.",
    "helper-refused": "The protected host helper could not be authenticated.",
    "helper-busy": "The protected host helper is at capacity.",
    "policy-missing": "The independently installed host policy is missing.",
    "policy-invalid":
        "The independently installed host policy could not be validated.",
    "deployment-unverified": "The installed deployment could not be verified.",
    "facts-unavailable": "Current host facts could not be established.",
    "guard-unconfirmed": "The archive guard state could not be established.",
    "key-missing": "The protected configuration revision key is missing.",
    "key-invalid":
        "The protected configuration revision key could not be validated.",
    "config-unavailable": "The installed configuration could not be verified.",
};
type HostResult = ReadResult<HostStatus, EmptyPayload>;
type Observation =
    { readonly result: HostResult } | { readonly unavailable: true };

function failure(observation: Observation): string {
    if ("unavailable" in observation) return "Host status could not be loaded.";
    const result = observation.result;
    switch (result.kind) {
        case "api_problem":
            return `${result.status === 401 || result.status === 403 ? "Access to host status was refused." : "Host status is unavailable."} Diagnostic code: ${result.problem.code}.`;
        case "domain_failure":
            return "The host status read completed with a failed outcome.";
        case "protocol_failure":
            return "The host status response could not be validated.";
        case "transport_failure":
            return "The connection did not produce a validated host status response.";
        case "aborted":
            return "The host status read was interrupted.";
        case "success":
            return "";
    }
}

function HostObservation({ status }: { status: HostStatus }) {
    const known = status.state === "supported" || status.state === "guarded";
    return (
        <>
            <p data-testid="host-state">
                Host state: <strong>{status.state}</strong>.
            </p>
            {status.reason !== null && (
                <p role="status">{reasons[status.reason]}</p>
            )}
            {status.binding !== null && (
                <dl className="host-binding">
                    <div>
                        <dt>Profile</dt>
                        <dd>{status.profile}</dd>
                    </div>
                    <div>
                        <dt>Installed release</dt>
                        <dd>
                            {status.binding.release_version}
                            {status.binding.source_dirty
                                ? " (modified source)"
                                : ""}
                        </dd>
                    </div>
                    <div>
                        <dt>Deployment identity</dt>
                        <dd>
                            <code>{status.binding.deployment_sha256}</code>
                        </dd>
                    </div>
                    <div>
                        <dt>Policy identity</dt>
                        <dd>
                            <code>{status.binding.policy_sha256}</code>
                        </dd>
                    </div>
                </dl>
            )}
            <dl
                className="host-permissions"
                aria-label="Effective host action permissions"
            >
                {actions.map((action) => (
                    <div key={action} data-testid={`host-permission-${action}`}>
                        <dt>{labels[action]}</dt>
                        <dd>
                            <strong>
                                {status.permissions[action]
                                    ? "Allowed"
                                    : known
                                      ? "Denied"
                                      : "Unavailable"}
                                .
                            </strong>{" "}
                            {
                                permissionReasons[
                                    status.permission_reasons[action]
                                ]
                            }
                        </dd>
                    </div>
                ))}
            </dl>
            {status.facts !== null && (
                <>
                    <p>
                        Archive guard: {status.facts.guard}. Archive mount:{" "}
                        {status.facts.archive_mount}.
                    </p>
                    <div className="host-unit-table">
                        <table>
                            <caption>Fixed archive services and timers</caption>
                            <thead>
                                <tr>
                                    <th scope="col">Unit</th>
                                    <th scope="col">Load</th>
                                    <th scope="col">State</th>
                                    <th scope="col">Installation</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(status.facts.units).map(
                                    ([unit, state]) => (
                                        <tr key={unit}>
                                            <th scope="row">
                                                <code>{unit}</code>
                                            </th>
                                            <td>{state.load}</td>
                                            <td>{state.active}</td>
                                            <td>{state.unit_file}</td>
                                        </tr>
                                    ),
                                )}
                            </tbody>
                        </table>
                    </div>
                    <h3>Synchronization schedule</h3>
                    {status.facts.sync_schedule.state === "observed" ? (
                        <dl>
                            <div>
                                <dt>Calendar</dt>
                                <dd>
                                    <code>
                                        {status.facts.sync_schedule.on_calendar}
                                    </code>
                                </dd>
                            </div>
                            <div>
                                <dt>Randomized delay</dt>
                                <dd>
                                    {status.facts.sync_schedule
                                        .randomized_delay_sec ??
                                        "No value was observed."}
                                </dd>
                            </div>
                            <div>
                                <dt>Source</dt>
                                <dd>{status.facts.sync_schedule.source}</dd>
                            </div>
                            <div>
                                <dt>Revision</dt>
                                <dd>
                                    <code>
                                        {status.facts.sync_schedule.revision}
                                    </code>
                                </dd>
                            </div>
                        </dl>
                    ) : (
                        <p>
                            {status.facts.sync_schedule.reason ===
                            "profile-unproved"
                                ? "Schedule observation is unavailable for this deployment profile."
                                : "Current schedule facts could not be established."}
                        </p>
                    )}
                </>
            )}
        </>
    );
}

/** A bounded, cancellable read. A new client or authority hides old facts immediately. */
export function HostStatusPanel({
    client,
    scope,
}: {
    client: ApiClient;
    scope: ApiScope;
}) {
    const [refresh, setRefresh] = useState(0);
    const key = JSON.stringify(scope);
    const identity = useMemo(
        () => ({ client, key, refresh }),
        [client, key, refresh],
    );
    const [observed, setObserved] = useState<{
        readonly identity: typeof identity;
        readonly observation: Observation;
    } | null>(null);
    const observation =
        observed?.identity === identity ? observed.observation : null;
    useEffect(() => {
        const controller = new AbortController();
        void client
            .hostStatus({ signal: controller.signal })
            .then((result) => {
                if (!controller.signal.aborted)
                    setObserved({ identity, observation: { result } });
            })
            .catch(() => {
                if (!controller.signal.aborted)
                    setObserved({
                        identity,
                        observation: { unavailable: true },
                    });
            });
        return () => {
            controller.abort();
        };
    }, [client, identity]);
    const result =
        observation !== null && "result" in observation
            ? observation.result
            : null;
    return (
        <Panel title="Host administration">
            <p>
                Host status reports administrative evidence. Archive health and
                operation outcomes have separate observations.
            </p>
            <p>
                Policy permissions describe host authority. This interface
                currently provides status reads.
            </p>
            {observation === null ? (
                <p role="status">Loading host status.</p>
            ) : result?.kind === "success" ? (
                <HostObservation status={result.payload} />
            ) : (
                <p role="alert">{failure(observation)}</p>
            )}
            <button
                type="button"
                disabled={observation === null}
                onClick={() => {
                    setRefresh((value) => value + 1);
                }}
            >
                Refresh host status
            </button>
        </Panel>
    );
}

export function HostAdministration({ bootstrap }: { bootstrap: UiBootstrap }) {
    const host = useMemo(() => {
        const scope = bootstrapScope(bootstrap);
        return { client: createApiClient({ scope }), scope };
    }, [bootstrap]);
    return <HostStatusPanel client={host.client} scope={host.scope} />;
}
