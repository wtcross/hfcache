import { afterEach, expect, test, vi } from "vitest";
import {
    InterfaceUpdateRequiredError,
    loadReconnectBootstrap,
} from "../src/bootstrap";
import { inertUiDocument, uiBootstrapFixture } from "./ui-fixtures";

const platform: unknown = await vi.importActual("node:crypto");
if (
    typeof platform !== "object" ||
    platform === null ||
    !("webcrypto" in platform)
)
    throw new Error("Native test crypto missing.");
const nativeCrypto = platform.webcrypto;
const previous = uiBootstrapFixture();
const compiled = {
    source: previous.build.metadata.source_snapshot_sha256,
    application: previous.build.metadata.application_version,
    wire: previous.wire_source_digest,
};
afterEach(() => {
    vi.unstubAllGlobals();
    document.head.innerHTML = "";
});
function setup(value: unknown) {
    inertUiDocument(document);
    vi.stubGlobal("crypto", nativeCrypto);
    const fetcher = vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify(value), {
            headers: { "Content-Type": "application/json" },
        }),
    );
    return {
        fetcher,
        load: () =>
            loadReconnectBootstrap(
                document,
                previous.configured_origin,
                compiled,
                previous,
                fetcher,
            ),
    };
}

test("same-build explicit reconnect admits a freshly verified instance and subject in one bounded read", async () => {
    const next = {
        ...previous,
        instance_id: "b".repeat(32),
        authority_epoch: "b".repeat(32),
        user: {
            ...previous.user,
            subject: "new-administrator",
            display_name: "new-administrator",
        },
    };
    const { load, fetcher } = setup(next);
    const actual = await load();
    expect(actual.instance_id).toBe(next.instance_id);
    expect(actual.user.subject).toBe("new-administrator");
    expect(actual.build).toEqual(previous.build);
    expect(fetcher).toHaveBeenCalledOnce();
    const call = fetcher.mock.calls[0];
    expect(call?.[0]).toBe("https://archive.invalid/ui/bootstrap.json");
    expect(call?.[1]?.credentials).toBe("same-origin");
    expect(call?.[1]?.redirect).toBe("error");
    expect(call?.[1]?.cache).toBe("no-store");
    expect(new Headers(call?.[1]?.headers).has("Authorization")).toBe(false);
    expect(previous.user.subject).toBe("administrator");
});

test.each(["asset", "source", "wire"] as const)(
    "a changed %s build produces a typed update refusal before private context adoption",
    async (change) => {
        const next = {
            ...previous,
            ...(change === "wire"
                ? { wire_source_digest: "f".repeat(64) }
                : {}),
            build: {
                ...previous.build,
                ...(change === "asset"
                    ? { asset_manifest_sha256: "f".repeat(64) }
                    : {}),
                metadata: {
                    ...previous.build.metadata,
                    ...(change === "source"
                        ? { source_snapshot_sha256: "f".repeat(64) }
                        : {}),
                    ...(change === "wire"
                        ? { wire_source_digest: "f".repeat(64) }
                        : {}),
                },
            },
        };
        const { load, fetcher } = setup(next);
        await expect(load()).rejects.toBeInstanceOf(
            InterfaceUpdateRequiredError,
        );
        expect(fetcher).toHaveBeenCalledOnce();
        expect(previous.build.asset_manifest_sha256).toBe("2".repeat(64));
        expect(
            document
                .querySelector('[name="hfcache-ui-fingerprint"]')
                ?.getAttribute("content"),
        ).toBe("2".repeat(64));
    },
);

test.each([
    { ...previous, configured_origin: "https://foreign.invalid" },
    { ...previous, paths: { ...previous.paths, mcp_base: null } },
    { ...previous, schema_version: 2 },
    { ...previous, authority_epoch: "invalid" },
    { ...previous, password: "private-secret-must-not-be-printed" },
])(
    "foreign or malformed reconnect context cannot be mistaken for an available build",
    async (value) => {
        const { load, fetcher } = setup(value);
        const result = await load().then(
            () => null,
            (error: unknown) => error,
        );
        expect(result).toBeInstanceOf(Error);
        expect(result).not.toBeInstanceOf(InterfaceUpdateRequiredError);
        expect(String(result)).not.toContain(
            "private-secret-must-not-be-printed",
        );
        expect(fetcher).toHaveBeenCalledOnce();
    },
);

test("same-build reconnect still verifies exact inert, compiled and toolchain identities", async () => {
    for (const change of ["compiled", "fingerprint", "toolchain"] as const) {
        const { fetcher } = setup(
            change === "toolchain"
                ? {
                      ...previous,
                      build: {
                          ...previous.build,
                          metadata: {
                              ...previous.build.metadata,
                              toolchain_sha256: "f".repeat(64),
                          },
                      },
                  }
                : previous,
        );
        if (change === "fingerprint")
            document
                .querySelector('[name="hfcache-ui-fingerprint"]')
                ?.setAttribute("content", "f".repeat(64));
        const result = loadReconnectBootstrap(
            document,
            previous.configured_origin,
            change === "compiled"
                ? { ...compiled, source: "f".repeat(64) }
                : compiled,
            previous,
            fetcher,
        );
        await expect(result).rejects.toThrow();
        expect(fetcher).toHaveBeenCalledOnce();
    }
});

test("a foreign caller origin refuses before ambient credentials can be sent", async () => {
    const { fetcher } = setup(previous);
    await expect(
        loadReconnectBootstrap(
            document,
            "https://foreign.invalid",
            compiled,
            previous,
            fetcher,
        ),
    ).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
});

test("reconnect preserves the existing bootstrap byte ceiling and never retries", async () => {
    const { fetcher } = setup(previous);
    fetcher.mockResolvedValue(
        new Response(" ".repeat(32769), {
            headers: { "Content-Type": "application/json" },
        }),
    );
    await expect(
        loadReconnectBootstrap(
            document,
            previous.configured_origin,
            compiled,
            previous,
            fetcher,
        ),
    ).rejects.toThrow();
    expect(fetcher).toHaveBeenCalledOnce();
});
