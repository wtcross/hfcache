/** Actual typed client/query-store boundary with owned HTTP responses; not installed acceptance. */
import { afterEach, expect, test, vi } from "vitest";
import {
    createRepositoryStore,
    MAX_REPOSITORY_PAGES,
} from "../src/repository/repository-state";
import type { RepositoryStore } from "../src/repository/repository-state";
import type {
    PublicationPair,
    RepositoryTarget,
    RepositoryView,
} from "../src/repository/routes";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
    statusPayload,
} from "./read-fixtures";
import { deferred } from "./state-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import {
    decodeReferencePayload,
    decodeManifestPayload,
} from "../src/wire/generated";
import { parseWireJson } from "../src/wire/json";

const target: RepositoryTarget = {
    repositoryType: "model",
    repositoryId: "owner/model",
};
const first: PublicationPair = {
    commitSha: "a".repeat(40),
    publicationId: "b".repeat(32),
};
const second: PublicationPair = {
    commitSha: "c".repeat(40),
    publicationId: "d".repeat(32),
};
const at = "2026-10-20T12:00:00.000000Z",
    fingerprint = "2".repeat(64);
const controllers: SessionController[] = [],
    stores: RepositoryStore[] = [];
afterEach(() => {
    for (const store of stores.splice(0)) store.dispose();
    for (const controller of controllers.splice(0)) controller.dispose();
    vi.unstubAllGlobals();
});
function wire(command: string, data: unknown, cursor: string | null = null) {
    return {
        ...readWire(command, data),
        archive_id: ARCHIVE_ID,
        config_fingerprint: fingerprint,
        next_cursor: cursor,
    };
}
function manifest(owned = target, pair = first, generation = 1) {
    return {
        schema_version: 1,
        application_version: "fixture",
        repository_type: owned.repositoryType,
        repository_id: owned.repositoryId,
        commit_sha: pair.commitSha,
        publication_id: pair.publicationId,
        publication_generation: generation,
        dependencies: [],
        download_completed_at: at,
        download_started_at: at,
        first_observed_at: at,
        file_count: 0,
        files: [],
        hub_endpoint: "https://huggingface.co",
        huggingface_hub_version: "fixture",
        publication_mode: "hardlink",
        published_at: at,
        python_version: "fixture",
        repair: null,
        requested_revision: "main",
        total_bytes: 0,
        tree: `published/repos/${owned.repositoryType}s/${owned.repositoryId}/revisions/${pair.commitSha}/${pair.publicationId}`,
        verification: {
            algorithm: "sha256",
            completeness_checked: true,
            hashed_bytes: 0,
            hashed_objects: 0,
            reused_digests: 0,
            outcome: "verified",
            verified_at: at,
        },
        verified_at: at,
    };
}
function reference(owned = target, pair = first, generation = 1) {
    return {
        locator_base: "published/",
        reference: {
            schema_version: 1,
            repository_type: owned.repositoryType,
            repository_id: owned.repositoryId,
            commit_sha: pair.commitSha,
            publication_id: pair.publicationId,
            publication_generation: generation,
            manifest: `manifests/${owned.repositoryType}s/${owned.repositoryId}/${pair.commitSha}/${pair.publicationId}.json`,
            tree: `repos/${owned.repositoryType}s/${owned.repositoryId}/revisions/${pair.commitSha}/${pair.publicationId}`,
            updated_at: at,
        },
    };
}
function coverage() {
    return {
        repositories: 1,
        tags_known: 1,
        tags_unknown: 0,
        publications: 1,
        usable: 1,
        partial: 0,
        unsupported: 0,
        failed: 0,
        missing: 0,
        technical_required: false,
        incomplete: false,
    };
}
function detail(owned = target, pair = first, generation = 1) {
    return {
        schema_version: 1,
        catalog_identity: "e".repeat(64),
        coverage: coverage(),
        entry: {
            repository_type: owned.repositoryType,
            repository_id: owned.repositoryId,
            tags: [],
            tag_origin: "configured",
            tag_observed_at: null,
            curation_fingerprint: null,
            configured: true,
            enabled: false,
            archived: true,
            matching_variant_count: 0,
            representative_variant: null,
            dataset_formats: [],
        },
        observations: [
            {
                commit_sha: pair.commitSha,
                publication_id: pair.publicationId,
                publication_generation: generation,
                extractor_version: "fixture",
                observed_at: at,
                status: "complete",
                sources: [],
                dataset_formats: [],
                diagnostics: [],
            },
        ],
    };
}
function card(owned = target, pair = first, generation = 1) {
    return {
        schema_version: 1,
        kind: "repository_card",
        archive_id: ARCHIVE_ID,
        repository_type: owned.repositoryType,
        repository_id: owned.repositoryId,
        commit_sha: pair.commitSha,
        publication_id: pair.publicationId,
        publication_generation: generation,
        manifest_path: `published/manifests/${owned.repositoryType}s/${owned.repositoryId}/${pair.commitSha}/${pair.publicationId}.json`,
        manifest_digest: "f".repeat(64),
        source_path: null,
        expected_source_sha256: null,
        captured_at: null,
        presentation_version: null,
        state: "not_captured",
        markdown: null,
        presentation_sha256: null,
        diagnostics: [],
    };
}
function revision(owned = target, pair = first, generation = 1) {
    return {
        repository_type: owned.repositoryType,
        repository_id: owned.repositoryId,
        commit_sha: pair.commitSha,
        publication_id: pair.publicationId,
        publication_generation: generation,
        published_at: at,
        file_count: 0,
        total_bytes: 0,
        verification_state: "verified",
    };
}
function setup(
    router?: (
        url: URL,
        init: RequestInit | undefined,
        fallback: () => Response,
    ) => Response | Promise<Response>,
) {
    let latest = first;
    const seen: URL[] = [];
    const defaultResponse = (url: URL): Response => {
        const path = url.pathname,
            dataset =
                path.includes("/dataset/") ||
                url.searchParams
                    .getAll("selector")
                    .some((x) => x.startsWith("dataset:"));
        const owned: RepositoryTarget = {
            repositoryType: dataset ? "dataset" : "model",
            repositoryId: "owner/model",
        };
        const segments = path.split("/"),
            pair = path.includes("/manifests/")
                ? {
                      commitSha: segments.at(-2) ?? "",
                      publicationId: segments.at(-1) ?? "",
                  }
                : path.endsWith("/card")
                  ? {
                        commitSha: segments.at(-3) ?? "",
                        publicationId: segments.at(-2) ?? "",
                    }
                  : {
                        commitSha:
                            url.searchParams.get("commit_sha") ??
                            latest.commitSha,
                        publicationId:
                            url.searchParams.get("publication_id") ??
                            latest.publicationId,
                    };
        const generation = pair.publicationId === first.publicationId ? 1 : 2;
        if (path.endsWith("/references/current"))
            return jsonResponse(
                wire(
                    "reference read",
                    reference(
                        owned,
                        latest,
                        latest.publicationId === first.publicationId ? 1 : 2,
                    ),
                ),
            );
        if (path.includes("/references/")) {
            const sha = segments.at(-1);
            const retained = sha === latest.commitSha ? latest : first;
            return jsonResponse(
                wire(
                    "reference read",
                    reference(
                        owned,
                        retained,
                        retained.publicationId === first.publicationId ? 1 : 2,
                    ),
                ),
            );
        }
        if (path.includes("/manifests/"))
            return jsonResponse(
                wire("manifest read", {
                    manifest: manifest(owned, pair, generation),
                    tree_base: "archive-root/",
                }),
            );
        if (path.endsWith("/card"))
            return jsonResponse(
                wire("card read", card(owned, pair, generation)),
            );
        if (path.endsWith("/variants"))
            return jsonResponse(
                wire("catalog.variants", {
                    schema_version: 1,
                    catalog_identity: "e".repeat(64),
                    coverage: coverage(),
                    total_matches: 0,
                    entries: [],
                }),
            );
        if (path.includes("/catalog/repositories/"))
            return jsonResponse(
                wire("catalog.detail", detail(owned, pair, generation)),
            );
        if (path.endsWith("/repositories/revisions"))
            return jsonResponse(
                wire("list", {
                    revisions: [
                        revision(
                            owned,
                            latest,
                            latest.publicationId === first.publicationId
                                ? 1
                                : 2,
                        ),
                        ...(latest.publicationId === first.publicationId
                            ? []
                            : [revision(owned)]),
                    ],
                }),
            );
        if (path.endsWith("/repositories"))
            return jsonResponse(
                wire("list", {
                    repositories: [
                        {
                            repository_type: owned.repositoryType,
                            repository_id: owned.repositoryId,
                            enabled: false,
                            managed: true,
                            retained_revisions: 2,
                            current_commit_sha: latest.commitSha,
                            current_publication_id: latest.publicationId,
                        },
                    ],
                }),
            );
        if (path.endsWith("/status"))
            return jsonResponse(wire("status", statusPayload(true)));
        if (path.endsWith("/runs"))
            return jsonResponse(wire("runs", { runs: ["1".repeat(32)] }));
        return jsonResponse(problemWire(), 404);
    };
    const fetcher = vi.fn<typeof fetch>((input, init) => {
        if (!(input instanceof URL)) throw new Error("expected typed URL");
        const url = input;
        seen.push(url);
        return Promise.resolve(
            router?.(url, init, () => defaultResponse(url)) ??
                defaultResponse(url),
        );
    });
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_archive_id: ARCHIVE_ID,
    };
    vi.stubGlobal("location", new URL(bootstrap.configured_origin));
    const controller = createSessionController({
        bootstrap,
        fetcher,
        storage: null,
        reconnect: () =>
            Promise.resolve({
                ...bootstrap,
                instance_id: "9".repeat(32),
                authority_epoch: "9".repeat(32),
            }),
    });
    const store = createRepositoryStore(controller);
    controllers.push(controller);
    stores.push(store);
    return {
        store,
        controller,
        fetcher,
        seen,
        moveCurrent: (pair: PublicationPair) => {
            latest = pair;
        },
    };
}
const overview: RepositoryView = { pair: null, tab: "overview" };
const paths = (seen: readonly URL[]) => seen.map((url) => url.pathname);

test("constructor sends no GET; current resolves once and pins the exact overview, with no hidden tabs or report reads", async () => {
    const { store, seen, fetcher } = setup();
    expect(seen).toHaveLength(0);
    decodeReferencePayload(parseWireJson(JSON.stringify(reference())));
    decodeManifestPayload(
        parseWireJson(
            JSON.stringify({
                manifest: manifest(),
                tree_base: "archive-root/",
            }),
        ),
    );
    await store.open(target, overview);
    const state = store.snapshot();
    expect(state.current.result).toMatchObject({ kind: "success" });
    expect(state.manifest.result).toMatchObject({ kind: "success" });
    expect(state.phase).toBe("ready");
    expect(state.view.pair).toEqual(first);
    expect(state.publicationGeneration).toBe(1);
    expect(state.manifestDigest).toBe("f".repeat(64));
    expect(state.selectedRevision).toBeNull();
    expect(paths(seen)).toHaveLength(7);
    expect(
        paths(seen).some(
            (path) =>
                path.endsWith("/variants") ||
                path.endsWith("/runs") ||
                path.endsWith("/revisions"),
        ),
    ).toBe(false);
    expect(fetcher.mock.calls.every(([, init]) => init?.method === "GET")).toBe(
        true,
    );
    await store.open(target, state.view);
    expect(seen).toHaveLength(7);
});
test("tabs load lazily, files use the whole manifest without invented paging, dataset details never request model variants", async () => {
    const { store, seen } = setup();
    await store.open(target, { pair: first, tab: "files" });
    expect(paths(seen).some((path) => path.includes("/catalog/"))).toBe(false);
    const manifestUrl = seen.find((url) =>
        url.pathname.includes("/manifests/"),
    );
    expect(manifestUrl?.search).toBe("");
    await store.setTab("details");
    expect(
        paths(seen).filter((path) => path.endsWith("/variants")),
    ).toHaveLength(1);
    await store.setTab("details");
    expect(
        paths(seen).filter((path) => path.endsWith("/variants")),
    ).toHaveLength(1);
    await store.open(
        { ...target, repositoryType: "dataset" },
        { pair: first, tab: "details" },
    );
    expect(
        paths(seen).some(
            (path) => path.includes("/dataset/") && path.endsWith("/variants"),
        ),
    ).toBe(false);
    expect(store.snapshot().manifest.result?.kind).toBe("success");
});
test("an explicit removed bookmark remains unavailable even when current is healthy; no unqualified fallback", async () => {
    const { store, seen, moveCurrent } = setup((url, _init, fallback) =>
        url.pathname.includes(`/manifests/${first.commitSha}/`)
            ? jsonResponse(problemWire(), 404)
            : fallback(),
    );
    moveCurrent(second);
    await store.open(target, { pair: first, tab: "overview" });
    expect(store.snapshot()).toMatchObject({
        phase: "unavailable",
        selected: first,
        manifestDigest: null,
    });
    expect(
        paths(seen).some((path) =>
            path.includes(`/manifests/${second.commitSha}/`),
        ),
    ).toBe(false);
    expect(paths(seen).some((path) => path.includes("/catalog/"))).toBe(false);
});
test("refresh updates current separately without changing selection; explicit selectCurrent adopts the new pair including same-SHA repair", async () => {
    const { store, moveCurrent } = setup();
    await store.open(target, overview);
    moveCurrent(second);
    await store.refresh();
    expect(store.snapshot().selected).toMatchObject(first);
    expect(store.snapshot().notice).toBe("publication_changed");
    await store.selectCurrent();
    expect(store.snapshot().selected).toMatchObject(second);
    expect(store.snapshot().publicationGeneration).toBe(2);
    const repaired = { ...second, publicationId: "7".repeat(32) };
    moveCurrent(repaired);
    await store.refresh();
    expect(store.snapshot().selected).toMatchObject(second);
    await store.selectCurrent();
    expect(store.snapshot().selected).toMatchObject(repaired);
});
test.each([404, 503])(
    "only actual current404 means unpublished; HTTP%s cannot fabricate a current publication",
    async (status) => {
        const { store, seen } = setup((url, _init, fallback) =>
            url.pathname.endsWith("/references/current")
                ? jsonResponse(
                      problemWire(
                          status === 503 ? "HFAPI019" : "HFAPI001",
                          status === 503 ? 20 : 10,
                      ),
                      status,
                  )
                : fallback(),
        );
        await store.open(target, overview);
        expect(store.snapshot().phase).toBe(
            status === 404 ? "unpublished" : "unavailable",
        );
        expect(store.snapshot().selected).toBeNull();
        expect(paths(seen).some((path) => path.includes("/manifests/"))).toBe(
            false,
        );
    },
);
test("missing/corrupt supplemental detail and card do not erase authoritative manifest inventory", async () => {
    const { store } = setup((url, _init, fallback) =>
        url.pathname.includes("/catalog/")
            ? jsonResponse({ malformed: true })
            : url.pathname.endsWith("/card")
              ? jsonResponse(problemWire(), 404)
              : fallback(),
    );
    await store.open(target, overview);
    const state = store.snapshot();
    expect(state.phase).toBe("ready");
    expect(state.manifest.result?.kind).toBe("success");
    expect(state.catalog.result?.kind).toBe("protocol_failure");
    expect(state.card.result?.kind).toBe("api_problem");
    expect(state.manifestDigest).toBeNull();
    await store.setTab("files");
    expect(store.snapshot().manifest.result?.kind).toBe("success");
});
test("a compatible card is the sole digest source; conflicting supplemental generation is withheld", async () => {
    const { store } = setup((url, _init, fallback) =>
        url.pathname.endsWith("/card")
            ? jsonResponse(wire("card read", card(target, first, 99)))
            : url.pathname.includes("/catalog/repositories/")
              ? jsonResponse(wire("catalog.detail", detail(target, first, 99)))
              : fallback(),
    );
    await store.open(target, overview);
    const state = store.snapshot();
    expect(state.phase).toBe("ready");
    expect(state.manifestDigest).toBeNull();
    expect(state.card.result).toBeNull();
    expect(state.catalog.result).toBeNull();
    expect(state.notice).toBe("join_unavailable");
});
test("current integrity cannot donate confidence to another selected pair or generation", async () => {
    const { store, moveCurrent } = setup();
    moveCurrent(second);
    await store.open(target, { pair: first, tab: "integrity" });
    expect(store.snapshot().selectedRevision).toMatchObject({
        commit_sha: first.commitSha,
        publication_id: first.publicationId,
        publication_generation: 1,
    });
    const other = setup((url, _init, fallback) =>
        url.pathname.endsWith("/revisions")
            ? jsonResponse(
                  wire("list", { revisions: [revision(target, first, 2)] }),
              )
            : fallback(),
    );
    await other.store.open(target, { pair: first, tab: "integrity" });
    expect(other.store.snapshot().selectedRevision).toBeNull();
});
test("same-spelling model/dataset route switch fences a delayed original manifest and derived requests", async () => {
    const delayed = deferred<Response>();
    let signal: AbortSignal | null | undefined;
    const { store, seen } = setup((url, init, fallback) => {
        if (
            url.pathname.includes("/repositories/model/") &&
            url.pathname.includes("/manifests/")
        ) {
            signal = init?.signal;
            return delayed.promise;
        }
        return fallback();
    });
    const old = store.open(target, { pair: first, tab: "overview" });
    await vi.waitFor(() => {
        expect(signal).toBeDefined();
    });
    await store.open(
        { ...target, repositoryType: "dataset" },
        { pair: second, tab: "files" },
    );
    expect(signal?.aborted).toBe(true);
    delayed.resolve(
        jsonResponse(
            wire("manifest read", {
                manifest: manifest(),
                tree_base: "archive-root/",
            }),
        ),
    );
    await old;
    expect(store.snapshot().selected).toMatchObject({
        repositoryType: "dataset",
        ...second,
    });
    expect(
        paths(seen).some((path) =>
            path.includes("/catalog/repositories/model/"),
        ),
    ).toBe(false);
});
test("authentication clears all aggregate pages synchronously, listener failures and late responses cannot resurrect them", async () => {
    let unauthorized = false;
    const { store } = setup((url, _init, fallback) =>
        unauthorized && url.pathname.endsWith("/references/current")
            ? jsonResponse(problemWire(), 401)
            : fallback(),
    );
    await store.open(target, overview);
    const peek = vi.fn(() => {
        const state = store.snapshot();
        expect(state.manifest.result).toBeNull();
        expect(state.card.result).toBeNull();
    });
    store.subscribe(() => {
        if (!store.snapshot().connected) throw new Error("detached");
    });
    store.subscribe(() => {
        if (!store.snapshot().connected) peek();
    });
    unauthorized = true;
    await store.refresh();
    expect(peek).toHaveBeenCalled();
    expect(store.snapshot().selected).toBeNull();
    expect(store.snapshot().phase).toBe("unavailable");
});
test("pause before queued work sends no hidden request; pausing a partial chain leaves it resumable only explicitly", async () => {
    const { store, seen } = setup();
    const opening = store.open(target, overview);
    store.pause();
    await opening;
    expect(seen).toHaveLength(0);
    await store.open(target, overview);
    expect(store.snapshot().phase).toBe("ready");
    const before = seen.length;
    store.pause();
    await Promise.resolve();
    expect(seen).toHaveLength(before);
});
test("variant409 resets just its finite page walk once; a second refusal stays visible", async () => {
    let calls = 0;
    const { store, seen } = setup((url, _init, fallback) => {
        if (!url.pathname.endsWith("/variants")) return fallback();
        calls++;
        return calls === 1
            ? jsonResponse(
                  wire(
                      "catalog.variants",
                      {
                          schema_version: 1,
                          catalog_identity: "e".repeat(64),
                          coverage: coverage(),
                          total_matches: 0,
                          entries: [],
                      },
                      "next",
                  ),
              )
            : jsonResponse(problemWire("HFAPI007", 10), 409);
    });
    await store.open(target, { pair: first, tab: "details" });
    const manifests = paths(seen).filter((x) =>
        x.includes("/manifests/"),
    ).length;
    await store.nextVariantsPage();
    expect(calls).toBe(3);
    expect(store.snapshot().variants.phase).toBe("failed");
    expect(store.snapshot().notice).toBe("stale_cursor");
    expect(paths(seen).filter((x) => x.includes("/manifests/"))).toHaveLength(
        manifests,
    );
});
test("loaded activity is one global ID page; reports require an explicitly loaded ID and no report is prefetched", async () => {
    const { store, seen } = setup();
    await store.open(target, { pair: first, tab: "activity" });
    expect(paths(seen).filter((x) => x.endsWith("/runs"))).toHaveLength(1);
    expect(paths(seen).some((x) => x.includes("/runs/"))).toBe(false);
    const before = seen.length;
    await store.openReport("9".repeat(32));
    expect(seen).toHaveLength(before);
    await store.openReport("1".repeat(32));
    expect(paths(seen).filter((x) => x.includes("/runs/"))).toHaveLength(1);
    expect(store.snapshot().reportRunId).toBe("1".repeat(32));
});
test("cursor cycles and32-page histories stop without a hidden continuation", async () => {
    let index = 0;
    const { store, seen } = setup((url, _init, fallback) =>
        url.pathname.endsWith("/runs")
            ? jsonResponse(
                  wire("runs", { runs: [] }, "cursor" + String(index++)),
              )
            : fallback(),
    );
    await store.open(target, { pair: first, tab: "activity" });
    for (let page = 1; page < MAX_REPOSITORY_PAGES; page++)
        await store.nextRunsPage();
    const count = seen.length;
    await store.nextRunsPage();
    expect(seen).toHaveLength(count);
    expect(store.snapshot().notice).toBe("page_limit");
    expect(store.snapshot().pagination.runs).toMatchObject({
        pageIndex: 31,
        hasNext: false,
    });
    const cycle = setup((url, _init, fallback) =>
        url.pathname.endsWith("/runs")
            ? jsonResponse(wire("runs", { runs: [] }, "same"))
            : fallback(),
    );
    await cycle.store.open(target, { pair: first, tab: "activity" });
    await cycle.store.nextRunsPage();
    const reads = cycle.seen.length;
    await cycle.store.nextRunsPage();
    expect(cycle.seen).toHaveLength(reads);
    expect(cycle.store.snapshot().notice).toBe("cursor_cycle");
});
test.each([413, 200])(
    "oversized HTTP%s or unsafe numeric manifest remains a failure, never empty inventory",
    async (status) => {
        const { store } = setup((url, _init, fallback) =>
            url.pathname.includes("/manifests/")
                ? status === 413
                    ? jsonResponse(problemWire("HFAPI005", 20), 413)
                    : jsonResponse(
                          wire("manifest read", {
                              manifest: {
                                  ...manifest(),
                                  total_bytes: 9007199254740992,
                              },
                              tree_base: "archive-root/",
                          }),
                      )
                : fallback(),
        );
        await store.open(target, overview);
        expect(store.snapshot().phase).toBe("failed");
        expect(store.snapshot().manifestDigest).toBeNull();
        expect(store.snapshot().manifest.result?.kind).toBe(
            status === 413 ? "api_problem" : "protocol_failure",
        );
    },
);
test("invalid half pair or unsupported tab refuses before any read", async () => {
    const { store, seen } = setup();
    await store.open(target, {
        tab: "overview",
        pair: { ...first, publicationId: "invalid" },
    });
    expect(store.snapshot().phase).toBe("invalid");
    expect(seen).toHaveLength(0);
});

test("current and selected manifest generation must agree, and refresh cannot rewrite an established exact generation", async () => {
    let changed = false;
    const { store } = setup((url, _init, fallback) =>
        changed && url.pathname.includes("/manifests/")
            ? jsonResponse(
                  wire("manifest read", {
                      manifest: manifest(target, first, 99),
                      tree_base: "archive-root/",
                  }),
              )
            : fallback(),
    );
    await store.open(target, overview);
    expect(store.snapshot().publicationGeneration).toBe(1);
    changed = true;
    await store.refresh();
    expect(store.snapshot()).toMatchObject({
        phase: "failed",
        notice: "join_unavailable",
        publicationGeneration: null,
        manifestDigest: null,
        selectedRevision: null,
    });
    expect(store.snapshot().manifest.result).toBeNull();
});

test("paused unfinished overview resumes explicitly from the pinned pair without retaining old pending content", async () => {
    const delayed = deferred<Response>();
    let calls = 0;
    const { store, seen } = setup((url, _init, fallback) => {
        if (url.pathname.endsWith("/card") && ++calls === 1)
            return delayed.promise;
        return fallback();
    });
    const opening = store.open(target, overview);
    await vi.waitFor(() => {
        expect(calls).toBe(1);
    });
    expect(store.snapshot().manifest.result?.kind).toBe("success");
    store.pause();
    expect(store.snapshot().phase).toBe("idle");
    delayed.resolve(jsonResponse(wire("card read", card())));
    await opening;
    const count = seen.length;
    await Promise.resolve();
    expect(seen).toHaveLength(count);
    await store.open(target, store.snapshot().view);
    expect(store.snapshot().phase).toBe("ready");
    expect(store.snapshot().manifestDigest).toBe("f".repeat(64));
});

test("an identical-subject new auth session clears private pages and recreates captured client reads", async () => {
    const { store, controller, seen } = setup();
    await store.open(target, overview);
    const oldKey = store.snapshot().manifest.key,
        bookmark = store.snapshot().view;
    await controller.reconnect();
    expect(store.snapshot().selected).toBeNull();
    expect(store.snapshot().manifest.result).toBeNull();
    expect(store.snapshot().card.result).toBeNull();
    const before = seen.length;
    await store.open(target, bookmark);
    expect(seen.length).toBeGreaterThan(before);
    expect(store.snapshot().manifest.key).not.toBe(oldKey);
    expect(store.snapshot().phase).toBe("ready");
});

test("refreshing an unpublished reference reports loading rather than reusing stale404 as fresh absence", async () => {
    const delayed = deferred<Response>();
    let calls = 0;
    const { store } = setup((url, _init, fallback) => {
        if (!url.pathname.endsWith("/references/current")) return fallback();
        return ++calls === 1
            ? jsonResponse(problemWire(), 404)
            : delayed.promise;
    });
    await store.open(target, overview);
    expect(store.snapshot().phase).toBe("unpublished");
    const refresh = store.refresh();
    await vi.waitFor(() => {
        expect(calls).toBe(2);
    });
    expect(store.snapshot().phase).toBe("loading");
    delayed.resolve(jsonResponse(wire("reference read", reference())));
    await refresh;
    expect(store.snapshot().phase).toBe("ready");
});

test("explicit report reads and page loads cannot continue after disposal", async () => {
    const { store, seen } = setup();
    await store.open(target, { pair: first, tab: "activity" });
    const before = seen.length;
    store.dispose();
    await store.nextRunsPage();
    await store.openReport("1".repeat(32));
    await store.refresh();
    await store.selectCurrent();
    expect(seen).toHaveLength(before);
    expect(store.snapshot().selected).toBeNull();
    expect(store.snapshot().report.result).toBeNull();
});

test.each(["missing", "repair"] as const)(
    "a %s per-SHA binding refuses an orphan manifest before any derived read",
    async (kind) => {
        const repaired = { ...first, publicationId: "8".repeat(32) };
        const { store, seen, moveCurrent } = setup((url, _init, fallback) => {
            if (!url.pathname.endsWith("/references/" + first.commitSha))
                return fallback();
            return kind === "missing"
                ? jsonResponse(problemWire(), 404)
                : jsonResponse(
                      wire("reference read", reference(target, repaired, 2)),
                  );
        });
        moveCurrent(second);
        await store.open(target, { pair: first, tab: "overview" });
        expect(store.snapshot()).toMatchObject({
            phase: "unavailable",
            retained: false,
            selected: first,
            publicationGeneration: null,
            manifestDigest: null,
        });
        expect(
            paths(seen).some(
                (path) =>
                    path.includes("/manifests/") ||
                    path.includes("/catalog/") ||
                    path.endsWith("/card"),
            ),
        ).toBe(false);
    },
);

test.each([503, 200])(
    "a selected-reference HTTP%s refusal remains unknown, never known absent or latest fallback",
    async (status) => {
        const { store, seen, moveCurrent } = setup((url, _init, fallback) =>
            url.pathname.endsWith("/references/" + first.commitSha)
                ? status === 503
                    ? jsonResponse(problemWire("HFAPI019", 20), status)
                    : jsonResponse({ malformed: true })
                : fallback(),
        );
        moveCurrent(second);
        await store.open(target, { pair: first, tab: "files" });
        expect(store.snapshot().phase).toBe(
            status === 503 ? "unavailable" : "failed",
        );
        expect(store.snapshot().retained).toBeNull();
        expect(paths(seen).some((path) => path.includes("/manifests/"))).toBe(
            false,
        );
    },
);

test("refresh revalidates the selected SHA reference and never relabels a retained orphan as current after repair", async () => {
    let repaired = false;
    const { store, seen } = setup((url, _init, fallback) =>
        repaired && url.pathname.endsWith("/references/" + first.commitSha)
            ? jsonResponse(
                  wire(
                      "reference read",
                      reference(
                          target,
                          { ...first, publicationId: "8".repeat(32) },
                          2,
                      ),
                  ),
              )
            : fallback(),
    );
    await store.open(target, overview);
    expect(store.snapshot().retained).toBe(true);
    const manifestReads = paths(seen).filter((path) =>
        path.includes("/manifests/"),
    ).length;
    repaired = true;
    await store.refresh();
    expect(store.snapshot().phase).toBe("unavailable");
    expect(store.snapshot().retained).toBe(false);
    expect(store.snapshot().selected).toMatchObject(first);
    expect(store.snapshot().manifestDigest).toBeNull();
    expect(store.snapshot().selectedRevision).toBeNull();
    expect(
        paths(seen).filter((path) => path.includes("/manifests/")),
    ).toHaveLength(manifestReads);
});

test("leaving a lazy tab releases its aggregate references and subscriptions instead of accumulating private pages", async () => {
    const { store } = setup();
    await store.open(target, { pair: first, tab: "details" });
    expect(store.snapshot().variants.result?.kind).toBe("success");
    await store.setTab("activity");
    expect(store.snapshot().variants.result).toBeNull();
    expect(store.snapshot().catalog.result).toBeNull();
    await store.openReport("1".repeat(32));
    expect(store.snapshot().reportRunId).not.toBeNull();
    await store.setTab("files");
    expect(store.snapshot().runs.result).toBeNull();
    expect(store.snapshot().report.result).toBeNull();
    expect(store.snapshot().reportRunId).toBeNull();
});

test("pausing an active refresh aborts its stale cached query and fences its late continuation", async () => {
    const delayed = deferred<Response>();
    let calls = 0;
    let signal: AbortSignal | null | undefined;
    const { store, seen } = setup((url, init, fallback) => {
        if (!url.pathname.endsWith("/references/current")) return fallback();
        if (++calls === 2) {
            signal = init?.signal;
            return delayed.promise;
        }
        return fallback();
    });
    await store.open(target, overview);
    const refresh = store.refresh();
    await vi.waitFor(() => {
        expect(signal).toBeDefined();
    });
    store.pause();
    expect(signal?.aborted).toBe(true);
    const before = seen.length;
    delayed.resolve(
        jsonResponse(wire("reference read", reference(target, second, 2))),
    );
    await refresh;
    expect(seen).toHaveLength(before);
    expect(store.snapshot().selected).toMatchObject(first);
    expect(store.snapshot().phase).toBe("idle");
});

test.each(["variants", "revisions", "runs"] as const)(
    "%s rejects a typed26-row response before publishing success, without truncation",
    async (name) => {
        let count = 25;
        const { store, seen } = setup((url, _init, fallback) => {
            if (name === "runs" && url.pathname.endsWith("/runs"))
                return jsonResponse(
                    wire("runs", {
                        runs: Array.from({ length: count }, (_, index) =>
                            index.toString(16).padStart(32, "0"),
                        ),
                    }),
                );
            if (
                name === "revisions" &&
                url.pathname.endsWith("/repositories/revisions")
            )
                return jsonResponse(
                    wire("list", {
                        revisions: Array.from({ length: count }, (_, index) =>
                            revision(
                                target,
                                {
                                    commitSha: index
                                        .toString(16)
                                        .padStart(40, "0"),
                                    publicationId: index
                                        .toString(16)
                                        .padStart(32, "0"),
                                },
                                index + 1,
                            ),
                        ),
                    }),
                );
            if (name === "variants" && url.pathname.endsWith("/variants"))
                return jsonResponse(
                    wire("catalog.variants", {
                        schema_version: 1,
                        catalog_identity: "e".repeat(64),
                        coverage: coverage(),
                        total_matches: count,
                        entries: Array.from({ length: count }, (_, index) => ({
                            commit_sha: first.commitSha,
                            publication_id: first.publicationId,
                            publication_generation: 1,
                            variant: {
                                variant_id: index
                                    .toString(16)
                                    .padStart(64, "0"),
                                format: "bin",
                                encoding: null,
                                quantization: null,
                                quantization_method: null,
                                bits: null,
                                group_size: null,
                                role: "unknown",
                                members: [
                                    {
                                        path: "file-" + String(index) + ".bin",
                                        size_bytes: 0,
                                    },
                                ],
                                total_bytes: null,
                                completeness: "unknown",
                                evidence: "filename",
                                source_paths: ["config.json"],
                                diagnostics: [],
                            },
                        })),
                    }),
                );
            return fallback();
        });
        const observed: string[] = [];
        store.subscribe(() => {
            const kind = store.snapshot()[name].result?.kind;
            if (kind !== undefined) observed.push(kind);
        });
        await store.open(target, {
            pair: first,
            tab:
                name === "variants"
                    ? "details"
                    : name === "revisions"
                      ? "revisions"
                      : "activity",
        });
        expect(store.snapshot()[name].result?.kind).toBe("success");
        observed.length = 0;
        count = 26;
        await store.refresh();
        expect(store.snapshot()[name].result).toEqual({
            kind: "protocol_failure",
            reason: "bounds",
        });
        expect(observed).not.toContain("success");
        expect(store.snapshot().pagination[name].hasNext).toBe(false);
        expect(
            seen
                .find((url) => url.pathname.endsWith("/" + name))
                ?.searchParams.get("limit"),
        ).toBe("25");
        expect(store.snapshot().manifest.result?.kind).toBe("success");
    },
);

test("a new unqualified open resolves fresh current instead of reusing the previous pinned view's reference", async () => {
    const { store, moveCurrent } = setup();
    await store.open(target, overview);
    moveCurrent(second);
    await store.open(target, overview);
    expect(store.snapshot().selected).toMatchObject(second);
    expect(store.snapshot().publicationGeneration).toBe(2);
});

test.each(["missing", "repair"] as const)(
    "a completed same-view remount revalidates a %s selected reference before qualifying cached immutable metadata",
    async (kind) => {
        let retired = false;
        const replacement = { ...first, publicationId: "8".repeat(32) };
        const { store, seen, moveCurrent } = setup((url, _init, fallback) =>
            retired && url.pathname.endsWith("/references/" + first.commitSha)
                ? kind === "missing"
                    ? jsonResponse(problemWire(), 404)
                    : jsonResponse(
                          wire(
                              "reference read",
                              reference(target, replacement, 2),
                          ),
                      )
                : fallback(),
        );
        await store.open(target, overview);
        const bookmark = store.snapshot().view;
        const before = seen.length,
            manifests = paths(seen).filter((path) =>
                path.includes("/manifests/"),
            ).length;
        store.pause();
        await Promise.resolve();
        expect(seen).toHaveLength(before);
        expect(store.snapshot().phase).toBe("idle");
        expect(store.snapshot().retained).toBeNull();
        retired = true;
        moveCurrent(kind === "repair" ? replacement : second);
        await store.open(target, bookmark);
        expect(store.snapshot().phase).toBe("unavailable");
        expect(store.snapshot().retained).toBe(false);
        expect(store.snapshot().selected).toMatchObject(first);
        expect(
            paths(seen).filter((path) => path.includes("/manifests/")),
        ).toHaveLength(manifests);
        expect(seen.length - before).toBe(2);
    },
);

test("a new tab revalidates one selected reference before fetching publication-derived data, with no reads per render", async () => {
    let retired = false;
    const { store, seen } = setup((url, _init, fallback) =>
        retired && url.pathname.endsWith("/references/" + first.commitSha)
            ? jsonResponse(problemWire(), 404)
            : fallback(),
    );
    await store.open(target, overview);
    const before = seen.length;
    retired = true;
    await store.setTab("details");
    expect(seen.length - before).toBe(1);
    expect(store.snapshot().phase).toBe("unavailable");
    expect(paths(seen).some((path) => path.endsWith("/variants"))).toBe(false);
    const count = seen.length;
    for (let render = 0; render < 50; render++) store.snapshot();
    expect(seen).toHaveLength(count);
});

test("continuation and report actions stop before their next GET when the selected reference no longer qualifies", async () => {
    let retired = false;
    const { store, seen } = setup((url, _init, fallback) => {
        if (retired && url.pathname.endsWith("/references/" + first.commitSha))
            return jsonResponse(problemWire(), 404);
        if (url.pathname.endsWith("/variants"))
            return jsonResponse(
                wire(
                    "catalog.variants",
                    {
                        schema_version: 1,
                        catalog_identity: "e".repeat(64),
                        coverage: coverage(),
                        total_matches: 0,
                        entries: [],
                    },
                    "next",
                ),
            );
        return fallback();
    });
    await store.open(target, { pair: first, tab: "details" });
    const variantReads = paths(seen).filter((path) =>
        path.endsWith("/variants"),
    ).length;
    retired = true;
    await store.nextVariantsPage();
    expect(store.snapshot().retained).toBe(false);
    expect(
        paths(seen).filter((path) => path.endsWith("/variants")),
    ).toHaveLength(variantReads);
    retired = false;
    await store.open(target, { pair: first, tab: "activity" });
    retired = true;
    await store.openReport("1".repeat(32));
    expect(paths(seen).some((path) => path.includes("/runs/"))).toBe(false);
});
