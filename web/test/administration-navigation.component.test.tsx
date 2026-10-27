import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useSyncExternalStore } from "react";
import { afterEach, expect, test } from "vitest";
import { App } from "../src/App";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { hostControlsFixture } from "./host-controls-fixtures";

const disposals: (() => void)[] = [];
afterEach(() => {
    cleanup();
    for (const dispose of disposals.splice(0)) dispose();
});
async function mount() {
    window.history.replaceState(null, "", "/ui/administration");
    const fixture = hostControlsFixture();
    const read = createAdministrationReadStore(fixture.controller);
    disposals.push(() => {
        read.dispose();
        fixture.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            fixture.controller.subscribe,
            fixture.controller.snapshot,
        );
        useSyncExternalStore(fixture.store.subscribe, fixture.store.snapshot);
        return (
            <App
                basePath="/ui/"
                bootstrap={session.bootstrap}
                controller={fixture.controller}
                session={session}
                administrationRead={read}
                hostControls={fixture.store}
            />
        );
    }
    render(<Connected />);
    const user = userEvent.setup();
    await user.click(
        screen.getByRole("button", { name: "Read schedule and observer" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Edit sync schedule" }),
        ).toBeEnabled();
    });
    await user.click(
        screen.getByRole("button", { name: "Edit sync schedule" }),
    );
    const calendar = screen.getByRole("textbox", {
        name: "OnCalendar expression",
    });
    await user.clear(calendar);
    await user.type(calendar, "weekly UTC");
    expect(fixture.store.snapshot().dirty).toBe(true);
    return { ...fixture, read, user };
}

test("Administration composes real controls and original recovery without submitting work on mount", async () => {
    const fixture = await mount();
    expect(
        screen.getByRole("heading", { name: "Archive health" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("heading", { name: "Original operation recovery" }),
    ).toBeInTheDocument();
    expect(
        screen.getByRole("heading", { name: "Sync schedule" }),
    ).toBeInTheDocument();
    expect(fixture.calls.every((call) => call.method === "GET")).toBe(true);
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
});

test("navigation offers Stay or explicit schedule discard and preserves original operations", async () => {
    const fixture = await mount();
    const before = fixture.controller.snapshot().registry.records;
    await fixture.user.click(screen.getByRole("link", { name: "Maintenance" }));
    expect(
        screen.getByRole("dialog", { name: "Unsaved schedule changes" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ui/administration");
    expect(screen.getByRole("button", { name: "Stay" })).toHaveFocus();
    await fixture.user.keyboard("{Escape}");
    expect(fixture.store.snapshot().draft.calendar).toBe("weekly UTC");
    expect(fixture.store.snapshot().dirty).toBe(true);
    await fixture.user.click(screen.getByRole("link", { name: "Maintenance" }));
    await fixture.user.click(
        screen.getByRole("button", { name: "Discard draft and leave" }),
    );
    expect(window.location.pathname).toBe("/ui/maintenance");
    expect(fixture.store.snapshot().dirty).toBe(false);
    expect(fixture.store.snapshot().active).toBe(false);
    expect(fixture.controller.snapshot().registry.records).toEqual(before);
    expect(fixture.calls.every((call) => call.method === "GET")).toBe(true);
});

test("history, fragment changes and unload cannot silently discard a private schedule draft", async () => {
    const fixture = await mount();
    const unload = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(unload);
    expect(unload.defaultPrevented).toBe(true);
    act(() => {
        window.history.pushState(null, "", "/ui/library");
        window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(window.location.pathname).toBe("/ui/administration");
    await fixture.user.click(screen.getByRole("button", { name: "Stay" }));
    act(() => {
        window.history.replaceState(null, "", "/ui/administration#changed");
        window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(window.location.hash).toBe("");
    await fixture.user.click(
        screen.getByRole("button", { name: "Discard draft and leave" }),
    );
    expect(window.location.hash).toBe("#changed");
    const clean = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(clean);
    expect(clean.defaultPrevented).toBe(false);
    expect(fixture.calls.every((call) => call.method === "GET")).toBe(true);
});
