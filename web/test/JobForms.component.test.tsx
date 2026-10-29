/** Real component/store/controller/typed HTTP boundary; responses are owned fixtures. */
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
import { JobForms } from "../src/components/JobForms";
import { createJobsStore } from "../src/operations/jobs-state";
import { createSessionController } from "../src/state/session-controller";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import { operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const cleanups: (() => void)[] = [];
afterEach(() => {
    cleanup();
    for (const dispose of cleanups.splice(0)) dispose();
    window.localStorage.clear();
    vi.restoreAllMocks();
});
const operationId = "a".repeat(32),
    sha = "b".repeat(40);
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
        lost?: boolean;
        denied?: boolean;
        persistenceRefused?: boolean;
    } = {},
) {
    let route = "/api/v1/plans";
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
        const requested = path(input);
        if (init?.method === "POST") {
            if (options.lost)
                return Promise.reject(new TypeError("Owned lost reply"));
            if (options.denied)
                return Promise.resolve(
                    jsonResponse(problemWire("HFAPI010"), 403),
                );
            route = requested;
            const status = "/api/v1/operations/" + operationId;
            return Promise.resolve(
                new Response(
                    JSON.stringify({
                        schema_version: 1,
                        request_id: "f".repeat(32),
                        archive_id: ARCHIVE_ID,
                        config_fingerprint: "2".repeat(64),
                        created: true,
                        operation: receipt({
                            route,
                            state: "queued",
                            domain_run_id: null,
                        }),
                        links: {
                            status,
                            result: status + "/result",
                            events: status + "/events",
                        },
                    }),
                    {
                        status: 202,
                        headers: {
                            "Content-Type": "application/json",
                            Location: status,
                        },
                    },
                ),
            );
        }
        if (requested.endsWith("/events"))
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations events", {
                        operation_id: operationId,
                        events: [],
                        next_cursor: 0,
                        oldest_sequence: 1,
                        truncated: false,
                    }),
                ),
            );
        if (requested === "/api/v1/operations/" + operationId)
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations show", {
                        operation: receipt({
                            route,
                            state: "interrupted",
                            completed_at: "2026-10-20T12:00:02.000000Z",
                            updated_at: "2026-10-20T12:00:02.000000Z",
                            domain_run_id: null,
                        }),
                    }),
                ),
            );
        if (requested === "/api/v1/verification/estimate")
            return Promise.resolve(
                jsonResponse(
                    operationResponse("verify --estimate", {
                        mode: "estimate",
                        repositories: 2,
                        revisions: 3,
                        unique_bytes: 13,
                        unique_objects: 1,
                        unreadable_objects: 0,
                        estimated_duration_seconds: null,
                        measured_throughput_bytes_per_second: null,
                        storage_maintenance: "undetectable",
                    }),
                ),
            );
        return Promise.resolve(jsonResponse(problemWire(), 404));
    });
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: window.location.origin,
        configured_archive_id: ARCHIVE_ID,
    };
    const controller = createSessionController({
        bootstrap,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
        storage: {
            getItem: (key) => window.localStorage.getItem(key),
            setItem: (key, value) => {
                if (options.persistenceRefused)
                    throw new Error("Owned quota refusal");
                window.localStorage.setItem(key, value);
            },
        },
    });
    const store = createJobsStore(controller),
        onOpenConfiguration = vi.fn();
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    const view = render(
        <JobForms store={store} onOpenConfiguration={onOpenConfiguration} />,
    );
    return {
        store,
        controller,
        fetcher,
        view,
        onOpenConfiguration,
        posts: () =>
            fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
    };
}
async function choose(label: string) {
    await userEvent.click(screen.getByRole("button", { name: /^Job: /u }));
    await userEvent.click(
        within(screen.getByRole("listbox", { name: "Job" })).getByRole(
            "option",
            { name: label },
        ),
    );
}
async function submit(fixture: ReturnType<typeof mounted>) {
    await userEvent.click(screen.getByRole("button", { name: "Submit job" }));
    await waitFor(() => {
        expect(fixture.posts()).toHaveLength(1);
    });
    const body = fixture.posts()[0]?.[1]?.body;
    if (typeof body !== "string") throw new Error("Missing owned request body");
    const value: unknown = JSON.parse(body);
    return value;
}

test("mount and local action/scope choices are read-free, CSP-safe and expose exact effects", async () => {
    const fixture = mounted();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(screen.getByRole("region", { name: "Jobs" })).toBeInTheDocument();
    const effects = screen.getByRole("group", {
        name: "Selected job effects",
    });
    expect(document.querySelector("select")).toBeNull();
    expect(
        screen.queryByRole("button", { name: /cancel/iu }),
    ).not.toBeInTheDocument();
    await choose("Candidate file sizing");
    expect(
        screen.getByRole("radio", {
            name: "All candidate repositories",
        }),
    ).toBeChecked();
    expect(
        within(effects).getByText(
            /Syntax validity does not prove authority compatibility/u,
        ),
    ).toBeInTheDocument();
    await choose("Refresh offline metadata");
    expect(
        screen.getByRole("radio", {
            name: "All configured and archived repositories",
        }),
    ).toBeChecked();
    expect(fixture.fetcher).not.toHaveBeenCalled();
});

test.each(["Installed sizing", "Sync"])(
    "%s selected scope submits one exact canonical request and admission stays distinct from completion",
    async (label) => {
        const fixture = mounted();
        await choose(label);
        await userEvent.click(
            screen.getByRole("radio", {
                name: "Selected repositories",
            }),
        );
        expect(
            screen.getByRole("button", { name: "Submit job" }),
        ).toBeDisabled();
        await userEvent.type(
            screen.getByLabelText("Repository selectors (one per line)"),
            "model:owned/model\ndataset:owned/data\nmodel:owned/model",
        );
        expect(await submit(fixture)).toEqual({
            selectors: ["dataset:owned/data", "model:owned/model"],
        });
        await screen.findByText(/202 admitted/u);
        expect(
            screen.getByText(new RegExp("^Action: " + label + "\\.", "u")),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/This is not domain completion/u),
        ).toBeInTheDocument();
        expect(fixture.posts()[0]?.[1]?.headers).toBeDefined();
        expect(
            new Headers(fixture.posts()[0]?.[1]?.headers).get(
                "Idempotency-Key",
            ),
        ).toMatch(/^[A-Za-z0-9._~+-]+$/u);
        await waitFor(() => {
            expect(
                screen.getByRole("button", { name: "Submit job" }),
            ).toBeDisabled();
        });
    },
);

test.each([
    ["New publications", { mode: "new", run_id: "c".repeat(32) }],
    ["All retained publications", { mode: "full" }],
    [
        "Exact revision",
        { mode: "revision", revision: "dataset:owned/data@" + sha },
    ],
])(
    "verification %s uses only the existing offline scope DTO",
    async (label, expected) => {
        const fixture = mounted();
        await choose("Verification");
        await userEvent.click(screen.getByRole("radio", { name: label }));
        if (label === "New publications")
            await userEvent.type(
                screen.getByLabelText("Original sync run ID (optional)"),
                "c".repeat(32),
            );
        if (label === "Exact revision")
            await userEvent.type(
                screen.getByLabelText(
                    "Exact revision (TYPE:namespace/name@SHA)",
                ),
                "dataset:owned/data@" + sha,
            );
        expect(await submit(fixture)).toEqual(expected);
        expect(
            screen.getByText(/No Hub contact, repair or pruning/u),
        ).toBeInTheDocument();
    },
);

test.each([
    ["Read-only checks", true],
    ["Temporary archive probes", false],
] as const)(
    "diagnostics %s sends explicit read_only=%s and preserves its effects",
    async (label, readOnly) => {
        const fixture = mounted();
        await choose("Diagnostics");
        await userEvent.click(screen.getByRole("radio", { name: label }));
        expect(await submit(fixture)).toEqual({ read_only: readOnly });
        expect(
            screen.getByText(
                readOnly
                    ? /skips archive-write probes/u
                    : /temporary archive health probes/u,
            ),
        ).toBeInTheDocument();
    },
);

test("refresh retains the explicit metadata flags and rejects an empty category selection", async () => {
    const fixture = mounted();
    await choose("Refresh offline metadata");
    await userEvent.click(
        screen.getByRole("checkbox", {
            name: "Refresh configured tags",
        }),
    );
    await userEvent.click(
        screen.getByRole("checkbox", {
            name: "Refresh technical metadata",
        }),
    );
    expect(screen.getByRole("button", { name: "Submit job" })).toBeDisabled();
    await userEvent.click(
        screen.getByRole("checkbox", {
            name: "Refresh technical metadata",
        }),
    );
    await userEvent.click(
        screen.getByRole("radio", {
            name: "Retained publications",
        }),
    );
    expect(await submit(fixture)).toEqual({
        selectors: [],
        revision_scope: "retained",
        tags: false,
        technical: true,
    });
});

test("candidate file selection is read-free, never exposes contents or persists them, and submits only on explicit action", async () => {
    const fixture = mounted();
    await choose("Candidate file sizing");
    const secret = "hf_OWNED_CANDIDATE_SECRET_NEVER_RENDER",
        body = "# " + secret + "\n";
    const input = screen.getByLabelText("Candidate TOML file for sizing");
    await userEvent.upload(
        input,
        new File([body], "candidate<owned>.toml", { type: "application/toml" }),
    );
    await screen.findByText("candidate<owned>.toml", { selector: "code" });
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(document.body.textContent).not.toContain(secret);
    expect(window.localStorage.getItem("hfcache.web.operations.v1")).toBeNull();
    expect(await submit(fixture)).toEqual({ selectors: [], candidate: body });
    expect(
        window.localStorage.getItem("hfcache.web.operations.v1"),
    ).not.toContain(secret);
    expect(document.body.textContent).not.toContain(secret);
});

test.each([
    [
        "invalid UTF-8",
        new File([new Uint8Array([0xff])], "invalid.toml"),
        /not strict UTF-8/u,
    ],
    [
        "oversize",
        new File(["x".repeat(1048577)], "large.toml"),
        /supported file/u,
    ],
])(
    "candidate %s is safely refused before any network request",
    async (_name, file, message) => {
        const fixture = mounted();
        await choose("Candidate file sizing");
        await userEvent.upload(
            screen.getByLabelText("Candidate TOML file for sizing"),
            file,
        );
        await screen.findByRole("alert");
        expect(screen.getByRole("alert")).toHaveTextContent(message);
        expect(
            screen.getByRole("button", { name: "Submit job" }),
        ).toBeDisabled();
        expect(fixture.fetcher).not.toHaveBeenCalled();
    },
);

test("managed draft sizing opens only the explicit configuration callback without an automatic read or POST", async () => {
    const fixture = mounted();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Plan configuration draft",
        }),
    );
    expect(fixture.onOpenConfiguration).toHaveBeenCalledOnce();
    expect(fixture.fetcher).not.toHaveBeenCalled();
});

test("estimate is one real typed GET, keeps unknown throughput explicit and creates no job", async () => {
    const fixture = mounted();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Read verification estimate",
        }),
    );
    const estimate = screen.getByRole("region", {
        name: "Verification estimate",
    });
    await within(estimate).findByText("Undetectable; no safety inference.");
    expect(within(estimate).getAllByText("Unknown")).toHaveLength(2);
    expect(fixture.posts()).toEqual([]);
    expect(fixture.fetcher).toHaveBeenCalledOnce();
    expect(window.localStorage.getItem("hfcache.web.operations.v1")).toBeNull();
});

test("unmount preserves one RAM form across routes, while auth clearing removes it and the file metadata", async () => {
    const fixture = mounted();
    await choose("Candidate file sizing");
    await userEvent.upload(
        screen.getByLabelText("Candidate TOML file for sizing"),
        new File(["# private\n"], "owned.toml"),
    );
    await screen.findByText("owned.toml", { selector: "code" });
    fixture.view.unmount();
    render(<JobForms store={fixture.store} />);
    expect(
        screen.getByText("owned.toml", { selector: "code" }),
    ).toBeInTheDocument();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    act(() => {
        fixture.controller.disconnect();
    });
    expect(
        screen.queryByText("owned.toml", { selector: "code" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit job" })).toBeDisabled();
});

test.each([{ lost: true }, { denied: true }, { persistenceRefused: true }])(
    "admission failure %j preserves classification and has no retry or cancellation control",
    async (options) => {
        const fixture = mounted(options);
        await userEvent.click(
            screen.getByRole("button", { name: "Submit job" }),
        );
        await waitFor(() => {
            expect(fixture.store.snapshot().pending).toBeNull();
        });
        expect(fixture.posts()).toHaveLength(
            options.persistenceRefused === true ? 0 : 1,
        );
        if (options.lost)
            expect(
                screen.getByText(/Admission is uncertain/u),
            ).toBeInTheDocument();
        if (options.denied)
            expect(screen.getByText(/HFAPI010/u)).toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: /cancel/iu }),
        ).not.toBeInTheDocument();
    },
);
