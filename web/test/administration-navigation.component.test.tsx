import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useSyncExternalStore } from "react";
import { afterEach, expect, test } from "vitest";
import { App } from "../src/App";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { hostControlsFixture } from "./host-controls-fixtures";
import {
    jsonResponse,
    readWire,
    statusPayload,
    versionPayload,
} from "./read-fixtures";

const disposals: (() => void)[] = [];
afterEach(() => {
    cleanup();
    for (const dispose of disposals.splice(0)) dispose();
});
async function mount() {
    window.history.replaceState(null, "", "/ui/administration");
    const fixture = hostControlsFixture({
        extra(url) {
            if (url.pathname === "/api/v1/status")
                return jsonResponse(readWire("status", statusPayload(true)));
            if (url.pathname === "/api/v1/health")
                return jsonResponse(
                    readWire("health", {
                        ready: true,
                        policy_valid: null,
                        archive: null,
                    }),
                );
            if (url.pathname === "/api/v1/version")
                return jsonResponse(readWire("version", versionPayload));
            throw new Error("Unexpected owned read: " + url.pathname);
        },
    });
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
    await act(async () => {
        await read.refresh();
    });
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

test("dirty unload veto retains the exact schedule draft, saved original ID and active working reads", async () => {
    const fixture = await mount();
    const operationId = "5".repeat(32);
    act(() => {
        fixture.controller.importHandle({ kind: "id", operationId });
    });
    const draft = JSON.stringify(fixture.store.snapshot().draft);
    const registry = fixture.controller.snapshot().registry.records;
    const saved = fixture.saved();
    const generation = fixture.controller.snapshot().generation;
    const scope = fixture.controller.originalScope();
    expect(registry).toHaveLength(1);
    expect(registry[0]?.handles).toMatchObject({
        kind: "imported",
        operationId,
    });
    expect(saved).toContain(operationId);
    expect(fixture.read.snapshot().active).toBe(true);
    expect(fixture.store.snapshot().active).toBe(true);
    expect(fixture.read.snapshot().version.phase).toBe("ready");
    const calls = fixture.calls.length;
    const unload = new Event("beforeunload", { cancelable: true });
    act(() => {
        window.dispatchEvent(unload);
    });
    expect(unload.defaultPrevented).toBe(true);
    expect(JSON.stringify(fixture.store.snapshot().draft)).toBe(draft);
    expect(fixture.store.snapshot().dirty).toBe(true);
    expect(fixture.store.snapshot().active).toBe(true);
    expect(fixture.read.snapshot().active).toBe(true);
    expect(fixture.controller.snapshot().registry.records).toEqual(registry);
    expect(fixture.saved()).toBe(saved);
    expect(fixture.calls).toHaveLength(calls);
    await fixture.user.click(
        screen.getByRole("button", { name: "Refresh administration status" }),
    );
    await waitFor(() => {
        expect(fixture.calls).toHaveLength(calls + 3);
        expect(fixture.read.snapshot().version.phase).toBe("ready");
    });
    expect(fixture.calls).toHaveLength(calls + 3);
    expect(fixture.calls.slice(calls).map((call) => call.path)).toEqual([
        "/api/v1/status",
        "/api/v1/health",
        "/api/v1/version",
    ]);
    expect(fixture.read.snapshot().status.phase).toBe("ready");
    expect(fixture.read.snapshot().health.result?.kind).toBe("success");
    expect(fixture.read.snapshot().version.phase).toBe("ready");
    expect(JSON.stringify(fixture.store.snapshot().draft)).toBe(draft);
    expect(fixture.store.snapshot().dirty).toBe(true);
    expect(fixture.controller.snapshot().registry.records).toEqual(registry);
    expect(fixture.saved()).toBe(saved);
    expect(fixture.controller.snapshot().generation).toBe(generation);
    expect(fixture.controller.originalScope()).toEqual(scope);
    expect(fixture.calls.every((call) => call.method === "GET")).toBe(true);
});
