import type { AdministrationReadStore } from "../administration/administration-read-state";
import type { HostControlsStore } from "../administration/host-controls-state";
import type { ConfigurationStore } from "../configuration/configuration-state";
import type { JobsStore } from "../operations/jobs-state";
import type {
    SessionController,
    SessionSnapshot,
} from "../state/session-controller";
import { Panel } from "../primitives";
import { AdministrationReadView } from "./AdministrationReadView";
import { AdministrationDiagnostics } from "./AdministrationDiagnostics";
import { HostControls } from "./HostControls";
import { SessionHostAdministration } from "./HostStatusPanel";
import { ConfigurationEditor } from "./ConfigurationEditor";
import { OperationRecovery } from "./OperationRecovery";

export function AdministrationWorkspace({
    controller,
    session,
    read,
    hostControls,
    configuration,
    jobs,
    onNavigate,
    onReadReport,
}: {
    controller: SessionController;
    session: SessionSnapshot;
    read: AdministrationReadStore;
    hostControls: HostControlsStore;
    configuration?: ConfigurationStore;
    jobs?: JobsStore;
    onNavigate: (
        destination: "configuration" | "maintenance" | "operations",
    ) => void;
    onReadReport?: (runId: string) => void;
}) {
    const canReadHost = session.bootstrap.user.admin_permissions.some(
        (permission) =>
            permission.capability === "host-read" && permission.effective,
    );
    return (
        <div className="administration-workspace">
            <AdministrationReadView
                store={read}
                controller={controller}
                session={session}
                onNavigate={onNavigate}
            />
            {canReadHost ? (
                <SessionHostAdministration controller={controller} />
            ) : (
                <Panel title="Host administration">
                    <p>
                        Current administrator permission does not allow host
                        status reads. Authentication alone does not grant host
                        authority.
                    </p>
                </Panel>
            )}
            <HostControls
                store={hostControls}
                controller={controller}
                session={session}
            />
            {configuration !== undefined && (
                <div id="administration-configuration" tabIndex={-1}>
                    <ConfigurationEditor store={configuration} />
                </div>
            )}
            {jobs !== undefined && (
                <AdministrationDiagnostics
                    key={session.generation}
                    store={jobs}
                    session={session}
                />
            )}
            <OperationRecovery
                controller={controller}
                session={session}
                {...(configuration === undefined ? {} : { configuration })}
                {...(onReadReport === undefined ? {} : { onReadReport })}
            />
        </div>
    );
}
