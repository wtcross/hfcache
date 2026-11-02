/** Owned synthetic API bodies around the actual built app; no installed/host acceptance. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import type { Page } from "@playwright/test";
import {
    problemWire,
    readWire,
    statusPayload,
    versionPayload,
} from "../read-fixtures.ts";
import config from "../../../tests/fixtures/web_wire/config.json" with { type: "json" };
import { libraryFixtureResponse } from "./library-fixture.ts";
import type { LibraryFixtureEvidence } from "./library-fixture.ts";

declare global {
    interface Window {
        recordOwnedCspViolation?: (value: string) => Promise<void>;
    }
}

export const SOURCE_FIXTURE_ORIGIN = "https://owned-source-fixture.invalid";
export const SOURCE_FIXTURE_CSP =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'none'";

function object(value: unknown): Record<string, unknown> {
    if (typeof value !== "object" || value === null || Array.isArray(value))
        throw new Error("Owned fixture expected an object.");
    return Object.fromEntries(Object.entries(value));
}
function text(value: unknown): string {
    if (typeof value !== "string")
        throw new Error("Owned fixture expected text.");
    return value;
}

export async function sourceFixture(
    page: Page,
    options: { library?: boolean; facetDelayMs?: number } = {},
) {
    if ((options.facetDelayMs ?? 0) < 0 || (options.facetDelayMs ?? 0) > 250)
        throw new Error("Owned facet delay must remain between0 and250ms.");
    const root = fileURLToPath(new URL("../../", import.meta.url));
    const manifestBytes = readFileSync(join(root, "dist/manifest.json"));
    const manifest = object(JSON.parse(manifestBytes.toString("utf8")));
    const build = object(manifest.build);
    if (!Array.isArray(manifest.members))
        throw new Error("Owned built asset members are unavailable.");
    const members: unknown[] = manifest.members;
    const fingerprint = createHash("sha256")
        .update(manifestBytes)
        .digest("hex");
    const files = new Map(
        members.map((value) => {
            const member = object(value),
                path = text(member.path);
            if (!/^(?:assets\/)?[A-Za-z0-9][A-Za-z0-9._-]*$/u.test(path))
                throw new Error("Owned built asset path is invalid.");
            return [
                "/ui/" + path,
                {
                    body: readFileSync(join(root, "dist", path)),
                    mime: text(member.mime),
                },
            ];
        }),
    );
    const index = readFileSync(join(root, "dist/index.html"), "utf8")
        .replaceAll("__HFCACHE_UI_BASE_V1__", "/ui/")
        .replaceAll("__HFCACHE_UI_BOOTSTRAP_V1__", "/ui/bootstrap.json")
        .replaceAll("__HFCACHE_UI_FINGERPRINT_V1__", fingerprint)
        .replaceAll("__HFCACHE_UI_CONTRACT_V1__", "1");
    const bootstrap = {
        schema_version: 1,
        kind: "hfcache_ui_bootstrap",
        ui_contract_version: 1,
        rest_api_schema_version: 1,
        wire_source_digest: text(build.wire_source_digest),
        instance_id: "1".repeat(32),
        authority_epoch: "1".repeat(32),
        configured_origin: SOURCE_FIXTURE_ORIGIN,
        configured_archive_id: config.read.archive_id,
        archive_identity_source: "installed_policy",
        config_fingerprint: null,
        paths: {
            public_prefix: "",
            effective_prefix: "",
            ui_base: "/ui/",
            bootstrap: "/ui/bootstrap.json",
            api_base: "/api/v1",
            mcp_base: "/mcp/",
        },
        build: { asset_manifest_sha256: fingerprint, metadata: build },
        user: {
            subject: "administrator",
            display_name: "administrator",
            authentication_method: "basic",
            credential_class: "rest-writer",
            rest_capabilities: ["read", "write"],
            admin_permissions: [
                "config-read",
                "config-write",
                "host-read",
                "observer-stop",
                "schedule-write",
            ].map((capability) => {
                const allowed = ["config-read", "config-write"].includes(
                    capability,
                );
                return {
                    capability,
                    granted: allowed,
                    effective: allowed,
                    reason: allowed ? "allowed" : "not_granted",
                };
            }),
        },
    };
    const requests: { method: string; path: string }[] = [];
    const unexpected: string[] = [];
    const cspViolations: string[] = [];
    const pageErrors: string[] = [];
    const pendingReads = new Set<() => void>();
    let libraryEvidence: LibraryFixtureEvidence = {};
    let apiActive = 0,
        apiPeak = 0;
    const apiTimings: { path: string; durationMs: number }[] = [];
    let configGets = 0;
    let nextRead: {
        outcome: "api" | "success";
        promise: Promise<void>;
    } | null = null;
    await page.exposeFunction("recordOwnedCspViolation", (value: string) => {
        cspViolations.push(value);
    });
    await page.addInitScript(() => {
        document.addEventListener("securitypolicyviolation", (event) => {
            void window.recordOwnedCspViolation?.(
                event.violatedDirective + ":" + event.blockedURI,
            );
        });
    });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.route("**/*", async (route) => {
        const request = route.request(),
            url = new URL(request.url()),
            path = url.pathname;
        requests.push({ method: request.method(), path: path + url.search });
        const apiRequest =
            url.origin === SOURCE_FIXTURE_ORIGIN && path.startsWith("/api/v1/");
        const started = performance.now();
        if (apiRequest) {
            apiActive++;
            apiPeak = Math.max(apiPeak, apiActive);
        }
        try {
            if (url.origin !== SOURCE_FIXTURE_ORIGIN) {
                unexpected.push(request.method() + " " + request.url());
                await route.abort("blockedbyclient");
                return;
            }
            const json = async (value: unknown, status = 200) => {
                await route.fulfill({
                    status,
                    contentType: "application/json",
                    body: JSON.stringify(value),
                    headers: { "Cache-Control": "no-store" },
                });
            };
            if (request.method() === "GET") {
                const library =
                    options.library === true
                        ? libraryFixtureResponse(url, libraryEvidence)
                        : null;
                if (library !== null) {
                    if (
                        path === "/api/v1/catalog/facets" &&
                        options.facetDelayMs !== undefined
                    )
                        await new Promise<void>((resolve) =>
                            setTimeout(resolve, options.facetDelayMs),
                        );
                    await json(library);
                    return;
                }
                if (path === "/ui/bootstrap.json") {
                    await json(bootstrap);
                    return;
                }
                if (path === "/api/v1/config") {
                    configGets++;
                    const pending = nextRead;
                    nextRead = null;
                    if (pending !== null) await pending.promise;
                    if (pending?.outcome === "api")
                        await json(problemWire("HFAPI005", 20), 503);
                    else
                        await json({
                            ...readWire("config read", config.read),
                            archive_id: config.read.archive_id,
                        });
                    return;
                }
                if (path === "/api/v1/status") {
                    await json(readWire("status", statusPayload(true)));
                    return;
                }
                if (path === "/api/v1/health") {
                    await json(
                        readWire("health", {
                            ready: true,
                            policy_valid: null,
                            archive: null,
                        }),
                    );
                    return;
                }
                if (path === "/api/v1/version") {
                    await json(
                        readWire("version", {
                            ...versionPayload,
                            application: text(build.application_version),
                        }),
                    );
                    return;
                }
                if (
                    ["/ui/", "/ui/administration", "/ui/library"].includes(path)
                ) {
                    await route.fulfill({
                        contentType: "text/html",
                        body: index,
                        headers: {
                            "Content-Security-Policy": SOURCE_FIXTURE_CSP,
                            "X-Content-Type-Options": "nosniff",
                            "Cache-Control": "no-store",
                        },
                    });
                    return;
                }
                const file = files.get(path);
                if (file !== undefined) {
                    await route.fulfill({
                        contentType: file.mime,
                        body: file.body,
                    });
                    return;
                }
            }
            unexpected.push(request.method() + " " + request.url());
            await route.fulfill({
                status: 405,
                body: "Owned fixture refuses.",
            });
        } finally {
            if (apiRequest) {
                apiActive--;
                apiTimings.push({
                    path: path + url.search,
                    durationMs: performance.now() - started,
                });
            }
        }
    });
    return {
        requests,
        unexpected,
        cspViolations,
        pageErrors,
        apiPeak: () => apiPeak,
        apiTimings,
        setLibraryEvidence(evidence: LibraryFixtureEvidence) {
            libraryEvidence = { ...libraryEvidence, ...evidence };
        },
        manifest: {
            sha256: fingerprint,
            build,
        },
        configGets: () => configGets,
        releasePendingReads() {
            for (const release of pendingReads) release();
        },
        deferRead(outcome: "api" | "success") {
            if (nextRead !== null)
                throw new Error("Only one owned configuration read may wait.");
            let release: () => void = () => {
                throw new Error("Deferred fixture read was not initialized.");
            };
            const promise = new Promise<void>((resolve) => {
                release = () => {
                    pendingReads.delete(release);
                    resolve();
                };
            });
            pendingReads.add(release);
            nextRead = { outcome, promise };
            return release;
        },
    };
}
