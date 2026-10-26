import configFixture from "../../tests/fixtures/web_wire/config.json";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "../src/App";
import { createConfigurationStore } from "../src/configuration/configuration-state";
import { createSessionController } from "../src/state/session-controller";
import { decodeConfigRead } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { isRecord } from "../src/wire/runtime";
import { ARCHIVE_ID, jsonResponse } from "./read-fixtures";
import { operationResponse } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const raw: unknown = configFixture;
if (!isRecord(raw)) throw new Error("Independent config fixture unavailable");
const config = decodeConfigRead(parseWireJson(JSON.stringify(raw.read)));
const cleanups: (() => void)[] = [];
afterEach(() => {
    for (const close of cleanups.splice(0)) close();
});
async function setup() {
    window.history.replaceState(null, "", "/ui/administration");
    const initial = uiBootstrapFixture();
    const bootstrap = {
        ...initial,
        configured_origin: location.origin,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...initial.user,
            admin_permissions: initial.user.admin_permissions.map(
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
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(
            jsonResponse({
                ...operationResponse("config read", config),
                config_fingerprint: null,
            }),
        ),
    );
    let saved: string | null = null;
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: {
            getItem: () => saved,
            setItem: (_key, value) => {
                saved = value;
            },
        },
        reconnect: () => Promise.resolve(bootstrap),
    });
    const store = createConfigurationStore(controller);
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    render(
        <App
            basePath="/ui/"
            bootstrap={bootstrap}
            controller={controller}
            session={controller.snapshot()}
            configuration={store}
        />,
    );
    expect(fetcher).not.toHaveBeenCalled();
    await act(async () => {
        await store.load();
    });
    act(() => {
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        });
    });
    return { store, controller, fetcher, user: userEvent.setup() };
}
test("workspace navigation offers Stay or explicit discard and keeps original operations untouched", async () => {
    const { store, controller, fetcher, user } = await setup();
    const records = controller.snapshot().registry.records;
    await user.click(screen.getByRole("link", { name: "Operations" }));
    expect(
        screen.getByRole("dialog", { name: "Unsaved configuration changes" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ui/administration");
    expect(screen.getByRole("button", { name: "Stay" })).toHaveFocus();
    await user.tab();
    expect(
        screen.getByRole("button", { name: "Discard draft and leave" }),
    ).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(store.snapshot().dirty).toBe(true);
    await user.click(screen.getByRole("link", { name: "Operations" }));
    await user.click(
        screen.getByRole("button", { name: "Discard draft and leave" }),
    );
    expect(window.location.pathname).toBe("/ui/operations");
    expect(store.snapshot().dirty).toBe(false);
    expect(controller.snapshot().registry.records).toEqual(records);
    expect(fetcher).toHaveBeenCalledTimes(1);
});
test("history and fragment changes cannot discard a dirty configuration; unload is guarded", async () => {
    const { store, user } = await setup();
    const before = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(before);
    expect(before.defaultPrevented).toBe(true);
    act(() => {
        window.history.pushState(null, "", "/ui/library");
        window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(window.location.pathname).toBe("/ui/administration");
    await user.click(screen.getByRole("button", { name: "Stay" }));
    expect(store.snapshot().dirty).toBe(true);
    act(() => {
        window.history.replaceState(null, "", "/ui/administration#changed");
        window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(window.location.hash).toBe("");
    await user.click(
        screen.getByRole("button", { name: "Discard draft and leave" }),
    );
    expect(window.location.hash).toBe("#changed");
    const clean = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(clean);
    expect(clean.defaultPrevented).toBe(false);
});
