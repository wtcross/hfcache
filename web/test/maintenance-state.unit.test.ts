/** Real ApiClient/session/query composition; controlled HTTP boundaries only. */
import { afterEach, expect, test, vi } from "vitest";
import {
    buildMaintenanceIntent,
    defaultMaintenanceForm,
    parseMaintenanceForm,
} from "../src/operations/maintenance-state";
import {
    setupMaintenance,
    recoveryPayload,
    quarantinePayload,
    repairFinding,
    reference,
    manifest,
    transactionId,
} from "./maintenance-fixtures";
import type { MaintenanceFixtureOptions } from "./maintenance-fixtures";
import { jsonResponse } from "./read-fixtures";
import { operationResponse } from "./state-fixtures";
const active: ReturnType<typeof setupMaintenance>[] = [];
afterEach(() => {
    for (const f of active.splice(0)) f.dispose();
    vi.restoreAllMocks();
});
function setup(options: MaintenanceFixtureOptions = {}) {
    const f = setupMaintenance(options);
    active.push(f);
    return f;
}
async function preview(f: ReturnType<typeof setup>) {
    await f.store.preview();
    await vi.waitFor(() => {
        expect(f.store.snapshot().review).not.toBeNull();
    });
}

test.each([
    [{ kind: "prune", scope: "all", selectors: "" }, { selectors: [] }],
    [
        {
            kind: "prune",
            scope: "selected",
            selectors:
                " model:owned/model\ndataset:owned/data\nmodel:owned/model ",
        },
        { selectors: ["dataset:owned/data", "model:owned/model"] },
    ],
    [
        { kind: "purge", scope: "all_unmanaged", selectors: "" },
        { selectors: [], all_unmanaged: true },
    ],
    [
        { kind: "purge", scope: "selected", selectors: "model:owned/model" },
        { selectors: ["model:owned/model"], all_unmanaged: false },
    ],
    [{ kind: "recovery" }, {}],
    [
        {
            kind: "quarantine",
            transactionIds: transactionId + "\n" + transactionId,
        },
        { transaction_ids: [transactionId] },
    ],
] as const)(
    "paired scope %j repeats only its canonical request",
    (raw, body) => {
        const form = parseMaintenanceForm(raw),
            a = buildMaintenanceIntent(form),
            b = buildMaintenanceIntent(form, true);
        expect(a.request).toEqual(body);
        expect(b.request).toEqual(body);
        expect(a.action).toMatch(/Preview$/u);
        expect(b.action).toMatch(/Apply$/u);
    },
);
test("constructor has no reads or submission and default prune is explicit", () => {
    const f = setup();
    expect(f.fetcher).not.toHaveBeenCalled();
    expect(f.store.snapshot().form).toEqual(defaultMaintenanceForm());
    expect(f.store.snapshot().canPreview).toBe(true);
    expect(f.store.snapshot().canApply).toBe(false);
});
test.each([
    { kind: "prune", scope: "all", selectors: "model:owned/model" },
    {
        kind: "prune",
        scope: "selected",
        selectors: "model:owned/model@" + "a".repeat(40),
    },
    { kind: "purge", scope: "selected", selectors: "" },
    { kind: "purge", scope: "all_unmanaged", selectors: "dataset:owned/data" },
    { kind: "quarantine", transactionIds: "../unknown" },
    {
        kind: "quarantine",
        transactionIds: Array.from({ length: 101 }, () => transactionId).join(
            "\n",
        ),
    },
])("invalid/ambiguous scope never builds a request %j", (raw) => {
    expect(() => buildMaintenanceIntent(parseMaintenanceForm(raw))).toThrow();
});
test("closed parser refuses accessors, unknown keys and oversized raw strings without invoking them", () => {
    const getter = vi.fn();
    expect(() =>
        parseMaintenanceForm({
            get kind() {
                getter();
                return "prune";
            },
        }),
    ).toThrow();
    expect(getter).not.toHaveBeenCalled();
    expect(() =>
        parseMaintenanceForm({ kind: "recovery", apply: true }),
    ).toThrow();
    expect(() =>
        parseMaintenanceForm({
            kind: "prune",
            scope: "all",
            selectors: "x".repeat(2 * 1024 * 1024),
        }),
    ).toThrow();
});
test("a same-auth successful original preview permits explicit one-use apply even when bootstrap fingerprint is null", async () => {
    const f = setup();
    expect(f.bootstrap.config_fingerprint).toBeNull();
    await preview(f);
    const s = f.store.snapshot();
    expect(s.previewObservation?.phase).toBe("settled");
    expect(s.canConfirm).toBe(true);
    expect(s.canApply).toBe(false);
    expect(f.store.confirm(s.reviewGeneration)).toBe(true);
    expect(f.store.snapshot().canApply).toBe(true);
    await f.store.apply();
    expect(
        f.requests.filter((r) => r.method === "POST").map((r) => r.path),
    ).toEqual(["/api/v1/prune-plans", "/api/v1/prunes"]);
    expect(f.store.snapshot().confirmed).toBe(false);
    expect(f.store.snapshot().review).toBeNull();
    await f.store.apply();
    expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(2);
});
test.each(["same", "invalid", "pause", "clear"] as const)(
    "%s retires confirmation synchronously before subscribers can render it",
    async (kind) => {
        const f = setup();
        await preview(f);
        f.store.confirm(f.store.snapshot().reviewGeneration);
        const observed: boolean[] = [];
        f.store.subscribe(() => {
            observed.push(f.store.snapshot().canApply);
        });
        if (kind === "same") f.store.setForm({ ...f.store.snapshot().form });
        else if (kind === "invalid")
            f.store.setForm({ kind: "recovery", extra: true });
        else if (kind === "pause") f.store.pause();
        else f.store.clearConfirmation();
        expect(f.store.snapshot().confirmed).toBe(false);
        expect(observed.length).toBeGreaterThan(0);
        expect(observed).not.toContain(true);
        expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(1);
    },
);
test("a raw edit attempt while preview admission is pending cannot rearm late evidence or strand pending", async () => {
    const f = setup();
    const pending = f.store.preview();
    expect(f.store.snapshot().pending).toBe("preview");
    expect(f.store.setForm(defaultMaintenanceForm("recovery"))).toBe(false);
    await pending;
    await vi.waitFor(() => {
        expect(f.store.snapshot().previewObservation?.phase).toBe("settled");
    });
    expect(f.store.snapshot().pending).toBeNull();
    expect(f.store.snapshot().review).toBeNull();
    expect(f.store.snapshot().canConfirm).toBe(false);
    expect(f.controller.snapshot().registry.records).toHaveLength(1);
});
test.each(["prune", "purge", "recovery", "quarantine"] as const)(
    "empty/noop %s preview is informational and never applies",
    async (kind) => {
        const payload =
            kind === "prune"
                ? { plans: [], applied: [] }
                : kind === "purge"
                  ? { plans: [], applied: [] }
                  : kind === "recovery"
                    ? { actionable: 0, blocked: 0, plan: [] }
                    : {
                          ...quarantinePayload(),
                          plans: quarantinePayload().plans.map((p) => ({
                              ...p,
                              already_absent: true,
                          })),
                      };
        const f = setup({ payload: () => payload });
        f.store.setForm(
            kind === "quarantine"
                ? { kind, transactionIds: transactionId }
                : kind === "purge"
                  ? { kind, scope: "all_unmanaged", selectors: "" }
                  : defaultMaintenanceForm(kind),
        );
        await preview(f);
        expect(f.store.snapshot().eligibility).toBe("nothing_eligible");
        expect(f.store.snapshot().canConfirm).toBe(false);
        expect(f.store.confirm(f.store.snapshot().reviewGeneration)).toBe(
            false,
        );
        await f.store.apply();
        expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(1);
    },
);
test("blocked recovery remains visible with no confirmation", async () => {
    const f = setup({
        payload: () => ({
            actionable: 0,
            blocked: 1,
            plan: recoveryPayload().plan.map((p) => ({
                ...p,
                remedy: "operator",
            })),
        }),
    });
    f.store.setForm({ kind: "recovery" });
    await preview(f);
    expect(f.store.snapshot().eligibility).toBe("blocked");
    expect(f.store.snapshot().review?.kind).toBe("recovery");
    expect(f.store.snapshot().canConfirm).toBe(false);
});
test("out-of-scope selected plan cannot arm confirmation", async () => {
    const f = setup();
    f.store.setForm({
        kind: "prune",
        scope: "selected",
        selectors: "model:owned/other",
    });
    await f.store.preview();
    await vi.waitFor(() => {
        expect(f.store.snapshot().previewObservation?.phase).toBe("settled");
    });
    expect(f.store.snapshot().review).toBeNull();
    expect(f.store.snapshot().formIssue).toBe("scope");
});
test("quarantine refuses a missing or duplicated member instead of applying a partial batch", async () => {
    const f = setup({
        payload: () => ({
            ...quarantinePayload(),
            plans: [...quarantinePayload().plans, ...quarantinePayload().plans],
        }),
    });
    f.store.setForm({ kind: "quarantine", transactionIds: transactionId });
    await f.store.preview();
    await vi.waitFor(() => {
        expect(f.store.snapshot().previewObservation?.phase).toBe("settled");
    });
    expect(f.store.snapshot().review).toBeNull();
    expect(f.store.snapshot().canApply).toBe(false);
});
test("fresh repair proof is exact SHA ref then manifest then ref and never current", async () => {
    const f = setup();
    expect(f.store.setRepairFinding(repairFinding())).toBe(true);
    await f.store.checkRepair();
    expect(f.store.snapshot().repairProof).toBe("ready");
    expect(f.store.snapshot().freshPublicationGeneration).toBe(
        reference.publication_generation,
    );
    expect(f.store.snapshot().canConfirm).toBe(true);
    expect(f.requests.map((r) => r.path)).toEqual([
        `/api/v1/repositories/model/organization/model-name/references/${reference.commit_sha}`,
        `/api/v1/repositories/model/organization/model-name/manifests/${manifest.commit_sha}/${manifest.publication_id}`,
        `/api/v1/repositories/model/organization/model-name/references/${reference.commit_sha}`,
    ]);
    f.store.confirm(f.store.snapshot().reviewGeneration);
    await f.store.repair();
    expect(f.requests.filter((r) => r.method === "POST")[0]?.body).toEqual({
        revision: `model:organization/model-name@${manifest.commit_sha}`,
        reason: "operator_requested",
    });
    expect(f.store.snapshot().effectFinding).toEqual(repairFinding());
    expect(f.store.snapshot().confirmed).toBe(false);
});
test("a replaced exact reference refuses repair with no fallback", async () => {
    const f = setup({
        fetch: (url) =>
            url.pathname.includes("/references/")
                ? jsonResponse(
                      operationResponse("reference read", {
                          reference: {
                              ...reference,
                              publication_id: "8".repeat(32),
                              tree: reference.tree.replace(
                                  reference.publication_id,
                                  "8".repeat(32),
                              ),
                              manifest: reference.manifest.replace(
                                  reference.publication_id,
                                  "8".repeat(32),
                              ),
                          },
                          locator_base: "published/",
                      }),
                  )
                : undefined,
    });
    f.store.setRepairFinding(repairFinding());
    await f.store.checkRepair();
    expect(f.store.snapshot().repairProof).toBe("changed");
    expect(f.requests).toHaveLength(1);
    expect(f.store.snapshot().canConfirm).toBe(false);
});
test("pause preserves charged finding but retires proof and confirmation", async () => {
    const f = setup();
    f.store.setRepairFinding(repairFinding());
    await f.store.checkRepair();
    f.store.confirm(f.store.snapshot().reviewGeneration);
    f.store.pause();
    expect(f.store.snapshot().finding).toEqual(repairFinding());
    expect(f.store.snapshot().repairProof).toBe("idle");
    expect(f.store.snapshot().canRepair).toBe(false);
    expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(0);
});
test("known QueryStore invalidation retires ready repair confirmation synchronously without refetch", async () => {
    const f = setup();
    f.store.setRepairFinding(repairFinding());
    await f.store.checkRepair();
    f.store.confirm(f.store.snapshot().reviewGeneration);
    const before = f.requests.length;
    const states: boolean[] = [];
    f.store.subscribe(() => {
        states.push(f.store.snapshot().canRepair);
    });
    f.controller.queries.invalidate((d) => d.routeId === "reference_default");
    expect(f.store.snapshot().confirmed).toBe(false);
    expect(f.store.snapshot().repairProof).toBe("unavailable");
    expect(states).not.toContain(true);
    expect(f.requests).toHaveLength(before);
});
test("a disposed stale store cannot submit or reclaim its private slot while controller remains alive", async () => {
    const f = setup();
    f.store.dispose();
    expect(f.store.setForm(defaultMaintenanceForm())).toBe(false);
    expect(f.store.setRepairFinding(repairFinding())).toBe(false);
    f.store.pause();
    f.store.reset();
    await f.store.preview();
    await f.store.apply();
    await f.store.repair();
    await f.store.checkRepair();
    expect(f.fetcher).not.toHaveBeenCalled();
    const slots = Array.from({ length: 4 }, () =>
        f.controller.createPrivateSlot(),
    );
    for (const slot of slots)
        expect(slot.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    for (const slot of slots) slot.clear();
});

test.each(["preview", "apply", "repairProof"] as const)(
    "a subscriber raw edit during %s publication cannot submit unreviewed scope or start hidden reads",
    async (kind) => {
        const f = setup();
        if (kind === "apply") {
            await preview(f);
            f.store.confirm(f.store.snapshot().reviewGeneration);
        } else if (kind === "repairProof") {
            f.store.setRepairFinding(repairFinding());
        }
        const before = f.requests.length;
        let edited = false;
        f.store.subscribe(() => {
            if (!edited && f.store.snapshot().pending === kind) {
                edited = true;
                expect(
                    f.store.setForm({
                        kind: "purge",
                        scope: "all_unmanaged",
                        selectors: "",
                    }),
                ).toBe(false);
            }
        });
        if (kind === "preview") await f.store.preview();
        else if (kind === "apply") await f.store.apply();
        else await f.store.checkRepair();
        expect(edited).toBe(true);
        expect(f.requests).toHaveLength(before);
        expect(f.store.snapshot().pending).toBeNull();
        expect(f.store.snapshot().confirmed).toBe(false);
    },
);

test("capacity refusal keeps the admitted form and retires its old review", async () => {
    const f = setup();
    await preview(f);
    f.store.confirm(f.store.snapshot().reviewGeneration);
    const before = f.store.snapshot().form;
    const slots = Array.from({ length: 4 }, () =>
        f.controller.createPrivateSlot(),
    );
    for (const slot of slots.slice(0, 3))
        expect(slot.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    const last = slots[3];
    if (last === undefined) throw new Error("Missing slot");
    expect(last.set("x".repeat(8 * 1024 * 1024 - 8192))).toBe(true);
    const selector = "model:" + "n".repeat(95) + "/" + "r".repeat(95);
    expect(
        f.store.setForm({
            kind: "prune",
            scope: "selected",
            selectors: Array.from({ length: 100 }, () => selector).join("\n"),
        }),
    ).toBe(false);
    expect(f.store.snapshot().form).toEqual(before);
    expect(f.store.snapshot().formIssue).toBe("capacity");
    expect(f.store.snapshot().confirmed).toBe(false);
    expect(f.store.snapshot().review).toBeNull();
    expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(1);
    for (const slot of slots) slot.clear();
});

test("disconnect clears charged private intent and cannot publish a pending original preview as fresh evidence", async () => {
    const f = setup();
    const task = f.store.preview();
    f.controller.disconnect();
    await task;
    expect(f.store.snapshot().connected).toBe(false);
    expect(f.store.snapshot().pending).toBeNull();
    expect(f.store.snapshot().review).toBeNull();
    expect(f.store.snapshot().previewRecordId).toBeNull();
    expect(f.store.snapshot().canConfirm).toBe(false);
    expect(f.controller.snapshot().registry.records).toHaveLength(1);
    await f.store.apply();
    expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(1);
});

test("a failed original preview preserves its handle without creating a review", async () => {
    const f = setup({ failed: true });
    await f.store.preview();
    await vi.waitFor(() => {
        expect(f.store.snapshot().previewObservation?.phase).toBe("settled");
    });
    expect(f.store.snapshot().previewObservation?.receipt?.state).toBe(
        "failed",
    );
    expect(f.store.snapshot().previewRecordId).not.toBeNull();
    expect(f.store.snapshot().review).toBeNull();
    expect(f.store.snapshot().canConfirm).toBe(false);
    await f.store.apply();
    expect(f.requests.filter((r) => r.method === "POST")).toHaveLength(1);
});

test("repair rechecks the same SHA reference after manifest and refuses a concurrent publication replacement", async () => {
    let refs = 0;
    const f = setup({
        fetch: (url) => {
            if (!url.pathname.includes("/references/") || ++refs === 1)
                return undefined;
            const pub = "8".repeat(32);
            return jsonResponse(
                operationResponse("reference read", {
                    reference: {
                        ...reference,
                        publication_id: pub,
                        tree: reference.tree.replace(
                            reference.publication_id,
                            pub,
                        ),
                        manifest: reference.manifest.replace(
                            reference.publication_id,
                            pub,
                        ),
                    },
                    locator_base: "published/",
                }),
            );
        },
    });
    f.store.setRepairFinding(repairFinding());
    await f.store.checkRepair();
    expect(f.requests).toHaveLength(3);
    expect(f.store.snapshot().repairProof).toBe("changed");
    expect(f.store.snapshot().freshPublication).toBeNull();
    expect(f.store.snapshot().canRepair).toBe(false);
});

test("captured repair attribution replaces the old displayed receipt before a second admission", async () => {
    const f = setup();
    f.store.setRepairFinding(repairFinding());
    await f.store.checkRepair();
    f.store.confirm(f.store.snapshot().reviewGeneration);
    await f.store.repair();
    await vi.waitFor(() => {
        expect(f.store.snapshot().effectObservation?.phase).toBe("settled");
    });
    const old = f.store.snapshot().effectRecordId;
    const next = {
        ...repairFinding(),
        finding: { ...repairFinding().finding, path: "weights.bin" },
    };
    f.store.setRepairFinding(next);
    await f.store.checkRepair();
    f.store.confirm(f.store.snapshot().reviewGeneration);
    const samples: unknown[] = [];
    f.store.subscribe(() => {
        const s = f.store.snapshot();
        if (s.pending === "apply")
            samples.push({
                id: s.effectRecordId,
                path: s.effectFinding?.finding.path,
            });
    });
    await f.store.repair();
    expect(samples.length).toBeGreaterThan(0);
    expect(samples).not.toContainEqual({ id: old, path: "weights.bin" });
    expect(samples[0]).toEqual({ id: null, path: "weights.bin" });
    expect(f.store.snapshot().effectRecordId).not.toBe(old);
});
