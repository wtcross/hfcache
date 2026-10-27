/** Branded browser transport boundary; real mount/controller/client, owned HTTP wires only. */
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { mountApplication } from "../src/mount";
import { bootstrapScope } from "../src/bootstrap";
import { createAuthSession } from "../src/state/authority";
import { createOperationRegistry } from "../src/state/operation-registry";
import { hostStatusWire } from "./host-fixtures";
import {
    jsonResponse,
    readWire,
    statusPayload,
    versionPayload,
} from "./read-fixtures";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";

const operationId = "a".repeat(32),
    runId = "3".repeat(32);
const originalKey = "7cb9ab4e-2e54-479b-b15f-3e2c92cfc85d";
const bootstrap = {
    ...uiBootstrapFixture(),
    configured_origin: "http://localhost",
    configured_archive_id: hostStatusWire().archive_id,
};
let unmount = () => {};
afterEach(() => {
    act(unmount);
    unmount = () => {};
    localStorage.clear();
    vi.unstubAllGlobals();
    document.head.innerHTML = "";
});
function mount(route: "administration" | "operations") {
    vi.stubGlobal(
        "location",
        new URL(bootstrap.configured_origin + "/ui/" + route),
    );
    window.history.replaceState(null, "", "/ui/" + route);
    inertUiDocument(document);
    act(() => {
        unmount = mountApplication(document, bootstrap);
    }); // Deliberately omit fetcher.
}
function brandedTransport() {
    const requests: {
        path: string;
        method: string;
        originalKey: string | null;
    }[] = [];
    let rejectedReceivers = 0;
    const nativeLike: typeof fetch = function (this: unknown, input, options) {
        // Chromium's native Window.fetch rejects an ApiClient receiver before network I/O.
        if (this !== globalThis) {
            rejectedReceivers++;
            throw new TypeError("Illegal invocation");
        }
        const url =
            input instanceof URL
                ? input
                : new URL(typeof input === "string" ? input : input.url);
        expect(url.origin).toBe(bootstrap.configured_origin);
        const method = options?.method ?? "GET";
        expect(method).toBe("GET");
        requests.push({
            path: url.pathname,
            method,
            originalKey: new Headers(options?.headers).get("Idempotency-Key"),
        });
        if (url.pathname === "/api/v1/host/status")
            return Promise.resolve(jsonResponse(hostStatusWire()));
        if (url.pathname === "/api/v1/status") {
            const payload = statusPayload(true);
            return Promise.resolve(
                jsonResponse({
                    ...readWire("status", {
                        ...payload,
                        archive: {
                            ...payload.archive,
                            archive_id: bootstrap.configured_archive_id,
                        },
                    }),
                    archive_id: bootstrap.configured_archive_id,
                }),
            );
        }
        if (url.pathname === "/api/v1/health")
            return Promise.resolve(
                jsonResponse(
                    readWire("health", {
                        ready: true,
                        // The actual unavailable-policy health variant remains
                        // daemon-ready and carries no archive inspection.
                        policy_valid: null,
                        archive: null,
                    }),
                ),
            );
        if (url.pathname === "/api/v1/version")
            return Promise.resolve(
                jsonResponse(readWire("version", versionPayload)),
            );
        const operation = {
            schema_version: 1,
            operation_id: operationId,
            principal: "rest-writer",
            route: "/api/v1/plans",
            archive_id: bootstrap.configured_archive_id,
            config_fingerprint: "2".repeat(64),
            state: "succeeded",
            created_at: "2026-10-20T12:00:00.000001Z",
            updated_at: "2026-10-20T12:00:00.000002Z",
            completed_at: "2026-10-20T12:00:00.000002Z",
            domain_run_id: runId,
            transaction_ids: [],
            next_event_sequence: 1,
            result_recorded: true,
        };
        const response =
            url.pathname === "/api/v1/operations/lookup"
                ? readWire("operations lookup", { operation })
                : url.pathname === `/api/v1/operations/${operationId}/result`
                  ? readWire("plan", { repositories: [] })
                  : null;
        if (response === null) throw new Error("Unexpected owned request");
        return Promise.resolve(
            jsonResponse({
                ...response,
                archive_id: bootstrap.configured_archive_id,
                config_fingerprint: "2".repeat(64),
            }),
        );
    };
    vi.stubGlobal("fetch", nativeLike);
    return { requests, rejectedReceivers: () => rejectedReceivers };
}

test("production default mount reaches host and Administration reads through a branded native-like fetch", async () => {
    localStorage.clear();
    const transport = brandedTransport();
    mount("administration");
    await waitFor(() => {
        expect(screen.getByTestId("host-state")).toHaveTextContent("supported");
    });
    await screen.findByText("API daemon: Ready.");
    expect(screen.getByText("Installed policy: Unknown.")).toBeInTheDocument();
    await screen.findByText(versionPayload.application, { exact: true });
    expect(transport.requests).toEqual([
        { path: "/api/v1/host/status", method: "GET", originalKey: null },
        { path: "/api/v1/status", method: "GET", originalKey: null },
        { path: "/api/v1/health", method: "GET", originalKey: null },
        { path: "/api/v1/version", method: "GET", originalKey: null },
    ]);
    expect(transport.rejectedReceivers()).toBe(0);
});

test("production default mount restores uncertain key then observes actual typed receipt/result without POST", async () => {
    localStorage.clear();
    const registry = createOperationRegistry({
        storage: localStorage,
        keyFactory: () => originalKey,
    });
    const session = createAuthSession({
        scope: bootstrapScope(bootstrap),
        authGeneration: 1,
    });
    const record = registry.prepare("installedPlan", session);
    registry.submitted(
        record.recordId,
        {
            kind: "uncertain",
            route: "/api/v1/plans",
            idempotencyKey: originalKey,
            reason: "network",
        },
        session,
    );
    const transport = brandedTransport();
    mount("operations");
    await screen.findByRole("heading", { name: "Original operation recovery" });
    expect(transport.requests).toEqual([]);
    await userEvent.click(
        screen.getByRole("button", {
            name: "Observe original operation",
        }),
    );
    await screen.findByText(/Verified in this session\./u);
    expect(screen.getByText("settled", { exact: true })).toBeInTheDocument();
    const recovery = screen.getByRole("article", {
        name: "Recovery record " + record.recordId,
    });
    expect(
        within(recovery).getByText("Original operation ID", { exact: true })
            .nextElementSibling,
    ).toHaveTextContent(operationId);
    expect(
        within(
            within(recovery).getByRole("region", {
                name: "Original operation result",
            }),
        ).getByText(operationId, { exact: true }),
    ).toBeInTheDocument();
    expect(transport.requests).toEqual([
        { path: "/api/v1/operations/lookup", method: "GET", originalKey },
        {
            path: `/api/v1/operations/${operationId}/result`,
            method: "GET",
            originalKey: null,
        },
    ]);
    expect(transport.rejectedReceivers()).toBe(0);
});
