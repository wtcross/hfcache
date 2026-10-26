/** The real GET/config envelope has no ordinary PolicySnapshot fingerprint. */
import { expect, test, vi } from "vitest";
import { ApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { prepareDraft } from "../src/configuration/draft";
import { decodeConfigRead } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { ARCHIVE_ID, jsonResponse, readWire } from "./read-fixtures";
import { scope } from "./state-fixtures";
import fixtures from "../../tests/fixtures/web_wire/config.json";

const fingerprint = "2".repeat(64);
const otherArchive = "12345678-1234-1234-1234-123456789abc";
// host_policy defaults omitted repositories to []; the strict payload itself
// remains the independently Python-serialized public schema.
const projection = decodeConfigRead(
    parseWireJson(
        JSON.stringify({
            ...fixtures.read,
            editable: { ...fixtures.read.editable, repositories: [] },
        }),
    ),
);
function envelope(changes: Record<string, unknown> = {}) {
    return {
        ...readWire("config read", projection),
        archive_id: ARCHIVE_ID,
        config_fingerprint: null,
        ...changes,
    };
}
function client(response: unknown, configFingerprint: string | null) {
    const authority = createApiScope({
        ...scope,
        publicPrefix: "/owned",
        configFingerprint,
    });
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(response));
    return {
        value: new ApiClient({ scope: authority, fetcher }),
        fetcher,
        authority,
    };
}

test.each([null, fingerprint])(
    "genuine config-read null fingerprint loads an empty editable draft under bootstrap fingerprint %s",
    async (configFingerprint) => {
        const { value, fetcher, authority } = client(
            envelope(),
            configFingerprint,
        );
        const result = await value.readConfiguration();
        expect(result.kind).toBe("success");
        if (result.kind !== "success")
            throw new Error("Genuine configuration response refused");
        expect(result.response.archive_id).toBe(ARCHIVE_ID);
        expect(result.response.config_fingerprint).toBeNull();
        expect(result.payload.base_revision).toBe(projection.base_revision);
        expect(result.payload.editable.repositories).toEqual([]);
        const draft = prepareDraft(result.payload, result.payload.editable);
        expect(draft).toMatchObject({
            dirty: false,
            diff: [],
            managed: { base_revision: projection.base_revision, edits: [] },
        });
        // A private HMAC base token is never substituted for the missing ordinary
        // validation fingerprint, nor does a read mutate bootstrap authority.
        expect(authority.configFingerprint).toBe(configFingerprint);
        expect(fetcher).toHaveBeenCalledTimes(1);
        const called = fetcher.mock.calls[0];
        if (called === undefined)
            throw new Error("Missing configuration request");
        const [url, options] = called;
        const href =
            typeof url === "string"
                ? url
                : url instanceof URL
                  ? url.href
                  : url.url;
        expect(href).toBe(scope.origin + "/owned/api/v1/config");
        expect(options?.method).toBe("GET");
        expect(options?.body).toBeUndefined();
        expect(new Headers(options?.headers).has("Idempotency-Key")).toBe(
            false,
        );
    },
);

test.each([
    { name: "wrong", archive_id: otherArchive },
    { name: "null", archive_id: null },
    { name: "omitted", archive_id: undefined },
])(
    "allowing a null fingerprint never permits %s wrapper archive identity",
    async ({ archive_id }) => {
        for (const configFingerprint of [null, fingerprint]) {
            const { value } = client(
                envelope({ archive_id }),
                configFingerprint,
            );
            expect((await value.readConfiguration()).kind).toBe(
                "protocol_failure",
            );
        }
    },
);

test("a correct wrapper cannot lend its archive identity to another ConfigRead payload", async () => {
    const response = envelope();
    const mismatched = {
        ...response,
        envelope: {
            ...response.envelope,
            data: { ...projection, archive_id: otherArchive },
        },
    };
    for (const configFingerprint of [null, fingerprint]) {
        const { value } = client(mismatched, configFingerprint);
        expect((await value.readConfiguration()).kind).toBe("protocol_failure");
    }
});

test("a supplied ordinary fingerprint must still match nonnull bootstrap authority", async () => {
    const { value } = client(
        envelope({ config_fingerprint: "f".repeat(64) }),
        fingerprint,
    );
    expect((await value.readConfiguration()).kind).toBe("protocol_failure");
});
