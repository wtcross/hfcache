import { createRoot } from "react-dom/client";
import { ConnectedApplication } from "./components/ConnectedApplication";
import { validateBasePath } from "./navigation";
import type { UiBootstrap } from "./wire/generated";
import {
    loadBootstrap,
    loadReconnectBootstrap,
    readInertMetadata,
} from "./bootstrap";
import type { CompiledIdentity } from "./bootstrap";
import { createSessionController } from "./state/session-controller";
import type { OperationStorage } from "./state/operation-registry";
import { createLibraryStore } from "./library/library-state";

export async function startApplication(
    document: Document,
    origin: string,
    compiled: CompiledIdentity,
    fetcher: typeof fetch = globalThis.fetch,
): Promise<() => void> {
    const bootstrap = await loadBootstrap(document, origin, compiled, fetcher);
    return mountApplication(document, bootstrap, fetcher, () =>
        loadReconnectBootstrap(document, origin, compiled, bootstrap, fetcher),
    );
}

export function mountApplication(
    document: Document,
    bootstrap: UiBootstrap,
    fetcher: typeof fetch = globalThis.fetch,
    reconnect?: () => Promise<UiBootstrap>,
): () => void {
    const container = document.getElementById("root");
    if (container === null)
        throw new Error("The application container is unavailable.");
    const metadata = readInertMetadata(document);
    if (
        metadata.base !== bootstrap.paths.ui_base ||
        metadata.fingerprint !== bootstrap.build.asset_manifest_sha256
    )
        throw new Error("The deployment identity changed.");
    const basePath = validateBasePath(metadata.base);
    let storage: OperationStorage | null = null;
    try {
        storage = document.defaultView?.localStorage ?? null;
    } catch {
        /* Visible recovery-storage refusal. */
    }
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage,
        reconnect:
            reconnect ??
            (() =>
                loadReconnectBootstrap(
                    document,
                    bootstrap.configured_origin,
                    {
                        source: bootstrap.build.metadata.source_snapshot_sha256,
                        application:
                            bootstrap.build.metadata.application_version,
                        wire: bootstrap.wire_source_digest,
                    },
                    bootstrap,
                    fetcher,
                )),
    });
    const root = createRoot(container);
    const library = createLibraryStore(controller);
    root.render(
        <ConnectedApplication
            basePath={basePath}
            controller={controller}
            fetcher={fetcher}
            library={library}
        />,
    );
    return () => {
        root.unmount();
        library.dispose();
        controller.dispose();
    };
}
