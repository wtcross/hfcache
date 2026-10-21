/** Actual built UI/shared-Caddy fixture; no interception or page credentials. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { once } from "node:events";
import { performance } from "node:perf_hooks";
import {
    connect as connectHttp2,
    constants as h2,
    sensitiveHeaders,
} from "node:http2";
import { readFile, writeFile, lstat, open } from "node:fs/promises";
import { request as httpsRequest } from "node:https";
import { request as httpRequest } from "node:http";
import path from "node:path";
import { pathToFileURL } from "node:url";
import {
    safeDiagnostic,
    assertApplicationIdentity,
    assertVersionPayload,
    processProof,
    requireUnprivileged,
    chromiumProof,
    ownedCleanupInventory,
    descendantsClosed,
    nativeNetworkObserver,
    assertNativeNetworkObservation,
} from "../auth-api/sandbox.mjs";

export const TOOLS = new Set([
    "get_archive_status",
    "list_repositories",
    "list_revisions",
    "get_current_reference",
    "get_revision_manifest",
    "list_run_reports",
    "get_run_report",
    "get_verification_report",
    "estimate_verification",
    "search_models",
    "search_datasets",
    "get_catalog_entry",
    "list_model_variants",
    "get_catalog_facets",
]);
const MAX_BODY = 8 * 1024 * 1024;
const MAX_FILE = 2 * 1024 * 1024;
const STALL_CANCEL_MS = 2000;
const STALL_DEADLINE_MS = 35000;
const BROWSER_VERSIONS = {
    chromium: "156.0.8078.4",
    firefox: "157.0",
    webkit: "27.2",
};
const UI_CSP =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'none'; worker-src 'none'";
let activeServer;
let interrupted = false;

export function certificateRefusal(error) {
    return /ERR_CERT_AUTHORITY_INVALID|SEC_ERROR_UNKNOWN_ISSUER|Unacceptable TLS certificate/u.test(
        String(error?.message),
    );
}

export function secretDiagnostic(error, credentials) {
    const diagnostic = safeDiagnostic(error, credentials);
    for (const token of Object.values(credentials?.tokens ?? {})) {
        for (const value of [
            token,
            encodeURIComponent(token),
            Buffer.from(token).toString("base64"),
        ]) {
            diagnostic.message = diagnostic.message
                .split(value)
                .join("[redacted]");
        }
    }
    return diagnostic;
}

export function assertUiHeaders(headers, cache = "no-store") {
    assert.equal(headers["cache-control"], cache);
    assert.equal(headers["x-content-type-options"], "nosniff");
    assert.equal(headers["referrer-policy"], "no-referrer");
    assert.equal(
        headers["permissions-policy"],
        "camera=(), microphone=(), geolocation=()",
    );
    assert.equal(headers["content-security-policy"], UI_CSP);
    assert.equal(headers["set-cookie"], undefined);
    assert.equal(headers["access-control-allow-origin"], undefined);
}

export function envelope(value) {
    assert.equal(value.schema_version, 1);
    assert.match(value.request_id, /^[a-f0-9]{32}$/u);
    assert.ok(value.envelope && typeof value.envelope === "object");
    assert.ok(
        ["success", "success_with_warnings"].includes(value.envelope.outcome),
    );
    assert.equal(value.envelope.exit_code, 0);
    assert.deepEqual(value.envelope.errors, []);
    return value.envelope.data;
}

export function protocolMessage(bytes, contentType, id) {
    assert.ok(bytes.byteLength <= MAX_BODY);
    const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    let messages;
    if (contentType.startsWith("application/json"))
        messages = [JSON.parse(text)];
    else {
        assert.ok(contentType.startsWith("text/event-stream"));
        messages = text
            .split(/\r?\n/u)
            .filter((line) => line.startsWith("data: "))
            .map((line) => JSON.parse(line.slice(6)));
    }
    const matching = messages.filter((message) => message.id === id);
    assert.equal(matching.length, 1);
    const value = matching[0];
    assert.equal(value.jsonrpc, "2.0");
    assert.equal(value.error, undefined);
    assert.ok(value.result && typeof value.result === "object");
    return value.result;
}

export function fixedEndpoint(origin, prefix, suffix) {
    const parsed = new URL(origin);
    assert.equal(parsed.protocol, "https:");
    assert.equal(parsed.hostname, "127.0.0.1");
    assert.ok(parsed.port && parsed.origin === origin);
    assert.ok(["", "/management"].includes(prefix));
    assert.ok(suffix.startsWith("/") && !suffix.startsWith("//"));
    assert.ok(
        !/[?#\\]/u.test(suffix) &&
            !suffix.split("/").some((part) => part === "." || part === ".."),
    );
    const endpoint = new URL(origin + prefix + suffix);
    assert.equal(endpoint.origin, origin);
    return endpoint;
}

async function jsonFile(filename) {
    const facts = await lstat(filename);
    assert.ok(
        facts.isFile() && !facts.isSymbolicLink() && facts.size <= MAX_FILE,
    );
    return JSON.parse(await readFile(filename, "utf8"));
}

async function deadline(operation, milliseconds, label) {
    let timer;
    try {
        return await Promise.race([
            operation,
            new Promise((_resolve, reject) => {
                timer = setTimeout(
                    () => reject(new Error(label)),
                    milliseconds,
                );
            }),
        ]);
    } finally {
        clearTimeout(timer);
    }
}

export async function nodeRequest(
    endpoint,
    { ca, method = "GET", token, body, agent } = {},
) {
    assert.equal(endpoint.hostname, "127.0.0.1");
    assert.equal(endpoint.username + endpoint.password, "");
    assert.ok(["https:", "http:"].includes(endpoint.protocol));
    if (endpoint.protocol === "http:")
        assert.ok(
            token === undefined && body === undefined && method === "GET",
        );
    const data =
        body === undefined ? undefined : Buffer.from(JSON.stringify(body));
    assert.ok(data === undefined || data.byteLength <= 65536);
    return await new Promise((resolve, reject) => {
        const headers = { "User-Agent": agent ?? "hfcache-functional-node" };
        if (token !== undefined) headers.Authorization = `Bearer ${token}`;
        if (data !== undefined) {
            headers["Content-Type"] = "application/json";
            headers["Content-Length"] = String(data.byteLength);
            headers.Accept = "application/json, text/event-stream";
            headers["MCP-Protocol-Version"] = "2025-11-25";
        }
        const start =
            endpoint.protocol === "https:" ? httpsRequest : httpRequest;
        const request = start(
            endpoint,
            { method, headers, ca, rejectUnauthorized: true, agent: false },
            (response) => {
                const parts = [];
                let size = 0;
                response.on("data", (chunk) => {
                    size += chunk.length;
                    if (size > MAX_BODY) {
                        response.destroy(
                            new Error("bounded-response-overflow"),
                        );
                        return;
                    }
                    parts.push(chunk);
                });
                response.once("error", reject);
                response.once("end", () =>
                    resolve({
                        status: response.statusCode,
                        headers: response.headers,
                        body: Buffer.concat(parts),
                        rawHeaders: response.rawHeaders,
                    }),
                );
            },
        );
        const absolute = setTimeout(
            () => request.destroy(new Error("bounded-request-deadline")),
            10000,
        );
        request.once("close", () => clearTimeout(absolute));
        request.setTimeout(10000, () =>
            request.destroy(new Error("bounded-request-timeout")),
        );
        request.once("error", reject);
        request.end(data);
    });
}

export async function assertPhase(runtime, phase, workspace) {
    assert.equal(runtime.phase_path, path.join(workspace, "browser-phase.txt"));
    const handle = await open(
        runtime.phase_path,
        constants.O_RDONLY | constants.O_NOFOLLOW,
    );
    try {
        const facts = await handle.stat();
        assert.ok(facts.isFile() && facts.nlink === 1 && facts.size <= 32);
        assert.equal(facts.dev, runtime.phase_identity.device);
        assert.equal(facts.ino, runtime.phase_identity.inode);
        assert.equal(await handle.readFile("ascii"), phase + "\n");
        const after = await lstat(runtime.phase_path);
        assert.ok(after.isFile() && !after.isSymbolicLink());
        assert.equal(after.dev, facts.dev);
        assert.equal(after.ino, facts.ino);
    } finally {
        await handle.close();
    }
}

export function largestJavascript(manifest) {
    const members = manifest.members.filter(
        (member) => member.mime === "text/javascript" && member.bytes > 0,
    );
    assert.ok(members.length > 0);
    return members.reduce((largest, member) =>
        member.bytes > largest.bytes ? member : largest,
    );
}

/** Real TLS HTTP/2 stream-level backpressure; never opens an alternate origin.
 * Node24.18.1 http2 documentation defines initialWindowSize=0 and localSettings
 * as receipt of SETTINGS acknowledgement. This suppresses response DATA, not
 * upstream sends; only correlated original API transfer facts establish stall.
 * https://nodejs.org/download/release/v24.18.1/docs/api/http2.html
 */
export async function zeroWindowProbe(
    endpoint,
    credentials,
    ca,
    engine,
    mode,
    during,
) {
    assert.equal(endpoint.protocol, "https:");
    assert.equal(endpoint.hostname, "127.0.0.1");
    assert.equal(endpoint.username + endpoint.password, "");
    assert.ok(["cancel", "deadline"].includes(mode));
    const heldMs = mode === "cancel" ? STALL_CANCEL_MS : STALL_DEADLINE_MS;
    const session = connectHttp2(endpoint.origin, {
        ca,
        rejectUnauthorized: true,
        settings: { initialWindowSize: 0, enablePush: false },
    });
    let stream,
        bodyBytes = 0,
        ended = false,
        remoteClosed = false,
        streamClosedObserved = false,
        sessionClosedObserved = false;
    let streamClosedPromise;
    const sessionClosedPromise = new Promise((resolve) =>
        session.once("close", () => {
            sessionClosedObserved = true;
            resolve();
        }),
    );
    let sessionFault = false,
        timer;
    const result = {
        mode,
        origin: endpoint.origin,
        path: endpoint.pathname,
        initial_window_size: 0,
        push_enabled: false,
        settings_acknowledged: false,
        received_bytes: 0,
        client_cancel_after_ms: null,
        observed_ms: 0,
        remote_closed: false,
        stream_closed: false,
        session_closed: false,
    };
    session.on("error", () => {
        sessionFault = true;
    });
    const absolute = setTimeout(() => session.destroy(), heldMs + 12000);
    try {
        await deadline(
            once(session, "localSettings"),
            5000,
            "http2-settings-ack",
        );
        assert.equal(session.localSettings.initialWindowSize, 0);
        assert.equal(session.localSettings.enablePush, false);
        assert.equal(session.alpnProtocol, "h2");
        assert.equal(session.encrypted, true);
        result.settings_acknowledged = true;
        // Only this Node transport probe uses Basic directly. The browser keeps
        // its native credential challenge; page JavaScript never sees a secret.
        stream = session.request({
            ":method": "GET",
            ":path": endpoint.pathname,
            authorization:
                "Basic " +
                Buffer.from(
                    credentials.username + ":" + credentials.password,
                ).toString("base64"),
            "user-agent": `hfcache-functional-node/${engine}`,
            [sensitiveHeaders]: ["authorization"],
        });
        stream.on("error", () => {});
        stream.on("data", (chunk) => {
            bodyBytes += chunk.length;
        });
        stream.once("end", () => {
            ended = true;
        });
        streamClosedPromise = new Promise((resolve) =>
            stream.once("close", () => {
                remoteClosed = true;
                streamClosedObserved = true;
                resolve();
            }),
        );
        const [headers] = await deadline(
            once(stream, "response"),
            5000,
            "http2-response-headers",
        );
        assert.equal(headers[":status"], 200);
        assert.match(headers["x-request-id"], /^[a-f0-9]{32}$/u);
        result.request_id = headers["x-request-id"];
        result.status = headers[":status"];
        const started = performance.now();
        await Promise.all([
            Promise.race([
                streamClosedPromise,
                new Promise((resolve) => {
                    timer = setTimeout(resolve, heldMs);
                }),
            ]),
            during?.(),
        ]);
        clearTimeout(timer);
        result.observed_ms = performance.now() - started;
        result.remote_closed = remoteClosed;
        assert.equal(bodyBytes, 0);
        assert.equal(ended, false);
        if (mode === "cancel") assert.equal(remoteClosed, false);
        else if (remoteClosed) assert.ok(result.observed_ms >= 28000);
        if (!stream.closed && !stream.destroyed) {
            result.client_cancel_after_ms = result.observed_ms;
            stream.close(h2.NGHTTP2_CANCEL);
        }
        await deadline(streamClosedPromise, 3000, "http2-stream-close");
        assert.equal(sessionFault, false);
        result.received_bytes = bodyBytes;
        return result;
    } finally {
        clearTimeout(timer);
        clearTimeout(absolute);
        if (stream && !stream.closed && !stream.destroyed)
            stream.close(h2.NGHTTP2_CANCEL);
        if (streamClosedPromise && !streamClosedObserved)
            await deadline(
                streamClosedPromise,
                1000,
                "http2-final-stream-close",
            ).catch(() => stream.destroy());
        result.stream_closed = stream === undefined || streamClosedObserved;
        session.close();
        await deadline(sessionClosedPromise, 1000, "http2-session-close").catch(
            () => session.destroy(),
        );
        if (!sessionClosedObserved) {
            session.destroy();
            await deadline(
                sessionClosedPromise,
                1000,
                "http2-destroyed-session-close",
            );
        }
        if (streamClosedPromise && !streamClosedObserved)
            await deadline(
                streamClosedPromise,
                1000,
                "http2-destroyed-stream-close",
            );
        result.stream_closed = stream === undefined || streamClosedObserved;
        result.session_closed = sessionClosedObserved;
    }
}

async function mcpCalls(binding, credentials, ca, page, engine) {
    const endpoint = fixedEndpoint(binding.origin, binding.prefix, "/mcp/");
    const agent = `hfcache-functional-node/${engine}`;
    let next = 0;
    const rpc = async (method, params) => {
        assert.equal(page.isClosed(), false);
        assert.equal(new URL(page.url()).origin, binding.origin);
        const id = ++next;
        const response = await nodeRequest(endpoint, {
            ca,
            method: "POST",
            token: credentials.tokens.mcp_reader,
            agent,
            body: { jsonrpc: "2.0", id, method, params },
        });
        assert.equal(response.status, 200);
        return protocolMessage(
            response.body,
            response.headers["content-type"],
            id,
        );
    };
    const initialized = await rpc("initialize", {
        protocolVersion: "2025-11-25",
        capabilities: {},
        clientInfo: { name: "hfcache-functional-native-active", version: "1" },
    });
    assert.ok(initialized.serverInfo && initialized.capabilities);
    const listed = await rpc("tools/list", {});
    assert.deepEqual(new Set(listed.tools.map((tool) => tool.name)), TOOLS);
    const results = {};
    for (const name of [...TOOLS].sort()) {
        const result = await rpc("tools/call", {
            name,
            arguments: binding.mcp_arguments[name],
        });
        assert.notEqual(result.isError, true);
        const data = result.structuredContent;
        envelope(data);
        results[name] = {
            passed: true,
            request_id: data.request_id,
            outcome: data.envelope.outcome,
            browser_active: !page.isClosed(),
            origin: endpoint.origin,
        };
    }
    return results;
}

async function closed(child, action) {
    if (child.exitCode !== null || child.signalCode !== null) return;
    const completion = new Promise((resolve) => child.once("close", resolve));
    await deadline(
        Promise.all([completion, action()]),
        5000,
        "owned-browser-close-deadline",
    );
}

async function checkEngine(name, type, bindings, credentials, phase) {
    const evidence = { version: null, cases: [], owned_descendants: [] };
    const retained = new Map();
    let server;
    let browser;
    let context;
    let observer;
    let page;
    const test = async (id, operation) => {
        const record = { id, attempts: 1, passed: false };
        evidence.cases.push(record);
        try {
            await deadline(
                operation(),
                id === "static-abort-drain" ? 55000 : 20000,
                `functional-case-deadline:${id}`,
            );
            record.passed = true;
        } catch (error) {
            record.diagnostic = secretDiagnostic(error, credentials);
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
        assert.equal(evidence.version, BROWSER_VERSIONS[name]);
        if (name === "chromium") {
            evidence.sandbox = { verified: false };
            await chromiumProof(browser, evidence.process, evidence.sandbox);
        }
        for (const proof of evidence.sandbox?.observed_descendants ?? [])
            retained.set(`${proof.pid}:${proof.start_ticks}`, proof);
        context = await browser.newContext({
            ...(phase === "trusted"
                ? {
                      httpCredentials: {
                          username: credentials.username,
                          password: credentials.password,
                      },
                  }
                : {}),
            userAgent: `hfcache-web-functional/${name}`,
            ignoreHTTPSErrors: false,
            serviceWorkers: "block",
            viewport: { width: 1440, height: 1000 },
        });
        observer = nativeNetworkObserver({ trusted: bindings.origin });
        evidence.network_observation = observer.state;
        // No route/HAR/CDP interception: Playwright otherwise synthesizes Chromium
        // preflights. The positively owned guest network is separately confined.
        context.on("request", (request) => observer.observe(request.url()));
        page = await context.newPage();
        page.setDefaultTimeout(10000);
        page.setDefaultNavigationTimeout(15000);
        const ui = bindings.prefix + "/ui/";
        if (phase === "untrusted") {
            await test("untrusted-certificate-refused", async () => {
                let caught;
                try {
                    await page.goto(bindings.origin + ui);
                } catch (error) {
                    caught = error;
                }
                evidence.certificate_diagnostic = secretDiagnostic(
                    caught ?? new Error("navigation-unexpectedly-succeeded"),
                    credentials,
                );
                assert.ok(caught && certificateRefusal(caught));
                evidence.certificate_refused = true;
            });
        } else {
            const ca = await readFile(bindings.manifest.browser.ca.path);
            const negative = bindings.untrusted.engines[name];
            await test("untrusted-certificate-refused", async () => {
                assert.equal(negative.certificate_refused, true);
                assert.equal(negative.browser_closed, true);
                assert.equal(negative.descendants_closed, true);
                assert.deepEqual(
                    negative.cases.map((item) => [
                        item.id,
                        item.passed,
                        item.attempts,
                    ]),
                    [["untrusted-certificate-refused", true, 1]],
                );
                evidence.untrusted_phase = negative;
            });
            await test("native-ui-challenge", async () => {
                const challenge = await nodeRequest(
                    fixedEndpoint(bindings.origin, bindings.prefix, "/ui/"),
                    { ca },
                );
                assert.equal(challenge.status, 401);
                assert.ok(
                    challenge.headers["www-authenticate"].startsWith("Basic"),
                );
                const alias = page.waitForResponse(
                    (response) =>
                        response.url() ===
                            bindings.origin + bindings.prefix + "/ui" &&
                        response.status() === 307,
                );
                const response = await page.goto(
                    bindings.origin + bindings.prefix + "/ui",
                );
                assert.equal((await alias).headers().location, ui);
                assert.equal(response.status(), 200);
                assert.equal(new URL(page.url()).origin, bindings.origin);
                await page
                    .getByRole("navigation")
                    .getByRole("link", { name: "Library", exact: true })
                    .waitFor();
            });
            await test("validated-bootstrap", async () => {
                const slots = await page
                    .locator("meta[name^='hfcache-ui-']")
                    .evaluateAll((elements) =>
                        elements.map((element) => [
                            element.getAttribute("name"),
                            element.getAttribute("content"),
                        ]),
                    );
                const values = Object.fromEntries(slots);
                assert.equal(slots.length, 4);
                assert.equal(values["hfcache-ui-base"], ui);
                assert.equal(
                    values["hfcache-ui-bootstrap"],
                    ui + "bootstrap.json",
                );
                assert.equal(
                    values["hfcache-ui-fingerprint"],
                    bindings.asset_manifest_sha256,
                );
                assert.equal(values["hfcache-ui-contract"], "1");
                const result = await page.evaluate(async (endpoint) => {
                    const response = await fetch(endpoint, {
                        credentials: "same-origin",
                        cache: "no-store",
                        redirect: "error",
                    });
                    return {
                        status: response.status,
                        body: await response.json(),
                    };
                }, ui + "bootstrap.json");
                assert.equal(result.status, 200);
                assert.equal(result.body.kind, "hfcache_ui_bootstrap");
                assert.equal(result.body.schema_version, 1);
                assert.equal(result.body.configured_origin, bindings.origin);
                assert.equal(result.body.paths.public_prefix, bindings.prefix);
                assert.equal(
                    result.body.paths.effective_prefix,
                    bindings.prefix,
                );
                assert.equal(result.body.paths.ui_base, ui);
                assert.equal(
                    result.body.paths.api_base,
                    bindings.prefix + "/api/v1",
                );
                assert.equal(
                    result.body.paths.mcp_base,
                    bindings.prefix + "/mcp/",
                );
                assert.equal(
                    result.body.build.asset_manifest_sha256,
                    bindings.asset_manifest_sha256,
                );
                assert.deepEqual(
                    result.body.build.metadata,
                    bindings.asset_manifest.build,
                );
                assert.equal(result.body.user.authentication_method, "basic");
                assert.equal(result.body.user.credential_class, "rest-writer");
                assert.equal(result.body.config_fingerprint, null);
                evidence.instance_id = result.body.instance_id;
            });
            await test("workspaces-deep-refresh", async () => {
                for (const [route, label] of [
                    ["library", "Library"],
                    ["operations", "Operations"],
                    ["maintenance", "Maintenance"],
                    ["administration", "Administration"],
                ]) {
                    const response = await page.goto(
                        bindings.origin + ui + route,
                    );
                    assert.equal(response.status(), 200);
                    await page
                        .getByRole("navigation")
                        .getByRole("link", { name: label, exact: true })
                        .waitFor();
                    assert.equal((await page.reload()).status(), 200);
                }
            });
            await test("history-back-forward", async () => {
                await page
                    .getByRole("navigation")
                    .getByRole("link", { name: "Library", exact: true })
                    .click();
                await page
                    .getByRole("navigation")
                    .getByRole("link", { name: "Operations", exact: true })
                    .click();
                await page.goBack();
                assert.equal(new URL(page.url()).pathname, ui + "library");
                await page.goForward();
                assert.equal(new URL(page.url()).pathname, ui + "operations");
            });
            await test("same-origin-security-headers", async () => {
                const result = await page.evaluate(
                    async (endpoints) => {
                        const rows = [];
                        for (const endpoint of endpoints) {
                            const response = await fetch(endpoint, {
                                credentials: "same-origin",
                                cache: "no-store",
                            });
                            rows.push({
                                status: response.status,
                                headers: Object.fromEntries(response.headers),
                                body: await response.text(),
                            });
                        }
                        return rows;
                    },
                    [
                        ui,
                        ui + "bootstrap.json",
                        ui + "licenses.json",
                        ui + "THIRD_PARTY_NOTICES.txt",
                    ],
                );
                for (const row of result) {
                    assert.equal(row.status, 200);
                    assertUiHeaders(row.headers);
                }
                for (const member of bindings.asset_manifest.members.filter(
                    (item) => item.path.startsWith("assets/"),
                )) {
                    const item = await page.evaluate(async (endpoint) => {
                        const response = await fetch(endpoint, {
                            credentials: "same-origin",
                            cache: "no-store",
                        });
                        const bytes = new Uint8Array(
                            await response.arrayBuffer(),
                        );
                        return {
                            status: response.status,
                            headers: Object.fromEntries(response.headers),
                            bytes: Array.from(bytes),
                        };
                    }, ui + member.path);
                    assert.equal(item.status, 200);
                    assert.equal(item.bytes.length, member.bytes);
                    assert.equal(
                        createHash("sha256")
                            .update(Buffer.from(item.bytes))
                            .digest("hex"),
                        member.sha256,
                    );
                    const hashed = /-[A-Za-z0-9_-]{8,64}\.[A-Za-z0-9]+$/u.test(
                        member.path,
                    );
                    assertUiHeaders(
                        item.headers,
                        hashed
                            ? "private, max-age=3600, immutable"
                            : "no-store",
                    );
                }
            });
            await test("missing-assets-isolated", async () => {
                const rows = await page.evaluate(async (base) => {
                    const result = [];
                    for (const name of [
                        "assets/missing-00000000.js",
                        "assets/missing-00000000.css",
                        "unknown-workspace",
                        "manifest.json",
                        "assets/%2e%2e/manifest.json",
                    ]) {
                        const response = await fetch(base + name, {
                            credentials: "same-origin",
                            redirect: "error",
                        });
                        result.push({
                            status: response.status,
                            type: response.headers.get("content-type"),
                            text: await response.text(),
                        });
                    }
                    return result;
                }, ui);
                for (const row of rows) {
                    assert.ok(row.status >= 400);
                    assert.ok(!row.type?.includes("text/html"));
                    assert.ok(!row.text.includes('<div id="root"'));
                }
            });
            await test("api-mcp-errors-not-html", async () => {
                const rows = await page.evaluate(
                    async (endpoints) => {
                        const results = [];
                        for (const endpoint of endpoints) {
                            const response = await fetch(endpoint, {
                                credentials: "same-origin",
                                redirect: "error",
                            });
                            results.push({
                                status: response.status,
                                type: response.headers.get("content-type"),
                                text: await response.text(),
                            });
                        }
                        return results;
                    },
                    [
                        bindings.prefix + "/api/v1/unknown-interface",
                        bindings.prefix + "/mcp/unknown-interface",
                    ],
                );
                for (const row of rows) {
                    assert.ok(row.status >= 400);
                    assert.ok(!row.type?.includes("text/html"));
                    assert.ok(!row.text.includes('<div id="root"'));
                }
            });
            await test("unsafe-method-no-fallback", async () => {
                const row = await page.evaluate(async (endpoint) => {
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
                        type: response.headers.get("content-type"),
                    };
                }, ui + "library");
                assert.ok(row.status >= 400);
                assert.ok(!row.type?.includes("text/html"));
            });
            await test("same-origin-json-validation", async () => {
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
                        body: await response.json(),
                    };
                }, bindings.prefix + "/api/v1/config/validate");
                assert.equal(result.status, 200);
                envelope(result.body);
            });
            await test("bearer-rest-with-browser", async () => {
                const version = await nodeRequest(
                    fixedEndpoint(
                        bindings.origin,
                        bindings.prefix,
                        "/api/v1/version",
                    ),
                    { ca, token: credentials.tokens.writer },
                );
                assert.equal(version.status, 200);
                assertVersionPayload(
                    JSON.parse(version.body),
                    bindings.asset_manifest.build.application_version,
                );
                const rows = {};
                for (const [key, expected] of [
                    ["writer", "rest-writer"],
                    ["reader", "rest-reader"],
                ]) {
                    assert.equal(page.isClosed(), false);
                    const result = await nodeRequest(
                        fixedEndpoint(
                            bindings.origin,
                            bindings.prefix,
                            "/api/v1/capabilities",
                        ),
                        {
                            ca,
                            token: credentials.tokens[key],
                            agent: `hfcache-functional-node/${name}`,
                        },
                    );
                    assert.equal(result.status, 200);
                    const capabilities = envelope(JSON.parse(result.body));
                    assert.equal(capabilities.credential_class, expected);
                    assert.equal(
                        capabilities.instance_id,
                        evidence.instance_id,
                    );
                    rows[key] = {
                        status: result.status,
                        credential_class: capabilities.credential_class,
                        instance_id: capabilities.instance_id,
                        browser_active: !page.isClosed(),
                    };
                    const uiRefusal = await nodeRequest(
                        fixedEndpoint(bindings.origin, bindings.prefix, "/ui/"),
                        { ca, token: credentials.tokens[key] },
                    );
                    assert.ok(uiRefusal.status >= 400);
                    assert.ok(
                        !uiRefusal.headers["content-type"]?.includes(
                            "text/html",
                        ),
                    );
                }
                const refused = await nodeRequest(
                    fixedEndpoint(
                        bindings.origin,
                        bindings.prefix,
                        "/api/v1/version",
                    ),
                    { ca, token: credentials.tokens.mcp_reader },
                );
                assert.equal(refused.status, 401);
                evidence.rest_classes = rows;
            });
            await test("all-mcp-tools-with-browser", async () => {
                evidence.mcp_tools = await mcpCalls(
                    bindings,
                    credentials,
                    ca,
                    page,
                    name,
                );
            });
            await test("native-prefix-projection", async () => {
                const row = await page.evaluate(async (endpoint) => {
                    const response = await fetch(endpoint, {
                        credentials: "same-origin",
                        headers: {
                            "X-Forwarded-Prefix": "/forged",
                            "X-Script-Name": "/forged",
                        },
                    });
                    return {
                        status: response.status,
                        body: await response.json(),
                    };
                }, ui + "bootstrap.json");
                assert.equal(row.status, 200);
                assert.equal(row.body.paths.public_prefix, bindings.prefix);
                assert.equal(row.body.paths.effective_prefix, bindings.prefix);
            });
            await test("plaintext-refused", async () => {
                const endpoint = fixedEndpoint(
                    bindings.origin,
                    bindings.prefix,
                    "/ui/",
                );
                endpoint.protocol = "http:";
                const row = await nodeRequest(endpoint);
                assert.ok(row.status >= 400);
                assert.ok(!row.headers.location);
                evidence.plaintext_status = row.status;
            });
            await test("private-browser-storage", async () => {
                const stored = await page.evaluate(() => ({
                    local: Object.entries(localStorage),
                    session: Object.entries(sessionStorage),
                    cookies: document.cookie,
                }));
                assert.deepEqual(stored, {
                    local: [],
                    session: [],
                    cookies: "",
                });
            });
            await test("same-origin-network", async () => {
                assertNativeNetworkObservation(observer.state);
            });
            await test("static-abort-drain", async () => {
                const member = largestJavascript(bindings.asset_manifest);
                const endpoint = fixedEndpoint(
                    bindings.origin,
                    bindings.prefix,
                    "/ui/" + member.path,
                );
                const requests = await page.evaluate(async (url) => {
                    const head = await fetch(url, {
                        method: "HEAD",
                        credentials: "same-origin",
                        cache: "no-store",
                    });
                    const result = {
                        head: {
                            status: head.status,
                            request_id: head.headers.get("x-request-id"),
                            bytes: (await head.arrayBuffer()).byteLength,
                            headers: Object.fromEntries(head.headers),
                        },
                        cancels: [],
                    };
                    for (let index = 0; index < 8; index++) {
                        const controller = new globalThis.AbortController();
                        const response = await fetch(url, {
                            credentials: "same-origin",
                            cache: "no-store",
                            signal: controller.signal,
                        });
                        const reader = response.body.getReader();
                        const first = await reader.read();
                        await reader.cancel();
                        controller.abort();
                        result.cancels.push({
                            status: response.status,
                            request_id: response.headers.get("x-request-id"),
                            read_bytes: first.value?.byteLength ?? 0,
                            first_read_done: first.done,
                            reader_cancelled: true,
                            controller_aborted: controller.signal.aborted,
                        });
                    }
                    return result;
                }, endpoint.href);
                assert.equal(requests.head.status, 200);
                assert.equal(requests.head.bytes, 0);
                assertUiHeaders(
                    requests.head.headers,
                    "private, max-age=3600, immutable",
                );
                assert.equal(requests.cancels.length, 8);
                for (const row of requests.cancels) {
                    assert.equal(row.status, 200);
                    assert.ok(
                        row.read_bytes > 0 && row.read_bytes <= member.bytes,
                    );
                    assert.equal(row.reader_cancelled, true);
                    assert.equal(row.controller_aborted, true);
                }
                let bearer;
                const cancel = await zeroWindowProbe(
                    endpoint,
                    credentials,
                    ca,
                    name,
                    "cancel",
                    async () => {
                        bearer = await nodeRequest(
                            fixedEndpoint(
                                bindings.origin,
                                bindings.prefix,
                                "/api/v1/capabilities",
                            ),
                            {
                                ca,
                                token: credentials.tokens.reader,
                                agent: `hfcache-functional-node/${name}`,
                            },
                        );
                    },
                );
                assert.ok(bearer);
                assert.equal(bearer.status, 200);
                assert.equal(
                    envelope(JSON.parse(bearer.body)).instance_id,
                    evidence.instance_id,
                );
                const stalled = await zeroWindowProbe(
                    endpoint,
                    credentials,
                    ca,
                    name,
                    "deadline",
                );
                evidence.static_abort = {
                    member: {
                        path: member.path,
                        bytes: member.bytes,
                        sha256: member.sha256,
                    },
                    head: requests.head,
                    browser_cancels: requests.cancels,
                    cancel,
                    deadline: stalled,
                    concurrent_bearer: {
                        status: bearer.status,
                        request_id: JSON.parse(bearer.body).request_id,
                        instance_id: evidence.instance_id,
                        browser_active: !page.isClosed(),
                    },
                };
            });
            await page.screenshot({
                path: path.join(
                    bindings.workspace,
                    `functional-${bindings.profile}-${bindings.prefix ? "prefixed" : "root"}-${name}.png`,
                ),
                fullPage: true,
            });
        }
    } catch (error) {
        evidence.infrastructure_failed = true;
        evidence.diagnostic = secretDiagnostic(error, credentials);
    } finally {
        if (server) {
            try {
                for (const proof of await ownedCleanupInventory(
                    server.process(),
                    evidence.process,
                )) {
                    const key = `${proof.pid}:${proof.start_ticks}`;
                    if (!retained.has(key)) retained.set(key, proof);
                }
            } catch (error) {
                evidence.descendant_inventory_unknown = true;
                evidence.descendant_diagnostic = secretDiagnostic(
                    error,
                    credentials,
                );
            }
        }
        evidence.owned_descendants = [...retained.values()];
        await deadline(
            context?.close() ?? Promise.resolve(),
            5000,
            "functional-context-close",
        ).catch(() => {});
        await deadline(
            browser?.close() ?? Promise.resolve(),
            5000,
            "functional-browser-disconnect",
        ).catch(() => {});
        if (server) {
            const child = server.process();
            try {
                await closed(child, () => server.close());
            } catch {
                try {
                    await closed(child, () => server.kill());
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
            evidence.descendants_closed = await descendantsClosed(
                evidence.owned_descendants,
            );
            activeServer = undefined;
        }
        if (observer) {
            try {
                assertNativeNetworkObservation(observer.state);
            } catch (error) {
                evidence.infrastructure_failed = true;
                evidence.network_diagnostic = secretDiagnostic(
                    error,
                    credentials,
                );
            }
        }
    }
    return evidence;
}

async function credentialsFromPipe() {
    const chunks = [];
    let size = 0;
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
    assert.ok(Buffer.byteLength(value.password) <= 1024);
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

export async function main(argv = process.argv.slice(2)) {
    if (argv.length === 1 && argv[0] === "--help") {
        console.log(
            "Run only through the protected functional fixture launcher.",
        );
        return;
    }
    assert.equal(argv.length, 6);
    assert.equal(argv[0], "--manifest");
    assert.equal(argv[2], "--workspace");
    assert.equal(argv[4], "--phase");
    assert.ok(["trusted", "untrusted"].includes(argv[5]));
    const manifest = await jsonFile(argv[1]);
    const workspace = argv[3];
    const runtime = await jsonFile(path.join(workspace, "runtime.json"));
    assert.equal(runtime.fixture_id, manifest.fixture_id);
    assert.ok(["application", "native", "rootless"].includes(runtime.profile));
    assert.equal(runtime.origin, manifest.profiles[runtime.profile].origin);
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
    const phase = argv[5];
    await assertPhase(runtime, phase, workspace);
    const credentials =
        phase === "trusted"
            ? await deadline(
                  credentialsFromPipe(),
                  5000,
                  "functional-credential-pipe",
              )
            : {};
    const bindings = {
        ...runtime,
        workspace,
        manifest,
        ...(phase === "trusted"
            ? {
                  untrusted: await jsonFile(
                      path.join(workspace, "browser-untrusted-report.json"),
                  ),
              }
            : {}),
    };
    const report = {
        schema_version: 1,
        fixture_id: runtime.fixture_id,
        profile: runtime.profile,
        prefix: runtime.prefix,
        asset_manifest_sha256: runtime.asset_manifest_sha256,
        engines: {},
    };
    process.once("SIGTERM", () => {
        interrupted = true;
        void activeServer?.close().catch(() => {});
    });
    for (const name of ["chromium", "firefox", "webkit"]) {
        assert.equal(interrupted, false);
        report.engines[name] = await checkEngine(
            name,
            playwright[name],
            bindings,
            credentials,
            phase,
        );
    }
    const filename =
        phase === "trusted"
            ? "browser-report.json"
            : "browser-untrusted-report.json";
    await writeFile(
        path.join(workspace, filename),
        JSON.stringify(report, null, 2) + "\n",
        { flag: "wx", mode: 0o600 },
    );
    if (
        interrupted ||
        Object.values(report.engines).some(
            (engine) =>
                engine.infrastructure_failed ||
                engine.descendant_inventory_unknown ||
                !engine.browser_closed ||
                !engine.descendants_closed ||
                engine.cases.some((item) => !item.passed),
        )
    )
        process.exitCode = 1;
}

if (
    process.argv[1] &&
    pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url
) {
    main().catch(() => {
        console.error(
            "Functional browser prerequisite or evidence refused; preserve the owned workspace.",
        );
        process.exitCode = 1;
    });
}
