import { expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import {
    jsonResponse,
    problemWire,
    readWire,
    REQUEST_ID,
    versionPayload,
} from "./read-fixtures";
import {
    createApiScope,
    publicationIdentity,
    queryIdentity,
    repositorySegments,
} from "../src/api/identity";
import type { ApiScope } from "../src/api/identity";
import { WireError } from "../src/wire/json";

const BASE: ApiScope = {
    origin: "https://archive.invalid",
    publicPrefix: "/management",
    authorityEpoch: "reader-epoch-1",
    subject: "fixture-reader",
    credentialClass: "rest-reader",
    instanceId: "1".repeat(32),
    archiveId: "3f2a1c88-7b40-4a2e-9c1d-0e5b6a7f8d90",
    configFingerprint: "2".repeat(64),
};

test("scope projection never retains a credential-like extra from a structurally typed object", () => {
    const input = { ...BASE, password: "independent-private-marker" };
    const scope = createApiScope(input);
    expect(Object.hasOwn(scope, "password")).toBe(false);
    expect(JSON.stringify(scope)).not.toContain("independent-private-marker");
});

test.each([
    "",
    "/management",
    "/a.b_/with-2",
    "//attacker.invalid",
    "/管理/Σ",
    "/a@b:42",
])("configured public prefix is canonical and relative: %s", (publicPrefix) => {
    const scope = createApiScope({ ...BASE, publicPrefix });
    expect(scope.publicPrefix).toBe(publicPrefix);
    expect(Object.isFrozen(scope)).toBe(true);
});

test.each([
    "/",
    "/management/",
    "///attacker.invalid",
    "/a//b",
    "/../x",
    "/a/.",
    "/a/%2e%2e",
    "https://attacker.invalid",
    "/a?query",
    "/a#fragment",
    "/a\\b",
    "/a\n",
])(
    "unsafe configured prefix refuses before URL construction: %s",
    (publicPrefix) => {
        expect(() => createApiScope({ ...BASE, publicPrefix })).toThrow(
            WireError,
        );
    },
);

test.each([
    "https://user:password@archive.invalid",
    "https://archive.invalid/",
    "https://archive.invalid/path",
    "https://archive.invalid?q=x",
    "https://archive.invalid#x",
    "//archive.invalid",
    "javascript:alert(1)",
    "https://archive.invalid:443",
])("origin is exactly canonical, without path or credentials: %s", (origin) => {
    expect(() => createApiScope({ ...BASE, origin })).toThrow();
});

test.each([
    "organization/model",
    "a.b/name_with-dash",
    "A/0",
    "a/" + "z".repeat(96),
])("identity segments preserve allowed literal names: %s", (id) => {
    expect(repositorySegments("model", id).join("/")).toBe(id);
});

test.each([
    "one-segment",
    "/name",
    "org/",
    "org/name/extra",
    "../name",
    "org/..",
    ".hidden/name",
    "org/name\n",
    "org/name\r\n",
    "org/name?x",
    "org/name%2Fother",
    "org/name#hash",
    "org/é",
    "org/" + "z".repeat(97),
])("unsafe identity cannot select a relative or external target: %s", (id) => {
    expect(() => repositorySegments("model", id)).toThrow(WireError);
});

test("query identity includes every authority dimension and exact publication identity", () => {
    const scope = createApiScope(BASE);
    const publication = {
        repositoryType: "model",
        repositoryId: "org/model",
        commitSha: "a".repeat(40),
        publicationId: "b".repeat(32),
    } as const;
    const key = queryIdentity(scope, "catalog.detail", [], publication);
    const changes: readonly ApiScope[] = [
        { ...scope, origin: "https://other.invalid" },
        { ...scope, publicPrefix: "" },
        { ...scope, authorityEpoch: "reader-epoch-2" },
        { ...scope, subject: "other-reader" },
        { ...scope, credentialClass: "rest-writer" },
        { ...scope, instanceId: "3".repeat(32) },
        { ...scope, archiveId: "00000000-0000-4000-8000-000000000001" },
        { ...scope, configFingerprint: "4".repeat(64) },
    ];
    for (const changed of changes)
        expect(
            queryIdentity(
                createApiScope(changed),
                "catalog.detail",
                [],
                publication,
            ),
        ).not.toBe(key);
    expect(
        queryIdentity(scope, "catalog.detail", [], {
            ...publication,
            publicationId: "c".repeat(32),
        }),
    ).not.toBe(key);
    expect(
        queryIdentity(scope, "catalog.detail", [], {
            ...publication,
            repositoryType: "dataset",
        }),
    ).not.toBe(key);
    expect(
        queryIdentity(scope, "catalog.detail", [], {
            ...publication,
            commitSha: "d".repeat(40),
        }),
    ).not.toBe(key);
    expect(
        queryIdentity(scope, "catalog.detail", [], {
            ...publication,
            repositoryId: "other/model",
        }),
    ).not.toBe(key);
    expect(queryIdentity(scope, "catalog.detail")).not.toBe(key);
    expect(
        queryIdentity(
            scope,
            "catalog.detail",
            [["q", "literal value"]],
            publication,
        ),
    ).not.toBe(key);
    expect(key).not.toContain("password");
});

test.each(["a".repeat(39), "A".repeat(40), "a".repeat(40) + "\n"])(
    "exact publication rejects noncanonical SHA %s",
    (commitSha) => {
        expect(() =>
            publicationIdentity({
                repositoryType: "model",
                repositoryId: "org/model",
                commitSha,
                publicationId: "b".repeat(32),
            }),
        ).toThrow(WireError);
    },
);

test("zero-like exact publication IDs remain identities rather than missing values", () => {
    expect(
        publicationIdentity({
            repositoryType: "dataset",
            repositoryId: "org/data",
            commitSha: "0".repeat(40),
            publicationId: "0".repeat(32),
        }),
    ).toBe(
        JSON.stringify(["dataset", "org/data", "0".repeat(40), "0".repeat(32)]),
    );
});

function transport(fetcher: typeof fetch, timeoutMs = 1000) {
    return createApiClient({
        scope: createApiScope({
            ...BASE,
            instanceId: null,
            archiveId: null,
            configFingerprint: null,
        }),
        fetcher,
        timeoutMs,
    });
}

test("a read uses exactly the fixed same-origin URL and safe fetch policy without credential fields", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(readWire("version", versionPayload)));
    const result = await transport(fetcher).readVersion();
    expect(result.kind).toBe("success");
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, options] = fetcher.mock.calls[0] ?? [];
    expect(url instanceof URL ? url.href : url).toBe(
        "https://archive.invalid/management/api/v1/version",
    );
    expect(options).toMatchObject({
        method: "GET",
        credentials: "same-origin",
        mode: "same-origin",
        redirect: "error",
        cache: "no-store",
        referrerPolicy: "no-referrer",
    });
    expect(new Headers(options?.headers).has("Authorization")).toBe(false);
    expect(options?.signal?.aborted).toBe(true);
});

test("a source-valid double-leading-slash prefix remains an inert same-origin path", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(readWire("version", versionPayload)));
    const scope = createApiScope({
        ...BASE,
        publicPrefix: "//attacker.invalid",
        instanceId: null,
        archiveId: null,
        configFingerprint: null,
    });
    const client = createApiClient({ scope, fetcher });
    expect((await client.readVersion()).kind).toBe("success");
    expect(fetcher).toHaveBeenCalledOnce();
    const [url] = fetcher.mock.calls[0] ?? [];
    expect(url).toBeInstanceOf(URL);
    if (!(url instanceof URL))
        throw new Error("Fixed transport did not receive a URL.");
    expect(url.origin).toBe(BASE.origin);
    expect(url.pathname).toBe("//attacker.invalid/api/v1/version");
});

test.each([undefined, null, false, 0, "1", 1.0 + 1, 9007199254740992])(
    "unsupported schema %s refuses without exposing payload facts",
    async (schema_version) => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            jsonResponse({
                ...readWire("version", versionPayload),
                schema_version,
            }),
        );
        const result = await transport(fetcher).readVersion();
        expect(result.kind).toBe("protocol_failure");
        expect(result).not.toHaveProperty("payload");
        expect(fetcher).toHaveBeenCalledOnce();
    },
);

test.each(["application", "huggingface_hub", "python", "transfer_backend"])(
    "missing %s is not filled from any default",
    async (field) => {
        const payload = Object.fromEntries(
            Object.entries(versionPayload).filter(([key]) => key !== field),
        );
        const result = await transport(
            vi
                .fn<typeof fetch>()
                .mockResolvedValue(jsonResponse(readWire("version", payload))),
        ).readVersion();
        expect(result.kind).toBe("protocol_failure");
    },
);

test.each([
    {
        name: "extra top-level field",
        wire: { ...readWire("version", versionPayload), invented: true },
    },
    {
        name: "extra payload field",
        wire: readWire("version", {
            ...versionPayload,
            password: "never expose",
        }),
    },
    { name: "wrong command", wire: readWire("status", versionPayload) },
    {
        name: "reverse microsecond timeline",
        wire: {
            ...readWire("version", versionPayload),
            envelope: {
                ...readWire("version", versionPayload).envelope,
                completed_at: "2026-10-20T12:00:00.000000Z",
            },
        },
    },
])(
    "$name is a protocol failure rather than a partial success",
    async ({ wire }) => {
        expect(
            (
                await transport(
                    vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(wire)),
                ).readVersion()
            ).kind,
        ).toBe("protocol_failure");
    },
);

test("valid failed metadata survives when the typed failed payload is unsupported", async () => {
    const result = await transport(
        vi
            .fn<typeof fetch>()
            .mockResolvedValue(
                jsonResponse(readWire("version", { unexpected: true }, true)),
            ),
    ).readVersion();
    expect(result).toMatchObject({
        kind: "protocol_failure",
        preserved: {
            request_id: REQUEST_ID,
            command: "version",
            exit_code: 20,
            errors: [{ code: "HFMNT001" }],
        },
    });
    expect(result).not.toHaveProperty("payload");
});

test("HTTP200 failed domain outcome remains failed and keeps its original request evidence", async () => {
    const result = await transport(
        vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(readWire("version", {}, true))),
    ).readVersion();
    expect(result).toMatchObject({
        kind: "domain_failure",
        response: {
            request_id: REQUEST_ID,
            envelope: { exit_code: 20, errors: [{ code: "HFMNT001" }] },
        },
        payload: {},
    });
});

test.each([401, 403, 503])(
    "HTTP %s API Problem is distinct from failed Envelope",
    async (status) => {
        const result = await transport(
            vi
                .fn<typeof fetch>()
                .mockResolvedValue(jsonResponse(problemWire(), status)),
        ).readVersion();
        expect(result).toMatchObject({
            kind: "api_problem",
            status,
            problem: { request_id: REQUEST_ID, code: "HFAPI001" },
        });
        expect(result).not.toHaveProperty("payload");
    },
);

test("a future classified problem code is accepted while an exit-class mismatch refuses", async () => {
    const good = await transport(
        vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(problemWire("HFCFG999", 10), 503)),
    ).readVersion();
    const bad = await transport(
        vi
            .fn<typeof fetch>()
            .mockResolvedValue(jsonResponse(problemWire("HFCFG999", 30), 503)),
    ).readVersion();
    expect(good.kind).toBe("api_problem");
    expect(bad.kind).toBe("protocol_failure");
});

test.each([201, 202, 302])(
    "unexpected HTTP %s cannot be treated as a completed read",
    async (status) => {
        expect(
            (
                await transport(
                    vi
                        .fn<typeof fetch>()
                        .mockResolvedValue(jsonResponse(problemWire(), status)),
                ).readVersion()
            ).kind,
        ).toBe("protocol_failure");
    },
);

test("network failure produces one bounded read and never replays it", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockRejectedValue(new TypeError("private network cause"));
    expect(await transport(fetcher).readVersion()).toEqual({
        kind: "transport_failure",
        reason: "network",
    });
    expect(fetcher).toHaveBeenCalledOnce();
});

test("an owned fetch timeout aborts transport and remains separate from domain failure", async () => {
    let signal: AbortSignal | null | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            signal = options?.signal;
            return new Promise((_resolve, reject) => {
                signal?.addEventListener(
                    "abort",
                    () => {
                        reject(new DOMException("Aborted", "AbortError"));
                    },
                    { once: true },
                );
            });
        });
    expect(await transport(fetcher, 5).readVersion()).toEqual({
        kind: "transport_failure",
        reason: "timeout",
    });
    expect(signal?.aborted).toBe(true);
    expect(fetcher).toHaveBeenCalledOnce();
});

test("pre-aborted read never contacts transport", async () => {
    const controller = new AbortController();
    controller.abort();
    const fetcher = vi.fn<typeof fetch>();
    expect(
        await transport(fetcher).readVersion({ signal: controller.signal }),
    ).toEqual({ kind: "aborted" });
    expect(fetcher).not.toHaveBeenCalled();
});

test("caller abort during body consumption cancels the body and never infers failure", async () => {
    let cancelled = false;
    const stream = new ReadableStream<Uint8Array>({
        cancel() {
            cancelled = true;
        },
    });
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response(stream, {
            headers: { "Content-Type": "application/json" },
        }),
    );
    const controller = new AbortController();
    const pending = transport(fetcher).readVersion({
        signal: controller.signal,
    });
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    controller.abort();
    expect(await pending).toEqual({ kind: "aborted" });
    expect(cancelled).toBe(true);
});

test("archive/config identity mismatch refuses even with structurally valid payload", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
            ...readWire("version", versionPayload),
            archive_id: "00000000-0000-4000-8000-000000000001",
            config_fingerprint: "a".repeat(64),
        }),
    );
    const client = createApiClient({ scope: createApiScope(BASE), fetcher });
    expect((await client.readVersion()).kind).toBe("protocol_failure");
});

test("unknown query controls and invalid idempotency lookup keys refuse before fetch", async () => {
    const fetcher = vi.fn<typeof fetch>();
    const client = transport(fetcher);
    const extra = { limit: 1, redirect: "https://attacker.invalid" };
    expect((await client.readStatus({}, extra)).kind).toBe("protocol_failure");
    expect((await client.lookupOperation("unsafe\nkey")).kind).toBe(
        "protocol_failure",
    );
    expect(fetcher).not.toHaveBeenCalled();
});

test.each(["org/name\n", "org/../other", "https://attacker.invalid/path"])(
    "unsafe repository URL input refuses before transport: %s",
    (id) => {
        const fetcher = vi.fn<typeof fetch>();
        expect(() =>
            transport(fetcher).readReference("model", id, "main"),
        ).toThrow(WireError);
        expect(fetcher).not.toHaveBeenCalled();
    },
);
