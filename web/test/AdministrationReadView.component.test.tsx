/** Rendered UI with the actual session/query/client boundary and controlled HTTP literals. */
import {
    act,
    cleanup,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { AdministrationReadView } from "../src/components/AdministrationReadView";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { WARNING_GUIDANCE } from "../src/administration/warnings";
import { createSessionController } from "../src/state/session-controller";
import { uiBootstrapFixture } from "./ui-fixtures";
import {
    ARCHIVE_ID,
    jsonResponse,
    readWire,
    statusPayload,
    versionPayload,
    problemWire,
    inspectionPayload,
} from "./read-fixtures";
import { hostStatusFixture, hostStatusWire } from "./host-fixtures";
import { deferred } from "./state-fixtures";

const cleanups: (() => void)[] = [];
afterEach(() => {
    cleanup();
    for (const dispose of cleanups.splice(0)) dispose();
    vi.unstubAllGlobals();
});
function path(input: RequestInfo | URL) {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    ).pathname;
}
function mounted(
    options: {
        reachable?: boolean;
        policy?: boolean | null;
        router?: (
            url: string,
            fallback: () => Response,
        ) => Response | Promise<Response>;
    } = {},
) {
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal("location", new URL(bootstrap.configured_origin));
    const fetcher = vi.fn<typeof fetch>((input) => {
        const url = path(input);
        const fallback = () =>
            jsonResponse(
                url.endsWith("/status")
                    ? readWire(
                          "status",
                          statusPayload(options.reachable ?? true),
                      )
                    : url.endsWith("/health")
                      ? readWire("health", {
                            ready: true,
                            policy_valid: options.policy ?? null,
                            archive: null,
                        })
                      : readWire("version", versionPayload),
            );
        return Promise.resolve(options.router?.(url, fallback) ?? fallback());
    });
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: null,
        reconnect: () => Promise.resolve(bootstrap),
    });
    const store = createAdministrationReadStore(controller);
    const onNavigate = vi.fn();
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    const props = () => ({
        store,
        controller,
        session: controller.snapshot(),
        onNavigate,
    });
    const view = render(<AdministrationReadView {...props()} />);
    return { store, controller, fetcher, onNavigate, view, props };
}
function definition(name: string) {
    const parent = screen.getByText(name, { selector: "dt" }).parentElement;
    if (parent === null) throw new Error("Missing definition");
    return within(parent).getByRole("definition");
}
test("viewing and explicit refresh perform only three bounded GETs each, with no host-status or operation submission", async () => {
    const fixture = mounted();
    await screen.findByText("API daemon: Ready.");
    await waitFor(() => {
        expect(definition("API application version")).toHaveTextContent(
            versionPayload.application,
        );
    });
    expect(fixture.fetcher).toHaveBeenCalledTimes(3);
    expect(
        fixture.fetcher.mock.calls.every(([, init]) => init?.method === "GET"),
    ).toBe(true);
    expect(fixture.controller.hostStatus.snapshot().phase).toBe("idle");
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
    await userEvent.click(
        screen.getByRole("button", { name: "Refresh administration status" }),
    );
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(6);
    });
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
});
test.each([false, null])(
    "daemon readiness with policy %s never becomes archive health or change permission",
    async (policy) => {
        mounted({ reachable: false, policy });
        await screen.findByText("API daemon: Ready.");
        expect(
            screen.getByText(
                `Installed policy: ${policy === false ? "Invalid" : "Unknown"}.`,
            ),
        ).toBeInTheDocument();
        expect(screen.getByText("Archive: Unreachable.")).toBeInTheDocument();
        for (const name of [
            "Available bytes",
            "Configured reserve bytes",
            "Headroom bytes",
            "Total bytes",
        ])
            expect(definition(name)).toHaveTextContent("Unavailable");
        expect(
            screen.getByText("No full verification has been observed."),
        ).toBeInTheDocument();
        expect(
            screen.queryByText(/archive.*healthy/iu),
        ).not.toBeInTheDocument();
    },
);
test("observed zero capacity is displayed as zero while a missing verification remains unverified", async () => {
    mounted();
    await screen.findByText("Archive: Reachable.");
    expect(definition("Available bytes")).toHaveTextContent(/^0$/u);
    expect(definition("Configured reserve bytes")).toHaveTextContent(/^0$/u);
    expect(
        screen.getByText("No full verification has been observed."),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/No degraded verification state was reported/u),
    ).toBeInTheDocument();
});
test("a valid installed policy can coexist with an unusable archive inspection", async () => {
    mounted({
        router(url, fallback) {
            return url.endsWith("/health")
                ? jsonResponse(
                      readWire("health", {
                          ready: true,
                          policy_valid: true,
                          archive: inspectionPayload,
                      }),
                  )
                : fallback();
        },
    });
    await screen.findByText("Installed policy: Valid.");
    expect(
        screen.getByText("Archive inspection: unusable."),
    ).toBeInTheDocument();
    expect(screen.getByText("API daemon: Ready.")).toBeInTheDocument();
});
test("last failed full verification and outstanding failures remain distinct from present reachability", async () => {
    mounted({
        router(url, fallback) {
            if (!url.endsWith("/status")) return fallback();
            const data = statusPayload(true);
            return jsonResponse(
                readWire("status", {
                    ...data,
                    archive: {
                        ...data.archive,
                        verification: {
                            degraded: true,
                            outstanding_failures: 2,
                            last_full_verification: {
                                started_at: "2026-10-27T00:00:00.000000Z",
                                completed_at: "2026-10-27T00:01:00.000000Z",
                                duration_seconds: 60,
                                outcome: "failed",
                                report: "reports/verification/owned.json",
                                unique_bytes: 4,
                                unique_objects: 1,
                                throughput_bytes_per_second: 1,
                            },
                        },
                    },
                }),
            );
        },
    });
    await screen.findByText("Archive: Reachable.");
    expect(screen.getByText(/Verification is degraded/u)).toHaveTextContent(
        "Outstanding failures: 2",
    );
    expect(definition("Last full verification")).toHaveTextContent("failed");
    expect(
        screen.getByText(/recorded verification history/u),
    ).toBeInTheDocument();
});
test("all runbook warnings and unknown fallback remain escaped and navigate only explicit existing workflows", async () => {
    const codes = [...Object.keys(WARNING_GUIDANCE), "HFNEW999"];
    const fixture = mounted({
        router(url, fallback) {
            if (!url.endsWith("/status")) return fallback();
            const wire = readWire("status", statusPayload(true));
            return jsonResponse({
                ...wire,
                envelope: {
                    ...wire.envelope,
                    outcome: "success_with_warnings",
                    warnings: codes.map((code) => ({
                        code,
                        message: '<img src="/api/v1/unsafe">',
                        repository: null,
                        context: { hidden: "do-not-render-context" },
                    })),
                },
            });
        },
    });
    const warnings = await screen.findByRole("region", {
        name: "Archive status warnings",
    });
    await within(warnings).findByText("HFNEW999", { selector: "code" });
    for (const code of codes)
        expect(
            within(warnings).getByText(code, { selector: "code" }),
        ).toBeInTheDocument();
    expect(
        within(warnings).getByText(/Unrecognized warning/u),
    ).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(screen.queryByText("do-not-render-context")).not.toBeInTheDocument();
    await userEvent.click(
        within(warnings).getByRole("button", {
            name: "Review configured dependencies",
        }),
    );
    expect(fixture.onNavigate).toHaveBeenLastCalledWith("configuration");
    await userEvent.click(
        within(warnings).getByRole("button", {
            name: "Review metadata refresh",
        }),
    );
    expect(fixture.onNavigate).toHaveBeenLastCalledWith("operations");
    await userEvent.click(
        within(warnings).getByRole("button", {
            name: "Review operation details",
        }),
    );
    expect(fixture.onNavigate).toHaveBeenLastCalledWith("operations");
    expect(fixture.fetcher).toHaveBeenCalledTimes(3);
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
});
test("archive findings, unknown entries and warnings page locally in groups of25 without extra GETs", async () => {
    const fixture = mounted({
        router(url, fallback) {
            if (!url.endsWith("/status")) return fallback();
            const data = statusPayload(true),
                wire = readWire("status", {
                    ...data,
                    archive: {
                        ...data.archive,
                        findings: Array.from({ length: 60 }, (_, i) => ({
                            age_hours: 1,
                            area: "staging",
                            path: "staging/entry-" + String(i),
                            transaction_id: i.toString(16).padStart(32, "0"),
                            stale: true,
                        })),
                        unknown_entries: Array.from(
                            { length: 60 },
                            (_, i) => "unknown/entry-" + String(i),
                        ),
                    },
                });
            return jsonResponse({
                ...wire,
                envelope: {
                    ...wire.envelope,
                    outcome: "success_with_warnings",
                    warnings: Array.from({ length: 60 }, () => ({
                        code: "HFWRN003",
                        message: "Preserved",
                        context: {},
                        repository: null,
                    })),
                },
            });
        },
    });
    await screen.findByText("Archive: Reachable.");
    for (const name of [
        "archive area findings",
        "unknown archive entries",
        "Archive status warnings",
    ]) {
        const collection = screen.getByRole("region", { name });
        expect(within(collection).getAllByRole("listitem")).toHaveLength(25);
        await userEvent.click(
            within(collection).getByRole("button", { name: "Next " + name }),
        );
        expect(within(collection).getAllByRole("listitem")).toHaveLength(25);
        expect(
            within(collection).getByText(/Showing 26–50 of 60 loaded/u),
        ).toBeInTheDocument();
    }
    expect(fixture.fetcher).toHaveBeenCalledTimes(3);
});
test("failed and malformed reads display their classifications without an empty archive claim", async () => {
    mounted({
        router(url, fallback) {
            return url.endsWith("/status")
                ? jsonResponse(problemWire("HFAPI016", 20), 503)
                : url.endsWith("/health")
                  ? jsonResponse({ malformed: true })
                  : fallback();
        },
    });
    await screen.findByText(/Diagnostic code: HFAPI016/u);
    await screen.findByText("API health could not be validated.");
    expect(screen.queryByText("Archive: Reachable.")).not.toBeInTheDocument();
    expect(screen.queryByText("API daemon: Ready.")).not.toBeInTheDocument();
    expect(
        screen.queryByText("No archive area findings in this result."),
    ).not.toBeInTheDocument();
});
test("stale facts are visibly qualified; failed refresh removes successful capacity values", async () => {
    const slow = deferred<Response>();
    let refreshing = false;
    const fixture = mounted({
        router(url, fallback) {
            return refreshing && url.endsWith("/status")
                ? slow.promise
                : fallback();
        },
    });
    await waitFor(() => {
        expect(fixture.store.snapshot().version.phase).toBe("ready");
    });
    refreshing = true;
    let work: Promise<void> = Promise.resolve();
    act(() => {
        work = fixture.store.refresh();
    });
    await screen.findByText(/Archive status is stale/u);
    expect(definition("Available bytes")).toHaveTextContent(/^0$/u);
    await act(async () => {
        slow.resolve(jsonResponse(problemWire("HFAPI016", 20), 503));
        await work;
    });
    expect(
        screen.queryByText("Available bytes", { selector: "dt" }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Diagnostic code: HFAPI016/u)).toBeInTheDocument();
});
test("software identities use the bootstrap and existing host owner without another host GET", async () => {
    const fixture = mounted({
        router(url, fallback) {
            return url.endsWith("/host/status")
                ? jsonResponse({
                      ...hostStatusWire({
                          ...hostStatusFixture(),
                          binding: {
                              ...hostStatusFixture().binding,
                              archive_id: ARCHIVE_ID,
                          },
                      }),
                      archive_id: ARCHIVE_ID,
                  })
                : fallback();
        },
    });
    await waitFor(() => {
        expect(fixture.store.snapshot().version.phase).toBe("ready");
    });
    expect(definition("UI application version")).toHaveTextContent("0.2.2");
    expect(definition("Installed host release")).toHaveTextContent(
        "Unavailable",
    );
    await act(async () => {
        await fixture.controller.hostStatus.refresh();
    });
    expect(definition("Installed host release")).toHaveTextContent(
        hostStatusFixture().binding?.release_version ?? "missing",
    );
    expect(fixture.fetcher).toHaveBeenCalledTimes(4);
    expect(
        screen.getByText(/Version observations differ/u),
    ).toBeInTheDocument();
});
test("unmount releases read ownership and return performs fresh reads; disconnected facts clear", async () => {
    const fixture = mounted();
    await waitFor(() => {
        expect(fixture.store.snapshot().version.phase).toBe("ready");
    });
    fixture.view.unmount();
    expect(fixture.store.snapshot().status.result).toBeNull();
    render(<AdministrationReadView {...fixture.props()} />);
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(6);
    });
    act(() => {
        fixture.controller.disconnect();
    });
    expect(screen.queryByText("Archive: Reachable.")).not.toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Refresh administration status" }),
    ).toBeDisabled();
});
