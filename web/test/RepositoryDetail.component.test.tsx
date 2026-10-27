/** WEB013: real controller/store/typed transport with independent owned HTTP wires. */
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
import { RepositoryDetail } from "../src/components/RepositoryDetail";
import { createRepositoryStore } from "../src/repository/repository-state";
import type { RepositoryStore } from "../src/repository/repository-state";
import { repositoryFragment, repositoryPath } from "../src/repository/routes";
import type {
    PublicationPair,
    RepositoryTarget,
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
import runReport from "../../tests/fixtures/schemas/run-report.json";

const target: RepositoryTarget = {
    repositoryType: "model",
    repositoryId: "owner/item",
};
const first: PublicationPair = {
    commitSha: "a".repeat(40),
    publicationId: "b".repeat(32),
};
const second: PublicationPair = {
    commitSha: "c".repeat(40),
    publicationId: "d".repeat(32),
};
const at = "2026-10-20T12:00:00.000000Z";
const markup = "<img src=x onerror=globalThis.ownedMetadataExecuted=true>";
const owned: { store: RepositoryStore; controller: SessionController }[] = [];
afterEach(() => {
    cleanup();
    for (const value of owned.splice(0)) {
        value.store.dispose();
        value.controller.dispose();
    }
    window.localStorage.clear();
    vi.unstubAllGlobals();
});
function wire(command: string, data: unknown, cursor: string | null = null) {
    return {
        ...readWire(command, data),
        archive_id: ARCHIVE_ID,
        config_fingerprint: "2".repeat(64),
        next_cursor: cursor,
    };
}
function tree(item: RepositoryTarget, pair: PublicationPair) {
    return `repos/${item.repositoryType}s/${item.repositoryId}/revisions/${pair.commitSha}/${pair.publicationId}`;
}
function manifest(
    item: RepositoryTarget,
    pair: PublicationPair,
    generation: number,
) {
    const files = Array.from({ length: 26 }, (_, index) => ({
        path: `file-${String(index).padStart(2, "0")}.txt`,
        size: 1,
        sha256: "e".repeat(64),
        provenance: {
            cache_root: "canonical",
            hash_reused_from: null,
            hashed: true,
            source: "hub_download",
        },
        upstream: { git_oid: null, lfs_sha256: null, xet_hash: null },
    }));
    return {
        schema_version: 1,
        application_version: "owned-fixture",
        repository_type: item.repositoryType,
        repository_id: item.repositoryId,
        commit_sha: pair.commitSha,
        publication_id: pair.publicationId,
        publication_generation: generation,
        dependencies: [],
        download_completed_at: at,
        download_started_at: at,
        first_observed_at: at,
        file_count: files.length,
        files,
        hub_endpoint: "https://huggingface.co",
        huggingface_hub_version: "fixture",
        publication_mode: "copy",
        published_at: at,
        python_version: "fixture",
        repair: null,
        requested_revision: "main",
        total_bytes: files.length,
        tree: "published/" + tree(item, pair),
        verification: {
            algorithm: "sha256",
            completeness_checked: true,
            hashed_bytes: files.length,
            hashed_objects: files.length,
            reused_digests: 0,
            outcome: "verified",
            verified_at: at,
        },
        verified_at: at,
    };
}
function reference(
    item: RepositoryTarget,
    pair: PublicationPair,
    generation: number,
) {
    return {
        locator_base: "published/",
        reference: {
            schema_version: 1,
            repository_type: item.repositoryType,
            repository_id: item.repositoryId,
            commit_sha: pair.commitSha,
            publication_id: pair.publicationId,
            publication_generation: generation,
            tree: tree(item, pair),
            manifest: `manifests/${item.repositoryType}s/${item.repositoryId}/${pair.commitSha}/${pair.publicationId}.json`,
            updated_at: at,
        },
    };
}
function qualified(pair: PublicationPair, generation: number) {
    return {
        commit_sha: pair.commitSha,
        publication_id: pair.publicationId,
        publication_generation: generation,
        variant: {
            variant_id: "8".repeat(64),
            format: "gguf",
            encoding: "Q4_0",
            quantization: "Q4_0",
            quantization_method: "ggml",
            bits: 4,
            group_size: null,
            role: "primary",
            members: [{ path: "file-00.txt", size_bytes: 1 }],
            total_bytes: 1,
            completeness: "complete",
            evidence: "header",
            source_paths: ["file-00.txt"],
            diagnostics: [],
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
function detail(
    item: RepositoryTarget,
    pair: PublicationPair,
    generation: number,
) {
    const dataset = item.repositoryType === "dataset";
    const fields = dataset
        ? [
              ["dataset_config", "owned-config"],
              ["dataset_feature", "text:string"],
              ["dataset_split", "train"],
          ]
        : [["task", markup]];
    return {
        schema_version: 1,
        catalog_identity: "7".repeat(64),
        coverage: coverage(),
        entry: {
            repository_type: item.repositoryType,
            repository_id: item.repositoryId,
            tags: [],
            tag_origin: "configured",
            tag_observed_at: null,
            curation_fingerprint: null,
            configured: true,
            enabled: false,
            archived: true,
            matching_variant_count: dataset ? 0 : 1,
            representative_variant: dataset
                ? null
                : qualified(pair, generation),
            dataset_formats: dataset ? ["parquet"] : [],
        },
        observations: [
            {
                commit_sha: pair.commitSha,
                publication_id: pair.publicationId,
                publication_generation: generation,
                extractor_version: "owned-fixture",
                observed_at: at,
                status: "complete",
                sources: fields.map(([field, value]) => ({
                    path: "file-00.txt",
                    sha256: "e".repeat(64),
                    field,
                    values: [value],
                    evidence: "declaration",
                })),
                dataset_formats: dataset ? ["parquet"] : [],
                diagnostics: [],
            },
        ],
    };
}
type Router = (
    url: URL,
    fallback: () => Response,
) => Response | Promise<Response>;
function setup(
    fragment = "",
    item = target,
    router?: Router,
    onReadReport?: (runId: string) => void,
) {
    window.history.replaceState(
        null,
        "",
        repositoryPath(item, "/ui/") + fragment,
    );
    window.localStorage.clear();
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: window.location.origin,
        configured_archive_id: ARCHIVE_ID,
    };
    let currentPair = first;
    const references = new Map<string, PublicationPair>([
        [first.commitSha, first],
        [second.commitSha, second],
    ]);
    const seen: URL[] = [];
    const fallback = (url: URL): Response => {
        const dataset =
            url.pathname.includes("/dataset/") ||
            url.searchParams
                .getAll("selector")
                .some((value) => value.startsWith("dataset:"));
        const selectedTarget: RepositoryTarget = {
            repositoryType: dataset ? "dataset" : "model",
            repositoryId: item.repositoryId,
        };
        const parts = url.pathname.split("/");
        const pair = url.pathname.includes("/manifests/")
            ? {
                  commitSha: parts.at(-2) ?? "",
                  publicationId: parts.at(-1) ?? "",
              }
            : url.pathname.endsWith("/card")
              ? {
                    commitSha: parts.at(-3) ?? "",
                    publicationId: parts.at(-2) ?? "",
                }
              : {
                    commitSha:
                        url.searchParams.get("commit_sha") ??
                        currentPair.commitSha,
                    publicationId:
                        url.searchParams.get("publication_id") ??
                        currentPair.publicationId,
                };
        const generation = pair.publicationId === first.publicationId ? 1 : 2;
        if (url.pathname.includes("/references/")) {
            const revision = parts.at(-1);
            const selectedPair =
                revision === "current"
                    ? currentPair
                    : references.get(revision ?? "");
            return selectedPair === undefined
                ? jsonResponse(problemWire(), 404)
                : jsonResponse(
                      wire(
                          "reference read",
                          reference(
                              selectedTarget,
                              selectedPair,
                              selectedPair.publicationId === first.publicationId
                                  ? 1
                                  : 2,
                          ),
                      ),
                  );
        }
        if (url.pathname.includes("/manifests/"))
            return jsonResponse(
                wire("manifest read", {
                    manifest: manifest(selectedTarget, pair, generation),
                    tree_base: "archive-root/",
                }),
            );
        if (url.pathname.endsWith("/card"))
            return jsonResponse(
                wire("card read", {
                    schema_version: 1,
                    kind: "repository_card",
                    archive_id: ARCHIVE_ID,
                    repository_type: selectedTarget.repositoryType,
                    repository_id: selectedTarget.repositoryId,
                    commit_sha: pair.commitSha,
                    publication_id: pair.publicationId,
                    publication_generation: generation,
                    manifest_path: `published/manifests/${selectedTarget.repositoryType}s/${selectedTarget.repositoryId}/${pair.commitSha}/${pair.publicationId}.json`,
                    manifest_digest: "f".repeat(64),
                    source_path: null,
                    expected_source_sha256: null,
                    captured_at: null,
                    presentation_version: null,
                    state: "not_captured",
                    markdown: null,
                    presentation_sha256: null,
                    diagnostics: [],
                }),
            );
        if (url.pathname.endsWith("/variants"))
            return jsonResponse(
                wire("catalog.variants", {
                    schema_version: 1,
                    catalog_identity: "7".repeat(64),
                    coverage: coverage(),
                    total_matches: 1,
                    entries: [qualified(pair, generation)],
                }),
            );
        if (url.pathname.includes("/catalog/repositories/"))
            return jsonResponse(
                wire(
                    "catalog.detail",
                    detail(selectedTarget, pair, generation),
                ),
            );
        if (url.pathname === "/api/v1/repositories/revisions")
            return jsonResponse(
                wire("list", {
                    revisions: [first, second].map((entry, index) => ({
                        repository_type: selectedTarget.repositoryType,
                        repository_id: selectedTarget.repositoryId,
                        commit_sha: entry.commitSha,
                        publication_id: entry.publicationId,
                        publication_generation: index + 1,
                        file_count: 26,
                        total_bytes: 26,
                        published_at: at,
                        verification_state:
                            entry.publicationId === first.publicationId
                                ? "failed"
                                : "verified",
                    })),
                }),
            );
        if (url.pathname === "/api/v1/repositories")
            return jsonResponse(
                wire("list", {
                    repositories: [
                        {
                            repository_type: selectedTarget.repositoryType,
                            repository_id: selectedTarget.repositoryId,
                            managed: true,
                            enabled: false,
                            current_commit_sha: currentPair.commitSha,
                            current_publication_id: currentPair.publicationId,
                            retained_revisions: 2,
                        },
                    ],
                }),
            );
        if (url.pathname === "/api/v1/status")
            return jsonResponse(
                wire("status", {
                    ...statusPayload(true),
                    repositories: [
                        {
                            repository_type: selectedTarget.repositoryType,
                            repository_id: selectedTarget.repositoryId,
                            managed: true,
                            enabled: false,
                            current_commit_sha: currentPair.commitSha,
                            current_publication_generation:
                                currentPair.publicationId ===
                                first.publicationId
                                    ? 1
                                    : 2,
                            requested_revision: "main",
                            retained_generations: [1, 2],
                            retained_revisions: 2,
                            verification_state: "verified",
                            last_run_status: "completed",
                            upstream_state: "unknown",
                        },
                    ],
                }),
            );
        if (url.pathname === "/api/v1/runs")
            return jsonResponse(wire("runs", { runs: [runReport.run_id] }));
        if (url.pathname === "/api/v1/runs/" + runReport.run_id) {
            const result = wire("runs read", {
                report: { ...runReport, config_fingerprint: "2".repeat(64) },
            });
            return jsonResponse({
                ...result,
                envelope: { ...result.envelope, run_id: runReport.run_id },
            });
        }
        throw new Error("Unexpected owned repository read.");
    };
    const fetcher = vi.fn<typeof fetch>((input, init) => {
        expect(init?.method).toBe("GET");
        const url =
            input instanceof URL
                ? input
                : new URL(typeof input === "string" ? input : input.url);
        expect(url.origin).toBe(window.location.origin);
        seen.push(url);
        return Promise.resolve(
            router === undefined
                ? fallback(url)
                : router(url, () => fallback(url)),
        );
    });
    const controller = createSessionController({
        bootstrap,
        storage: window.localStorage,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
    });
    const store = createRepositoryStore(controller);
    owned.push({ store, controller });
    const rendered = render(
        <RepositoryDetail
            store={store}
            target={item}
            basePath="/ui/"
            {...(onReadReport === undefined ? {} : { onReadReport })}
        />,
    );
    const loaded = async () => {
        await waitFor(() => {
            expect(store.snapshot().phase).toBe("ready");
        });
        await waitFor(() => {
            expect(store.snapshot().refreshing).toBe(false);
        });
    };
    return {
        ...rendered,
        store,
        controller,
        fetcher,
        seen,
        loaded,
        references,
        setCurrent: (pair: PublicationPair) => {
            currentPair = pair;
        },
    };
}

test("current resolves once, pins exact URL and never changes selection when current later moves", async () => {
    const fixture = setup();
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(first);
    await waitFor(() => {
        expect(window.location.hash).toContain("commit_sha=" + first.commitSha);
        expect(window.location.hash).toContain(
            "publication_id=" + first.publicationId,
        );
    });
    fixture.setCurrent(second);
    await userEvent.click(
        screen.getByRole("tab", { name: "Files & manifest" }),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(first);
    expect(
        fixture.seen
            .filter((url) => url.pathname.includes("/manifests/"))
            .every((url) =>
                url.pathname.endsWith(
                    first.commitSha + "/" + first.publicationId,
                ),
            ),
    ).toBe(true);
    await userEvent.click(
        screen.getByRole("button", { name: "Select current publication" }),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(second);
});
test("an invalid half-pair fragment performs zero reads and unmount cannot start a hidden request", async () => {
    const fixture = setup("#commit_sha=" + first.commitSha);
    await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
            /invalid or unsupported selection fields/u,
        );
    });
    expect(fixture.fetcher).not.toHaveBeenCalled();
    fixture.unmount();
    await act(async () => {
        await Promise.resolve();
    });
    expect(fixture.fetcher).not.toHaveBeenCalled();
});
test("explicit missing selection is unavailable and never adopts latest", async () => {
    const fragment = repositoryFragment({ pair: first, tab: "overview" });
    const fixture = setup(fragment, target, (url, fallback) =>
        url.pathname.endsWith("/references/" + first.commitSha)
            ? jsonResponse(problemWire(), 404)
            : fallback(),
    );
    fixture.setCurrent(second);
    await waitFor(() => {
        expect(fixture.store.snapshot().phase).toBe("unavailable");
    });
    expect(fixture.store.snapshot().selected).toMatchObject(first);
    expect(
        fixture.seen
            .filter((url) => url.pathname.includes("/manifests/"))
            .every((url) =>
                url.pathname.endsWith(
                    first.commitSha + "/" + first.publicationId,
                ),
            ),
    ).toBe(true);
});
test("files are locally paged from one whole artifact and copied tree bases are explicit", async () => {
    const fixture = setup(repositoryFragment({ pair: first, tab: "files" }));
    await fixture.loaded();
    expect(
        screen.getByText("Metadata coverage has not been loaded for this tab."),
    ).toBeInTheDocument();
    expect(
        screen.queryByText("Loading bounded Metadata coverage."),
    ).not.toBeInTheDocument();
    expect(
        fixture.seen.filter((url) =>
            url.pathname.includes("/catalog/repositories/"),
        ),
    ).toHaveLength(0);
    expect(screen.getByText("file-00.txt")).toBeInTheDocument();
    expect(screen.queryByText("file-25.txt")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next files" }));
    expect(screen.getByText("file-25.txt")).toBeInTheDocument();
    expect(screen.queryByText("file-00.txt")).not.toBeInTheDocument();
    expect(
        fixture.seen.filter((url) => url.pathname.includes("/manifests/")),
    ).toHaveLength(1);
    const copied = vi
        .fn<(text: string) => Promise<void>>()
        .mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText: copied } });
    fireEvent.click(
        screen.getByRole("button", { name: "Copy archive-relative tree" }),
    );
    await waitFor(() => {
        expect(copied).toHaveBeenLastCalledWith(
            "published/" + tree(target, first),
        );
    });
    fireEvent.click(
        screen.getByRole("button", { name: "Copy published-relative tree" }),
    );
    await waitFor(() => {
        expect(copied).toHaveBeenLastCalledWith(tree(target, first));
    });
});
test("dataset declarations remain static and no model variants request or model field is invented", async () => {
    const dataset = { ...target, repositoryType: "dataset" as const };
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "details" }),
        dataset,
    );
    await fixture.loaded();
    expect(screen.getByText("owned-config")).toBeInTheDocument();
    expect(screen.getByText("text:string")).toBeInTheDocument();
    expect(screen.getByText("train")).toBeInTheDocument();
    expect(fixture.seen.some((url) => url.pathname.endsWith("/variants"))).toBe(
        false,
    );
    expect(screen.queryByText("Q4_0")).not.toBeInTheDocument();
});
test("metadata markup remains plain text and never constructs an active element", async () => {
    const fixture = setup();
    await fixture.loaded();
    expect(screen.getByText(markup)).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("[onerror]")).toBeNull();
});

test("a same-SHA repair replacement cannot authorize an old bookmarked publication", async () => {
    const fixture = setup(repositoryFragment({ pair: first, tab: "files" }));
    const repaired = { ...first, publicationId: "6".repeat(32) };
    fixture.references.set(first.commitSha, repaired);
    fixture.setCurrent(second);
    await waitFor(() => {
        expect(fixture.store.snapshot().phase).toBe("unavailable");
    });
    expect(fixture.store.snapshot().selected).toMatchObject(first);
    expect(
        fixture.seen.some((url) =>
            url.pathname.endsWith(repaired.publicationId),
        ),
    ).toBe(false);
    expect(
        screen.queryByRole("table", { name: "Manifest files" }),
    ).not.toBeInTheDocument();
});
test("selection changes fence a late old manifest and every later panel remains exact", async () => {
    const gate = deferred<Response>();
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "files" }),
        target,
        (url, fallback) =>
            url.pathname.endsWith(first.commitSha + "/" + first.publicationId)
                ? gate.promise
                : fallback(),
    );
    await waitFor(() => {
        expect(
            fixture.seen.some((url) => url.pathname.includes("/manifests/")),
        ).toBe(true);
    });
    await act(async () => {
        window.history.replaceState(
            null,
            "",
            repositoryPath(target, "/ui/") +
                repositoryFragment({ pair: second, tab: "files" }),
        );
        window.dispatchEvent(new HashChangeEvent("hashchange"));
        await Promise.resolve();
    });
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(second);
    await act(async () => {
        gate.resolve(
            jsonResponse(
                wire("manifest read", {
                    tree_base: "archive-root/",
                    manifest: manifest(target, first, 1),
                }),
            ),
        );
        await new Promise((resolve) => setTimeout(resolve, 10));
    });
    const selected = screen.getByRole("region", {
        name: "Selected publication",
    });
    expect(within(selected).getByText(second.commitSha)).toBeInTheDocument();
    expect(
        within(selected).queryByText(first.commitSha),
    ).not.toBeInTheDocument();
    expect(fixture.store.snapshot().publicationGeneration).toBe(2);
});
test("unmount aborts a pending manifest without late catalog, card or variant reads", async () => {
    const gate = deferred<Response>();
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "overview" }),
        target,
        (url, fallback) =>
            url.pathname.includes("/manifests/") ? gate.promise : fallback(),
    );
    await waitFor(() => {
        expect(
            fixture.seen.some((url) => url.pathname.includes("/manifests/")),
        ).toBe(true);
    });
    const before = fixture.seen.length;
    fixture.unmount();
    await act(async () => {
        gate.resolve(
            jsonResponse(
                wire("manifest read", {
                    tree_base: "archive-root/",
                    manifest: manifest(target, first, 1),
                }),
            ),
        );
        await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(fixture.seen).toHaveLength(before);
});
test("a failed supplemental source does not erase authoritative files and does not execute markup", async () => {
    const fixture = setup("", target, (url, fallback) =>
        url.pathname.includes("/catalog/repositories/")
            ? jsonResponse({ schema_version: 999 })
            : fallback(),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().catalog.phase).toBe("failed");
    expect(fixture.store.snapshot().manifest.phase).toBe("ready");
    await userEvent.click(
        screen.getByRole("tab", { name: "Files & manifest" }),
    );
    await fixture.loaded();
    expect(
        screen.getByRole("table", { name: "Manifest files" }),
    ).toBeInTheDocument();
    expect(screen.getByText("file-00.txt")).toBeInTheDocument();
});
test("a wrong consumer locator base is refused before file inventory or copy readiness", async () => {
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "files" }),
        target,
        (url, fallback) =>
            url.pathname.includes("/manifests/")
                ? jsonResponse(
                      wire("manifest read", {
                          tree_base: "published/",
                          manifest: manifest(target, first, 1),
                      }),
                  )
                : fallback(),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().phase).toBe("failed");
    });
    expect(
        screen.queryByRole("table", { name: "Manifest files" }),
    ).not.toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Copy published-relative tree" }),
    ).not.toBeInTheDocument();
});

test("selected offline, ingestion and newer current confidence remain distinct", async () => {
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "integrity" }),
    );
    fixture.setCurrent(second);
    await fixture.loaded();
    expect(fixture.store.snapshot().selectedRevision?.verification_state).toBe(
        "failed",
    );
    const panel = screen.getByRole("tabpanel");
    expect(panel).toHaveTextContent(
        /Selected publication offline verification\s*failed/u,
    );
    expect(panel).toHaveTextContent(
        /Publication ingestion verification\s*verified/u,
    );
    expect(panel).toHaveTextContent(
        /Current inventory verification\s*verified/u,
    );
    expect(fixture.store.snapshot().selected).toMatchObject(first);
});
test("clipboard denial is visible without claiming a copied locator or exposing raw diagnostics", async () => {
    const fixture = setup(repositoryFragment({ pair: first, tab: "files" }));
    await fixture.loaded();
    const copied = vi
        .fn<(text: string) => Promise<void>>()
        .mockRejectedValue(new Error("owned-private-clipboard-diagnostic"));
    vi.stubGlobal("navigator", { clipboard: { writeText: copied } });
    fireEvent.click(screen.getByRole("button", { name: "Copy commit SHA" }));
    await waitFor(() => {
        expect(copied).toHaveBeenCalledWith(first.commitSha);
    });
    await waitFor(() => {
        expect(
            screen.getByText(
                "Copy is unavailable. Select and copy the displayed commit sha.",
            ),
        ).toBeInTheDocument();
    });
    expect(
        screen.queryByText(/owned-private-clipboard-diagnostic/u),
    ).not.toBeInTheDocument();
    expect(fixture.store.snapshot().selected).toMatchObject(first);
});
test("activity observes explicitly loaded history and reports without inventing mutation or complete audit", async () => {
    const fixture = setup(repositoryFragment({ pair: first, tab: "activity" }));
    await fixture.loaded();
    expect(fixture.store.snapshot().runs.result?.kind).toBe("success");
    expect(
        fixture.seen.filter((url) => url.pathname === "/api/v1/runs"),
    ).toHaveLength(1);
    expect(
        fixture.seen.some((url) => url.pathname.startsWith("/api/v1/runs/")),
    ).toBe(false);
    await userEvent.click(
        screen.getByRole("button", {
            name: "Inspect report " + runReport.run_id,
        }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().report.phase).toBe("ready");
    });
    expect(
        fixture.seen.filter(
            (url) => url.pathname === "/api/v1/runs/" + runReport.run_id,
        ),
    ).toHaveLength(1);
    expect(
        fixture.fetcher.mock.calls.every(([, init]) => init?.method === "GET"),
    ).toBe(true);
});

test("repository Activity forwards the exact loaded run ID to Operations without submitting or walking history", async () => {
    const openReport = vi.fn();
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "activity" }),
        target,
        undefined,
        openReport,
    );
    await fixture.loaded();
    const requests = fixture.fetcher.mock.calls.length;
    await userEvent.click(
        screen.getByRole("button", {
            name: "Open run report in Operations " + runReport.run_id,
        }),
    );
    expect(openReport).toHaveBeenCalledExactlyOnceWith(runReport.run_id);
    expect(fixture.fetcher).toHaveBeenCalledTimes(requests);
    expect(fixture.controller.snapshot().registry.records).toEqual([]);
});

test("model details retain primary, adapter and incomplete declarations without inventing unknown bits", async () => {
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "details" }),
        target,
        (url, fallback) => {
            if (!url.pathname.endsWith("/variants")) return fallback();
            const primary = qualified(first, 1);
            const adapter = {
                ...primary,
                variant: {
                    ...primary.variant,
                    variant_id: "9".repeat(64),
                    role: "adapter",
                },
            };
            const incomplete = {
                ...primary,
                variant: {
                    ...primary.variant,
                    variant_id: "a".repeat(64),
                    role: "unknown",
                    completeness: "incomplete",
                    encoding: null,
                    bits: null,
                    quantization: null,
                    quantization_method: null,
                    total_bytes: null,
                    diagnostics: ["owned_fixture_incomplete"],
                },
            };
            return jsonResponse(
                wire("catalog.variants", {
                    schema_version: 1,
                    catalog_identity: "7".repeat(64),
                    coverage: coverage(),
                    total_matches: 3,
                    entries: [primary, adapter, incomplete],
                }),
            );
        },
    );
    await fixture.loaded();
    const panel = screen.getByRole("tabpanel");
    expect(panel).toHaveTextContent("primary");
    expect(panel).toHaveTextContent("adapter");
    expect(panel).toHaveTextContent("incomplete");
    const declared = within(panel).getAllByRole("article");
    expect(declared).toHaveLength(3);
    expect(declared[2]).toHaveTextContent(/Bits\s*Not observed/u);
    expect(declared[2]).toHaveTextContent(
        /Logical weight bytes\s*Not observed/u,
    );
    expect(
        screen.queryByText(/GPU fit|VRAM required/u),
    ).not.toBeInTheDocument();
});
test("revision selection and browser history keep the exact pair while local file pages reset", async () => {
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "revisions" }),
    );
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", {
            name: "View publication " + second.publicationId,
        }),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(second);
    expect(window.location.hash).toContain(
        "publication_id=" + second.publicationId,
    );
    await userEvent.click(
        screen.getByRole("tab", { name: "Files & manifest" }),
    );
    await fixture.loaded();
    await userEvent.click(screen.getByRole("button", { name: "Next files" }));
    expect(screen.getByText("file-25.txt")).toBeInTheDocument();
    await act(async () => {
        window.history.replaceState(
            null,
            "",
            repositoryPath(target, "/ui/") +
                repositoryFragment({ pair: first, tab: "files" }),
        );
        window.dispatchEvent(new PopStateEvent("popstate"));
        await Promise.resolve();
    });
    await fixture.loaded();
    expect(fixture.store.snapshot().selected).toMatchObject(first);
    expect(screen.getByText("file-00.txt")).toBeInTheDocument();
    expect(screen.queryByText("file-25.txt")).not.toBeInTheDocument();
});
test("a model-to-dataset route change cannot render a late old model payload", async () => {
    const gate = deferred<Response>();
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "files" }),
        target,
        (url, fallback) =>
            url.pathname.includes("/model/") &&
            url.pathname.includes("/manifests/")
                ? gate.promise
                : fallback(),
    );
    await waitFor(() => {
        expect(
            fixture.seen.some((url) => url.pathname.includes("/manifests/")),
        ).toBe(true);
    });
    const dataset: RepositoryTarget = { ...target, repositoryType: "dataset" };
    await act(async () => {
        window.history.replaceState(
            null,
            "",
            repositoryPath(dataset, "/ui/") +
                repositoryFragment({ pair: first, tab: "details" }),
        );
        fixture.rerender(
            <RepositoryDetail
                store={fixture.store}
                target={dataset}
                basePath="/ui/"
            />,
        );
        await Promise.resolve();
    });
    await fixture.loaded();
    await act(async () => {
        gate.resolve(
            jsonResponse(
                wire("manifest read", {
                    tree_base: "archive-root/",
                    manifest: manifest(target, first, 1),
                }),
            ),
        );
        await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(fixture.store.snapshot().target?.repositoryType).toBe("dataset");
    expect(
        screen.getByRole("tab", { name: "Dataset details" }),
    ).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("owned-config")).toBeInTheDocument();
    expect(screen.queryByText(markup)).not.toBeInTheDocument();
});

test("a cached ready remount rejects an invalid bookmark without revealing or rewriting old selection", async () => {
    const fixture = setup();
    await fixture.loaded();
    fixture.unmount();
    const before = fixture.seen.length;
    const invalid = "#commit_sha=" + first.commitSha;
    window.history.replaceState(
        null,
        "",
        repositoryPath(target, "/ui/") + invalid,
    );
    render(
        <RepositoryDetail
            store={fixture.store}
            target={target}
            basePath="/ui/"
        />,
    );
    await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
            /invalid or unsupported selection fields/u,
        );
    });
    expect(window.location.hash).toBe(invalid);
    expect(fixture.seen).toHaveLength(before);
    expect(
        screen.queryByRole("region", { name: "Selected publication" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(markup)).not.toBeInTheDocument();
    expect(
        screen.queryByRole("button", { name: "Copy commit SHA" }),
    ).not.toBeInTheDocument();
});

test("a mounted old target cannot rewrite or read a different pathname on browser history", async () => {
    const fixture = setup();
    await fixture.loaded();
    const before = fixture.seen.length;
    await act(async () => {
        window.history.pushState(null, "", "/ui/library#q=owned");
        window.dispatchEvent(new PopStateEvent("popstate"));
        await Promise.resolve();
    });
    expect(window.location.pathname + window.location.hash).toBe(
        "/ui/library#q=owned",
    );
    expect(fixture.seen).toHaveLength(before);
    expect(
        screen.queryByRole("region", { name: "Selected publication" }),
    ).not.toBeInTheDocument();
});

test("keyboard tabs rove focus and selection with Home End and wrapping arrows", async () => {
    const fixture = setup();
    await fixture.loaded();
    const user = userEvent.setup();
    screen.getByRole("tab", { name: "Overview" }).focus();
    for (const [key, name, tab] of [
        ["{ArrowRight}", "Variants", "details"],
        ["{End}", "Activity", "activity"],
        ["{Home}", "Overview", "overview"],
        ["{ArrowLeft}", "Activity", "activity"],
    ] as const) {
        await user.keyboard(key);
        await fixture.loaded();
        const selected = screen.getByRole("tab", { name });
        await waitFor(() => {
            expect(selected).toHaveFocus();
        });
        expect(selected).toHaveAttribute("aria-selected", "true");
        expect(selected).toHaveAttribute("tabindex", "0");
        expect(window.location.hash).toContain("tab=" + tab);
        expect(
            screen.getAllByRole("tab").filter((node) => node.tabIndex === 0),
        ).toEqual([selected]);
    }
});

test("large valid reports page diagnostics locally and qualify only the exact repository and generation", async () => {
    const errors = Array.from({ length: 26 }, () => "HFVER007");
    const warnings = Array.from({ length: 26 }, () => "HFWRN011");
    const row = {
        ...runReport.repositories[0],
        repository_type: "model",
        repository_id: target.repositoryId,
        resolved_commit_sha: first.commitSha,
        publication_id: first.publicationId,
        publication_generation: 1,
        status: "failed",
        downloaded_bytes: 0,
        hashed_bytes: 0,
        reused_bytes: 0,
        file_count: 0,
        errors,
        warnings,
    };
    // Run reports require unique, sorted type/ID rows. Unrelated entries must
    // remain unrelated even when their publication fields happen to coincide.
    const report = {
        ...runReport,
        config_fingerprint: "2".repeat(64),
        outcome: "failed",
        exit_code: 20,
        errors,
        warnings,
        repositories: [
            row,
            ...Array.from({ length: 25 }, (_, index) => ({
                ...row,
                repository_id: "owner/z" + String(index).padStart(2, "0"),
            })),
        ],
        totals: {
            downloaded_bytes: 0,
            hashed_bytes: 0,
            pruned_logical_bytes: 0,
            published_bytes: 0,
            reused_bytes: 0,
            xet_cache_peak_bytes: 0,
        },
    };
    const fixture = setup(
        repositoryFragment({ pair: first, tab: "activity" }),
        target,
        (url, fallback) => {
            if (url.pathname !== "/api/v1/runs/" + runReport.run_id)
                return fallback();
            const result = wire("runs read", { report });
            return jsonResponse({
                ...result,
                envelope: { ...result.envelope, run_id: runReport.run_id },
            });
        },
    );
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", {
            name: "Inspect report " + runReport.run_id,
        }),
    );
    await waitFor(() => {
        expect(fixture.store.snapshot().report.phase).toBe("ready");
    });
    expect(
        screen.getByText(
            /1 loaded repository entries match the selected type, ID, SHA, publication ID and generation/u,
        ),
    ).toBeInTheDocument();
    for (const name of [
        "entry warnings",
        "entry errors",
        "report warnings",
        "report errors",
    ]) {
        expect(
            within(screen.getByRole("list", { name })).getAllByRole("listitem"),
        ).toHaveLength(25);
    }
    const reads = fixture.seen.length;
    await userEvent.click(
        screen.getByRole("button", { name: "Next entry errors" }),
    );
    await userEvent.click(
        screen.getByRole("button", { name: "Next report warnings" }),
    );
    for (const name of ["entry errors", "report warnings"]) {
        expect(
            within(screen.getByRole("list", { name })).getAllByRole("listitem"),
        ).toHaveLength(1);
    }
    expect(
        within(
            screen.getByRole("list", { name: "report errors" }),
        ).getAllByRole("listitem"),
    ).toHaveLength(25);
    expect(fixture.seen).toHaveLength(reads);
});
