import { describe, expect, test } from "vitest";
import {
    exactPublication,
    isRepositoryTab,
    MAX_REPOSITORY_FRAGMENT_BYTES,
    parseRepositoryFragment,
    parseRepositoryRoute,
    REPOSITORY_TABS,
    repositoryFragment,
    repositoryPath,
    RepositoryRouteError,
} from "../src/repository/routes";
import { publicationIdentity } from "../src/api/identity";

const target = {
    repositoryType: "model" as const,
    repositoryId: "Owner_1/Repo.v2-X",
};
const pair = { commitSha: "a".repeat(40), publicationId: "b".repeat(32) };

describe("canonical type-aware repository shell paths", () => {
    test.each(["/ui/", "/edge/ui/", "/archive:one/ui/", "/%CE%B1/ui/"])(
        "roundtrips under the exact configured base %s",
        (base) => {
            const path = repositoryPath(target, base);
            expect(path).toBe(base + "repositories/model/Owner_1/Repo.v2-X");
            expect(parseRepositoryRoute(path, base)).toEqual(target);
            expect(Object.isFrozen(parseRepositoryRoute(path, base))).toBe(
                true,
            );
            expect(path).not.toContain("?");
            expect(path).not.toContain("#");
        },
    );
    test("model and dataset with the same ID are different canonical identities", () => {
        const dataset = { ...target, repositoryType: "dataset" as const };
        expect(repositoryPath(dataset, "/ui/")).not.toBe(
            repositoryPath(target, "/ui/"),
        );
        expect(
            parseRepositoryRoute(
                "/ui/repositories/dataset/Owner_1/Repo.v2-X",
                "/ui/",
            ),
        ).toEqual(dataset);
    });
    test.each([
        "/ui/library",
        "/ui/repositories",
        "/ui/repositories/model",
        "/ui/repositories/model/owner",
        "/ui/repositories/model/owner/name/",
        "/ui/repositories/model/owner/name/files",
        "/ui/repositories/models/owner/name",
        "/ui/repositories/MODEL/owner/name",
        "/ui/repositories/unknown/owner/name",
        "/ui/repositories/model//name",
        "/ui/repositories/model/owner//name",
        "/ui/repositories/model/owner/../name",
        "/ui/repositories/model/../name",
        "/ui/repositories/model/owner/.",
        "/ui/repositories/model/_owner/name",
        "/ui/repositories/model/owner/-name",
        "/ui/repositories/model/owner/name?tab=files",
        "/ui/repositories/model/owner/name#tab=files",
        "/ui/repositories/model/owner\\name",
        "/ui/repositories/model/own er/name",
        "/ui/repositories/model/öwner/name",
        "/ui/repositories/model/owner/name\u0000",
        "/ui/repositories/model/owner/\ud800",
        "/UI/repositories/model/owner/name",
        "/other/ui/repositories/model/owner/name",
        "https://other.example/ui/repositories/model/owner/name",
        "//other.example/ui/repositories/model/owner/name",
    ])("unrecognized or unsafe path returns null: %s", (path) => {
        expect(parseRepositoryRoute(path, "/ui/")).toBeNull();
    });
    test.each([
        "owner%2Fextra/name",
        "owner%2fextra/name",
        "owner/name%2fextra",
        "%6Fwner/name",
        "owner/%6eame",
        "owner/%2e%2e",
        "owner/%252e%252e",
        "owner/name%5cother",
        "owner/%GG",
        "owner/%",
        "owner/name%00",
        "owner/%ED%A0%80",
    ])("encoded ID spelling is never a path authority: %s", (suffix) => {
        expect(
            parseRepositoryRoute("/ui/repositories/model/" + suffix, "/ui/"),
        ).toBeNull();
    });
    test.each([
        "/ui",
        "//ui/",
        "/edge//ui/",
        "/edge/../ui/",
        "/edge%2Fother/ui/",
        "/%ce%b1/ui/",
        "/%65dge/ui/",
        "/edge%/ui/",
        "/edge?bad/ui/",
        "/edge#bad/ui/",
        "/edge\\bad/ui/",
        "https://foreign.example/ui/",
    ])(
        "invalid configured base cannot recognize or build a repository %s",
        (base) => {
            expect(
                parseRepositoryRoute(
                    base + "repositories/model/owner/name",
                    base,
                ),
            ).toBeNull();
            expect(() => repositoryPath(target, base)).toThrow(
                RepositoryRouteError,
            );
        },
    );
    test("prefix membership is exact, without Unicode/case/encoding approximation", () => {
        expect(
            parseRepositoryRoute(
                "/%ce%b1/ui/repositories/model/owner/name",
                "/%CE%B1/ui/",
            ),
        ).toBeNull();
        expect(
            parseRepositoryRoute(
                "/edge2/ui/repositories/model/owner/name",
                "/edge/ui/",
            ),
        ).toBeNull();
        expect(
            parseRepositoryRoute(
                "/edge/ui/repositories/model/owner/name",
                "/ui/",
            ),
        ).toBeNull();
    });
    test("existing segment bounds are96 per namespace/name and total input work is finite", () => {
        const maximum = {
            repositoryType: "dataset" as const,
            repositoryId: "a".repeat(96) + "/" + "b".repeat(96),
        };
        expect(
            parseRepositoryRoute(repositoryPath(maximum, "/ui/"), "/ui/"),
        ).toEqual(maximum);
        expect(() =>
            repositoryPath(
                { ...maximum, repositoryId: "a".repeat(97) + "/name" },
                "/ui/",
            ),
        ).toThrow(RepositoryRouteError);
        expect(
            parseRepositoryRoute("/ui/" + "a".repeat(8192), "/ui/"),
        ).toBeNull();
    });
});

describe("bounded exact-publication fragments", () => {
    test("current is represented by no pair, not by a special SHA or new publication", () => {
        expect(parseRepositoryFragment("")).toEqual({
            pair: null,
            tab: "overview",
        });
        expect(parseRepositoryFragment("#")).toEqual({
            pair: null,
            tab: "overview",
        });
        expect(repositoryFragment({ pair: null, tab: "overview" })).toBe(
            "#tab=overview",
        );
    });
    test.each(REPOSITORY_TABS)(
        "roundtrips the selected pair and %s tab",
        (tab) => {
            const fragment = repositoryFragment({ pair, tab });
            expect(parseRepositoryFragment(fragment)).toEqual({ pair, tab });
            expect(parseRepositoryFragment(fragment.slice(1))).toEqual({
                pair,
                tab,
            });
            expect(
                Object.isFrozen(parseRepositoryFragment(fragment).pair),
            ).toBe(true);
            expect(fragment).toBe(
                `#commit_sha=${pair.commitSha}&publication_id=${pair.publicationId}&tab=${tab}`,
            );
            expect(isRepositoryTab(tab)).toBe(true);
        },
    );
    test("old retained and repaired instances with the same SHA remain separate", () => {
        const repaired = { ...pair, publicationId: "c".repeat(32) };
        const original = parseRepositoryFragment(
            repositoryFragment({ pair, tab: "files" }),
        );
        const replacement = parseRepositoryFragment(
            repositoryFragment({ pair: repaired, tab: "files" }),
        );
        expect(original.pair?.commitSha).toBe(replacement.pair?.commitSha);
        expect(original.pair?.publicationId).not.toBe(
            replacement.pair?.publicationId,
        );
        expect(publicationIdentity(exactPublication(target, pair))).not.toBe(
            publicationIdentity(exactPublication(target, repaired)),
        );
        expect(original.pair).toEqual(pair); // No later current/ref state can rewrite a bookmark.
    });
    test.each([
        "#commit_sha=" + pair.commitSha,
        "#publication_id=" + pair.publicationId,
        `#commit_sha=${pair.commitSha}&publication_id=`,
        `#commit_sha=&publication_id=${pair.publicationId}`,
        "#commit_sha=current&publication_id=" + pair.publicationId,
        `#commit_sha=${"a".repeat(39)}&publication_id=${pair.publicationId}`,
        `#commit_sha=${"A".repeat(40)}&publication_id=${pair.publicationId}`,
        `#commit_sha=${pair.commitSha}&publication_id=${"b".repeat(31)}`,
        `#commit_sha=${pair.commitSha}&publication_id=${"B".repeat(32)}`,
        `#commit_sha=${pair.commitSha}&publication_id=${pair.publicationId}&commit_sha=${pair.commitSha}`,
        "#tab=files&tab=files",
        "#tab=files&%74ab=overview",
        "#tab=unknown",
        "#tab=Files",
        "#tab=",
        "#cursor=opaque",
        "#authority=old",
        "#generation=2",
        "#repository_type=model",
        "#operation_id=" + "a".repeat(32),
        "#__proto__=x",
        "#tab",
        "#=overview",
        "#tab=files&",
        "#tab=%",
        "#tab=%F0%9F",
        "#tab=%ED%A0%80",
        "#tab=over+view",
        "#tab=overview\n",
        "#tab=\ud800",
    ])("refuses partial, unsafe or unsupported selection %s", (fragment) => {
        expect(() => parseRepositoryFragment(fragment)).toThrow(
            RepositoryRouteError,
        );
    });
    test("raw encoded work is bounded before any decoding or normalization", () => {
        expect(MAX_REPOSITORY_FRAGMENT_BYTES).toBe(8192);
        expect(() =>
            parseRepositoryFragment(
                "#" + "x".repeat(MAX_REPOSITORY_FRAGMENT_BYTES),
            ),
        ).toThrow(RepositoryRouteError);
        expect(() =>
            parseRepositoryFragment("#tab=" + "😀".repeat(2048)),
        ).toThrow(RepositoryRouteError);
    });
    test("unknown IDs and locators cannot hide in durable view or target state", () => {
        const view = {
            pair,
            tab: "overview" as const,
            archiveRoot: "/private/archive",
        };
        expect(() => repositoryFragment(view)).toThrow(RepositoryRouteError);
        expect(() =>
            repositoryPath(
                { ...target, repositoryId: "https://foreign/name" },
                "/ui/",
            ),
        ).toThrow(RepositoryRouteError);
        expect(() =>
            repositoryPath(
                { ...target, repositoryId: "published/repos" },
                "/ui/",
            ),
        ).not.toThrow(); // An ID is never interpreted as a raw archive locator.
        expect(
            repositoryPath(
                { ...target, repositoryId: "published/repos" },
                "/ui/",
            ),
        ).toBe("/ui/repositories/model/published/repos");
        expect(isRepositoryTab("../files")).toBe(false);
    });
    test("construction validates identity and leaves caller objects unchanged", () => {
        expect(exactPublication(target, pair)).toEqual({ ...target, ...pair });
        expect(Object.isFrozen(exactPublication(target, pair))).toBe(true);
        expect(() =>
            exactPublication(target, { ...pair, publicationId: "current" }),
        ).toThrow(RepositoryRouteError);
        expect(target).toEqual({
            repositoryType: "model",
            repositoryId: "Owner_1/Repo.v2-X",
        });
        expect(pair.publicationId).toBe("b".repeat(32));
    });
    test("accessors are refused without reading arbitrary route/view data", () => {
        let calls = 0;
        const hostile = {
            pair: null,
            get tab() {
                calls++;
                return "overview" as const;
            },
        };
        expect(() => repositoryFragment(hostile)).toThrow(RepositoryRouteError);
        expect(calls).toBe(0);
        const badTarget = {
            repositoryType: "model" as const,
            get repositoryId() {
                calls++;
                return "owner/name";
            },
        };
        expect(() => repositoryPath(badTarget, "/ui/")).toThrow(
            RepositoryRouteError,
        );
        expect(calls).toBe(0);
    });
});
