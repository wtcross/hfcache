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
        screen.getByRole("button", { name: "Observe original operation" }),
    );
}
test("mounted document visibility aborts original observation, fences late response, and disposes its listener", async () => {
    const late = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const fetcher = vi
        .fn<typeof fetch>()
        .mockImplementationOnce((_input, options) => {
            signal = options?.signal;
            return late.promise;
        })
        .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
    const view = mount(fetcher);
    await importAndObserve();
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
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
    expect(fetcher).toHaveBeenCalledOnce();
    expect(screen.getByText("paused · hidden")).toBeInTheDocument();
    expect(localStorage.getItem(OPERATION_STORAGE_KEY)).toBe(saved);
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original operation" }),
    );
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
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
test("an initially hidden mounted page requires explicit Observe after visibility returns", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire("HFAPI013", 20), 404));
    const view = mount(fetcher, true);
    await importAndObserve();
    expect(fetcher).not.toHaveBeenCalled();
    expect(screen.getByText("paused · hidden")).toBeInTheDocument();
    view.setHidden(false);
    await Promise.resolve();
    expect(fetcher).not.toHaveBeenCalled();
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original operation" }),
    );
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
});
