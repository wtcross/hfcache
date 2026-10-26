import { createHash } from "node:crypto";
import { afterEach, expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { decodeRepositoryCardRead } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { validateCardDigest } from "../src/wire/card-semantics";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
} from "./read-fixtures";

const sha = "a".repeat(40);
const publicationId = "b".repeat(32);
const fingerprint = "c".repeat(64);
const publication = {
    repositoryType: "model",
    repositoryId: "owner/model",
    commitSha: sha,
    publicationId,
} satisfies Parameters<
    ReturnType<typeof createApiClient>["readRepositoryCard"]
>[0];

function card(overrides: Record<string, unknown> = {}) {
    const markdown = "# Card\n";
    return {
        schema_version: 1,
        kind: "repository_card",
        archive_id: ARCHIVE_ID,
        repository_type: "model",
        repository_id: "owner/model",
        commit_sha: sha,
        publication_id: publicationId,
        publication_generation: 1,
        manifest_path: `published/manifests/models/owner/model/${sha}/${publicationId}.json`,
        manifest_digest: "d".repeat(64),
        source_path: "README.md",
        expected_source_sha256: "e".repeat(64),
        captured_at: "2026-10-25T00:00:00.000000Z",
        presentation_version: "markdown-1",
        state: "present",
        markdown,
        presentation_sha256: createHash("sha256")
            .update(markdown)
            .digest("hex"),
        diagnostics: [],
        ...overrides,
    };
}

function encoded(value: unknown): unknown {
    return parseWireJson(JSON.stringify(value));
}

function response(payload: unknown, failed = false) {
    return {
        ...readWire("card read", payload, failed),
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
    };
}

function client(fetcher: typeof fetch) {
    return createApiClient({
        scope: createApiScope({
            origin: "https://archive.invalid",
            publicPrefix: "/management",
            authorityEpoch: "card-epoch",
            subject: "card-reader",
            credentialClass: "rest-reader",
            instanceId: null,
            archiveId: ARCHIVE_ID,
            configFingerprint: fingerprint,
        }),
        fetcher,
    });
}

afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});

test("closed projection reconstructs every unavailable state and exact capture metadata", () => {
    expect(decodeRepositoryCardRead(encoded(card()))).toEqual(card());
    for (const state of [
        "absent",
        "unsupported",
        "oversize",
        "unsafe",
        "failed",
    ]) {
        const value = card({
            state,
            markdown: null,
            presentation_sha256: null,
            ...(state === "absent"
                ? { source_path: null, expected_source_sha256: null }
                : {}),
        });
        expect(decodeRepositoryCardRead(encoded(value))).toEqual(value);
    }
    for (const noSource of [false, true]) {
        const value = card({
            state: "not_captured",
            markdown: null,
            presentation_sha256: null,
            captured_at: null,
            presentation_version: null,
            ...(noSource
                ? { source_path: null, expected_source_sha256: null }
                : {}),
        });
        expect(decodeRepositoryCardRead(encoded(value))).toEqual(value);
    }
});

test.each([
    { schema_version: 2 },
    { schema_version: true },
    { state: "future" },
    { kind: "arbitrary" },
    { presentation_version: "markdown-2" },
    { source_path: "nested/README.md" },
    { expected_source_sha256: null },
    { captured_at: null },
    { markdown: null },
    { presentation_sha256: null },
    { diagnostics: ["private raw reason"] },
    { diagnostics: ["source_changed", "read_failed"] },
    { diagnostics: ["read_failed", "read_failed"] },
    { extra: "unreviewed" },
    { state: "absent" },
    { state: "failed" },
    { state: "not_captured" },
])("strict decoder refuses version/state/coherence mutation %j", (change) => {
    expect(() => decodeRepositoryCardRead(encoded(card(change)))).toThrow();
});

test("missing capture cannot invent capture identity or diagnostics", () => {
    const missing = card({
        state: "not_captured",
        captured_at: null,
        presentation_version: null,
        markdown: null,
        presentation_sha256: null,
    });
    for (const change of [
        { captured_at: "2026-10-25T00:00:00.000000Z" },
        { presentation_version: "markdown-1" },
        { diagnostics: ["readme_absent"] },
        { source_path: null },
    ])
        expect(() =>
            decodeRepositoryCardRead(encoded({ ...missing, ...change })),
        ).toThrow();
});

test.each([
    ["a".repeat(1024 * 1024 - 2), true],
    ["a".repeat(1024 * 1024 - 1), false],
    ['"'.repeat(1024 * 512 - 1), true],
    ['"'.repeat(1024 * 512), false],
    ["😺".repeat(1024 * 256 - 1), true],
    ["😺".repeat(1024 * 256), false],
])("UTF8 and JSON-string size boundaries %#", (markdown, accepted) => {
    const value = encoded(card({ markdown }));
    if (accepted) expect(() => decodeRepositoryCardRead(value)).not.toThrow();
    else expect(() => decodeRepositoryCardRead(value)).toThrow();
});

test.each(["# Card\n", "", "# Unicode 😺 café\n"])(
    "typed read verifies native SHA256 before exposing body %j",
    async (markdown) => {
        const payload = card({
            markdown,
            presentation_sha256: createHash("sha256")
                .update(markdown)
                .digest("hex"),
        });
        const fetcher = vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(response(payload)));
        const result = await client(fetcher).readRepositoryCard(publication);
        expect(result.kind).toBe("success");
        if (result.kind === "success") expect(result.payload).toEqual(payload);
        expect(fetcher).toHaveBeenCalledOnce();
        const [url, options] = fetcher.mock.calls[0] ?? [];
        expect(url instanceof URL ? url.pathname : "").toBe(
            `/management/api/v1/repositories/model/owner/model/publications/${sha}/${publicationId}/card`,
        );
        expect(options).toMatchObject({
            method: "GET",
            credentials: "same-origin",
            mode: "same-origin",
            cache: "no-store",
            redirect: "error",
        });
    },
);

test("synchronous reconstruction does not claim crypto verification; actual typed read refuses tamper", async () => {
    const tampered = card({ markdown: "Changed after digest" });
    expect(() => decodeRepositoryCardRead(encoded(tampered))).not.toThrow();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response(tampered)));
    expect(await client(fetcher).readRepositoryCard(publication)).toEqual({
        kind: "protocol_failure",
        reason: "semantic",
    });
    expect(fetcher).toHaveBeenCalledOnce();
});

test("missing secure-context crypto is a classified refusal, never unverified success", async () => {
    vi.stubGlobal("crypto", undefined);
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response(card())));
    expect(await client(fetcher).readRepositoryCard(publication)).toEqual({
        kind: "protocol_failure",
        reason: "unsupported_engine",
    });
    await expect(validateCardDigest(card())).rejects.toThrow(
        "unsupported_engine",
    );
});

test.each([
    { repository_type: "dataset" },
    { repository_id: "owner/other" },
    { commit_sha: "f".repeat(40) },
    { publication_id: "f".repeat(32) },
    { archive_id: "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb" },
    { manifest_path: "published/manifests/models/other/path.json" },
])("request binding refuses mixed provenance %j", async (change) => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response(card(change))));
    expect(await client(fetcher).readRepositoryCard(publication)).toEqual({
        kind: "protocol_failure",
        reason: "semantic",
    });
    expect(fetcher).toHaveBeenCalledOnce();
});

test("404 vanished publication never retries current or a different publication", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFARG004", 10), 404));
    expect(await client(fetcher).readRepositoryCard(publication)).toMatchObject(
        {
            kind: "api_problem",
            status: 404,
        },
    );
    expect(fetcher).toHaveBeenCalledOnce();
});

test("not-captured body needs no crypto and nonzero domain evidence remains preserved", async () => {
    vi.stubGlobal("crypto", undefined);
    const missing = card({
        state: "not_captured",
        captured_at: null,
        presentation_version: null,
        markdown: null,
        presentation_sha256: null,
    });
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response(missing)));
    expect(await client(fetcher).readRepositoryCard(publication)).toMatchObject(
        { kind: "success", payload: missing },
    );
    fetcher.mockResolvedValue(jsonResponse(response({}, true)));
    expect(await client(fetcher).readRepositoryCard(publication)).toMatchObject(
        {
            kind: "domain_failure",
            response: { envelope: { exit_code: 20 } },
        },
    );
});

test("response has its own 2MiB ceiling before decode", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response(" ".repeat(2 * 1024 * 1024 + 1), {
            headers: { "Content-Type": "application/json" },
        }),
    );
    expect(await client(fetcher).readRepositoryCard(publication)).toMatchObject(
        {
            kind: "protocol_failure",
            reason: "bounds",
        },
    );
});

test("late crypto completion cannot expose an aborted request", async () => {
    const actual = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode("# Card\n"),
    );
    let finish: ((value: ArrayBuffer) => void) | undefined;
    vi.spyOn(crypto.subtle, "digest").mockImplementation(
        () =>
            new Promise<ArrayBuffer>((resolve) => {
                finish = resolve;
            }),
    );
    const abort = new AbortController();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response(card())));
    const pending = client(fetcher).readRepositoryCard(publication, {
        signal: abort.signal,
    });
    await vi.waitFor(() => {
        expect(finish).toBeDefined();
    });
    abort.abort();
    finish?.(actual);
    expect(await pending).toEqual({ kind: "aborted" });
});

test("request publication binding is captured before asynchronous transport", async () => {
    const mutable = { ...publication };
    const fetcher = vi.fn<typeof fetch>().mockImplementation(() => {
        mutable.publicationId = "f".repeat(32);
        return Promise.resolve(jsonResponse(response(card())));
    });
    expect(await client(fetcher).readRepositoryCard(mutable)).toMatchObject({
        kind: "success",
    });
});
