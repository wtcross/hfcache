/** Closed new wire surfaces exercise the existing generated decoder/transport. */
import { expect, test, vi } from "vitest";
import { ApiClient } from "../src/api/client";
import {
    decodeJobReadiness,
    decodeOriginalIntent,
    routeContracts,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { jsonResponse, ARCHIVE_ID } from "./read-fixtures";
import { scope } from "./state-fixtures";

const readiness = {
    schema_version: 1,
    archive_id: ARCHIVE_ID,
    config_fingerprint: scope.configFingerprint,
    archive: null,
    hub: false,
    control: true,
    archive_writable: null,
    verification_available: false,
};
const unknown = {
    schema_version: 1,
    archive_id: ARCHIVE_ID,
    state: "unknown",
    operation: null,
    disposition: null,
};
const decode = (value: unknown) => parseWireJson(JSON.stringify(value));
test.each([
    { ...readiness, extra: false },
    { ...readiness, archive: "false" },
    { ...readiness, schema_version: true },
    { ...readiness, archive_id: "foreign" },
])("readiness rejects malformed or coercive facts %j", (value) => {
    expect(() => decodeJobReadiness(decode(value))).toThrow();
});
test("nullable readiness remains distinct and named route registry describes real raw documents", () => {
    expect(decodeJobReadiness(decode(readiness))).toEqual(readiness);
    expect(decodeOriginalIntent(decode(unknown))).toEqual(unknown);
    expect(routeContracts.job_readiness_default.responseKind).toBe("raw");
    expect(routeContracts.original_intent_default.path).toBe(
        "/api/v1/operations/intent",
    );
    expect(routeContracts.retire_intent_default.method).toBe("POST");
});
test.each([
    { ...unknown, state: "admitted" },
    { ...unknown, state: "not_admitted" },
    { ...unknown, archive_id: "12345678-1234-1234-1234-123456789abc" },
    { ...unknown, disposition: { key_digest: "forbidden" } },
])(
    "typed own-key GET refuses contradictory/foreign/private projection %j",
    async (value) => {
        const client = new ApiClient({
            scope,
            fetcher: () => Promise.resolve(jsonResponse(value)),
        });
        const result = await client
            .readOriginalIntent("owned-original-key")
            .catch(() => null);
        expect(result?.kind).not.toBe("success");
    },
);
test("readiness GET and explicit retirement preserve fixed authenticated controls and body", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValueOnce(jsonResponse(readiness))
        .mockResolvedValueOnce(jsonResponse(unknown));
    const client = new ApiClient({ scope, fetcher });
    expect((await client.readJobReadiness()).kind).toBe("success");
    expect((await client.retireOriginalIntent("owned-original-key")).kind).toBe(
        "success",
    );
    expect(fetcher).toHaveBeenCalledTimes(2);
    const get = fetcher.mock.calls[0],
        post = fetcher.mock.calls[1];
    expect(get?.[0] instanceof URL ? get[0].href : "missing").toBe(
        scope.origin + "/api/v1/jobs/readiness",
    );
    expect(get?.[1]).toMatchObject({
        method: "GET",
        credentials: "same-origin",
        mode: "same-origin",
        redirect: "error",
        cache: "no-store",
    });
    expect(new Headers(get?.[1]?.headers).has("Idempotency-Key")).toBe(false);
    expect(post?.[0] instanceof URL ? post[0].href : "missing").toBe(
        scope.origin + "/api/v1/operations/intent/retire",
    );
    expect(post?.[1]?.body).toBe(
        '{"schema_version":1,"confirm":"retire_unknown"}',
    );
    expect(new Headers(post?.[1]?.headers).get("Idempotency-Key")).toBe(
        "owned-original-key",
    );
    expect(new Headers(post?.[1]?.headers).get("X-Hfcache-Request")).toBe("1");
});
test("raw responses retain the 64KiB ceiling and are never automatically retried", async () => {
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response("x", {
            headers: {
                "Content-Type": "application/json",
                "Content-Length": "65537",
            },
        }),
    );
    const result = await new ApiClient({ scope, fetcher }).readOriginalIntent(
        "owned-original-key",
    );
    expect(result.kind).toBe("unavailable");
    expect(fetcher).toHaveBeenCalledOnce();
});
