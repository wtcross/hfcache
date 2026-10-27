/** Real typed boundaries and original-handle proof; no installed manager claim. */
import { afterEach, expect, test, vi } from "vitest";
import * as wire from "../src/wire/generated";
import { parseWireJson, WireError } from "../src/wire/json";
import { ApiClient } from "../src/api/client";
import { createAuthSession } from "../src/state/authority";
import { createOperationRegistry } from "../src/state/operation-registry";
import {
    createSessionController,
    resultCertainty,
} from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import { ARCHIVE_ID, jsonResponse, readWire } from "./read-fixtures";
import {
    deferred,
    OPERATION_ID,
    operationResponse,
    receipt,
    scope,
    session,
} from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const scheduleRoute = "/api/v1/host/sync-schedule/changes";
const observerRoute = "/api/v1/host/sync-observer/stops";
const key = "owned-original-host-action";
const expected = {
    boot_id: ARCHIVE_ID,
    invocation_id: "b".repeat(32),
    main_pid: 1234,
    start_ticks: 5678,
};
const request = { action: "pause", expected_revision: "a".repeat(64) } as const;
function schedule(patch: Record<string, unknown> = {}) {
    return wire.decodeScheduleChangeOutcome(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                operation_id: OPERATION_ID,
                request_digest: "e".repeat(64),
                state: "confirmed",
                pending: false,
                action: "pause",
                expected_revision: request.expected_revision,
                stored_revision: request.expected_revision,
                file_state: "unchanged",
                manager_state: "timer_acknowledged",
                timer_was_active: true,
                timer_is_active: false,
                ...patch,
            }),
        ),
    );
}
function stopped(patch: Record<string, unknown> = {}) {
    return wire.decodeObserverStopOutcome(
        parseWireJson(
            JSON.stringify({
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                operation_id: OPERATION_ID,
                request_digest: "e".repeat(64),
                state: "confirmed",
                pending: false,
                expected,
                stop_state: "exit_confirmed",
                ...patch,
            }),
        ),
    );
}
function hostWire(command: string, payload: unknown) {
    return {
        ...readWire(command, payload),
        archive_id: ARCHIVE_ID,
        config_fingerprint: null,
    };
}
function original(route = scheduleRoute, state = "interrupted") {
    return receipt({
        route,
        state,
        completed_at: ["succeeded", "failed", "interrupted"].includes(state)
            ? "2026-10-20T12:00:01.000000Z"
            : null,
        result_recorded: state === "succeeded" || state === "failed",
    });
}
class Storage {
    saved: string | null = null;
    getItem() {
        return this.saved;
    }
    setItem(_name: string, value: string) {
        this.saved = value;
    }
}
function proof(route = scheduleRoute, state = "interrupted") {
    const storage = new Storage(),
        registry = createOperationRegistry({ storage });
    const record = registry.importHandle(
        {
            kind: "basic-key",
            key,
            operationId: OPERATION_ID,
            originalScope: session.scope,
        },
        session,
    );
    registry.observed(
        registry.authorizeObservation(record.recordId, session),
        original(route, state),
    );
    return {
        registry,
        storage,
        record,
        auth: registry.authorizeObservation(record.recordId, session),
    };
}
function bootstrap(hostRead = true, write = false): wire.UiBootstrap {
    const base = uiBootstrapFixture();
    return {
        ...base,
        configured_origin: scope.origin,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...base.user,
            admin_permissions: base.user.admin_permissions.map((row) => {
                const allowed =
                    row.capability === "host-read"
                        ? hostRead
                        : (row.capability === "schedule-write" ||
                              row.capability === "observer-stop") &&
                          write;
                return {
                    ...row,
                    effective: allowed,
                    granted: allowed,
                    reason: allowed ? "allowed" : "not_granted",
                };
            }),
        },
    };
}
const controllers = new Set<SessionController>();
function controller(
    fetcher: typeof fetch,
    initial = bootstrap(),
    storage = new Storage(),
) {
    const value = createSessionController({
        bootstrap: initial,
        fetcher,
        storage,
        reconnect: () => Promise.resolve(initial),
    });
    controllers.add(value);
    return value;
}
afterEach(() => {
    for (const value of controllers) value.dispose();
    controllers.clear();
    vi.restoreAllMocks();
});
function url(value: RequestInfo | URL) {
    return new URL(
        typeof value === "string"
            ? value
            : value instanceof URL
              ? value.href
              : value.url,
    );
}

function firstCall(fetcher: ReturnType<typeof vi.fn<typeof fetch>>) {
    const call = fetcher.mock.calls[0];
    if (call === undefined) throw new Error("Missing original request");
    return call;
}

test("schedule variants preserve exact body presence and reject selector-like additions", () => {
    const contract = wire.routeContracts.schedule_change_default;
    expect(contract.decodeBody(parseWireJson(JSON.stringify(request)))).toEqual(
        request,
    );
    const replace = {
        ...request,
        action: "replace",
        on_calendar: "daily",
        randomized_delay_sec: null,
    };
    expect(contract.decodeBody(parseWireJson(JSON.stringify(replace)))).toEqual(
        replace,
    );
    for (const body of [
        { ...request, on_calendar: null },
        { ...request, randomized_delay_sec: null },
        { ...request, unit: "other.service" },
        { ...replace, randomized_delay_sec: undefined },
        { ...replace, on_calendar: "daily\nExecStart=bad" },
        { ...replace, on_calendar: "daily\\" },
    ])
        expect(() =>
            contract.decodeBody(parseWireJson(JSON.stringify(body))),
        ).toThrow(WireError);
});

test("observer expected tuple is closed and keeps strict safe integer identity", () => {
    expect(
        wire.decodeRequestObserverStopRequest(
            parseWireJson(JSON.stringify({ expected })),
        ),
    ).toEqual({ expected });
    for (const bad of [
        { ...expected, main_pid: true },
        { ...expected, start_ticks: 9007199254740992 },
        { ...expected, boot_id: "other" },
        { ...expected, unit: "other.service" },
    ])
        expect(() =>
            wire.decodeRequestObserverStopRequest(
                parseWireJson(JSON.stringify({ expected: bad })),
            ),
        ).toThrow(WireError);
});

test("dedicated observer status permits native transient observation without widening legacy HostStatus", async () => {
    const binding = {
        deployment_sha256: "a".repeat(64),
        policy_sha256: "b".repeat(64),
        release_version: "0.2.2",
        source_commit: "c".repeat(40),
        source_snapshot_sha256: "d".repeat(64),
        source_dirty: false,
        archive_id: ARCHIVE_ID,
        archive_root: "/srv/hfcache",
    };
    const status = {
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        profile: "native",
        host_binding: binding,
        permissions: { schedule: true, observer: true },
        permission_reasons: { schedule: "granted", observer: "granted" },
        state: "observed",
        reason: null,
        unit: "hfcache-sync.service",
        expected,
    };
    expect(
        wire.decodeHostObserverStatus(parseWireJson(JSON.stringify(status)))
            .expected,
    ).toEqual(expected);
    for (const patch of [
        { profile: "rootless" },
        { state: "unavailable", reason: "facts-unavailable", expected: null },
        {
            host_binding: {
                ...binding,
                archive_id: "12345678-1234-1234-1234-123456789abc",
            },
        },
        { expected: null },
    ])
        expect(() =>
            wire.decodeHostObserverStatus(
                parseWireJson(JSON.stringify({ ...status, ...patch })),
            ),
        ).toThrow(WireError);
    const rootless = {
        ...status,
        profile: "rootless",
        state: "unavailable",
        expected: null,
        reason: "profile-unproved",
        permissions: { schedule: false, observer: false },
        permission_reasons: {
            schedule: "profile-unproved",
            observer: "profile-unproved",
        },
    };
    expect(
        wire.decodeHostObserverStatus(parseWireJson(JSON.stringify(rootless)))
            .permissions,
    ).toEqual({ schedule: false, observer: false });
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(
            jsonResponse(hostWire("host observer status", status)),
        );
    expect(
        (await new ApiClient({ scope, fetcher }).readHostObserver()).kind,
    ).toBe("success");
    expect(url(firstCall(fetcher)[0]).pathname).toBe(
        "/api/v1/host/sync-observer",
    );
});

test("original host integer lexemes and journal request selectors fail before transport", async () => {
    expect(() =>
        wire.decodeRequestObserverStopRequest(
            parseWireJson(
                JSON.stringify({ expected }).replace(
                    '"main_pid":1234',
                    '"main_pid":1234.0',
                ),
            ),
        ),
    ).toThrow(WireError);
    const fetcher = vi.fn<typeof fetch>(),
        client = new ApiClient({ scope, fetcher });
    expect(
        (await client.readHostJournal({ source: "sync-observer", limit: 81 }))
            .kind,
    ).toBe("protocol_failure");
    expect(fetcher).not.toHaveBeenCalled();
});

test("stale revision refusal has no file/manager effect and cannot masquerade as prepared or confirmed", () => {
    const value = schedule({
        state: "unchanged",
        stored_revision: "c".repeat(64),
        manager_state: "not_sent",
        timer_is_active: true,
    });
    expect(value.stored_revision).not.toBe(value.expected_revision);
    for (const patch of [
        { pending: true },
        { state: "prepared" },
        { state: "confirmed" },
        { timer_is_active: false },
        { timer_was_active: null },
    ])
        expect(() => schedule({ ...value, ...patch })).toThrow(WireError);
});

test("journal exposes only recognized event, level and run ID with authenticated page bounds", async () => {
    const entry = {
        at: null,
        message: "event=run.completed level=info run_id=" + "a".repeat(32),
    };
    const page = {
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        source: "sync-observer",
        entries: [entry],
        next_cursor: "x".repeat(2048),
        gap: true,
        truncated: true,
    };
    expect(
        wire.decodeHostJournalPage(parseWireJson(JSON.stringify(page))).entries,
    ).toHaveLength(1);
    for (const message of [
        entry.message + " secret=opaque",
        "event=unknown level=info run_id=" + "a".repeat(32),
        "<script>unsafe</script>",
    ])
        expect(() =>
            wire.decodeHostJournalPage(
                parseWireJson(
                    JSON.stringify({
                        ...page,
                        entries: [{ ...entry, message }],
                    }),
                ),
            ),
        ).toThrow(WireError);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        jsonResponse({
            ...hostWire("host journal", page),
            next_cursor: null,
        }),
    );
    const client = new ApiClient({ scope, fetcher });
    expect(
        (await client.readHostJournal({ source: "sync-observer", limit: 1 }))
            .kind,
    ).toBe("success");
    expect(url(firstCall(fetcher)[0]).searchParams.get("source")).toBe(
        "sync-observer",
    );
    expect(
        (await client.readHostJournal({ source: "verify-observer", limit: 1 }))
            .kind,
    ).toBe("protocol_failure");
    expect(() =>
        wire.decodeHostJournalPage(
            parseWireJson(
                JSON.stringify({ ...page, next_cursor: "x".repeat(2049) }),
            ),
        ),
    ).toThrow(WireError);
});

test("validation is nonkeyed and binds exact input echoes plus nonnull archive despite null wrapper fingerprint", async () => {
    const input = { on_calendar: "daily", randomized_delay_sec: null };
    const payload = {
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        ...input,
        normalized_on_calendar: "*-*-* 00:00:00",
        normalized_randomized_delay_sec: null,
        next_elapse: null,
    };
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(
            jsonResponse(hostWire("host schedule validate", payload)),
        );
    const client = new ApiClient({ scope, fetcher });
    expect((await client.validateSchedule(input)).kind).toBe("success");
    const options = firstCall(fetcher)[1];
    expect(options?.method).toBe("POST");
    expect(new Headers(options?.headers).has("Idempotency-Key")).toBe(false);
    expect(options?.body).toBe(JSON.stringify(input));
    fetcher.mockResolvedValue(
        jsonResponse(
            hostWire("host schedule validate", {
                ...payload,
                on_calendar: "weekly",
            }),
        ),
    );
    expect((await client.validateSchedule(input)).kind).toBe(
        "protocol_failure",
    );
    fetcher.mockResolvedValue(
        jsonResponse({
            ...hostWire("host schedule validate", payload),
            archive_id: null,
        }),
    );
    expect((await client.validateSchedule(input)).kind).toBe(
        "protocol_failure",
    );
});

test.each([scheduleRoute, observerRoute])(
    "fresh original-key outcome for %s is RAM-only certainty, never rewritten API success",
    (route) => {
        const { registry, storage, auth, record } = proof(route);
        const saved = storage.saved,
            before = registry.snapshot().records[0];
        registry.hostActionOutcome(
            auth,
            route === scheduleRoute ? schedule() : stopped(),
        );
        expect(registry.canSubmit(session)).toBe(true);
        expect(storage.saved).toBe(saved);
        expect(registry.snapshot().records[0]).toEqual(before);
        const restored = createOperationRegistry({ storage });
        expect(restored.canSubmit(session)).toBe(false);
        expect(
            restored.authorizeObservation(record.recordId, session).locator,
        ).toEqual({ kind: "key", key });
        registry.invalidateObservations();
        expect(
            registry.canSubmit(createAuthSession({ scope, authGeneration: 2 })),
        ).toBe(false);
        expect(() => {
            registry.hostActionOutcome(auth, schedule());
        }).toThrow();
    },
);

test.each(["queued", "running", "interrupted"])(
    "pending/uncertain outcome never releases %s original",
    (state) => {
        const { registry, auth } = proof(scheduleRoute, state);
        for (const value of [
            schedule({ pending: true }),
            schedule({ state: "effect_unconfirmed" }),
        ]) {
            registry.hostActionOutcome(auth, value);
            expect(registry.canSubmit(session)).toBe(false);
        }
        registry.hostActionOutcome(auth, schedule());
        expect(registry.canSubmit(session)).toBe(state === "interrupted");
    },
);

test("fresh host proof refuses mismatched operation/archive, wrong route and copied authorization", () => {
    const { registry, auth } = proof();
    for (const value of [
        schedule({ operation_id: "b".repeat(32) }),
        schedule({ archive_id: "12345678-1234-1234-1234-123456789abc" }),
    ])
        expect(() => {
            registry.hostActionOutcome(auth, value);
        }).toThrow();
    expect(() => {
        registry.hostActionOutcome({ ...auth }, schedule());
    }).toThrow();
    const other = proof("/api/v1/config/applications");
    expect(() => {
        other.registry.hostActionOutcome(other.auth, schedule());
    }).toThrow();
    expect(registry.canSubmit(session)).toBe(false);
});

test.each([scheduleRoute, observerRoute])(
    "read-only controller proves original key then outcome for %s without write grant or POST",
    async (route) => {
        const fetcher = vi
            .fn<typeof fetch>()
            .mockImplementation((target, options) => {
                expect(options?.method).toBe("GET");
                expect(
                    new Headers(options?.headers).get("Idempotency-Key"),
                ).toBe(key);
                if (url(target).pathname === "/api/v1/operations/lookup")
                    return Promise.resolve(
                        jsonResponse(
                            operationResponse("operations lookup", {
                                operation: original(route),
                            }),
                        ),
                    );
                expect(url(target).pathname).toBe(route + "/" + OPERATION_ID);
                return Promise.resolve(
                    jsonResponse(
                        hostWire(
                            route === scheduleRoute
                                ? "host schedule outcome"
                                : "host observer outcome",
                            route === scheduleRoute ? schedule() : stopped(),
                        ),
                    ),
                );
            });
        const value = controller(fetcher),
            record = value.importHandle({
                kind: "basic-key",
                key,
                operationId: OPERATION_ID,
                originalScope: value.originalScope(),
            });
        expect(value.snapshot().canSubmit).toBe(false);
        expect(
            (await value.observeHostActionOutcome(record.recordId)).kind,
        ).toBe("outcome");
        expect(value.snapshot().canSubmit).toBe(true);
        expect(fetcher).toHaveBeenCalledTimes(2);
    },
);

test("late outcome after disconnect cannot release the preserved original handle", async () => {
    const pending = deferred<Response>();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValueOnce(
            jsonResponse(
                operationResponse("operations lookup", {
                    operation: original(),
                }),
            ),
        )
        .mockImplementationOnce(() => pending.promise);
    const value = controller(fetcher),
        record = value.importHandle({
            kind: "basic-key",
            key,
            operationId: OPERATION_ID,
            originalScope: value.originalScope(),
        });
    const observing = value.observeHostActionOutcome(record.recordId);
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    value.disconnect();
    pending.resolve(
        jsonResponse(hostWire("host schedule outcome", schedule())),
    );
    await expect(observing).rejects.toThrow();
    expect(value.snapshot().connection).toBe("disconnected");
    expect(value.snapshot().canSubmit).toBe(false);
    expect(value.snapshot().registry.records[0]?.handles).toMatchObject({
        key,
        operationId: OPERATION_ID,
    });
});

test("independent schedule/observer grants refuse locally before preserving a fresh key or making POST", async () => {
    const fetcher = vi.fn<typeof fetch>();
    const value = controller(fetcher);
    await expect(
        value.submit({ action: "scheduleChange", request }),
    ).rejects.toThrow();
    await expect(
        value.submit({ action: "observerStop", request: { expected } }),
    ).rejects.toThrow();
    await expect(
        value.validateSchedule({
            on_calendar: "daily",
            randomized_delay_sec: null,
        }),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
    expect(value.snapshot().registry.records).toEqual([]);
});

test.each(["scheduleChange", "observerStop"] as const)(
    "%s persists original key before its sole POST and preserves an uncertain transmission without replay",
    async (action) => {
        const storage = new Storage();
        const fetcher = vi
            .fn<typeof fetch>()
            .mockImplementation((_target, options) => {
                const header = new Headers(options?.headers).get(
                    "Idempotency-Key",
                );
                expect(options?.method).toBe("POST");
                expect(header).not.toBeNull();
                expect(storage.saved).toContain(header);
                expect(storage.saved).toContain(
                    action === "scheduleChange" ? scheduleRoute : observerRoute,
                );
                expect(options?.body).toBe(
                    JSON.stringify(
                        action === "scheduleChange" ? request : { expected },
                    ),
                );
                return Promise.reject(new Error("owned connection loss"));
            });
        const value = controller(fetcher, bootstrap(true, true), storage);
        const intent =
            action === "scheduleChange"
                ? { action, request }
                : { action, request: { expected } };
        const result = await value.submit(intent);
        expect(result.result.kind).toBe("uncertain");
        expect(fetcher).toHaveBeenCalledOnce();
        expect(value.snapshot().canSubmit).toBe(false);
        await expect(value.submit(intent)).rejects.toThrow();
        expect(fetcher).toHaveBeenCalledOnce();
        expect(storage.saved).not.toContain("expected_revision");
        expect(storage.saved).not.toContain("main_pid");
    },
);

test("locally invalid host body removes only its fresh prepared handle before releasing submission", async () => {
    const fetcher = vi.fn<typeof fetch>(),
        value = controller(fetcher, bootstrap(true, true));
    const result = await value.submit({
        action: "scheduleChange",
        request: { ...request, expected_revision: "not-a-revision" },
    });
    expect(result.result.kind).toBe("refused");
    expect(fetcher).not.toHaveBeenCalled();
    expect(value.snapshot().registry.records).toEqual([]);
    expect(value.snapshot().canSubmit).toBe(true);
});

test("host-read denial cannot use outcome lookup and validation carries only its independent schedule grant", async () => {
    const fetcher = vi.fn<typeof fetch>(),
        denied = controller(fetcher, bootstrap(false));
    const record = denied.importHandle({
        kind: "basic-key",
        key,
        operationId: OPERATION_ID,
        originalScope: denied.originalScope(),
    });
    await expect(
        denied.observeHostActionOutcome(record.recordId),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
    const input = { on_calendar: "daily", randomized_delay_sec: null };
    fetcher.mockResolvedValue(
        jsonResponse(
            hostWire("host schedule validate", {
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                ...input,
                normalized_on_calendar: "*-*-* 00:00:00",
                normalized_randomized_delay_sec: null,
                next_elapse: null,
            }),
        ),
    );
    const writer = controller(fetcher, bootstrap(false, true));
    expect((await writer.validateSchedule(input)).kind).toBe("success");
    expect(fetcher).toHaveBeenCalledTimes(1);
});

test("current schedule validation is discarded after disconnect and cannot publish late readiness", async () => {
    const pending = deferred<Response>(),
        fetcher = vi
            .fn<typeof fetch>()
            .mockImplementation(() => pending.promise);
    const value = controller(fetcher, bootstrap(true, true));
    const input = { on_calendar: "daily", randomized_delay_sec: null };
    const validation = value.validateSchedule(input);
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    const signal = firstCall(fetcher)[1]?.signal;
    value.disconnect();
    expect(signal?.aborted).toBe(true);
    pending.resolve(
        jsonResponse(
            hostWire("host schedule validate", {
                schema_version: 1,
                archive_id: ARCHIVE_ID,
                ...input,
                normalized_on_calendar: "*-*-* 00:00:00",
                normalized_randomized_delay_sec: null,
                next_elapse: null,
            }),
        ),
    );
    expect(await validation).toEqual({ kind: "aborted" });
});

test("host outcome/result joins reject another operation even with correct envelope and original route", async () => {
    const mismatch = schedule({ operation_id: "c".repeat(32) });
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(
            jsonResponse(hostWire("host schedule outcome", mismatch)),
        );
    const client = new ApiClient({ scope, fetcher });
    expect((await client.readScheduleOutcome(OPERATION_ID, key)).kind).toBe(
        "protocol_failure",
    );
    fetcher.mockResolvedValue(
        jsonResponse(operationResponse("host schedule change", mismatch)),
    );
    expect(
        (await client.readOperationResult(original(scheduleRoute, "succeeded")))
            .kind,
    ).toBe("protocol_failure");
});

test("typed original host results keep unknown effects blocked even with terminal failed API receipt", async () => {
    const failed = original(scheduleRoute, "failed");
    for (const [value, known] of [
        [schedule(), true],
        [schedule({ pending: true }), false],
        [schedule({ state: "effect_unconfirmed" }), false],
    ] as const) {
        const client = new ApiClient({
            scope,
            fetcher: () =>
                Promise.resolve(
                    jsonResponse({
                        ...operationResponse("host schedule change", value),
                        envelope: {
                            ...operationResponse("host schedule change", value)
                                .envelope,
                            exit_code: 10,
                            outcome: "failed",
                            errors: [
                                {
                                    code: "HFAPI007",
                                    message: "Host action refused",
                                    context: {},
                                    repository: null,
                                },
                            ],
                        },
                    }),
                ),
        });
        const result = await client.readOperationResult(failed);
        expect(result.kind).toBe("domain_failure");
        expect(resultCertainty(failed, result)).toBe(
            known ? "known" : "unknown-effects",
        );
    }
});

test.each(["observed", "inactive"] as const)(
    "native %s identity remains readable and scheduling validates when observer confinement is unproved",
    async (state) => {
        const status = {
            schema_version: 1,
            archive_id: ARCHIVE_ID,
            profile: "native",
            host_binding: {
                deployment_sha256: "a".repeat(64),
                policy_sha256: "b".repeat(64),
                release_version: "0.2.2",
                source_commit: "c".repeat(40),
                source_snapshot_sha256: "d".repeat(64),
                source_dirty: false,
                archive_id: ARCHIVE_ID,
                archive_root: "/srv/hfcache",
            },
            permissions: { schedule: true, observer: false },
            permission_reasons: {
                schedule: "granted",
                observer: "profile-unproved",
            },
            state,
            reason: null,
            unit: "hfcache-sync.service",
            expected: state === "observed" ? expected : null,
        };
        const decoded = wire.decodeHostObserverStatus(
            parseWireJson(JSON.stringify(status)),
        );
        expect(decoded.permissions).toEqual({
            schedule: true,
            observer: false,
        });
        expect(decoded.expected).toEqual(status.expected);
        const input = { on_calendar: "daily", randomized_delay_sec: "1s" };
        const fetcher = vi
            .fn<typeof fetch>()
            .mockResolvedValueOnce(
                jsonResponse(hostWire("host observer status", status)),
            )
            .mockResolvedValueOnce(
                jsonResponse(
                    hostWire("host schedule validate", {
                        schema_version: 1,
                        archive_id: ARCHIVE_ID,
                        ...input,
                        normalized_on_calendar: "*-*-* 00:00:00",
                        normalized_randomized_delay_sec: "1s",
                        next_elapse: null,
                    }),
                ),
            );
        const client = new ApiClient({ scope, fetcher });
        const observed = await client.readHostObserver();
        expect(observed.kind).toBe("success");
        if (observed.kind !== "success") throw new Error("Status refused");
        expect(observed.payload).toEqual(decoded);
        expect((await client.validateSchedule(input)).kind).toBe("success");
        expect(
            fetcher.mock.calls.map(([target]) => url(target).pathname),
        ).toEqual([
            "/api/v1/host/sync-observer",
            "/api/v1/host/sync-schedule/validations",
        ]);
        expect(
            fetcher.mock.calls.some(
                ([target]) => url(target).pathname === observerRoute,
            ),
        ).toBe(false);
    },
);
