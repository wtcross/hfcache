import { startApplication } from "./mount";
import "./styles.css";
import { WIRE_SOURCE_DIGEST } from "./wire/generated";

declare const __HFCACHE_BUILD_SOURCE__: string;
declare const __HFCACHE_APPLICATION_VERSION__: string;

void startApplication(document, window.location.origin, {
    source: __HFCACHE_BUILD_SOURCE__,
    application: __HFCACHE_APPLICATION_VERSION__,
    wire: WIRE_SOURCE_DIGEST,
}).catch(() => {
    const container = document.getElementById("root");
    if (container !== null && !container.querySelector('[role="status"]')) {
        const diagnostic = document.createElement("p");
        diagnostic.setAttribute("role", "status");
        diagnostic.textContent =
            "The interface could not start. Reload the interface or contact your operator.";
        container.append(diagnostic);
    }
});
