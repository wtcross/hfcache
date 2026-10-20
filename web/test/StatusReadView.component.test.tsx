import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { createApiClient } from "../src/api/client";
import { createApiScope } from "../src/api/identity";
import { StatusReadView } from "../src/components/StatusReadView";
import type { ReadSource } from "../src/components/StatusReadView";
import { decodeNamed } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import {
    capabilitiesPayload,
    inspectionPayload,
    jsonResponse,
    problemWire,
    readWire,
    REQUEST_ID,
    statusPayload,
    versionPayload,
} from "./read-fixtures";

const scope = createApiScope({
    origin: "http://localhost",
    publicPrefix: "",
    authorityEpoch: "component-reader-1",
    subject: "component-reader",
    credentialClass: "rest-reader",
    instanceId: null,
    archiveId: null,
    configFingerprint: null,
});
test("independent status and inspection literal helpers satisfy generated source shapes", () => {
    expect(
        decodeNamed(
            "StatusPayload",
            parseWireJson(JSON.stringify(statusPayload(false))),
        ),
    ).toEqual(statusPayload(false));
    expect(
        decodeNamed(
            "StatusPayload",
            parseWireJson(JSON.stringify(statusPayload(true))),
        ),
    ).toEqual(statusPayload(true));
    expect(
        decodeNamed(
            "InspectionPayload",
            parseWireJson(JSON.stringify(inspectionPayload)),
        ),
    ).toEqual(inspectionPayload);
});
function mount(value: unknown, source: ReadSource = "version", status = 200) {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation(() => Promise.resolve(jsonResponse(value, status)));
    const client = createApiClient({ scope, fetcher });
    const view = render(
        <StatusReadView client={client} scope={scope} source={source} />,
    );
    return { ...view, client, fetcher };
}

test.each([
    {
        source: "version" as const,
        command: "version",
        payload: versionPayload,
        title: "Server version",
        detail: "Application independent-version.",
    },
    {
        source: "capabilities" as const,
        command: "capabilities",
        payload: capabilitiesPayload,
        title: "Server capabilities",
        detail: "Maintenance disabled.",
    },
    {
        source: "capabilities" as const,
        command: "capabilities",
        payload: { ...capabilitiesPayload, maintenance_enabled: true },
        title: "Server capabilities",
        detail: "Maintenance enabled.",
    },
    {
        source: "status" as const,
        command: "status",
        payload: statusPayload(false),
        title: "Server status",
        detail: "0 loaded repositories. Archive unavailable.",
    },
    {
        source: "status" as const,
        command: "status",
        payload: statusPayload(true),
        title: "Server status",
        detail: "0 loaded repositories. Archive reachable.",
    },
    {
        source: "inspection" as const,
        command: "archive init",
        payload: inspectionPayload,
        title: "Archive inspection",
        detail: "The archive inspection completed successfully.",
    },
])(
    "actual typed $source read presents validated facts: $detail",
    async ({ source, command, payload, title, detail }) => {
        const { fetcher } = mount(readWire(command, payload), source);
        expect(
            await screen.findByRole("heading", { name: title }),
        ).toBeInTheDocument();
        expect(screen.getByRole("status")).toHaveTextContent(detail);
        expect(screen.getByTestId("read-request-id")).toHaveTextContent(
            REQUEST_ID,
        );
        expect(fetcher).toHaveBeenCalledOnce();
    },
);

test("genuine domain classification preserves codes without rendering private messages or inferring success", async () => {
    mount(readWire("archive init", inspectionPayload, true), "inspection");
    expect(
        await screen.findByRole("heading", { name: "Read failed" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("HFMNT001");
    expect(screen.getByTestId("read-request-id")).toHaveTextContent(REQUEST_ID);
    expect(
        screen.queryByText(/Private original detail/u),
    ).not.toBeInTheDocument();
});

test.each([401, 403, 503])(
    "HTTP %s displays API refusal separately from completed domain failure",
    async (status) => {
        mount(problemWire(), "version", status);
        expect(
            await screen.findByRole("heading", {
                name: status === 503 ? "API unavailable" : "Access refused",
            }),
        ).toBeInTheDocument();
        expect(screen.getByRole("alert")).toHaveTextContent("HFAPI001");
        expect(document.querySelector("script")).toBeNull();
        expect(
            screen.queryByText(/Private service detail/u),
        ).not.toBeInTheDocument();
    },
);

test("unsupported wire never presents a known version as a validated server fact", async () => {
    mount({ ...readWire("version", versionPayload), schema_version: 2 });
    expect(
        await screen.findByRole("heading", { name: "Unsupported response" }),
    ).toBeInTheDocument();
    expect(
        screen.queryByText("Application independent-version."),
    ).not.toBeInTheDocument();
});

test("unsupported failed payload still presents validated original diagnostic evidence", async () => {
    mount(readWire("version", { fictional_count: 999 }, true));
    expect(
        await screen.findByRole("heading", { name: "Unsupported response" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("HFMNT001");
    expect(screen.getByTestId("read-request-id")).toHaveTextContent(REQUEST_ID);
    expect(screen.queryByText(/999/u)).not.toBeInTheDocument();
});

test("a successful read preserves original warnings without presenting a failed outcome", async () => {
    const wire = readWire("version", versionPayload);
    mount({
        ...wire,
        envelope: {
            ...wire.envelope,
            outcome: "success_with_warnings",
            warnings: [
                {
                    code: "HFWRN999",
                    context: {},
                    message: "private warning detail",
                    repository: null,
                },
            ],
        },
    });
    expect(
        await screen.findByRole("heading", { name: "Server version" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("HFWRN999");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(
        screen.queryByText("private warning detail"),
    ).not.toBeInTheDocument();
});

test("a failed read preserves warning codes alongside the original errors", async () => {
    const wire = readWire("version", {}, true);
    mount({
        ...wire,
        envelope: {
            ...wire.envelope,
            warnings: [
                {
                    code: "HFWRN998",
                    context: {},
                    message: "private warning detail",
                    repository: null,
                },
            ],
        },
    });
    expect(
        await screen.findByRole("heading", { name: "Read failed" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("HFWRN998");
    expect(screen.getByRole("alert")).toHaveTextContent("HFMNT001");
});

test("manual refresh issues exactly one additional GET and disables the action while loading", async () => {
    const { fetcher } = mount(readWire("version", versionPayload));
    expect(screen.getByRole("button", { name: "Refresh read" })).toBeDisabled();
    await screen.findByRole("heading", { name: "Server version" });
    await userEvent.click(screen.getByRole("button", { name: "Refresh read" }));
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    await screen.findByRole("heading", { name: "Server version" });
    for (const [, options] of fetcher.mock.calls)
        expect(options?.method).toBe("GET");
});

test("network rejection is unavailable, and no automatic retry occurs", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockRejectedValue(new Error("private network detail"));
    render(
        <StatusReadView
            client={createApiClient({ scope, fetcher })}
            scope={scope}
            source="version"
        />,
    );
    expect(
        await screen.findByRole("heading", { name: "Connection unavailable" }),
    ).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledOnce();
    expect(
        screen.queryByText("private network detail"),
    ).not.toBeInTheDocument();
});

test("an explicitly aborted client result remains unknown instead of displaying failure or success", async () => {
    const client = createApiClient({ scope });
    vi.spyOn(client, "readVersion").mockResolvedValue({ kind: "aborted" });
    render(<StatusReadView client={client} scope={scope} source="version" />);
    expect(
        await screen.findByRole("heading", { name: "Read unavailable" }),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("an unexpected rejected client promise has a safe unavailable boundary", async () => {
    const client = createApiClient({ scope });
    vi.spyOn(client, "readVersion").mockRejectedValue(
        new Error("never expose exception"),
    );
    render(<StatusReadView client={client} scope={scope} source="version" />);
    expect(
        await screen.findByRole("heading", { name: "Connection unavailable" }),
    ).toBeInTheDocument();
    expect(
        screen.queryByText("never expose exception"),
    ).not.toBeInTheDocument();
});

test("changing authority masks earlier facts immediately, aborts the old read and ignores late completion", async () => {
    let late: ((value: Response) => void) | undefined;
    let oldSignal: AbortSignal | null | undefined;
    const oldFetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((_url, options) => {
            oldSignal = options?.signal;
            return new Promise((resolve) => {
                late = resolve;
            });
        });
    const oldClient = createApiClient({ scope, fetcher: oldFetcher });
    const view = render(
        <StatusReadView client={oldClient} scope={scope} source="version" />,
    );
    const nextScope = createApiScope({
        ...scope,
        authorityEpoch: "component-reader-2",
    });
    const nextClient = createApiClient({
        scope: nextScope,
        fetcher: vi.fn<typeof fetch>().mockResolvedValue(
            jsonResponse(
                readWire("version", {
                    ...versionPayload,
                    application: "new-authority",
                }),
            ),
        ),
    });
    view.rerender(
        <StatusReadView
            client={nextClient}
            scope={nextScope}
            source="version"
        />,
    );
    expect(oldSignal?.aborted).toBe(true);
    expect(
        await screen.findByText("Application new-authority."),
    ).toBeInTheDocument();
    act(() => {
        late?.(jsonResponse(readWire("version", versionPayload)));
    });
    expect(
        screen.queryByText("Application independent-version."),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Application new-authority.")).toBeInTheDocument();
    view.unmount();
});

test("changing scope clears already displayed facts while the new authority remains loading", async () => {
    const { rerender, client } = mount(readWire("version", versionPayload));
    await screen.findByText("Application independent-version.");
    const nextScope = createApiScope({
        ...scope,
        subject: "different-subject",
    });
    vi.spyOn(client, "readVersion").mockImplementation(
        () => new Promise(() => {}),
    );
    rerender(
        <StatusReadView client={client} scope={nextScope} source="version" />,
    );
    expect(
        screen.queryByText("Application independent-version."),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("heading", { name: "Loading server information" }),
    ).toBeInTheDocument();
});
