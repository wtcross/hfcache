/** WEB015: editable intent remains complete, bounded and independent of private authority. */
import { expect, test, vi } from "vitest";
import {
    ConfigurationDraftError,
    MAX_DRAFT_BYTES,
    defaultRepository,
    prepareDraft,
    prepareDraftJson,
    removeRepository,
    upsertRepository,
} from "../src/configuration/draft";
import { decodeConfigRead } from "../src/wire/generated";
import type { ConfigRead, EditableConfig } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import fixtures from "../../tests/fixtures/web_wire/config.json";

function base(): ConfigRead {
    return decodeConfigRead(parseWireJson(JSON.stringify(fixtures.read)));
}
function originalRepository() {
    const entry = base().editable.repositories[0];
    if (entry === undefined) throw new Error("Owned fixture entry missing.");
    return entry;
}
function expectError(
    action: () => unknown,
    reason: ConfigurationDraftError["reason"],
    field: string,
) {
    try {
        action();
        throw new Error("Expected draft refusal.");
    } catch (error) {
        expect(error).toBeInstanceOf(ConfigurationDraftError);
        if (!(error instanceof ConfigurationDraftError)) throw error;
        expect(error.reason).toBe(reason);
        expect(error.field).toBe(field);
        expect(error.message).not.toContain("owned-private-canary");
    }
}

test("unchanged editable intent is a frozen empty assessment bound to the original full-byte revision", () => {
    const source = base();
    const before = JSON.stringify(source);
    const prepared = prepareDraft(source, source.editable);
    expect(prepared).toMatchObject({
        dirty: false,
        diff: [],
        managed: { base_revision: source.base_revision, edits: [] },
    });
    expect(prepared.editable).toEqual(source.editable);
    expect(JSON.stringify(source)).toBe(before);
    expect(Object.isFrozen(prepared)).toBe(true);
    expect(Object.isFrozen(prepared.diff)).toBe(true);
    expect(Object.isFrozen(prepared.managed.edits)).toBe(true);
    expect(JSON.stringify(prepared)).not.toContain("protected_fields");
    expect(JSON.stringify(prepared)).not.toContain("archive_root");
});
test("new model and dataset entries use complete explicit defaults without conflating their identities", () => {
    const model = defaultRepository("model", "owned/shared");
    const dataset = defaultRepository("dataset", "owned/shared");
    expect(model).toEqual({
        id: "owned/shared",
        type: "model",
        revision: "main",
        enabled: true,
        tags: [],
        declared_dependencies: [],
    });
    expect(dataset).toEqual({ ...model, type: "dataset" });
    const source = base();
    const desired = upsertRepository(
        upsertRepository(source.editable, model),
        dataset,
    );
    const prepared = prepareDraft(source, desired);
    expect(prepared.managed.edits).toEqual([
        { kind: "repository-upsert", repository: model },
        { kind: "repository-upsert", repository: dataset },
    ]);
    expect(Object.isFrozen(model.tags)).toBe(true);
});
test("tag-only upserts retain revision, disabled state and declared dependencies while normalizing raw tags", () => {
    const entry = {
        ...originalRepository(),
        revision: "release/v2",
        enabled: false,
        declared_dependencies: ["owned/dependency"],
    };
    const source = {
        ...base(),
        editable: { ...base().editable, repositories: [entry] },
    };
    const input = { ...entry, tags: [" GPU ", "gpu", "team:Research"] };
    const desired = upsertRepository(source.editable, input);
    const prepared = prepareDraft(source, desired);
    const normalized = { ...entry, tags: ["gpu", "team:research"] };
    expect(prepared.editable.repositories).toEqual([normalized]);
    expect(prepared.managed.edits).toEqual([
        { kind: "repository-upsert", repository: normalized },
    ]);
    expect(prepared.diff).toEqual([
        {
            kind: "repository",
            field: "repositories",
            repositoryType: "model",
            repositoryId: entry.id,
            before: entry,
            after: normalized,
        },
    ]);
    expect(input.tags).toEqual([" GPU ", "gpu", "team:Research"]);
});
test("spelling-only tag normalization does not fabricate a dirty draft or an empty settings edit", () => {
    const source = base();
    const desired = {
        ...source.editable,
        repositories: [
            { ...originalRepository(), tags: [" CODING ", "coding"] },
        ],
    };
    expect(prepareDraft(source, desired)).toMatchObject({
        dirty: false,
        diff: [],
        managed: { edits: [] },
    });
});
test("mixed settings, removal, update and additions have deterministic order and complete reviewed entries", () => {
    const a = defaultRepository("model", "owned/a");
    const b = defaultRepository("dataset", "owned/b");
    const source = {
        ...base(),
        editable: { ...base().editable, repositories: [a, b] },
    };
    const updated = { ...b, enabled: false };
    const d = defaultRepository("model", "owned/d");
    const c = defaultRepository("model", "owned/c");
    const desired = {
        ...source.editable,
        storage: { ...source.editable.storage, maximum_revisions: 5 },
        repositories: [updated, d, c],
    };
    const result = prepareDraft(source, desired);
    expect(result.managed.edits).toEqual([
        {
            kind: "settings-replace",
            settings: { storage: { maximum_revisions: 5 } },
        },
        {
            kind: "repository-remove",
            repository_type: "model",
            repository_id: "owned/a",
        },
        { kind: "repository-upsert", repository: updated },
        { kind: "repository-upsert", repository: d },
        { kind: "repository-upsert", repository: c },
    ]);
    expect(result.diff[0]).toEqual({
        kind: "setting",
        field: "storage.maximum_revisions",
        before: 3,
        after: 5,
    });
    expect(result.diff).toHaveLength(5);
    expect(result.diff[1]).toMatchObject({ before: a, after: null });
    expect(JSON.stringify(prepareDraft(source, desired))).toBe(
        JSON.stringify(result),
    );
});
test("repository reorder and interleaved addition refuse rather than review an unattainable installed order", () => {
    const a = defaultRepository("model", "owned/a"),
        b = defaultRepository("model", "owned/b");
    const source = {
        ...base(),
        editable: { ...base().editable, repositories: [a, b] },
    };
    for (const repositories of [
        [b, a],
        [defaultRepository("model", "owned/new"), a, b],
    ])
        expectError(
            () => prepareDraft(source, { ...source.editable, repositories }),
            "order",
            "repositories",
        );
    expect(
        upsertRepository(source.editable, {
            ...a,
            enabled: false,
        }).repositories.map((row) => row.id),
    ).toEqual(["owned/a", "owned/b"]);
});
test("remove only changes configuration intent, and a missing or malformed identity is not silently adopted", () => {
    const source = base();
    const entry = originalRepository();
    const desired = removeRepository(source.editable, entry.type, entry.id);
    expect(prepareDraft(source, desired).managed.edits).toEqual([
        {
            kind: "repository-remove",
            repository_type: entry.type,
            repository_id: entry.id,
        },
    ]);
    expect(source.editable.repositories).toHaveLength(1);
    expectError(
        () => removeRepository(source.editable, "dataset", entry.id),
        "missing",
        "repositories",
    );
    expectError(
        () =>
            removeRepository(
                source.editable,
                "model",
                "../owned-private-canary",
            ),
        "invalid",
        "repositories",
    );
});
test("incomplete upserts refuse rather than resetting the parts a tag editor omitted", () => {
    const source = base();
    expectError(
        () =>
            upsertRepository(source.editable, {
                id: originalRepository().id,
                type: "model",
                tags: ["gpu"],
            }),
        "invalid",
        "repositories",
    );
});

test.each([
    ["storage", "publication_mode", "copy", "owned-private-canary"],
    ["storage", "minimum_free_space_gib", 1048576, -1],
    ["storage", "minimum_free_space_percent", 100, 101],
    ["storage", "maximum_revisions", 5, 4],
    ["sync", "max_workers", 32, "4"],
    ["sync", "lock_wait_seconds", 86400, -1],
    ["sync", "continue_on_repository_error", false, 0],
    ["sync", "dependency_policy", "warn", "ignore"],
    ["sync", "stale_staging_age_hours", 8760, 0],
    ["verification", "lock_wait_seconds", 604800, 604801],
    ["repair", "retired_instance_grace_hours", 8760, 167],
] as const)(
    "the supported %s.%s setting uses generated strict constraints and a controlled error path",
    (table, key, valid, invalid) => {
        const source = base();
        const section = source.editable[table];
        const desired = {
            ...source.editable,
            [table]: { ...section, [key]: valid },
        };
        expect(prepareDraft(source, desired).editable[table]).toMatchObject({
            [key]: valid,
        });
        expectError(
            () =>
                prepareDraft(source, {
                    ...desired,
                    [table]: { ...section, [key]: invalid },
                }),
            "invalid",
            table + "." + key,
        );
    },
);
test("all changed settings are combined once and omit unchanged/empty tables", () => {
    const source = base();
    const desired = {
        ...source.editable,
        storage: {
            publication_mode: "copy",
            minimum_free_space_gib: 0,
            minimum_free_space_percent: 0,
            maximum_revisions: 5,
        },
        sync: {
            max_workers: 8,
            lock_wait_seconds: 120,
            continue_on_repository_error: false,
            dependency_policy: "warn",
            stale_staging_age_hours: 48,
        },
        verification: { lock_wait_seconds: 0 },
        repair: { retired_instance_grace_hours: 336 },
    };
    const result = prepareDraft(source, desired);
    expect(result.managed.edits).toHaveLength(1);
    expect(result.managed.edits[0]).toMatchObject({
        kind: "settings-replace",
        settings: {
            storage: desired.storage,
            verification: desired.verification,
            repair: desired.repair,
        },
    });
    expect(result.diff).toHaveLength(10); // dependency_policy has only one supported value.
    expect(JSON.stringify(result.managed)).not.toContain("dependency_policy");
});
test("protected values, extra tables, missing settings and nulls never enter a diff", () => {
    const source = base();
    for (const desired of [
        { ...source.editable, hub: { token: "owned-private-canary" } },
        {
            ...source.editable,
            storage: {
                ...source.editable.storage,
                archive_root: "owned-private-canary",
            },
        },
        { ...source.editable, verification: { lock_wait_seconds: null } },
        { ...source.editable, sync: {} },
    ])
        expect(() => prepareDraft(source, desired)).toThrow(
            ConfigurationDraftError,
        );
});
test("raw tag limits are enforced before normalization and duplicate removal", () => {
    const source = base();
    for (const tags of [
        Array.from({ length: 65 }, () => "gpu"),
        [" ".repeat(128) + "g"],
        ["gpu\t"],
        ["é"],
        [""],
    ])
        expectError(
            () =>
                prepareDraft(source, {
                    ...source.editable,
                    repositories: [{ ...originalRepository(), tags }],
                }),
            "invalid",
            "repositories.0.tags",
        );
});
test("duplicate repository identities and dependencies refuse, while same ID across types remains distinct", () => {
    const source = base();
    const entry = originalRepository();
    expectError(
        () =>
            prepareDraft(source, {
                ...source.editable,
                repositories: [entry, entry],
            }),
        "duplicate",
        "repositories.1",
    );
    expectError(
        () =>
            prepareDraft(source, {
                ...source.editable,
                repositories: [
                    {
                        ...entry,
                        declared_dependencies: ["owned/base", "owned/base"],
                    },
                ],
            }),
        "invalid",
        "repositories.0.declared_dependencies",
    );
    const added = defaultRepository("dataset", entry.id);
    expect(
        prepareDraft(source, upsertRepository(source.editable, added)).managed
            .edits,
    ).toEqual([{ kind: "repository-upsert", repository: added }]);
});
test("256 edits is a request bound, not a limit on unchanged configured entries", () => {
    const empty: EditableConfig = { ...base().editable, repositories: [] };
    const source = { ...base(), editable: empty };
    const repositories = Array.from({ length: 257 }, (_, index) =>
        defaultRepository("model", "owned/repo-" + String(index)),
    );
    expect(
        prepareDraft(source, {
            ...empty,
            repositories: repositories.slice(0, 256),
        }).managed.edits,
    ).toHaveLength(256);
    expectError(
        () => prepareDraft(source, { ...empty, repositories }),
        "bounds",
        "repositories",
    );
    const unchanged = { ...source, editable: { ...empty, repositories } };
    expect(prepareDraft(unchanged, unchanged.editable).dirty).toBe(false);
    expectError(
        () =>
            prepareDraft(source, {
                ...empty,
                storage: { ...empty.storage, maximum_revisions: 5 },
                repositories: repositories.slice(0, 256),
            }),
        "bounds",
        "repositories",
    );
});
test("size/depth/work limits refuse before serialization or unbounded decoder walks", () => {
    const source = base();
    expectError(
        () =>
            prepareDraft(source, {
                ...source.editable,
                repositories: [
                    {
                        ...originalRepository(),
                        revision: "x".repeat(MAX_DRAFT_BYTES + 1),
                    },
                ],
            }),
        "bounds",
        "repositories.0.revision",
    );
    expectError(
        () =>
            prepareDraft(source, {
                ...source.editable,
                repositories: [
                    {
                        ...originalRepository(),
                        revision: "\u0000".repeat(350000),
                    },
                ],
            }),
        "bounds",
        "repositories.0.revision",
    );
    const huge: unknown[] = [];
    huge.length = 100000000;
    const getter = vi.fn(() => originalRepository());
    Object.defineProperty(huge, "0", { get: getter, enumerable: true });
    expectError(
        () => prepareDraft(source, { ...source.editable, repositories: huge }),
        "bounds",
        "repositories",
    );
    expect(getter).not.toHaveBeenCalled();
    const cycle: Record<string, unknown> = {};
    cycle.next = cycle;
    expectError(
        () => prepareDraft(source, { ...source.editable, owned: cycle }),
        "bounds",
        "editable",
    );
});
test("accessors, sparse arrays and toJSON cannot execute while producing a reviewed draft", () => {
    const source = base();
    const getter = vi.fn(() => "owned-private-canary");
    const withGetter = Object.defineProperty(
        { ...source.editable },
        "storage",
        { get: getter, enumerable: true },
    );
    expectError(() => prepareDraft(source, withGetter), "invalid", "storage");
    const toJSON = vi.fn(() => source.editable);
    expectError(
        () => prepareDraft(source, { ...source.editable, toJSON }),
        "invalid",
        "editable",
    );
    const sparse = Array.from({ length: 2 }, () => originalRepository());
    Reflect.deleteProperty(sparse, "0");
    expectError(
        () =>
            prepareDraft(source, { ...source.editable, repositories: sparse }),
        "invalid",
        "repositories",
    );
    expect(getter).not.toHaveBeenCalled();
    expect(toJSON).not.toHaveBeenCalled();
});
test("a malformed original projection never lends its revision to new public intent", () => {
    const source = { ...base(), base_revision: "owned-private-canary" };
    expectError(() => prepareDraft(source, source.editable), "invalid", "base");
});

test("advanced JSON normalizes only tags and produces the same complete typed managed intent", () => {
    const source = base();
    const desired = {
        ...source.editable,
        repositories: [
            {
                ...originalRepository(),
                revision: "release/v2",
                enabled: false,
                declared_dependencies: ["owned/dependency"],
                tags: [" GPU ", "gpu"],
            },
        ],
    };
    const text = JSON.stringify(desired);
    expect(prepareDraftJson(source, text)).toEqual(
        prepareDraft(source, desired),
    );
    expect(
        prepareDraftJson(source, text).editable.repositories[0],
    ).toMatchObject({
        revision: "release/v2",
        enabled: false,
        declared_dependencies: ["owned/dependency"],
        tags: ["gpu"],
    });
});
test.each(["1.0", "1e0", "9007199254740993"])(
    "advanced JSON refuses original noninteger/unsafe numeric lexeme %s before normalization",
    (number) => {
        const source = base();
        const text = JSON.stringify(source.editable).replace(
            '"minimum_free_space_gib":100',
            '"minimum_free_space_gib":' + number,
        );
        expect(text).toContain('"minimum_free_space_gib":' + number);
        expectError(
            () => prepareDraftJson(source, text),
            "invalid",
            "storage.minimum_free_space_gib",
        );
    },
);
test("advanced JSON rejects duplicate keys, coercion and unknown protected values without reviewing them", () => {
    const source = base();
    const text = JSON.stringify(source.editable);
    const duplicate = text.replace(
        '"maximum_revisions":3',
        '"maximum_revisions":3,"maximum_revisions":5',
    );
    expectError(
        () => prepareDraftJson(source, duplicate),
        "invalid",
        "editable",
    );
    expectError(
        () =>
            prepareDraftJson(
                source,
                text.replace('"max_workers":4', '"max_workers":"4"'),
            ),
        "invalid",
        "sync.max_workers",
    );
    expectError(
        () =>
            prepareDraftJson(
                source,
                JSON.stringify({
                    ...source.editable,
                    hub: { token: "owned-private-canary" },
                }),
            ),
        "invalid",
        "editable",
    );
    expectError(
        () => prepareDraftJson(source, "schema_version = 1\n"),
        "invalid",
        "editable",
    );
});
test("advanced JSON enforces raw UTF8/depth budgets before decoding fields or allocating a reviewed diff", () => {
    const source = base();
    expectError(
        () => prepareDraftJson(source, " ".repeat(MAX_DRAFT_BYTES + 1)),
        "bounds",
        "editable",
    );
    const multibyte = JSON.stringify({
        ...source.editable,
        repositories: [
            {
                ...originalRepository(),
                revision: "é".repeat(MAX_DRAFT_BYTES / 2),
            },
        ],
    });
    expect(multibyte.length).toBeLessThan(MAX_DRAFT_BYTES);
    expectError(
        () => prepareDraftJson(source, multibyte),
        "bounds",
        "editable",
    );
    expectError(
        () => prepareDraftJson(source, "[".repeat(10) + "0" + "]".repeat(10)),
        "bounds",
        "editable",
    );
});
