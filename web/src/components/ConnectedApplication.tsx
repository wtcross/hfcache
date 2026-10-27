import { useSyncExternalStore } from "react";
import { App } from "../App";
import { checkRelease } from "../bootstrap";
import type { SessionController } from "../state/session-controller";
import type { LibraryStore } from "../library/library-state";
import { libraryFragment } from "../library/filters";
import type { RepositoryStore } from "../repository/repository-state";
import type { ConfigurationStore } from "../configuration/configuration-state";
import type { JobsStore } from "../operations/jobs-state";
import type { HistoryStore } from "../operations/history-state";
import type { MaintenanceStore } from "../operations/maintenance-state";

export function ConnectedApplication({
    controller,
    basePath,
    fetcher,
    library,
    repository,
    configuration,
    jobs,
    history,
    maintenance,
}: {
    controller: SessionController;
    basePath: string;
    fetcher: typeof fetch;
    library: LibraryStore;
    repository: RepositoryStore;
    configuration: ConfigurationStore;
    jobs: JobsStore;
    history: HistoryStore;
    maintenance: MaintenanceStore;
}) {
    const session = useSyncExternalStore(
        controller.subscribe,
        controller.snapshot,
    );
    const libraryState = useSyncExternalStore(
        library.subscribe,
        library.snapshot,
    );
    useSyncExternalStore(configuration.subscribe, configuration.snapshot);
    return (
        <App
            basePath={basePath}
            bootstrap={session.bootstrap}
            controller={controller}
            session={session}
            library={library}
            repository={repository}
            configuration={configuration}
            jobs={jobs}
            history={history}
            maintenance={maintenance}
            libraryBookmark={libraryFragment(libraryState.filters)}
            onCheckRelease={() => checkRelease(session.bootstrap, fetcher)}
        />
    );
}
