import {
    act,
    fireEvent,
    render,
    screen,
    waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { App } from "../src/App";
import { mountApplication } from "../src/mount";
import { createAdministrationReadStore } from "../src/administration/administration-read-state";
import { createLibraryStore } from "../src/library/library-state";
import { createRepositoryStore } from "../src/repository/repository-state";
import { createSessionController } from "../src/state/session-controller";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";
import {
    ARCHIVE_ID,
    jsonResponse,
    problemWire,
    readWire,
} from "./read-fixtures";
import { deferred, OPERATION_ID } from "./state-fixtures";

test("unconnected Library reports unavailable facts without fictional measurements or API requests", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(<App basePath="/ui/" />);
    expect(
        screen.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Archive not connected")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
        "Archive information is unavailable.",
    );
    expect(screen.getByText("Models")).toBeInTheDocument();
    expect(screen.getByText("Datasets")).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
});

test("keyboard navigation selects all four workspaces and focuses their content", async () => {
    const user = userEvent.setup();
    render(<App basePath="/ui/" />);
    await user.tab();
    expect(screen.getByRole("link", { name: "Skip to content" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("link", { name: "Library" })).toHaveFocus();
    for (const label of [
        "Operations",
        "Maintenance",
        "Administration",
        "Library",
    ]) {
        const link = screen.getByRole("link", { name: label });
        link.focus();
        await user.keyboard("{Enter}");
        expect(
            screen.getByRole("heading", { level: 1, name: label }),
        ).toBeInTheDocument();
        expect(link).toHaveAttribute("aria-current", "page");
        expect(screen.getByRole("main")).toHaveFocus();
        expect(document.title).toBe(`hfcache · ${label}`);
    }
});

test("Library navigation restores filter fragments and skip navigation preserves them", async () => {
    window.history.replaceState(null, "", "/ui/operations");
    const fragment = "#type=model&q=owner%2Frepo";
    render(<App basePath="/ui/" libraryBookmark={fragment} />);
    const library = screen.getByRole("link", { name: "Library" });
    expect(library).toHaveAttribute("href", "/ui/library" + fragment);
    await userEvent.click(library);
    expect(
        screen.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ui/library");
    expect(window.location.hash).toBe(fragment);
    await userEvent.click(
        screen.getByRole("link", { name: "Skip to content" }),
    );
    expect(screen.getByRole("main")).toHaveFocus();
    expect(window.location.hash).toBe(fragment);
});

test("unknown paths retain an explicit unavailable screen and a safe Library destination", async () => {
    window.history.replaceState(null, "", "/ui/not-a-workspace");
    render(<App basePath="/ui/" />);
    expect(
        screen.getByRole("heading", { level: 1, name: "Page unavailable" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "Open Library" }));
    expect(
        screen.getByRole("heading", { level: 1, name: "Library" }),
    ).toBeInTheDocument();
});

test("mobile navigation is explicitly labelled and closes on navigation or history changes", async () => {
    render(<App basePath="/ui/" />);
    await userEvent.click(
        screen.getByRole("button", { name: "Open navigation" }),
    );
    expect(
        screen.getByRole("button", { name: "Close navigation" }),
    ).toHaveAttribute("aria-expanded", "true");
    await userEvent.click(screen.getByRole("link", { name: "Operations" }));
    expect(
        screen.getByRole("button", { name: "Open navigation" }),
    ).toHaveAttribute("aria-expanded", "false");
    act(() => {
        window.history.replaceState(null, "", "/ui/maintenance");
        window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(
        screen.getByRole("heading", { level: 1, name: "Maintenance" }),
    ).toBeInTheDocument();
});

test("session disclosure preserves deliberate controls and makes no request when opened or closed", async () => {
    const fixture = mountReadOwners();
    try {
        const summary = screen
            .getByText("Session and interface")
            .closest("summary");
        if (summary === null) throw new Error("Missing session summary");
        const details = summary.closest("details");
        expect(details).not.toHaveAttribute("open");
        expect(summary).toHaveTextContent("Authenticated");
        const before = fixture.fetcher.mock.calls.length;
        await userEvent.click(summary);
        expect(details).toHaveAttribute("open");
        expect(screen.getByRole("button", { name: "Reconnect" })).toBeEnabled();
        await userEvent.click(summary);
        expect(details).not.toHaveAttribute("open");
        expect(summary).toHaveFocus();
        expect(fixture.fetcher).toHaveBeenCalledTimes(before);
        expect(fixture.controller.snapshot().registry.records).toHaveLength(1);
    } finally {
        fixture.dispose();
    }
});

test("the mount boundary validates deployment metadata and supports owned cleanup", async () => {
    const bootstrap = uiBootstrapFixture();
    vi.stubGlobal("location", new URL(bootstrap.configured_origin + "/ui/"));
    expect(() => mountApplication(document, bootstrap)).toThrow("container");
    const container = document.createElement("div");
    container.id = "root";
    document.body.append(container);
    expect(() => mountApplication(document, bootstrap)).toThrow();
    container.remove();
    inertUiDocument(document);
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(jsonResponse(problemWire("HFAPI019", 20), 503)),
    );
    let unmount = () => {};
    act(() => {
        unmount = mountApplication(document, bootstrap, fetcher);
    });
    await waitFor(() => {
        expect(
            screen.getByRole("heading", { level: 1, name: "Library" }),
        ).toBeInTheDocument();
    });
    act(unmount);
    expect(document.getElementById("root")).toBeEmptyDOMElement();
});

function mountReadOwners(first?: Promise<Response>, path = "/ui/operations") {
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", path);
    const bootstrap = {
        ...uiBootstrapFixture(),
        configured_origin: window.location.origin,
        configured_archive_id: ARCHIVE_ID,
    };
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(jsonResponse(problemWire("HFAPI019", 20), 503)),
    );
    if (first !== undefined) fetcher.mockImplementationOnce(() => first);
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
    controller.importHandle({ kind: "id", operationId: OPERATION_ID });
    const ownedLibrary = createLibraryStore(controller);
    const library = {
        ...ownedLibrary,
        pause: vi.fn(ownedLibrary.pause),
        refresh: vi.fn(ownedLibrary.refresh),
        setPageActive: vi.fn(ownedLibrary.setPageActive),
    };
    const ownedRepository = createRepositoryStore(controller);
    const repository = {
        ...ownedRepository,
        pause: vi.fn(ownedRepository.pause),
        refresh: vi.fn(ownedRepository.refresh),
        setPageActive: vi.fn(ownedRepository.setPageActive),
    };
    const ownedAdministration = createAdministrationReadStore(controller);
    const administrationRead = {
        ...ownedAdministration,
        setPageActive: vi.fn(ownedAdministration.setPageActive),
    };
    const view = render(
        <App
            basePath="/ui/"
            bootstrap={bootstrap}
            controller={controller}
            session={controller.snapshot()}
            library={library}
            repository={repository}
            administrationRead={administrationRead}
        />,
    );
    return {
        ...view,
        controller,
        library,
        repository,
        administrationRead,
        fetcher,
        saved: () => saved,
        dispose() {
            view.unmount();
            ownedLibrary.dispose();
            ownedRepository.dispose();
            ownedAdministration.dispose();
            controller.dispose();
        },
    };
}

function requestUrl(input: RequestInfo | URL | undefined): URL {
    if (input === undefined) throw new Error("Expected an owned request.");
    return input instanceof URL
        ? input
        : new URL(typeof input === "string" ? input : input.url);
}

const emptyCatalog = () =>
    jsonResponse({
        ...readWire("catalog.search", {
            schema_version: 1,
            catalog_identity: "f".repeat(64),
            coverage: {
                repositories: 0,
                tags_known: 0,
                tags_unknown: 0,
                publications: 0,
                usable: 0,
                partial: 0,
                unsupported: 0,
                failed: 0,
                missing: 0,
                technical_required: false,
                incomplete: false,
            },
            total_matches: 0,
            entries: [],
        }),
        archive_id: ARCHIVE_ID,
        config_fingerprint: "2".repeat(64),
    });

test.each(["beforeunload", "pagehide"])(
    "%s fences pending read batches without changing original operation ownership",
    async (event) => {
        for (const owner of ["library", "repository", "administration"]) {
            const slow = deferred<Response>();
            const fixture = mountReadOwners(slow.promise);
            try {
                const records = fixture.controller.snapshot().registry.records;
                const saved = fixture.saved();
                let work: Promise<void> = Promise.resolve();
                act(() => {
                    if (owner === "library") work = fixture.library.refresh();
                    else if (owner === "repository")
                        work = fixture.repository.open(
                            {
                                repositoryType: "model",
                                repositoryId: "owner/repo",
                            },
                            { pair: null, tab: "overview" },
                        );
                    else {
                        fixture.administrationRead.setPageActive(true);
                        work = fixture.administrationRead.refresh();
                    }
                });
                await waitFor(() => {
                    expect(fixture.fetcher).toHaveBeenCalledOnce();
                });
                const signal = fixture.fetcher.mock.calls[0]?.[1]?.signal;
                expect(signal?.aborted).toBe(false);
                const leave = new Event(event, { cancelable: true });
                act(() => {
                    window.dispatchEvent(leave);
                });
                expect(leave.defaultPrevented).toBe(false);
                expect(signal?.aborted).toBe(true);
                await act(async () => {
                    slow.resolve(
                        owner === "library"
                            ? emptyCatalog()
                            : jsonResponse(problemWire("HFAPI019", 20), 503),
                    );
                    await work;
                });
                expect(fixture.fetcher).toHaveBeenCalledOnce();
                expect(fixture.controller.snapshot().registry.records).toEqual(
                    records,
                );
                expect(fixture.saved()).toBe(saved);
                expect(fixture.controller.snapshot().connection).toBe(
                    "connected",
                );
            } finally {
                fixture.dispose();
            }
        }
    },
);

test.each([
    ["/ui/library", "library"],
    ["/ui/repositories/model/owner/repo", "repository"],
    ["/ui/administration", "administration"],
    ["/ui/operations", "none"],
])(
    "a persisted pageshow restores only the current %s read owner once",
    (path, owner) => {
        const fixture = mountReadOwners();
        try {
            act(() => {
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
            });
            expect(fixture.fetcher).not.toHaveBeenCalled();
            expect(fixture.library.refresh).not.toHaveBeenCalled();
            act(() => {
                window.dispatchEvent(
                    new Event("beforeunload", { cancelable: true }),
                );
                window.dispatchEvent(
                    new PageTransitionEvent("pagehide", { persisted: true }),
                );
                window.dispatchEvent(
                    new PageTransitionEvent("pagehide", { persisted: true }),
                );
            });
            expect(
                fixture.library.setPageActive,
            ).toHaveBeenCalledExactlyOnceWith(false);
            expect(
                fixture.repository.setPageActive,
            ).toHaveBeenCalledExactlyOnceWith(false);
            expect(
                fixture.administrationRead.setPageActive,
            ).toHaveBeenCalledExactlyOnceWith(false);
            window.history.replaceState(null, "", path);
            act(() => {
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
            });
            expect(fixture.library.setPageActive.mock.calls).toEqual(
                owner === "library" ? [[false], [true]] : [[false]],
            );
            expect(fixture.repository.setPageActive.mock.calls).toEqual(
                owner === "repository" ? [[false], [true]] : [[false]],
            );
            expect(fixture.administrationRead.setPageActive.mock.calls).toEqual(
                owner === "administration" ? [[false], [true]] : [[false]],
            );
            expect(fixture.controller.snapshot().registry.records).toHaveLength(
                1,
            );
        } finally {
            fixture.dispose();
        }
    },
);

test("a prior unload veto and cleaned-up document listeners cannot suspend or restart reads", () => {
    const veto = (event: Event) => {
        event.preventDefault();
    };
    window.addEventListener("beforeunload", veto);
    const fixture = mountReadOwners();
    try {
        act(() => {
            window.dispatchEvent(
                new Event("beforeunload", { cancelable: true }),
            );
            window.dispatchEvent(
                new PageTransitionEvent("pageshow", { persisted: true }),
            );
        });
        expect(fixture.library.pause).not.toHaveBeenCalled();
        expect(fixture.repository.pause).not.toHaveBeenCalled();
        expect(fixture.library.setPageActive).not.toHaveBeenCalled();
        expect(fixture.repository.setPageActive).not.toHaveBeenCalled();
        expect(fixture.administrationRead.setPageActive).not.toHaveBeenCalled();
        fixture.unmount();
        window.removeEventListener("beforeunload", veto);
        window.dispatchEvent(new Event("beforeunload", { cancelable: true }));
        window.dispatchEvent(
            new PageTransitionEvent("pagehide", { persisted: true }),
        );
        window.dispatchEvent(
            new PageTransitionEvent("pageshow", { persisted: true }),
        );
        expect(fixture.library.pause).not.toHaveBeenCalled();
        expect(fixture.repository.pause).not.toHaveBeenCalled();
        expect(fixture.library.setPageActive).not.toHaveBeenCalled();
        expect(fixture.repository.setPageActive).not.toHaveBeenCalled();
        expect(fixture.administrationRead.setPageActive).not.toHaveBeenCalled();
        expect(fixture.fetcher).not.toHaveBeenCalled();
    } finally {
        window.removeEventListener("beforeunload", veto);
        fixture.dispose();
    }
});

test.each([
    ["/ui/library", "#q=returned", "/api/v1/catalog/search"],
    [
        "/ui/repositories/model/owner/repo",
        "#tab=activity",
        "/api/v1/repositories/model/owner/repo/references/current",
    ],
])(
    "document suspension fences queued %s mount reads and restores current fragment ownership",
    async (path, fragment, expectedPath) => {
        const fixture = mountReadOwners(undefined, path);
        try {
            act(() => {
                window.dispatchEvent(
                    new Event("beforeunload", { cancelable: true }),
                );
            });
            await act(async () => {
                await Promise.resolve();
            });
            expect(fixture.fetcher).not.toHaveBeenCalled();
            expect(fixture.library.snapshot().pageActive).toBe(false);
            expect(fixture.repository.snapshot().pageActive).toBe(false);
            window.history.replaceState(null, "", path + fragment);
            await act(async () => {
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
                await Promise.resolve();
            });
            await waitFor(() => {
                expect(fixture.fetcher).toHaveBeenCalled();
            });
            const first = fixture.fetcher.mock.calls[0]?.[0];
            const url = requestUrl(first);
            expect(url.pathname).toBe(expectedPath);
            if (path === "/ui/library") {
                expect(url.searchParams.get("q")).toBe("returned");
                expect(fixture.library.snapshot().filters.q).toBe("returned");
            } else
                expect(fixture.repository.snapshot().view.tab).toBe("activity");
            expect(
                fixture.fetcher.mock.calls.every(
                    ([, init]) => init?.method === "GET",
                ),
            ).toBe(true);
        } finally {
            fixture.dispose();
        }
    },
);

test("document suspension cancels a queued Library search and SPA return still owns fresh reads", async () => {
    const fixture = mountReadOwners(undefined, "/ui/library");
    try {
        await waitFor(() => {
            expect(fixture.fetcher).toHaveBeenCalledOnce();
        });
        fireEvent.change(
            screen.getByRole("searchbox", { name: "Find repositories" }),
            { target: { value: "never-transmitted" } },
        );
        act(() => {
            window.dispatchEvent(
                new Event("beforeunload", { cancelable: true }),
            );
        });
        await act(() => new Promise((resolve) => setTimeout(resolve, 400)));
        expect(fixture.fetcher).toHaveBeenCalledOnce();
        expect(window.location.hash).not.toContain("never-transmitted");
        await act(async () => {
            window.dispatchEvent(
                new PageTransitionEvent("pageshow", { persisted: true }),
            );
            await Promise.resolve();
        });
        await waitFor(() => {
            expect(fixture.fetcher).toHaveBeenCalledTimes(2);
        });
        await userEvent.click(screen.getByRole("link", { name: "Operations" }));
        expect(fixture.library.snapshot().pageActive).toBe(false);
        await userEvent.click(screen.getByRole("link", { name: "Library" }));
        await waitFor(() => {
            expect(fixture.fetcher).toHaveBeenCalledTimes(3);
        });
        expect(fixture.library.snapshot().pageActive).toBe(true);
    } finally {
        fixture.dispose();
    }
});

test.each([
    ["/ui/library", "#q=after-freeze"],
    ["/ui/repositories/model/owner/repo", "#tab=activity"],
])(
    "pageshow restores %s even when React cannot render the intervening pagehide",
    async (path, fragment) => {
        const fixture = mountReadOwners(undefined, path);
        try {
            await act(async () => {
                await Promise.resolve();
                if (path === "/ui/library") await fixture.library.refresh();
                else await fixture.repository.refresh();
            });
            const before = fixture.fetcher.mock.calls.length;
            expect(before).toBeGreaterThan(0);
            await act(async () => {
                window.dispatchEvent(
                    new Event("beforeunload", { cancelable: true }),
                );
                window.dispatchEvent(
                    new PageTransitionEvent("pagehide", { persisted: true }),
                );
                window.history.replaceState(null, "", path + fragment);
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
                await Promise.resolve();
            });
            await waitFor(() => {
                expect(fixture.fetcher.mock.calls.length).toBeGreaterThan(
                    before,
                );
            });
            if (path === "/ui/library") {
                expect(fixture.library.snapshot().filters.q).toBe(
                    "after-freeze",
                );
                expect(
                    requestUrl(
                        fixture.fetcher.mock.calls[before]?.[0],
                    ).searchParams.get("q"),
                ).toBe("after-freeze");
            } else
                expect(fixture.repository.snapshot().view.tab).toBe("activity");
            const after = fixture.fetcher.mock.calls.length;
            await act(async () => {
                window.dispatchEvent(
                    new PageTransitionEvent("pageshow", { persisted: true }),
                );
                await Promise.resolve();
            });
            expect(fixture.fetcher).toHaveBeenCalledTimes(after);
        } finally {
            fixture.dispose();
        }
    },
);
