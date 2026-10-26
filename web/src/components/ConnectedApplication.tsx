import { useSyncExternalStore } from "react";
import { App } from "../App";
import { checkRelease } from "../bootstrap";
import type { SessionController } from "../state/session-controller";

export function ConnectedApplication({
    controller,
    basePath,
    fetcher,
}: {
    controller: SessionController;
    basePath: string;
    fetcher: typeof fetch;
}) {
    const session = useSyncExternalStore(
        controller.subscribe,
        controller.snapshot,
    );
    return (
        <App
            basePath={basePath}
            bootstrap={session.bootstrap}
            controller={controller}
            session={session}
            onCheckRelease={() => checkRelease(session.bootstrap, fetcher)}
        />
    );
}
