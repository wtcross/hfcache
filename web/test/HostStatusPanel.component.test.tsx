import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { HostStatusPanel } from "../src/components/HostStatusPanel";
import { hostStatusFixture, hostStatusWire } from "./host-fixtures";
import { jsonResponse, problemWire } from "./read-fixtures";
import { App } from "../src/App";
import { uiBootstrapFixture } from "./ui-fixtures";

const original = hostStatusFixture();
afterEach(() => {
    vi.unstubAllGlobals();
});
const scope = createApiScope({
    origin: "http://localhost",
    publicPrefix: "",
    authorityEpoch: "host-panel-1",
    subject: "administrator",
    credentialClass: "rest-writer",
    instanceId: null,
    archiveId: original.binding?.archive_id ?? null,
    configFingerprint: null,
});
function mount(value: unknown = hostStatusWire(), status = 200) {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(value, status));
    const client = createApiClient({ scope, fetcher });
    return {
        ...render(<HostStatusPanel client={client} scope={scope} />),
        client,
        fetcher,
    };
}
test("configuration-only rootless policy displays every denial and fixed unit without action controls", async () => {
    const { fetcher } = mount();
    expect(
        screen.getByRole("heading", { name: "Host administration" }),
    ).toBeInTheDocument();
    await waitFor(() => {
        expect(screen.getByTestId("host-state")).toHaveTextContent("supported");
    });
    expect(
        screen.getByTestId("host-permission-configuration"),
    ).toHaveTextContent("Allowed. Granted by the installed policy.");
    for (const category of ["archive", "hub", "control"])
        expect(
            screen.getByTestId(`host-permission-${category}`),
        ).toHaveTextContent("The installed policy denies this action.");
    for (const category of ["schedule", "observer"])
        expect(
            screen.getByTestId(`host-permission-${category}`),
        ).toHaveTextContent(
            "This deployment profile has not established this authority.",
        );
    expect(screen.getByRole("table")).toHaveAccessibleName(
        "Fixed archive services and timers",
    );
    expect(screen.getByText("hfcache-sync.service")).toBeInTheDocument();
    expect(
        screen.getByText(
            "Schedule observation is unavailable for this deployment profile.",
        ),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(1);
    expect(fetcher).toHaveBeenCalledOnce();
});
test("a helper outage clears authority and gives a visible reason", async () => {
    const unavailable = {
        schema_version: 1,
        state: "unavailable",
        reason: "helper-timeout",
        profile: null,
        binding: null,
        facts: null,
        permissions: {
            archive: false,
            hub: false,
            control: false,
            schedule: false,
            configuration: false,
            observer: false,
        },
        permission_reasons: {
            archive: "helper-unavailable",
            hub: "helper-unavailable",
            control: "helper-unavailable",
            schedule: "helper-unavailable",
            configuration: "helper-unavailable",
            observer: "helper-unavailable",
        },
    };
    mount(hostStatusWire(unavailable));
    await waitFor(() => {
        expect(screen.getByTestId("host-state")).toHaveTextContent(
            "unavailable",
        );
    });
    expect(
        screen.getByText(
            "The protected host helper did not complete within its time limit.",
        ),
    ).toBeInTheDocument();
    expect(
        screen.getByTestId("host-permission-configuration"),
    ).toHaveTextContent("Unavailable.");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
});
test("manual refresh replaces old permissions while retaining a safe refusal code", async () => {
    const { fetcher } = mount();
    await screen.findByTestId("host-state");
    fetcher.mockResolvedValue(jsonResponse(problemWire("HFAPI022", 20), 503));
    await userEvent.click(
        screen.getByRole("button", { name: "Refresh host status" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("HFAPI022");
    expect(
        screen.queryByTestId("host-permission-configuration"),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByText(/Private service detail/),
    ).not.toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(2);
});

test("guarded native status displays the archive denial and an observed schedule as inert text", async () => {
    const calendar = "<svg onload=alert(1)>";
    mount(
        hostStatusWire({
            ...original,
            profile: "native",
            state: "guarded",
            permission_reasons: {
                ...original.permission_reasons,
                archive: "guard-held",
            },
            facts: {
                ...original.facts,
                guard: "held",
                sync_schedule: {
                    state: "observed",
                    reason: null,
                    revision: "e".repeat(64),
                    source: "managed",
                    on_calendar: calendar,
                    randomized_delay_sec: "15m",
                },
            },
        }),
    );
    await waitFor(() => {
        expect(screen.getByTestId("host-state")).toHaveTextContent("guarded");
    });
    expect(screen.getByTestId("host-permission-archive")).toHaveTextContent(
        "Denied. The archive guard blocks archive changes.",
    );
    expect(screen.getByText(calendar)).toBeInTheDocument();
    expect(screen.getByText("15m")).toBeInTheDocument();
    expect(document.querySelector("svg")).toBeNull();
});

test.each([
    {
        value: hostStatusWire({ ...original, schema_version: 2 }),
        status: 200,
        detail: "The host status response could not be validated.",
    },
    {
        value: {
            ...hostStatusWire({}),
            envelope: {
                ...hostStatusWire({}).envelope,
                outcome: "failed",
                exit_code: 20,
                errors: [
                    {
                        code: "HFMNT001",
                        message: "private refusal",
                        context: {},
                        repository: null,
                    },
                ],
            },
        },
        status: 200,
        detail: "The host status read completed with a failed outcome.",
    },
    {
        value: problemWire("HFAPI002", 10),
        status: 403,
        detail: "Access to host status was refused. Diagnostic code: HFAPI002.",
    },
])(
    "a refused host read retains safe failure meaning %#",
    async ({ value, status, detail }) => {
        mount(value, status);
        expect(await screen.findByRole("alert")).toHaveTextContent(detail);
        expect(
            screen.queryByTestId("host-permission-configuration"),
        ).not.toBeInTheDocument();
        expect(screen.queryByText(/private refusal/)).not.toBeInTheDocument();
    },
);

test("network failure gives no partial permissions", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockRejectedValue(new Error("private network data"));
    const client = createApiClient({ scope, fetcher });
    render(<HostStatusPanel client={client} scope={scope} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
        "The connection did not produce a validated host status response.",
    );
    expect(screen.queryByText(/private network data/)).not.toBeInTheDocument();
});
test("unmount aborts the exact owned request and suppresses late results", async () => {
    let signal: AbortSignal | null | undefined;
    let finish: ((response: Response) => void) | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            signal = options?.signal;
            return new Promise<Response>((resolve) => {
                finish = resolve;
            });
        });
    const client = createApiClient({ scope, fetcher });
    const view = render(<HostStatusPanel client={client} scope={scope} />);
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    view.unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () => {
        finish?.(jsonResponse(hostStatusWire()));
        await Promise.resolve();
    });
    expect(screen.queryByTestId("host-state")).not.toBeInTheDocument();
});
test("changing authority hides old facts before the replacement read completes", async () => {
    const { rerender } = mount();
    await screen.findByTestId("host-state");
    const nextScope = createApiScope({
        ...scope,
        authorityEpoch: "host-panel-2",
    });
    const fetcher = vi.fn<typeof fetch>().mockImplementation(
        (_url, options) =>
            new Promise<Response>((_resolve, reject) => {
                options?.signal?.addEventListener("abort", () => {
                    reject(new Error("owned abort"));
                });
            }),
    );
    const client = createApiClient({ scope: nextScope, fetcher });
    rerender(<HostStatusPanel client={client} scope={nextScope} />);
    expect(screen.queryByTestId("host-state")).not.toBeInTheDocument();
    expect(screen.getByText("Loading host status.")).toBeInTheDocument();
});
test("authenticated administration loads through the named client while ungranted users make no helper request", async () => {
    window.history.replaceState(null, "", "/ui/administration");
    const bootstrap = uiBootstrapFixture();
    vi.stubGlobal(
        "location",
        new URL(bootstrap.configured_origin + "/ui/administration"),
    );
    const fetcher = vi.spyOn(globalThis, "fetch").mockResolvedValue(
        jsonResponse({
            ...hostStatusWire(),
            archive_id: bootstrap.configured_archive_id,
            envelope: {
                ...hostStatusWire().envelope,
                data: {
                    ...original,
                    binding: {
                        ...original.binding,
                        archive_id: bootstrap.configured_archive_id,
                    },
                },
            },
        }),
    );
    const view = render(<App basePath="/ui/" bootstrap={bootstrap} />);
    await screen.findByTestId("host-state");
    expect(fetcher).toHaveBeenCalledOnce();
    view.unmount();
    fetcher.mockClear();
    const ungranted = {
        ...bootstrap,
        user: {
            ...bootstrap.user,
            admin_permissions: bootstrap.user.admin_permissions.map(
                (permission) =>
                    permission.capability === "host-read"
                        ? {
                              ...permission,
                              granted: false,
                              effective: false,
                              reason: "not_granted" as const,
                          }
                        : permission,
            ),
        },
    };
    render(<App basePath="/ui/" bootstrap={ungranted} />);
    expect(
        screen.queryByRole("heading", { name: "Host administration" }),
    ).not.toBeInTheDocument();
    expect(fetcher).not.toHaveBeenCalled();
});
