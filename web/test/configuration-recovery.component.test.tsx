/** Reloaded original-key recovery through actual store/controller/typed GETs. */
import { useSyncExternalStore } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { OperationRecovery } from "../src/components/OperationRecovery";
import { createSessionController } from "../src/state/session-controller";
import { createConfigurationStore } from "../src/configuration/configuration-state";
import { ARCHIVE_ID, jsonResponse } from "./read-fixtures";
import { operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import fixtures from "../../tests/fixtures/web_wire/config.json";

const closes: (() => void)[] = [];
afterEach(() => {
    for (const close of closes.splice(0)) close();
});
test.each(["confirmed", "installed_unconfirmed"] as const)(
    "restored original application observes host %s separately from interrupted API, without write/host grants",
    async (state) => {
        const user = userEvent.setup();
        const original = uiBootstrapFixture();
        const bootstrap = {
            ...original,
            configured_origin: location.origin,
            configured_archive_id: ARCHIVE_ID,
            user: {
                ...original.user,
                admin_permissions: original.user.admin_permissions.map(
                    (permission) => ({
                        ...permission,
                        granted: permission.capability === "config-read",
                        effective: permission.capability === "config-read",
                        reason:
                            permission.capability === "config-read"
                                ? ("allowed" as const)
                                : ("not_granted" as const),
                    }),
                ),
            },
        };
        const id = fixtures.application_outcome.operation_id;
        const interrupted = receipt({
            operation_id: id,
            route: "/api/v1/config/applications",
            state: "interrupted",
            completed_at: "2026-10-20T12:00:02.000000Z",
            updated_at: "2026-10-20T12:00:02.000000Z",
            domain_run_id: null,
        });
        const fetcher = vi.fn<typeof fetch>((input) => {
            const url = new URL(
                input instanceof Request ? input.url : String(input),
            );
            if (url.pathname === "/api/v1/operations/lookup")
                return Promise.resolve(
                    jsonResponse(
                        operationResponse("operations lookup", {
                            operation: interrupted,
                        }),
                    ),
                );
            if (url.pathname === "/api/v1/config")
                return Promise.resolve(
                    jsonResponse({
                        ...operationResponse("config read", fixtures.read),
                        config_fingerprint: null,
                    }),
                );
            return Promise.resolve(
                jsonResponse(
                    operationResponse("config outcome", {
                        ...fixtures.application_outcome,
                        state,
                        pending: state !== "confirmed",
                    }),
                ),
            );
        });
        let saved: string | null = null;
        const options = {
            bootstrap,
            fetcher,
            storage: {
                getItem: () => saved,
                setItem: (_key: string, value: string) => {
                    saved = value;
                },
            },
            reconnect: () => Promise.resolve(bootstrap),
        };
        const first = createSessionController(options);
        first.importHandle({
            kind: "basic-key",
            key: "original-owned-application-key",
            originalScope: first.originalScope(),
        });
        first.dispose();
        const controller = createSessionController(options);
        const store = createConfigurationStore(controller);
        closes.push(() => {
            store.dispose();
            controller.dispose();
        });
        function View() {
            const session = useSyncExternalStore(
                controller.subscribe,
                controller.snapshot,
            );
            return (
                <OperationRecovery
                    controller={controller}
                    session={session}
                    configuration={store}
                />
            );
        }
        render(<View />);
        expect(fetcher).not.toHaveBeenCalled();
        await user.click(
            screen.getByRole("button", { name: "Observe original operation" }),
        );
        await waitFor(() => {
            expect(screen.getByText("interrupted")).toBeInTheDocument();
        });
        await user.click(
            screen.getByRole("button", {
                name: "Observe original configuration outcome",
            }),
        );
        await waitFor(() => {
            expect(
                screen.getByText("Protected host outcome"),
            ).toBeInTheDocument();
        });
        expect(
            screen.getByText("Original API receipt state: interrupted."),
        ).toBeInTheDocument();
        expect(screen.getByText(state, { exact: true })).toBeInTheDocument();
        if (state === "confirmed") {
            expect(
                screen.getByText(
                    "Installed configuration confirmed. The original API receipt is unchanged.",
                ),
            ).toBeInTheDocument();
            expect(controller.snapshot().canSubmit).toBe(true);
        } else {
            expect(
                screen.getByText(
                    "Protected effects remain unresolved. Preserve original handles and evidence; do not repeat Apply.",
                ),
            ).toBeInTheDocument();
            expect(controller.snapshot().canSubmit).toBe(false);
            expect(
                screen.queryByText(
                    "Installed configuration confirmed. The original API receipt is unchanged.",
                ),
            ).not.toBeInTheDocument();
        }
        expect(
            fetcher.mock.calls.every(
                ([, options]) => options?.method === "GET",
            ),
        ).toBe(true);
        const keys = fetcher.mock.calls.filter(([input]) => {
            const path = new URL(
                input instanceof Request ? input.url : String(input),
            ).pathname;
            return path.includes("/lookup") || path.includes("/applications/");
        });
        expect(keys).toHaveLength(3);
        for (const [, options] of keys)
            expect(new Headers(options?.headers).get("Idempotency-Key")).toBe(
                "original-owned-application-key",
            );
    },
);
