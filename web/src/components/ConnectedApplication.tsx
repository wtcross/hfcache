import { useSyncExternalStore } from "react";
import { App } from "../App";
import { checkRelease } from "../bootstrap";
import type { SessionController } from "../state/session-controller";
import type { LibraryStore } from "../library/library-state";
import { libraryFragment } from "../library/filters";
import type { RepositoryStore } from "../repository/repository-state";
import type { ConfigurationStore } from "../configuration/configuration-state";

export function ConnectedApplication({
    controller,
    basePath,
    fetcher,
    library,
    repository,
    configuration,
}: {
    controller: SessionController;
    basePath: string;
    fetcher: typeof fetch;
    library: LibraryStore;
    repository: RepositoryStore;
    configuration: ConfigurationStore;
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
            libraryBookmark={libraryFragment(libraryState.filters)}
            onCheckRelease={() => checkRelease(session.bootstrap, fetcher)}
        />
    );
}
