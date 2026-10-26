import { describe, expect, test } from "vitest";
import {
    joinLibraryRows,
    LibraryJoinError,
    libraryRepositoryKey,
} from "../src/library/joins";
import type { ScopedLibraryRead } from "../src/library/joins";
import type { ApiScope } from "../src/api/identity";
import type {
    CatalogEntry,
    CatalogSearchPayload,
    RepositoryPayload,
    RepositoryStatusPayload,
    RevisionPayload,
} from "../src/wire/generated";
import { ARCHIVE_ID } from "./read-fixtures";

const scope: ApiScope = {
    origin: "https://fixture.example",
    publicPrefix: "",
    authorityEpoch: "epoch-1",
    subject: "administrator",
    credentialClass: "rest-writer",
    instanceId: "a".repeat(32),
    archiveId: ARCHIVE_ID,
    configFingerprint: "b".repeat(64),
};
const sha = "c".repeat(40),
    publication = "d".repeat(32),
    at = "2026-10-26T12:00:00.000000Z";
function read<T>(
    data: T,
    overrides: Partial<ApiScope> = {},
): ScopedLibraryRead<T> {
    const target = { ...scope, ...overrides };
    return {
        scope: target,
        response: {
            schema_version: 1,
            request_id: "1".repeat(32),
            archive_id: target.archiveId,
            config_fingerprint: target.configFingerprint,
            next_cursor: null,
            envelope: {
                schema_version: 1,
                command: "fixture metadata",
                run_id: "2".repeat(32),
                started_at: at,
                completed_at: at,
                outcome: "success",
                exit_code: 0,
                errors: [],
                warnings: [],
                data,
            },
        },
    };
}
function entry(overrides: Partial<CatalogEntry> = {}): CatalogEntry {
    return {
        repository_type: "model",
        repository_id: "owner/shared",
        tags: ["gpu"],
        tag_origin: "configured",
        tag_observed_at: null,
        curation_fingerprint: null,
        configured: true,
        enabled: false,
        archived: true,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: [],
        ...overrides,
    };
}
function catalog(entries = [entry()]): ScopedLibraryRead<CatalogSearchPayload> {
    return read({
        schema_version: 1,
        catalog_identity: "3".repeat(64),
        coverage: {
            repositories: entries.length,
            tags_known: entries.length,
            tags_unknown: 0,
            publications: entries.length,
            usable: entries.length,
            partial: 0,
            unsupported: 0,
            failed: 0,
            missing: 0,
            technical_required: false,
            incomplete: false,
        },
        total_matches: entries.length,
        entries,
    });
}
function inventory(
    overrides: Partial<RepositoryPayload> = {},
): RepositoryPayload {
    return {
        repository_type: "model",
        repository_id: "owner/shared",
        managed: true,
        enabled: false,
        current_commit_sha: sha,
        current_publication_id: publication,
        retained_revisions: 1,
        ...overrides,
    };
}
function status(
    overrides: Partial<RepositoryStatusPayload> = {},
): RepositoryStatusPayload {
    return {
        repository_type: "model",
        repository_id: "owner/shared",
        managed: true,
        enabled: false,
        current_commit_sha: sha,
        current_publication_generation: 1,
        last_run_status: "completed",
        requested_revision: "main",
        retained_generations: [1],
        retained_revisions: 1,
        upstream_state: "unknown",
        verification_state: "verified",
        ...overrides,
    };
}
function revision(overrides: Partial<RevisionPayload> = {}): RevisionPayload {
    return {
        repository_type: "model",
        repository_id: "owner/shared",
        commit_sha: sha,
        publication_id: publication,
        publication_generation: 1,
        file_count: 2,
        published_at: at,
        total_bytes: 17,
        verification_state: "verified",
        ...overrides,
    };
}
const complete = () => ({
    inventory: read({ repositories: [inventory()] }),
    status: read({
        archive: {
            archive_id: ARCHIVE_ID,
            root: "/owned/archive",
            reachable: false as const,
            verification: {
                degraded: false,
                last_full_verification: null,
                outstanding_failures: 0,
            },
        },
        repositories: [status()],
    }),
    revisions: read({ revisions: [revision()] }),
});

describe("Library bounded identity joins", () => {
    test("same spelling across models and datasets joins by tuple despite source ordering", () => {
        const dataset = { repository_type: "dataset" as const };
        const rows = joinLibraryRows(catalog([entry(), entry(dataset)]), {
            inventory: read({
                repositories: [inventory(dataset), inventory()],
            }),
            status: read({
                ...complete().status.response.envelope.data,
                repositories: [status(dataset), status()],
            }),
            revisions: read({
                revisions: [
                    revision({ ...dataset, total_bytes: 29 }),
                    revision(),
                ],
            }),
        });
        expect(rows.map((row) => row.key)).toEqual([
            "model:owner/shared",
            "dataset:owner/shared",
        ]);
        expect(rows.map((row) => row.currentRevision?.total_bytes)).toEqual([
            17, 29,
        ]);
        expect(rows.every((row) => row.enrichment === "complete")).toBe(true);
        expect(rows[0]?.entry.enabled).toBe(false);
        expect(Object.isFrozen(rows)).toBe(true);
        expect(Object.isFrozen(rows[0])).toBe(true);
    });
    test("unrequested/missing enrichment remains informational unknown, not zero or absence", () => {
        const rows = joinLibraryRows(catalog());
        expect(rows[0]).toMatchObject({
            inventory: null,
            status: null,
            currentRevision: null,
            representativeRevision: null,
            enrichment: "unavailable",
        });
        const partial = joinLibraryRows(catalog(), {
            inventory: read({ repositories: [] }),
        });
        expect(partial[0]).toMatchObject({
            inventory: null,
            currentRevision: null,
            enrichment: "partial",
        });
    });
    test.each<Partial<ApiScope>>([
        { origin: "https://other.example" },
        { publicPrefix: "/different" },
        { subject: "other" },
        { credentialClass: "rest-reader" },
        { archiveId: "01234567-89ab-cdef-0123-456789abcdef" },
        { configFingerprint: "e".repeat(64) },
        { authorityEpoch: "epoch-2" },
        { instanceId: "e".repeat(32) },
    ])(
        "withholds a successful response from a different authority/session",
        (changed) => {
            const rows = joinLibraryRows(catalog(), {
                inventory: read({ repositories: [inventory()] }, changed),
            });
            expect(rows[0]).toMatchObject({
                inventory: null,
                enrichment: "changed",
            });
        },
    );
    test("wrapper authority must agree even if caller retained the same local scope", () => {
        const source = read({ repositories: [inventory()] });
        const rows = joinLibraryRows(catalog(), {
            inventory: {
                ...source,
                response: {
                    ...source.response,
                    config_fingerprint: "e".repeat(64),
                },
            },
        });
        expect(rows[0]).toMatchObject({
            inventory: null,
            enrichment: "changed",
        });
        const sourceCatalog = catalog();
        expect(() =>
            joinLibraryRows({
                ...sourceCatalog,
                response: { ...sourceCatalog.response, archive_id: null },
            }),
        ).toThrow(LibraryJoinError);
        expect(() =>
            joinLibraryRows({
                ...sourceCatalog,
                response: {
                    ...sourceCatalog.response,
                    config_fingerprint: null,
                },
            }),
        ).toThrow(LibraryJoinError);
    });
    test("an exact retained representative stays distinct from inventory's current pair", () => {
        const old = revision({
            commit_sha: "e".repeat(40),
            publication_id: "f".repeat(32),
            publication_generation: 2,
            total_bytes: 31,
        });
        const representative = {
            commit_sha: old.commit_sha,
            publication_id: old.publication_id,
            publication_generation: 2,
            variant: {
                variant_id: "weights",
                format: "gguf",
                encoding: null,
                quantization: "Q4_K_M",
                quantization_method: "gguf",
                bits: 4,
                group_size: null,
                role: "primary" as const,
                members: [],
                total_bytes: 31,
                completeness: "complete" as const,
                evidence: "header" as const,
                source_paths: [],
                diagnostics: [],
            },
        };
        const rows = joinLibraryRows(
            catalog([
                entry({
                    matching_variant_count: 1,
                    representative_variant: representative,
                }),
            ]),
            {
                ...complete(),
                revisions: read({ revisions: [revision(), old] }),
            },
        );
        expect(rows[0]?.currentRevision?.total_bytes).toBe(17);
        expect(rows[0]?.representativeRevision?.total_bytes).toBe(31);
        expect(rows[0]?.enrichment).toBe("complete");
        expect(rows[0]?.entry.representative_variant?.variant.total_bytes).toBe(
            31,
        );
    });
    test("same SHA but another publication cannot donate bytes to current", () => {
        const rows = joinLibraryRows(catalog(), {
            ...complete(),
            revisions: read({
                revisions: [
                    revision({
                        publication_id: "e".repeat(32),
                        total_bytes: 99,
                    }),
                ],
            }),
        });
        expect(rows[0]).toMatchObject({
            currentRevision: null,
            enrichment: "partial",
        });
    });
    test("a current ref movement or repair generation cannot attach old verification/size", () => {
        for (const changed of [
            { current_commit_sha: "e".repeat(40) },
            { current_publication_generation: 2 },
        ]) {
            const rows = joinLibraryRows(catalog(), {
                ...complete(),
                status: read({
                    ...complete().status.response.envelope.data,
                    repositories: [status(changed)],
                }),
            });
            expect(rows[0]).toMatchObject({
                status: null,
                currentRevision: null,
                enrichment: "changed",
            });
        }
    });
    test.each([
        { managed: false },
        { enabled: true },
        { retained_revisions: 0 },
    ])(
        "configuration/archive drift never overwrites catalog source truth",
        (changed) => {
            const rows = joinLibraryRows(catalog(), {
                ...complete(),
                inventory: read({ repositories: [inventory(changed)] }),
            });
            expect(rows[0]).toMatchObject({
                inventory: null,
                currentRevision: null,
                enrichment: "changed",
            });
            expect(rows[0]?.entry).toMatchObject({
                configured: true,
                enabled: false,
                archived: true,
                tag_origin: "configured",
                tags: ["gpu"],
            });
        },
    );
    test("status drift remains separate from catalog and exact inventory", () => {
        const rows = joinLibraryRows(catalog(), {
            ...complete(),
            status: read({
                ...complete().status.response.envelope.data,
                repositories: [status({ enabled: true })],
            }),
        });
        expect(rows[0]).toMatchObject({ status: null, enrichment: "changed" });
        expect(rows[0]?.inventory?.enabled).toBe(false);
        expect(rows[0]?.entry.enabled).toBe(false);
    });
    test("a representative generation mismatch withholds its revision bytes", () => {
        const representative = {
            commit_sha: sha,
            publication_id: publication,
            publication_generation: 2,
            variant: {
                variant_id: "weights",
                format: "gguf",
                encoding: null,
                quantization: null,
                quantization_method: null,
                bits: null,
                group_size: null,
                role: "primary" as const,
                members: [],
                total_bytes: null,
                completeness: "unknown" as const,
                evidence: "filename" as const,
                source_paths: [],
                diagnostics: [],
            },
        };
        const rows = joinLibraryRows(
            catalog([
                entry({
                    matching_variant_count: 1,
                    representative_variant: representative,
                }),
            ]),
            complete(),
        );
        expect(rows[0]).toMatchObject({
            representativeRevision: null,
            enrichment: "changed",
        });
        expect(rows[0]?.currentRevision?.total_bytes).toBe(17);
    });
    test("half-present current identities cannot become a confirmed absence", () => {
        expect(() =>
            joinLibraryRows(catalog(), {
                inventory: read({
                    repositories: [inventory({ current_publication_id: null })],
                }),
            }),
        ).toThrow(LibraryJoinError);
        expect(() =>
            joinLibraryRows(catalog(), {
                status: read({
                    ...complete().status.response.envelope.data,
                    repositories: [
                        status({ current_publication_generation: null }),
                    ],
                }),
            }),
        ).toThrow(LibraryJoinError);
    });
    test("configured unpublished with known empty tags is not a fictional zero-byte publication", () => {
        const row = entry({ archived: false, tags: [] });
        const rows = joinLibraryRows(catalog([row]), {
            inventory: read({
                repositories: [
                    inventory({
                        current_commit_sha: null,
                        current_publication_id: null,
                        retained_revisions: 0,
                    }),
                ],
            }),
            status: read({
                ...complete().status.response.envelope.data,
                repositories: [
                    status({
                        current_commit_sha: null,
                        current_publication_generation: null,
                        retained_revisions: 0,
                        retained_generations: [],
                        verification_state: "unverified",
                    }),
                ],
            }),
            revisions: read({ revisions: [] }),
        });
        expect(rows[0]).toMatchObject({
            currentRevision: null,
            enrichment: "complete",
        });
        expect(rows[0]?.entry.tags).toEqual([]);
    });
    test("unmanaged historical tags and dataset declarations stay independent", () => {
        const row = entry({
            repository_type: "dataset",
            configured: false,
            enabled: null,
            tag_origin: "last_observed",
            tag_observed_at: at,
            dataset_formats: ["parquet"],
        });
        const rows = joinLibraryRows(catalog([row]), {
            inventory: read({
                repositories: [
                    inventory({
                        repository_type: "dataset",
                        managed: false,
                        enabled: null,
                    }),
                ],
            }),
        });
        expect(rows[0]).toMatchObject({
            status: null,
            currentRevision: null,
            enrichment: "partial",
        });
        expect(rows[0]?.entry).toMatchObject({
            tag_origin: "last_observed",
            dataset_formats: ["parquet"],
            representative_variant: null,
        });
    });
    test("duplicates are a protocol contradiction, never last-row-wins", () => {
        expect(() => joinLibraryRows(catalog([entry(), entry()]))).toThrow(
            LibraryJoinError,
        );
        expect(() =>
            joinLibraryRows(catalog(), {
                inventory: read({ repositories: [inventory(), inventory()] }),
            }),
        ).toThrow(LibraryJoinError);
        expect(() =>
            joinLibraryRows(catalog(), {
                status: read({
                    ...complete().status.response.envelope.data,
                    repositories: [status(), status()],
                }),
            }),
        ).toThrow(LibraryJoinError);
        expect(() =>
            joinLibraryRows(catalog(), {
                revisions: read({ revisions: [revision(), revision()] }),
            }),
        ).toThrow(LibraryJoinError);
    });
    test("no match stays no known match without rewriting incomplete whole-scope coverage", () => {
        const source = catalog([]);
        const coverage = {
            ...source.response.envelope.data.coverage,
            repositories: 7,
            tags_unknown: 7,
            incomplete: true,
        };
        const input = {
            ...source,
            response: {
                ...source.response,
                envelope: {
                    ...source.response.envelope,
                    data: { ...source.response.envelope.data, coverage },
                },
            },
        };
        expect(joinLibraryRows(input)).toEqual([]);
        expect(input.response.envelope.data.coverage).toEqual(coverage);
    });
    test("work and malformed identity are bounded without archive traversal", () => {
        expect(() =>
            joinLibraryRows(catalog(Array<CatalogEntry>(10_001).fill(entry()))),
        ).toThrow(LibraryJoinError);
        expect(() =>
            libraryRepositoryKey(entry({ repository_id: "../escape" })),
        ).toThrow(LibraryJoinError);
        expect(() =>
            joinLibraryRows(catalog(), {
                revisions: read({
                    revisions: [revision({ publication_id: "bad" })],
                }),
            }),
        ).toThrow(LibraryJoinError);
    });
});
