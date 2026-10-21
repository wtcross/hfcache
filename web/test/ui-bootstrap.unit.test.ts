import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, test, vi } from "vitest";
import {
    verifyBootstrapContext,
    bootstrapScope,
    releaseChanged,
    checkRelease,
} from "../src/bootstrap";
import {
    canonicalToolchain,
    applyUiSemantic,
    uiSemanticIds,
} from "../src/wire/ui-semantics";
import {
    decodeUiBootstrap,
    decodeUiAssetManifest,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { uriPath } from "../src/api/url-paths";
import { uiBootstrapFixture } from "./ui-fixtures";
const bootstrap = uiBootstrapFixture();
const metadata = {
    base: "/ui/",
    bootstrap: "/ui/bootstrap.json",
    fingerprint: bootstrap.build.asset_manifest_sha256,
};
const compiled = {
    source: bootstrap.build.metadata.source_snapshot_sha256,
    application: bootstrap.build.metadata.application_version,
    wire: bootstrap.wire_source_digest,
};

test("platform SHA256 binds independent canonical toolchain bytes before trusting bootstrap", async () => {
    const canonical = canonicalToolchain(bootstrap.build.metadata.toolchain);
    expect(canonical).toBe(
        '{\n  "node": "24.18.1",\n  "pnpm": "11.18.0",\n  "typescript": "6.0.3",\n  "vite": "8.3.4"\n}\n',
    );
    expect(createHash("sha256").update(canonical).digest("hex")).toBe(
        bootstrap.build.metadata.toolchain_sha256,
    );
    const actual = decodeUiBootstrap(parseWireJson(JSON.stringify(bootstrap)));
    await expect(
        verifyBootstrapContext(
            actual,
            metadata,
            bootstrap.configured_origin,
            compiled,
        ),
    ).resolves.toBeUndefined();
    expect(bootstrapScope(actual)).toMatchObject({
        subject: "administrator",
        archiveId: bootstrap.configured_archive_id,
        configFingerprint: null,
        publicPrefix: "",
    });
});
test("a later bounded bootstrap detects release/authority changes without adopting or replaying data", async () => {
    const fetcher =
        (value: unknown): typeof fetch =>
        () =>
            Promise.resolve(
                new Response(JSON.stringify(value), {
                    headers: { "content-type": "application/json" },
                }),
            );
    await expect(checkRelease(bootstrap, fetcher(bootstrap))).resolves.toBe(
        false,
    );
    const next = {
        ...bootstrap,
        build: { ...bootstrap.build, asset_manifest_sha256: "0".repeat(64) },
    };
    await expect(checkRelease(bootstrap, fetcher(next))).resolves.toBe(true);
    await expect(
        checkRelease(
            bootstrap,
            fetcher({
                ...bootstrap,
                instance_id: "9".repeat(32),
                authority_epoch: "9".repeat(32),
            }),
        ),
    ).resolves.toBe(true);
    await expect(
        checkRelease(
            bootstrap,
            fetcher({
                ...bootstrap,
                user: {
                    ...bootstrap.user,
                    subject: "new-admin",
                    display_name: "new-admin",
                },
            }),
        ),
    ).resolves.toBe(true);
    await expect(
        checkRelease(
            bootstrap,
            fetcher({
                ...bootstrap,
                configured_archive_id: "99999999-9999-9999-9999-999999999999",
            }),
        ),
    ).resolves.toBe(true);
    await expect(
        checkRelease(
            bootstrap,
            fetcher({
                ...bootstrap,
                configured_origin: "https://foreign.invalid",
            }),
        ),
    ).rejects.toThrow();
    await expect(
        checkRelease(
            bootstrap,
            fetcher({
                ...bootstrap,
                paths: { ...bootstrap.paths, mcp_base: null },
            }),
        ),
    ).rejects.toThrow();
    expect(bootstrap.build.asset_manifest_sha256).toBe("2".repeat(64));
});
test("independent UI artifact golden enforces MIME/root ownership, complete sorted membership and aggregate bytes", () => {
    const manifest = decodeUiAssetManifest(
        parseWireJson(
            readFileSync(
                fileURLToPath(
                    new URL(
                        "../../tests/fixtures/schemas/ui-asset-manifest.json",
                        import.meta.url,
                    ),
                ),
                "utf8",
            ),
        ),
    );
    const decode = (value: unknown) =>
        decodeUiAssetManifest(parseWireJson(JSON.stringify(value)));
    expect(() => decode(manifest)).not.toThrow();
    for (const members of [
        [...manifest.members].reverse(),
        manifest.members.slice(1),
        [...manifest.members, manifest.members[0]],
        manifest.members.map((item) =>
            item.path === "index.html" ? { ...item, bytes: 0 } : item,
        ),
        manifest.members.map((item) =>
            item.path === "index.html"
                ? { ...item, path: "assets/page.html" }
                : item,
        ),
        manifest.members.map((item) =>
            item.path === "THIRD_PARTY_NOTICES.txt"
                ? { ...item, path: "other.txt" }
                : item,
        ),
        manifest.members.map((item) =>
            item.path === "licenses.json"
                ? { ...item, sha256: "0".repeat(64) }
                : item,
        ),
        [
            ...manifest.members,
            ...Array.from({ length: 8 }, (_, i) => ({
                path: `assets/large-${String(i)}.js`,
                bytes: 8388608,
                sha256: "0".repeat(64),
                mime: "text/javascript",
            })),
        ].sort((a, b) => (a.path < b.path ? -1 : 1)),
    ])
        expect(() => decode({ ...manifest, members })).toThrow();
});
test("model-level UI ports reject structurally valid identity/path/permission contradictions", () => {
    const decode = (value: unknown) =>
        decodeUiBootstrap(parseWireJson(JSON.stringify(value)));
    for (const value of [
        { ...bootstrap, authority_epoch: "0".repeat(32) },
        { ...bootstrap, wire_source_digest: "0".repeat(64) },
        {
            ...bootstrap,
            paths: { ...bootstrap.paths, effective_prefix: "/other" },
        },
        {
            ...bootstrap,
            user: { ...bootstrap.user, display_name: "other-admin" },
        },
        {
            ...bootstrap,
            user: { ...bootstrap.user, rest_capabilities: ["write", "read"] },
        },
        {
            ...bootstrap,
            user: {
                ...bootstrap.user,
                admin_permissions: [
                    ...bootstrap.user.admin_permissions,
                ].reverse(),
            },
        },
        {
            ...bootstrap,
            user: {
                ...bootstrap.user,
                admin_permissions: bootstrap.user.admin_permissions.map(
                    (item) => ({
                        ...item,
                        granted: false,
                        effective: true,
                        reason: "allowed",
                    }),
                ),
            },
        },
        {
            ...bootstrap,
            user: {
                ...bootstrap.user,
                admin_permissions: bootstrap.user.admin_permissions.map(
                    (item) => ({ ...item, reason: "allowed" }),
                ),
            },
        },
    ])
        expect(() => decode(value)).toThrow();
    for (const [id, value] of [
        ["_ascii", null],
        ["_ascii", ""],
        ["_ascii", "管理"],
        ["_one", true],
        ["_origin", "not a URL"],
        ["_prefix", "/a/"],
        ["_prefix", "/"],
        ["_prefix", "/a/../b"],
        ["_prefix", "/a//b"],
        ["_prefix", "/" + "a".repeat(1024)],
        ["_asset_path", "assets/" + "a".repeat(256) + ".js"],
        ["_asset_path", "a/".repeat(8) + "x.js"],
        ["_subject", null],
    ] as const)
        expect(() => {
            applyUiSemantic("hfcache.ui_models." + id, value);
        }).toThrow();
    expect(() => {
        applyUiSemantic("hfcache.ui_models._prefix", "/管理");
    }).not.toThrow();
});
test("context refuses mismatched origin, separately delivered fingerprint, source, version and wire", async () => {
    for (const [meta, origin, identity] of [
        [metadata, "https://foreign.invalid", compiled],
        [
            { ...metadata, base: "/wrong/" },
            bootstrap.configured_origin,
            compiled,
        ],
        [
            { ...metadata, bootstrap: "/wrong" },
            bootstrap.configured_origin,
            compiled,
        ],
        [
            { ...metadata, fingerprint: "0".repeat(64) },
            bootstrap.configured_origin,
            compiled,
        ],
        [
            metadata,
            bootstrap.configured_origin,
            { ...compiled, source: "0".repeat(64) },
        ],
        [
            metadata,
            bootstrap.configured_origin,
            { ...compiled, application: "other" },
        ],
        [
            metadata,
            bootstrap.configured_origin,
            { ...compiled, wire: "0".repeat(64) },
        ],
    ] as const)
        await expect(
            verifyBootstrapContext(bootstrap, meta, origin, identity),
        ).rejects.toThrow();
    await expect(
        verifyBootstrapContext(
            {
                ...bootstrap,
                build: {
                    ...bootstrap.build,
                    metadata: {
                        ...bootstrap.build.metadata,
                        toolchain_sha256: "0".repeat(64),
                    },
                },
            },
            metadata,
            bootstrap.configured_origin,
            compiled,
        ),
    ).rejects.toThrow();
});
test("absence of the complete platform crypto object produces explicit unsupported-engine refusal", async () => {
    vi.stubGlobal("crypto", undefined);
    try {
        await expect(
            verifyBootstrapContext(
                bootstrap,
                metadata,
                bootstrap.configured_origin,
                compiled,
            ),
        ).rejects.toThrow("unsupported_engine");
    } finally {
        vi.unstubAllGlobals();
    }
});
test("URI encoding preserves ordinary native paths and escapes Unicode/unsafe ASCII", () => {
    expect(uriPath('/管理/"<>/ui/')).toBe("/%E7%AE%A1%E7%90%86/%22%3C%3E/ui/");
    expect(uriPath("/management/api/v1/operations/id")).toBe(
        "/management/api/v1/operations/id",
    );
    for (const raw of [
        "",
        "//foreign/ui/",
        "/a//b",
        "/a/../b",
        "/a/./b",
        "/a%20",
        "/a?x",
        "/a#x",
        "/a\\x",
        "/a x",
        "/a\n",
        "/a\ud800",
    ])
        expect(() => uriPath(raw)).toThrow();
});
test("release checks retain exact original identities and request user-controlled update", () => {
    expect(releaseChanged(bootstrap, bootstrap)).toBe(false);
    expect(
        releaseChanged(bootstrap, {
            ...bootstrap,
            build: {
                ...bootstrap.build,
                asset_manifest_sha256: "0".repeat(64),
            },
        }),
    ).toBe(true);
    expect(
        releaseChanged(bootstrap, {
            ...bootstrap,
            wire_source_digest: "0".repeat(64),
        }),
    ).toBe(true);
    expect(
        releaseChanged(bootstrap, {
            ...bootstrap,
            build: {
                ...bootstrap.build,
                metadata: {
                    ...bootstrap.build.metadata,
                    source_snapshot_sha256: "0".repeat(64),
                },
            },
        }),
    ).toBe(true);
});
test("unknown UI semantic authorities refuse rather than accept generic data", () => {
    expect(uiSemanticIds.length).toBe(13);
    expect(() => {
        applyUiSemantic("unreviewed", {});
    }).toThrow();
    expect(() => {
        applyUiSemantic("hfcache.ui_models._subject", "administrator\n");
    }).toThrow();
    expect(() => {
        applyUiSemantic(
            "hfcache.ui_models._origin",
            "https://archive.invalid:443",
        );
    }).toThrow();
    expect(() => {
        applyUiSemantic("hfcache.ui_models._asset_path", "assets//bad.js");
    }).toThrow();
    expect(() => {
        applyUiSemantic("hfcache.ui_models._prefix", "//foreign");
    }).toThrow();
    expect(() => {
        applyUiSemantic("hfcache.ui_models._instance", "0".repeat(33));
    }).toThrow();
    expect(() => decodeUiAssetManifest(parseWireJson("{}"))).toThrow();
});
