import { expect, test, vi } from "vitest";
import { ApiClient, createApiClient } from "../src/api/client";
import type { SubmissionOptions } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { decodeClientOperation } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
} from "./read-fixtures";

const id = "a".repeat(32),
    sha = "b".repeat(40),
    fingerprint = "c".repeat(64),
    at = "2026-10-20T12:00:00Z";
const original = {
    schema_version: 1,
    operation_id: id,
    principal: "rest-writer",
    route: "/api/v1/syncs",
    archive_id: ARCHIVE_ID,
    config_fingerprint: fingerprint,
    state: "queued",
    created_at: at,
    updated_at: at,
    completed_at: null,
    domain_run_id: null,
    transaction_ids: [],
    next_event_sequence: 1,
    result_recorded: false,
};
const operation = decodeClientOperation(
    parseWireJson(JSON.stringify(original)),
);
function client(fetcher: typeof fetch, writer = true, timeoutMs = 1000) {
    return createApiClient({
        scope: createApiScope({
            origin: "https://archive.invalid",
            publicPrefix: "/management",
            authorityEpoch: "test-epoch",
            subject: "test-subject",
            credentialClass: writer ? "rest-writer" : "rest-reader",
            instanceId: null,
            archiveId: null,
            configFingerprint: null,
        }),
        fetcher,
        timeoutMs,
    });
}
type ReadInvocation = (api: ApiClient) => Promise<{ readonly kind: string }>;
const reads: readonly (readonly [string, ReadInvocation])[] = [
    ["/health", (api) => api.readHealth()],
    ["/repositories", (api) => api.readRepositories()],
    ["/repositories/revisions", (api) => api.readRevisions()],
    ["/verification/estimate", (api) => api.readVerificationEstimate()],
    ["/runs", (api) => api.readRuns()],
    ["/runs/" + id, (api) => api.readReport(id)],
    [
        "/repositories/model/org/name/references/current",
        (api) => api.readReference("model", "org/name", "current"),
    ],
    [
        "/repositories/model/org/name/manifests/" + sha + "/" + id,
        (api) =>
            api.readManifest({
                repositoryType: "model",
                repositoryId: "org/name",
                commitSha: sha,
                publicationId: id,
            }),
    ],
    ["/operations", (api) => api.readOperations()],
    ["/operations/lookup", (api) => api.lookupOperation("original-key")],
    ["/operations/" + id, (api) => api.readOperation(id)],
    [
        "/operations/" + id + "/events",
        (api) => api.readOperationEvents(operation),
    ],
    [
        "/operations/" + id + "/result",
        (api) => api.readOperationResult(operation),
    ],
    ["/catalog/search", (api) => api.readCatalogSearch()],
    ["/catalog/facets", (api) => api.readCatalogFacets()],
    [
        "/catalog/repositories/model/org/name",
        (api) => api.readCatalogDetail("model", "org/name"),
    ],
    [
        "/catalog/repositories/model/org/name/variants",
        (api) => api.readCatalogVariants("model", "org/name"),
    ],
    ["/config/validate", (api) => api.validateInstalledConfiguration()],
    [
        "/config/validate",
        (api) =>
            api.validateCandidateConfiguration({
                candidate: "schema_version=1",
            }),
    ],
];
test.each(reads)(
    "fixed read %s validates and retains an API problem without replay",
    async (path, invoke) => {
        const fetcher = vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(problemWire("HFAPI019", 20), 503));
        expect(await invoke(client(fetcher))).toMatchObject({
            kind: "api_problem",
            status: 503,
            problem: { code: "HFAPI019", exit_code: 20 },
        });
        expect(fetcher).toHaveBeenCalledOnce();
        const [url] = fetcher.mock.calls[0] ?? [];
        expect(url instanceof URL ? url.pathname : "").toBe(
            "/management/api/v1" + path,
        );
    },
);
type SubmitInvocation = (
    api: ApiClient,
    options: SubmissionOptions,
) => Promise<{ readonly kind: string }>;
const submits: readonly (readonly [string, SubmitInvocation])[] = [
    [
        "/syncs",
        (api, options) =>
            api.submitSync({ selectors: ["model:org/name"] }, options),
    ],
    ["/plans", (api, options) => api.submitInstalledPlan({}, options)],
    [
        "/plans",
        (api, options) =>
            api.submitCandidatePlan({ candidate: "schema_version=1" }, options),
    ],
    [
        "/diagnostics",
        (api, options) =>
            api.submitReadOnlyDiagnostics({ read_only: true }, options),
    ],
    [
        "/diagnostics",
        (api, options) =>
            api.submitProbeDiagnostics({ read_only: false }, options),
    ],
    [
        "/verifications",
        (api, options) => api.submitNewVerification({ mode: "new" }, options),
    ],
    [
        "/verifications",
        (api, options) => api.submitFullVerification({ mode: "full" }, options),
    ],
    [
        "/verifications",
        (api, options) =>
            api.submitRevisionVerification(
                { mode: "revision", revision: "model:org/name@" + sha },
                options,
            ),
    ],
    ["/prune-plans", (api, options) => api.submitPrunePreview({}, options)],
    ["/prunes", (api, options) => api.submitPruneApply({}, options)],
    [
        "/purge-plans",
        (api, options) =>
            api.submitPurgePreview({ all_unmanaged: true }, options),
    ],
    [
        "/purges",
        (api, options) =>
            api.submitPurgeApply({ selectors: ["model:org/name"] }, options),
    ],
    [
        "/recovery-plans",
        (api, options) => api.submitRecoveryPreview({}, options),
    ],
    ["/recoveries", (api, options) => api.submitRecoveryApply({}, options)],
    [
        "/quarantine-plans",
        (api, options) =>
            api.submitQuarantinePreview({ transaction_ids: [id] }, options),
    ],
    [
        "/quarantine-cleanups",
        (api, options) =>
            api.submitQuarantineApply({ transaction_ids: [id] }, options),
    ],
    [
        "/repairs",
        (api, options) =>
            api.submitRepair({ revision: "model:org/name@" + sha }, options),
    ],
    [
        "/catalog/refreshes",
        (api, options) => api.submitCatalogRefresh({}, options),
    ],
];
function acceptance(path: string, change: object = {}) {
    const status = "/management/api/v1/operations/" + id;
    return {
        schema_version: 1,
        request_id: "d".repeat(32),
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
        operation: { ...original, route: "/api/v1" + path },
        created: true,
        links: {
            status,
            result: status + "/result",
            events: status + "/events",
        },
        ...change,
    };
}
test.each(submits)(
    "named submission %s retains the original key and validates exact receipt links",
    async (path, invoke) => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            new Response(JSON.stringify(acceptance(path)), {
                status: 202,
                headers: {
                    "Content-Type": "application/json",
                    Location: "/management/api/v1/operations/" + id,
                },
            }),
        );
        expect(
            await invoke(client(fetcher), { idempotencyKey: "retained-key" }),
        ).toMatchObject({
            kind: "accepted",
            idempotencyKey: "retained-key",
            route: "/api/v1" + path,
        });
        expect(fetcher).toHaveBeenCalledOnce();
        const [, options] = fetcher.mock.calls[0] ?? [];
        expect(new Headers(options?.headers).get("Idempotency-Key")).toBe(
            "retained-key",
        );
        expect(new Headers(options?.headers).get("X-Hfcache-Request")).toBe(
            "1",
        );
    },
);
test.each(["\n", "\r", "\r\n", "\u2028", "\u2029"])(
    "malformed original-key suffix refuses before any POST %s",
    async (suffix) => {
        const fetcher = vi.fn<typeof fetch>();
        expect(
            await client(fetcher).submitSync(
                {},
                { idempotencyKey: "original" + suffix },
            ),
        ).toEqual({ kind: "refused", reason: "schema" });
        expect(fetcher).not.toHaveBeenCalled();
    },
);
test("reader scope and malformed request refuse before transmission", async () => {
    const fetcher = vi.fn<typeof fetch>();
    expect(
        await client(fetcher, false).submitSync(
            {},
            { idempotencyKey: "original" },
        ),
    ).toEqual({ kind: "refused", reason: "authority" });
    expect(
        await client(fetcher).submitSync(
            { selectors: ["invalid"] },
            { idempotencyKey: "original" },
        ),
    ).toEqual({ kind: "refused", reason: "schema" });
    expect(fetcher).not.toHaveBeenCalled();
});
test.each([
    [
        "/plans",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitInstalledPlan({}, options),
    ],
    [
        "/diagnostics",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitReadOnlyDiagnostics({ read_only: true }, options),
    ],
    [
        "/prune-plans",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitPrunePreview({}, options),
    ],
    [
        "/purge-plans",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitPurgePreview({ all_unmanaged: true }, options),
    ],
    [
        "/recovery-plans",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitRecoveryPreview({}, options),
    ],
    [
        "/quarantine-plans",
        (api: ApiClient, options: SubmissionOptions) =>
            api.submitQuarantinePreview({ transaction_ids: [id] }, options),
    ],
] as const)(
    "reader-authorized %s preview retains keyed admission",
    async (path, invoke) => {
        const accepted = acceptance(path, {
            operation: {
                ...original,
                route: "/api/v1" + path,
                principal: "rest-reader",
            },
        });
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            new Response(JSON.stringify(accepted), {
                status: 202,
                headers: {
                    "Content-Type": "application/json",
                    Location: "/management/api/v1/operations/" + id,
                },
            }),
        );
        expect(
            await invoke(client(fetcher, false), {
                idempotencyKey: "reader-preview-original",
            }),
        ).toMatchObject({
            kind: "accepted",
            route: "/api/v1" + path,
            idempotencyKey: "reader-preview-original",
        });
        expect(fetcher).toHaveBeenCalledOnce();
    },
);
test("reader cannot admit literal candidate planning or diagnostic probes", async () => {
    const fetcher = vi.fn<typeof fetch>(),
        api = client(fetcher, false),
        options = { idempotencyKey: "original" };
    expect(
        await api.submitCandidatePlan(
            { candidate: "schema_version=1" },
            options,
        ),
    ).toEqual({ kind: "refused", reason: "authority" });
    expect(
        await api.submitProbeDiagnostics({ read_only: false }, options),
    ).toEqual({ kind: "refused", reason: "authority" });
    expect(fetcher).not.toHaveBeenCalled();
});
test.each(["network", "protocol", "timeout", "aborted"] as const)(
    "post-transmission %s retains the original route/key as uncertainty and never replays",
    async (reason) => {
        const controller = new AbortController();
        const fetcher = vi
            .fn<typeof fetch>()
            .mockImplementation(async (_url, options) => {
                if (reason === "network") throw new TypeError("offline");
                if (reason === "protocol") return jsonResponse({}, 202);
                if (reason === "aborted") controller.abort();
                return await new Promise<Response>((_resolve, reject) => {
                    const fail = () => {
                        reject(new DOMException("Aborted", "AbortError"));
                    };
                    options?.signal?.addEventListener("abort", fail, {
                        once: true,
                    });
                    if (options?.signal?.aborted === true) fail();
                });
            });
        expect(
            await client(fetcher, true, 5).submitSync(
                {},
                { idempotencyKey: "original", signal: controller.signal },
            ),
        ).toEqual({
            kind: "uncertain",
            route: "/api/v1/syncs",
            idempotencyKey: "original",
            reason,
        });
        expect(fetcher).toHaveBeenCalledOnce();
    },
);
test("accepted HTTP transport with a mismatched original route remains uncertain", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify(acceptance("/plans")), {
            status: 202,
            headers: {
                "Content-Type": "application/json",
                Location: "/management/api/v1/operations/" + id,
            },
        }),
    );
    expect(
        await client(fetcher).submitSync({}, { idempotencyKey: "original" }),
    ).toMatchObject({ kind: "uncertain", reason: "protocol" });
});
test("an API admission refusal remains a classified problem", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire(), 403));
    expect(
        await client(fetcher).submitSync({}, { idempotencyKey: "original" }),
    ).toMatchObject({ kind: "api_problem", status: 403 });
});
test("unsupported failed payload retains exact validated domain identity but withholds data", async () => {
    const wire = readWire("version", { unexpected: "rejected" }, true);
    const result = await client(
        vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(wire)),
    ).readVersion();
    expect(result).toMatchObject({
        kind: "protocol_failure",
        preserved: {
            request_id: wire.request_id,
            run_id: wire.envelope.run_id,
            started_at: wire.envelope.started_at,
            completed_at: wire.envelope.completed_at,
            outcome: "failed",
            schema_version: 1,
        },
    });
    expect(result).not.toHaveProperty("payload");
});
test("historical operation identity survives a changed installed fingerprint without rebinding its archive", async () => {
    const terminal = decodeClientOperation(
        parseWireJson(
            JSON.stringify({
                ...original,
                state: "failed",
                completed_at: at,
                domain_run_id: "3".repeat(32),
                result_recorded: true,
            }),
        ),
    );
    const responses = [
        readWire("operations show", { operation: original }),
        readWire("operations lookup", { operation: original }),
        readWire("operations events", {
            operation_id: id,
            events: [],
            next_cursor: 0,
            oldest_sequence: 1,
            truncated: false,
        }),
        readWire("sync", {}, true),
    ];
    const fetcher = vi.fn<typeof fetch>();
    for (const response of responses)
        fetcher.mockResolvedValueOnce(
            jsonResponse({
                ...response,
                archive_id: ARCHIVE_ID,
                config_fingerprint: fingerprint,
            }),
        );
    const api = createApiClient({
        scope: createApiScope({
            origin: "https://archive.invalid",
            publicPrefix: "",
            authorityEpoch: "changed-policy",
            subject: "same-reader",
            credentialClass: "rest-writer",
            instanceId: null,
            archiveId: ARCHIVE_ID,
            configFingerprint: "f".repeat(64),
        }),
        fetcher,
    });
    expect((await api.readOperation(id)).kind).toBe("success");
    expect((await api.lookupOperation("retained-key")).kind).toBe("success");
    expect((await api.readOperationEvents(operation)).kind).toBe("success");
    expect((await api.readOperationResult(terminal)).kind).toBe(
        "domain_failure",
    );
    const different = {
        ...readWire("operations show", { operation: original }),
        archive_id: "00000000-0000-0000-0000-000000000000",
        config_fingerprint: fingerprint,
    };
    fetcher.mockResolvedValueOnce(jsonResponse(different));
    expect((await api.readOperation(id)).kind).toBe("protocol_failure");
});
