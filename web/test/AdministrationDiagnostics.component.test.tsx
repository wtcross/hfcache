/** Real shared jobs/controller/client composition; labelled HTTP fixtures, no host effects. */
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
import { AdministrationDiagnostics } from "../src/components/AdministrationDiagnostics";
import { createJobsStore } from "../src/operations/jobs-state";
import { createSessionController } from "../src/state/session-controller";
import type {
    DiagnosticCheckPayload,
    UiBootstrap,
} from "../src/wire/generated";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import { deferred, events, operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const disposers: (() => void)[] = [];
afterEach(() => {
    cleanup();
    disposers
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    vi.restoreAllMocks();
});
const OPERATION = "a".repeat(32);
const ROUTE = "/api/v1/diagnostics";
const PROBE_REVIEW =
    "I understand these probes can write temporary archive data.";
const checks: readonly DiagnosticCheckPayload[] = [
    {
        name: "configuration",
        outcome: "pass",
        detail: "Owned configuration is valid.",
    },
    {
        name: "atomic_rename",
        outcome: "skipped",
        detail: "Read-only mode does not perform this archive probe.",
    },
];
function requestUrl(input: RequestInfo | URL): URL {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    );
}
function operation(terminal = false, failed = false) {
    return receipt({
        route: ROUTE,
        state: terminal ? (failed ? "failed" : "succeeded") : "queued",
        updated_at: terminal
            ? "2026-10-20T12:00:02.000000Z"
            : "2026-10-20T12:00:01.000000Z",
        completed_at: terminal ? "2026-10-20T12:00:02.000000Z" : null,
        result_recorded: terminal,
        domain_run_id: terminal ? "3".repeat(32) : null,
    });
}
function acceptance() {
    const status = "/api/v1/operations/" + OPERATION;
    return new Response(
        JSON.stringify({
            schema_version: 1,
            request_id: "f".repeat(32),
            archive_id: ARCHIVE_ID,
            config_fingerprint: "2".repeat(64),
            created: true,
            operation: operation(),
            links: {
                status,
                result: status + "/result",
                events: status + "/events",
            },
        }),
        {
            status: 202,
            headers: { "Content-Type": "application/json", Location: status },
        },
    );
}
function resultWire(payload: unknown, failed = false) {
    return operationResponse("doctor", payload, failed);
}
interface Options {
    admission?: "accepted" | "denied" | "lost";
    result?: unknown;
    failed?: boolean;
    capabilities?: UiBootstrap["user"]["rest_capabilities"];
    quota?: boolean;
    route?: (
        url: URL,
        init?: RequestInit,
    ) => Response | Promise<Response> | undefined;
}
function mount(options: Options = {}) {
    const storage = new Map<string, string>();
    const trace: string[] = [];
    const bootstrap: UiBootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: window.location.origin,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...uiBootstrapFixture().user,
            rest_capabilities: options.capabilities ?? ["read", "write"],
        },
    };
    let originalKey: string | null = null;
    const fetcher = vi.fn<typeof fetch>((input, init) => {
        const url = requestUrl(input);
        trace.push(`${init?.method ?? "GET"} ${url.pathname}`);
        if (init?.method === "POST") {
            originalKey = new Headers(init.headers).get("Idempotency-Key");
            expect(originalKey).toBeTruthy();
            expect(
                [...storage.values()].some((value) =>
                    value.includes(originalKey ?? "missing"),
                ),
            ).toBe(true);
            expect(url.pathname).toBe(ROUTE);
        }
        const custom = options.route?.(url, init);
        if (custom !== undefined) return Promise.resolve(custom);
        if (init?.method === "POST") {
            if (options.admission === "lost")
                return Promise.reject(
                    new TypeError("private transport detail hf_NEVER_DISPLAY"),
                );
            if (options.admission === "denied")
                return Promise.resolve(
                    jsonResponse(problemWire("HFAPI002"), 403),
                );
            return Promise.resolve(acceptance());
        }
        if (url.pathname.endsWith("/result"))
            return Promise.resolve(
                jsonResponse(
                    resultWire(options.result ?? { checks }, options.failed),
                ),
            );
        if (url.pathname.endsWith("/events"))
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations events", events([])),
                ),
            );
        if (
            url.pathname === "/api/v1/operations/lookup" ||
            url.pathname === "/api/v1/operations/" + OPERATION
        ) {
            const complete = options.result !== undefined;
            const current = complete
                ? operation(true, options.failed)
                : receipt({
                      route: ROUTE,
                      state: "interrupted",
                      domain_run_id: null,
                      updated_at: "2026-10-20T12:00:02.000000Z",
                      completed_at: "2026-10-20T12:00:02.000000Z",
                  });
            return Promise.resolve(
                jsonResponse(
                    operationResponse(
                        url.pathname.endsWith("/lookup")
                            ? "operations lookup"
                            : "operations show",
                        { operation: current },
                    ),
                ),
            );
        }
        return Promise.resolve(jsonResponse(problemWire("HFAPI019", 20), 404));
    });
    const controller = createSessionController({
        bootstrap,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
        storage: {
            getItem: (key) => storage.get(key) ?? null,
            setItem: (key, value) => {
                if (options.quota) throw new Error("Owned quota refusal");
                trace.push("persist");
                storage.set(key, value);
            },
        },
    });
    const jobs = createJobsStore(controller);
    disposers.push(() => {
        jobs.dispose();
        controller.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            controller.subscribe,
            controller.snapshot,
        );
        return (
            <AdministrationDiagnostics
                key={session.generation}
                store={jobs}
                session={session}
            />
        );
    }
    return {
        controller,
        jobs,
        fetcher,
        storage,
        trace,
        posts: () =>
            fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
        ...render(<Connected />),
    };
}
async function runReadOnly() {
    await userEvent.click(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    );
    return screen.findByRole("region", { name: "Original diagnostic job" });
}

test("mounting and reviewing probes are read-free, and probe acknowledgement alone does not submit", async () => {
    const fixture = mount();
    expect(
        screen.getByRole("region", { name: "Diagnostics" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Run temporary archive probes" }),
    ).toBeDisabled();
    await userEvent.click(screen.getByRole("checkbox", { name: PROBE_REVIEW }));
    expect(
        screen.getByRole("button", { name: "Run temporary archive probes" }),
    ).toBeEnabled();
    await userEvent.click(screen.getByRole("checkbox", { name: PROBE_REVIEW }));
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
    expect(fixture.storage.size).toBe(0);
});

test.each([true, false])(
    "explicit diagnostic intent read_only=%s persists its original key before its only POST",
    async (readOnly) => {
        const fixture = mount();
        expect(fixture.jobs.snapshot().form.kind).toBe("installedPlan");
        if (!readOnly)
            await userEvent.click(
                screen.getByRole("checkbox", { name: PROBE_REVIEW }),
            );
        await userEvent.click(
            screen.getByRole("button", {
                name: readOnly
                    ? "Run read-only diagnostics"
                    : "Run temporary archive probes",
            }),
        );
        const original = await screen.findByRole("region", {
            name: "Original diagnostic job",
        });
        expect(
            within(original).getByText(
                /HTTP 202 acknowledges admission, not completion/,
            ),
        ).toBeInTheDocument();
        expect(fixture.jobs.snapshot().form).toEqual({
            kind: "diagnostics",
            readOnly,
        });
        expect(fixture.jobs.snapshot().lastAction).toBe(
            readOnly ? "readOnlyDiagnostics" : "probeDiagnostics",
        );
        const post = fixture.posts()[0];
        expect(fixture.posts()).toHaveLength(1);
        expect(
            typeof post?.[1]?.body === "string"
                ? JSON.parse(post[1].body)
                : null,
        ).toEqual({ read_only: readOnly });
        expect(fixture.trace.indexOf("persist")).toBeLessThan(
            fixture.trace.indexOf("POST " + ROUTE),
        );
        expect(
            screen.getByRole("checkbox", { name: PROBE_REVIEW }),
        ).not.toBeChecked();
        expect(
            screen.getByRole("button", { name: "Run read-only diagnostics" }),
        ).toBeDisabled();
        expect([...fixture.storage.values()].join()).not.toContain("read_only");
    },
);

test("an uncertain admission keeps one original key and cannot be replayed by either diagnostic button", async () => {
    const fixture = mount({ admission: "lost" });
    const original = await runReadOnly();
    expect(within(original).getByRole("alert")).toHaveTextContent(
        "Admission is uncertain",
    );
    expect(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Run temporary archive probes" }),
    ).toBeDisabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    );
    expect(fixture.posts()).toHaveLength(1);
    expect(fixture.controller.snapshot().registry.records).toHaveLength(1);
    expect([...fixture.storage.values()].join()).toContain("basic-key");
    expect(document.body).not.toHaveTextContent("private transport detail");
    expect(document.body).not.toHaveTextContent("hf_NEVER_DISPLAY");
});

test("a real API refusal preserves its safe code without showing raw problem text or inventing checks", async () => {
    const fixture = mount({ admission: "denied" });
    const original = await runReadOnly();
    expect(within(original).getByRole("alert")).toHaveTextContent(
        "HTTP 403, HFAPI002",
    );
    expect(
        screen.queryByRole("region", { name: "Diagnostic checks" }),
    ).not.toBeInTheDocument();
    expect(document.body).not.toHaveTextContent("Private service detail");
    expect(document.querySelector("script")).toBeNull();
    expect(fixture.posts()).toHaveLength(1);
    expect(fixture.fetcher).toHaveBeenCalledTimes(1);
});

test("reader capability permits read-only diagnostics but cannot acknowledge or submit archive probes", async () => {
    const fixture = mount({ capabilities: ["read"] });
    expect(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    ).toBeEnabled();
    expect(screen.getByRole("checkbox", { name: PROBE_REVIEW })).toBeDisabled();
    await userEvent.click(screen.getByRole("checkbox", { name: PROBE_REVIEW }));
    await userEvent.click(
        screen.getByRole("button", { name: "Run temporary archive probes" }),
    );
    expect(fixture.fetcher).not.toHaveBeenCalled();
    await runReadOnly();
    expect(fixture.posts()).toHaveLength(1);
});

test("disconnect clears local acknowledgement and private results; reconnect does not re-arm probes or submit", async () => {
    const fixture = mount();
    await userEvent.click(screen.getByRole("checkbox", { name: PROBE_REVIEW }));
    act(() => {
        fixture.controller.disconnect();
    });
    expect(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("checkbox", { name: PROBE_REVIEW }),
    ).not.toBeChecked();
    await act(async () => {
        await fixture.controller.reconnect();
    });
    expect(
        screen.getByRole("button", { name: "Run temporary archive probes" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("checkbox", { name: PROBE_REVIEW }),
    ).not.toBeChecked();
    expect(fixture.fetcher).not.toHaveBeenCalled();
});

test("a failed doctor preserves partial pass/fail/skipped evidence and its actual exit classification", async () => {
    const partial: readonly DiagnosticCheckPayload[] = [
        ...checks.slice(0, 1),
        {
            name: "free_space",
            outcome: "fail",
            detail: "Owned reserve refusal",
        },
        ...checks.slice(1),
    ];
    const fixture = mount({ result: { checks: partial }, failed: true });
    await runReadOnly();
    const panel = await screen.findByRole("region", {
        name: "Diagnostic checks",
    });
    expect(
        within(panel).getByText(/Skipped checks are not passes/),
    ).toBeInTheDocument();
    expect(within(panel).getByText("pass")).toBeInTheDocument();
    expect(within(panel).getByText("fail")).toBeInTheDocument();
    expect(within(panel).getByText("skipped")).toBeInTheDocument();
    expect(
        within(panel).getByText(/Owned reserve refusal/),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/failed a preflight or environment check/),
    ).toBeInTheDocument();
    const result = screen.getByRole("region", {
        name: "Original operation result",
    });
    expect(
        within(result).getByText("Domain outcome").nextElementSibling,
    ).toHaveTextContent("failed");
    expect(within(result).getByText("20")).toBeInTheDocument();
    expect(fixture.jobs.snapshot().observation?.result?.kind).toBe(
        "domain_failure",
    );
    expect(fixture.posts()).toHaveLength(1);
});

test("a successful read-only result renders skipped checks honestly and escapes upstream-looking text", async () => {
    const literal =
        '<img src=x onerror="window.hf_owned_leak=1">literal detail';
    const fixture = mount({
        result: {
            checks: [
                ...checks,
                { name: "literal", outcome: "pass", detail: literal },
            ],
        },
    });
    await runReadOnly();
    const panel = await screen.findByRole("region", {
        name: "Diagnostic checks",
    });
    expect(
        within(panel).getByText(/Skipped checks are not passes/),
    ).toBeInTheDocument();
    expect(
        within(panel).getByText(literal, { exact: false }),
    ).toBeInTheDocument();
    expect(document.querySelector("img, iframe, script")).toBeNull();
    expect(
        screen.getByText(/original command completed successfully/),
    ).toBeInTheDocument();
    expect([...fixture.storage.values()].join()).not.toContain(literal);
});

test.each([
    ["empty failure payload", {}, true],
    [
        "malformed diagnostic result",
        {
            checks: [
                { name: "archive", outcome: "healthy", detail: "invalid" },
            ],
        },
        false,
    ],
])(
    "%s never invents successful check rows",
    async (_label, payload, failed) => {
        const fixture = mount({ result: payload, failed });
        await runReadOnly();
        await waitFor(() => {
            expect(fixture.jobs.snapshot().observation?.phase).toMatch(
                /settled|unknown/,
            );
        });
        expect(
            screen.queryByRole("region", { name: "Diagnostic checks" }),
        ).not.toBeInTheDocument();
        expect(screen.queryByText("healthy")).not.toBeInTheDocument();
        expect(fixture.posts()).toHaveLength(1);
    },
);

test("large valid diagnostics replace local rows in pages of 25 and clamp long check fields without another request", async () => {
    const large: readonly DiagnosticCheckPayload[] = Array.from(
        { length: 27 },
        (_, i) => ({
            name: i === 0 ? "n".repeat(300) : "check-" + String(i),
            outcome: "pass",
            detail: i === 0 ? "d".repeat(5000) : "detail-" + String(i),
        }),
    );
    const fixture = mount({ result: { checks: large } });
    await runReadOnly();
    const panel = await screen.findByRole("region", {
        name: "Diagnostic checks",
    });
    const collection = within(panel).getByRole("region", {
        name: "diagnostic checks",
    });
    expect(within(collection).getAllByRole("listitem")).toHaveLength(25);
    expect(collection).not.toHaveTextContent("n".repeat(257));
    expect(collection).not.toHaveTextContent("d".repeat(4097));
    expect(within(collection).getAllByText(/display truncated/)).toHaveLength(
        2,
    );
    const before = fixture.fetcher.mock.calls.length;
    await userEvent.click(
        within(collection).getByRole("button", {
            name: "Next diagnostic checks",
        }),
    );
    expect(within(collection).getAllByRole("listitem")).toHaveLength(2);
    expect(within(collection).getByText("check-26")).toBeInTheDocument();
    expect(within(collection).queryByText("check-1")).not.toBeInTheDocument();
    await userEvent.click(
        within(collection).getByRole("button", {
            name: "Previous diagnostic checks",
        }),
    );
    expect(within(collection).getAllByRole("listitem")).toHaveLength(25);
    expect(fixture.fetcher).toHaveBeenCalledTimes(before);
});

test("shared job input and a pending estimate disable diagnostics; unmount pauses that read without a POST", async () => {
    const pending = deferred<Response>();
    const transport: { signal: AbortSignal | null } = { signal: null };
    const fixture = mount({
        route: (url, init) => {
            if (url.pathname === "/api/v1/verification/estimate") {
                transport.signal = init?.signal ?? null;
                return pending.promise;
            }
            return undefined;
        },
    });
    let reading: Promise<void> = Promise.resolve();
    act(() => {
        reading = fixture.jobs.estimate();
    });
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(1);
    });
    expect(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    ).toBeDisabled();
    fixture.unmount();
    expect(transport.signal?.aborted).toBe(true);
    expect(fixture.jobs.snapshot().pending).toBeNull();
    pending.resolve(
        jsonResponse(
            operationResponse("verify --estimate", {
                mode: "estimate",
                repositories: 0,
                revisions: 0,
                unique_bytes: 0,
                unique_objects: 0,
                unreadable_objects: 0,
                estimated_duration_seconds: null,
                measured_throughput_bytes_per_second: null,
                storage_maintenance: "undetectable",
            }),
        ),
    );
    await act(async () => {
        await reading;
    });
    expect(fixture.jobs.snapshot().estimate?.result).toBeNull();
    expect(fixture.posts()).toHaveLength(0);
});

test("an admitted late acknowledgement survives unmount without private diagnostic bodies in browser storage", async () => {
    const delayed = deferred<Response>();
    const fixture = mount({
        route: (_url, init) =>
            init?.method === "POST" ? delayed.promise : undefined,
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    );
    expect(fixture.posts()).toHaveLength(1);
    fixture.unmount();
    delayed.resolve(acceptance());
    await waitFor(() => {
        expect(fixture.jobs.snapshot().submission?.kind).toBe("accepted");
    });
    expect(fixture.controller.snapshot().registry.records).toHaveLength(1);
    expect(
        fixture.controller.snapshot().registry.records[0]?.handles.kind,
    ).toBe("basic-key");
    expect([...fixture.storage.values()].join()).not.toContain("read_only");
    expect(fixture.posts()).toHaveLength(1);
});

test("persistence refusal blocks transmission and does not manufacture an admitted diagnostic", async () => {
    const fixture = mount({ quota: true });
    await userEvent.click(
        screen.getByRole("button", { name: "Run read-only diagnostics" }),
    );
    await waitFor(() => {
        expect(fixture.jobs.snapshot().pending).toBeNull();
    });
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(
        screen.queryByRole("region", { name: "Original diagnostic job" }),
    ).not.toBeInTheDocument();
    expect(fixture.jobs.snapshot().submission).toBeNull();
});
