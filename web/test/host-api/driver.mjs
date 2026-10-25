/** WEB006 real installed host boundary; native Basic stays out of page JS. */
import assert from "node:assert/strict";
import { createHash, randomUUID } from "node:crypto";
import { lstat, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { pathToFileURL } from "node:url";
import {
    assertApplicationIdentity,
    assertNativeNetworkObservation,
    chromiumProof,
    descendantsClosed,
    nativeNetworkObserver,
    ownedCleanupInventory,
    processProof,
    requireUnprivileged,
} from "../auth-api/sandbox.mjs";
import {
    assertUiHeaders,
    envelope,
    fixedEndpoint,
    nodeRequest,
    secretDiagnostic,
} from "../functional-api/driver.mjs";

const VERSIONS = {
    chromium: "156.0.8078.4",
    firefox: "157.0",
    webkit: "27.2",
};
const MODES = new Set(["baseline", "helper-down", "restarted", "timeout"]);
const ACTIONS = [
    "archive",
    "hub",
    "control",
    "schedule",
    "configuration",
    "observer",
];
let interrupted = false;
let activeServer;

async function deadline(operation, milliseconds) {
    let timer;
    try {
        return await Promise.race([
            operation,
            new Promise((_resolve, reject) => {
                timer = setTimeout(
                    () => reject(new Error("owned-host-browser-deadline")),
                    milliseconds,
                );
            }),
        ]);
    } finally {
        clearTimeout(timer);
    }
}

async function jsonFile(filename) {
    const facts = await lstat(filename);
    assert.ok(
        facts.isFile() &&
            !facts.isSymbolicLink() &&
            facts.nlink === 1 &&
            facts.size <= 2097152,
    );
    return JSON.parse(await readFile(filename, "utf8"));
}

async function credentialsFromPipe() {
    let size = 0;
    const chunks = [];
    for await (const chunk of process.stdin) {
        size += chunk.length;
        assert.ok(size <= 8192);
        chunks.push(chunk);
    }
    const value = JSON.parse(Buffer.concat(chunks));
    assert.deepEqual(Object.keys(value).sort(), [
        "password",
        "schema_version",
        "tokens",
        "username",
    ]);
    assert.equal(value.schema_version, 1);
    assertApplicationIdentity(value.username);
    assert.equal(typeof value.password, "string");
    assert.ok(
        Buffer.byteLength(value.password) > 0 &&
            Buffer.byteLength(value.password) <= 1024,
    );
    assert.deepEqual(Object.keys(value.tokens).sort(), [
        "hub",
        "mcp_reader",
        "reader",
        "writer",
    ]);
    for (const token of Object.values(value.tokens))
        assert.ok(
            typeof token === "string" &&
                token.length >= 32 &&
                token.length <= 128,
        );
    return value;
}

export function assertHostStatus(status, runtime, manifest, mode) {
    assert.deepEqual(Object.keys(status).sort(), [
        "binding",
        "facts",
        "permission_reasons",
        "permissions",
        "profile",
        "reason",
        "schema_version",
        "state",
    ]);
    assert.equal(status.schema_version, 1);
    assert.deepEqual(
        Object.keys(status.permissions).sort(),
        [...ACTIONS].sort(),
    );
    assert.deepEqual(
        Object.keys(status.permission_reasons).sort(),
        [...ACTIONS].sort(),
    );
    if (mode === "baseline" || mode === "restarted") {
        assert.equal(status.state, "supported");
        assert.equal(status.reason, null);
        assert.equal(status.profile, runtime.profile);
        assert.equal(
            status.binding.deployment_sha256,
            manifest.profiles[runtime.profile].deployment.sha256,
        );
        assert.equal(
            status.binding.policy_sha256,
            manifest.profiles[runtime.profile].policy.sha256,
        );
        assert.equal(status.binding.archive_root, "/srv/hfcache");
        assert.ok(["absent", "inactive"].includes(status.facts.guard));
        for (const action of ACTIONS) {
            assert.equal(
                status.permissions[action],
                action === "configuration",
            );
            const reason =
                action === "configuration"
                    ? "granted"
                    : runtime.profile === "rootless" &&
                        ["schedule", "observer"].includes(action)
                      ? "profile-unproved"
                      : "policy-denied";
            assert.equal(status.permission_reasons[action], reason);
        }
    } else {
        assert.equal(status.state, "unavailable");
        assert.equal(status.profile, null);
        assert.equal(status.binding, null);
        assert.equal(status.facts, null);
        if (mode === "timeout") assert.equal(status.reason, "helper-timeout");
        else
            assert.ok(
                ["helper-unavailable", "helper-refused"].includes(
                    status.reason,
                ),
            );
        for (const action of ACTIONS) {
            assert.equal(status.permissions[action], false);
            assert.equal(
                status.permission_reasons[action],
                "helper-unavailable",
            );
        }
    }
    return status;
}

/** Keep bounded public classification even when the acceptance assertion fails. */
export function assertObservedHostStatus(
    evidence,
    status,
    runtime,
    manifest,
    mode,
) {
    const reasons = new Set([
        "helper-disabled",
        "helper-unavailable",
        "helper-timeout",
        "helper-refused",
        "helper-busy",
        "policy-missing",
        "policy-invalid",
        "deployment-unverified",
        "facts-unavailable",
        "guard-unconfirmed",
        "key-missing",
        "key-invalid",
        "config-unavailable",
    ]);
    assert.ok(
        status !== null && typeof status === "object" && !Array.isArray(status),
    );
    assert.ok(
        ["supported", "guarded", "unknown", "unavailable"].includes(
            status.state,
        ),
    );
    assert.ok(status.reason === null || reasons.has(status.reason));
    assert.ok([null, "native", "rootless"].includes(status.profile));
    evidence.host_status_observation = {
        state: status.state,
        reason: status.reason,
        profile: status.profile,
    };
    const confirmed = assertHostStatus(status, runtime, manifest, mode);
    evidence.host_status = confirmed;
    return confirmed;
}

export function assertProblem(value, status, code) {
    assert.equal(status, code === "HFAPI022" ? 503 : 403);
    assert.deepEqual(Object.keys(value).sort(), [
        "code",
        "exit_code",
        "message",
        "request_id",
    ]);
    assert.match(value.request_id, /^[a-f0-9]{32}$/u);
    assert.equal(value.code, code);
    assert.equal(typeof value.message, "string");
    // INV-006 / CLI §5.1: authorization retains the configuration exit family.
    assert.equal(value.exit_code, code === "HFAPI022" ? 20 : 10);
    return { request_id: value.request_id, status, error_code: code };
}

/** Read one real response in its page context, without a protocol body lookup. */
export async function readBrowserJSON(page, url) {
    return await page.evaluate(async (endpoint) => {
        const response = await fetch(endpoint, { credentials: "same-origin" });
        return {
            status: response.status,
            request_id: response.headers.get("x-request-id"),
            body: await response.json(),
        };
    }, url);
}

async function basicPost(page, runtime, suffix, extraHeaders = {}) {
    // Credentials remain in the native browser Basic cache; none enter JS.
    return await page.evaluate(
        async ({ url, key, extra }) => {
            const response = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-Hfcache-Request": "1",
                    "Idempotency-Key": key,
                    ...extra,
                },
                body: "{}",
            });
            return { status: response.status, body: await response.json() };
        },
        {
            url: fixedEndpoint(runtime.origin, runtime.prefix, suffix).href,
            key: "web006-" + randomUUID(),
            extra: extraHeaders,
        },
    );
}

async function checkEngine(name, type, manifest, runtime, credentials, mode) {
    const evidence = {
        version: null,
        cases: [],
        owned_descendants: [],
        forced_close: false,
    };
    const retained = new Map();
    const observer = nativeNetworkObserver({ trusted: runtime.origin });
    evidence.network_observation = observer.state;
    let server;
    let browser;
    let context;
    const test = async (id, operation) => {
        const row = { id, attempts: 1, passed: false };
        evidence.cases.push(row);
        try {
            const result = await deadline(
                operation(),
                mode === "timeout" ? 30000 : 25000,
            );
            if (result !== undefined) row.result = result;
            row.passed = true;
        } catch (error) {
            row.diagnostic = secretDiagnostic(error, credentials);
        }
    };
    try {
        server = await type.launchServer({
            headless: true,
            ...(name === "chromium"
                ? { chromiumSandbox: true, channel: "chromium" }
                : {}),
            host: "127.0.0.1",
            port: 0,
            timeout: 15000,
        });
        activeServer = server;
        evidence.process = await processProof(server.process().pid);
        requireUnprivileged(evidence.process);
        browser = await type.connect(server.wsEndpoint());
        evidence.version = browser.version();
        assert.equal(evidence.version, VERSIONS[name]);
        if (name === "chromium") {
            evidence.sandbox = { verified: false };
            await chromiumProof(browser, evidence.process, evidence.sandbox);
            for (const proof of evidence.sandbox.observed_descendants ?? [])
                retained.set(`${proof.pid}:${proof.start_ticks}`, proof);
        }
        context = await browser.newContext({
            httpCredentials: {
                username: credentials.username,
                password: credentials.password,
            },
            ignoreHTTPSErrors: false,
            serviceWorkers: "block",
            viewport: { width: 1440, height: 1000 },
            userAgent: `hfcache-web-host/${name}`,
        });
        context.on("request", (request) => observer.observe(request.url()));
        const page = await context.newPage();
        page.setDefaultTimeout(30000);
        page.setDefaultNavigationTimeout(15000);
        const hostUrl = fixedEndpoint(
            runtime.origin,
            runtime.prefix,
            "/api/v1/host/status",
        ).href;
        const started = performance.now();
        const navigation = await page.goto(
            fixedEndpoint(runtime.origin, runtime.prefix, "/ui/administration")
                .href,
        );
        assert.equal(navigation.status(), 200);
        assertUiHeaders(navigation.headers());
        const observed = await readBrowserJSON(page, hostUrl);
        assert.equal(observed.status, 200);
        const status = envelope(observed.body);
        assertObservedHostStatus(evidence, status, runtime, manifest, mode);
        const elapsed = (performance.now() - started) / 1000;
        const capabilities = await page.evaluate(
            async (url) => {
                const reply = await fetch(url, { credentials: "same-origin" });
                return { status: reply.status, body: await reply.json() };
            },
            fixedEndpoint(
                runtime.origin,
                runtime.prefix,
                "/api/v1/capabilities",
            ).href,
        );
        assert.equal(capabilities.status, 200);
        assert.equal(
            envelope(capabilities.body).instance_id,
            runtime.instance_id,
        );
        await page
            .getByRole("heading", { name: "Host administration", exact: true })
            .waitFor();
        await page
            .getByTestId("host-state")
            .filter({ hasText: `Host state: ${status.state}.` })
            .waitFor();
        if (mode === "baseline") {
            await test("host-status-observed", async () => ({
                state: status.state,
                guard: status.facts.guard,
                request_id: observed.request_id,
            }));
            await test("host-denial-ui-reasons", async () => {
                for (const action of ["archive", "hub", "control"])
                    await page
                        .getByTestId(`host-permission-${action}`)
                        .filter({
                            hasText: "The installed policy denies this action.",
                        })
                        .waitFor();
                await page
                    .getByTestId("host-permission-configuration")
                    .filter({ hasText: "Granted by the installed policy." })
                    .waitFor();
                if (runtime.profile === "rootless")
                    for (const action of ["schedule", "observer"])
                        await page
                            .getByTestId(`host-permission-${action}`)
                            .filter({
                                hasText:
                                    "This deployment profile has not established this authority.",
                            })
                            .waitFor();
            });
            for (const [id, route] of [
                ["basic-hub-denied", "/api/v1/plans"],
                ["basic-archive-denied", "/api/v1/syncs"],
                ["basic-control-denied", "/api/v1/prune-plans"],
            ])
                await test(id, async () => {
                    const denied = await basicPost(page, runtime, route);
                    return assertProblem(
                        denied.body,
                        denied.status,
                        "HFAPI002",
                    );
                });
            await test("forged-admin-header-denied", async () => {
                const denied = await basicPost(page, runtime, "/api/v1/plans", {
                    "X-Hfcache-Admin": "true",
                    "X-Hfcache-Host-Permissions": "all",
                });
                return assertProblem(denied.body, denied.status, "HFAPI002");
            });
            await test("old-writer-no-host-admin", async () => {
                const denied = await nodeRequest(new URL(hostUrl), {
                    ca: await readFile(manifest.browser.ca.path),
                    token: credentials.tokens.writer,
                });
                return assertProblem(
                    JSON.parse(denied.body),
                    denied.status,
                    "HFAPI002",
                );
            });
        } else if (mode === "helper-down") {
            await test("host-unavailable-visible", async () => {
                await page
                    .getByRole("status")
                    .filter({
                        hasText:
                            status.reason === "helper-refused"
                                ? "The protected host helper could not be authenticated."
                                : "The protected host helper is unavailable.",
                    })
                    .waitFor();
            });
            await test("basic-unavailable-denied", async () => {
                const denied = await basicPost(page, runtime, "/api/v1/plans");
                return assertProblem(denied.body, denied.status, "HFAPI022");
            });
        } else if (mode === "restarted") {
            await test("host-restart-same-parent", async () => {
                assert.equal(status.state, "supported");
                await page
                    .getByRole("button", { name: "Refresh host status" })
                    .waitFor();
            });
        } else {
            evidence.timeout_elapsed_seconds = elapsed;
            await test("actual-timeout-visible", async () => {
                assert.ok(elapsed >= 21 && elapsed < 28);
                await page
                    .getByRole("status")
                    .filter({
                        hasText:
                            "The protected host helper did not complete within its time limit.",
                    })
                    .waitFor();
            });
        }
    } catch (error) {
        evidence.infrastructure_failed = true;
        evidence.diagnostic = secretDiagnostic(error, credentials);
    } finally {
        if (server)
            try {
                for (const proof of await ownedCleanupInventory(
                    server.process(),
                    evidence.process,
                ))
                    retained.set(`${proof.pid}:${proof.start_ticks}`, proof);
            } catch (error) {
                evidence.descendant_inventory_unknown = true;
                evidence.descendant_diagnostic = secretDiagnostic(
                    error,
                    credentials,
                );
            }
        evidence.owned_descendants = [...retained.values()];
        await deadline(context?.close() ?? Promise.resolve(), 5000).catch(
            () => {},
        );
        await deadline(browser?.close() ?? Promise.resolve(), 5000).catch(
            () => {},
        );
        if (server) {
            const child = server.process();
            try {
                await deadline(server.close(), 5000);
                if (child.exitCode === null && child.signalCode === null)
                    await deadline(
                        new Promise((resolve) => child.once("close", resolve)),
                        5000,
                    );
            } catch {
                // Preserve actual ownership uncertainty; never turn force into success.
                evidence.browser_drain_unknown = true;
            }
            evidence.browser_closed =
                child.exitCode !== null || child.signalCode !== null;
            evidence.browser_exit = {
                code: child.exitCode,
                signal: child.signalCode,
            };
            evidence.descendants_closed = await descendantsClosed(
                evidence.owned_descendants,
            );
            activeServer = undefined;
        }
        try {
            assertNativeNetworkObservation(observer.state);
        } catch (error) {
            evidence.infrastructure_failed = true;
            evidence.network_diagnostic = secretDiagnostic(error, credentials);
        }
    }
    return evidence;
}

export async function main(argv = process.argv.slice(2)) {
    if (argv.length === 1 && argv[0] === "--help") {
        console.log(
            "Run WEB006 browser checks only through the protected owned fixture launcher.",
        );
        return;
    }
    assert.equal(argv.length, 6);
    assert.equal(argv[0], "--manifest");
    assert.equal(argv[2], "--workspace");
    assert.equal(argv[4], "--mode");
    const mode = argv[5];
    assert.ok(MODES.has(mode));
    const manifest = await jsonFile(argv[1]);
    assert.equal(manifest.kind, "hfcache_web_host_fixture");
    const workspace = argv[3];
    const runtime = await jsonFile(path.join(workspace, "runtime.json"));
    assert.equal(runtime.fixture_id, manifest.fixture_id);
    assert.ok(["native", "rootless"].includes(runtime.profile));
    assert.equal(runtime.origin, manifest.profiles[runtime.profile].origin);
    assert.equal(runtime.prefix, manifest.profiles[runtime.profile].prefix);
    assert.equal(
        runtime.asset_manifest_sha256,
        manifest.assets.manifest_sha256,
    );
    assert.equal(process.version, "v24.18.1");
    for (const variable of [
        "MOZ_DISABLE_CONTENT_SANDBOX",
        "MOZ_DISABLE_RDD_SANDBOX",
        "MOZ_DISABLE_GMP_SANDBOX",
        "WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS",
        "NODE_TLS_REJECT_UNAUTHORIZED",
    ])
        assert.equal(process.env[variable], undefined);
    const modulePath = manifest.browser.playwright_module.path;
    assert.equal(
        createHash("sha256")
            .update(await readFile(modulePath))
            .digest("hex"),
        manifest.browser.playwright_module.sha256,
    );
    const playwright = await import(pathToFileURL(modulePath).href);
    const credentials = await deadline(credentialsFromPipe(), 5000);
    process.once("SIGTERM", () => {
        interrupted = true;
        void activeServer?.close().catch(() => {});
    });
    const report = {
        schema_version: 1,
        fixture_id: runtime.fixture_id,
        generation_id: runtime.generation_id,
        profile: runtime.profile,
        prefix: runtime.prefix,
        mode,
        asset_manifest_sha256: runtime.asset_manifest_sha256,
        instance_id: runtime.instance_id,
        engines: {},
    };
    for (const name of ["chromium", "firefox", "webkit"]) {
        assert.equal(interrupted, false);
        report.engines[name] = await checkEngine(
            name,
            playwright[name],
            manifest,
            runtime,
            credentials,
            mode,
        );
    }
    await writeFile(
        path.join(workspace, `browser-${mode}-report.json`),
        JSON.stringify(report, null, 2) + "\n",
        { flag: "wx", mode: 0o600 },
    );
    if (
        interrupted ||
        Object.values(report.engines).some(
            (engine) =>
                engine.infrastructure_failed ||
                engine.descendant_inventory_unknown ||
                engine.browser_drain_unknown ||
                !engine.browser_closed ||
                !engine.descendants_closed ||
                engine.browser_exit.code !== 0 ||
                engine.browser_exit.signal !== null ||
                engine.cases.some((row) => !row.passed),
        )
    )
        process.exitCode = 1;
}

if (
    process.argv[1] &&
    pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url
)
    main().catch(() => {
        console.error(
            "Owned WEB006 browser prerequisite or evidence refused; preserve its workspace.",
        );
        process.exitCode = 1;
    });
