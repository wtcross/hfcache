/** Native fetch policy boundary; these controlled responses are not browser/CSRF acceptance. */
import { expect, test, vi } from "vitest";
import { ApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { decodeRequestManagedEditRequest } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
} from "./read-fixtures";
import { receipt, scope } from "./state-fixtures";
import fixtures from "../../tests/fixtures/web_wire/config.json";

const managed = decodeRequestManagedEditRequest(
    parseWireJson(JSON.stringify(fixtures.request.managed)),
);
const key = "original-origin-policy-key";
const operationId = "a".repeat(32);
const origin = "https://archive.invalid";

function client(fetcher: typeof fetch, prefix = "") {
    return new ApiClient({
        scope: createApiScope({ ...scope, origin, publicPrefix: prefix }),
        fetcher,
    });
}

function nativeOptions(
    call: Parameters<typeof fetch> | undefined,
    path: string,
    method: "GET" | "POST",
) {
    if (call === undefined || call[1] === undefined)
        throw new Error("Missing native request.");
    const [input, options] = call;
    const url =
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url;
    expect(url).toBe(origin + path);
    expect(options).toMatchObject({
        method,
        mode: "same-origin",
        credentials: "same-origin",
        redirect: "error",
        cache: "no-store",
    });
    expect(options.signal).toBeInstanceOf(AbortSignal);
    expect(new Headers(options.headers).has("Authorization")).toBe(false);
    return options;
}

test.each(["", "/management"])(
    "managed validation POST preserves native same-origin proof under prefix %s",
    async (prefix) => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            jsonResponse({
                ...readWire("config validate", fixtures.validation),
                archive_id: ARCHIVE_ID,
            }),
        );
        const result = await client(
            fetcher,
            prefix,
        ).validateManagedConfiguration({
            managed,
        });
        expect(result.kind).toBe("success");
        if (result.kind !== "success")
            throw new Error("Managed validation response refused.");
        expect(result.payload).toEqual(fixtures.validation);
        expect(fetcher).toHaveBeenCalledOnce();
        const options = nativeOptions(
            fetcher.mock.calls[0],
            prefix + "/api/v1/config/validate",
            "POST",
        );
        expect(options.referrerPolicy).toBe("same-origin");
        if (typeof options.body !== "string")
            throw new Error("Missing managed validation body.");
        expect(options.body).toBe(JSON.stringify({ managed }));
        const headers = new Headers(options.headers);
        expect(headers.get("Content-Type")).toBe("application/json");
        expect(headers.get("X-Hfcache-Request")).toBe("1");
        expect(headers.has("Idempotency-Key")).toBe(false);
    },
);

test.each(["", "/management"])(
    "keyed managed plan POST keeps its original key and same-origin proof under prefix %s",
    async (prefix) => {
        const status = prefix + "/api/v1/operations/" + operationId;
        const accepted = jsonResponse(
            {
                schema_version: 1,
                request_id: "f".repeat(32),
                archive_id: ARCHIVE_ID,
                config_fingerprint: scope.configFingerprint,
                created: true,
                operation: receipt({
                    operation_id: operationId,
                    route: "/api/v1/plans",
                    state: "queued",
                    domain_run_id: null,
                }),
                links: {
                    status,
                    result: status + "/result",
                    events: status + "/events",
                },
            },
            202,
        );
        accepted.headers.set("Location", status);
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(accepted);
        expect(
            await client(fetcher, prefix).submitManagedPlan(
                { managed },
                { idempotencyKey: key },
            ),
        ).toMatchObject({
            kind: "accepted",
            route: "/api/v1/plans",
            idempotencyKey: key,
            acceptance: { operation: { operation_id: operationId } },
        });
        expect(fetcher).toHaveBeenCalledOnce();
        const options = nativeOptions(
            fetcher.mock.calls[0],
            prefix + "/api/v1/plans",
            "POST",
        );
        expect(options.referrerPolicy).toBe("same-origin");
        if (typeof options.body !== "string")
            throw new Error("Missing managed plan body.");
        expect(options.body).toBe(JSON.stringify({ managed }));
        expect(new Headers(options.headers).get("Idempotency-Key")).toBe(key);
        expect(new Headers(options.headers).get("X-Hfcache-Request")).toBe("1");
    },
);

test.each(["", "/management"])(
    "installed configuration GET retains no-referrer policy under prefix %s",
    async (prefix) => {
        const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
            jsonResponse({
                ...readWire("config read", fixtures.read),
                archive_id: ARCHIVE_ID,
            }),
        );
        expect((await client(fetcher, prefix).readConfiguration()).kind).toBe(
            "success",
        );
        expect(fetcher).toHaveBeenCalledOnce();
        const options = nativeOptions(
            fetcher.mock.calls[0],
            prefix + "/api/v1/config",
            "GET",
        );
        expect(options.referrerPolicy).toBe("no-referrer");
        expect(options.body).toBeUndefined();
        expect(new Headers(options.headers).has("Idempotency-Key")).toBe(false);
        expect(new Headers(options.headers).has("X-Hfcache-Request")).toBe(
            false,
        );
    },
);

test("a CSRF refusal never falls back to another fetch policy or repeats either POST", async () => {
    const validationFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
            Promise.resolve(jsonResponse(problemWire("HFAPI010"), 403)),
        );
    const submissionFetch = vi
        .fn<typeof fetch>()
        .mockImplementation(() =>
            Promise.resolve(jsonResponse(problemWire("HFAPI010"), 403)),
        );
    expect(
        await client(validationFetch).validateManagedConfiguration({ managed }),
    ).toMatchObject({ kind: "api_problem", status: 403 });
    expect(
        await client(submissionFetch).submitManagedPlan(
            { managed },
            { idempotencyKey: key },
        ),
    ).toMatchObject({ kind: "api_problem", status: 403 });
    for (const fetcher of [validationFetch, submissionFetch]) {
        expect(fetcher).toHaveBeenCalledOnce();
        expect(fetcher.mock.calls[0]?.[1]?.referrerPolicy).toBe("same-origin");
    }
});

test("a lost keyed response preserves the original handle without a policy fallback or retry", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockRejectedValue(new TypeError("Owned lost response."));
    expect(
        await client(fetcher).submitManagedPlan(
            { managed },
            { idempotencyKey: key },
        ),
    ).toEqual({
        kind: "uncertain",
        route: "/api/v1/plans",
        idempotencyKey: key,
        reason: "network",
    });
    expect(fetcher).toHaveBeenCalledOnce();
    expect(fetcher.mock.calls[0]?.[1]?.referrerPolicy).toBe("same-origin");
});
