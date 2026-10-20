import { createRoot } from "react-dom/client";
import { App } from "./App";
import { validateBasePath } from "./navigation";

export function mountApplication(document: Document): () => void {
    const container = document.getElementById("root");
    if (container === null)
        throw new Error("The application container is unavailable.");
    const basePath = validateBasePath(
        document
            .querySelector('meta[name="hfcache-ui-base"]')
            ?.getAttribute("content"),
    );
    const root = createRoot(container);
    root.render(<App basePath={basePath} />);
    return () => {
        root.unmount();
    };
}
