/** Real client/controller fixtures; controlled HTTP boundaries, no business-effect acceptance. */
import { vi } from "vitest";
import prune from "../../tests/fixtures/schemas/prune-plan.json";
import purge from "../../tests/fixtures/schemas/purge-plan.json";
import manifest from "../../tests/fixtures/schemas/manifest.json";
import reference from "../../tests/fixtures/schemas/reference.json";
import { createSessionController } from "../src/state/session-controller";
import { createMaintenanceStore } from "../src/operations/maintenance-state";
import type { RepairFindingIntent } from "../src/operations/maintenance-state";
import {
    decodeFinding,
    decodePrunePayload,
    decodePurgePayload,
    decodeRecoveryPlanPayload,
    decodeQuarantinePayload,
} from "../src/wire/generated";
import type { UiBootstrap } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import { operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
export { manifest, reference };
const wire = (value: unknown) => parseWireJson(JSON.stringify(value));
export const transactionId = "7".repeat(32);
export function prunePayload() {
    return decodePrunePayload(wire({ plans: [prune], applied: [] }));
}
export function purgePayload() {
    return decodePurgePayload(wire({ plans: [purge], applied: [] }));
}
export function recoveryPayload() {
    return decodeRecoveryPlanPayload(
        wire({
            actionable: 1,
            blocked: 0,
            plan: [
                {
                    transaction_id: transactionId,
                    operation: "sync",
                    state: "downloaded",
                    last_checkpoint: null,
                    remedy: "quarantine_staging",
                    reason: "owned unfinished transaction",
                },
            ],
        }),
    );
}
export function quarantinePayload() {
    return decodeQuarantinePayload(
        wire({
            plans: [
                {
                    transaction_id: transactionId,
                    repository: "model:organization/model-name",
                    quarantine_path: "quarantine/" + transactionId,
                    recovery_transaction_id: "8".repeat(32),
                    files: [],
                    directories: [],
                    logical_bytes: 0,
                    already_absent: false,
                },
            ],
            applied: [],
        }),
    );
}
export function repairFinding(): RepairFindingIntent {
    return {
        source: {
            archiveId: ARCHIVE_ID,
            runId: "3".repeat(32),
            completedAt: "2026-10-20T12:00:02.000000Z",
        },
        finding: decodeFinding(
            wire({
                repository_type: manifest.repository_type,
                repository_id: manifest.repository_id,
                commit_sha: manifest.commit_sha,
                publication_id: manifest.publication_id,
                kind: "digest_mismatch",
                path: "config.json",
                expected: "a".repeat(64),
                observed: "b".repeat(64),
            }),
        ),
    };
}
export interface MaintenanceFixtureOptions {
    readonly payload?: (route: string, request: unknown) => unknown;
    readonly fetch?: (
        url: URL,
        init: RequestInit | undefined,
    ) => Response | Promise<Response> | undefined;
    readonly failed?: boolean;
    readonly bootstrap?: UiBootstrap;
}
export function setupMaintenance(options: MaintenanceFixtureOptions = {}) {
    const bootstrap = options.bootstrap ?? {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
        configured_origin:
            typeof location === "undefined"
                ? "https://archive.invalid"
                : location.origin,
    };
    const storage = new Map<string, string>();
    const operations = new Map<
        string,
        { route: string; key: string; body: unknown }
    >();
    const requests: {
        method: string;
        path: string;
        key: string | null;
        body: unknown;
    }[] = [];
    function resultPayload(route: string, body: unknown): unknown {
        if (options.payload) return options.payload(route, body);
        if (route.includes("prune")) return prunePayload();
        if (route.includes("purge")) return purgePayload();
        if (route.includes("quarantine")) return quarantinePayload();
        if (route === "/api/v1/recovery-plans") return recoveryPayload();
        if (route === "/api/v1/recoveries")
            return {
                ...recoveryPayload(),
                applied: 1,
                report: "runs/recovery.json",
            };
        return {
            commit_sha: manifest.commit_sha,
            retired_publication_id: manifest.publication_id,
            replacement_publication_id: "9".repeat(32),
            grace_expires_at: "2026-10-21T12:00:00Z",
            transaction_id: transactionId,
            retirement_record: "retirements/owned.json",
            verified: true,
        };
    }
    const commands: Record<string, string> = {
        "/api/v1/prune-plans": "prune --dry-run",
        "/api/v1/prunes": "prune --apply",
        "/api/v1/purge-plans": "purge --dry-run",
        "/api/v1/purges": "purge --apply",
        "/api/v1/recovery-plans": "recover --dry-run",
        "/api/v1/recoveries": "recover --apply",
        "/api/v1/quarantine-plans": "quarantine --dry-run",
        "/api/v1/quarantine-cleanups": "quarantine --apply",
        "/api/v1/repairs": "repair",
    };
    function current(id: string, row: { route: string }, accepted = false) {
        return receipt({
            operation_id: id,
            route: row.route,
            state: accepted
                ? "queued"
                : options.failed
                  ? "failed"
                  : "succeeded",
            domain_run_id: accepted ? null : "3".repeat(32),
            completed_at: accepted ? null : "2026-10-20T12:00:02.000000Z",
            updated_at: accepted
                ? "2026-10-20T12:00:01.000000Z"
                : "2026-10-20T12:00:02.000000Z",
            result_recorded: !accepted,
        });
    }
    const fetcher = vi.fn<typeof fetch>(async (input, init) => {
        const url = new URL(
            typeof input === "string"
                ? input
                : input instanceof URL
                  ? input.href
                  : input.url,
        );
        const method = init?.method ?? "GET";
        const key = new Headers(init?.headers).get("Idempotency-Key");
        const body: unknown =
            typeof init?.body === "string" ? JSON.parse(init.body) : null;
        requests.push({ method, path: url.pathname, key, body });
        const override = options.fetch?.(url, init);
        if (override !== undefined) return await override;
        if (method === "POST") {
            const id = (operations.size + 1).toString(16).padStart(32, "0");
            if (key === null) throw new Error("Expected original key");
            operations.set(id, { route: url.pathname, key, body });
            const status = "/api/v1/operations/" + id;
            return new Response(
                JSON.stringify({
                    schema_version: 1,
                    request_id: "f".repeat(32),
                    archive_id: ARCHIVE_ID,
                    config_fingerprint: "2".repeat(64),
                    created: true,
                    operation: current(id, { route: url.pathname }, true),
                    links: {
                        status,
                        result: status + "/result",
                        events: status + "/events",
                    },
                }),
                {
                    status: 202,
                    headers: {
                        "Content-Type": "application/json",
                        Location: status,
                    },
                },
            );
        }
        if (url.pathname.endsWith("/operations/lookup")) {
            const row = [...operations].find(([, entry]) => entry.key === key);
            return row
                ? jsonResponse(
                      operationResponse("operations lookup", {
                          operation: current(row[0], row[1]),
                      }),
                  )
                : jsonResponse(problemWire("HFAPI013", 20), 404);
        }
        const match =
            /\/operations\/([0-9a-f]{32})(?:\/(events|result))?$/u.exec(
                url.pathname,
            );
        if (match) {
            const id = match[1];
            if (id === undefined) throw new Error("Missing operation id");
            const row = operations.get(id);
            if (!row) return jsonResponse(problemWire("HFAPI013", 20), 404);
            if (match[2] === "events")
                return jsonResponse(
                    operationResponse("operations events", {
                        operation_id: id,
                        events: [],
                        next_cursor: 0,
                        oldest_sequence: 1,
                        truncated: false,
                    }),
                );
            if (match[2] === "result") {
                const command = commands[row.route];
                if (command === undefined)
                    throw new Error("Unknown operation route");
                return jsonResponse(
                    operationResponse(
                        command,
                        options.failed
                            ? {}
                            : resultPayload(row.route, row.body),
                        options.failed,
                    ),
                );
            }
            return jsonResponse(
                operationResponse("operations show", {
                    operation: current(id, row),
                }),
            );
        }
        if (url.pathname.includes("/manifests/"))
            return jsonResponse(
                operationResponse("manifest read", {
                    manifest,
                    tree_base: "archive-root/",
                }),
            );
        if (url.pathname.includes("/references/"))
            return jsonResponse(
                operationResponse("reference read", {
                    reference,
                    locator_base: "published/",
                }),
            );
        return jsonResponse(problemWire("HFAPI013", 20), 404);
    });
    const controller = createSessionController({
        bootstrap,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
        storage: {
            getItem: (key) => storage.get(key) ?? null,
            setItem: (key, value) => {
                storage.set(key, value);
            },
        },
    });
    const store = createMaintenanceStore(controller);
    return {
        controller,
        store,
        fetcher,
        storage,
        requests,
        operations,
        bootstrap,
        dispose() {
            store.dispose();
            controller.dispose();
        },
    };
}
