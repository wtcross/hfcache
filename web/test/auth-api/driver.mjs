/** Native browser credentials cross only the three provisioned guest origins. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile, lstat } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import {
    chromiumProof,
    assertVersionPayload,
    assertApplicationIdentity,
    descendantsClosed,
    ownedCleanupInventory,
    processProof,
    requireUnprivileged,
    safeDiagnostic,
    nativeNetworkObserver,
    assertNativeNetworkObservation,
} from "./sandbox.mjs";

const ENGINE_NAMES = ["chromium", "firefox", "webkit"];
const CASE_COUNT = 8;
const BROWSER_VERSIONS = {
    chromium: "156.0.8078.4",
    firefox: "157.0",
    webkit: "27.2",
};
let activeServer;
let interrupted = false;
let interruptCase;
const interruptedCase = new Promise((_, reject) => {
    interruptCase = reject;
});
// Attach a rejection observer even while no test is running.
interruptedCase.catch(() => {});
const deadline = (promise, milliseconds, label) => {
    let timer;
    return Promise.race([
        promise,
        new Promise((_, reject) => {
            timer = setTimeout(() => {
                reject(new Error(label));
            }, milliseconds);
        }),
    ]).finally(() => {
        clearTimeout(timer);
    });
};

function argumentsFrom(argv) {
    assert.equal(argv.length, 4);
    assert.equal(argv[0], "--manifest");
    assert.equal(argv[2], "--workspace");
    for (const item of [argv[1], argv[3]]) {
        assert.ok(path.isAbsolute(item));
        assert.ok(
            !item.split("/").some((part) => part === "." || part === ".."),
        );
    }
    return { manifest: argv[1], workspace: argv[3] };
}

async function credentialsFromPipe() {
    assert.equal(process.stdin.isTTY, undefined);
    const chunks = [];
    let length = 0;
    for await (const chunk of process.stdin) {
        length += chunk.byteLength;
        assert.ok(length <= 4096);
        chunks.push(chunk);
    }
    const value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    assert.deepEqual(Object.keys(value).sort(), ["password", "username"]);
    assert.equal(typeof value.username, "string");
    assert.equal(typeof value.password, "string");
    assert.ok(Buffer.byteLength(value.username) <= 128);
    assert.ok(Buffer.byteLength(value.password) <= 1024);
    return value;
}

async function closedProcess(child, action) {
    const exit = new Promise((resolve) => {
        if (child.exitCode !== null || child.signalCode !== null) resolve();
        else child.once("close", resolve);
    });
    await deadline(action(), 15_000, "owned-browser-stop");
    await deadline(exit, 15_000, "owned-browser-close");
    assert.ok(child.exitCode !== null || child.signalCode !== null);
}

async function checkEngine(name, type, bindings, credentials, report) {
    const evidence = {
        stage: "launch",
        passed: 0,
        failed: 0,
        skipped: 0,
        cases: [],
        browser_closed: false,
    };
    report.engines[name] = evidence;
    let server;
    let browser;
    let context;
    const { trusted, foreign, untrusted } = bindings.manifest.origins;
    const route = bindings.prefix + "/api/v1/";
    let networkObserver;
    try {
        server = await type.launchServer({
            host: "127.0.0.1",
            port: 0,
            headless: true,
            ...(name === "chromium"
                ? { chromiumSandbox: true, channel: "chromium" }
                : {}),
        });
        activeServer = server;
        const child = server.process();
        assert.ok(child && Number.isSafeInteger(child.pid));
        evidence.browser_pid = child.pid;
        evidence.stage = "process-proof";
        evidence.process = await processProof(child.pid);
        requireUnprivileged(evidence.process);
        browser = await type.connect(server.wsEndpoint());
        evidence.stage = "version-proof";
        evidence.browser_version = browser.version();
        assert.equal(evidence.browser_version, BROWSER_VERSIONS[name]);
        if (name === "chromium") {
            evidence.stage = "sandbox-proof";
            evidence.sandbox = { verified: false };
            await chromiumProof(browser, evidence.process, evidence.sandbox);
        }
        evidence.stage = "native-credentials-context";
        context = await browser.newContext({
            // Playwright delegates this pair to each engine's native HTTP challenge
            // provider. No Authorization header or page JavaScript receives it.
            // This context permits credentials on TWO explicitly owned origins so
            // a real foreign document can load. The guest has no external route;
            // the passive observer below refuses unexpected fixture origins.
            httpCredentials: credentials,
            // A fixture User-Agent labels observations without changing a simple
            // request into a CORS preflight or supplying a credential header.
            userAgent: "hfcache-owned-native-auth/" + name,
            ignoreHTTPSErrors: false,
            serviceWorkers: "block",
        });
        evidence.stage = "native-request-observation";
        networkObserver = nativeNetworkObserver(bindings.manifest.origins);
        evidence.network_observation = networkObserver.state;
        // Do not use request routing: pinned Playwright's Chromium interceptor
        // synthesizes successful preflight responses before they reach the API.
        // crNetworkManager.ts284-305 in the official v1.64.1 source.
        context.on("request", (request) => {
            networkObserver.observe(request.url());
        });
        context.setDefaultTimeout(10_000);
        context.setDefaultNavigationTimeout(15_000);
        evidence.stage = "native-first-page";
        const page = await context.newPage();
        evidence.stage = "native-foreign-page";
        const foreignPage = await context.newPage();

        async function test(caseId, action) {
            evidence.stage = caseId;
            try {
                await deadline(
                    Promise.race([action(), interruptedCase]),
                    25_000,
                    "owned-case-deadline",
                );
                evidence.cases.push({ case_id: caseId, status: "passed" });
                evidence.passed += 1;
            } catch (error) {
                evidence.cases.push({
                    case_id: caseId,
                    status: "failed",
                    diagnostic: safeDiagnostic(error, credentials),
                });
                evidence.failed += 1;
                // A JSON response cannot contain credential values; no trace, HAR,
                // request/response headers or raw exception text is persisted.
                await page
                    .screenshot({
                        path: path.join(
                            bindings.workspace,
                            `${name}-${caseId}.png`,
                        ),
                    })
                    .catch(() => {});
                if (interrupted)
                    throw new Error("interrupted", { cause: error });
            }
        }

        await test("native-challenge-version", async () => {
            const response = await page.goto(trusted + route + "version");
            assert.equal(response.status(), 200);
            assert.equal(new URL(page.url()).origin, trusted);
            assertVersionPayload(
                await response.json(),
                bindings.expectedApplication,
            );
        });
        await test("same-origin-capabilities", async () => {
            assert.equal(new URL(page.url()).origin, trusted);
            const result = await page.evaluate(async (endpoint) => {
                const response = await fetch(endpoint, {
                    credentials: "same-origin",
                });
                return {
                    status: response.status,
                    payload: await response.json(),
                };
            }, route + "capabilities");
            assert.equal(result.status, 200);
            assert.equal(
                result.payload.envelope.data.credential_class,
                "rest-writer",
            );
            assert.deepEqual(result.payload.envelope.data.capabilities, [
                "read",
                "write",
            ]);
        });
        await test("same-origin-json-post", async () => {
            const result = await page.evaluate(async (endpoint) => {
                const response = await fetch(endpoint, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Hfcache-Request": "1",
                    },
                    body: "{}",
                });
                return {
                    status: response.status,
                    payload: await response.json(),
                };
            }, route + "config/validate");
            assert.equal(result.status, 200);
            assert.equal(result.payload.envelope.exit_code, 0);
        });
        // This is an actual second installed API, not a synthetic HTML origin.
        const foreignResponse = await foreignPage.goto(
            foreign + route + "version",
        );
        assert.equal(foreignResponse.status(), 200);
        assert.equal(new URL(foreignPage.url()).origin, foreign);
        evidence.credential_origin_exception = [trusted, foreign];
        const target = trusted + route + "config/validate";

        await test("foreign-text", async () => {
            const observed = foreignPage.waitForResponse(
                (response) =>
                    response.url() === target &&
                    response.request().method() === "POST",
            );
            await foreignPage.evaluate(async (endpoint) => {
                await fetch(endpoint, {
                    method: "POST",
                    mode: "no-cors",
                    credentials: "include",
                    headers: { "Content-Type": "text/plain" },
                    body: "{}",
                }).catch(() => {});
            }, target);
            assert.equal((await observed).status(), 403);
        });
        await test("foreign-multipart", async () => {
            const observed = foreignPage.waitForResponse(
                (response) =>
                    response.url() === target &&
                    response.request().method() === "POST",
            );
            await foreignPage.evaluate(async (endpoint) => {
                const body = new FormData();
                body.set("candidate", "owned");
                await fetch(endpoint, {
                    method: "POST",
                    mode: "no-cors",
                    credentials: "include",
                    body,
                }).catch(() => {});
            }, target);
            assert.equal((await observed).status(), 403);
        });
        await test("foreign-form", async () => {
            const observed = foreignPage.waitForResponse(
                (response) =>
                    response.url() === target &&
                    response.request().method() === "POST",
            );
            await foreignPage.evaluate((endpoint) => {
                const frame = document.createElement("iframe");
                frame.name = "owned-csrf-frame";
                document.body.append(frame);
                const form = document.createElement("form");
                form.action = endpoint;
                form.method = "POST";
                form.target = frame.name;
                const field = document.createElement("input");
                field.name = "candidate";
                field.value = "owned";
                form.append(field);
                document.body.append(form);
                form.submit();
            }, target);
            assert.equal((await observed).status(), 403);
        });
        await test("foreign-preflight", async () => {
            const result = await foreignPage.evaluate(async (endpoint) => {
                try {
                    await fetch(endpoint, {
                        method: "POST",
                        credentials: "include",
                        headers: {
                            "Content-Type": "application/json",
                            "X-Hfcache-Request": "1",
                        },
                        body: "{}",
                    });
                    return { outcome: "unexpectedly-readable" };
                } catch (error) {
                    return {
                        outcome: "refused",
                        name: error.name,
                        message: error.message,
                    };
                }
            }, target);
            evidence.preflight_fetch_diagnostic = safeDiagnostic(
                result,
                credentials,
            );
            assert.equal(result.outcome, "refused");
            // Browser tooling does not expose every engine's internal preflight.
            // The independent API observer requires this engine's real OPTIONS
            // refusal before the parent can accept this case.
        });
        await test("untrusted-ca-refused", async () => {
            const untrustedPage = await context.newPage();
            try {
                let refused = false;
                try {
                    await untrustedPage.goto(untrusted + route + "version");
                } catch (error) {
                    refused = true;
                    evidence.untrusted_navigation_diagnostic = safeDiagnostic(
                        error,
                        credentials,
                    );
                    evidence.untrusted_certificate_rejected =
                        /ERR_CERT_AUTHORITY_INVALID|SEC_ERROR_UNKNOWN_ISSUER|SEC_ERROR_UNTRUSTED_ISSUER|Unacceptable TLS certificate|certificate.*(?:untrusted|unknown issuer)/i.test(
                            error.message,
                        );
                }
                assert.ok(refused);
                assert.equal(evidence.untrusted_certificate_rejected, true);
                assert.notEqual(new URL(untrustedPage.url()).origin, untrusted);
            } finally {
                await untrustedPage.close();
            }
        });
        assert.equal(evidence.cases.length, CASE_COUNT);
        assertNativeNetworkObservation(networkObserver.state);
        evidence.stage = "cases-complete";
    } catch (error) {
        evidence.infrastructure_failed = true;
        evidence.diagnostic = safeDiagnostic(error, credentials);
        evidence.browser_connected_at_failure = browser?.isConnected() ?? false;
    } finally {
        const retained = new Map(
            (evidence.sandbox?.observed_descendants ?? []).map((proof) => [
                `${proof.pid}:${proof.start_ticks}`,
                proof,
            ]),
        );
        if (server) {
            try {
                for (const proof of await ownedCleanupInventory(
                    server.process(),
                    evidence.process,
                )) {
                    const key = `${proof.pid}:${proof.start_ticks}`;
                    // A cleanup-only snapshot never replaces an earlier strict
                    // sandbox/renderer/zombie observation of this exact identity.
                    if (!retained.has(key)) retained.set(key, proof);
                }
            } catch (error) {
                evidence.descendant_inventory_unknown = true;
                evidence.descendant_diagnostic = safeDiagnostic(
                    error,
                    credentials,
                );
            }
        }
        const descendants = [...retained.values()];
        evidence.owned_descendants = descendants;
        await deadline(
            context?.close() ?? Promise.resolve(),
            5000,
            "owned-context-close",
        ).catch(() => {});
        await deadline(
            browser?.close() ?? Promise.resolve(),
            5000,
            "owned-connection-close",
        ).catch(() => {});
        if (server) {
            const child = server.process();
            try {
                await closedProcess(child, () => server.close());
            } catch {
                // BrowserServer owns this exact child. Chromium may have its own
                // process group; a detached CLI process-group kill is insufficient.
                try {
                    await closedProcess(child, () => server.kill());
                } catch {
                    evidence.browser_drain_unknown = true;
                }
            }
            evidence.browser_closed =
                child.exitCode !== null || child.signalCode !== null;
            evidence.browser_exit = {
                code: child.exitCode,
                signal: child.signalCode,
            };
            evidence.descendants_closed = await descendantsClosed(descendants);
            activeServer = undefined;
        }
        // Include requests observed during context, browser and process cleanup.
        // This refusal runs after exact owned drains, so it cannot bypass them.
        if (networkObserver) {
            try {
                assertNativeNetworkObservation(networkObserver.state);
            } catch (error) {
                evidence.infrastructure_failed = true;
                evidence.network_diagnostic = safeDiagnostic(
                    error,
                    credentials,
                );
            }
        }
    }
}

async function main() {
    const args = argumentsFrom(process.argv.slice(2));
    const manifest = JSON.parse(await readFile(args.manifest, "utf8"));
    const runtime = JSON.parse(
        await readFile(path.join(args.workspace, "runtime.json"), "utf8"),
    );
    assert.equal(runtime.fixture_id, manifest.fixture_id);
    assert.ok(["", "/management"].includes(runtime.prefix));
    assertApplicationIdentity(runtime.expected_application);
    assert.equal(process.version, "v24.18.1");
    for (const variable of [
        "MOZ_DISABLE_CONTENT_SANDBOX",
        "MOZ_DISABLE_RDD_SANDBOX",
        "MOZ_DISABLE_GMP_SANDBOX",
        "WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS",
        "NODE_TLS_REJECT_UNAUTHORIZED",
    ]) {
        assert.equal(process.env[variable], undefined);
    }
    assert.equal(manifest.toolchain.playwright_version, "1.64.1");
    assert.equal(
        manifest.toolchain.image_manifest_sha256,
        "bdfda2a8fdf48707c5e50a49bd3e06d8d0c759153dc8ee057d8a81c3450bb3e9",
    );
    const moduleBytes = await readFile(manifest.toolchain.playwright_module);
    assert.equal(
        createHash("sha256").update(moduleBytes).digest("hex"),
        manifest.toolchain.playwright_module_sha256,
    );
    const packageJson = path.join(
        path.dirname(manifest.toolchain.playwright_module),
        "package.json",
    );
    const packageFacts = await lstat(packageJson);
    assert.ok(packageFacts.isFile() && !packageFacts.isSymbolicLink());
    assert.equal(
        JSON.parse(await readFile(packageJson, "utf8")).version,
        "1.64.1",
    );
    const facts = await lstat(args.workspace);
    assert.ok(facts.isDirectory() && (facts.mode & 0o077) === 0);
    const credentials = await deadline(
        credentialsFromPipe(),
        5000,
        "credential-pipe-deadline",
    );
    const playwright = await import(
        pathToFileURL(manifest.toolchain.playwright_module).href
    );
    const report = {
        schema_version: 1,
        fixture_id: manifest.fixture_id,
        node_version: process.version,
        engines: {},
    };
    const bindings = {
        manifest,
        workspace: args.workspace,
        prefix: runtime.prefix,
        expectedApplication: runtime.expected_application,
    };
    // Normal signal cleanup follows the same awaited BrowserServer ownership
    // boundaries. The parent refuses any deadline even if this exits cleanly.
    process.once("SIGTERM", () => {
        interrupted = true;
        interruptCase(new Error("interrupted"));
        // Close the exact owned BrowserServer immediately, so an in-flight page
        // promise cannot hold its detached browser beyond parent termination.
        if (activeServer) {
            deadline(activeServer.close(), 5000, "owned-signal-close").catch(
                async () => {
                    await activeServer?.kill().catch(() => {});
                },
            );
        }
    });
    for (const name of ENGINE_NAMES) {
        if (interrupted) break;
        await checkEngine(
            name,
            playwright[name],
            bindings,
            credentials,
            report,
        );
        await writeFile(
            path.join(args.workspace, "browser-report.json"),
            JSON.stringify(report, null, 2) + "\n",
            { mode: 0o600 },
        );
    }
    const passed =
        !interrupted &&
        ENGINE_NAMES.every((name) => {
            const item = report.engines[name];
            return (
                item?.passed === CASE_COUNT &&
                item.failed === 0 &&
                item.skipped === 0 &&
                item.browser_closed &&
                item.descendants_closed &&
                !item.descendant_inventory_unknown &&
                !item.infrastructure_failed
            );
        });
    process.exitCode = passed ? 0 : 1;
    process.stdout.write(
        passed
            ? "Native browser cases passed; exact browser processes closed.\n"
            : "Native browser cases failed; retained bounded report.\n",
    );
}

main().catch(() => {
    process.stderr.write(
        "Owned native browser prerequisite or lifecycle failed.\n",
    );
    process.exitCode = 1;
});
