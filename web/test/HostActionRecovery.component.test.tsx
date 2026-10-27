/** Original Basic-key records and real controller/client, with controlled HTTP responses. */
import {
    act,
    cleanup,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useSyncExternalStore } from "react";
import { afterEach, expect, test, vi } from "vitest";
import { HostActionRecovery } from "../src/components/HostActionRecovery";
import { OperationRecovery } from "../src/components/OperationRecovery";
import { bootstrapScope } from "../src/bootstrap";
import { createAuthSession } from "../src/state/authority";
import { createOperationRegistry } from "../src/state/operation-registry";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import type { UiBootstrap } from "../src/wire/generated";
import {
    ARCHIVE_ID,
    jsonResponse,
    readWire,
    problemWire,
} from "./read-fixtures";
import {
    deferred,
    OPERATION_ID,
    operationResponse,
    receipt,
} from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const scheduleRoute = "/api/v1/host/sync-schedule/changes";
const observerRoute = "/api/v1/host/sync-observer/stops";
const originalKey = "owned-original-host-action";
const expected = {
    boot_id: ARCHIVE_ID,
    invocation_id: "b".repeat(32),
    main_pid: 1234,
    start_ticks: 5678,
};
const disposers: (() => void)[] = [];
afterEach(() => {
    cleanup();
    disposers
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    vi.unstubAllGlobals();
});
class Storage {
    saved: string | null = null;
    getItem() {
        return this.saved;
    }
    setItem(_key: string, value: string) {
        this.saved = value;
    }
}
function url(input: RequestInfo | URL) {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    );
}
function original(route: string, state = "interrupted") {
    return receipt({
        route,
        state,
        completed_at: ["succeeded", "failed", "interrupted"].includes(state)
            ? "2026-10-20T12:00:01.000000Z"
            : null,
        result_recorded: state === "succeeded" || state === "failed",
    });
}
function outcome(route: string, patch: Record<string, unknown> = {}) {
    return {
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        operation_id: OPERATION_ID,
        request_digest: "e".repeat(64),
        state: "confirmed",
        pending: false,
        ...(route === scheduleRoute
            ? {
                  action: "pause",
                  expected_revision: "a".repeat(64),
                  stored_revision: "a".repeat(64),
                  file_state: "unchanged",
                  manager_state: "timer_acknowledged",
                  timer_was_active: true,
                  timer_is_active: false,
              }
            : { expected, stop_state: "exit_confirmed" }),
        ...patch,
    };
}
function hostWire(route: string, patch: Record<string, unknown> = {}) {
    return {
        ...readWire(
            route === scheduleRoute
                ? "host schedule outcome"
                : "host observer outcome",
            outcome(route, patch),
        ),
        archive_id: ARCHIVE_ID,
        config_fingerprint: null,
    };
}
function bootstrap(hostRead = true, prefix = ""): UiBootstrap {
    const initial = uiBootstrapFixture();
    return {
        ...initial,
        configured_archive_id: ARCHIVE_ID,
        paths: {
            ...initial.paths,
            public_prefix: prefix,
            effective_prefix: prefix,
            ui_base: prefix + "/ui/",
            api_base: prefix + "/api/v1",
            bootstrap: prefix + "/ui/bootstrap.json",
        },
        user: {
            ...initial.user,
            admin_permissions: initial.user.admin_permissions.map((row) => {
                const allowed = row.capability === "host-read" && hostRead;
                return {
                    ...row,
                    granted: allowed,
                    effective: allowed,
                    reason: allowed ? "allowed" : "not_granted",
                };
            }),
        },
    };
}
function setup(
    options: {
        route?: string;
        patch?: Record<string, unknown>;
        receiptState?: string;
        hostRead?: boolean;
        prefix?: string;
        router?: (
            url: URL,
            fallback: () => Response,
            init?: RequestInit,
        ) => Response | Promise<Response>;
        integration?: boolean;
    } = {},
) {
    const route = options.route ?? scheduleRoute;
    const initial = bootstrap(options.hostRead ?? true, options.prefix ?? "");
    vi.stubGlobal("location", new URL(initial.configured_origin));
    const auth = createAuthSession({
        scope: bootstrapScope(initial),
        authGeneration: 1,
    });
    const storage = new Storage();
    const registry = createOperationRegistry({ storage });
    const seeded = registry.importHandle(
        {
            kind: "basic-key",
            key: originalKey,
            operationId: OPERATION_ID,
            originalScope: auth.scope,
        },
        auth,
    );
    registry.observed(
        registry.authorizeObservation(seeded.recordId, auth),
        original(route, options.receiptState),
    );
    const fetcher = vi.fn<typeof fetch>((input, init) => {
        const requested = url(input);
        const fallback = () =>
            jsonResponse(
                requested.pathname.endsWith("/operations/lookup")
                    ? operationResponse("operations lookup", {
                          operation: original(route, options.receiptState),
                      })
                    : hostWire(route, options.patch),
            );
        return Promise.resolve(
            options.router?.(requested, fallback, init) ?? fallback(),
        );
    });
    const controller = createSessionController({
        bootstrap: initial,
        fetcher,
        storage,
        reconnect: () =>
            Promise.resolve({
                ...initial,
                authority_epoch: "f".repeat(32),
                instance_id: "e".repeat(32),
            }),
    });
    disposers.push(() => {
        controller.dispose();
    });
    const first = controller.snapshot().registry.records[0];
    if (first === undefined)
        throw new Error("Original registry record missing");
    const record = first;
    function Connected() {
        const session = useSyncExternalStore(
            controller.subscribe,
            controller.snapshot,
        );
        return options.integration === true ? (
            <OperationRecovery controller={controller} session={session} />
        ) : (
            <HostActionRecovery controller={controller} record={record} />
        );
    }
    const view = render(<Connected />);
    return { controller, fetcher, record, storage, view, Connected, route };
}
async function observe() {
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", {
                name: "Observe original host outcome",
            }),
        ).toBeEnabled();
    });
}
function fact(name: string) {
    const term = screen.getByText(name, { selector: "dt" });
    const definition = term.nextElementSibling;
    if (definition === null) throw new Error("Missing outcome fact");
    return definition;
}
function onlyOriginalGets(
    controller: SessionController,
    fetcher: ReturnType<typeof vi.fn<typeof fetch>>,
    route: string,
    prefix = "",
) {
    expect(fetcher.mock.calls.map(([input]) => url(input).pathname)).toEqual([
        prefix + "/api/v1/operations/lookup",
        prefix + route + "/" + OPERATION_ID,
    ]);
    for (const [input, init] of fetcher.mock.calls) {
        expect(url(input).origin).toBe(
            controller.snapshot().bootstrap.configured_origin,
        );
        expect(init?.method).toBe("GET");
        expect(new Headers(init?.headers).get("Idempotency-Key")).toBe(
            originalKey,
        );
    }
}
test.each([scheduleRoute, observerRoute])(
    "%s mounts without a read and recovers via explicit original-key GETs despite revoked write grants",
    async (route) => {
        const fixture = setup({ route, prefix: "/owned" });
        expect(fixture.fetcher).not.toHaveBeenCalled();
        expect(
            fixture.controller
                .snapshot()
                .bootstrap.user.admin_permissions.filter((row) => row.effective)
                .map((row) => row.capability),
        ).toEqual(["host-read"]);
        expect(fixture.controller.snapshot().canSubmit).toBe(false);
        await observe();
        onlyOriginalGets(fixture.controller, fixture.fetcher, route, "/owned");
        expect(fact("Protected host outcome")).toHaveTextContent("confirmed");
        expect(fact("Pending protected work")).toHaveTextContent("No");
        expect(
            screen.getByText("Original API receipt state: interrupted."),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/accepted backend work has its own outcome/u),
        ).toBeInTheDocument();
        expect(fixture.controller.snapshot().canSubmit).toBe(true);
        expect(fixture.storage.saved).not.toContain("manager_state");
        expect(fixture.storage.saved).not.toContain("file_state");
        expect(fixture.storage.saved).not.toContain("stop_state");
        expect(
            fixture.controller.snapshot().registry.records[0]
                ?.originalAuthority,
        ).toEqual(fixture.record.originalAuthority);
        expect(
            fixture.controller.snapshot().registry.records[0]?.handles,
        ).toEqual(fixture.record.handles);
    },
);
test("file installation and manager uncertainty remain separate from a failed API receipt", async () => {
    const fixture = setup({
        receiptState: "failed",
        patch: {
            state: "effect_unconfirmed",
            pending: true,
            action: "replace",
            stored_revision: "b".repeat(64),
            timer_is_active: null,
            file_state: "installed",
            manager_state: "unknown",
        },
    });
    await observe();
    expect(fact("Stored schedule file")).toHaveTextContent("installed");
    expect(fact("Manager acknowledgement")).toHaveTextContent("unknown");
    expect(
        screen.getByText("Original API receipt state: failed."),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/Protected effects remain unresolved/u),
    ).toBeInTheDocument();
    expect(fixture.controller.snapshot().canSubmit).toBe(false);
    onlyOriginalGets(fixture.controller, fixture.fetcher, scheduleRoute);
});
test("a confirmed protected outcome does not complete a running API receipt or its backend job", async () => {
    const fixture = setup({ route: observerRoute, receiptState: "running" });
    await observe();
    expect(fact("Original observer stop evidence")).toHaveTextContent(
        "exit_confirmed",
    );
    expect(
        screen.getByText("Original API receipt state: running."),
    ).toBeInTheDocument();
    expect(fixture.controller.snapshot().canSubmit).toBe(false);
    expect(fixture.controller.snapshot().registry.records[0]?.state).not.toBe(
        "terminal",
    );
});
test("unchanged is a known no-effect outcome rather than confirmation of the requested change", async () => {
    const fixture = setup({
        patch: {
            state: "unchanged",
            manager_state: "not_sent",
            timer_is_active: true,
        },
    });
    await observe();
    expect(
        screen.getByText(
            /known unchanged.*requested host change is not confirmed/u,
        ),
    ).toBeInTheDocument();
    expect(fixture.controller.snapshot().canSubmit).toBe(true);
    expect(fixture.controller.snapshot().registry.records[0]?.state).not.toBe(
        "terminal",
    );
});
test.each([
    { state: "confirmed", pending: true },
    {
        state: "prepared",
        pending: true,
        manager_state: "not_sent",
        timer_was_active: null,
        timer_is_active: null,
    },
    { state: "unknown", pending: false },
    { state: "conflict", pending: false },
])("protected outcome %j remains unresolved without replay", async (patch) => {
    const fixture = setup({ patch });
    await observe();
    expect(
        screen.getByText(/Protected effects remain unresolved/u),
    ).toBeInTheDocument();
    expect(fixture.controller.snapshot().canSubmit).toBe(false);
    expect(fixture.controller.snapshot().registry.records).toHaveLength(1);
    onlyOriginalGets(fixture.controller, fixture.fetcher, scheduleRoute);
});
test.each(["lookup", "outcome"])(
    "missing %s history stays unconfirmed and preserves the original handles",
    async (missing) => {
        const fixture = setup({
            router(requested, fallback) {
                return (requested.pathname.endsWith("/lookup")
                    ? "lookup"
                    : "outcome") === missing
                    ? jsonResponse(problemWire("HFAPI003"), 404)
                    : fallback();
            },
        });
        await observe();
        expect(
            screen.getByText(/Diagnostic code: HFAPI003/u),
        ).toBeInTheDocument();
        if (missing === "lookup")
            expect(
                screen.getByText(
                    /Missing history does not prove nonexecution/u,
                ),
            ).toBeInTheDocument();
        expect(
            screen.queryByText("Protected host outcome", { selector: "dt" }),
        ).not.toBeInTheDocument();
        expect(fixture.controller.snapshot().canSubmit).toBe(false);
        expect(
            fixture.controller.snapshot().registry.records[0]?.handles,
        ).toEqual(fixture.record.handles);
        expect(fixture.fetcher).toHaveBeenCalledTimes(
            missing === "lookup" ? 1 : 2,
        );
        expect(
            fixture.fetcher.mock.calls.every(
                ([, init]) => init?.method === "GET",
            ),
        ).toBe(true);
    },
);
test("host-read denial disables original outcome reads without changing or removing the record", () => {
    const fixture = setup({ hostRead: false });
    expect(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    ).toBeDisabled();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(fixture.controller.snapshot().registry.records[0]?.handles).toEqual(
        fixture.record.handles,
    );
});
test("disconnect hides a late old-generation outcome and requires an explicit fresh observation after reconnect", async () => {
    const slow = deferred<Response>();
    let outcomeReads = 0;
    const fixture = setup({
        router(requested, fallback) {
            if (!requested.pathname.endsWith("/lookup") && ++outcomeReads === 1)
                return slow.promise;
            return fallback();
        },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    );
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(2);
    });
    act(() => {
        fixture.controller.disconnect();
    });
    expect(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    ).toBeDisabled();
    await act(async () => {
        slow.resolve(jsonResponse(hostWire(scheduleRoute)));
        await Promise.resolve();
    });
    expect(
        screen.queryByText("Protected host outcome", { selector: "dt" }),
    ).not.toBeInTheDocument();
    expect(fixture.controller.snapshot().canSubmit).toBe(false);
    await act(async () => {
        await fixture.controller.reconnect();
    });
    expect(fixture.fetcher).toHaveBeenCalledTimes(2);
    expect(
        screen.queryByText("Protected host outcome", { selector: "dt" }),
    ).not.toBeInTheDocument();
    await observe();
    expect(fact("Protected host outcome")).toHaveTextContent("confirmed");
    expect(fixture.fetcher).toHaveBeenCalledTimes(4);
    expect(
        fixture.controller.snapshot().registry.records[0]?.originalAuthority,
    ).toEqual(fixture.record.originalAuthority);
});
test("route unmount releases the charged private outcome without removing original recovery handles", async () => {
    const fixture = setup();
    await observe();
    const owners = Array.from({ length: 4 }, () =>
        fixture.controller.createPrivateSlot(),
    );
    for (const owner of owners.slice(0, 3))
        expect(owner.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    const last = owners[3];
    if (last === undefined) throw new Error("Missing private capacity owner");
    expect(last.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(false);
    fixture.view.unmount();
    expect(last.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    for (const owner of owners) owner.clear();
    render(<fixture.Connected />);
    expect(
        screen.queryByText("Protected host outcome", { selector: "dt" }),
    ).not.toBeInTheDocument();
    expect(fixture.fetcher).toHaveBeenCalledTimes(2);
    expect(fixture.controller.snapshot().registry.records[0]?.handles).toEqual(
        fixture.record.handles,
    );
});
test("capacity refusal sends no GET or POST, keeps the original key, and does not infer a host outcome", async () => {
    const fixture = setup();
    const owners = Array.from({ length: 4 }, () =>
        fixture.controller.createPrivateSlot(),
    );
    for (const owner of owners)
        expect(owner.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    await observe();
    expect(
        screen.getByText(
            /Preserve the original handles; no write was retried/u,
        ),
    ).toBeInTheDocument();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(fixture.controller.snapshot().canSubmit).toBe(false);
    expect(fixture.controller.snapshot().registry.records[0]?.handles).toEqual(
        fixture.record.handles,
    );
    for (const owner of owners) owner.clear();
});
test("post-read private retention refusal preserves the original handle and reports capacity without replay", async () => {
    const fixture = setup();
    const owners = Array.from({ length: 4 }, () =>
        fixture.controller.createPrivateSlot(),
    );
    let filled = false;
    const claims: boolean[] = [];
    const unsubscribe = fixture.controller.subscribe(() => {
        if (filled || !fixture.controller.snapshot().canSubmit) return;
        filled = true;
        // Host proof publishes before the read promise reaches the view. A
        // separate admitted RAM owner can take that released response capacity.
        queueMicrotask(() => {
            for (const owner of owners)
                claims.push(owner.set("x".repeat(8 * 1024 * 1024 - 2)));
        });
    });
    await observe();
    expect(claims).toEqual([true, true, true, true]);
    expect(
        screen.getByText(/Browser read capacity is unavailable/u),
    ).toBeInTheDocument();
    expect(
        screen.queryByText("Protected host outcome", { selector: "dt" }),
    ).not.toBeInTheDocument();
    expect(fixture.controller.snapshot().registry.records[0]?.handles).toEqual(
        fixture.record.handles,
    );
    onlyOriginalGets(fixture.controller, fixture.fetcher, scheduleRoute);
    unsubscribe();
    for (const owner of owners) owner.clear();
});
test("a late outcome after unmount creates no retained private result or new request", async () => {
    const slow = deferred<Response>();
    const fixture = setup({
        router(requested, fallback) {
            return requested.pathname.endsWith("/lookup")
                ? fallback()
                : slow.promise;
        },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original host outcome" }),
    );
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(2);
    });
    fixture.view.unmount();
    await act(async () => {
        slow.resolve(jsonResponse(hostWire(scheduleRoute)));
        await Promise.resolve();
    });
    await waitFor(() => {
        expect(fixture.controller.snapshot().canSubmit).toBe(true);
    });
    const owners = Array.from({ length: 4 }, () =>
        fixture.controller.createPrivateSlot(),
    );
    for (const owner of owners)
        expect(owner.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    expect(
        screen.queryByRole("region", { name: "Original host outcome" }),
    ).not.toBeInTheDocument();
    onlyOriginalGets(fixture.controller, fixture.fetcher, scheduleRoute);
    for (const owner of owners) owner.clear();
});
test.each([scheduleRoute, observerRoute])(
    "OperationRecovery includes %s original host outcomes without an automatic observer or effect",
    async (route) => {
        const fixture = setup({ route, integration: true });
        const entry = screen.getByRole("article", {
            name: "Recovery record " + fixture.record.recordId,
        });
        expect(
            within(entry).getByRole("region", {
                name: "Original host outcome",
            }),
        ).toBeInTheDocument();
        expect(fixture.fetcher).not.toHaveBeenCalled();
        await observe();
        expect(
            within(entry).getByText("Original API receipt state: interrupted."),
        ).toBeInTheDocument();
        expect(
            within(entry).getByText(/Browser observation/u).nextElementSibling,
        ).toHaveTextContent("idle");
        onlyOriginalGets(fixture.controller, fixture.fetcher, route);
    },
);
