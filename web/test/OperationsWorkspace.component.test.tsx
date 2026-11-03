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
import { OperationsWorkspace } from "../src/components/OperationsWorkspace";
import { createHistoryStore } from "../src/operations/history-state";
import { createJobsStore } from "../src/operations/jobs-state";
import { createSessionController } from "../src/state/session-controller";
import { uiBootstrapFixture } from "./ui-fixtures";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import {
    events,
    operationResponse,
    OPERATION_ID,
    receipt,
    resultResponse,
    terminal,
} from "./state-fixtures";
import report from "../../tests/fixtures/schemas/run-report.json";
import { hostStatusFixture, hostStatusWire } from "./host-fixtures";

const cleanupStores: (() => void)[] = [];
afterEach(() => {
    cleanup();
    cleanupStores
        .splice(0)
        .reverse()
        .forEach((dispose) => {
            dispose();
        });
    window.localStorage.clear();
    vi.unstubAllGlobals();
});
function mount(router: (url: URL, init?: RequestInit) => Response) {
    window.localStorage.clear();
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal(
        "location",
        new URL(bootstrap.configured_origin + "/ui/operations"),
    );
    const fetcher = vi.fn<typeof fetch>((input, init) =>
        Promise.resolve(
            new URL(input instanceof Request ? input.url : input).pathname ===
                "/api/v1/jobs/readiness"
                ? jsonResponse({
                      schema_version: 1,
                      archive_id: ARCHIVE_ID,
                      config_fingerprint: null,
                      archive: null,
                      hub: null,
                      control: null,
                      archive_writable: null,
                      verification_available: null,
                  })
                : router(
                      new URL(input instanceof Request ? input.url : input),
                      init,
                  ),
        ),
    );
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: window.localStorage,
        reconnect: () => Promise.resolve(bootstrap),
    });
    const history = createHistoryStore(controller),
        jobs = createJobsStore(controller);
    const openConfiguration = vi.fn();
    cleanupStores.push(() => {
        history.dispose();
        jobs.dispose();
        controller.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            controller.subscribe,
            controller.snapshot,
        );
        return (
            <OperationsWorkspace
                controller={controller}
                session={session}
                history={history}
                jobs={jobs}
                onOpenConfiguration={openConfiguration}
            />
        );
    }
    return {
        controller,
        history,
        jobs,
        fetcher,
        openConfiguration,
        ...render(<Connected />),
    };
}
function historyPage(url: URL) {
    return jsonResponse(
        operationResponse(
            url.pathname.endsWith("/runs") ? "runs" : "operations list",
            url.pathname.endsWith("/runs")
                ? { runs: [report.run_id] }
                : { operations: [terminal()] },
        ),
    );
}

test("workspace starts read-free, explicitly lists bounded histories and never imports selected IDs as owned keys", async () => {
    const { fetcher, controller } = mount(historyPage);
    expect(fetcher).not.toHaveBeenCalled();
    expect(
        screen.getByText(/HTTP 202 acknowledges admission/),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: /^Cancel/ }),
    ).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Read history" }));
    expect(
        await screen.findByRole("button", {
            name: `Inspect operation ${OPERATION_ID}`,
        }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("button", {
            name: `Read run report ${report.run_id}`,
        }),
    ).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(3);
    expect(
        screen.getByText(/1 operation receipts in the known loaded extent/),
    ).toBeInTheDocument();
    expect(controller.snapshot().registry.records).toEqual([]);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});

test("job permission evidence is an explicit shared GET and preserves effective denied reasons", async () => {
    const original = hostStatusFixture();
    const value = {
        ...original,
        binding: { ...original.binding, archive_id: ARCHIVE_ID },
    };
    const { fetcher, controller } = mount(() =>
        jsonResponse({ ...hostStatusWire(value), archive_id: ARCHIVE_ID }),
    );
    expect(fetcher).not.toHaveBeenCalled();
    await userEvent.click(
        screen.getByRole("button", { name: "Read job permission evidence" }),
    );
    await waitFor(() => {
        expect(screen.getByTestId("host-permission-archive")).toHaveTextContent(
            "The installed policy denies this action.",
        );
    });
    expect(screen.getByTestId("host-permission-hub")).toHaveTextContent(
        "The installed policy denies this action.",
    );
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(fetcher.mock.calls[0]?.[1]?.method).toBe("GET");
    expect(controller.snapshot().registry.records).toEqual([]);
});

test("exact selected operation presents original result separately from events and report identity", async () => {
    const { fetcher, controller } = mount((url) => {
        if (url.pathname.endsWith("/result"))
            return jsonResponse(resultResponse());
        if (url.pathname.endsWith("/events"))
            return jsonResponse(
                operationResponse("operations events", events([])),
            );
        if (url.pathname.endsWith(OPERATION_ID))
            return jsonResponse(
                operationResponse("operations show", { operation: terminal() }),
            );
        return historyPage(url);
    });
    await userEvent.click(screen.getByRole("button", { name: "Read history" }));
    await userEvent.click(
        await screen.findByRole("button", {
            name: `Inspect operation ${OPERATION_ID}`,
        }),
    );
    const result = await screen.findByRole("region", {
        name: "Original operation result",
    });
    await waitFor(() => {
        expect(within(result).getByText("catalog refresh")).toBeInTheDocument();
    });
    expect(
        screen.getByText(/Events are diagnostic evidence/),
    ).toBeInTheDocument();
    expect(screen.getByText(/does not prove ownership/)).toBeInTheDocument();
    expect(controller.snapshot().registry.records).toEqual([]);
    expect(fetcher).toHaveBeenCalledTimes(6);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});

test("a run selected from a repository can open directly without an implicit history walk", async () => {
    const { history, fetcher } = mount(() =>
        jsonResponse({
            ...operationResponse("runs read", { report }),
            config_fingerprint: "2".repeat(64),
            envelope: {
                ...operationResponse("runs read", { report }).envelope,
                run_id: report.run_id,
            },
        }),
    );
    await act(async () => {
        await history.selectRun(report.run_id);
    });
    expect(
        await screen.findByRole("article", { name: "Run report" }),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/Historical report policy may differ/),
    ).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledTimes(2);
    const request = fetcher.mock.calls[1]?.[0];
    expect(request instanceof URL ? request.pathname : null).toBe(
        `/api/v1/runs/${report.run_id}`,
    );
});

test("missing history keeps its diagnostic and uncertainty visible", async () => {
    const { history, controller } = mount(() =>
        jsonResponse(problemWire("HFAPI019", 20), 404),
    );
    await act(async () => {
        await history.selectOperation(OPERATION_ID);
    });
    expect(
        screen.getByText(/Missing or expired history does not prove/),
    ).toBeInTheDocument();
    expect(screen.getByText(/HFAPI019/)).toBeInTheDocument();
    expect(controller.snapshot().registry.records).toEqual([]);
});

test("leaving a mounted workspace invalidates private reads without removing saved original handles", async () => {
    const { controller, history, unmount, fetcher } = mount(historyPage);
    act(() => {
        controller.importHandle({
            kind: "id",
            operationId: receipt().operation_id,
        });
    });
    await act(async () => {
        await history.refresh();
    });
    expect(history.snapshot().operations.phase).toBe("ready");
    unmount();
    expect(history.snapshot().selectedOperationId).toBeNull();
    expect(history.snapshot().operations.result).toBeNull();
    expect(controller.snapshot().registry.records).toHaveLength(1);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});
