import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { mountApplication } from "../src/mount";
import { OPERATION_STORAGE_KEY } from "../src/state/operation-registry";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import {
    deferred,
    OPERATION_ID,
    operationResponse,
    terminal,
} from "./state-fixtures";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";

let unmount = () => {};
afterEach(() => {
    act(unmount);
    unmount = () => {};
    localStorage.clear();
    document.head.innerHTML = "";
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
});
function mount(fetcher: typeof fetch, initialHidden = false) {
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal(
        "location",
        new URL(bootstrap.configured_origin + "/ui/operations"),
    );
    window.history.replaceState(null, "", "/ui/operations");
    let hidden = initialHidden;
    vi.spyOn(document, "hidden", "get").mockImplementation(() => hidden);
    const added = vi.spyOn(document, "addEventListener"),
        removed = vi.spyOn(document, "removeEventListener");
    inertUiDocument(document);
    act(() => {
        unmount = mountApplication(document, bootstrap, fetcher);
    });
    return {
        added,
        removed,
        setHidden(value: boolean) {
            hidden = value;
            act(() => {
                document.dispatchEvent(new Event("visibilitychange"));
            });
        },
    };
}
async function importAndObserve() {
    await userEvent.type(
        screen.getByRole("textbox", { name: "Original handle" }),
        OPERATION_ID,
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Save original handle" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Recheck original request" }),
    );
}
test("mounted document visibility aborts original observation, fences late response, and disposes its listener", async () => {
    const late = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementation((input, options) => {
            if (
                (input instanceof URL ? input.pathname : "") ===
                "/api/v1/jobs/readiness"
            )
                return Promise.resolve(
                    jsonResponse(problemWire("HFAPI013", 20), 404),
                );
            if (signal === undefined) {
                signal = options?.signal;
                return late.promise;
            }
            return Promise.resolve(
                jsonResponse(problemWire("HFAPI013", 20), 404),
            );
        });
    const view = mount(fetcher);
    await importAndObserve();
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    const saved = localStorage.getItem(OPERATION_STORAGE_KEY);
    expect(saved).toContain(OPERATION_ID);
    view.setHidden(true);
    expect(signal?.aborted).toBe(true);
    expect(screen.getByText("paused · hidden")).toBeInTheDocument();
    view.setHidden(false);
    await act(async () => {
        late.resolve(
            jsonResponse(
                operationResponse("operations show", { operation: terminal() }),
            ),
        );
        await late.promise;
    });
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(4);
    });
    await screen.findByText(/history missing/u);
    const after: unknown = JSON.parse(
        localStorage.getItem(OPERATION_STORAGE_KEY) ?? "null",
    );
    expect(JSON.stringify(after)).toContain(OPERATION_ID);
    expect(saved).toContain(OPERATION_ID);
    await userEvent.click(
        screen.getByRole("button", { name: "Recheck original request" }),
    );
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(5);
    });
    expect(
        fetcher.mock.calls.every(([, options]) => options?.method === "GET"),
    ).toBe(true);
    const handler = view.added.mock.calls.find(
        ([name]) => name === "visibilitychange",
    )?.[1];
    expect(handler).toBeDefined();
    act(unmount);
    unmount = () => {};
    expect(view.removed).toHaveBeenCalledWith("visibilitychange", handler);
});
test("an initially hidden mounted page reconciles saved originals using GETs after visibility returns", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
    const view = mount(fetcher, true);
    await importAndObserve();
    expect(fetcher).not.toHaveBeenCalled();
    view.setHidden(false);
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});
