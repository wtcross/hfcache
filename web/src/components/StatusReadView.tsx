import { useEffect, useMemo, useState } from "react";
import type { ApiClient } from "../api/client";
import type { ApiScope } from "../api/identity";
import type { ReadResult } from "../api/types";

export type ReadSource = "version" | "capabilities" | "status" | "inspection";

type DisplayState = {
    kind:
        | "loading"
        | "success"
        | "domain_failure"
        | "api_problem"
        | "protocol_failure"
        | "transport_failure"
        | "aborted";
    title: string;
    detail: string;
    codes: readonly string[];
    requestId?: string;
};

const loading: DisplayState = {
    kind: "loading",
    title: "Loading server information",
    detail: "A bounded read is in progress.",
    codes: [],
};

function display<Success, Failure>(
    result: ReadResult<Success, Failure>,
    title: string,
    describe: (payload: Success) => string,
): DisplayState {
    switch (result.kind) {
        case "success":
            return {
                kind: "success",
                title,
                detail: describe(result.payload),
                codes: result.response.envelope.warnings.map(
                    (warning) => warning.code,
                ),
                requestId: result.response.request_id,
            };
        case "domain_failure":
            return {
                kind: "domain_failure",
                title: "Read failed",
                detail: "The server completed this read with a failed domain outcome.",
                codes: [
                    ...result.response.envelope.errors,
                    ...result.response.envelope.warnings,
                ].map((error) => error.code),
                requestId: result.response.request_id,
            };
        case "api_problem":
            return {
                kind: "api_problem",
                title:
                    result.status === 401 || result.status === 403
                        ? "Access refused"
                        : "API unavailable",
                detail: "The API refused this read. Its diagnostic code is preserved below.",
                codes: [result.problem.code],
                requestId: result.problem.request_id,
            };
        case "protocol_failure":
            return {
                kind: "protocol_failure",
                title: "Unsupported response",
                detail: "The response could not be validated. No server facts have been inferred.",
                codes:
                    result.preserved === undefined
                        ? []
                        : [
                              ...result.preserved.errors,
                              ...result.preserved.warnings,
                          ].map((problem) => problem.code),
                ...(result.preserved === undefined
                    ? {}
                    : { requestId: result.preserved.request_id }),
            };
        case "transport_failure":
            return {
                kind: "transport_failure",
                title: "Connection unavailable",
                detail: "The read did not produce a validated response.",
                codes: [],
            };
        case "aborted":
            return {
                kind: "aborted",
                title: "Read unavailable",
                detail: "This read was interrupted. No outcome has been inferred.",
                codes: [],
            };
    }
}

/** A real bounded GET view; the temporary fixture mount grants no write authority. */
export function StatusReadView({
    client,
    scope,
    source,
}: {
    client: ApiClient;
    scope: ApiScope;
    source: ReadSource;
}) {
    const [refresh, setRefresh] = useState(0);
    const key = JSON.stringify([
        source,
        scope.origin,
        scope.publicPrefix,
        scope.authorityEpoch,
        scope.subject,
        scope.credentialClass,
        scope.instanceId,
        scope.archiveId,
        scope.configFingerprint,
    ]);
    const identity = useMemo(
        () => ({ client, key, refresh }),
        [client, key, refresh],
    );
    const [observed, setObserved] = useState({ identity, state: loading });
    // Identity changes hide private stale data before the effect runs (INV-019).
    const state = observed.identity === identity ? observed.state : loading;

    useEffect(() => {
        const controller = new AbortController();
        async function read(): Promise<DisplayState> {
            const options = { signal: controller.signal };
            switch (source) {
                case "version":
                    return display(
                        await client.readVersion(options),
                        "Server version",
                        (payload) => `Application ${payload.application}.`,
                    );
                case "capabilities":
                    return display(
                        await client.readCapabilities(options),
                        "Server capabilities",
                        (payload) =>
                            payload.maintenance_enabled
                                ? "Maintenance enabled."
                                : "Maintenance disabled.",
                    );
                case "status":
                    return display(
                        await client.readStatus(options),
                        "Server status",
                        (payload) =>
                            payload.archive.reachable
                                ? `${String(payload.repositories.length)} loaded repositories. Archive reachable.`
                                : `${String(payload.repositories.length)} loaded repositories. Archive unavailable.`,
                    );
                case "inspection":
                    return display(
                        await client.readArchiveInspection(options),
                        "Archive inspection",
                        () => "The archive inspection completed successfully.",
                    );
            }
        }
        void read()
            .then((next) => {
                if (!controller.signal.aborted)
                    setObserved({ identity, state: next });
            })
            .catch(() => {
                if (!controller.signal.aborted)
                    setObserved({
                        identity,
                        state: {
                            kind: "transport_failure",
                            title: "Connection unavailable",
                            detail: "The read did not produce a validated response.",
                            codes: [],
                        },
                    });
            });
        return () => {
            controller.abort();
        };
    }, [client, identity, source]);

    const failure =
        state.kind !== "success" &&
        state.kind !== "loading" &&
        state.kind !== "aborted";
    return (
        <section aria-labelledby="server-read-heading">
            <h2 id="server-read-heading">{state.title}</h2>
            <div role={failure ? "alert" : "status"}>
                <p>{state.detail}</p>
                {state.codes.length > 0 && (
                    <ul aria-label="Original diagnostic codes">
                        {state.codes.map((code, index) => (
                            <li key={`${String(index)}:${code}`}>
                                <code>{code}</code>
                            </li>
                        ))}
                    </ul>
                )}
                {state.requestId !== undefined && (
                    <p>
                        Request ID:{" "}
                        <code data-testid="read-request-id">
                            {state.requestId}
                        </code>
                    </p>
                )}
            </div>
            <button
                type="button"
                disabled={state.kind === "loading"}
                onClick={() => {
                    setRefresh((value) => value + 1);
                }}
            >
                Refresh read
            </button>
        </section>
    );
}
