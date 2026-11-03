/** Actual typed client/session/store composition; no installed-domain effect claim. */
import { afterEach, expect, test, vi } from "vitest";
import {
    buildJobIntent,
    createJobsStore,
    defaultJobForm,
    describeJob,
    MAX_CANDIDATE_FILE_BYTES,
    parseJobForm,
} from "../src/operations/jobs-state";
import { createSessionController } from "../src/state/session-controller";
import { ARCHIVE_ID, jsonResponse, problemWire } from "./read-fixtures";
import { deferred, operationResponse, receipt } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";

const cleanups: (() => void)[] = [];
afterEach(() => {
    for (const cleanup of cleanups.splice(0)) cleanup();
    vi.restoreAllMocks();
});
const sha = "b".repeat(40),
    run = "c".repeat(32),
    operationId = "a".repeat(32);
const plan = () => defaultJobForm();
function setup(
    fetcher: typeof fetch = vi
        .fn<typeof fetch>()
        .mockResolvedValue(jsonResponse(problemWire(), 403)),
) {
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    const storage = new Map<string, string>();
    const controller = createSessionController({
        bootstrap,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
        storage: {
            getItem: (key) => storage.get(key) ?? null,
            setItem: (key, value) => {
                storage.set(key, value);
            },
        },
    });
    const store = createJobsStore(controller);
    cleanups.push(() => {
        store.dispose();
        controller.dispose();
    });
    return { store, controller, storage };
}
function urlOf(input: RequestInfo | URL) {
    return new URL(
        typeof input === "string"
            ? input
            : input instanceof URL
              ? input.href
              : input.url,
    );
}
function accepted(route: string) {
    const status = "/api/v1/operations/" + operationId;
    return new Response(
        JSON.stringify({
            schema_version: 1,
            request_id: "f".repeat(32),
            archive_id: ARCHIVE_ID,
            config_fingerprint: "2".repeat(64),
            created: true,
            operation: receipt({ route, state: "queued", domain_run_id: null }),
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

test.each([
    [
        { kind: "sync", scope: "all", selectors: "" },
        { action: "sync", request: { selectors: [] } },
    ],
    [
        {
            kind: "installedPlan",
            scope: "selected",
            selectors:
                "model:owned/model\ndataset:owned/data\nmodel:owned/model",
        },
        {
            action: "installedPlan",
            request: { selectors: ["dataset:owned/data", "model:owned/model"] },
        },
    ],
    [
        { kind: "verification", mode: "new", runId: "", revision: "" },
        { action: "newVerification", request: { mode: "new" } },
    ],
    [
        { kind: "verification", mode: "new", runId: run, revision: "" },
        { action: "newVerification", request: { mode: "new", run_id: run } },
    ],
    [
        { kind: "verification", mode: "full", runId: "", revision: "" },
        { action: "fullVerification", request: { mode: "full" } },
    ],
    [
        {
            kind: "verification",
            mode: "revision",
            runId: "",
            revision: "dataset:owned/data@" + sha,
        },
        {
            action: "revisionVerification",
            request: {
                mode: "revision",
                revision: "dataset:owned/data@" + sha,
            },
        },
    ],
    [
        { kind: "diagnostics", readOnly: true },
        { action: "readOnlyDiagnostics", request: { read_only: true } },
    ],
    [
        { kind: "diagnostics", readOnly: false },
        { action: "probeDiagnostics", request: { read_only: false } },
    ],
    [
        {
            kind: "catalogRefresh",
            scope: "all",
            selectors: "",
            revisionScope: "retained",
            tags: false,
            technical: true,
        },
        {
            action: "catalogRefresh",
            request: {
                selectors: [],
                revision_scope: "retained",
                tags: false,
                technical: true,
            },
        },
    ],
])(
    "builds one existing action DTO without broadening its scope: %j",
    (form, expected) => {
        expect(buildJobIntent(parseJobForm(form))).toEqual(expected);
    },
);

test.each([
    { kind: "sync", scope: "selected", selectors: "" },
    { kind: "sync", scope: "all", selectors: "model:owned/model" },
    { kind: "sync", scope: "selected", selectors: "../private/path" },
    {
        kind: "sync",
        scope: "selected",
        selectors: Array(101).fill("model:owned/model").join("\n"),
    },
    { kind: "verification", mode: "full", runId: run, revision: "" },
    { kind: "verification", mode: "new", runId: "wrong", revision: "" },
    {
        kind: "verification",
        mode: "revision",
        runId: "",
        revision: "model:owned/model@main",
    },
    {
        kind: "catalogRefresh",
        scope: "all",
        selectors: "",
        revisionScope: "current",
        tags: false,
        technical: false,
    },
])("rejects malformed or mixed job scope before transmission: %j", (form) => {
    expect(() => buildJobIntent(parseJobForm(form))).toThrow();
});

test("closed form parsing refuses unknown keys and accessors without invoking them", () => {
    expect(() => parseJobForm({ ...plan(), candidate: "private" })).toThrow();
    const getter = vi.fn(() => "sync");
    expect(() =>
        parseJobForm(Object.defineProperty({}, "kind", { get: getter })),
    ).toThrow();
    expect(getter).not.toHaveBeenCalled();
});

test("effect descriptions keep reader Hub jobs, offline writers and probe effects distinct", () => {
    expect(describeJob(plan())).toMatchObject({ capability: "read" });
    expect(describeJob(defaultJobForm("diagnostics"))).toMatchObject({
        capability: "read",
    });
    expect(
        describeJob({ kind: "diagnostics", readOnly: false }).effects,
    ).toMatch(/temporary archive health probes/u);
    expect(describeJob(defaultJobForm("verification")).effects).toMatch(
        /No Hub contact, repair or pruning/u,
    );
    expect(describeJob(defaultJobForm("catalogRefresh")).effects).toMatch(
        /Offline supplemental/u,
    );
});

test("constructor and RAM form/file changes are read-free and candidate contents never reach snapshots or storage", async () => {
    const fetcher = vi.fn<typeof fetch>();
    const { store, storage } = setup(fetcher);
    expect(store.setForm(defaultJobForm("candidatePlan"))).toBe(true);
    const body = "# private candidate hf_OWNED_SECRET_NEVER_RENDER\n";
    expect(await store.selectCandidate(new File([body], "owned.toml"))).toBe(
        true,
    );
    expect(store.snapshot().candidateFile).toEqual({
        name: "owned.toml",
        bytes: body.length,
    });
    expect(store.snapshot().canSubmit).toBe(true);
    expect(JSON.stringify(store.snapshot())).not.toContain(body);
    expect([...storage.values()].join()).not.toContain(body);
    expect(fetcher).not.toHaveBeenCalled();
    store.clearCandidate();
    expect(store.snapshot().candidateFile).toBeNull();
    expect(store.snapshot().canSubmit).toBe(false);
});

test("file-only sizing preserves exact UTF-8 bytes including BOM and the original key exists before the sole POST", async () => {
    const source = "\ufeffschema_version=1\n# owned candidate\n";
    const fetcher = vi.fn<typeof fetch>().mockImplementation((input, init) => {
        if (init?.method !== "POST")
            return Promise.resolve(jsonResponse(problemWire(), 404));
        const key = new Headers(init.headers).get("Idempotency-Key");
        expect(key).not.toBeNull();
        expect(
            [...fixture.storage.values()].some((value) =>
                value.includes(key ?? "missing"),
            ),
        ).toBe(true);
        if (typeof init.body !== "string")
            throw new Error("Missing captured body");
        const body: unknown = JSON.parse(init.body);
        expect(body).toEqual({ candidate: source, selectors: [] });
        expect(urlOf(input).pathname).toBe("/api/v1/plans");
        return Promise.resolve(accepted("/api/v1/plans"));
    });
    const fixture = setup(fetcher);
    fixture.store.setForm(defaultJobForm("candidatePlan"));
    expect(
        await fixture.store.selectCandidate(
            new File([source], "candidate.toml"),
        ),
    ).toBe(true);
    await fixture.store.submit();
    expect(fixture.store.snapshot().submission?.kind).toBe("accepted");
    expect(
        fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(1);
    expect([...fixture.storage.values()].join()).not.toContain(source);
    expect(fixture.store.snapshot().canSubmit).toBe(false);
    await fixture.store.submit();
    expect(
        fetcher.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(1);
});

test.each([
    [
        "oversize",
        new File(["x".repeat(MAX_CANDIDATE_FILE_BYTES + 1)], "large.toml"),
        "bounds",
    ],
    [
        "JSON expansion",
        new File(['"'.repeat(600000)], "escaped.toml"),
        "bounds",
    ],
    [
        "invalid UTF-8",
        new File([new Uint8Array([0xff])], "invalid.toml"),
        "utf8",
    ],
    ["empty", new File([], "empty.toml"), "bounds"],
])(
    "candidate %s is refused without a request and preserves the previous admitted file",
    async (_name, file, issue) => {
        const fetcher = vi.fn<typeof fetch>();
        const { store } = setup(fetcher);
        store.setForm(defaultJobForm("candidatePlan"));
        expect(
            await store.selectCandidate(
                new File(["# previous\n"], "previous.toml"),
            ),
        ).toBe(true);
        expect(await store.selectCandidate(file)).toBe(false);
        expect(store.snapshot().candidateFile?.name).toBe("previous.toml");
        expect(store.snapshot().issue).toBe(issue);
        expect(fetcher).not.toHaveBeenCalled();
    },
);

test("shared capacity refuses candidate retention without discarding the prior admitted input", async () => {
    const { controller, store } = setup();
    store.setForm(defaultJobForm("candidatePlan"));
    await store.selectCandidate(new File(["# previous\n"], "previous.toml"));
    const fillers = Array.from({ length: 4 }, () =>
        controller.createPrivateSlot(),
    );
    for (const slot of fillers.slice(0, 3))
        expect(slot.set("x".repeat(8 * 1024 * 1024 - 2))).toBe(true);
    expect(fillers[3]?.set("x".repeat(7.8 * 1024 * 1024))).toBe(true);
    expect(
        await store.selectCandidate(new File(["x".repeat(400000)], "new.toml")),
    ).toBe(false);
    expect(store.snapshot()).toMatchObject({
        issue: "capacity",
        candidateFile: { name: "previous.toml" },
    });
    for (const slot of fillers) slot.clear();
});

test("auth clearing fences a late candidate read and drops private form data even after identical-authority reconnect", async () => {
    const { controller, store } = setup();
    store.setForm(defaultJobForm("candidatePlan"));
    const file = new File(["# late secret\n"], "late.toml"),
        pending = deferred<ArrayBuffer>();
    vi.spyOn(file, "arrayBuffer").mockReturnValue(pending.promise);
    const reading = store.selectCandidate(file);
    controller.disconnect();
    pending.resolve(new TextEncoder().encode("# late secret\n").buffer);
    expect(await reading).toBe(false);
    await controller.reconnect();
    expect(store.snapshot()).toMatchObject({
        form: { kind: "installedPlan" },
        candidateFile: null,
        lastRecordId: null,
    });
    expect(JSON.stringify(store.snapshot())).not.toContain("late secret");
});

test("lost acknowledgement retains the original handle and repeated click cannot create another POST", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockRejectedValue(new TypeError("Owned lost reply"));
    const { store, storage } = setup(fetcher);
    await store.submit();
    expect(store.snapshot().submission?.kind).toBe("uncertain");
    expect(store.snapshot().lastRecordId).not.toBeNull();
    expect([...storage.values()].join()).toContain("basic-key");
    await store.submit();
    expect(fetcher).toHaveBeenCalledOnce();
});

test("estimate uses the shared typed GET and pause fences its late response without cancelling any job", async () => {
    const pending = deferred<Response>();
    const fetcher = vi.fn<typeof fetch>().mockReturnValue(pending.promise);
    const { store } = setup(fetcher);
    const reading = store.estimate();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    expect(fetcher.mock.calls[0]?.[1]?.method).toBe("GET");
    expect(
        urlOf(fetcher.mock.calls[0]?.[0] ?? "https://invalid/").pathname,
    ).toBe("/api/v1/verification/estimate");
    store.pause();
    pending.resolve(
        jsonResponse(
            operationResponse("verify --estimate", {
                mode: "estimate",
                repositories: 0,
                revisions: 0,
                unique_bytes: 0,
                unique_objects: 0,
                unreadable_objects: 0,
                estimated_duration_seconds: null,
                measured_throughput_bytes_per_second: null,
                storage_maintenance: "undetectable",
            }),
        ),
    );
    await reading;
    expect(store.snapshot().pending).toBeNull();
    expect(store.snapshot().estimate?.result).toBeNull();
});

test("detached subscribers cannot prevent state changes or private clearing", async () => {
    const { controller, store } = setup();
    store.subscribe(() => {
        throw new Error("detached");
    });
    expect(store.setForm(defaultJobForm("candidatePlan"))).toBe(true);
    await store.selectCandidate(new File(["# private\n"], "private.toml"));
    controller.disconnect();
    expect(store.snapshot().candidateFile).toBeNull();
    expect(store.snapshot().form.kind).toBe("installedPlan");
});

function readinessResponse(changes: Record<string, unknown> = {}) {
    return jsonResponse({
        schema_version: 1,
        archive_id: ARCHIVE_ID,
        config_fingerprint: "2".repeat(64),
        archive: true,
        hub: true,
        control: true,
        archive_writable: true,
        verification_available: true,
        ...changes,
    });
}
test.each([
    [{ archive: false }, "archive writes are disabled"],
    [{ archive_writable: false }, "required archive storage is read-only"],
    [{ verification_available: false }, "verification worker is unavailable"],
])(
    "fresh readiness %j explains a real disabled job without host-read prerequisite",
    async (changes, reason) => {
        const fetcher = vi
            .fn<typeof fetch>()
            .mockResolvedValue(readinessResponse(changes));
        const { store } = setup(fetcher);
        store.setForm({
            kind: "verification",
            mode: "full",
            runId: "",
            revision: "",
        });
        await store.recheckReadiness();
        expect(store.snapshot().canSubmit).toBe(false);
        expect(store.snapshot().availabilityReason).toContain(reason);
        expect(fetcher).toHaveBeenCalledOnce();
        expect(
            urlOf(fetcher.mock.calls[0]?.[0] ?? "https://invalid").pathname,
        ).toBe("/api/v1/jobs/readiness");
        expect(fetcher.mock.calls[0]?.[1]?.method).toBe("GET");
    },
);
test("unknown advisory readiness permits an explicit fresh server check and expires without background GET", async () => {
    const fetcher = vi
        .fn<typeof fetch>()
        .mockResolvedValue(readinessResponse({ hub: null }));
    const { store } = setup(fetcher);
    await store.recheckReadiness();
    expect(store.snapshot().canSubmit).toBe(true);
    expect(store.snapshot().availabilityReason).toContain("unknown");
    expect(fetcher).toHaveBeenCalledOnce();
    vi.spyOn(performance, "now").mockReturnValue(performance.now() + 30001);
    store.setForm({ ...defaultJobForm(), selectors: "" });
    expect(store.snapshot().availabilityReason).toContain(
        "Readiness unavailable",
    );
    expect(store.snapshot().canSubmit).toBe(true);
    expect(fetcher).toHaveBeenCalledOnce();
});
test("hidden readiness GET aborts and late response cannot become current; return owns one fresh GET", async () => {
    const late = deferred<Response>();
    const fetcher = vi
        .fn<typeof fetch>()
        .mockReturnValueOnce(late.promise)
        .mockResolvedValue(readinessResponse({ hub: false }));
    const { store, controller } = setup(fetcher);
    const reading = store.recheckReadiness();
    await vi.waitFor(() => {
        expect(fetcher).toHaveBeenCalledOnce();
    });
    controller.setPageHidden(true);
    expect(fetcher.mock.calls[0]?.[1]?.signal?.aborted).toBe(true);
    late.resolve(readinessResponse());
    await reading;
    expect(store.snapshot().readinessPhase).toBe("unavailable");
    controller.setPageHidden(false);
    await vi.waitFor(() => {
        expect(store.snapshot().availabilityReason).toContain(
            "Hub access is disabled",
        );
    });
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
});
