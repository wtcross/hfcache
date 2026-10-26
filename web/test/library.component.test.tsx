/** WEB012 view regressions through the real session/store/typed client boundary. */
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
import { Library } from "../src/components/Library";
import { createLibraryStore } from "../src/library/library-state";
import type { LibraryStore } from "../src/library/library-state";
import { createSessionController } from "../src/state/session-controller";
import type { SessionController } from "../src/state/session-controller";
import type { CatalogEntry } from "../src/wire/generated";
import {
    ARCHIVE_ID,
    jsonResponse,
    readWire,
    statusPayload,
} from "./read-fixtures";
import { uiBootstrapFixture } from "./ui-fixtures";
import { deferred } from "./state-fixtures";

const sha = "a".repeat(40),
    oldSha = "b".repeat(40),
    publication = "c".repeat(32),
    oldPublication = "d".repeat(32);
const at = "2026-10-20T12:00:00.000000Z";
const owned: { controller: SessionController; store: LibraryStore }[] = [];
afterEach(() => {
    cleanup();
    for (const item of owned.splice(0)) {
        item.store.dispose();
        item.controller.dispose();
    }
    window.localStorage.clear();
    vi.unstubAllGlobals();
});
function entries(url: URL): readonly CatalogEntry[] {
    const retained = url.searchParams.get("revision_scope") === "retained";
    const model: CatalogEntry = {
        repository_type: "model",
        repository_id: "owner/shared",
        tags: ["gpu"],
        tag_origin: "configured",
        tag_observed_at: null,
        curation_fingerprint: null,
        configured: true,
        enabled: false,
        archived: true,
        matching_variant_count: 1,
        representative_variant: {
            commit_sha: retained ? oldSha : sha,
            publication_id: retained ? oldPublication : publication,
            publication_generation: retained ? 1 : 2,
            variant: {
                variant_id: "e".repeat(64),
                format: "gguf",
                encoding: "Q4_0",
                quantization: "Q4_0",
                quantization_method: "ggml",
                bits: 4,
                group_size: null,
                role: "primary",
                members: [{ path: "weight.gguf", size_bytes: 17 }],
                total_bytes: 17,
                completeness: "complete",
                evidence: "header",
                source_paths: ["weight.gguf"],
                diagnostics: [],
            },
        },
        dataset_formats: [],
    };
    const dataset: CatalogEntry = {
        repository_type: "dataset",
        repository_id: "owner/shared",
        tags: ["history"],
        tag_origin: "last_observed",
        tag_observed_at: at,
        curation_fingerprint: null,
        configured: false,
        enabled: null,
        archived: true,
        matching_variant_count: 0,
        representative_variant: null,
        dataset_formats: ["parquet"],
    };
    return [dataset, model].filter(
        (row) =>
            !url.searchParams.has("type") ||
            row.repository_type === url.searchParams.get("type"),
    );
}
function coverage(
    url: URL,
    rows: readonly CatalogEntry[],
    incomplete: boolean,
) {
    const count = incomplete ? 1 : rows.length;
    return {
        repositories: count,
        tags_known: incomplete ? 0 : count,
        tags_unknown: incomplete ? 1 : 0,
        publications: count,
        usable: incomplete ? 0 : count,
        partial: 0,
        unsupported: 0,
        failed: 0,
        missing: incomplete ? count : 0,
        technical_required: [
            "format",
            "quantization",
            "quantization_method",
            "bits",
            "max_variant_bytes",
        ].some((key) => url.searchParams.has(key)),
        incomplete,
    };
}
function response(
    command: string,
    payload: unknown,
    incomplete = false,
    cursor: string | null = null,
) {
    const wire = readWire(command, payload);
    return jsonResponse({
        ...wire,
        archive_id: ARCHIVE_ID,
        config_fingerprint: "2".repeat(64),
        next_cursor: cursor,
        envelope: incomplete
            ? {
                  ...wire.envelope,
                  outcome: "success_with_warnings",
                  warnings: [
                      {
                          code: "HFWRN011",
                          message: "Incomplete fixture metadata",
                          repository: null,
                          context: {},
                      },
                  ],
              }
            : wire.envelope,
    });
}
function urlOf(input: RequestInfo | URL): URL {
    return input instanceof URL
        ? input
        : new URL(typeof input === "string" ? input : input.url);
}
function mount(
    fragment = "",
    incomplete = false,
    override?: (url: URL) => Response | Promise<Response> | undefined,
) {
    window.history.replaceState(null, "", "/ui/library" + fragment);
    window.localStorage.clear();
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: window.location.origin,
        configured_archive_id: ARCHIVE_ID,
    };
    const fetcher = vi.fn<typeof fetch>((input, init) => {
        expect(init?.method).toBe("GET");
        const url = urlOf(input);
        expect(url.origin).toBe(window.location.origin);
        const replacement = override?.(url);
        if (replacement !== undefined) return Promise.resolve(replacement);
        const rows = incomplete ? [] : entries(url);
        const common = {
            schema_version: 1,
            catalog_identity: "f".repeat(64),
            coverage: coverage(url, rows, incomplete),
        };
        if (url.pathname === "/api/v1/catalog/search")
            return Promise.resolve(
                response(
                    "catalog.search",
                    { ...common, total_matches: rows.length, entries: rows },
                    incomplete,
                ),
            );
        if (url.pathname === "/api/v1/catalog/facets")
            return Promise.resolve(
                response(
                    "catalog.facets",
                    {
                        ...common,
                        facet: url.searchParams.get("facet"),
                        total_matches: 0,
                        entries: [],
                    },
                    incomplete,
                ),
            );
        const all = entries(new URL(window.location.origin));
        if (url.pathname === "/api/v1/repositories")
            return Promise.resolve(
                response("list", {
                    repositories: [...all].reverse().map((row) => ({
                        repository_type: row.repository_type,
                        repository_id: row.repository_id,
                        managed: row.configured,
                        enabled: row.enabled,
                        current_commit_sha: sha,
                        current_publication_id: publication,
                        retained_revisions: 2,
                    })),
                }),
            );
        if (url.pathname === "/api/v1/status")
            return Promise.resolve(
                response("status", {
                    ...statusPayload(true),
                    repositories: [...all].reverse().map((row) => ({
                        repository_type: row.repository_type,
                        repository_id: row.repository_id,
                        managed: row.configured,
                        enabled: row.enabled,
                        current_commit_sha: sha,
                        current_publication_generation: 2,
                        last_run_status: null,
                        requested_revision: row.configured ? "main" : null,
                        retained_generations: [1, 2],
                        retained_revisions: 2,
                        upstream_state: "unknown",
                        verification_state: "verified",
                    })),
                }),
            );
        if (url.pathname === "/api/v1/repositories/revisions")
            return Promise.resolve(
                response("list", {
                    revisions: all.flatMap((row) => [
                        {
                            repository_type: row.repository_type,
                            repository_id: row.repository_id,
                            commit_sha: oldSha,
                            publication_id: oldPublication,
                            publication_generation: 1,
                            file_count: 1,
                            published_at: at,
                            total_bytes: 17,
                            verification_state: "unverified",
                        },
                        {
                            repository_type: row.repository_type,
                            repository_id: row.repository_id,
                            commit_sha: sha,
                            publication_id: publication,
                            publication_generation: 2,
                            file_count: 2,
                            published_at: at,
                            total_bytes:
                                row.repository_type === "model" ? 4096 : 8192,
                            verification_state: "verified",
                        },
                    ]),
                }),
            );
        throw new Error("Unexpected Library read.");
    });
    const controller = createSessionController({
        bootstrap,
        storage: window.localStorage,
        fetcher,
        reconnect: () => Promise.resolve(bootstrap),
    });
    const store = createLibraryStore(controller);
    owned.push({ controller, store });
    const view = render(<Library store={store} />);
    const searches = () =>
        fetcher.mock.calls
            .map(([input]) => urlOf(input))
            .filter((url) => url.pathname === "/api/v1/catalog/search");
    const loaded = async () => {
        await waitFor(() => {
            expect(store.snapshot().phase).toBe(
                incomplete ? "partial_empty" : "ready",
            );
        });
        await waitFor(() => {
            expect(store.snapshot().refreshing).toBe(false);
        });
    };
    return { store, controller, fetcher, searches, loaded, ...view };
}

test("Clear filters replaces optional fields and All repositories really removes type", async () => {
    const fixture = mount(
        "#type=model&q=owner&tag_all=gpu&format=gguf&bits=4&max_variant_bytes=100",
    );
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("button", { name: "Clear filters" }),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().filters).toEqual({
        scope: "all",
        revision_scope: "current",
        tag_source: "current_or_last_observed",
        limit: 25,
    });
    expect(
        screen.getByRole("searchbox", { name: "Find repositories" }),
    ).toHaveValue("");
    expect(fixture.searches().at(-1)?.searchParams.has("q")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Models" }));
    await fixture.loaded();
    expect(fixture.store.snapshot().filters.type).toBe("model");
    await userEvent.click(
        screen.getByRole("button", { name: "All repositories" }),
    );
    await fixture.loaded();
    expect(fixture.store.snapshot().filters.type).toBeUndefined();
    expect(fixture.searches().at(-1)?.searchParams.has("type")).toBe(false);
});
test("invalid bookmarked filters make zero GETs until explicitly cleared", async () => {
    const fixture = mount("#unreviewed=private-fragment");
    await waitFor(() => {
        expect(screen.getByRole("alert")).toHaveTextContent(
            /invalid or unsupported filters/u,
        );
    });
    expect(fixture.fetcher).not.toHaveBeenCalled();
    expect(
        screen.getByRole("button", { name: "Refresh library" }),
    ).toBeDisabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Clear filters" }),
    );
    await fixture.loaded();
    expect(fixture.searches()).toHaveLength(1);
    expect(window.location.search).toBe("");
    expect(window.location.hash).not.toContain("unreviewed");
});
test("search debounces to the last raw literal and unmount cancels a pending draft", async () => {
    const fixture = mount();
    await fixture.loaded();
    const before = fixture.searches().length;
    const search = screen.getByRole("searchbox", { name: "Find repositories" });
    fireEvent.change(search, { target: { value: "owner" } });
    fireEvent.change(search, { target: { value: "STRAẞE e\u0301" } });
    expect(fixture.searches()).toHaveLength(before);
    await act(() => new Promise((resolve) => setTimeout(resolve, 400)));
    await fixture.loaded();
    expect(fixture.searches()).toHaveLength(before + 1);
    expect(fixture.searches().at(-1)?.searchParams.get("q")).toBe(
        "STRAẞE e\u0301",
    );
    fireEvent.change(search, { target: { value: "never-requested" } });
    fixture.unmount();
    await act(() => new Promise((resolve) => setTimeout(resolve, 400)));
    expect(fixture.searches()).toHaveLength(before + 1);
});
test("dataset switch clears only model predicates, keeps format and announces the transition", async () => {
    const fixture = mount(
        "#type=model&format=gguf&quantization=Q4_0&quantization_method=ggml&bits=4&max_variant_bytes=100",
    );
    await fixture.loaded();
    await userEvent.click(screen.getByRole("button", { name: "Datasets" }));
    await fixture.loaded();
    expect(fixture.store.snapshot().filters).toMatchObject({
        type: "dataset",
        format: "gguf",
    });
    const query = fixture.searches().at(-1)?.searchParams;
    for (const field of [
        "quantization",
        "quantization_method",
        "bits",
        "max_variant_bytes",
    ])
        expect(query?.has(field)).toBe(false);
    expect(
        screen.getByText(
            "Model-only variant filters were cleared for datasets.",
        ),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Bits" })).toBeDisabled();
    expect(screen.getByRole("textbox", { name: "Bits" })).toHaveValue("");
});
test("type-identical names retain distinct selectors and exact current size joins", async () => {
    const fixture = mount("#revision_scope=retained");
    await fixture.loaded();
    const modelBox = screen.getByRole("checkbox", {
        name: "Select model owner/shared",
    });
    const datasetBox = screen.getByRole("checkbox", {
        name: "Select dataset owner/shared",
    });
    const modelRow = modelBox.closest("tr"),
        datasetRow = datasetBox.closest("tr");
    if (modelRow === null || datasetRow === null)
        throw new Error("Missing repository row.");
    expect(within(modelRow).getByText("4 KiB")).toBeInTheDocument();
    expect(within(datasetRow).getByText("8 KiB")).toBeInTheDocument();
    expect(
        within(modelRow).getByText(sha, { selector: "code" }),
    ).toBeInTheDocument();
    expect(
        within(modelRow).getByText(oldSha, { selector: "code" }),
    ).toBeInTheDocument();
    expect(
        within(modelRow).getByText(oldPublication, { selector: "code" }),
    ).toBeInTheDocument();
    expect(
        within(datasetRow).queryByText(/bit declaration/u),
    ).not.toBeInTheDocument();
    await userEvent.click(modelBox);
    expect(
        screen.getByText("model:owner/shared", { selector: "pre" }),
    ).toBeInTheDocument();
    expect(datasetBox).not.toBeChecked();
});
test("zero known matches with incomplete coverage never claims complete absence", async () => {
    const fixture = mount("#q=unknown", true);
    await fixture.loaded();
    expect(
        screen.getByRole("heading", {
            name: "No known matches; metadata coverage is incomplete",
        }),
    ).toBeInTheDocument();
    expect(
        screen.getByText(
            "Coverage is incomplete. Zero known matches does not prove absence.",
        ),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("heading", {
            name: "No known matches for these filters",
        }),
    ).not.toBeInTheDocument();
    expect(
        fixture.fetcher.mock.calls.every(([, init]) => init?.method === "GET"),
    ).toBe(true);
});

test("tag and technical controls form one canonical conjunctive catalog query", async () => {
    const fixture = mount();
    await fixture.loaded();
    const before = fixture.searches().length;
    for (const [name, value] of [
        ["Require all tags", " GPU ,gpu,team:Research"],
        ["Match any tags", "owner:a, GPU"],
        ["Format", "GGUF"],
        ["Quantization method", "GGML"],
        ["Quantization scheme", "q4_0"],
        ["Bits", "4"],
        ["Maximum variant bytes", "17"],
    ]) {
        fireEvent.change(screen.getByLabelText(name ?? ""), {
            target: { value },
        });
    }
    await userEvent.click(
        screen.getByRole("button", { name: "Apply filters" }),
    );
    await fixture.loaded();
    expect(fixture.searches()).toHaveLength(before + 1);
    const query = fixture.searches().at(-1)?.searchParams;
    expect(query?.getAll("tag_all")).toEqual(["gpu", "team:research"]);
    expect(query?.getAll("tag_any")).toEqual(["gpu", "owner:a"]);
    expect(query?.get("format")).toBe("gguf");
    expect(query?.get("quantization")).toBe("Q4_0");
    expect(query?.get("quantization_method")).toBe("ggml");
    expect(query?.get("bits")).toBe("4");
    expect(query?.get("max_variant_bytes")).toBe("17");
});

test("main pages stay finite and selected identities do not return after generation changes", async () => {
    const fixture = mount("", false, (url) => {
        if (
            url.pathname !== "/api/v1/catalog/search" &&
            url.pathname !== "/api/v1/catalog/facets"
        )
            return undefined;
        const first = entries(new URL(window.location.origin));
        const model = first.find((row) => row.repository_type === "model");
        if (model === undefined) throw new Error("Missing owned model.");
        const second = { ...model, repository_id: "owner/second" };
        const common = {
            schema_version: 1,
            catalog_identity: "f".repeat(64),
            coverage: coverage(url, [...first, second], false),
        };
        if (url.pathname.endsWith("/facets"))
            return response("catalog.facets", {
                ...common,
                facet: url.searchParams.get("facet"),
                total_matches: 0,
                entries: [],
            });
        const next = url.searchParams.has("cursor");
        return response(
            "catalog.search",
            { ...common, total_matches: 3, entries: next ? [second] : first },
            false,
            next ? null : "main-page-two",
        );
    });
    await fixture.loaded();
    await userEvent.click(
        screen.getByRole("checkbox", { name: "Select model owner/shared" }),
    );
    expect(
        screen.getByText("model:owner/shared", { selector: "pre" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next page" }));
    await fixture.loaded();
    expect(fixture.store.snapshot().pageIndex).toBe(1);
    expect(fixture.searches().at(-1)?.searchParams.get("cursor")).toBe(
        "main-page-two",
    );
    expect(
        screen.getByRole("checkbox", { name: "Select model owner/second" }),
    ).not.toBeChecked();
    expect(
        screen.queryByText("model:owner/shared", { selector: "pre" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next page" })).toBeDisabled();
    await userEvent.click(
        screen.getByRole("button", { name: "Previous page" }),
    );
    await fixture.loaded();
    expect(
        screen.getByRole("checkbox", { name: "Select model owner/shared" }),
    ).not.toBeChecked();
    await userEvent.click(
        screen.getByRole("checkbox", { name: "Select loaded page" }),
    );
    await userEvent.selectOptions(
        screen.getByRole("combobox", { name: "Repository scope" }),
        "archived",
    );
    await fixture.loaded();
    expect(
        screen.getByRole("checkbox", { name: "Select loaded page" }),
    ).not.toBeChecked();
    expect(fixture.searches().at(-1)?.searchParams.has("cursor")).toBe(false);
});

test("compatible tag pages expose scoped counts and explicit continuation only", async () => {
    const fixture = mount("", false, (url) => {
        if (
            url.pathname !== "/api/v1/catalog/facets" ||
            url.searchParams.get("facet") !== "tag"
        )
            return undefined;
        const later = url.searchParams.has("cursor");
        return response(
            "catalog.facets",
            {
                schema_version: 1,
                catalog_identity: "f".repeat(64),
                coverage: coverage(url, entries(url), false),
                facet: "tag",
                total_matches: 2,
                entries: [
                    { value: later ? "history" : "gpu", repository_count: 1 },
                ],
            },
            false,
            later ? null : "tag-page-two",
        );
    });
    await fixture.loaded();
    const sidebar = screen.getByRole("complementary", {
        name: "Library evidence and tag suggestions",
    });
    expect(
        within(sidebar).getByRole("checkbox", { name: /^gpu\s*1$/u }),
    ).toBeInTheDocument();
    expect(
        within(sidebar).getByText(
            /1 values on this page of 2 known matching values/u,
        ),
    ).toBeInTheDocument();
    await userEvent.click(
        within(sidebar).getByRole("button", { name: "Load more tags" }),
    );
    await fixture.loaded();
    expect(
        within(sidebar).queryByRole("checkbox", { name: /^gpu\s*1$/u }),
    ).not.toBeInTheDocument();
    expect(
        within(sidebar).getByRole("checkbox", { name: /^history\s*1$/u }),
    ).toBeInTheDocument();
    expect(
        within(sidebar).getByRole("button", { name: "Load more tags" }),
    ).toBeDisabled();
    expect(
        fixture.fetcher.mock.calls
            .map(([input]) => urlOf(input))
            .filter((url) => url.searchParams.get("cursor") === "tag-page-two"),
    ).toHaveLength(1);
});
test("mismatched facet identity withholds counts and warns after one restart", async () => {
    const fixture = mount("", false, (url) => {
        if (url.pathname !== "/api/v1/catalog/facets") return undefined;
        return response("catalog.facets", {
            schema_version: 1,
            catalog_identity: "9".repeat(64),
            coverage: coverage(url, entries(url), false),
            facet: url.searchParams.get("facet"),
            total_matches: 1,
            entries: [{ value: "unsafe-to-join", repository_count: 1 }],
        });
    });
    await fixture.loaded();
    expect(fixture.searches()).toHaveLength(2);
    expect(
        screen.getByText(/Catalog evidence changed between reads/u),
    ).toBeInTheDocument();
    expect(
        screen.getByText(/Tag suggestions are unavailable/u),
    ).toBeInTheDocument();
    expect(
        screen.queryByRole("checkbox", { name: /unsafe-to-join/u }),
    ).not.toBeInTheDocument();
});
test("popstate and hashchange restore filter controls without any shell query", async () => {
    const fixture = mount("#type=model&q=first");
    await fixture.loaded();
    await act(async () => {
        window.history.pushState(
            null,
            "",
            "/ui/library#type=dataset&q=second&scope=configured",
        );
        window.dispatchEvent(new PopStateEvent("popstate"));
        await Promise.resolve();
    });
    await waitFor(() => {
        expect(fixture.store.snapshot().filters.type).toBe("dataset");
    });
    await fixture.loaded();
    expect(
        screen.getByRole("searchbox", { name: "Find repositories" }),
    ).toHaveValue("second");
    expect(
        screen.getByRole("combobox", { name: "Repository scope" }),
    ).toHaveValue("configured");
    await act(async () => {
        window.history.replaceState(null, "", "/ui/library#type=model&q=back");
        window.dispatchEvent(new HashChangeEvent("hashchange"));
        await Promise.resolve();
    });
    await waitFor(() => {
        expect(fixture.store.snapshot().filters.q).toBe("back");
    });
    await fixture.loaded();
    expect(
        screen.getByRole("searchbox", { name: "Find repositories" }),
    ).toHaveValue("back");
    expect(window.location.search).toBe("");
});

test.each(["capacity", "domain", "malformed"])(
    "%s failure remains unavailable rather than empty success",
    async (kind) => {
        const fixture = mount("", false, (url) => {
            if (url.pathname !== "/api/v1/catalog/search") return undefined;
            if (kind === "capacity")
                return jsonResponse(
                    {
                        request_id: "1".repeat(32),
                        code: "HFAPI005",
                        message: "Owned projection bound",
                        exit_code: 20,
                    },
                    413,
                );
            if (kind === "malformed")
                return jsonResponse({ schema_version: 99 });
            return jsonResponse({
                ...readWire("catalog.search", {}, true),
                archive_id: ARCHIVE_ID,
                config_fingerprint: "2".repeat(64),
            });
        });
        await waitFor(() => {
            expect(fixture.store.snapshot().phase).toBe("failed");
        });
        expect(screen.getByRole("alert")).toHaveTextContent(
            /unavailable or failed/u,
        );
        expect(
            screen.queryByRole("heading", {
                name: "No known matches for these filters",
            }),
        ).not.toBeInTheDocument();
        expect(screen.queryByRole("table")).not.toBeInTheDocument();
        expect(fixture.searches()).toHaveLength(1);
    },
);
test("complete zero and disconnected states have different evidence labels", async () => {
    const fixture = mount("", false, (url) => {
        if (
            url.pathname !== "/api/v1/catalog/search" &&
            url.pathname !== "/api/v1/catalog/facets"
        )
            return undefined;
        const common = {
            schema_version: 1,
            catalog_identity: "f".repeat(64),
            coverage: coverage(url, [], false),
            total_matches: 0,
            entries: [],
        };
        return url.pathname.endsWith("/search")
            ? response("catalog.search", common)
            : response("catalog.facets", {
                  ...common,
                  facet: url.searchParams.get("facet"),
              });
    });
    await waitFor(() => {
        expect(fixture.store.snapshot().phase).toBe("empty");
    });
    expect(
        screen.getByRole("heading", {
            name: "No known matches for these filters",
        }),
    ).toBeInTheDocument();
    expect(
        screen.getByText("Coverage is complete for this read scope."),
    ).toBeInTheDocument();
    await act(async () => {
        fixture.controller.disconnect();
        await Promise.resolve();
    });
    expect(
        screen.queryByRole("heading", {
            name: "No known matches for these filters",
        }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
        "Reconnect to read the current archive.",
    );
    expect(
        screen.getByRole("button", { name: "Refresh library" }),
    ).toBeDisabled();
});

test("publication/provenance/page controls and facet groups preserve canonical loaded selection", async () => {
    const fixture = mount("", false, (url) => {
        if (
            url.pathname !== "/api/v1/catalog/facets" ||
            url.searchParams.get("facet") !== "tag"
        )
            return undefined;
        return response("catalog.facets", {
            schema_version: 1,
            catalog_identity: "f".repeat(64),
            coverage: coverage(url, entries(url), false),
            facet: "tag",
            total_matches: 1,
            entries: [{ value: "gpu", repository_count: 1 }],
        });
    });
    await fixture.loaded();
    for (const [name, value] of [
        ["Publication scope", "retained"],
        ["Tag provenance", "current_only"],
        ["Rows per page", "50"],
    ]) {
        await userEvent.selectOptions(
            screen.getByRole("combobox", { name: name ?? "" }),
            value ?? "",
        );
        await fixture.loaded();
    }
    expect(fixture.searches().at(-1)?.searchParams.get("revision_scope")).toBe(
        "retained",
    );
    expect(fixture.searches().at(-1)?.searchParams.get("tag_source")).toBe(
        "current_only",
    );
    expect(fixture.searches().at(-1)?.searchParams.get("limit")).toBe("50");
    await userEvent.selectOptions(
        screen.getByRole("combobox", { name: "Facet selection group" }),
        "tag_any",
    );
    await userEvent.click(screen.getByRole("checkbox", { name: /^gpu\s*1$/u }));
    await fixture.loaded();
    expect(fixture.searches().at(-1)?.searchParams.getAll("tag_any")).toEqual([
        "gpu",
    ]);
    await userEvent.click(
        screen.getByRole("checkbox", { name: "Select loaded page" }),
    );
    const copied = vi
        .fn<(value: string) => Promise<void>>()
        .mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText: copied } });
    fireEvent.click(screen.getByRole("button", { name: "Copy selectors" }));
    await waitFor(() => {
        expect(copied).toHaveBeenCalledWith(
            "dataset:owner/shared\nmodel:owner/shared",
        );
    });
});
test("invalid numeric draft refuses without a new read or discarding valid evidence", async () => {
    const fixture = mount();
    await fixture.loaded();
    const before = fixture.searches().length;
    fireEvent.change(screen.getByLabelText("Bits"), {
        target: { value: "1.0" },
    });
    await userEvent.click(
        screen.getByRole("button", { name: "Apply filters" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/exact whole numbers/u);
    expect(fixture.searches()).toHaveLength(before);
    expect(
        screen.getByRole("checkbox", { name: "Select model owner/shared" }),
    ).toBeInTheDocument();
});
test("unmount before queued location parsing performs no hidden GET", async () => {
    const fixture = mount("#type=model");
    fixture.unmount();
    await act(async () => {
        await Promise.resolve();
    });
    expect(fixture.fetcher).not.toHaveBeenCalled();
});
test("unmount after a filter read starts rejects its late continuation and enrichment reads", async () => {
    const gate = deferred<Response>();
    let hold = false;
    const captured: URL[] = [];
    const fixture = mount("", false, (url) => {
        if (hold && url.pathname === "/api/v1/catalog/search") {
            captured.push(url);
            return gate.promise;
        }
        return undefined;
    });
    await fixture.loaded();
    const before = fixture.searches().length;
    hold = true;
    fireEvent.click(screen.getByRole("button", { name: "Models" }));
    await waitFor(() => {
        expect(fixture.searches()).toHaveLength(before + 1);
    });
    const requests = fixture.fetcher.mock.calls.length;
    fixture.unmount();
    const target = captured[0];
    if (target === undefined) throw new Error("Missing original pending read.");
    const rows = entries(target);
    await act(async () => {
        gate.resolve(
            response("catalog.search", {
                schema_version: 1,
                catalog_identity: "f".repeat(64),
                coverage: coverage(target, rows, false),
                total_matches: rows.length,
                entries: rows,
            }),
        );
        await new Promise((resolve) => setTimeout(resolve, 10));
    });
    expect(fixture.fetcher).toHaveBeenCalledTimes(requests);
});
