import {
    mkdtempSync,
    mkdirSync,
    writeFileSync,
    chmodSync,
    symlinkSync,
    readFileSync,
} from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { expect, test } from "vitest";
import { requireOwnedProfile } from "./read-api/ownership";

function fixture() {
    const repository = mkdtempSync(join(tmpdir(), "hfcache-read-ownership-"));
    const web = join(repository, "web");
    mkdirSync(web);
    const scratch = join(repository, ".scratch");
    mkdirSync(scratch, { mode: 0o700 });
    const owner = join(scratch, "new-owned-fixture");
    mkdirSync(owner, { mode: 0o700 });
    const profile = join(owner, "root");
    mkdirSync(profile, { mode: 0o700 });
    const marker = join(owner, "fixture.json");
    writeFileSync(
        marker,
        JSON.stringify({
            purpose: "WEB-003-owned-read-fixture",
            id: "a".repeat(32),
        }),
        { mode: 0o600 },
    );
    const cache = join(web, ".cache/ms-playwright"),
        token = join(profile, "reader.token");
    return { repository, web, scratch, owner, profile, marker, cache, token };
}

test("a private generated owned profile passes before runtime effects", () => {
    const item = fixture();
    expect(() => {
        requireOwnedProfile(item.profile, item.web, item.cache, item.token);
    }).not.toThrow();
});

test.each([
    "/srv/hfcache/root",
    "/etc/hfcache/root",
    "/tmp/unowned/root",
    "relative/root",
])(
    "unrelated profile %s refuses lexically before any target access",
    (profile) => {
        expect(() => {
            requireOwnedProfile(
                profile,
                "/nonexistent-owned-repository/web",
                "/invalid/cache",
                "/invalid/token",
            );
        }).toThrow("Only a generated repository");
    },
);

test("a linked ancestor cannot grant fixture ownership", () => {
    const item = fixture();
    const link = join(item.scratch, "alias");
    symlinkSync(item.owner, link, "dir");
    expect(() => {
        requireOwnedProfile(
            join(link, "root"),
            item.web,
            item.cache,
            join(link, "root/reader.token"),
        );
    }).toThrow("ancestry");
});

test("an unrelated cache or credential path cannot be supplied to a generated profile", () => {
    const item = fixture();
    expect(() => {
        requireOwnedProfile(
            item.profile,
            item.web,
            "/unrelated/cache",
            item.token,
        );
    }).toThrow("Only a generated repository");
    expect(() => {
        requireOwnedProfile(
            item.profile,
            item.web,
            item.cache,
            "/etc/hfcache/writer.token",
        );
    }).toThrow("Only a generated repository");
});

test.each([
    "wrong-purpose",
    "unsafe-marker-mode",
    "linked-marker",
    "public-profile",
    "writable-ancestor",
])("ownership rejection preserves existing marker evidence: %s", (kind) => {
    const item = fixture();
    if (kind === "wrong-purpose")
        writeFileSync(
            item.marker,
            JSON.stringify({ purpose: "unrelated-work", id: "a".repeat(32) }),
        );
    if (kind === "unsafe-marker-mode") chmodSync(item.marker, 0o644);
    if (kind === "public-profile") chmodSync(item.profile, 0o755);
    if (kind === "writable-ancestor") chmodSync(item.scratch, 0o777);
    if (kind === "linked-marker") {
        const other = join(item.owner, "other");
        writeFileSync(other, "do not erase", { mode: 0o600 });
        // A second owner retains the existing original marker untouched.
        const linkedOwner = join(item.scratch, "linked-owner");
        mkdirSync(linkedOwner, { mode: 0o700 });
        const linkedProfile = join(linkedOwner, "root");
        mkdirSync(linkedProfile, { mode: 0o700 });
        symlinkSync(other, join(linkedOwner, "fixture.json"));
        expect(() => {
            requireOwnedProfile(
                linkedProfile,
                item.web,
                item.cache,
                join(linkedProfile, "reader.token"),
            );
        }).toThrow("marker is unsafe");
        expect(readFileSync(other, "utf8")).toBe("do not erase");
        return;
    }
    const before = readFileSync(item.marker);
    expect(() => {
        requireOwnedProfile(item.profile, item.web, item.cache, item.token);
    }).toThrow();
    expect(readFileSync(item.marker)).toEqual(before);
});
