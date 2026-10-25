import { expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { decodeHostStatus } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { hostStatusFixture, hostStatusWire } from "./host-fixtures";
import { jsonResponse, problemWire } from "./read-fixtures";

const original = hostStatusFixture();
const scope = createApiScope({
    origin: "https://archive.invalid",
    publicPrefix: "/management",
    authorityEpoch: "host-reader-1",
    subject: "administrator",
    credentialClass: "rest-writer",
    instanceId: null,
    archiveId: original.binding?.archive_id ?? null,
    configFingerprint: null,
});

test("host status uses the fixed same-origin read and binds the archive wrapper", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(hostStatusWire()));
    const result = await createApiClient({ scope, fetcher }).hostStatus();
    expect(result.kind).toBe("success");
    expect(fetcher).toHaveBeenCalledOnce();
    const [url, options] = fetcher.mock.calls[0] ?? [];
    expect(url instanceof URL ? url.href : "").toBe(
        "https://archive.invalid/management/api/v1/host/status",
    );
    expect(options).toMatchObject({
        method: "GET",
        credentials: "same-origin",
        redirect: "error",
        cache: "no-store",
    });
    const mismatched = vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
            ...hostStatusWire(),
            archive_id: "12345678-1234-1234-1234-123456789abc",
        }),
    );
    expect(
        (await createApiClient({ scope, fetcher: mismatched }).hostStatus())
            .kind,
    ).toBe("protocol_failure");
});
test("host authority safety failure retains HFAPI022 without retry", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI022", 20), 503));
    expect(
        await createApiClient({ scope, fetcher }).hostStatus(),
    ).toMatchObject({
        kind: "api_problem",
        status: 503,
        problem: { code: "HFAPI022", exit_code: 20 },
    });
    expect(fetcher).toHaveBeenCalledOnce();
});
test.each([
    { ...original, schema_version: true },
    { ...original, state: "unknown" },
    { ...original, reason: "facts-unavailable" },
    { ...original, binding: null },
    { ...original, facts: null },
    { ...original, permissions: { ...original.permissions, archive: true } },
    {
        ...original,
        permissions: { ...original.permissions, schedule: true },
        permission_reasons: {
            ...original.permission_reasons,
            schedule: "granted",
        },
    },
    {
        ...original,
        permissions: { ...original.permissions, observer: true },
        permission_reasons: {
            ...original.permission_reasons,
            observer: "granted",
        },
    },
    {
        ...original,
        binding: { ...original.binding, release_version: "0.2.2\n" },
    },
    { ...original, state: "guarded" },
    { ...original, facts: { ...original.facts, units: {} } },
    {
        ...original,
        facts: {
            ...original.facts,
            units: {
                ...original.facts?.units,
                "other.service": {
                    active: "inactive",
                    load: "masked",
                    unit_file: "masked",
                },
            },
        },
    },
    {
        ...original,
        facts: {
            ...original.facts,
            sync_schedule: {
                state: "observed",
                reason: null,
                revision: "a".repeat(64),
                source: "default",
                on_calendar: null,
                randomized_delay_sec: null,
            },
        },
    },
    {
        ...original,
        facts: {
            ...original.facts,
            sync_schedule: {
                state: "unavailable",
                reason: "profile-unproved",
                revision: null,
                source: null,
                on_calendar: "daily",
                randomized_delay_sec: null,
            },
        },
    },
    {
        ...original,
        facts: {
            ...original.facts,
            sync_schedule: {
                state: "observed",
                reason: null,
                revision: "a".repeat(64),
                source: "default",
                on_calendar: "daily\n",
                randomized_delay_sec: null,
            },
        },
    },
])(
    "host authority contradictions refuse rather than displaying permissions %#",
    (value) => {
        expect(() =>
            decodeHostStatus(parseWireJson(JSON.stringify(value))),
        ).toThrow();
    },
);
test("native observed schedule preserves bounded printable values", () => {
    expect(
        decodeHostStatus(
            parseWireJson(
                JSON.stringify({
                    ...original,
                    profile: "native",
                    facts: {
                        ...original.facts,
                        sync_schedule: {
                            state: "observed",
                            reason: null,
                            revision: "a".repeat(64),
                            source: "default",
                            on_calendar: "*-*-* 03:00:00",
                            randomized_delay_sec: "15m",
                        },
                    },
                }),
            ),
        ),
    ).toMatchObject({
        profile: "native",
        facts: { sync_schedule: { on_calendar: "*-*-* 03:00:00" } },
    });
});
