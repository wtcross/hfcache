import { expect, test } from "vitest";
import {
    applySemantic,
    compareCodePoints,
    compareTimestamps,
    timestampParts,
} from "../src/wire/semantics";
import { WireError, parseWireJson } from "../src/wire/json";
import {
    decodeNamed,
    routeContracts,
    decodeOriginalOperationPayload,
} from "../src/wire/generated";
import { buildRequestInput, serializeRequestJson } from "../src/api/request";

const at = "2026-10-20T10:11:12.123456Z";
const envelope = {
    schema_version: 1,
    exit_code: 0,
    outcome: "success",
    warnings: [],
    errors: [],
    started_at: at,
    completed_at: at,
};
const row = { repository_type: "model", repository_id: "org/name" };
const cases: readonly (readonly [string, unknown, unknown])[] = [
    ["hfcache.client_models.exact_version", 1, true],
    [
        "hfcache.models.VersionedModel._check_schema_version",
        { schema_version: 1 },
        { schema_version: 2 },
    ],
    [
        "hfcache.client_models.ClientEvent.timestamp",
        { at },
        { at: "2026-02-31T00:00:00Z" },
    ],
    [
        "hfcache.client_models.ClientRead.required_envelope_version",
        { envelope },
        { envelope: { schema_version: 2 } },
    ],
    [
        "hfcache.client_models.ClientRead.coherent_envelope",
        { envelope },
        {
            envelope: {
                ...envelope,
                completed_at: "2026-10-20T10:11:12.123455Z",
            },
        },
    ],
    [
        "hfcache.client_models.Acceptance.identity",
        {
            archive_id: "a",
            config_fingerprint: "f",
            operation: { archive_id: "a", config_fingerprint: "f" },
        },
        {
            archive_id: "a",
            config_fingerprint: "f",
            operation: { archive_id: "b", config_fingerprint: "f" },
        },
    ],
    [
        "hfcache.client_models.Capabilities.permissions",
        { credential_class: "rest-writer", capabilities: ["write", "read"] },
        { credential_class: "rest-reader", capabilities: ["write"] },
    ],
    [
        "hfcache.reporting.Envelope._check",
        envelope,
        { ...envelope, exit_code: 10, outcome: "failed" },
    ],
    [
        "hfcache.reporting.RunEnvelope._check_envelope",
        envelope,
        { ...envelope, outcome: "success_with_warnings" },
    ],
    [
        "hfcache.reporting.RunReport._check",
        { repositories: [row] },
        { repositories: [row, row] },
    ],
    [
        "hfcache.reporting.RepositoryRunResult._check",
        { status: "published", publication_id: "p", errors: [], warnings: [] },
        { status: "published", publication_id: null, errors: [], warnings: [] },
    ],
    [
        "hfcache.reporting.VerificationReport._check",
        { verification_outcome: "clean", findings: [] },
        { verification_outcome: "failed", findings: [] },
    ],
    [
        "hfcache.reporting.Finding._check",
        {
            commit_sha: null,
            kind: "ref_invalid",
            publication_id: null,
            path: null,
        },
        { commit_sha: null, kind: "missing", publication_id: null, path: null },
    ],
    [
        "hfcache.reporting.RecoveryReport._check",
        { remediations: [{ transaction_id: "a" }, { transaction_id: "b" }] },
        { remediations: [{ transaction_id: "b" }, { transaction_id: "a" }] },
    ],
    [
        "hfcache.models.PrunePlan._check",
        {
            retained: [{ publication_generation: 2 }],
            selected: { publication_generation: 2, commit_sha: "a" },
            current: { commit_sha: "b" },
        },
        {
            retained: [],
            selected: { publication_generation: 1, commit_sha: "a" },
            current: { commit_sha: "b" },
        },
    ],
    [
        "hfcache.models.PurgePlan._check",
        {
            revisions: [
                {
                    publication_generation: 1,
                    commit_sha: "a",
                    logical_bytes: 2,
                },
            ],
            cache_revisions_to_delete: ["a"],
            current: { publication_generation: 1, commit_sha: "a" },
            unique_bytes_released_estimate: 2,
        },
        {
            revisions: [],
            cache_revisions_to_delete: [],
            current: {},
            unique_bytes_released_estimate: 0,
        },
    ],
    [
        "hfcache.api.command_models._selection",
        "model:org/name",
        "model:org/name@" + "a".repeat(40),
    ],
    [
        "hfcache.api.maintenance_models._whole_repository",
        "dataset:org/name",
        "dataset:org/name@" + "a".repeat(40),
    ],
    ["hfcache.api.command_models._candidate_text", "enabled=true", ""],
    [
        "hfcache.api.command_models.SyncSubmission.canonical",
        { selectors: ["a", "b"] },
        { selectors: ["a", "a"] },
    ],
    [
        "hfcache.api.command_models.PlanSubmission.explicit_candidate",
        {},
        { candidate: null },
    ],
    [
        "hfcache.api.command_models.ValidationSubmission.explicit_candidate",
        {},
        { candidate: null },
    ],
    [
        "hfcache.api.command_models.VerificationSubmission.scope",
        { mode: "revision", revision: "model:org/name@" + "a".repeat(40) },
        { mode: "full", run_id: "a".repeat(32) },
    ],
    [
        "hfcache.api.command_models.CatalogRefreshSubmission.canonical",
        { selectors: [], tags: true, technical: false },
        { selectors: [], tags: false, technical: false },
    ],
    [
        "hfcache.api.maintenance_models.PurgeSubmission.scope",
        { selectors: ["model:org/name"], all_unmanaged: false },
        { selectors: [], all_unmanaged: false },
    ],
    [
        "hfcache.api.maintenance_models.QuarantineSubmission.canonical",
        { transaction_ids: ["a", "b"] },
        { transaction_ids: ["b", "a"] },
    ],
    [
        "hfcache.api.maintenance_models.RepairSubmission.scope",
        { revision: "dataset:org/name@" + "a".repeat(40) },
        { revision: "dataset:org/name" },
    ],
    [
        "hfcache.api.maintenance_models.InitializationSubmission.confirmation",
        { confirm: true },
        { confirm: false },
    ],
    [
        "hfcache.api.maintenance_models._archive_root",
        "/owned/archive",
        "/owned/../archive",
    ],
];
test.each(cases)(
    "audited semantic %s accepts coherent data and refuses its independent contradiction",
    (id, good, bad) => {
        expect(() => {
            applySemantic(id, good);
        }).not.toThrow();
        expect(() => {
            applySemantic(id, bad);
        }).toThrow(WireError);
    },
);
test.each([
    "hfcache.identity.parse_run_id",
    "hfcache.identity.parse_transaction_id",
    "hfcache.identity.parse_publication_id",
])("canonical identifier %s is a complete lowercase token", (id) => {
    applySemantic(id, "a".repeat(32));
    for (const suffix of ["\n", "\r", "\r\n", "\u2028", "\u2029"])
        expect(() => {
            applySemantic(id, "a".repeat(32) + suffix);
        }).toThrow(WireError);
});
test.each([
    "hfcache.client_models._archive_id",
    "hfcache.models._parse_archive_id",
    "hfcache.config._parse_archive_id",
])("UUID semantic %s keeps exact spelling", (id) => {
    applySemantic(id, "00000000-0000-0000-0000-000000000000");
    expect(() => {
        applySemantic(id, "00000000-0000-0000-0000-000000000000\n");
    }).toThrow(WireError);
});
test("SHA, type and repository hooks have exact boundaries", () => {
    applySemantic("hfcache.identity.parse_commit_sha", "a".repeat(40));
    applySemantic("hfcache.models._parse_sha256", "b".repeat(64));
    applySemantic("hfcache.identity.parse_repository_type", "dataset");
    applySemantic("hfcache.identity.parse_repository_id", "org/name");
    for (const [id, value] of [
        ["hfcache.identity.parse_commit_sha", "A".repeat(40)],
        ["hfcache.models._parse_sha256", "b".repeat(64) + "\n"],
        ["hfcache.identity.parse_repository_type", "models"],
        ["hfcache.identity.parse_repository_id", "org/name\n"],
    ])
        expect(() => {
            applySemantic(id ?? "", value);
        }).toThrow(WireError);
});
test.each([
    "2026-02-29T00:00:00Z",
    "2026-02-31T00:00:00Z",
    "0000-01-01T00:00:00Z",
    "2026-01-01T24:00:00Z",
    "2026-01-01T00:60:00Z",
    "2026-01-01T00:00:60Z",
    "2026-01-01T00:00:00+00:00",
    at + "\n",
])("timestamp refuses noncalendar/noncanonical text %s", (value) => {
    expect(() => timestampParts(value)).toThrow(WireError);
});
test("calendar leap boundaries and microsecond ordering retain precision", () => {
    expect(timestampParts("2000-02-29T00:00:00Z")).toEqual([
        2000, 2, 29, 0, 0, 0, 0,
    ]);
    expect(compareTimestamps(at, "2026-10-20T10:11:12.123455Z")).toBe(1);
    expect(compareTimestamps(at, at)).toBe(0);
    expect(compareTimestamps("2026-10-20T10:11:12.123455Z", at)).toBe(-1);
    applySemantic("timestamp.serialized", at);
    applySemantic("timestamp.wire", "2026-01-01T00:00:00Z");
    expect(() => {
        applySemantic("timestamp.serialized", "2026-01-01T00:00:00Z");
    }).toThrow(WireError);
    expect(compareCodePoints("\ue000", "😀")).toBe(-1);
    expect(compareCodePoints("a", "aa")).toBe(-1);
    expect(compareCodePoints("z", "a")).toBe(1);
    expect(compareCodePoints("a", "a")).toBe(0);
});
test("operation receipts require terminal evidence and supported original routes", () => {
    const operation = {
        state: "queued",
        route: "/api/v1/syncs",
        created_at: at,
        updated_at: at,
        completed_at: null,
        result_recorded: false,
        domain_run_id: null,
    };
    applySemantic("hfcache.client_models.ClientOperation.evidence", operation);
    applySemantic("hfcache.client_models.ClientOperation.evidence", {
        ...operation,
        state: "succeeded",
        completed_at: at,
        result_recorded: true,
        domain_run_id: "a",
    });
    for (const change of [
        { route: "/unsupported" },
        { completed_at: at },
        { updated_at: "2026-10-20T10:11:12.123455Z" },
        { state: "failed", completed_at: at },
        { state: "interrupted", completed_at: at, result_recorded: true },
    ])
        expect(() => {
            applySemantic("hfcache.client_models.ClientOperation.evidence", {
                ...operation,
                ...change,
            });
        }).toThrow(WireError);
});
test("closed generated payloads keep output defaults required and request omissions explicit", () => {
    expect(decodeNamed("EmptyPayload", parseWireJson("{}"))).toEqual({});
    expect(() =>
        decodeNamed("EmptyPayload", parseWireJson('{"extra":true}')),
    ).toThrow(WireError);
    expect(() => decodeNamed("missing", {})).toThrow(WireError);
    expect(
        routeContracts.plan_installed.decodeBody(parseWireJson("{}")),
    ).toEqual({});
    expect(() =>
        routeContracts.plan_literal_candidate.decodeBody(parseWireJson("{}")),
    ).toThrow(WireError);
    expect(() =>
        routeContracts.config_validate_literal_candidate.decodeBody(
            parseWireJson('{"candidate":null}'),
        ),
    ).toThrow(WireError);
    expect(() =>
        decodeOriginalOperationPayload("/unknown", "sync", false, {}),
    ).toThrow(WireError);
});
test("request builders explicitly normalize Python selector and transaction transformations", () => {
    expect(
        buildRequestInput("/api/v1/syncs", {
            selectors: [
                "model:z/z@" + "a".repeat(40),
                "dataset:a/a",
                "model:z/z",
            ],
        }),
    ).toEqual({ selectors: ["dataset:a/a", "model:z/z"] });
    expect(
        buildRequestInput("/api/v1/quarantine-plans", {
            transaction_ids: ["b".repeat(32), "a".repeat(32), "a".repeat(32)],
        }),
    ).toEqual({ transaction_ids: ["a".repeat(32), "b".repeat(32)] });
    expect(() =>
        buildRequestInput("/api/v1/catalog/refreshes", {
            selectors: ["model:z/z@" + "a".repeat(40)],
        }),
    ).toThrow(WireError);
});
test.each([
    undefined,
    NaN,
    Infinity,
    new Date(),
    { toJSON: () => null },
    { value: undefined },
    [undefined],
    new Array(1),
    Object.assign([1], { extra: 2 }),
])("request serialization refuses normalization hazards", (value) => {
    expect(() => serializeRequestJson(value)).toThrow(WireError);
});
test("request serialization refuses getters without invoking them and inertly preserves ordinary keys", () => {
    let invoked = false;
    const value = {};
    Object.defineProperty(value, "secret", {
        enumerable: true,
        get() {
            invoked = true;
            return "private";
        },
    });
    expect(() => serializeRequestJson(value)).toThrow(WireError);
    expect(invoked).toBe(false);
    expect(
        serializeRequestJson({
            zero: 0,
            no: false,
            empty: "",
            none: null,
            items: [1],
        }),
    ).toBe('{"zero":0,"no":false,"empty":"","none":null,"items":[1]}');
    expect(() => {
        applySemantic("unaudited", {});
    }).toThrow(WireError);
});
