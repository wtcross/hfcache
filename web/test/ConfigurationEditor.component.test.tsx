/** Real controller/store/typed-client DOM boundary; these fixtures perform no host effects. */
import {
    act,
    cleanup,
    fireEvent,
    render,
    screen,
    waitFor,
    within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { ConfigurationEditor } from "../src/components/ConfigurationEditor";
import { createConfigurationStore } from "../src/configuration/configuration-state";
import type { ConfigurationStore } from "../src/configuration/configuration-state";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import { decodeConfigRead } from "../src/wire/generated";
import type {
    ConfigApplicationOutcome,
    ConfigRead,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { jsonResponse, problemWire, readWire } from "./read-fixtures";
import { operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import fixtures from "../../tests/fixtures/web_wire/config.json";

const owned: { store: ConfigurationStore; controller: SessionController }[] =
    [];
const planId = "a".repeat(32),
    appId = fixtures.application_outcome.operation_id;
function base(): ConfigRead {
    return decodeConfigRead(parseWireJson(JSON.stringify(fixtures.read)));
}
function pathOf(input: RequestInfo | URL): string {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    ).pathname;
}
function mount(
    options: {
        read?: boolean;
        write?: boolean;
        installed?: ConfigRead;
        validationConflict?: boolean;
        outcomeState?: ConfigApplicationOutcome["state"];
        outcomePending?: boolean;
        readFailure?: "domain" | "malformed" | "offline";
        requiredScope?: boolean;
        failAfterOutcomeRead?: boolean;
    } = {},
) {
    let installed = options.installed ?? base();
    const bootstrap = uiBootstrapFixture();
    const actual = {
        ...bootstrap,
        configured_origin: window.location.origin,
        configured_archive_id: installed.archive_id,
        user: {
            ...bootstrap.user,
            admin_permissions: bootstrap.user.admin_permissions.map(
                (permission) => {
                    const allowed =
                        permission.capability === "config-read"
                            ? options.read !== false
                            : permission.capability === "config-write"
                              ? options.write !== false
                              : false;
                    return {
                        ...permission,
                        granted: allowed,
                        effective: allowed,
                        reason: allowed
                            ? ("allowed" as const)
                            : ("not_granted" as const),
                    };
                },
            ),
        },
    };
    const row = (id: string, route: string, terminal = false) =>
        receipt({
            operation_id: id,
            route,
            state: terminal ? "succeeded" : "queued",
            updated_at: terminal
                ? "2026-10-20T12:00:02.000000Z"
                : "2026-10-20T12:00:00.000001Z",
            completed_at: terminal ? "2026-10-20T12:00:02.000000Z" : null,
            domain_run_id: terminal ? "3".repeat(32) : null,
            result_recorded: terminal,
        });
    function accepted(id: string, route: string) {
        const status = "/api/v1/operations/" + id;
        return new Response(
            JSON.stringify({
                schema_version: 1,
                request_id: "f".repeat(32),
                archive_id: installed.archive_id,
                config_fingerprint: "2".repeat(64),
                created: true,
                operation: row(id, route),
                links: {
                    status,
                    result: status + "/result",
                    events: status + "/events",
                },
            }),
            {
                status: 202,
                headers: {
                    "Content-Type": "application/json",
                    Location: status,
                },
            },
        );
    }
    const observedOutcome = {
        ...fixtures.application_outcome,
        state: options.outcomeState ?? "confirmed",
        pending: options.outcomePending ?? false,
    };
    const requiredSelectors = options.requiredScope ? ["model:owned/new"] : [];
    let observedHostOutcome = false;
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
        const path = pathOf(input);
        if (path === "/api/v1/config" && init?.method === "GET") {
            if (options.failAfterOutcomeRead && observedHostOutcome)
                return Promise.resolve(
                    jsonResponse(problemWire("HFAPI005", 20), 503),
                );
            if (options.readFailure === "offline")
                return Promise.reject(
                    new TypeError("Owned unavailable transport"),
                );
            if (options.readFailure === "malformed")
                return Promise.resolve(jsonResponse({ schema_version: 99 }));
            if (options.readFailure === "domain")
                return Promise.resolve(
                    jsonResponse({
                        ...readWire("config read", {}, true),
                        archive_id: installed.archive_id,
                    }),
                );
            return Promise.resolve(
                jsonResponse({
                    ...readWire("config read", installed),
                    archive_id: installed.archive_id,
                }),
            );
        }
        if (path === "/api/v1/config/validate")
            return Promise.resolve(
                options.validationConflict
                    ? jsonResponse(problemWire("HFAPI007", 10), 409)
                    : jsonResponse(
                          operationResponse("config validate", {
                              ...fixtures.validation,
                              required_selectors: requiredSelectors,
                          }),
                      ),
            );
        if (path === "/api/v1/plans" && init?.method === "POST")
            return Promise.resolve(accepted(planId, path));
        if (path === "/api/v1/config/applications" && init?.method === "POST")
            return Promise.resolve(accepted(appId, path));
        if (path === "/api/v1/operations/" + planId)
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations show", {
                        operation: row(planId, "/api/v1/plans", true),
                    }),
                ),
            );
        if (path === "/api/v1/operations/" + planId + "/result")
            return Promise.resolve(
                jsonResponse(
                    operationResponse("plan", {
                        ...fixtures.assessment,
                        required_selectors: requiredSelectors,
                        sizing: options.requiredScope
                            ? {
                                  repositories: [
                                      {
                                          repository_type: "model",
                                          repository_id: "owned/new",
                                          requested_revision: "main",
                                          resolved_commit_sha: "8".repeat(40),
                                          enabled: true,
                                          upstream_state: "available",
                                          publication_mode: "hardlink",
                                          file_count: 2,
                                          logical_bytes: 17,
                                          estimated_new_bytes: 7,
                                          projected_publication_bytes: 17,
                                      },
                                  ],
                              }
                            : null,
                    }),
                ),
            );
        if (
            path === "/api/v1/operations/" + appId ||
            path === "/api/v1/operations/lookup"
        )
            return Promise.resolve(
                jsonResponse(
                    operationResponse(
                        path.endsWith("lookup")
                            ? "operations lookup"
                            : "operations show",
                        {
                            operation: row(
                                appId,
                                "/api/v1/config/applications",
                                true,
                            ),
                        },
                    ),
                ),
            );
        if (path === "/api/v1/operations/" + appId + "/result")
            return Promise.resolve(
                jsonResponse(
                    operationResponse("config apply", {
                        ...fixtures.application_outcome,
                        state: "installed_unconfirmed",
                        pending: true,
                    }),
                ),
            );
        if (path === "/api/v1/config/applications/" + appId) {
            observedHostOutcome = true;
            return Promise.resolve(
                jsonResponse(
                    operationResponse("config outcome", observedOutcome),
                ),
            );
        }
        throw new Error("Unexpected editor boundary request.");
    });
    const controller = createSessionController({
        bootstrap: actual,
        fetcher,
        storage: window.localStorage,
        reconnect: () => Promise.resolve(actual),
    });
    const store = createConfigurationStore(controller);
    owned.push({ controller, store });
    const view = render(<ConfigurationEditor store={store} />);
    return {
        ...view,
        controller,
        store,
        fetcher,
        install(value: ConfigRead) {
            installed = value;
        },
        async loaded() {
            await userEvent.click(
                screen.getByRole("button", {
                    name: "Read installed configuration",
                }),
            );
            await waitFor(() => {
                expect(store.snapshot().phase).toBe("ready");
            });
        },
        posts: () =>
            fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
    };
}
afterEach(() => {
    cleanup();
    for (const item of owned.splice(0)) {
        item.store.dispose();
        item.controller.dispose();
    }
    window.localStorage.clear();
    vi.restoreAllMocks();
});

test("initial render is read-free, then the real projection exposes descriptors without protected-value inputs", async () => {
    const fixture = mount();
    expect(fixture.fetcher).not.toHaveBeenCalled();
    await fixture.loaded();
    expect(fixture.fetcher).toHaveBeenCalledTimes(1);
    const read = fixture.store.snapshot().readResult;
    expect(read?.kind).toBe("success");
    if (read?.kind !== "success")
        throw new Error("Missing genuine configuration projection.");
    expect(read.response.archive_id).toBe(base().archive_id);
    expect(read.response.config_fingerprint).toBeNull();
    expect(read.response.envelope.data).toEqual(base());
    expect(
        screen.getByRole("region", { name: "Configuration and tags" }),
    ).toBeInTheDocument();
    expect(
        screen.getByText(base().base_revision, { selector: "code" }),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("textbox", { name: /archive root|token|server/iu }),
    ).not.toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Apply reviewed changes" }),
    ).toBeDisabled();
    expect(fixture.posts()).toEqual([]);
});

test("tag editing preserves complete revision, disabled state and dependencies while retiring validation on every raw edit", async () => {
    const original = base();
    const entry = original.editable.repositories[0];
    if (entry === undefined) throw new Error("Missing owned repository.");
    const complete = {
        ...entry,
        revision: "release/v2",
        enabled: false,
        declared_dependencies: ["owned/dependency"],
    };
    const fixture = mount({
        installed: {
            ...original,
            editable: { ...original.editable, repositories: [complete] },
        },
    });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Validate draft" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Preview sizing" }),
        ).toBeEnabled();
    });
    await userEvent.click(
        screen.getByRole("button", {
            name: "Edit model organization/model-name",
        }),
    );
    expect(screen.getByLabelText("Repository ID")).toBeDisabled();
    expect(screen.getByLabelText("Requested revision")).toHaveValue(
        "release/v2",
    );
    expect(screen.getByLabelText("Enabled")).not.toBeChecked();
    expect(
        screen.getByRole("button", { name: "Preview sizing" }),
    ).toBeDisabled();
    const generation = fixture.store.snapshot().generation;
    fireEvent.change(screen.getByLabelText("Tags (one per line)"), {
        target: { value: " GPU \ngpu\nteam:Research" },
    });
    expect(fixture.store.snapshot().generation).toBeGreaterThan(generation);
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft repository" }),
    );
    expect(fixture.store.snapshot().prepared?.editable.repositories).toEqual([
        { ...complete, tags: ["gpu", "team:research"] },
    ]);
    expect(fixture.store.snapshot().editing).toBe(false);
    expect(fixture.posts()).toHaveLength(1); // Only explicit validation, no job.
    expect(window.localStorage.getItem("hfcache.operations.v1")).toBeNull();
});

test("new model and dataset entries retain separate defaults, and removal is only local reviewed intent", async () => {
    const fixture = mount();
    await fixture.loaded();
    for (const type of ["Model", "Dataset"]) {
        await userEvent.click(
            screen.getByRole("button", { name: "Add repository" }),
        );
        await userEvent.click(screen.getByRole("radio", { name: type }));
        fireEvent.change(screen.getByLabelText("Repository ID"), {
            target: { value: "owned/shared" },
        });
        await userEvent.click(
            screen.getByRole("button", { name: "Update draft repository" }),
        );
    }
    expect(
        fixture.store.snapshot().prepared?.editable.repositories.slice(1),
    ).toEqual(
        ["model", "dataset"].map((type) => ({
            type,
            id: "owned/shared",
            revision: "main",
            enabled: true,
            tags: [],
            declared_dependencies: [],
        })),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Remove model owned/shared" }),
    );
    expect(fixture.store.snapshot().prepared?.managed.edits).toEqual([
        {
            kind: "repository-upsert",
            repository: {
                type: "dataset",
                id: "owned/shared",
                revision: "main",
                enabled: true,
                tags: [],
                declared_dependencies: [],
            },
        },
    ]);
    expect(fixture.posts()).toEqual([]);
});

test("all global settings use the supported typed projection, invalid numbers preserve the prior draft", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit global settings" }),
    );
    const form = screen.getByRole("form", { name: "Global settings draft" });
    expect(within(form).getByLabelText("Dependency policy")).toHaveValue(
        "warn",
    );
    expect(
        within(form).getByLabelText("Continue after repository error"),
    ).toBeChecked();
    fireEvent.change(within(form).getByLabelText("Maximum sync workers"), {
        target: { value: "1.0" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft settings" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("exact whole numbers");
    expect(fixture.store.snapshot().prepared?.dirty).toBe(false);
    fireEvent.change(within(form).getByLabelText("Maximum sync workers"), {
        target: { value: "8" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft settings" }),
    );
    expect(fixture.store.snapshot().prepared?.managed.edits).toEqual([
        { kind: "settings-replace", settings: { sync: { max_workers: 8 } } },
    ]);
    expect(fixture.store.snapshot().prepared?.editable.repositories).toEqual(
        base().editable.repositories,
    );
    expect(fixture.container.querySelector("select,[style]")).toBeNull();
});

test("global choice and boolean controls commit typed settings without dropping complete repositories", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit global settings" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Publication mode: Hardlink" }),
    );
    await userEvent.click(screen.getByRole("option", { name: "Copy" }));
    await userEvent.click(
        screen.getByRole("button", { name: "Maximum retained revisions: 3" }),
    );
    await userEvent.click(screen.getByRole("option", { name: "5" }));
    await userEvent.click(
        screen.getByLabelText("Continue after repository error"),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft settings" }),
    );
    expect(fixture.store.snapshot().prepared?.managed.edits).toEqual([
        {
            kind: "settings-replace",
            settings: {
                storage: { publication_mode: "copy", maximum_revisions: 5 },
                sync: { continue_on_repository_error: false },
            },
        },
    ]);
    expect(fixture.store.snapshot().prepared?.editable.repositories).toEqual(
        base().editable.repositories,
    );
    expect(fixture.posts()).toEqual([]);
});

test("revision, enabled and complete dependency form fields are retained in the exact reviewed upsert", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Edit model organization/model-name",
        }),
    );
    fireEvent.change(screen.getByLabelText("Requested revision"), {
        target: { value: "release/v3" },
    });
    await userEvent.click(screen.getByLabelText("Enabled"));
    fireEvent.change(
        screen.getByLabelText("Declared dependencies (one per line)"),
        { target: { value: "owned/a\nowned/b" } },
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft repository" }),
    );
    expect(fixture.store.snapshot().prepared?.editable.repositories[0]).toEqual(
        {
            ...base().editable.repositories[0],
            revision: "release/v3",
            enabled: false,
            declared_dependencies: ["owned/a", "owned/b"],
        },
    );
    expect(fixture.posts()).toEqual([]);
});

test.each(["domain", "malformed", "offline"] as const)(
    "%s initial evidence failure remains explicit without an editable empty configuration",
    async (readFailure) => {
        const fixture = mount({ readFailure });
        await userEvent.click(
            screen.getByRole("button", {
                name: "Read installed configuration",
            }),
        );
        await waitFor(() => {
            expect(fixture.store.snapshot().phase).toBe("unavailable");
        });
        expect(screen.getByRole("alert")).toHaveTextContent(
            "Configuration evidence failed",
        );
        expect(
            screen.queryByRole("button", { name: "Add repository" }),
        ).not.toBeInTheDocument();
        expect(
            screen.queryByText(/Private original detail/u),
        ).not.toBeInTheDocument();
        expect(fixture.posts()).toEqual([]);
    },
);

test("supported JSON rejects protected fields and duplicate keys without closing the raw form", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Supported JSON view" }),
    );
    const input = screen.getByLabelText("Editable configuration JSON");
    const canonical = JSON.stringify(base().editable);
    for (const bad of [
        JSON.stringify({
            ...base().editable,
            hub: { endpoint: "https://other.invalid" },
        }),
        canonical.replace(
            '"maximum_revisions":3',
            '"maximum_revisions":3,"maximum_revisions":5',
        ),
        "schema_version = 1",
    ]) {
        fireEvent.change(input, { target: { value: bad } });
        await userEvent.click(
            screen.getByRole("button", { name: "Use JSON as draft" }),
        );
        expect(
            screen.getByLabelText("Editable configuration JSON"),
        ).toHaveValue(bad);
        expect(fixture.store.snapshot().prepared?.dirty).toBe(false);
        expect(fixture.store.snapshot().editing).toBe(true);
    }
    fireEvent.change(input, {
        target: {
            value: JSON.stringify({
                ...base().editable,
                storage: { ...base().editable.storage, maximum_revisions: 5 },
            }),
        },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Use JSON as draft" }),
    );
    expect(
        screen.queryByLabelText("Editable configuration JSON"),
    ).not.toBeInTheDocument();
    expect(
        fixture.store.snapshot().prepared?.editable.storage.maximum_revisions,
    ).toBe(5);
    expect(fixture.posts()).toEqual([]);
});

test("compare preserves the original dirty base until explicit reload, and discard resets both form and draft", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Remove model organization/model-name",
        }),
    );
    fixture.install({ ...base(), base_revision: "c".repeat(64) });
    await userEvent.click(
        screen.getByRole("button", { name: "Compare installed configuration" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().comparison?.base_revision).toBe(
            "c".repeat(64),
        );
    });
    expect(fixture.store.snapshot().base?.base_revision).toBe("a".repeat(64));
    expect(fixture.store.snapshot().prepared?.editable.repositories).toEqual(
        [],
    );
    expect(
        screen.getByText(/no automatic merge or overwrite/iu),
    ).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Reload installed configuration" }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().base?.base_revision).toBe(
            "c".repeat(64),
        );
    });
    await userEvent.click(
        screen.getByRole("button", {
            name: "Edit model organization/model-name",
        }),
    );
    fireEvent.change(screen.getByLabelText("Tags (one per line)"), {
        target: { value: "unsaved" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Discard draft" }),
    );
    expect(
        screen.queryByLabelText("Tags (one per line)"),
    ).not.toBeInTheDocument();
    expect(fixture.store.snapshot().dirty).toBe(false);
    expect(fixture.store.snapshot().prepared?.editable.repositories).toEqual(
        base().editable.repositories,
    );
});

test("stale validation exposes its code and comparison path without manufacturing an Apply", async () => {
    const fixture = mount({ validationConflict: true });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Validate draft" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("HFAPI007");
    expect(screen.getByRole("alert")).toHaveTextContent("no automatic merge");
    expect(
        screen.getByRole("button", { name: "Preview sizing" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Apply reviewed changes" }),
    ).toBeDisabled();
    expect(
        screen.queryByText(/Private service detail/u),
    ).not.toBeInTheDocument();
});

test("historical intent starts defaults with empty tags and only current configured values are editable", async () => {
    const fixture = mount();
    act(() => {
        fixture.store.setIntent({
            repositoryType: "dataset",
            repositoryId: "owned/historical",
            historical: true,
        });
    });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit requested repository" }),
    );
    expect(screen.getByLabelText("Repository ID")).toHaveValue(
        "owned/historical",
    );
    expect(screen.getByRole("radio", { name: "Dataset" })).toBeChecked();
    expect(screen.getByLabelText("Tags (one per line)")).toHaveValue("");
    expect(screen.getByLabelText("Requested revision")).toHaveValue("main");
    expect(
        screen.getByText(/Historical tags were not copied/u),
    ).toBeInTheDocument();
});

test("opt-in suggestions are bounded current-base tags, not historical or hidden reads", async () => {
    const original = base();
    const template = original.editable.repositories[0];
    if (template === undefined) throw new Error("Missing owned repository.");
    const tags = Array.from(
        { length: 64 },
        (_, index) => "current-" + String(index),
    ).sort();
    const fixture = mount({
        installed: {
            ...original,
            editable: {
                ...original.editable,
                repositories: [
                    { ...template, tags },
                    {
                        ...template,
                        type: "dataset",
                        id: "owned/other",
                        tags: ["additional-current-tag"],
                    },
                ],
            },
        },
    });
    act(() => {
        fixture.store.setIntent({
            repositoryType: "dataset",
            repositoryId: "owned/historical",
            historical: true,
        });
    });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Edit requested repository" }),
    );
    expect(
        screen.queryByRole("region", { name: "Configured tag suggestions" }),
    ).not.toBeInTheDocument();
    const requests = fixture.fetcher.mock.calls.length;
    const generation = fixture.store.snapshot().generation;
    await userEvent.click(
        screen.getByRole("button", { name: "Show configured tag suggestions" }),
    );
    const suggestions = screen.getByRole("region", {
        name: "Configured tag suggestions",
    });
    expect(within(suggestions).getAllByRole("listitem")).toHaveLength(64);
    expect(suggestions).toHaveTextContent(
        "current configured labels, not historical catalog tags",
    );
    expect(within(suggestions).getByText("current-0")).toBeInTheDocument();
    expect(
        within(suggestions).queryByText("additional-current-tag"),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("Tags (one per line)")).toHaveValue("");
    expect(fixture.store.snapshot().generation).toBe(generation);
    expect(fixture.fetcher).toHaveBeenCalledTimes(requests);
});

test("read-only grants need no host permission, and authentication clears raw private forms", async () => {
    const readOnly = mount({ write: false });
    await readOnly.loaded();
    expect(
        screen.getByRole("button", { name: "Add repository" }),
    ).toBeDisabled();
    expect(
        screen.getByRole("button", { name: "Validate draft" }),
    ).toBeDisabled();
    readOnly.unmount();
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Edit model organization/model-name",
        }),
    );
    fireEvent.change(screen.getByLabelText("Tags (one per line)"), {
        target: { value: "private-unsaved-tag" },
    });
    act(() => {
        fixture.controller.disconnect();
    });
    expect(
        screen.queryByLabelText("Tags (one per line)"),
    ).not.toBeInTheDocument();
    expect(fixture.store.snapshot().base).toBeNull();
    expect(JSON.stringify(window.localStorage)).not.toContain(
        "private-unsaved-tag",
    );
});

test("repository and reviewed-diff pages render at most25 rows without reading more configuration", async () => {
    const original = base();
    const template = original.editable.repositories[0];
    if (template === undefined) throw new Error("Missing owned repository.");
    const repositories = Array.from({ length: 26 }, (_, index) => ({
        ...template,
        id: "owned/row-" + String(index),
        enabled: false,
    }));
    const fixture = mount({
        installed: {
            ...original,
            editable: { ...original.editable, repositories },
        },
    });
    await fixture.loaded();
    expect(
        screen.getAllByRole("button", { name: /^Edit model owned\/row-/u }),
    ).toHaveLength(25);
    await userEvent.click(
        screen.getByRole("button", { name: "Next repositories" }),
    );
    expect(
        screen.getAllByRole("button", { name: /^Edit model owned\/row-/u }),
    ).toHaveLength(1);
    expect(
        screen.getByRole("button", { name: "Edit model owned/row-25" }),
    ).toBeInTheDocument();
    await userEvent.click(
        screen.getByRole("button", { name: "Supported JSON view" }),
    );
    fireEvent.change(screen.getByLabelText("Editable configuration JSON"), {
        target: {
            value: JSON.stringify({ ...original.editable, repositories: [] }),
        },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Use JSON as draft" }),
    );
    expect(
        fixture.container.querySelectorAll(".configuration-diff"),
    ).toHaveLength(25);
    await userEvent.click(screen.getByRole("button", { name: "Next changes" }));
    expect(
        fixture.container.querySelectorAll(".configuration-diff"),
    ).toHaveLength(1);
    await userEvent.click(
        screen.getByRole("button", { name: "Previous changes" }),
    );
    expect(
        fixture.container.querySelectorAll(".configuration-diff"),
    ).toHaveLength(25);
    expect(fixture.fetcher).toHaveBeenCalledTimes(1);
});

test("shared capacity refusal keeps the last admitted raw JSON buffer and leaves Apply unavailable", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Supported JSON view" }),
    );
    const input = screen.getByLabelText("Editable configuration JSON");
    const before = input instanceof HTMLTextAreaElement ? input.value : null;
    const chunk = "x".repeat(8 * 1024 * 1024 - 4);
    for (let index = 0; index < 3; index++)
        expect(fixture.controller.createPrivateSlot().set(chunk)).toBe(true);
    expect(
        fixture.controller.createPrivateSlot().set("x".repeat(7 * 1024 * 1024)),
    ).toBe(true);
    fireEvent.change(input, { target: { value: " ".repeat(1536 * 1024) } });
    expect(input).toHaveValue(before);
    expect(screen.getByRole("alert")).toHaveTextContent(
        "supported draft limit",
    );
    expect(
        screen.getByRole("button", { name: "Apply reviewed changes" }),
    ).toBeDisabled();
    expect(fixture.posts()).toEqual([]);
});

test("bounded invalid fields and duplicate Add cannot reset an existing complete entry", async () => {
    const fixture = mount();
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Add repository" }),
    );
    const identifier = screen.getByLabelText("Repository ID");
    fireEvent.change(identifier, { target: { value: "owned/new" } });
    fireEvent.change(identifier, { target: { value: "x".repeat(194) } });
    expect(identifier).toHaveValue("owned/new");
    expect(screen.getByRole("alert")).toHaveTextContent("editing limit");
    fireEvent.change(identifier, {
        target: { value: "organization/model-name" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft repository" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("already configured");
    expect(fixture.store.snapshot().prepared?.editable).toEqual(
        base().editable,
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Cancel form edits" }),
    );
    expect(screen.queryByLabelText("Repository ID")).not.toBeInTheDocument();
    expect(fixture.store.snapshot().dirty).toBe(false);
});

test("a nonempty original sizing preview shows exact repository metrics before Apply", async () => {
    const fixture = mount({ requiredScope: true });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Add repository" }),
    );
    fireEvent.change(screen.getByLabelText("Repository ID"), {
        target: { value: "owned/new" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Update draft repository" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Validate draft" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Preview sizing" }),
        ).toBeEnabled();
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Preview sizing" }),
    );
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Apply reviewed changes" }),
        ).toBeEnabled();
    });
    expect(
        screen.getByText("8".repeat(40), { selector: "code" }),
    ).toBeInTheDocument();
    expect(
        screen.getByText("Estimated new bytes").nextElementSibling,
    ).toHaveTextContent("7");
    expect(
        screen.getByText("Files", { selector: "dt" }).nextElementSibling,
    ).toHaveTextContent("2");
    expect(fixture.posts().map(([input]) => pathOf(input))).toEqual([
        "/api/v1/config/validate",
        "/api/v1/plans",
    ]);
});

test.each([
    ["confirmed", false, false],
    ["confirmed", false, true],
    ["confirmed", true, false],
    ["installed_unconfirmed", true, false],
    ["unknown", false, false],
] as const)(
    "actual typed original outcome %s pending=%s with readFailure=%s never promotes receipt success alone",
    async (outcomeState, outcomePending, failAfterOutcomeRead) => {
        const fixture = mount({
            outcomeState,
            outcomePending,
            failAfterOutcomeRead,
        });
        await fixture.loaded();
        await userEvent.click(
            screen.getByRole("button", { name: "Validate draft" }),
        );
        await waitFor(() => {
            expect(
                screen.getByRole("button", { name: "Preview sizing" }),
            ).toBeEnabled();
        });
        await userEvent.click(
            screen.getByRole("button", { name: "Preview sizing" }),
        );
        await waitFor(() => {
            expect(
                screen.getByRole("button", { name: "Apply reviewed changes" }),
            ).toBeEnabled();
        });
        await userEvent.click(
            screen.getByRole("button", { name: "Apply reviewed changes" }),
        );
        await waitFor(() => {
            expect(
                fixture.store.snapshot().applicationObservation?.receipt?.state,
            ).toBe("succeeded");
        });
        expect(
            screen.queryByText(/Installed configuration confirmed\./u),
        ).not.toBeInTheDocument();
        await userEvent.click(
            screen.getByRole("button", {
                name: "Observe original application outcome",
            }),
        );
        await waitFor(() => {
            expect(fixture.store.snapshot().outcome?.kind).toBe("outcome");
        });
        if (outcomeState === "confirmed" && !outcomePending)
            expect(
                await screen.findByText(
                    /The exact host outcome is independent/u,
                ),
            ).toBeInTheDocument();
        else
            expect(
                await screen.findByText(
                    /Installation is not confirmed\. Preserve original handles/u,
                ),
            ).toBeInTheDocument();
        if (failAfterOutcomeRead) {
            await waitFor(() => {
                expect(fixture.store.snapshot().phase).toBe("unavailable");
            });
            expect(
                screen.getByText(/The exact host outcome is independent/u),
            ).toBeInTheDocument();
            expect(
                screen.getByRole("heading", {
                    name: "Original configuration application",
                }),
            ).toBeInTheDocument();
            expect(screen.getByRole("alert")).toHaveTextContent("HFAPI005");
        }
        expect(fixture.posts().map(([input]) => pathOf(input))).toEqual([
            "/api/v1/config/validate",
            "/api/v1/plans",
            "/api/v1/config/applications",
        ]);
    },
);
