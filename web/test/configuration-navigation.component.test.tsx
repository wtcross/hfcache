import configFixture from "../../tests/fixtures/web_wire/config.json";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useSyncExternalStore } from "react";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "../src/App";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { createHostControlsStore } from "../src/administration/host-controls-state";
import { createConfigurationStore } from "../src/configuration/configuration-state";
import { createSessionController } from "../src/state/session-controller";
import { decodeConfigRead } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { isRecord } from "../src/wire/runtime";
import {
    ARCHIVE_ID,
    jsonResponse,
    readWire,
    statusPayload,
    versionPayload,
} from "./read-fixtures";
import { operationResponse } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const raw: unknown = configFixture;
if (!isRecord(raw)) throw new Error("Independent config fixture unavailable");
const config = decodeConfigRead(parseWireJson(JSON.stringify(raw.read)));
const cleanups: (() => void)[] = [];
afterEach(() => {
    for (const close of cleanups.splice(0)) close();
});
async function setup(withAdministrationReads = false) {
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
    const fetcher = vi.fn<typeof fetch>((input) => {
        const path = new URL(
            typeof input === "string"
                ? input
                : input instanceof URL
                  ? input.href
                  : input.url,
        ).pathname;
        if (path === "/api/v1/status")
            return Promise.resolve(
                jsonResponse(readWire("status", statusPayload(true))),
            );
        if (path === "/api/v1/health")
            return Promise.resolve(
                jsonResponse(
                    readWire("health", {
                        ready: true,
                        policy_valid: null,
                        archive: null,
                    }),
                ),
            );
        if (path === "/api/v1/version")
            return Promise.resolve(
                jsonResponse(readWire("version", versionPayload)),
            );
        if (path !== "/api/v1/config")
            throw new Error("Unexpected owned read: " + path);
        return Promise.resolve(
            jsonResponse({
                ...operationResponse("config read", config),
                config_fingerprint: null,
            }),
        );
    });
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
    const read = withAdministrationReads
        ? createAdministrationReadStore(controller)
        : null;
    const hostControls = withAdministrationReads
        ? createHostControlsStore(controller)
        : null;
    cleanups.push(() => {
        read?.dispose();
        hostControls?.dispose();
        store.dispose();
        controller.dispose();
    });
    function Connected() {
        const session = useSyncExternalStore(
            controller.subscribe,
            controller.snapshot,
        );
        return (
            <App
                basePath="/ui/"
                bootstrap={bootstrap}
                controller={controller}
                session={session}
                configuration={store}
                {...(read === null || hostControls === null
                    ? {}
                    : { administrationRead: read, hostControls })}
            />
        );
    }
    render(<Connected />);
    if (!withAdministrationReads) expect(fetcher).not.toHaveBeenCalled();
    await act(async () => {
        await store.load();
        await read?.refresh();
    });
    act(() => {
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        });
    });
    return {
        store,
        controller,
        fetcher,
        read,
        saved: () => saved,
        user: userEvent.setup(),
    };
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

test("dirty unload veto retains the exact configuration draft, saved original ID and working administration reads", async () => {
    const fixture = await setup(true);
    const read = fixture.read;
    if (read === null) throw new Error("Missing owned administration reader");
    const operationId = "4".repeat(32);
    act(() => {
        fixture.controller.importHandle({ kind: "id", operationId });
    });
    const draft = JSON.stringify(fixture.store.snapshot().prepared);
    const registry = fixture.controller.snapshot().registry.records;
    const saved = fixture.saved();
    const generation = fixture.controller.snapshot().generation;
    const scope = fixture.controller.originalScope();
    expect(fixture.store.snapshot().dirty).toBe(true);
    expect(registry).toHaveLength(1);
    expect(registry[0]?.handles).toMatchObject({
        kind: "imported",
        operationId,
    });
    expect(saved).toContain(operationId);
    expect(read.snapshot().active).toBe(true);
    expect(read.snapshot().version.phase).toBe("ready");
    const calls = fixture.fetcher.mock.calls.length;
    const unload = new Event("beforeunload", { cancelable: true });
    act(() => {
        window.dispatchEvent(unload);
    });
    expect(unload.defaultPrevented).toBe(true);
    expect(JSON.stringify(fixture.store.snapshot().prepared)).toBe(draft);
    expect(fixture.store.snapshot().dirty).toBe(true);
    expect(read.snapshot().active).toBe(true);
    expect(fixture.controller.snapshot().registry.records).toEqual(registry);
    expect(fixture.saved()).toBe(saved);
    expect(fixture.fetcher).toHaveBeenCalledTimes(calls);
    await fixture.user.click(
        screen.getByRole("button", { name: "Refresh administration status" }),
    );
    await waitFor(() => {
        expect(fixture.fetcher).toHaveBeenCalledTimes(calls + 3);
        expect(read.snapshot().version.phase).toBe("ready");
    });
    expect(fixture.fetcher).toHaveBeenCalledTimes(calls + 3);
    expect(read.snapshot().status.phase).toBe("ready");
    expect(read.snapshot().health.result?.kind).toBe("success");
    expect(read.snapshot().version.phase).toBe("ready");
    expect(JSON.stringify(fixture.store.snapshot().prepared)).toBe(draft);
    expect(fixture.store.snapshot().dirty).toBe(true);
    expect(fixture.controller.snapshot().registry.records).toEqual(registry);
    expect(fixture.saved()).toBe(saved);
    expect(fixture.controller.snapshot().generation).toBe(generation);
    expect(fixture.controller.originalScope()).toEqual(scope);
    expect(
        fixture.fetcher.mock.calls.every(([, init]) => init?.method === "GET"),
    ).toBe(true);
});
