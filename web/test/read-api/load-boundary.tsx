/** Real HTTP/API pool stress; transport faults are labelled negative evidence. */
import { useState } from "react";
import { createApiClient } from "../../src/api/client";
import type { ApiScope } from "../../src/api/identity";
import type { ReadOptions, ReadResult } from "../../src/api/types";
import { createQueryStore } from "../../src/state/query-state";
import {
    createReadCoordinator,
    createRetentionBudget,
    MAX_RETAINED_BYTES,
} from "../../src/state/retention-budget";

type Load = (options: ReadOptions) => Promise<ReadResult<unknown, unknown>>;

function requireCondition(value: boolean, message: string): void {
    if (!value) throw new Error(message);
}

async function until(predicate: () => boolean) {
    const deadline = performance.now() + 5000;
    while (!predicate()) {
        if (performance.now() >= deadline)
            throw new Error("A finite query-pool condition was not observed.");
        await new Promise<void>((resolve) => {
            setTimeout(resolve, 5);
        });
    }
}

async function exercise(scope: ApiScope) {
    const retention = createRetentionBudget();
    const reads = createReadCoordinator();
    let unauthorized = 0;
    const store = createQueryStore({
        session: { scope, authGeneration: 1 },
        retention,
        reads,
        onUnauthorized() {
            unauthorized++;
        },
    });
    let activeMaximum = 0;
    let waitingMaximum = 0;
    let retainedMaximum = 0;
    let startedReads = 0;
    const sample = () => {
        activeMaximum = Math.max(activeMaximum, reads.active);
        waitingMaximum = Math.max(waitingMaximum, reads.waiting);
        retainedMaximum = Math.max(retainedMaximum, retention.usedBytes);
        requireCondition(
            reads.active <= 2,
            "The active GET pool exceeded two.",
        );
        requireCondition(
            reads.waiting <= 64,
            "The finite GET queue overflowed.",
        );
        requireCondition(
            retention.usedBytes <= MAX_RETAINED_BYTES,
            "Encoded logical retention exceeded 32 MiB.",
        );
    };
    const observe =
        (load: Load): Load =>
        async (options) => {
            startedReads++;
            sample();
            const result = await load(options);
            sample();
            return result;
        };
    const transportClient = (fault: string, onHeaders = () => {}) =>
        createApiClient({
            scope,
            fetcher: async (input, init) => {
                const headers = new Headers(init?.headers);
                headers.set("X-Hfcache-Fixture-Fault", fault);
                const response = await fetch(input, { ...init, headers });
                onHeaders();
                return response;
            },
        });
    const client = createApiClient({ scope });
    let slowResponseHeaders = 0;
    const slow = transportClient("delay", () => {
        slowResponseHeaders++;
    });
    const cycleSamples: { cycle: number; retainedBytes: number }[] = [];
    const releases: (() => void)[] = [];
    try {
        const parallel = [
            store.query(
                { routeId: "version_default" },
                observe((options) => slow.readVersion(options)),
            ),
            store.query(
                { routeId: "capabilities_default" },
                observe((options) => slow.readCapabilities(options)),
            ),
            store.query(
                { routeId: "status_default" },
                observe((options) => slow.readStatus(options)),
            ),
        ];
        for (const query of parallel) releases.push(query.subscribe(sample));
        const pending = parallel.map((query) => query.refresh());
        await until(() => reads.active === 2 && reads.waiting === 1);
        sample();
        await Promise.all(pending);
        requireCondition(
            parallel.every((query) => query.snapshot().phase === "ready"),
            "Slow real service reads did not become ready.",
        );
        for (const release of releases.splice(0)) release();
        store.setSession({ scope, authGeneration: 2 });
        requireCondition(
            retention.usedBytes === 0,
            "Retired queries retained private data.",
        );

        const cancelled = store.query(
            { routeId: "version_default" },
            observe((options) => slow.readVersion(options)),
        );
        releases.push(cancelled.subscribe(sample));
        const beforeCancelledHeaders = slowResponseHeaders;
        const abandoned = cancelled.refresh();
        await until(() => slowResponseHeaders > beforeCancelledHeaders);
        cancelled.invalidate();
        await abandoned;
        requireCondition(
            cancelled.snapshot().phase === "idle" &&
                cancelled.snapshot().result === null,
            "Cancelled response supplied stale private facts.",
        );
        requireCondition(
            reads.active === 0 && reads.waiting === 0,
            "Cancelled GET ownership failed to drain.",
        );
        await cancelled.refresh();
        requireCondition(
            cancelled.snapshot().phase === "ready",
            "Explicit fresh read did not recover after cancellation.",
        );
        for (const release of releases.splice(0)) release();

        const old = store.query(
            { routeId: "capabilities_default" },
            observe((options) => slow.readCapabilities(options)),
        );
        const originalKey = old.snapshot().key;
        releases.push(old.subscribe(sample));
        const beforeSupersededHeaders = slowResponseHeaders;
        const superseded = old.refresh();
        await until(() => slowResponseHeaders > beforeSupersededHeaders);
        store.setSession({ scope, authGeneration: 3 });
        await superseded;
        const beforeRetiredRead = startedReads;
        await old.refresh();
        requireCondition(
            old.snapshot().result === null &&
                old.snapshot().phase === "unavailable" &&
                startedReads === beforeRetiredRead,
            "Retired authority was reused by an old handle.",
        );
        for (const release of releases.splice(0)) release();

        const cycleStarted = performance.now();
        for (let cycle = 1; cycle <= 100; cycle++) {
            const route = cycle % 3;
            const query =
                route === 0
                    ? store.query(
                          { routeId: "version_default" },
                          observe((options) => client.readVersion(options)),
                      )
                    : route === 1
                      ? store.query(
                            { routeId: "capabilities_default" },
                            observe((options) =>
                                client.readCapabilities(options),
                            ),
                        )
                      : store.query(
                            { routeId: "status_default" },
                            observe((options) => client.readStatus(options)),
                        );
            const release = query.subscribe(sample);
            try {
                await query.refresh();
                requireCondition(
                    query.snapshot().phase === "ready" &&
                        query.snapshot().key !== originalKey,
                    "A route-cycle read reused unavailable or old-generation data.",
                );
                sample();
                requireCondition(
                    reads.active === 0 && reads.waiting === 0,
                    "A settled route retained GET ownership.",
                );
                if (cycle % 10 === 0)
                    cycleSamples.push({
                        cycle,
                        retainedBytes: retention.usedBytes,
                    });
            } finally {
                release();
            }
        }
        requireCondition(
            Math.max(...cycleSamples.map((item) => item.retainedBytes)) <
                64 * 1024,
            "Small completed route reads accumulated beyond their finite cache.",
        );
        const cycleElapsedMs = performance.now() - cycleStarted;

        for (const fault of ["response-limit", "unsafe-integer"]) {
            const broken = transportClient(fault);
            const query = store.query(
                {
                    routeId:
                        fault === "unsafe-integer"
                            ? "capabilities_default"
                            : "version_default",
                },
                observe((options) =>
                    fault === "unsafe-integer"
                        ? broken.readCapabilities(options)
                        : broken.readVersion(options),
                ),
            );
            await query.refresh();
            const snapshot = query.snapshot();
            requireCondition(
                snapshot.phase === "failed" &&
                    snapshot.result?.kind === "protocol_failure" &&
                    snapshot.result.reason ===
                        (fault === "unsafe-integer"
                            ? "unsafe_number"
                            : "bounds"),
                `The labelled ${fault} wire did not receive its exact refusal: ${JSON.stringify(snapshot.result)}.`,
            );
        }
        requireCondition(
            unauthorized === 0,
            "A real authenticated service read unexpectedly lost authority.",
        );
        return {
            cycles: 100,
            cycleElapsedMs,
            browser: navigator.userAgent,
            activeMaximum,
            waitingMaximum,
            retainedMaximum,
            maximumRetainedBytes: retention.maximumBytes,
            cycleSamples,
            startedReads,
            slowCompletedServiceHeaders: slowResponseHeaders,
            interruptedAfterCompletedServiceHeaders: 2,
            cancelledAndSupersededDrained: true,
            retiredHandlesBlocked: true,
            finalOwnershipDrained: true,
            negativeFaults: ["response-limit", "unsafe-integer"],
            heapMeasurement: "not measured; encoded retention is not JS heap",
        };
    } finally {
        for (const release of releases) release();
        store.dispose();
        await until(() => reads.active === 0 && reads.waiting === 0);
        requireCondition(
            reads.active === 0 &&
                reads.waiting === 0 &&
                retention.usedBytes === 0,
            "Final query/read/encoded-retention ownership did not drain.",
        );
    }
}

export function LoadBoundary({ scope }: { readonly scope: ApiScope }) {
    const [phase, setPhase] = useState("idle");
    const [summary, setSummary] = useState("");
    return (
        <section>
            <h2>Real API query-pool stress</h2>
            <p>
                Owned source integration. Positive reads use real authentication
                and services. Explicit post-service faults provide negative
                evidence only.
            </p>
            <button
                type="button"
                disabled={phase !== "idle"}
                onClick={() => {
                    setPhase("running");
                    void exercise(scope)
                        .then((result) => {
                            setSummary(JSON.stringify(result));
                            setPhase("passed");
                        })
                        .catch((error: unknown) => {
                            setSummary(
                                error instanceof Error
                                    ? error.message
                                    : "Unknown integration failure.",
                            );
                            setPhase("failed");
                        });
                }}
            >
                Run finite read stress
            </button>
            <p
                data-testid="load-phase"
                role={phase === "failed" ? "alert" : "status"}
            >
                {phase}
            </p>
            <pre data-testid="load-summary">{summary}</pre>
        </section>
    );
}
