import { describe, expect, test } from "vitest";
import {
    applyManifestSemantic,
    manifestSemanticIds,
    validateRelativePath,
} from "../src/wire/manifest-semantics";

const manifest = "hfcache.manifests.RevisionManifest.";
const provenance = "hfcache.manifests.FileProvenance._check";
const apply = (id: string, value: unknown) => applyManifestSemantic(id, value);

describe("manifest identity and consistency", () => {
    test("all seven audited manifest/path hooks dispatch explicitly", () => {
        expect(manifestSemanticIds).toHaveLength(7);
        expect(new Set(manifestSemanticIds).size).toBe(7);
        for (const id of [
            "hfcache.models._archive_path",
            "hfcache.models._repository_path",
        ])
            expect(apply(id, "published/path")).toBe("published/path");
        expect(() => apply("unknown", {})).toThrow("semantic");
    });
    test.each([
        "weights/model.bin",
        "e\u0301/file",
        "CON",
        "trailing space ",
        "a:b",
        "é".repeat(127),
        "a/".repeat(511) + "a",
    ])("allowed awkward relative spelling %s", (path) => {
        expect(validateRelativePath(path)).toBe(path);
    });
    test.each([
        null,
        true,
        "",
        "/a",
        "a/",
        "a//b",
        ".",
        "..",
        "a/./b",
        "a/../b",
        "a\\b",
        "a\0b",
        "a\nb",
        "a\u007fb",
        "\ud800",
        "a".repeat(256),
        "é".repeat(128),
        "a/".repeat(512) + "a",
    ])("refused relative path", (path) => {
        expect(() => validateRelativePath(path)).toThrow();
    });
    test("hash reuse names an actual prior publication and repair cache", () => {
        const hashed = {
            hashed: true,
            hash_reused_from: null,
            source: "hub_download",
            cache_root: "canonical",
        };
        const reused = {
            hashed: false,
            hash_reused_from: { commit_sha: "sha", publication_id: "pub" },
            source: "cache_reuse",
            cache_root: "canonical",
        };
        apply(provenance, hashed);
        apply(provenance, reused);
        apply(provenance, {
            ...hashed,
            source: "repair_download",
            cache_root: "repair",
        });
        for (const value of [
            { ...hashed, hash_reused_from: {} },
            { ...reused, hash_reused_from: null },
            { ...hashed, source: "repair_download" },
            { ...hashed, hashed: 1 },
            null,
            {},
        ])
            expect(() => apply(provenance, value)).toThrow();
        const getter = Object.defineProperty({}, "hashed", {
            get() {
                throw new Error("must not execute");
            },
        });
        expect(() => apply(provenance, getter)).toThrow("semantic");
    });
    test("file totals and reused counts use exact integer arithmetic", () => {
        const value = {
            files: [
                { size: 4, provenance: { hashed: true } },
                { size: 5, provenance: { hashed: false } },
            ],
            file_count: 2,
            total_bytes: 9,
            verification: { reused_digests: 1 },
        };
        apply(manifest + "_check_arithmetic", value);
        for (const changed of [
            { file_count: 1 },
            { total_bytes: 8 },
            { verification: { reused_digests: 0 } },
            { files: false },
            { file_count: -1 },
            { total_bytes: Number.MAX_SAFE_INTEGER + 1 },
        ])
            expect(() =>
                apply(manifest + "_check_arithmetic", { ...value, ...changed }),
            ).toThrow();
        apply(manifest + "_check_arithmetic", {
            files: [],
            file_count: 0,
            total_bytes: 0,
            verification: { reused_digests: 0 },
        });
    });
    test("Unicode normalization/full folds collide while code point ordering stays exact", () => {
        for (const paths of [
            ["a", "b"],
            ["\ue000", "\u{10000}"],
            ["①", "１"],
        ])
            apply(manifest + "_check_paths", {
                files: paths.map((path) => ({ path })),
            });
        for (const paths of [
            ["a", "a"],
            ["file", "ﬁle"],
            ["e\u0301", "é"],
            ["SS", "ß"],
            ["Σ", "ς"],
            ["b", "a"],
            ["\u{10000}", "\ue000"],
        ])
            expect(() =>
                apply(manifest + "_check_paths", {
                    files: paths.map((path) => ({ path })),
                }),
            ).toThrow("semantic");
    });
    test("dependency tuple sort preserves equal duplicate observations", () => {
        const first = {
            source_file: "config.json",
            source_field: "base_model",
            detected_id: "owner/a",
        };
        const second = { ...first, detected_id: "owner/b" };
        apply(manifest + "_check_ordering", {
            dependencies: [first, first, second],
        });
        apply(manifest + "_check_ordering", {
            dependencies: [first, { ...second, source_file: "other.json" }],
        });
        for (const dependencies of [
            [second, first],
            [{ ...first, source_field: "z" }, first],
            [{ ...first, source_file: "z" }, first],
        ])
            expect(() =>
                apply(manifest + "_check_ordering", { dependencies }),
            ).toThrow("semantic");
    });
    test("timeline and nested verification preserve microsecond ordering", () => {
        const value = {
            first_observed_at: "2026-01-01T00:00:00.000000Z",
            download_started_at: "2026-10-20T00:00:00.000001Z",
            download_completed_at: "2026-10-20T00:00:00.000002Z",
            verified_at: "2026-10-20T00:00:00.000003Z",
            published_at: "2026-10-20T00:00:00.000004Z",
            verification: { verified_at: "2026-10-20T00:00:00.000003Z" },
        };
        apply(manifest + "_check_timeline", value);
        for (const changed of [
            { first_observed_at: "2027-01-01T00:00:00.000000Z" },
            { download_completed_at: "2026-10-20T00:00:00.000000Z" },
            { published_at: value.download_started_at },
            { verification: { verified_at: "2026-10-20T00:00:00.000002Z" } },
            { published_at: "invalid" },
        ])
            expect(() =>
                apply(manifest + "_check_timeline", { ...value, ...changed }),
            ).toThrow("semantic");
    });
});
