import { describe, expect, test } from "vitest";
import {
    applyCatalogSemantic,
    catalogSemanticIds,
    compareCatalogText,
    validateCatalogRead,
    validateCatalogRefresh,
} from "../src/wire/catalog-semantics";

const query = "hfcache.catalog_query_models.";
const model = "hfcache.catalog_models.";
const refresh = "hfcache.catalog_refresh_models.";
const check = (id: string, value: unknown) => applyCatalogSemantic(id, value);

function coverage(overrides: Record<string, unknown> = {}) {
    return {
        repositories: 1,
        tags_known: 1,
        tags_unknown: 0,
        publications: 1,
        usable: 1,
        partial: 0,
        unsupported: 0,
        failed: 0,
        missing: 0,
        technical_required: false,
        incomplete: false,
        ...overrides,
    };
}
function entry(overrides: Record<string, unknown> = {}) {
    return {
        repository_type: "model",
        repository_id: "owner/model",
        tags: [],
        tag_origin: "unknown",
        tag_observed_at: null,
        curation_fingerprint: null,
        configured: false,
        enabled: null,
        archived: true,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: [],
        ...overrides,
    };
}
function publication(overrides: Record<string, unknown> = {}) {
    return {
        commit_sha: "a".repeat(40),
        publication_id: "b".repeat(32),
        publication_generation: 1,
        write_status: "written",
        observation_status: "complete",
        observed_at: "2026-10-20T00:00:00.000000Z",
        manifest_digest: "c".repeat(64),
        error_code: null,
        ...overrides,
    };
}
function repository(overrides: Record<string, unknown> = {}) {
    return {
        repository_type: "model",
        repository_id: "owner/model",
        tag_status: "captured",
        technical_status: "complete",
        publications: [publication()],
        warnings: [],
        errors: [],
        ...overrides,
    };
}
function refreshResult(overrides: Record<string, unknown> = {}) {
    return {
        state: "complete",
        tags: true,
        technical: true,
        repositories: [repository()],
        counts: {
            repositories: 1,
            snapshots_written: 1,
            observations_written: 1,
            records_failed: 0,
            technical_incomplete: 0,
            technical_skipped: 0,
        },
        ...overrides,
    };
}
// These minimal records isolate semantic rules; full wire/oracle fixtures test shape.
function response(
    command: string,
    data: unknown,
    overrides: Record<string, unknown> = {},
) {
    return {
        archive_id: "archive",
        config_fingerprint: "policy",
        next_cursor: null,
        envelope: { command, data, exit_code: 0, warnings: [] },
        ...overrides,
    };
}

describe("independent catalog evidence rules", () => {
    test("dispatch covers exactly the audited catalog hooks", () => {
        expect(catalogSemanticIds).toHaveLength(17);
        expect(new Set(catalogSemanticIds).size).toBe(17);
        expect(() => check("unknown", "private rejected content")).toThrow(
            "semantic",
        );
    });
    test.each([
        query + "CatalogPayload._version",
        refresh + "CatalogRefreshResult._strict_version",
    ])("strict version %s", (id) => {
        expect(check(id, 1)).toBe(1);
        for (const value of [true, "1", null, 2, 1.5, Number.NaN])
            expect(() => check(id, value)).toThrow();
    });
    test("canonical labels and identifiers refuse normalized-looking replacements", () => {
        expect(check(query + "_canonical_tags", ["a", "team/x"])).toEqual([
            "a",
            "team/x",
        ]);
        for (const tags of [
            ["A"],
            [" a"],
            ["tag\n"],
            ["tag\r\n"],
            ["a", "a"],
            ["b", "a"],
            ["a:".repeat(33)],
            new Array<string>(65).fill("a"),
            "a",
            [false],
        ])
            expect(() => check(query + "_canonical_tags", tags)).toThrow();
        expect(check(model + "_identifier", "Q4_K/M")).toBe("Q4_K/M");
        for (const value of ["", "a:b", "-x", "format\n", "format\r\n", 2])
            expect(() => check(model + "_identifier", value)).toThrow();
        expect(check(query + "CatalogFacetValue._safe_value", "team:x")).toBe(
            "team:x",
        );
        expect(() =>
            check(query + "CatalogFacetValue._safe_value", "x y"),
        ).toThrow();
        for (const value of ["x\n", "x\r\n"])
            expect(() =>
                check(query + "CatalogFacetValue._safe_value", value),
            ).toThrow();
    });
    test("Python code point ordering handles non-BMP sources and prefix pairs", () => {
        expect(compareCatalogText("\ue000", "\u{10000}")).toBe(-1);
        expect(compareCatalogText("a", "ab")).toBe(-1);
        expect(compareCatalogText("ab", "a")).toBe(1);
        expect(compareCatalogText("same", "same")).toBe(0);
        expect(compareCatalogText("b", "a")).toBe(1);
        expect(
            check(model + "SourceObservation.ordered", {
                values: ["\ue000", "\u{10000}"],
            }),
        ).toEqual({ values: ["\ue000", "\u{10000}"] });
        expect(() =>
            check(model + "SourceObservation.ordered", {
                values: ["\u{10000}", "\ue000"],
            }),
        ).toThrow();
        for (const invalid of [null, {}, { values: false }, { values: [1] }])
            expect(() =>
                check(model + "SourceObservation.ordered", invalid),
            ).toThrow();
        const getter = Object.defineProperty({}, "values", {
            get() {
                throw new Error("must not execute");
            },
        });
        expect(() =>
            check(model + "SourceObservation.ordered", getter),
        ).toThrow("semantic");
    });
    test("coverage partitions use exact sums", () => {
        check(query + "CatalogCoverage._coherent", coverage());
        for (const value of [
            coverage({ tags_unknown: 1 }),
            coverage({ failed: 1 }),
            coverage({ repositories: Number.MAX_SAFE_INTEGER + 1 }),
            coverage({ publications: 1.5 }),
        ])
            expect(() =>
                check(query + "CatalogCoverage._coherent", value),
            ).toThrow();
    });
    test("configured, disabled, unknown, dataset and unarchived facts stay distinct", () => {
        for (const value of [
            entry(),
            entry({
                configured: true,
                enabled: false,
                tag_origin: "configured",
            }),
            entry({ repository_type: "dataset", dataset_formats: ["parquet"] }),
            entry({ archived: false }),
        ])
            check(query + "CatalogEntry._coherent", value);
        for (const value of [
            entry({ enabled: false }),
            entry({ configured: true }),
            entry({ tags: ["invented"] }),
            entry({ tag_observed_at: "date" }),
            entry({ curation_fingerprint: "hash" }),
            entry({ dataset_formats: ["GGUF"] }),
            entry({ dataset_formats: ["gguf"] }),
            entry({ repository_type: "dataset", matching_variant_count: 1 }),
            entry({ representative_variant: {} }),
            entry({ archived: false, matching_variant_count: 1 }),
        ])
            expect(() =>
                check(query + "CatalogEntry._coherent", value),
            ).toThrow();
        check(
            query + "CatalogEntry._coherent",
            entry({ matching_variant_count: 1, representative_variant: {} }),
        );
    });
    test("variant membership, ordering and complete byte totals agree", () => {
        const value = {
            members: [
                { path: "a", size_bytes: 4 },
                { path: "b", size_bytes: 5 },
            ],
            source_paths: ["config.json"],
            diagnostics: [],
            total_bytes: 9,
            completeness: "complete",
        };
        check(model + "ModelVariant.coherent", value);
        check(model + "ModelVariant.coherent", {
            ...value,
            total_bytes: null,
            completeness: "unknown",
        });
        for (const changed of [
            { total_bytes: 8 },
            { total_bytes: null },
            {
                members: [
                    { path: "a", size_bytes: 4 },
                    { path: "a", size_bytes: 5 },
                ],
            },
            { source_paths: ["z", "a"] },
            { diagnostics: ["x", "x"] },
            {
                total_bytes: Number.MAX_SAFE_INTEGER,
                members: [
                    { path: "a", size_bytes: Number.MAX_SAFE_INTEGER },
                    { path: "b", size_bytes: 2 },
                ],
            },
        ])
            expect(() =>
                check(model + "ModelVariant.coherent", {
                    ...value,
                    ...changed,
                }),
            ).toThrow();
    });
    test("search/detail/variant identities cannot hide duplicates or excess rows", () => {
        check(query + "CatalogSearchPayload._coherent", {
            entries: [entry()],
            total_matches: 1,
            coverage: coverage(),
        });
        for (const value of [
            {
                entries: [entry(), entry()],
                total_matches: 2,
                coverage: coverage({ repositories: 2 }),
            },
            { entries: [entry()], total_matches: 0, coverage: coverage() },
            { entries: [], total_matches: 2, coverage: coverage() },
        ])
            expect(() =>
                check(query + "CatalogSearchPayload._coherent", value),
            ).toThrow();
        const identity = { commit_sha: "sha", publication_id: "pub" };
        check(query + "CatalogDetailPayload._coherent", {
            observations: [identity],
        });
        expect(() =>
            check(query + "CatalogDetailPayload._coherent", {
                observations: [identity, identity],
            }),
        ).toThrow();
        const variant = { ...identity, variant: { variant_id: "variant" } };
        check(query + "CatalogVariantsPayload._coherent", {
            entries: [variant],
            total_matches: 1,
        });
        for (const value of [
            { entries: [variant, variant], total_matches: 2 },
            { entries: [variant], total_matches: 0 },
        ])
            expect(() =>
                check(query + "CatalogVariantsPayload._coherent", value),
            ).toThrow();
    });
    test("facet case is specific to tags, format and quantization", () => {
        const payload = {
            entries: [{ value: "q4", repository_count: 1 }],
            total_matches: 1,
            coverage: coverage(),
            facet: "format",
        };
        check(query + "CatalogFacetPayload._coherent", payload);
        check(query + "CatalogFacetPayload._coherent", {
            ...payload,
            facet: "tag",
        });
        check(query + "CatalogFacetPayload._coherent", {
            ...payload,
            facet: "quantization",
            entries: [{ value: "Q4", repository_count: 1 }],
        });
        for (const changed of [
            { facet: "quantization" },
            { total_matches: 0 },
            { entries: [{ value: "q4", repository_count: 2 }] },
            { entries: [{ value: "Q4", repository_count: 1 }] },
        ])
            expect(() =>
                check(query + "CatalogFacetPayload._coherent", {
                    ...payload,
                    ...changed,
                }),
            ).toThrow();
        const observation = {
            sources: [{ path: "a", field: "task", evidence: "declaration" }],
            dataset_formats: [],
            diagnostics: [],
        };
        check(query + "ObservationSummary._ordered", observation);
        expect(() =>
            check(query + "ObservationSummary._ordered", {
                ...observation,
                sources: [...observation.sources, ...observation.sources],
            }),
        ).toThrow();
    });
    test("publication refresh never invents an observation after a failed write", () => {
        check(refresh + "PublicationRefresh._coherent", publication());
        check(
            refresh + "PublicationRefresh._coherent",
            publication({
                write_status: "failed",
                observation_status: null,
                observed_at: null,
                manifest_digest: null,
                error_code: "HFERR001",
            }),
        );
        for (const changed of [
            { error_code: "HFERR001" },
            { observed_at: null },
            { write_status: "failed" },
        ])
            expect(() =>
                check(
                    refresh + "PublicationRefresh._coherent",
                    publication(changed),
                ),
            ).toThrow();
    });
    test("repository refresh preserves skips, partial attempts and failure codes", () => {
        check(refresh + "RepositoryRefresh._coherent", repository());
        for (const status of ["not_requested", "skipped_unpublished"])
            check(
                refresh + "RepositoryRefresh._coherent",
                repository({ technical_status: status, publications: [] }),
            );
        check(
            refresh + "RepositoryRefresh._coherent",
            repository({
                technical_status: "incomplete",
                publications: [publication({ observation_status: "partial" })],
                warnings: ["HFWRN011"],
            }),
        );
        check(
            refresh + "RepositoryRefresh._coherent",
            repository({
                technical_status: "failed",
                publications: [
                    publication({
                        write_status: "failed",
                        observation_status: null,
                        error_code: "HFERR001",
                    }),
                ],
                warnings: ["HFWRN011"],
                errors: ["HFERR001"],
            }),
        );
        for (const changed of [
            { warnings: ["z", "a"] },
            { technical_status: "not_requested" },
            { publications: [] },
            { publications: [publication(), publication()] },
            { technical_status: "failed" },
            { tag_status: "failed" },
            { errors: ["HFERR001"] },
            { publications: [publication({ error_code: "HFERR001" })] },
        ])
            expect(() =>
                check(
                    refresh + "RepositoryRefresh._coherent",
                    repository(changed),
                ),
            ).toThrow();
    });
    test("refresh aggregate counts/state come from exact attempts and enabled outputs", () => {
        check(refresh + "CatalogRefreshResult._coherent", refreshResult());
        const failedRow = repository({
            tag_status: "failed",
            technical_status: "skipped_unpublished",
            publications: [],
            warnings: ["HFWRN011"],
            errors: ["HFERR001"],
        });
        check(
            refresh + "CatalogRefreshResult._coherent",
            refreshResult({
                state: "failed",
                repositories: [failedRow],
                counts: {
                    repositories: 1,
                    snapshots_written: 0,
                    observations_written: 0,
                    records_failed: 1,
                    technical_incomplete: 0,
                    technical_skipped: 1,
                },
            }),
        );
        const partial = repository({
            technical_status: "incomplete",
            publications: [publication({ observation_status: "partial" })],
            warnings: ["HFWRN011"],
        });
        check(
            refresh + "CatalogRefreshResult._coherent",
            refreshResult({
                state: "partial",
                repositories: [partial],
                counts: {
                    repositories: 1,
                    snapshots_written: 1,
                    observations_written: 1,
                    records_failed: 0,
                    technical_incomplete: 1,
                    technical_skipped: 0,
                },
            }),
        );
        for (const changed of [
            { state: "partial" },
            { tags: false },
            { technical: false },
            { tags: false, technical: false },
            { counts: { repositories: 0 } },
            { repositories: [repository(), repository()] },
        ])
            expect(() =>
                check(
                    refresh + "CatalogRefreshResult._coherent",
                    refreshResult(changed),
                ),
            ).toThrow();
        check(
            refresh + "CatalogRefreshResult._coherent",
            refreshResult({
                tags: false,
                technical: true,
                repositories: [repository({ tag_status: "not_requested" })],
                counts: {
                    repositories: 1,
                    snapshots_written: 0,
                    observations_written: 1,
                    records_failed: 0,
                    technical_incomplete: 0,
                    technical_skipped: 0,
                },
            }),
        );
    });
});

describe("catalog request/response binding", () => {
    test("incomplete coverage requires exactly its supplemental warning", () => {
        const data = { coverage: coverage(), entries: [] };
        validateCatalogRead(response("catalog.search", data), {
            command: "catalog.search",
        });
        validateCatalogRead(
            response("catalog.search", data, { next_cursor: "opaque" }),
            { command: "catalog.search" },
        );
        const incomplete = {
            coverage: coverage({
                tags_known: 0,
                tags_unknown: 1,
                incomplete: true,
            }),
            entries: [],
        };
        validateCatalogRead(
            response("catalog.search", incomplete, {
                envelope: {
                    command: "catalog.search",
                    data: incomplete,
                    exit_code: 0,
                    warnings: [{ code: "HFWRN011" }],
                },
            }),
            { command: "catalog.search" },
        );
        for (const changed of [
            { archive_id: null },
            { config_fingerprint: null },
            { next_cursor: "\u0100" },
            { next_cursor: "hf_12345678" },
            { next_cursor: true },
        ])
            expect(() => {
                validateCatalogRead(response("catalog.search", data, changed), {
                    command: "catalog.search",
                });
            }).toThrow();
        expect(() => {
            validateCatalogRead(response("other", data), {
                command: "catalog.search",
            });
        }).toThrow();
        expect(() => {
            validateCatalogRead(response("catalog.search", incomplete), {
                command: "catalog.search",
            });
        }).toThrow();
        expect(() => {
            validateCatalogRead(
                response("catalog.search", {
                    coverage: coverage({ tags_unknown: 1 }),
                    entries: [],
                }),
                { command: "catalog.search" },
            );
        }).toThrow();
        validateCatalogRead(
            response(
                "catalog.search",
                {},
                {
                    envelope: { command: "catalog.search", exit_code: 20 },
                    next_cursor: null,
                },
            ),
            { command: "catalog.search" },
        );
        expect(() => {
            validateCatalogRead(
                response(
                    "catalog.search",
                    {},
                    {
                        envelope: { command: "catalog.search", exit_code: 20 },
                        next_cursor: "cursor",
                    },
                ),
                { command: "catalog.search" },
            );
        }).toThrow();
    });
    test("details and variants retain exact requested publication and repository", () => {
        const context = {
            command: "catalog.detail",
            repositoryType: "model",
            repositoryId: "owner/model",
            commitSha: "sha",
            publicationId: "pub",
        } satisfies Parameters<typeof validateCatalogRead>[1];
        const payload = {
            coverage: coverage(),
            entry: entry(),
            observations: [{ commit_sha: "sha", publication_id: "pub" }],
        };
        validateCatalogRead(response(context.command, payload), context);
        const conflictingScopes = [
            { repositoryId: "owner/other" },
            { repositoryType: "dataset" },
            { publicationId: "other" },
            { commitSha: "other" },
        ] satisfies readonly Partial<
            Parameters<typeof validateCatalogRead>[1]
        >[];
        for (const changed of conflictingScopes)
            expect(() => {
                validateCatalogRead(response(context.command, payload), {
                    ...context,
                    ...changed,
                } satisfies Parameters<typeof validateCatalogRead>[1]);
            }).toThrow();
        expect(() => {
            validateCatalogRead(
                response(context.command, payload, { next_cursor: "cursor" }),
                context,
            );
        }).toThrow();
        expect(() => {
            validateCatalogRead(response(context.command, payload), {
                command: context.command,
                commitSha: "sha",
            });
        }).toThrow();
        validateCatalogRead(
            response("catalog.variants", {
                coverage: coverage(),
                entries: payload.observations,
            }),
            {
                command: "catalog.variants",
                commitSha: "sha",
                publicationId: "pub",
            },
        );
        expect(() => {
            validateCatalogRead(
                response("catalog.search", {
                    coverage: coverage(),
                    entries: [entry()],
                }),
                { command: "catalog.search", repositoryType: "dataset" },
            );
        }).toThrow();
    });
    test("facet positive counts and request facet are checked beyond model shape", () => {
        const data = {
            coverage: coverage(),
            facet: "tag",
            entries: [{ repository_count: 1 }],
        };
        validateCatalogRead(response("catalog.facets", data), {
            command: "catalog.facets",
            facet: "tag",
        });
        expect(() => {
            validateCatalogRead(response("catalog.facets", data), {
                command: "catalog.facets",
                facet: "format",
            });
        }).toThrow();
        expect(() => {
            validateCatalogRead(
                response("catalog.facets", {
                    ...data,
                    entries: [{ repository_count: 0 }],
                }),
                { command: "catalog.facets" },
            );
        }).toThrow();
    });
    test("empty failed refresh stays failed while recorded progress binds archive", () => {
        validateCatalogRefresh(
            response(
                "catalog refresh",
                {},
                {
                    envelope: {
                        command: "catalog refresh",
                        exit_code: 20,
                        data: {},
                    },
                },
            ),
        );
        validateCatalogRefresh(
            response("catalog refresh", { archive_id: "archive" }),
        );
        for (const value of [
            response("catalog refresh", {}),
            response("catalog refresh", { archive_id: "other" }),
            response("other", {}),
            response("catalog refresh", {}, { next_cursor: "cursor" }),
        ])
            expect(() => {
                validateCatalogRefresh(value);
            }).toThrow();
    });
});
