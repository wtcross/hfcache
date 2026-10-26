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
import { App } from "../src/App";
import { InterfaceUpdateRequiredError } from "../src/bootstrap";
import type { UiBootstrap } from "../src/wire/generated";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import { jsonResponse, problemWire } from "./read-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const controllers: SessionController[] = [];
afterEach(() => {
    cleanup();
    for (const controller of controllers.splice(0)) controller.dispose();
    vi.unstubAllGlobals();
});
function mount(
    fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire(), 404)),
    storage: Storage | null = window.localStorage,
    reconnect?: () => Promise<UiBootstrap>,
) {
    storage?.clear();
    const bootstrap = uiBootstrapFixture();
    const documentLocation = document.location;
    const location = new URL(bootstrap.configured_origin + "/ui/operations");
    Object.defineProperty(location, "pathname", {
        get: () => documentLocation.pathname,
    });
    vi.stubGlobal("location", location);
    window.history.replaceState(null, "", "/ui/operations");
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage,
        reconnect: reconnect ?? (() => Promise.resolve(bootstrap)),
    });
    controllers.push(controller);
    function Connected() {
        const session = useSyncExternalStore(
            controller.subscribe,
            controller.snapshot,
        );
        return (
            <App
                basePath="/ui/"
                bootstrap={session.bootstrap}
                controller={controller}
                session={session}
            />
        );
    }
    return { controller, fetcher, ...render(<Connected />) };
}
async function importId(id = "a".repeat(32)) {
    await userEvent.type(
        screen.getByRole("textbox", { name: "Original handle" }),
        id,
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Save original handle" }),
    );
}
test("manual ID is saved without a request, survives route remount, and observes only on explicit action", async () => {
    const { controller, fetcher } = mount();
    await importId();
    expect(fetcher).not.toHaveBeenCalled();
    expect(screen.getByText(/Creator unknown/)).toBeInTheDocument();
    expect(controller.snapshot().registry.records).toHaveLength(1);
    await userEvent.click(screen.getByRole("link", { name: "Library" }));
    await userEvent.click(screen.getByRole("link", { name: "Operations" }));
    expect(fetcher).not.toHaveBeenCalled();
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original operation" }),
    );
    await waitFor(() => {
        expect(screen.getByText(/history missing/)).toBeInTheDocument();
    });
    expect(fetcher).toHaveBeenCalledTimes(1);
    const target = fetcher.mock.calls[0]?.[0];
    expect(target).toBeInstanceOf(URL);
    expect(target instanceof URL ? target.href : null).toBe(
        "https://archive.invalid/api/v1/operations/" + "a".repeat(32),
    );
    expect(fetcher.mock.calls[0]?.[1]?.method).toBe("GET");
    expect(controller.snapshot().registry.records[0]?.handles.operationId).toBe(
        "a".repeat(32),
    );
    expect(screen.getByText(/Outcome is unconfirmed/)).toBeInTheDocument();
});
test("stopping observation aborts GET and preserves the imported handle without cancellation or POST", async () => {
    let signal: AbortSignal | null | undefined;
    const fetcher = vi.fn<typeof fetch>((_url, init) => {
        signal = init?.signal;
        return new Promise((_resolve, reject) => {
            signal?.addEventListener(
                "abort",
                () => {
                    reject(new DOMException("aborted", "AbortError"));
                },
                { once: true },
            );
        });
    });
    const { controller } = mount(fetcher);
    await importId();
    await userEvent.click(
        screen.getByRole("button", { name: "Observe original operation" }),
    );
    await waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Stop observing in this browser" }),
    );
    await waitFor(() => {
        expect(screen.getByText("paused · user")).toBeInTheDocument();
    });
    expect(signal?.aborted).toBe(true);
    expect(controller.snapshot().registry.records).toHaveLength(1);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});
test("legacy bearer-key reference is preserved separately and cannot be converted by the Basic session", async () => {
    const { controller, fetcher } = mount();
    await userEvent.click(
        screen.getByRole("radio", { name: "Legacy Cockpit key reference" }),
    );
    await userEvent.type(
        screen.getByRole("textbox", { name: "Original handle" }),
        "legacy-original-key",
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Save original handle" }),
    );
    const entry = screen.getByRole("article");
    await userEvent.click(
        within(entry).getByRole("button", {
            name: "Observe original operation",
        }),
    );
    expect(
        within(entry).getByText(/Observation is unavailable/),
    ).toBeInTheDocument();
    expect(controller.snapshot().registry.records[0]?.handles).toEqual({
        kind: "imported",
        operationId: null,
        legacyKey: {
            value: "legacy-original-key",
            credentialClass: "rest-writer",
        },
    });
    expect(fetcher).not.toHaveBeenCalled();
});
test("native radio groups support keyboard mode changes while preserving typed and saved original handles", async () => {
    const { controller, fetcher } = mount();
    await importId();
    const saved = controller.snapshot().registry.records[0];
    const original = screen.getByRole("textbox", { name: "Original handle" });
    const user = userEvent.setup();
    await user.type(original, "legacy-reader-key");
    const handleChoices = screen.getByRole("group", { name: "Handle type" });
    const idChoice = within(handleChoices).getByRole("radio", {
        name: "Original operation ID",
    });
    expect(idChoice).toBeChecked();
    idChoice.focus();
    await user.keyboard("{ArrowRight}");
    expect(
        within(handleChoices).getByRole("radio", {
            name: "Original key for this Basic user",
        }),
    ).toBeChecked();
    expect(
        screen.queryByRole("group", { name: "Original credential class" }),
    ).not.toBeInTheDocument();
    await user.keyboard("{ArrowRight}");
    const legacyChoice = within(handleChoices).getByRole("radio", {
        name: "Legacy Cockpit key reference",
    });
    expect(legacyChoice).toBeChecked();
    expect(legacyChoice).toHaveFocus();
    const credentials = screen.getByRole("group", {
        name: "Original credential class",
    });
    const writer = within(credentials).getByRole("radio", {
        name: "REST writer",
    });
    expect(writer).toBeChecked();
    writer.focus();
    await user.keyboard("{ArrowRight}");
    expect(
        within(credentials).getByRole("radio", { name: "REST reader" }),
    ).toBeChecked();
    expect(legacyChoice).toBeChecked();
    expect(original).toHaveValue("legacy-reader-key");
    expect(controller.snapshot().registry.records[0]).toEqual(saved);
    await user.click(
        within(handleChoices).getByRole("radio", {
            name: "Original key for this Basic user",
        }),
    );
    expect(
        screen.queryByRole("group", { name: "Original credential class" }),
    ).not.toBeInTheDocument();
    await user.click(legacyChoice);
    expect(screen.getByRole("radio", { name: "REST reader" })).toBeChecked();
    await user.click(
        screen.getByRole("button", { name: "Save original handle" }),
    );
    expect(controller.snapshot().registry.records).toHaveLength(2);
    expect(controller.snapshot().registry.records[0]).toEqual(saved);
    expect(controller.snapshot().registry.records[1]?.handles).toEqual({
        kind: "imported",
        operationId: null,
        legacyKey: {
            value: "legacy-reader-key",
            credentialClass: "rest-reader",
        },
    });
    expect(original).toHaveValue("");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(fetcher).not.toHaveBeenCalled();
});
test("unavailable storage is visible and no manual handle or request is fabricated", async () => {
    const { controller, fetcher } = mount(undefined, null);
    expect(screen.getByText("unavailable")).toBeInTheDocument();
    await importId();
    expect(screen.getByText(/handle could not be saved/)).toBeInTheDocument();
    expect(controller.snapshot().registry.records).toHaveLength(0);
    expect(fetcher).not.toHaveBeenCalled();
});
test("authentication loss clears observations and reconnect does not issue an operation request", async () => {
    const { controller, fetcher } = mount();
    await importId();
    const original = controller.snapshot().registry.records[0];
    act(() => {
        controller.disconnect();
    });
    expect(screen.getByText("disconnected")).toBeInTheDocument();
    expect(
        screen.getByText(/Private observations were cleared/),
    ).toBeInTheDocument();
    expect(controller.snapshot().registry.records[0]?.handles).toEqual(
        original?.handles,
    );
    await userEvent.click(screen.getByRole("button", { name: "Reconnect" }));
    await waitFor(() => {
        expect(
            screen.getByText(/Reconnected\. Observe original/),
        ).toBeInTheDocument();
    });
    expect(fetcher).not.toHaveBeenCalled();
    expect(
        screen.getByText(/Original operation handles are preserved separately/),
    ).toBeInTheDocument();
});
test("copy failure leaves selectable original handles and invalid imports produce no request", async () => {
    const { fetcher } = mount();
    await importId("invalid-id");
    expect(screen.getByText(/handle could not be saved/)).toBeInTheDocument();
    await userEvent.clear(
        screen.getByRole("textbox", { name: "Original handle" }),
    );
    await importId();
    Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: {
            writeText: () =>
                Promise.reject(new Error("fixture clipboard denied")),
        },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Copy recovery handles" }),
    );
    expect(screen.getByText(/Select and copy/)).toBeInTheDocument();
    expect(screen.getByText(/"operationId": "a{32}"/)).toBeInTheDocument();
    expect(fetcher).not.toHaveBeenCalled();
});

test("production host reads share the session and authentication refusal clears their private state", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire(), 401));
    const { controller } = mount(fetcher);
    await userEvent.click(screen.getByRole("link", { name: "Administration" }));
    await waitFor(() => {
        expect(screen.getByText("disconnected")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(
        "Reconnect to load current host authority.",
    );
    expect(controller.hostStatus.snapshot().result).toBeNull();
    expect(controller.hostStatus.snapshot().reason).toBe("authentication");
    expect(fetcher).toHaveBeenCalledOnce();
    await userEvent.click(screen.getByRole("link", { name: "Operations" }));
    await userEvent.click(screen.getByRole("link", { name: "Administration" }));
    expect(fetcher).toHaveBeenCalledOnce();
    expect(
        screen.getByRole("button", { name: "Refresh host status" }),
    ).toBeDisabled();
});

test("a changed interface build offers explicit reload while preserving the original handles", async () => {
    const { controller, fetcher } = mount(undefined, window.localStorage, () =>
        Promise.reject(new InterfaceUpdateRequiredError()),
    );
    await importId();
    const original = controller.snapshot().registry.records[0]?.handles;
    await userEvent.click(screen.getByRole("button", { name: "Reconnect" }));
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Reload interface" }),
        ).toBeInTheDocument();
    });
    expect(controller.snapshot().connection).toBe("update_required");
    expect(controller.snapshot().registry.records[0]?.handles).toEqual(
        original,
    );
    expect(fetcher).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Reconnect" })).toBeDisabled();
});
