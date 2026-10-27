/** Owned transport adapters; real controller/query/registry, no installed host claim. */
import { vi } from "vitest";
import { createHostControlsStore } from "../src/administration/host-controls-state";
import { createSessionController } from "../src/state/session-controller";
import { hostStatusFixture } from "./host-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import { ARCHIVE_ID, jsonResponse, readWire } from "./read-fixtures";
import { decodeRequestScheduleValidationRequest } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import type {
    HostObserverStatus,
    HostStatus,
    UiBootstrap,
} from "../src/wire/generated";

export const expectedObserver = {
    boot_id: ARCHIVE_ID,
    invocation_id: "a".repeat(32),
    main_pid: 4321,
    start_ticks: 123456,
};
export function hostControlsFixture(
    options: {
        schedule?: boolean;
        observer?: boolean;
        running?: boolean;
        hostRead?: boolean;
        validation?: (body: {
            on_calendar: string;
            randomized_delay_sec: string | null;
        }) => Promise<Response>;
        journal?: (url: URL) => Response;
        extra?: (
            url: URL,
            init: RequestInit | undefined,
        ) => Response | Promise<Response>;
    } = {},
) {
    const schedule = options.schedule !== false,
        stop = options.observer !== false;
    const base = hostStatusFixture();
    if (base.binding === null || base.facts === null)
        throw new Error("Missing owned golden facts");
    const binding = { ...base.binding, archive_id: ARCHIVE_ID };
    let host: HostStatus = {
        ...base,
        profile: "native",
        binding,
        permissions: { ...base.permissions, schedule, observer: stop },
        permission_reasons: {
            ...base.permission_reasons,
            schedule: schedule ? "granted" : "policy-denied",
            observer: stop ? "granted" : "profile-unproved",
        },
        facts: {
            ...base.facts,
            units: {
                "hfcache-sync.service": {
                    load: "loaded",
                    active: "inactive",
                    unit_file: "linked",
                },
                "hfcache-sync.timer": {
                    load: "loaded",
                    active: "inactive",
                    unit_file: "linked",
                },
                "hfcache-verify.service": {
                    load: "loaded",
                    active: "inactive",
                    unit_file: "linked",
                },
                "hfcache-verify.timer": {
                    load: "loaded",
                    active: "inactive",
                    unit_file: "linked",
                },
            },
            sync_schedule: {
                state: "observed",
                reason: null,
                revision: "e".repeat(64),
                source: "default",
                on_calendar: "daily UTC",
                randomized_delay_sec: "30m",
            },
        },
    };
    let observer: HostObserverStatus = {
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        profile: "native",
        host_binding: binding,
        permissions: { schedule, observer: stop },
        permission_reasons: {
            schedule: schedule ? "granted" : "policy-denied",
            observer: stop ? "granted" : "profile-unproved",
        },
        state: options.running ? "observed" : "inactive",
        reason: null,
        unit: "hfcache-sync.service",
        expected: options.running ? expectedObserver : null,
    };
    const original = uiBootstrapFixture();
    const bootstrap: UiBootstrap = {
        ...original,
        configured_origin:
            typeof location === "undefined"
                ? "https://host-controls.invalid"
                : location.origin,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...original.user,
            admin_permissions: original.user.admin_permissions.map((p) => ({
                ...p,
                granted:
                    p.capability !== "host-read" || options.hostRead !== false,
                effective:
                    p.capability !== "host-read" || options.hostRead !== false,
                reason:
                    p.capability === "host-read" && options.hostRead === false
                        ? "not_granted"
                        : "allowed",
            })),
        },
    };
    const calls: {
        method: string;
        path: string;
        query: string;
        body: unknown;
        key: string | null;
    }[] = [];
    const wire = (command: string, value: unknown) => ({
        ...readWire(command, value),
        archive_id: ARCHIVE_ID,
        config_fingerprint: null,
    });
    const fetcher = vi.fn<typeof fetch>(async (target, init) => {
        const url = new URL(
            typeof target === "string"
                ? target
                : target instanceof URL
                  ? target.href
                  : target.url,
        );
        const method = init?.method ?? "GET";
        const body: unknown =
            typeof init?.body === "string" ? JSON.parse(init.body) : null;
        calls.push({
            method,
            path: url.pathname,
            query: url.search,
            body,
            key: new Headers(init?.headers).get("Idempotency-Key"),
        });
        if (url.pathname === "/api/v1/host/status")
            return jsonResponse(wire("host status", host));
        if (url.pathname === "/api/v1/host/sync-observer")
            return jsonResponse(wire("host observer status", observer));
        if (url.pathname === "/api/v1/host/sync-schedule/validations") {
            const request = decodeRequestScheduleValidationRequest(
                parseWireJson(JSON.stringify(body)),
            );
            if (options.validation) return options.validation(request);
            return jsonResponse(
                wire("host schedule validate", {
                    schema_version: 1,
                    archive_id: ARCHIVE_ID,
                    ...request,
                    normalized_on_calendar: "*-*-* 00:00:00 UTC",
                    normalized_randomized_delay_sec:
                        request.randomized_delay_sec,
                    next_elapse: "Thu 2099-01-01 00:00:00 UTC",
                }),
            );
        }
        if (url.pathname === "/api/v1/host/journal")
            return (
                options.journal?.(url) ??
                jsonResponse(
                    wire("host journal", {
                        schema_version: 1,
                        archive_id: ARCHIVE_ID,
                        source: url.searchParams.get("source"),
                        entries: [],
                        next_cursor: null,
                        gap: false,
                        truncated: false,
                    }),
                )
            );
        if (method === "POST")
            throw new TypeError("owned lost acknowledgement");
        if (options.extra) return options.extra(url, init);
        throw new Error("Unexpected owned request: " + url.pathname);
    });
    let saved: string | null = null;
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: {
            getItem: () => saved,
            setItem: (_key, value) => {
                saved = value;
            },
        },
        reconnect: () => Promise.resolve(bootstrap),
    });
    const store = createHostControlsStore(controller);
    return {
        controller,
        store,
        fetcher,
        calls,
        wire,
        setHost: (value: HostStatus) => {
            host = value;
        },
        host: () => host,
        setObserver: (value: HostObserverStatus) => {
            observer = value;
        },
        observer: () => observer,
        saved: () => saved,
        dispose() {
            store.dispose();
            controller.dispose();
        },
    };
}
