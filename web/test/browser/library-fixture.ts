/** Fixed 50-repository synthetic catalog; two finite 25-row pages, incomplete metadata. */
import type { CatalogCoverage, CatalogEntry } from "../../src/wire/generated";
import { ARCHIVE_ID, readWire, statusPayload } from "../read-fixtures.ts";

const publication = "d".repeat(32),
    sha = "c".repeat(40);
const coverage: CatalogCoverage = {
    repositories: 50,
    tags_known: 50,
    tags_unknown: 0,
    publications: 50,
    usable: 25,
    partial: 0,
    unsupported: 0,
    failed: 0,
    missing: 25,
    technical_required: false,
    incomplete: true,
};
function wrapper(command: string, data: unknown, cursor: string | null = null) {
    const wire = readWire(command, data);
    return {
        ...wire,
        archive_id: ARCHIVE_ID,
        config_fingerprint: "2".repeat(64),
        next_cursor: cursor,
        envelope: {
            ...wire.envelope,
            outcome: "success_with_warnings",
            warnings: [
                {
                    code: "HFWRN011",
                    message: "Owned incomplete metadata coverage",
                    context: {},
                    repository: null,
                },
            ],
        },
    };
}
export interface LibraryFixtureEvidence {
    readonly identity?: string;
    readonly missing?: number;
}
export function libraryFixtureResponse(
    url: URL,
    evidence: LibraryFixtureEvidence = {},
): unknown {
    const p = url.searchParams;
    const type = p.get("type") === "dataset" ? "dataset" : "model";
    const rows: CatalogEntry[] = Array.from({ length: 50 }, (_, index) => ({
        repository_type: type,
        repository_id: `owned/${type}-${String(index).padStart(2, "0")}`,
        tags: ["project:fixture"],
        tag_origin: "configured",
        tag_observed_at: null,
        curation_fingerprint: null,
        configured: true,
        enabled: true,
        archived: true,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: [],
    }));
    const technical = [
        "format",
        "quantization",
        "quantization_method",
        "bits",
        "max_variant_bytes",
    ].some((key) => p.has(key));
    const missing = evidence.missing ?? coverage.missing;
    const scopedCoverage = {
        ...coverage,
        usable: 50 - missing,
        missing,
        technical_required: technical,
    };
    if (url.pathname === "/api/v1/catalog/search") {
        const limit = Number(p.get("limit") ?? "25");
        const offset = p.get("cursor") === "owned-page-2" ? 25 : 0;
        const entries =
            p.get("q") === "owned-no-known-match" || technical
                ? []
                : rows.slice(offset, offset + limit);
        return wrapper(
            "catalog.search",
            {
                schema_version: 1,
                catalog_identity: evidence.identity ?? "a".repeat(64),
                coverage: scopedCoverage,
                total_matches: entries.length === 0 ? 0 : 50,
                entries,
            },
            entries.length > 0 && offset === 0 && limit < 50
                ? "owned-page-2"
                : null,
        );
    }
    if (url.pathname === "/api/v1/catalog/facets") {
        const facet = p.get("facet");
        const entries =
            facet === "tag" &&
            p.get("q") !== "owned-no-known-match" &&
            !technical
                ? [{ value: "project:fixture", repository_count: 50 }]
                : [];
        return wrapper("catalog.facets", {
            schema_version: 1,
            catalog_identity: evidence.identity ?? "a".repeat(64),
            coverage: scopedCoverage,
            facet,
            total_matches: entries.length,
            entries,
        });
    }
    const selected = p.getAll("selector").map((selector) => {
        const colon = selector.indexOf(":");
        return {
            repository_type: selector.slice(0, colon),
            repository_id: selector.slice(colon + 1),
        };
    });
    if (url.pathname === "/api/v1/repositories")
        return wrapper("list", {
            repositories: selected.map((row) => ({
                ...row,
                managed: true,
                enabled: true,
                current_commit_sha: sha,
                current_publication_id: publication,
                retained_revisions: 1,
            })),
        });
    if (url.pathname === "/api/v1/status")
        return wrapper("status", {
            ...statusPayload(true),
            repositories: selected.map((row) => ({
                ...row,
                managed: true,
                enabled: true,
                current_commit_sha: sha,
                current_publication_generation: 1,
                retained_generations: [1],
                retained_revisions: 1,
                requested_revision: "main",
                upstream_state: "unknown",
                verification_state: "unverified",
                last_run_status: null,
            })),
        });
    if (url.pathname === "/api/v1/repositories/revisions")
        return wrapper("list", {
            revisions: selected.map((row) => ({
                ...row,
                commit_sha: sha,
                publication_id: publication,
                publication_generation: 1,
                published_at: "2026-10-20T12:00:00.000000Z",
                total_bytes: 17,
                file_count: 1,
                verification_state: "unverified",
            })),
        });
    return null;
}
