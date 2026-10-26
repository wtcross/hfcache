import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import {
    loadBootstrap,
    readInertMetadata,
    verifyBootstrapContext,
} from "../src/bootstrap";
import { App } from "../src/App";
import { mountApplication, startApplication } from "../src/mount";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";

afterEach(() => {
    vi.unstubAllGlobals();
    document.head.innerHTML = "";
});
const bootstrap = uiBootstrapFixture();
const compiled = {
    source: bootstrap.build.metadata.source_snapshot_sha256,
    application: bootstrap.build.metadata.application_version,
    wire: bootstrap.wire_source_digest,
};
test("only a reconstructed real bootstrap read can replace inert startup recovery", async () => {
    vi.stubGlobal("location", new URL(bootstrap.configured_origin + "/ui/"));
    inertUiDocument(document);
    const platform: unknown = await vi.importActual("node:crypto");
    if (
        typeof platform !== "object" ||
        platform === null ||
        !("webcrypto" in platform)
    )
        throw new Error("Native test crypto missing.");
    vi.stubGlobal("crypto", platform.webcrypto);
    const fetcher = vi.fn<typeof fetch>(() =>
        Promise.resolve(
            new Response(JSON.stringify(bootstrap), {
                headers: { "content-type": "application/json" },
            }),
        ),
    );
    expect(
        screen.getByRole("link", { name: "Reload interface" }),
    ).toBeInTheDocument();
    let unmount = () => {};
    await act(async () => {
        unmount = await startApplication(
            document,
            bootstrap.configured_origin,
            compiled,
            fetcher,
        );
    });
    expect(screen.getByText("Administrator session")).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledExactlyOnceWith(
        "https://archive.invalid/ui/bootstrap.json",
        expect.objectContaining({
            credentials: "same-origin",
            cache: "no-store",
            redirect: "error",
            method: "GET",
        }),
    );
    await act(async () => {
        screen.getByRole("button", { name: "Check interface version" }).click();
        await waitFor(() => {
            expect(fetcher).toHaveBeenCalledTimes(2);
        });
    });
    await waitFor(() => {
        expect(
            screen.getByRole("button", { name: "Check interface version" }),
        ).toBeEnabled();
    });
    act(unmount);
});
test("a DOM/bootstrap identity change refuses mount before removing recovery", () => {
    inertUiDocument(document);
    expect(() =>
        mountApplication(document, {
            ...bootstrap,
            paths: { ...bootstrap.paths, ui_base: "/other/ui/" },
        }),
    ).toThrow("identity changed");
    expect(() =>
        mountApplication(document, {
            ...bootstrap,
            build: {
                ...bootstrap.build,
                asset_manifest_sha256: "0".repeat(64),
            },
        }),
    ).toThrow("identity changed");
    expect(
        screen.getByRole("link", { name: "Reload interface" }),
    ).toBeInTheDocument();
});
test("invalid percent spelling and noncanonical encoding are refused as inert slots", () => {
    for (const base of ["/%ZZ/ui/", "/%61/ui/"]) {
        inertUiDocument(document);
        document.querySelector("base")?.setAttribute("href", base);
        document
            .querySelector('meta[name="hfcache-ui-base"]')
            ?.setAttribute("content", base);
        document
            .querySelector('meta[name="hfcache-ui-bootstrap"]')
            ?.setAttribute("content", base + "bootstrap.json");
        expect(() => readInertMetadata(document)).toThrow();
    }
});
test.each([
    "base",
    "hfcache-ui-base",
    "hfcache-ui-bootstrap",
    "hfcache-ui-fingerprint",
    "hfcache-ui-contract",
])("duplicate or missing inert %s is refused before fetch", (name) => {
    inertUiDocument(document);
    const selector = name === "base" ? "base" : `meta[name="${name}"]`,
        slot = document.querySelector(selector);
    if (slot === null) throw new Error("Missing test slot.");
    document.head.append(slot.cloneNode(true));
    expect(() => readInertMetadata(document)).toThrow();
    slot.remove();
    document.querySelector(selector)?.remove();
    expect(() => readInertMetadata(document)).toThrow();
});
test.each([
    ["base", "href", "//foreign/ui/"],
    ['meta[name="hfcache-ui-contract"]', "content", "2"],
    ['meta[name="hfcache-ui-fingerprint"]', "content", "0"],
    [
        'meta[name="hfcache-ui-bootstrap"]',
        "content",
        "https://foreign/bootstrap",
    ],
    ['meta[name="hfcache-ui-base"]', "content", "/wrong/"],
    ['meta[name="hfcache-ui-base"]', "content", "/%ZZ/ui/"],
])(
    "malformed inert slot %s/%s is refused without navigation",
    (selector, attribute, value) => {
        inertUiDocument(document);
        document.querySelector(selector)?.setAttribute(attribute, value);
        expect(() => readInertMetadata(document)).toThrow();
    },
);
test("inert metadata accepts canonical encoded Unicode prefix without changing origin", () => {
    inertUiDocument(document);
    for (const selector of ["base", 'meta[name="hfcache-ui-base"]'])
        document
            .querySelector(selector)
            ?.setAttribute(
                selector === "base" ? "href" : "content",
                "/%E7%AE%A1%E7%90%86/ui/",
            );
    document
        .querySelector('meta[name="hfcache-ui-bootstrap"]')
        ?.setAttribute("content", "/%E7%AE%A1%E7%90%86/ui/bootstrap.json");
    expect(readInertMetadata(document).base).toBe("/%E7%AE%A1%E7%90%86/ui/");
});
test.each([401, 404, 503])(
    "bootstrap HTTP%s retains fallback and cancels the owned response body",
    async (status) => {
        inertUiDocument(document);
        let canceled = false;
        const body = new ReadableStream({
            cancel() {
                canceled = true;
            },
        });
        const fetcher: typeof fetch = () =>
            Promise.resolve(new Response(body, { status }));
        await expect(
            loadBootstrap(
                document,
                bootstrap.configured_origin,
                compiled,
                fetcher,
            ),
        ).rejects.toThrow();
        await waitFor(() => {
            expect(canceled).toBe(true);
        });
        expect(
            screen.getByRole("link", { name: "Reload interface" }),
        ).toBeInTheDocument();
    },
);
test("bootstrap body bounds, strict schema, and absent WebCrypto fail closed", async () => {
    inertUiDocument(document);
    for (const body of [
        "{}",
        '{"schema_version":1,"schema_version":1}',
        " ".repeat(32769),
    ]) {
        const fetcher: typeof fetch = () =>
            Promise.resolve(
                new Response(body, {
                    headers: { "content-type": "application/json" },
                }),
            );
        await expect(
            loadBootstrap(
                document,
                bootstrap.configured_origin,
                compiled,
                fetcher,
            ),
        ).rejects.toThrow();
    }
    await expect(
        verifyBootstrapContext(
            bootstrap,
            readInertMetadata(document),
            bootstrap.configured_origin,
            compiled,
            {},
        ),
    ).rejects.toThrow("unsupported_engine");
});
test("authenticated shell distinguishes configured identity from archive health and permission availability", async () => {
    vi.stubGlobal(
        "location",
        new URL(bootstrap.configured_origin + "/ui/administration"),
    );
    window.history.replaceState(null, "", "/ui/administration");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
        new Response("{}", { status: 503 }),
    );
    render(<App basePath="/ui/" bootstrap={bootstrap} />);
    expect(screen.getByText("Configured archive")).toBeInTheDocument();
    expect(
        screen.getByText(bootstrap.configured_archive_id),
    ).toBeInTheDocument();
    expect(screen.getByText(/Signed in as administrator/)).toBeInTheDocument();
    expect(screen.getAllByRole("status")[0]).toHaveTextContent(
        "Archive health and repository data have not been requested.",
    );
    for (const name of [
        "View configuration",
        "Edit configuration",
        "View host status",
        "Stop observation",
        "Change schedules",
    ])
        expect(screen.getByText(name)).toBeInTheDocument();
    expect(
        screen.getByRole("heading", { name: "Host administration" }),
    ).toBeInTheDocument();
    await screen.findByRole("alert");
    vi.unstubAllGlobals();
});
test("lazy chunk failure shows a user-controlled update state without navigation or replay", () => {
    render(<App basePath="/ui/" bootstrap={bootstrap} />);
    const fetcher = vi.spyOn(globalThis, "fetch");
    act(() => {
        window.dispatchEvent(
            new Event("vite:preloadError", { cancelable: true }),
        );
    });
    expect(screen.getByText("Interface update required.")).toBeInTheDocument();
    expect(
        screen.getByRole("button", { name: "Reload interface" }),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ui/");
    expect(fetcher).not.toHaveBeenCalled();
});
test("manual version checks show update or observation failure without silent reload", async () => {
    const changed = vi
        .fn<() => Promise<boolean>>()
        .mockResolvedValueOnce(false)
        .mockResolvedValueOnce(true)
        .mockRejectedValueOnce(new Error("network"));
    render(
        <App basePath="/ui/" bootstrap={bootstrap} onCheckRelease={changed} />,
    );
    const button = screen.getByRole("button", {
        name: "Check interface version",
    });
    await act(async () => {
        button.click();
        await Promise.resolve();
    });
    expect(
        screen.queryByText("Interface update required."),
    ).not.toBeInTheDocument();
    await act(async () => {
        button.click();
        await Promise.resolve();
    });
    expect(screen.getByText("Interface update required.")).toBeInTheDocument();
    await act(async () => {
        button.click();
        await Promise.resolve();
    });
    expect(
        screen.getByText(/The interface version could not be checked/),
    ).toBeInTheDocument();
    expect(window.location.pathname).toBe("/ui/");
});
test("entry startup failure adds only fixed text and retains the original reload fallback", async () => {
    inertUiDocument(document);
    vi.resetModules();
    vi.stubGlobal("__HFCACHE_BUILD_SOURCE__", compiled.source);
    vi.stubGlobal("__HFCACHE_APPLICATION_VERSION__", compiled.application);
    vi.stubGlobal(
        "fetch",
        vi.fn<typeof fetch>(() =>
            Promise.resolve(
                new Response("{}", {
                    headers: { "content-type": "application/json" },
                }),
            ),
        ),
    );
    await import("../src/main");
    await waitFor(() => {
        expect(screen.getByRole("status")).toHaveTextContent(
            "The interface could not start.",
        );
    });
    expect(
        screen.getByRole("link", { name: "Reload interface" }),
    ).toBeInTheDocument();
});
