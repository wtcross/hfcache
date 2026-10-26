import { expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import {
    ARTIFACT_JSON_LIMITS,
    CARD_JSON_LIMITS,
    NORMAL_JSON_LIMITS,
} from "../src/wire/json";
import { ARCHIVE_ID, problemWire } from "./read-fixtures";

const scope = createApiScope({
    origin: "https://archive.invalid",
    publicPrefix: "",
    authorityEpoch: "session",
    subject: "administrator",
    credentialClass: "rest-reader",
    instanceId: null,
    archiveId: ARCHIVE_ID,
    configFingerprint: null,
});

test.each([0, -1, 1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1])(
    "invalid consumer response ceiling refuses before transport: %s",
    async (responseByteLimit) => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(new Response());
        const result = await createApiClient({ scope, fetcher }).readVersion({
            responseByteLimit,
        });
        expect(result).toEqual({ kind: "protocol_failure", reason: "bounds" });
        expect(fetcher).not.toHaveBeenCalled();
    },
);

test("the exact UTF8 ceiling preserves a classified refusal; one byte less cannot expose it", async () => {
    const problem = problemWire("HFAPI005", 20);
    problem.message = "界".repeat(10);
    const raw = JSON.stringify(problem);
    const size = new TextEncoder().encode(raw).byteLength;
    const fetcher = vi.fn(() =>
        Promise.resolve(
            new Response(raw, {
                status: 503,
                headers: { "Content-Type": "application/json" },
            }),
        ),
    );
    const client = createApiClient({ scope, fetcher });
    expect(await client.readVersion({ responseByteLimit: size })).toMatchObject(
        {
            kind: "api_problem",
            status: 503,
            problem: { code: "HFAPI005" },
        },
    );
    expect(await client.readVersion({ responseByteLimit: size - 1 })).toEqual({
        kind: "protocol_failure",
        reason: "bounds",
    });
});

test.each(["normal", "artifact", "card"] as const)(
    "consumer ceiling cannot enlarge the %s route ceiling",
    async (kind) => {
        const maximum = {
            normal: NORMAL_JSON_LIMITS.maxBytes,
            artifact: ARTIFACT_JSON_LIMITS.maxBytes,
            card: CARD_JSON_LIMITS.maxBytes,
        }[kind];
        const fetcher = vi.fn(() =>
            Promise.resolve(
                new Response("{}", {
                    headers: {
                        "Content-Type": "application/json",
                        "Content-Length": String(maximum + 1),
                    },
                }),
            ),
        );
        const client = createApiClient({ scope, fetcher });
        const options = { responseByteLimit: Number.MAX_SAFE_INTEGER };
        const publication = {
            repositoryType: "model" as const,
            repositoryId: "org/model",
            commitSha: "a".repeat(40),
            publicationId: "b".repeat(32),
        };
        const result =
            kind === "normal"
                ? await client.readVersion(options)
                : kind === "artifact"
                  ? await client.readManifest(publication, options)
                  : await client.readRepositoryCard(publication, options);
        expect(result).toEqual({ kind: "protocol_failure", reason: "bounds" });
        expect(fetcher).toHaveBeenCalledTimes(1);
    },
);

test("unadvertised stream overflow cancels the response without returning a partial value", async () => {
    let cancelled = false;
    const response = new Response(
        new ReadableStream<Uint8Array>({
            start(controller) {
                controller.enqueue(new TextEncoder().encode('"界界界界"'));
            },
            cancel() {
                cancelled = true;
            },
        }),
        { headers: { "Content-Type": "application/json" } },
    );
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(response);
    const result = await createApiClient({ scope, fetcher }).readVersion({
        responseByteLimit: 8,
    });
    expect(result).toEqual({ kind: "protocol_failure", reason: "bounds" });
    expect(cancelled).toBe(true);
});
