import { createRoot } from "react-dom/client";
import { useEffect, useState } from "react";
import { createApiClient } from "../../src/api/client";
import { createApiScope } from "../../src/api/identity";
import { StatusReadView } from "../../src/components/StatusReadView";
import type { ReadSource } from "../../src/components/StatusReadView";
import "../../src/styles.css";
import { readBoundedJson, WireError } from "../../src/wire/json";
import { decodeNamed } from "../../src/wire/generated";
import { wireArray, wireObject, wireString } from "../../src/wire/runtime";
import { LoadBoundary } from "./load-boundary";

function metadata(name: string): string {
    const value = document.querySelector<HTMLMetaElement>(
        `meta[name="${name}"]`,
    )?.content;
    if (value === undefined)
        throw new Error("Owned read fixture metadata is missing.");
    return value;
}

const scope = createApiScope({
    origin: window.location.origin,
    publicPrefix: metadata("fixture-api-prefix"),
    authorityEpoch: "owned-fixture-reader-1",
    subject: "owned-fixture-reader",
    credentialClass: "rest-reader",
    instanceId: metadata("fixture-instance-id"),
    archiveId: metadata("fixture-archive-id"),
    configFingerprint: null,
});
const client = createApiClient({ scope });
const selected = new URL(window.location.href).searchParams.get("source");
const source: ReadSource =
    selected === "version" ||
    selected === "capabilities" ||
    selected === "inspection"
        ? selected
        : "status";

export function ModelRoundtrip() {
    const [message, setMessage] = useState(
        "Loading original Python model fixtures.",
    );
    const [failed, setFailed] = useState(false);
    useEffect(() => {
        const controller = new AbortController();
        async function check() {
            const response = await fetch(
                scope.publicPrefix + "/__fixture__/original-models.json",
                {
                    credentials: "same-origin",
                    mode: "same-origin",
                    redirect: "error",
                    signal: controller.signal,
                },
            );
            if (response.status !== 200)
                throw new Error("Original model fixture was unavailable.");
            const root = wireObject(
                await readBoundedJson(response, { signal: controller.signal }),
                ["originals", "incorrect"],
            );
            const cases = (value: unknown) =>
                wireArray(
                    value,
                    (item) => {
                        const row = wireObject(item, [
                            "case_id",
                            "definition",
                            "value",
                        ]);
                        return {
                            caseId: wireString(row.case_id, 1, 128, null),
                            definition: wireString(
                                row.definition,
                                1,
                                128,
                                null,
                            ),
                            value: row.value,
                        };
                    },
                    1,
                    512,
                );
            const originals = cases(root.originals),
                incorrect = cases(root.incorrect);
            for (const item of originals)
                decodeNamed(item.definition, item.value);
            for (const item of incorrect) {
                let rejected = false;
                try {
                    decodeNamed(item.definition, item.value);
                } catch (error) {
                    if (!(error instanceof WireError)) throw error;
                    rejected = true;
                }
                if (!rejected)
                    throw new Error(
                        "An independently incorrect wire was accepted.",
                    );
            }
            if (!controller.signal.aborted)
                setMessage(
                    `Original Python models validated: ${String(originals.length)}. Independent incorrect wires refused: ${String(incorrect.length)}.`,
                );
        }
        void check().catch(() => {
            if (!controller.signal.aborted) {
                setFailed(true);
                setMessage("Original Python model roundtrip failed.");
            }
        });
        return () => {
            controller.abort();
        };
    }, []);
    return (
        <section>
            <h2>Original model roundtrip</h2>
            <p role={failed ? "alert" : "status"}>{message}</p>
        </section>
    );
}
const container = document.getElementById("root");
if (container === null)
    throw new Error("Owned read fixture container is missing.");
createRoot(container).render(
    <main>
        <h1>Read boundary preview</h1>
        <p>
            Owned source fixture. Caddy, Basic authentication and installed
            platform behavior are not established here.
        </p>
        {selected === "load" ? (
            <LoadBoundary scope={scope} />
        ) : selected === "roundtrip" ? (
            <ModelRoundtrip />
        ) : (
            <StatusReadView client={client} scope={scope} source={source} />
        )}
    </main>,
);
