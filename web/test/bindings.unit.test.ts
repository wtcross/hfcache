import { expect, test } from "vitest";
import {
    applyBindings,
    validateApiProblem,
    validateOperationTransition,
} from "../src/api/bindings";
import type { RequestBinding } from "../src/api/bindings";
import { decodeClientRead, decodeClientOperation } from "../src/wire/generated";
import type { ClientOperation } from "../src/wire/generated";
import { parseWireJson, WireError } from "../src/wire/json";
import { ARCHIVE_ID, readWire } from "./read-fixtures";

const run = "3".repeat(32),
    sha = "a".repeat(40),
    pub = "b".repeat(32),
    fingerprint = "c".repeat(64),
    at = "2026-10-20T12:00:00Z";
const operation = decodeClientOperation(
    parseWireJson(
        JSON.stringify({
            schema_version: 1,
            operation_id: "d".repeat(32),
            principal: "rest-writer",
            route: "/api/v1/syncs",
            archive_id: ARCHIVE_ID,
            config_fingerprint: fingerprint,
            state: "running",
            created_at: at,
            updated_at: at,
            completed_at: null,
            domain_run_id: run,
            transaction_ids: [],
            next_event_sequence: 1,
            result_recorded: false,
        }),
    ),
);
function response(payload: unknown, failed = false) {
    return decodeClientRead(
        parseWireJson(
            JSON.stringify({
                ...readWire("sync", payload, failed),
                archive_id: ARCHIVE_ID,
                config_fingerprint: fingerprint,
            }),
        ),
    );
}
function bind(
    id: string,
    payload: unknown,
    context: RequestBinding = {},
    failed = false,
) {
    applyBindings([id], response(payload, failed), context);
}
test("stored report identities bind requested run and wrapper archive", () => {
    const report = { command: "sync", run_id: run, archive_id: ARCHIVE_ID };
    bind("run.report", { report }, { runId: run });
    bind(
        "run.report",
        {
            report: {
                ...report,
                command: "verify --full",
                verification_outcome: "clean",
            },
        },
        { runId: run },
    );
    bind(
        "run.report",
        { report: { ...report, command: "recover --apply", remediations: [] } },
        { runId: run },
    );
    expect(() => {
        bind("run.report", { report }, { runId: "e".repeat(32) });
    }).toThrow(WireError);
    expect(() => {
        bind(
            "run.report",
            { report: { ...report, remediations: [] } },
            { runId: run },
        );
    }).toThrow(WireError);
    expect(() => {
        bind("run.report", {}, {}, true);
    }).not.toThrow();
});
test("reference identity binds exact repository revision and both original locators", () => {
    const reference = {
        repository_type: "model",
        repository_id: "org/name",
        commit_sha: sha,
        publication_id: pub,
        tree: `repos/models/org/name/revisions/${sha}/${pub}`,
        manifest: `manifests/models/org/name/${sha}/${pub}.json`,
    };
    const context = {
        repositoryType: "model",
        repositoryId: "org/name",
        revision: sha,
    } as const;
    bind(
        "publication.reference",
        { reference, locator_base: "published/" },
        context,
    );
    bind(
        "publication.reference",
        { reference, locator_base: "published/" },
        { ...context, revision: "current" },
    );
    expect(() => {
        bind(
            "publication.reference",
            {
                reference: { ...reference, publication_id: "e".repeat(32) },
                locator_base: "published/",
            },
            context,
        );
    }).toThrow(WireError);
    expect(() => {
        bind(
            "publication.reference",
            { reference, locator_base: "elsewhere/" },
            context,
        );
    }).toThrow(WireError);
    bind("publication.reference", {}, {}, true);
});
test("manifest identity includes publication ID and archive-root tree base", () => {
    const manifest = {
        repository_type: "dataset",
        repository_id: "org/name",
        commit_sha: sha,
        publication_id: pub,
        tree: `published/repos/datasets/org/name/revisions/${sha}/${pub}`,
    };
    const context = {
        repositoryType: "dataset",
        repositoryId: "org/name",
        commitSha: sha,
        publicationId: pub,
    } as const;
    bind(
        "publication.manifest",
        { manifest, tree_base: "archive-root/" },
        context,
    );
    expect(() => {
        bind(
            "publication.manifest",
            { manifest, tree_base: "published/" },
            context,
        );
    }).toThrow(WireError);
    expect(() => {
        bind(
            "publication.manifest",
            {
                manifest: { ...manifest, publication_id: "e".repeat(32) },
                tree_base: "archive-root/",
            },
            context,
        );
    }).toThrow(WireError);
    bind("publication.manifest", {}, {}, true);
});
test("operation wrapper and known original ID cannot be rebound", () => {
    bind(
        "operation.identity",
        { operation },
        { operationId: operation.operation_id },
    );
    bind("operation.identity", { operation });
    expect(() => {
        bind(
            "operation.identity",
            { operation },
            { operationId: "e".repeat(32) },
        );
    }).toThrow(WireError);
    expect(() => {
        bind("operation.identity", {
            operation: { ...operation, config_fingerprint: "e".repeat(64) },
        });
    }).toThrow(WireError);
    bind("operation.identity", {}, {}, true);
});
test("events are contiguous after original cursor with exact bounded truncation semantics", () => {
    const data = {
        operation_id: operation.operation_id,
        events: [{ sequence: 3 }, { sequence: 4 }],
        next_cursor: 4,
        oldest_sequence: 2,
        truncated: false,
    };
    bind("operation.events", data, { operation, after: 2, limit: 2 });
    bind(
        "operation.events",
        { ...data, events: [], next_cursor: 2 },
        { operation, after: 2 },
    );
    bind(
        "operation.events",
        { ...data, events: [{ sequence: 2 }], next_cursor: 2, truncated: true },
        { operation, after: 0 },
    );
    for (const change of [
        { events: [{ sequence: 4 }] },
        { next_cursor: 3 },
        { truncated: true },
        { operation_id: "e".repeat(32) },
    ])
        expect(() => {
            bind(
                "operation.events",
                { ...data, ...change },
                { operation, after: 2, limit: 2 },
            );
        }).toThrow(WireError);
    expect(() => {
        bind("operation.events", data, {});
    }).toThrow(WireError);
    bind("operation.events", {}, {}, true);
});
test("result state binds original domain run and receipt fingerprint", () => {
    const failed: ClientOperation = {
        ...operation,
        state: "failed",
        completed_at: at,
        result_recorded: true,
    };
    bind("operation.result", {}, { operation: failed }, true);
    bind(
        "operation.result",
        {},
        { operation: { ...failed, state: "succeeded" } },
    );
    expect(() => {
        bind("operation.result", {}, { operation: failed });
    }).toThrow(WireError);
    expect(() => {
        bind(
            "operation.result",
            {},
            { operation: { ...failed, domain_run_id: "e".repeat(32) } },
            true,
        );
    }).toThrow(WireError);
    expect(() => {
        bind("operation.result", {});
    }).toThrow(WireError);
    expect(() => {
        bind("unaudited", {});
    }).toThrow(WireError);
});
test("receipt observations preserve immutable identity and append-only transaction evidence", () => {
    validateOperationTransition(undefined, operation);
    validateOperationTransition(operation, {
        ...operation,
        transaction_ids: [pub],
    });
    const changes: readonly Partial<ClientOperation>[] = [
        { archive_id: "00000000-0000-0000-0000-000000000000" },
        { config_fingerprint: "e".repeat(64) },
        { route: "/api/v1/plans" },
        { principal: "rest-reader" },
        { domain_run_id: "e".repeat(32) },
    ];
    for (const change of changes)
        expect(() => {
            validateOperationTransition(operation, { ...operation, ...change });
        }).toThrow(WireError);
    expect(() => {
        validateOperationTransition(
            { ...operation, transaction_ids: [pub] },
            { ...operation, transaction_ids: [] },
        );
    }).toThrow(WireError);
    const terminal: ClientOperation = {
        ...operation,
        state: "succeeded",
        result_recorded: true,
        completed_at: at,
    };
    validateOperationTransition(terminal, terminal);
    expect(() => {
        validateOperationTransition(terminal, {
            ...terminal,
            updated_at: "2026-10-20T12:00:01Z",
        });
    }).toThrow(WireError);
});
test("known operation observations cannot regress state or original microsecond chronology", () => {
    const running = { ...operation, updated_at: "2026-10-20T12:00:00.000002Z" };
    expect(() => {
        validateOperationTransition(running, { ...running, state: "queued" });
    }).toThrow(WireError);
    expect(() => {
        validateOperationTransition(running, {
            ...running,
            state: "waiting_lock",
        });
    }).toThrow(WireError);
    expect(() => {
        validateOperationTransition(running, {
            ...running,
            updated_at: "2026-10-20T12:00:00.000001Z",
        });
    }).toThrow(WireError);
    expect(() => {
        validateOperationTransition(running, {
            ...running,
            created_at: "2026-10-20T11:59:59Z",
        });
    }).toThrow(WireError);
    validateOperationTransition(
        { ...running, state: "queued" },
        {
            ...running,
            state: "succeeded",
            completed_at: running.updated_at,
            result_recorded: true,
        },
    );
    validateOperationTransition(
        { ...running, state: "waiting_lock" },
        { ...running, state: "running" },
    );
    validateOperationTransition(
        { ...running, state: "running", updated_at: at },
        running,
    );
});
test.each([
    ["HFCFG999", 10],
    ["HFARG999", 10],
    ["HFAPI019", 20],
    ["HFHUB999", 30],
    ["HFVER999", 40],
    ["HFRET999", 50],
] as const)(
    "future diagnostic family %s preserves classification",
    (code, exit_code) => {
        validateApiProblem({
            request_id: run,
            code,
            exit_code,
            message: "bounded plain detail",
        });
    },
);
test.each([
    ["HFCFG999", 20],
    ["HFAPI019", 10],
    ["HFWRN001", 0],
    ["unknown!", 10],
    ["HFCFG99\n", 10],
] as const)("incoherent API problem %s refuses", (code, exit_code) => {
    expect(() => {
        validateApiProblem({
            request_id: run,
            code,
            exit_code,
            message: "detail",
        });
    }).toThrow(WireError);
});
