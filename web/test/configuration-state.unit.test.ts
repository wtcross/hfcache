/** Real store/controller/typed HTTP composition; installed host effects remain separate. */
import { readFileSync } from "node:fs";
import { afterEach, expect, test, vi } from "vitest";
import { createConfigurationStore } from "../src/configuration/configuration-state";
import { createSessionController } from "../src/state/session-controller";
import { decodeConfigRead } from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";
import { isRecord } from "../src/wire/runtime";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import { deferred, operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const raw: unknown = JSON.parse(
    readFileSync(
        new URL("../../tests/fixtures/web_wire/config.json", import.meta.url),
        "utf8",
    ),
);
if (!isRecord(raw)) throw new Error("Independent config fixture unavailable");
const fixtures = raw;
const config = decodeConfigRead(parseWireJson(JSON.stringify(fixtures.read)));
const planId = "a".repeat(32),
    applyId = "b".repeat(32);
const cleanups: (() => void)[] = [];
afterEach(() => {
    for (const cleanup of cleanups.splice(0)) cleanup();
    vi.unstubAllGlobals();
});
function setup(fetcher: typeof fetch, read = true, write = true) {
    const original = uiBootstrapFixture();
    const bootstrap = {
        ...original,
        configured_archive_id: ARCHIVE_ID,
        user: {
            ...original.user,
            admin_permissions: original.user.admin_permissions.map(
                (permission) => {
                    const effective =
                        permission.capability === "config-read"
                            ? read
                            : permission.capability === "config-write"
                              ? write
                              : false;
                    return {
                        ...permission,
                        granted: effective,
                        effective,
                        reason: effective
                            ? ("allowed" as const)
                            : ("not_granted" as const),
                    };
                },
            ),
        },
    };
    let saved: string | null = null;
    const controller = createSessionController({
        bootstrap,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
        storage: {
            getItem: () => saved,
            setItem: (_key, value) => {
                saved = value;
            },
        },
    });
    const store = createConfigurationStore(controller);
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    return { store, controller };
}
function urlOf(url: RequestInfo | URL) {
    return new URL(url instanceof Request ? url.url : String(url));
}
function configReadResponse(data: unknown) {
    return {
        ...operationResponse("config read", data),
        config_fingerprint: null,
    };
}
function queued(id: string) {
    return receipt({
        operation_id: id,
        route: id === planId ? "/api/v1/plans" : "/api/v1/config/applications",
        state: "queued",
        domain_run_id: null,
    });
}
function complete(id: string) {
    return receipt({
        operation_id: id,
        route: id === planId ? "/api/v1/plans" : "/api/v1/config/applications",
        state: "succeeded",
        completed_at: "2026-10-20T12:00:02.000000Z",
        updated_at: "2026-10-20T12:00:02.000000Z",
        result_recorded: true,
    });
}
function accepted(id: string) {
    const status = "/api/v1/operations/" + id;
    return new Response(
        JSON.stringify({
            schema_version: 1,
            request_id: "f".repeat(32),
            archive_id: ARCHIVE_ID,
            config_fingerprint: "2".repeat(64),
            created: true,
            operation: queued(id),
            links: {
                status,
                result: status + "/result",
                events: status + "/events",
            },
        }),
        {
            status: 202,
            headers: { "Content-Type": "application/json", Location: status },
        },
    );
}
function transport(assessment: unknown = fixtures.assessment) {
    const outcome = isRecord(fixtures.application_outcome)
        ? { ...fixtures.application_outcome, operation_id: applyId }
        : null;
    const respond = (value: unknown) => Promise.resolve(jsonResponse(value));
    return vi.fn<typeof fetch>((url, options) => {
        const path = urlOf(url).pathname;
        if (path === "/api/v1/config")
            return respond(configReadResponse(config));
        if (path === "/api/v1/config/validate")
            return respond(
                operationResponse("config validate", fixtures.validation),
            );
        if (path === "/api/v1/plans" && options?.method === "POST")
            return Promise.resolve(accepted(planId));
        if (
            path === "/api/v1/config/applications" &&
            options?.method === "POST"
        )
            return Promise.resolve(accepted(applyId));
        if (path === "/api/v1/operations/lookup")
            return respond(
                operationResponse("operations lookup", {
                    operation: complete(applyId),
                }),
            );
        if (path.endsWith("/" + planId + "/result"))
            return respond(operationResponse("plan", assessment));
        if (
            path.endsWith("/" + applyId + "/result") ||
            path.endsWith("/applications/" + applyId)
        )
            return respond(
                operationResponse(
                    path.includes("/applications/")
                        ? "config outcome"
                        : "config apply",
                    outcome,
                ),
            );
        if (path.endsWith("/" + planId))
            return respond(
                operationResponse("operations show", {
                    operation: complete(planId),
                }),
            );
        if (path.endsWith("/" + applyId))
            return respond(
                operationResponse("operations show", {
                    operation: complete(applyId),
                }),
            );
        throw new Error("Unexpected configuration test request " + path);
    });
}
test("constructing or denied configuration never reads; independent read works without host/write", async () => {
    const fetcher = transport();
    const denied = setup(fetcher, false, false);
    expect(fetcher).not.toHaveBeenCalled();
    await denied.store.load();
    expect(fetcher).not.toHaveBeenCalled();
    const { store } = setup(fetcher, true, false);
    await store.load();
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(store.snapshot().canEdit).toBe(false);
    await store.validate();
    expect(fetcher).toHaveBeenCalledTimes(1);
});
test("every raw edit retires validation; late reply cannot restore readiness or overwrite the draft", async () => {
    const late = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>((url) =>
        urlOf(url).pathname === "/api/v1/config/validate"
            ? late.promise
            : Promise.resolve(jsonResponse(configReadResponse(config))),
    );
    const { store } = setup(fetcher);
    await store.load();
    const pending = store.validate();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    expect(store.setEditing(true, { tags: "unfinished" })).toBe(true);
    late.resolve(
        jsonResponse(operationResponse("config validate", fixtures.validation)),
    );
    await pending;
    expect(store.snapshot().validation).toBeNull();
    expect(store.snapshot().dirty).toBe(true);
    expect(store.snapshot().canApply).toBe(false);
    expect(store.snapshot().canPreview).toBe(false);
    expect(store.snapshot().pending).toBeNull();
});
test("fresh compare preserves exact original base and draft; only explicit reload replaces it", async () => {
    let reads = 0;
    const newer = { ...config, base_revision: "d".repeat(64) };
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(
            jsonResponse(configReadResponse(++reads === 1 ? config : newer)),
        ),
    );
    const { store } = setup(fetcher);
    await store.load();
    store.replaceEditable({
        ...config.editable,
        sync: { ...config.editable.sync, max_workers: 3 },
    });
    await store.compare();
    expect(store.snapshot().comparison?.base_revision).toBe(
        newer.base_revision,
    );
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(store.snapshot().prepared?.editable.sync.max_workers).toBe(3);
    await store.load();
    expect(fetcher).toHaveBeenCalledTimes(2);
    const reviewed = store.reviewReload();
    if (reviewed === null) throw new Error("Missing reload review");
    await store.reload(reviewed);
    expect(store.snapshot().base?.base_revision).toBe(newer.base_revision);
    expect(store.snapshot().dirty).toBe(false);
});
test("a fresh different installed base retires an otherwise ready original preview without changing the reviewed draft", async () => {
    let reads = 0;
    const ordinary = transport();
    const newer = { ...config, base_revision: "d".repeat(64) };
    const fetcher = vi.fn<typeof fetch>((url, options) =>
        urlOf(url).pathname === "/api/v1/config"
            ? Promise.resolve(
                  jsonResponse(
                      configReadResponse(++reads === 1 ? config : newer),
                  ),
              )
            : ordinary(url, options),
    );
    const { store } = setup(fetcher);
    await store.load();
    expect(
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        }),
    ).toBe(true);
    await store.validate();
    await store.preview();
    await vi.waitFor(() => {
        expect(store.snapshot().canApply).toBe(true);
    });
    const reviewed = store.snapshot().prepared;
    await store.compare();
    expect(store.snapshot().comparison?.base_revision).toBe(
        newer.base_revision,
    );
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(store.snapshot().prepared).toBe(reviewed);
    expect(store.snapshot().dirty).toBe(true);
    expect(store.snapshot().validation).toBeNull();
    expect(store.snapshot().assessment).toBeNull();
    expect(store.snapshot().canPreview).toBe(false);
    expect(store.snapshot().canApply).toBe(false);
    expect(store.snapshot().pending).toBeNull();
});
test("typed Envelope/API refusals stay failures and do not become an empty editable document", async () => {
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(jsonResponse(problemWire(), 409)),
    );
    const { store } = setup(fetcher);
    await store.load();
    expect(store.snapshot().phase).toBe("unavailable");
    expect(store.snapshot().readResult?.kind).toBe("api_problem");
    expect(store.snapshot().prepared).toBeNull();
    expect(store.snapshot().canValidate).toBe(false);
});
test("complete original preview grants one exact Apply; repeated clicks cannot produce another POST", async () => {
    const fetcher = transport();
    const { store } = setup(fetcher);
    await store.load();
    expect(
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        }),
    ).toBe(true);
    await store.validate();
    await store.preview();
    await vi.waitFor(() => {
        expect(store.snapshot().canApply).toBe(true);
    });
    const managed = store.snapshot().prepared?.managed;
    await Promise.all([store.apply(), store.apply()]);
    const applications = fetcher.mock.calls.filter(
        ([url, options]) =>
            urlOf(url).pathname === "/api/v1/config/applications" &&
            options?.method === "POST",
    );
    expect(applications).toHaveLength(1);
    const encoded = applications[0]?.[1]?.body;
    if (typeof encoded !== "string")
        throw new Error("Missing application JSON");
    const body: unknown = JSON.parse(encoded);
    expect(body).toMatchObject({ managed, preview: { operation_id: planId } });
    expect(store.snapshot().canApply).toBe(false);
    await vi.waitFor(() => {
        expect(store.snapshot().applicationObservation?.result?.kind).toBe(
            "success",
        );
    });
    await store.observeOutcome();
    expect(store.snapshot().notice).toContain(
        "Installed configuration confirmed",
    );
    expect(
        fetcher.mock.calls.filter(([, options]) => options?.method === "POST"),
    ).toHaveLength(3);
});
test("wrong or incomplete original assessment cannot authorize Apply", async () => {
    const bad = isRecord(fixtures.assessment)
        ? { ...fixtures.assessment, complete: false }
        : null;
    const { store } = setup(transport(bad));
    await store.load();
    await store.validate();
    await store.preview();
    await vi.waitFor(() => {
        expect(store.snapshot().previewObservation?.result).not.toBeNull();
    });
    expect(store.snapshot().assessment).toBeNull();
    expect(store.snapshot().canApply).toBe(false);
});
test("capacity refusal preserves admitted draft and auth loss clears private values but not original registry", async () => {
    const { store, controller } = setup(transport());
    await store.load();
    expect(store.setEditing(true, "x".repeat(2 * 1024 * 1024 + 1))).toBe(false);
    expect(store.snapshot().prepared?.editable).toEqual(config.editable);
    expect(store.snapshot().canApply).toBe(false);
    controller.disconnect();
    expect(store.snapshot().base).toBeNull();
    expect(store.snapshot().prepared).toBeNull();
    expect(store.snapshot().dirty).toBe(false);
});

test("editing during original preview admission preserves its handle without stranding pending or accepting old readiness", async () => {
    const acceptedLater = deferred<Response>();
    const ordinary = transport();
    const fetcher = vi.fn<typeof fetch>((url, options) =>
        urlOf(url).pathname === "/api/v1/plans" && options?.method === "POST"
            ? acceptedLater.promise
            : ordinary(url, options),
    );
    const { store, controller } = setup(fetcher);
    await store.load();
    await store.validate();
    const pending = store.preview();
    await vi.waitFor(() => {
        expect(controller.snapshot().pendingSubmission).toBe(true);
    });
    expect(
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 5 },
        }),
    ).toBe(true);
    expect(store.snapshot().pending).toBeNull();
    acceptedLater.resolve(accepted(planId));
    await pending;
    await vi.waitFor(() => {
        expect(
            controller.snapshot().registry.records[0]?.handles.operationId,
        ).toBe(planId);
    });
    expect(store.snapshot().prepared?.editable.sync.max_workers).toBe(5);
    expect(store.snapshot().validation).toBeNull();
    expect(store.snapshot().assessment).toBeNull();
    expect(store.snapshot().canApply).toBe(false);
    expect(store.snapshot().pending).toBeNull();
    expect(
        fetcher.mock.calls.filter(
            ([url, options]) =>
                urlOf(url).pathname === "/api/v1/plans" &&
                options?.method === "POST",
        ),
    ).toHaveLength(1);
});

test("confirmation of an admitted application preserves a newer draft and its original base without reloading", async () => {
    const acceptedLater = deferred<Response>();
    const ordinary = transport();
    const fetcher = vi.fn<typeof fetch>((url, options) =>
        urlOf(url).pathname === "/api/v1/config/applications" &&
        options?.method === "POST"
            ? acceptedLater.promise
            : ordinary(url, options),
    );
    const { store } = setup(fetcher);
    await store.load();
    store.replaceEditable({
        ...config.editable,
        sync: { ...config.editable.sync, max_workers: 3 },
    });
    await store.validate();
    await store.preview();
    await vi.waitFor(() => {
        expect(store.snapshot().canApply).toBe(true);
    });
    const pending = store.apply();
    expect(store.snapshot().pending).toBe("apply");
    expect(
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 5 },
        }),
    ).toBe(true);
    acceptedLater.resolve(accepted(applyId));
    await pending;
    await vi.waitFor(() => {
        expect(store.snapshot().applicationObservation?.result?.kind).toBe(
            "success",
        );
    });
    await store.observeOutcome();
    expect(store.snapshot().notice).toContain("Your newer draft is preserved");
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(store.snapshot().prepared?.editable.sync.max_workers).toBe(5);
    expect(store.snapshot().dirty).toBe(true);
    expect(store.snapshot().pending).toBeNull();
    expect(
        fetcher.mock.calls.filter(
            ([url]) => urlOf(url).pathname === "/api/v1/config",
        ),
    ).toHaveLength(1);
});

test("a throwing subscriber cannot strand initial read or interrupt the owned load lifecycle", async () => {
    const fetcher = transport();
    const { store } = setup(fetcher);
    store.subscribe(() => {
        throw new Error("Detached view failed");
    });
    await store.load();
    expect(store.snapshot().phase).toBe("ready");
    expect(store.snapshot().pending).toBeNull();
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(fetcher).toHaveBeenCalledTimes(1);
});

test("comparison capacity refusal preserves only the last admitted comparison and original draft", async () => {
    const later = deferred<Response>();
    let reads = 0;
    const fetcher = vi.fn<typeof fetch>(() =>
        ++reads === 1
            ? Promise.resolve(jsonResponse(configReadResponse(config)))
            : later.promise,
    );
    const { store, controller } = setup(fetcher);
    await store.load();
    const compared = store.compare();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    // The in-flight read owns its reservation; these drafts leave room for that
    // response, but not a second private copy of the large new comparison.
    const held = Array.from({ length: 3 }, () =>
        controller.createPrivateSlot(),
    );
    const chunk = "x".repeat(31 * 256 * 1024 - 2);
    for (const slot of held) expect(slot.set(chunk)).toBe(true);
    const tags = Array.from(
        { length: 64 },
        (_, index) => "tag-" + String(index).padStart(3, "0") + "x".repeat(57),
    );
    const large = {
        ...config,
        base_revision: "d".repeat(64),
        editable: {
            ...config.editable,
            repositories: Array.from({ length: 1280 }, (_, index) => ({
                type: "model",
                id: "owned/entry-" + String(index),
                revision: "main",
                enabled: false,
                tags,
                declared_dependencies: [],
            })),
        },
    };
    const checked = decodeConfigRead(parseWireJson(JSON.stringify(large)));
    expect(checked.editable.repositories).toHaveLength(1280);
    later.resolve(jsonResponse(configReadResponse(large)));
    await compared;
    expect(store.snapshot().notice).toContain("capacity is unavailable");
    expect(store.snapshot().comparison).toBeNull();
    expect(store.snapshot().base?.base_revision).toBe(config.base_revision);
    expect(store.snapshot().prepared?.editable).toEqual(config.editable);
    expect(store.snapshot().pending).toBeNull();
    for (const slot of held) slot.clear();
});

test.each(["base_revision", "candidate_revision"] as const)(
    "a complete preview with another %s cannot qualify the local draft",
    async (field) => {
        const changed = isRecord(fixtures.assessment)
            ? { ...fixtures.assessment, [field]: "d".repeat(64) }
            : null;
        const { store } = setup(transport(changed));
        await store.load();
        await store.validate();
        await store.preview();
        await vi.waitFor(() => {
            expect(store.snapshot().previewObservation?.result).not.toBeNull();
        });
        expect(store.snapshot().assessment).toBeNull();
        expect(store.snapshot().canApply).toBe(false);
        expect(store.snapshot().notice).toContain(
            "required configuration proof",
        );
    },
);

test("a real failed preview result and failed receipt remain failure evidence, never Apply readiness", async () => {
    const ordinary = transport();
    const assessment = isRecord(fixtures.assessment)
        ? { ...fixtures.assessment, complete: false }
        : null;
    const fetcher = vi.fn<typeof fetch>((url, options) => {
        const path = urlOf(url).pathname;
        if (path.endsWith("/" + planId + "/result"))
            return Promise.resolve(
                jsonResponse(operationResponse("plan", assessment, true)),
            );
        if (path.endsWith("/" + planId))
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations show", {
                        operation: { ...complete(planId), state: "failed" },
                    }),
                ),
            );
        return ordinary(url, options);
    });
    const { store } = setup(fetcher);
    await store.load();
    await store.validate();
    await store.preview();
    await vi.waitFor(() => {
        expect(store.snapshot().previewObservation?.result?.kind).toBe(
            "domain_failure",
        );
    });
    expect(store.snapshot().assessment).toBeNull();
    expect(store.snapshot().canApply).toBe(false);
    expect(store.snapshot().previewObservation?.receipt?.state).toBe("failed");
    expect(
        fetcher.mock.calls.filter(
            ([url, options]) =>
                urlOf(url).pathname === "/api/v1/config/applications" &&
                options?.method === "POST",
        ),
    ).toHaveLength(0);
});

test("an old configuration load cannot repopulate private draft state after auth loss", async () => {
    const late = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>(() => late.promise);
    const { store, controller } = setup(fetcher);
    const loading = store.load();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(1);
    });
    controller.disconnect();
    late.resolve(jsonResponse(configReadResponse(config)));
    await loading;
    expect(store.snapshot().base).toBeNull();
    expect(store.snapshot().prepared).toBeNull();
    expect(store.snapshot().pending).toBeNull();
    expect(store.snapshot().phase).toBe("unavailable");
    expect(store.snapshot().canRead).toBe(false);
});

test("starting another original outcome read never labels the previous confirmed result with its new record", async () => {
    const secondLookup = deferred<Response>();
    const firstKey = "owned-first-application-key",
        secondKey = "owned-second-application-key";
    const otherId = "c".repeat(32);
    const firstOutcome = isRecord(fixtures.application_outcome)
        ? { ...fixtures.application_outcome, operation_id: applyId }
        : null;
    const fetcher = vi.fn<typeof fetch>((url, options) => {
        const path = urlOf(url).pathname;
        if (path === "/api/v1/config")
            return Promise.resolve(jsonResponse(configReadResponse(config)));
        if (path === "/api/v1/operations/lookup") {
            const key = new Headers(options?.headers).get("Idempotency-Key");
            if (key === secondKey) return secondLookup.promise;
            expect(key).toBe(firstKey);
            return Promise.resolve(
                jsonResponse(
                    operationResponse("operations lookup", {
                        operation: complete(applyId),
                    }),
                ),
            );
        }
        expect(path).toBe("/api/v1/config/applications/" + applyId);
        return Promise.resolve(
            jsonResponse(operationResponse("config outcome", firstOutcome)),
        );
    });
    const { store, controller } = setup(fetcher);
    const first = controller.importHandle({
        kind: "basic-key",
        key: firstKey,
        operationId: applyId,
        originalScope: controller.originalScope(),
    });
    const second = controller.importHandle({
        kind: "basic-key",
        key: secondKey,
        operationId: otherId,
        originalScope: controller.originalScope(),
    });
    await store.observeOutcome(first.recordId);
    expect(store.snapshot().outcomeRecordId).toBe(first.recordId);
    expect(store.snapshot().outcome).toMatchObject({
        kind: "outcome",
        result: {
            kind: "success",
            payload: { state: "confirmed", operation_id: applyId },
        },
    });
    const observing = store.observeOutcome(second.recordId);
    expect(store.snapshot().outcomeRecordId).toBe(second.recordId);
    expect(store.snapshot().pending).toBe("outcome");
    expect(store.snapshot().outcome).toBeNull();
    // A real API failure still belongs to the second original lookup; it cannot
    // resurrect the prior successful host payload beneath the second record.
    secondLookup.resolve(jsonResponse(problemWire(), 500));
    await observing;
    expect(store.snapshot().outcomeRecordId).toBe(second.recordId);
    expect(store.snapshot().outcome).toMatchObject({
        kind: "lookup",
        result: { kind: "api_problem", status: 500 },
    });
    expect(store.snapshot().pending).toBeNull();
    expect(
        controller
            .snapshot()
            .registry.records.find((row) => row.recordId === second.recordId)
            ?.handles.operationId,
    ).toBe(otherId);
});

test.each(["transport", "api", "domain", "protocol", "identity"] as const)(
    "failed same-authority reload (%s) preserves the exact base, prepared intent and admitted buffer",
    async (kind) => {
        const fetcher = transport();
        const { store } = setup(fetcher);
        await store.load();
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        });
        store.setEditing(true, { kind: "settings", raw: "003-invalid" });
        const original = store.snapshot();
        const late = deferred<Response>();
        fetcher.mockImplementationOnce(() =>
            late.promise.then((response) => {
                if (kind === "transport") throw new TypeError("Owned offline");
                return response;
            }),
        );
        const reviewed = store.reviewReload();
        if (reviewed === null) throw new Error("Missing reload review");
        const loading = store.reload(reviewed);
        expect(store.snapshot().pending).toBe("read");
        expect(store.snapshot().base).toBe(original.base);
        expect(store.snapshot().prepared).toBe(original.prepared);
        expect(store.snapshot().dirty).toBe(true);
        expect(store.snapshot().editing).toBe(true);
        expect(store.snapshot().canEdit).toBe(false);
        expect(store.setEditing(true, { raw: "newer" })).toBe(false);
        expect(store.replaceJson("{}")).toBe(false);
        expect(store.replaceEditable(config.editable)).toBe(false);
        const repository = config.editable.repositories[0];
        if (repository === undefined)
            throw new Error("Missing fixture repository");
        expect(store.upsert(repository)).toBe(false);
        expect(store.remove("model", "organization/model-name")).toBe(false);
        late.resolve(
            kind === "api"
                ? jsonResponse(problemWire(), 500)
                : kind === "domain"
                  ? jsonResponse(operationResponse("config read", {}, true))
                  : kind === "protocol"
                    ? jsonResponse({ schema_version: 99 })
                    : jsonResponse(
                          configReadResponse({
                              ...config,
                              archive_id:
                                  "00000000-0000-4000-8000-000000000000",
                          }),
                      ),
        );
        await loading;
        expect(store.snapshot().base).toBe(original.base);
        expect(store.snapshot().prepared).toBe(original.prepared);
        expect(store.snapshot().dirty).toBe(true);
        expect(store.snapshot().editing).toBe(true);
        expect(store.snapshot().pending).toBeNull();
        expect(store.snapshot().canEdit).toBe(true);
        expect(store.snapshot().editorRevision).toBe(original.editorRevision);
        expect(store.snapshot().notice).toContain("reload failed");
        expect(store.snapshot().validation).toBeNull();
        expect(store.snapshot().assessment).toBeNull();
        expect(
            fetcher.mock.calls.every(([, init]) => init?.method === "GET"),
        ).toBe(true);
    },
);

test("reload review is one-use and cannot admit a stale decision after edits, discard or authentication change", async () => {
    const fetcher = transport();
    const { store, controller } = setup(fetcher);
    await store.load();
    store.setEditing(true, { raw: "first" });
    const reviewed = store.reviewReload();
    if (reviewed === null) throw new Error("Missing reload review");
    store.setEditing(true, { raw: "newer" });
    await store.reload(reviewed);
    await store.reload();
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(store.snapshot().dirty).toBe(true);
    store.discard();
    await store.reload(reviewed);
    expect(fetcher).toHaveBeenCalledTimes(1);
    store.setEditing(true, { raw: "current" });
    const current = store.reviewReload();
    if (current === null) throw new Error("Missing reload review");
    controller.disconnect();
    await store.reload(current);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(store.snapshot().prepared).toBeNull();
});

test.each(["same", "different"] as const)(
    "successful %s-base replacement resets all draft state in one publication and increments the editor revision",
    async (kind) => {
        const fetcher = transport();
        const { store } = setup(fetcher);
        await store.load();
        store.replaceEditable({
            ...config.editable,
            sync: { ...config.editable.sync, max_workers: 3 },
        });
        store.setEditing(true, { kind: "json", text: "{ unfinished" });
        const revision = store.snapshot().editorRevision;
        const next = {
            ...config,
            base_revision:
                kind === "same" ? config.base_revision : "e".repeat(64),
        };
        fetcher.mockResolvedValueOnce(jsonResponse(configReadResponse(next)));
        const reviewed = store.reviewReload();
        if (reviewed === null) throw new Error("Missing reload review");
        const observations: ReturnType<typeof store.snapshot>[] = [];
        store.subscribe(() => observations.push(store.snapshot()));
        await store.reload(reviewed);
        expect(store.snapshot().base).toEqual(next);
        expect(store.snapshot().prepared?.editable).toEqual(config.editable);
        expect(store.snapshot().editing).toBe(false);
        expect(store.snapshot().dirty).toBe(false);
        expect(store.snapshot().editorRevision).toBe(revision + 1);
        for (const observed of observations) {
            if (observed.editorRevision > revision) {
                expect(observed.prepared?.managed.base_revision).toBe(
                    next.base_revision,
                );
                expect(observed.prepared?.editable).toEqual(config.editable);
                expect(observed.editing).toBe(false);
            }
        }
        const reads = fetcher.mock.calls.length;
        await store.reload(reviewed);
        expect(fetcher).toHaveBeenCalledTimes(reads);
    },
);

test.each(["disconnect", "dispose"] as const)(
    "late replacement after %s cannot restore private values or overwrite the invalidation notice",
    async (action) => {
        const fetcher = transport();
        const { store, controller } = setup(fetcher);
        await store.load();
        store.setEditing(true, { raw: "private" });
        const late = deferred<Response>();
        fetcher.mockImplementationOnce(() => late.promise);
        const reviewed = store.reviewReload();
        if (reviewed === null) throw new Error("Missing reload review");
        const loading = store.reload(reviewed);
        await vi.waitFor(() => {
            expect(fetcher).toHaveBeenCalledTimes(2);
        });
        if (action === "disconnect") controller.disconnect();
        else store.dispose();
        const invalidated = store.snapshot();
        late.resolve(jsonResponse(configReadResponse(config)));
        await loading;
        expect(store.snapshot()).toBe(invalidated);
        expect(store.snapshot().base).toBeNull();
        expect(store.snapshot().prepared).toBeNull();
        expect(store.snapshot().dirty).toBe(false);
        const calls = fetcher.mock.calls.length;
        await store.load();
        await store.reload();
        expect(fetcher).toHaveBeenCalledTimes(calls);
    },
);

test("replacement retention capacity refusal preserves the admitted original draft and buffer", async () => {
    const fetcher = transport();
    const { store, controller } = setup(fetcher);
    await store.load();
    store.setEditing(true, { kind: "json", text: "{ private raw" });
    const original = store.snapshot();
    const tags = Array.from(
        { length: 64 },
        (_, index) => "tag-" + String(index).padStart(3, "0") + "x".repeat(57),
    );
    const next = {
        ...config,
        base_revision: "d".repeat(64),
        editable: {
            ...config.editable,
            repositories: Array.from({ length: 430 }, (_, index) => ({
                type: "model",
                id: "owned/entry-" + String(index),
                revision: "main",
                enabled: false,
                tags,
                declared_dependencies: [],
            })),
        },
    };
    const checked = decodeConfigRead(parseWireJson(JSON.stringify(next)));
    expect(checked.editable.repositories).toHaveLength(430);
    const late = deferred<Response>();
    fetcher.mockImplementationOnce(() => late.promise);
    const reviewed = store.reviewReload();
    if (reviewed === null) throw new Error("Missing reload review");
    const loading = store.reload(reviewed);
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledTimes(2);
    });
    const held = Array.from({ length: 3 }, () =>
        controller.createPrivateSlot(),
    );
    const chunk = "x".repeat(31 * 256 * 1024 - 2);
    for (const slot of held) expect(slot.set(chunk)).toBe(true);
    late.resolve(jsonResponse(configReadResponse(next)));
    await loading;
    expect(store.snapshot().notice).toContain("reload failed");
    expect(store.snapshot().notice).toContain("capacity is unavailable");
    expect(store.snapshot().base).toBe(original.base);
    expect(store.snapshot().prepared).toBe(original.prepared);
    expect(store.snapshot().editing).toBe(true);
    expect(store.snapshot().dirty).toBe(true);
    expect(store.snapshot().editorRevision).toBe(original.editorRevision);
    expect(store.snapshot().canEdit).toBe(true);
    for (const slot of held) slot.clear();
});
