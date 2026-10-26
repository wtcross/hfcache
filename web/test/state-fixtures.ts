/** Owned transport adapters for state units; no installed/API-effect acceptance claim. */
import { ApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { createAuthSession, receiptIdentity } from "../src/state/authority";
import type { AuthorizedObservation } from "../src/state/authority";
import {
    decodeClientOperation,
    decodeClientEvents,
} from "../src/wire/generated";
import type { ClientOperation } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { ARCHIVE_ID, jsonResponse, readWire } from "./read-fixtures";

export const scope = createApiScope({
    origin:
        typeof location === "undefined"
            ? "https://state.invalid"
            : location.origin,
    publicPrefix: "",
    authorityEpoch: "epoch-one",
    subject: "owned-user",
    credentialClass: "rest-writer",
    instanceId: "1".repeat(32),
    archiveId: ARCHIVE_ID,
    configFingerprint: "2".repeat(64),
});
export const session = createAuthSession({ scope, authGeneration: 1 });
export const OPERATION_ID = "a".repeat(32);
export type VersionResult = Awaited<ReturnType<ApiClient["readVersion"]>>;

export function versionResult(application = "owned"): Promise<VersionResult> {
    return new ApiClient({
        scope,
        fetcher: () =>
            Promise.resolve(
                jsonResponse(
                    readWire("version", {
                        application,
                        python: "fixture",
                        huggingface_hub: "fixture",
                        transfer_backend: "http",
                    }),
                ),
            ),
    }).readVersion();
}
export function deferred<T>() {
    let resolve: (value: T) => void = () => {
        throw new Error("Deferred not initialized.");
    };
    const promise = new Promise<T>((complete) => {
        resolve = complete;
    });
    return {
        promise,
        resolve: (value: T) => {
            resolve(value);
        },
    };
}
export function receipt(change: Record<string, unknown> = {}): ClientOperation {
    return decodeClientOperation(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                operation_id: OPERATION_ID,
                principal: "rest-writer",
                route: "/api/v1/catalog/refreshes",
                archive_id: ARCHIVE_ID,
                config_fingerprint: scope.configFingerprint,
                state: "running",
                created_at: "2026-10-20T12:00:00.000001Z",
                updated_at: "2026-10-20T12:00:01.000000Z",
                completed_at: null,
                domain_run_id: "3".repeat(32),
                transaction_ids: [],
                next_event_sequence: 1,
                result_recorded: false,
                ...change,
            }),
        ),
    );
}
export function terminal(state: "succeeded" | "failed" = "succeeded") {
    return receipt({
        state,
        updated_at: "2026-10-20T12:00:02.000000Z",
        completed_at: "2026-10-20T12:00:02.000000Z",
        result_recorded: true,
    });
}
export function authorized(
    locator: AuthorizedObservation["locator"] = {
        kind: "key",
        key: "owned-original-key",
    },
): AuthorizedObservation {
    return Object.freeze({
        recordId: "owned-record",
        target: scope,
        authGeneration: 1,
        locator,
        expectedSafeReceiptIdentity: null,
    });
}
export function reauthorize(
    auth: AuthorizedObservation,
    value: ClientOperation,
): AuthorizedObservation {
    const next: AuthorizedObservation = {
        ...auth,
        locator: { kind: "id", operationId: value.operation_id },
        expectedSafeReceiptIdentity: receiptIdentity(value),
    };
    return Object.freeze(next);
}
export function operationResponse(
    command: string,
    data: unknown,
    failed = false,
) {
    const value = readWire(command, data, failed);
    return {
        ...value,
        archive_id: ARCHIVE_ID,
        config_fingerprint: scope.configFingerprint,
    };
}
export function resultResponse() {
    return operationResponse("catalog refresh", {
        schema_version: 1,
        state: "complete",
        archive_id: ARCHIVE_ID,
        revision_scope: "retained",
        tags: false,
        technical: true,
        curation_fingerprint: "4".repeat(64),
        curation_observed_at: "2026-10-20T12:00:00.000000Z",
        counts: {
            repositories: 0,
            snapshots_written: 0,
            observations_written: 0,
            records_failed: 0,
            technical_incomplete: 0,
            technical_skipped: 0,
        },
        repositories: [],
    });
}
export function events(
    sequences: number[],
    change: Record<string, unknown> = {},
) {
    return decodeClientEvents(
        parseWireJson(
            JSON.stringify({
                operation_id: OPERATION_ID,
                events: sequences.map((sequence) => ({
                    schema_version: 1,
                    sequence,
                    at: "2026-10-20T12:00:01.000000Z",
                    kind: "operation.progress",
                    message: "owned event",
                })),
                next_cursor: sequences.at(-1) ?? 0,
                oldest_sequence: 1,
                truncated: false,
                ...change,
            }),
        ),
    );
}
