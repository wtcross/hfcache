import { createRoot } from "react-dom/client";
import { App } from "./App";
import { validateBasePath } from "./navigation";
import type { UiBootstrap } from "./wire/generated";
import { checkRelease, loadBootstrap, readInertMetadata } from "./bootstrap";
import type { CompiledIdentity } from "./bootstrap";

export async function startApplication(
    document: Document,
    origin: string,
    compiled: CompiledIdentity,
    fetcher: typeof fetch = globalThis.fetch,
): Promise<() => void> {
    const bootstrap = await loadBootstrap(document, origin, compiled, fetcher);
    return mountApplication(document, bootstrap, fetcher);
}

export function mountApplication(
    document: Document,
    bootstrap: UiBootstrap,
    fetcher: typeof fetch = globalThis.fetch,
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
    const root = createRoot(container);
    root.render(
        <App
            basePath={basePath}
            bootstrap={bootstrap}
            onCheckRelease={() => checkRelease(bootstrap, fetcher)}
        />,
    );
    return () => {
        root.unmount();
    };
}
