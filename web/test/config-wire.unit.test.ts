import { readFileSync } from "node:fs";
import { expect, test } from "vitest";
import {
    decodeConfigRead,
    decodeManagedValidation,
    decodeManagedAssessment,
    decodePlanResultPayload,
    decodeRequestManagedPlanRequest,
    routeContracts,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { isRecord } from "../src/wire/runtime";
import { buildRequestInput } from "../src/api/request";
import { createApiClient } from "../src/api/client";
import { jsonResponse, readWire } from "./read-fixtures";

const source: unknown = JSON.parse(
    readFileSync(
        new URL("../../tests/fixtures/web_wire/config.json", import.meta.url),
        "utf8",
    ),
);
function object(value: unknown): Record<string, unknown> {
    if (!isRecord(value)) throw new Error("fixture");
    return value;
}
const fixtures = object(source);
const wire = (value: unknown): unknown => parseWireJson(JSON.stringify(value));

test("original Python serialized public config fixtures decode without private candidate data", () => {
    expect(decodeConfigRead(wire(fixtures.read)).schema_version).toBe(1);
    expect(decodeManagedValidation(wire(fixtures.validation)).valid).toBe(true);
    expect(decodeManagedAssessment(wire(fixtures.assessment)).sizing).toBe(
        null,
    );
    expect(routeContracts.config_read_default.commands).toEqual([
        "config read",
    ]);
    expect(routeContracts.config_validate_managed.commands).toEqual([
        "config validate",
    ]);
    expect(routeContracts.plan_managed.commands).toEqual(["plan"]);
    for (const [key, decoder] of [
        ["read", decodeConfigRead],
        ["validation", decodeManagedValidation],
        ["assessment", decodeManagedAssessment],
    ] as const) {
        for (const field of [
            "candidate",
            "config_sha256",
            "token",
            "archive_root",
        ]) {
            expect(() =>
                decoder(
                    wire({ ...object(fixtures[key]), [field]: "not-public" }),
                ),
            ).toThrow();
        }
    }
});

test("schema, revisions and nonsecret field metadata cannot coerce or expand", () => {
    for (const schema_version of [true, "1", 2, null])
        expect(() =>
            decodeConfigRead(
                wire({ ...object(fixtures.read), schema_version }),
            ),
        ).toThrow();
    for (const base_revision of [
        "A".repeat(64),
        "a".repeat(63),
        "a".repeat(64) + "\n",
    ])
        expect(() =>
            decodeConfigRead(wire({ ...object(fixtures.read), base_revision })),
        ).toThrow();
    expect(() =>
        decodeConfigRead(
            wire({
                ...object(fixtures.read),
                editable_fields: ["hub.credential_name"],
            }),
        ),
    ).toThrow();
    const changed = {
        ...object(fixtures.read),
        protected_fields: [
            { field: "hub", description: "private arbitrary content" },
        ],
    };
    expect(() => decodeConfigRead(wire(changed))).toThrow();
});

test("managed request normalization uses existing tag rules without accepting mixed forms", () => {
    const raw = {
        managed: {
            base_revision: "a".repeat(64),
            edits: [
                {
                    kind: "repository-upsert",
                    repository: {
                        type: "model",
                        id: "organization/model",
                        tags: [" DATA ", "data", "Critical"],
                    },
                },
            ],
        },
    };
    const decoded = decodeRequestManagedPlanRequest(
        buildRequestInput("/api/v1/plans", raw),
    );
    const edit = decoded.managed.edits[0];
    expect(edit?.kind).toBe("repository-upsert");
    if (edit?.kind !== "repository-upsert") throw new Error("fixture");
    expect(edit.repository.tags).toEqual(["critical", "data"]);
    for (const extra of [
        { candidate: "schema_version=1" },
        { managed: null },
        { selectors: ["model:organization/subset"] },
    ]) {
        expect(() =>
            decodeRequestManagedPlanRequest(
                wire({ ...object(fixtures.request), ...extra }),
            ),
        ).toThrow();
    }
    const managed = object(object(fixtures.request).managed);
    const badEdits = [
        [{ kind: "settings-replace", settings: { sync: {} } }],
        [
            {
                kind: "settings-replace",
                settings: { sync: { max_workers: null } },
            },
        ],
        [
            {
                kind: "settings-replace",
                settings: { storage: { archive_root: "/tmp/no" } },
            },
        ],
        [
            {
                kind: "settings-replace",
                settings: { sync: { max_workers: "2" } },
            },
        ],
        [{ kind: "unknown" }],
    ];
    for (const edits of badEdits)
        expect(() =>
            decodeRequestManagedPlanRequest(
                wire({ managed: { ...managed, edits } }),
            ),
        ).toThrow();
});

test("legacy plans and explicit empty managed assessments retain distinct exact shapes", () => {
    expect(decodePlanResultPayload(wire({ repositories: [] }))).toEqual({
        repositories: [],
    });
    expect(decodePlanResultPayload(wire(fixtures.assessment))).toEqual(
        fixtures.assessment,
    );
    expect(() =>
        decodeManagedAssessment(
            wire({
                ...object(fixtures.assessment),
                sizing: { repositories: [] },
            }),
        ),
    ).toThrow();
    expect(() =>
        decodeManagedAssessment(
            wire({
                ...object(fixtures.assessment),
                required_selectors: ["model:organization/new"],
            }),
        ),
    ).toThrow();
    const request = { managed: { base_revision: "a".repeat(64), edits: [] } };
    expect(routeContracts.plan_managed.decodeBody(wire(request))).toEqual(
        request,
    );
    expect(routeContracts.plan_installed.decodeBody(wire({}))).toEqual({});
    expect(
        routeContracts.plan_literal_candidate.decodeBody(
            wire({ candidate: "schema_version=1" }),
        ),
    ).toEqual({ candidate: "schema_version=1" });
});

test("typed config reads bind archive and managed validation binds the original base", async () => {
    function client(payload: unknown, command: string) {
        const response = {
            ...readWire(command, payload),
            archive_id: object(fixtures.read).archive_id,
            config_fingerprint: "c".repeat(64),
        };
        return createApiClient({
            scope: {
                origin: "https://archive.invalid",
                publicPrefix: "",
                authorityEpoch: "test",
                subject: "test",
                credentialClass: "rest-writer",
                instanceId: null,
                archiveId: null,
                configFingerprint: null,
            },
            fetcher: () => Promise.resolve(jsonResponse(response)),
        });
    }
    expect(
        (await client(fixtures.read, "config read").readConfiguration()).kind,
    ).toBe("success");
    expect(
        (
            await client(
                {
                    ...object(fixtures.read),
                    archive_id: "e046da76-d3cb-460a-a655-fd31bd9d0503",
                },
                "config read",
            ).readConfiguration()
        ).kind,
    ).toBe("protocol_failure");
    const request = { managed: { base_revision: "a".repeat(64), edits: [] } };
    expect(
        (
            await client(
                fixtures.validation,
                "config validate",
            ).validateManagedConfiguration(request)
        ).kind,
    ).toBe("success");
    expect(
        (
            await client(
                {
                    ...object(fixtures.validation),
                    base_revision: "d".repeat(64),
                },
                "config validate",
            ).validateManagedConfiguration(request)
        ).kind,
    ).toBe("protocol_failure");
});

test("complete managed sizing requires the whole derived scope and every metric", () => {
    const repository = {
        enabled: true,
        estimated_new_bytes: 0,
        file_count: 1,
        logical_bytes: 5,
        projected_publication_bytes: 5,
        publication_mode: "hardlink",
        repository_id: "organization/new",
        repository_type: "model",
        requested_revision: "main",
        resolved_commit_sha: "b".repeat(40),
        upstream_state: "available",
    };
    const assessment = {
        ...object(fixtures.assessment),
        required_selectors: ["model:organization/new"],
        sizing: { repositories: [repository] },
    };
    expect(decodeManagedAssessment(wire(assessment)).complete).toBe(true);
    for (const sizing of [
        { repositories: [] },
        { repositories: [repository, repository] },
        { repositories: [{ ...repository, file_count: null }] },
        { repositories: [{ ...repository, upstream_state: "unreachable" }] },
    ]) {
        expect(() =>
            decodeManagedAssessment(wire({ ...assessment, sizing })),
        ).toThrow();
    }
    expect(
        decodeManagedAssessment(
            wire({ ...assessment, complete: false, sizing: null }),
        ).complete,
    ).toBe(false);
});
