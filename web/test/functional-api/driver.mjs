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
import { pathToFileURL, URLSearchParams } from "node:url";
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

/** WEB029: presentation-only disclosure access never substitutes for read evidence. */
export async function openLibraryDisclosure(page, label) {
    const summary = page
        .getByRole("region", { name: "Repository library", exact: true })
        .getByText(label, { exact: true });
    if (
        !(await summary.evaluate(
            (node) => node.closest("details")?.open === true,
        ))
    )
        await summary.click();
}

export function certificateRefusal(error) {
    return /ERR_CERT_AUTHORITY_INVALID|SEC_ERROR_UNKNOWN_ISSUER|Unacceptable TLS certificate/u.test(
        String(error?.message),
    );
}

export function certificateNavigationRefusal(
    error,
    failure,
    expectedUrl,
    response,
) {
    return (
        response === null &&
        error instanceof Error &&
        failure?.url === expectedUrl &&
        failure?.navigation === true &&
        (certificateRefusal(error) ||
            certificateRefusal({ message: failure.errorText }))
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

export function assertApiHeaders(headers) {
    assert.equal(headers["cache-control"], "no-store");
    assert.equal(headers["x-content-type-options"], "nosniff");
    assert.equal(headers["content-security-policy"], "frame-ancestors 'none'");
    assert.equal(headers["set-cookie"], undefined);
    assert.equal(headers["access-control-allow-origin"], undefined);
}

export function assertCredentialRefusal(row, challenge) {
    const challenges = {
        basic: 'Basic realm="hfcache", charset="UTF-8"',
        bearer: 'Bearer realm="hfcache"',
        both: 'Basic realm="hfcache", charset="UTF-8", Bearer realm="hfcache"',
    };
    assert.ok(Object.hasOwn(challenges, challenge));
    assert.equal(row.status, 401);
    assert.equal(row.headers["www-authenticate"], challenges[challenge]);
    assert.equal(row.headers.location, undefined);
    assert.ok(!row.headers["content-type"]?.includes("text/html"));
}

export function basicReadProbes(credentials) {
    assert.ok(
        typeof credentials.username === "string" &&
            typeof credentials.password === "string" &&
            Buffer.byteLength(credentials.username) <= 128 &&
            Buffer.byteLength(credentials.password) <= 1024,
    );
    const basic = (value) => "Basic " + Buffer.from(value).toString("base64");
    const valid = basic(credentials.username + ":" + credentials.password);
    const wrongUser =
        credentials.username === "refusal-user"
            ? "other-refusal-user"
            : "refusal-user";
    const wrongPassword =
        credentials.password === "refusal-password"
            ? "other-refusal-password"
            : "refusal-password";
    return [
        ["missing", []],
        ["wrong-user", [basic(wrongUser + ":" + credentials.password)]],
        ["wrong-password", [basic(credentials.username + ":" + wrongPassword)]],
        ["malformed-base64", ["Basic %%%"]],
        ["missing-colon", [basic("invalid-no-colon")]],
        ["noncanonical-base64", [basic("a:b") + "="]],
        ["invalid-utf8-user", [basic(Buffer.from([255, 58, 120]))]],
        [
            "invalid-utf8-password",
            [
                basic(
                    Buffer.concat([
                        Buffer.from(credentials.username + ":"),
                        Buffer.from([255]),
                    ]),
                ),
            ],
        ],
        ["duplicate-headers", [valid, valid]],
        ["duplicate-schemes", [valid + ", Bearer invalid"]],
        ["oversized-user", [basic("u".repeat(129) + ":x")]],
        [
            "oversized-password",
            [basic(credentials.username + ":" + "p".repeat(1025))],
        ],
        ["oversized-authorization", ["Basic " + "a".repeat(8193 - 6)]],
    ].map(([label, authorization]) => ({ label, authorization }));
}

export function basicReadHeaders(endpoint, authorization, agent) {
    assert.ok(
        endpoint.protocol === "https:" &&
            endpoint.hostname === "127.0.0.1" &&
            endpoint.username + endpoint.password === "" &&
            Array.isArray(authorization) &&
            authorization.length <= 2 &&
            authorization.every(
                (value) =>
                    typeof value === "string" &&
                    /^[\x20-\x7e]{1,8193}$/u.test(value),
            ),
    );
    // A raw alternating array preserves duplicate Authorization fields. Host is
    // explicit because Node's raw-header form does not synthesize it.
    return [
        "Host",
        endpoint.host,
        "User-Agent",
        agent ?? "hfcache-functional-node",
        ...authorization.flatMap((value) => ["Authorization", value]),
    ];
}

export function basicReadRefusal(row, probe, credentials) {
    try {
        assertCredentialRefusal(
            row,
            probe.authorization.length === 0 ? "both" : "basic",
        );
        assertApiHeaders(row.headers);
        assert.ok(row.headers["content-type"]?.startsWith("application/json"));
        assert.ok(Buffer.isBuffer(row.body) && row.body.byteLength <= 4096);
        const text = new TextDecoder("utf-8", { fatal: true }).decode(row.body);
        const exposed = text + JSON.stringify(row.headers);
        const privateValues = [
            credentials.password,
            ...probe.authorization.flatMap((value) => [value, value.slice(6)]),
        ];
        for (const secret of privateValues)
            for (const variant of [
                secret,
                encodeURIComponent(secret),
                Buffer.from(secret).toString("base64"),
            ])
                assert.ok(!variant || !exposed.includes(variant));
        const problem = JSON.parse(text);
        assert.deepEqual(Object.keys(problem).sort(), [
            "code",
            "exit_code",
            "message",
            "request_id",
        ]);
        assert.ok(
            problem.code === "HFAPI001" &&
                problem.exit_code === 10 &&
                problem.message === "Not authenticated" &&
                typeof problem.request_id === "string" &&
                /^[0-9a-f]{32}$/u.test(problem.request_id),
        );
        const normalized = {
            code: problem.code,
            message: problem.message,
            exit_code: problem.exit_code,
        };
        return {
            label: probe.label,
            status: row.status,
            code: problem.code,
            request_id: problem.request_id,
            authorization_fields: probe.authorization.length,
            body_bytes: row.body.byteLength,
            body_sha256: createHash("sha256").update(row.body).digest("hex"),
            problem_sha256: createHash("sha256")
                .update(JSON.stringify(normalized))
                .digest("hex"),
        };
    } catch {
        // Never retain a parser/assertion message containing a reflected header
        // or credential, including derived invalid Basic encodings.
        throw new Error("Basic read refusal was not proven.");
    }
}

export function assertBootstrapPaths(paths, prefix) {
    assert.ok(["", "/management"].includes(prefix));
    assert.ok(["", "/management"].includes(paths.public_prefix));
    assert.ok(prefix === "" || paths.public_prefix === prefix);
    assert.equal(paths.effective_prefix, prefix);
    assert.equal(paths.ui_base, prefix + "/ui/");
    assert.equal(paths.bootstrap, prefix + "/ui/bootstrap.json");
    assert.equal(paths.api_base, prefix + "/api/v1");
    assert.equal(paths.mcp_base, prefix + "/mcp/");
}

export async function browserRead(page, endpoint, headers = {}) {
    const origin = new URL(page.url()).origin;
    assert.ok(endpoint.startsWith("/") && !endpoint.startsWith("//"));
    const target = new URL(endpoint, origin);
    assert.equal(target.origin, origin);
    assert.equal(target.username + target.password + target.hash, "");
    assert.ok(
        !Object.keys(headers).some((name) =>
            /^(authorization|cookie|origin)$/iu.test(name),
        ),
    );
    return await page.evaluate(
        async ({ endpoint, headers, maximum }) => {
            const controller = new globalThis.AbortController();
            const timer = setTimeout(() => controller.abort(), 15000);
            try {
                const response = await fetch(endpoint, {
                    credentials: "same-origin",
                    cache: "no-store",
                    redirect: "error",
                    referrerPolicy: "no-referrer",
                    headers,
                    signal: controller.signal,
                });
                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8", { fatal: true });
                let bytes = 0,
                    text = "";
                while (true) {
                    const part = await reader.read();
                    if (part.done) break;
                    bytes += part.value.byteLength;
                    assertBound(bytes <= maximum);
                    text += decoder.decode(part.value, { stream: true });
                }
                return {
                    status: response.status,
                    headers: Object.fromEntries(response.headers),
                    text: text + decoder.decode(),
                };
            } finally {
                clearTimeout(timer);
                controller.abort();
            }
            function assertBound(valid) {
                if (!valid)
                    throw new Error("Owned read exceeds response bound.");
            }
        },
        { endpoint, headers, maximum: MAX_BODY },
    );
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
    {
        ca,
        method = "GET",
        token,
        body,
        agent,
        authorization,
        maximumResponseBytes = MAX_BODY,
    } = {},
) {
    assert.equal(endpoint.hostname, "127.0.0.1");
    assert.equal(endpoint.username + endpoint.password, "");
    assert.ok(["https:", "http:"].includes(endpoint.protocol));
    if (endpoint.protocol === "http:")
        assert.ok(
            token === undefined &&
                authorization === undefined &&
                body === undefined &&
                method === "GET",
        );
    assert.ok(
        Number.isSafeInteger(maximumResponseBytes) &&
            maximumResponseBytes > 0 &&
            maximumResponseBytes <= MAX_BODY,
    );
    if (authorization !== undefined)
        assert.ok(
            method === "GET" && token === undefined && body === undefined,
        );
    const data =
        body === undefined ? undefined : Buffer.from(JSON.stringify(body));
    assert.ok(data === undefined || data.byteLength <= 65536);
    return await new Promise((resolve, reject) => {
        const headers =
            authorization === undefined
                ? { "User-Agent": agent ?? "hfcache-functional-node" }
                : basicReadHeaders(endpoint, authorization, agent);
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
                    if (size > maximumResponseBytes) {
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

/** Tag provenance and bounds use separate real UI intents under the existing callback deadline. */
export const TAG_FILTER_ASSERTIONS = [
    "library-tags-default-corpus",
    "library-tags-canonical-all",
    "library-tags-all-and-missing",
    "library-tags-clear-after-all",
    "library-tags-any",
    "library-tags-groups-combine-with-and",
    "library-tags-clear-before-observed",
    "library-tags-last-observed",
    "library-tags-current-only-withholds-old",
    "library-tags-clear-before-unpublished",
    "library-tags-disabled-unpublished",
    "library-tags-clear-before-count-bound",
    "library-tags-64-accepted",
    "library-tags-65-refused",
    "library-tags-restore-valid-count",
    "library-tags-64-canonical-128-raw",
    "library-tags-65-canonical-refused",
    "library-tags-129-raw-refused",
    "library-tags-restore-default",
];
export async function libraryTagProvenanceSplit({
    page,
    bindings,
    evidence,
    test,
}) {
    const prefix = bindings.prefix,
        ui = prefix + "/ui/",
        api = prefix + "/api/v1";
    assert.deepEqual(bindings.mcp_arguments.get_current_reference, {
        repository_type: "model",
        repository_id: "fixture/model",
    });
    assert(["application", "native", "rootless"].includes(bindings.profile));
    assert(["", "/management"].includes(prefix));
    const result = {
        steps: [],
        queries: [],
        catalogSearchRequests: [],
        invalidClientRefusals: [],
        non_get: [],
        fullOriginalTagGroupPassed: false,
    };
    evidence.library_tag_provenance_split = result;
    const observe = (request) => {
        const url = new URL(request.url());
        if (!["GET", "HEAD"].includes(request.method()))
            result.non_get.push({
                method: request.method(),
                path: url.pathname,
            });
        if (
            url.origin === bindings.origin &&
            url.pathname === api + "/catalog/search"
        )
            result.catalogSearchRequests.push({
                method: request.method(),
                url: request.url(),
                caseId: evidence.cases.at(-1)?.id ?? "startup",
            });
    };
    page.on("request", observe);
    const filters = page.getByRole("form", {
            name: "Library filters",
            exact: true,
        }),
        clear = () =>
            filters
                .getByRole("button", { name: "Clear filters", exact: true })
                .click(),
        apply = () =>
            filters
                .getByRole("button", { name: "Apply filters", exact: true })
                .click();
    const repoPath = (entry) =>
        ui +
        "repositories/" +
        entry.repository_type +
        "/" +
        entry.repository_id;
    let archiveId,
        all,
        matching,
        observed,
        currentOnly,
        unpublished,
        previous,
        validAddress;
    const absent = "browser-absent-tag",
        lastTag = "browser-last-observed",
        atLimit = Array.from(
            { length: 64 },
            (_, index) => "browser-bound-" + index,
        ),
        tag64 = "b".repeat(64);
    async function read(route) {
        const response = await browserRead(page, api + route);
        assert.equal(response.status, 200);
        assertApiHeaders(response.headers);
        const body = JSON.parse(response.text);
        assert.equal(body.archive_id, archiveId);
        return { wire: body, value: envelope(body) };
    }
    async function search(values = {}) {
        const query = new URLSearchParams();
        for (const [key, value] of Object.entries({
            scope: "all",
            revision_scope: "current",
            tag_source: "current_or_last_observed",
            limit: 100,
            ...values,
        }))
            for (const item of Array.isArray(value) ? value : [value])
                query.append(key, String(item));
        const response = await read("/catalog/search?" + query);
        assert(Number.isSafeInteger(response.value.total_matches));
        assert(response.value.entries.length <= 100);
        return response;
    }
    async function choose(label, option) {
        if (label !== "Repository scope")
            await openLibraryDisclosure(page, "Filters and page size");
        await filters
            .getByRole("button", { name: new RegExp("^" + label + ": ", "u") })
            .click();
        await filters
            .getByRole("listbox", { name: label, exact: true })
            .getByRole("option", { name: option, exact: true })
            .click();
    }
    async function rows(label, expected, action, values = null) {
        let responsePromise, requestPromise, identity;
        if (values !== null) {
            const query = new URLSearchParams();
            for (const [key, value] of Object.entries({
                scope: "all",
                revision_scope: "current",
                tag_source: "current_or_last_observed",
                limit: 25,
                ...values,
            }))
                for (const item of Array.isArray(value) ? value : [value])
                    query.append(key, String(item));
            identity = JSON.stringify([...query].sort());
            const matches = (request) => {
                const url = new URL(request.url());
                return (
                    request.method() === "GET" &&
                    url.origin === bindings.origin &&
                    url.pathname === api + "/catalog/search" &&
                    JSON.stringify([...url.searchParams].sort()) === identity
                );
            };
            requestPromise = page.waitForRequest(matches, { timeout: 35000 });
            responsePromise = page.waitForResponse(
                async (response) =>
                    matches(response.request()) &&
                    response.request() === (await requestPromise),
                { timeout: 35000 },
            );
        }
        await action();
        if (responsePromise) {
            const [request, response] = await Promise.all([
                requestPromise,
                responsePromise,
            ]);
            assert.equal(response.request(), request);
            assert.equal(response.status(), 200);
            await page.waitForFunction(
                ({ identity, path }) =>
                    globalThis.location.pathname === path &&
                    JSON.stringify(
                        [
                            ...new URLSearchParams(
                                globalThis.location.hash.slice(1),
                            ),
                        ].sort(),
                    ) === identity &&
                    ![...document.querySelectorAll('[role="status"]')].some(
                        (node) =>
                            node.textContent.includes("Updating the Library."),
                    ),
                { identity, path: ui + "library" },
            );
        }
        const hrefs = expected.entries
            .slice(0, 25)
            .map((entry) => repoPath(entry) + "#tab=overview");
        await page.waitForFunction(
            ({ ui, hrefs, total, publications }) => {
                const knownMatches = document
                        .querySelector(
                            '[aria-label="Library read scope"] > p > strong',
                        )
                        ?.textContent.trim(),
                    scopedPublications = [
                        ...document.querySelectorAll(
                            ".library .coverage-facts dt",
                        ),
                    ]
                        .filter(
                            (node) =>
                                node.textContent.trim() ===
                                "Scoped publications",
                        )
                        .map((node) =>
                            node.nextElementSibling?.textContent.trim(),
                        ),
                    rows = [
                        ...document.querySelectorAll(".library-table tbody tr"),
                    ],
                    links = [
                        ...document.querySelectorAll(".library-table tbody a"),
                    ]
                        .map((node) => node.getAttribute("href"))
                        .filter(
                            (value) =>
                                value?.startsWith(ui + "repositories/") &&
                                value.endsWith("#tab=overview"),
                        );
                return (
                    knownMatches ===
                        "Known matching repositories: " +
                            total.toLocaleString("en-US") &&
                    scopedPublications.length === 1 &&
                    scopedPublications[0] ===
                        publications.toLocaleString("en-US") &&
                    rows.length === hrefs.length &&
                    JSON.stringify(links) === JSON.stringify(hrefs)
                );
            },
            {
                ui,
                hrefs,
                total: expected.total_matches,
                publications: expected.coverage.publications,
            },
        );
        result.queries.push({
            label,
            total_matches: expected.total_matches,
            page_rows: hrefs.length,
            canonical_hrefs: hrefs,
            coverage: expected.coverage,
            actualHash: new URL(page.url()).hash,
            ...(identity
                ? {
                      actualQueryAndHttp200Joined: true,
                      bodyCompletionClaimed: false,
                  }
                : {}),
        });
    }
    async function step(id, operation) {
        await test(id, operation);
        assert.equal(evidence.cases.at(-1)?.id, id);
        assert.equal(
            evidence.cases.at(-1)?.passed,
            true,
            "Stop after failed real tag assertion",
        );
        result.steps.push(id);
    }
    async function invalid(value, address) {
        const before = result.catalogSearchRequests.length,
            caseId = evidence.cases.at(-1)?.id;
        await filters
            .getByLabel("Require all tags", { exact: true })
            .fill(value);
        await apply();
        await page
            .getByText(
                "These filters are invalid or exceed the supported bounds. The last valid filters remain in effect.",
                { exact: true },
            )
            .waitFor();
        assert.equal(page.url(), address);
        const initiated = result.catalogSearchRequests.slice(before);
        result.invalidClientRefusals.push({
            caseId,
            rawLength: value.length,
            unchangedUrl: page.url(),
            catalogSearchRequestsInitiated: initiated,
        });
        assert.deepEqual(
            initiated,
            [],
            "Invalid tag input must be refused by the UI without initiating catalog/search",
        );
    }
    try {
        await step(TAG_FILTER_ASSERTIONS[0], async () => {
            const bootstrap = JSON.parse(
                (await browserRead(page, ui + "bootstrap.json")).text,
            );
            assert.equal(bootstrap.configured_origin, bindings.origin);
            assertBootstrapPaths(bootstrap.paths, prefix);
            assert.equal(
                bootstrap.build.asset_manifest_sha256,
                bindings.asset_manifest_sha256,
            );
            assert.deepEqual(
                bootstrap.build.metadata,
                bindings.asset_manifest.build,
            );
            archiveId = bootstrap.configured_archive_id;
            assert.match(
                archiveId,
                /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u,
            );
            all = (await search()).value;
            assert(
                all.total_matches > 25 &&
                    all.entries.length === all.total_matches,
            );
            assert(!all.entries.some((entry) => entry.tags.includes(absent)));
            assert(
                all.entries.some(
                    (entry) =>
                        entry.configured &&
                        !entry.archived &&
                        entry.enabled === false,
                ),
            );
            await rows("default-current-scope", all, async () => {});
            await openLibraryDisclosure(page, "Filters and page size");
        });
        await step(TAG_FILTER_ASSERTIONS[1], async () => {
            matching = (await search({ tag_all: ["functional"] })).value;
            await rows(
                "canonical-all-tags",
                matching,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill(" FUNCTIONAL, functional ");
                    await apply();
                },
                { tag_all: ["functional"] },
            );
            assert.deepEqual(
                new URLSearchParams(new URL(page.url()).hash.slice(1)).getAll(
                    "tag_all",
                ),
                ["functional"],
            );
        });
        await step(TAG_FILTER_ASSERTIONS[2], async () => {
            await rows(
                "all-and-missing",
                (await search({ tag_all: ["functional", absent] })).value,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill("functional," + absent);
                    await apply();
                },
                { tag_all: ["functional", absent] },
            );
        });
        await step(TAG_FILTER_ASSERTIONS[3], () =>
            rows("clear", all, clear, {}),
        );
        await step(TAG_FILTER_ASSERTIONS[4], async () => {
            await rows(
                "any-tags",
                (await search({ tag_any: ["functional", absent] })).value,
                async () => {
                    await filters
                        .getByLabel("Match any tags", { exact: true })
                        .fill("functional," + absent);
                    await apply();
                },
                { tag_any: ["functional", absent] },
            );
        });
        await step(TAG_FILTER_ASSERTIONS[5], async () => {
            await rows(
                "groups-combine-with-and",
                (await search({ tag_all: ["functional"], tag_any: [absent] }))
                    .value,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill("functional");
                    await filters
                        .getByLabel("Match any tags", { exact: true })
                        .fill(absent);
                    await apply();
                },
                { tag_all: ["functional"], tag_any: [absent] },
            );
        });
        await step(TAG_FILTER_ASSERTIONS[6], () =>
            rows("clear", all, clear, {}),
        );
        await step(TAG_FILTER_ASSERTIONS[7], async () => {
            observed = (await search({ tag_all: [lastTag] })).value;
            assert(
                observed.entries.length > 0 &&
                    observed.entries.every(
                        (entry) =>
                            !entry.configured &&
                            entry.tag_origin === "last_observed",
                    ),
            );
            await rows(
                "last-observed",
                observed,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill(lastTag);
                    await apply();
                },
                { tag_all: [lastTag] },
            );
            await page
                .locator(".library-table tbody tr")
                .getByText("Last-observed tags", { exact: true })
                .waitFor();
            for (const label of [
                "Unmanaged archive",
                "Outside current configuration",
            ])
                await page
                    .locator(".library-table tbody tr")
                    .getByText(label, { exact: true })
                    .waitFor();
        });
        await step(TAG_FILTER_ASSERTIONS[8], async () => {
            currentOnly = (
                await search({ tag_all: [lastTag], tag_source: "current_only" })
            ).value;
            assert.equal(currentOnly.total_matches, 0);
            await rows(
                "current-only-withholds-old-tag",
                currentOnly,
                () => choose("Tag provenance", "Current configuration only"),
                { tag_all: [lastTag], tag_source: "current_only" },
            );
        });
        await step(TAG_FILTER_ASSERTIONS[9], () =>
            rows("clear", all, clear, {}),
        );
        await step(TAG_FILTER_ASSERTIONS[10], async () => {
            unpublished = all.entries.find(
                (entry) =>
                    entry.configured &&
                    !entry.archived &&
                    entry.enabled === false,
            );
            await rows(
                "disabled-unpublished",
                (await search({ q: unpublished.repository_id })).value,
                () =>
                    filters
                        .getByLabel("Find repositories", { exact: true })
                        .fill(unpublished.repository_id),
                { q: unpublished.repository_id },
            );
            const row = page.locator(".library-table tbody tr");
            for (const label of [
                "Not archived",
                "Sync disabled",
                "No current snapshot",
            ])
                await row.getByText(label, { exact: true }).waitFor();
        });
        await step(TAG_FILTER_ASSERTIONS[11], () =>
            rows("clear", all, clear, {}),
        );
        await step(TAG_FILTER_ASSERTIONS[12], async () => {
            await rows(
                "64-tags-accepted",
                (await search({ tag_all: atLimit })).value,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill(atLimit.join(","));
                    await apply();
                },
                { tag_all: atLimit },
            );
            previous = page.url();
        });
        await step(TAG_FILTER_ASSERTIONS[13], () =>
            invalid([...atLimit, "browser-bound-over"].join(","), previous),
        );
        await step(TAG_FILTER_ASSERTIONS[14], () =>
            rows("restore-valid", all, clear, {}),
        );
        await step(TAG_FILTER_ASSERTIONS[15], async () => {
            await rows(
                "64-canonical-128-raw",
                (await search({ tag_all: [tag64] })).value,
                async () => {
                    await filters
                        .getByLabel("Require all tags", { exact: true })
                        .fill(" ".repeat(64) + tag64);
                    await apply();
                },
                { tag_all: [tag64] },
            );
            validAddress = page.url();
        });
        await step(TAG_FILTER_ASSERTIONS[16], () =>
            invalid("b".repeat(65), validAddress),
        );
        await step(TAG_FILTER_ASSERTIONS[17], () =>
            invalid(" ".repeat(65) + tag64, validAddress),
        );
        await step(TAG_FILTER_ASSERTIONS[18], () =>
            rows("restore-default", all, clear, {}),
        );
        assert.deepEqual(result.steps, TAG_FILTER_ASSERTIONS);
        assert.equal(result.invalidClientRefusals.length, 3);
        assert(
            result.invalidClientRefusals.every(
                (row) => row.catalogSearchRequestsInitiated.length === 0,
            ),
        );
        assert.deepEqual(result.non_get, []);
        result.fullOriginalTagGroupPassed = true;
        return result;
    } finally {
        page.off("request", observe);
    }
}

export const TECHNICAL_FILTER_ASSERTIONS = [
    "library-technical-primary-GGUF-all-predicates",
    "library-technical-one-byte-below-excludes-GGUF",
    "library-technical-primary-GPTQ-same-variant",
    "library-technical-cross-variant-format-method-bits",
    "library-technical-cross-variant-scheme-bits",
    "library-technical-adapter-excluded",
    "library-technical-projector-excluded",
    "library-technical-unknown-role-excluded",
    "library-technical-incomplete-members-excluded",
];

/** Actual controls use independently checked source variants, never query-derived expectations. */
export async function libraryTechnicalFilterCases({
    page,
    bindings,
    evidence,
    test,
    source,
}) {
    const prefix = bindings.prefix,
        api = prefix + "/api/v1",
        ui = prefix + "/ui/";
    const repositoryId =
        bindings.mcp_arguments.get_current_reference.repository_id;
    assert.equal(repositoryId, "fixture/model");
    assert.equal(source.manifest.file_count, 8);
    assert.equal(source.manifest.total_bytes, 6777);
    assert.equal(source.variants.length, 6);
    const byPath = (
        path,
        role,
        completeness,
        format,
        method,
        scheme,
        bits,
        size,
    ) => {
        const found = source.variants.filter((entry) =>
            entry.variant.source_paths.includes(path),
        );
        assert.equal(found.length, 1);
        const entry = found[0],
            variant = entry.variant;
        assert.equal(entry.commit_sha, source.pair.commit_sha);
        assert.equal(entry.publication_id, source.pair.publication_id);
        assert.deepEqual(
            [
                variant.role,
                variant.completeness,
                variant.format,
                variant.quantization_method,
                variant.quantization,
                variant.bits,
                variant.total_bytes,
            ],
            [role, completeness, format, method, scheme, bits, size],
        );
        return variant;
    };
    const gguf = byPath(
        "primary-q4.gguf",
        "primary",
        "complete",
        "gguf",
        "ggml",
        "Q4_0",
        4,
        1184,
    );
    const gptq = byPath(
        "gptq/config.json",
        "primary",
        "complete",
        "safetensors",
        "gptq",
        null,
        8,
        84,
    );
    byPath(
        "adapter-q8.gguf",
        "adapter",
        "complete",
        "gguf",
        "ggml",
        "Q8_0",
        8,
        1216,
    );
    byPath(
        "mmproj-q4.gguf",
        "projector",
        "complete",
        "gguf",
        "ggml",
        "Q4_1",
        4,
        1216,
    );
    byPath(
        "future-q5.gguf",
        "unknown",
        "complete",
        "gguf",
        "ggml",
        "Q5_0",
        5,
        1184,
    );
    byPath(
        "split-q2-00001-of-00002.gguf",
        "primary",
        "incomplete",
        "gguf",
        "ggml",
        "Q2_K",
        null,
        1248,
    );
    const result = {
        source: {
            pair: source.pair,
            manifest: source.manifest,
            variants: source.variants,
        },
        queries: [],
    };
    evidence.library_technical_filters = result;
    const queries = [
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q4_0",
                bits: 4,
                max_variant_bytes: 1184,
            },
            1,
            gguf,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q4_0",
                bits: 4,
                max_variant_bytes: 1183,
            },
            0,
        ],
        [
            {
                format: "safetensors",
                quantization_method: "gptq",
                bits: 8,
                max_variant_bytes: 84,
            },
            1,
            gptq,
        ],
        [
            {
                format: "gguf",
                quantization_method: "gptq",
                bits: 8,
                max_variant_bytes: 1184,
            },
            0,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q4_0",
                bits: 8,
            },
            0,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q8_0",
            },
            0,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q4_1",
            },
            0,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q5_0",
            },
            0,
        ],
        [
            {
                format: "gguf",
                quantization_method: "ggml",
                quantization: "Q2_K",
            },
            0,
        ],
    ];
    const fields = {
        format: "Format",
        quantization_method: "Quantization method",
        quantization: "Quantization scheme",
        bits: "Bits",
        max_variant_bytes: "Maximum variant bytes",
    };
    for (const [index, [values, total, variant]] of queries.entries()) {
        const id = TECHNICAL_FILTER_ASSERTIONS[index];
        await test(id, async () => {
            if (index === 0) {
                await page
                    .getByRole("navigation", {
                        name: "Main navigation",
                        exact: true,
                    })
                    .getByRole("link", { name: "Library", exact: true })
                    .click();
                await page
                    .getByRole("heading", { name: "Library", exact: true })
                    .waitFor();
                await page
                    .getByRole("button", { name: "Clear filters", exact: true })
                    .click();
                await page
                    .getByRole("group", {
                        name: "Repository type",
                        exact: true,
                    })
                    .getByRole("button", { name: "Models", exact: true })
                    .click();
                await page
                    .getByLabel("Find repositories", { exact: true })
                    .fill(repositoryId);
            }
            const filters = page.getByRole("form", {
                name: "Library filters",
                exact: true,
            });
            await openLibraryDisclosure(page, "Filters and page size");
            for (const [key, label] of Object.entries(fields))
                await filters
                    .getByLabel(label, { exact: true })
                    .fill(values[key] === undefined ? "" : String(values[key]));
            const query = new URLSearchParams(
                Object.fromEntries(
                    Object.entries({
                        scope: "all",
                        revision_scope: "current",
                        tag_source: "current_or_last_observed",
                        limit: 25,
                        q: repositoryId,
                        type: "model",
                        ...values,
                    }).map(([key, value]) => [key, String(value)]),
                ),
            );
            const identity = JSON.stringify([...query].sort());
            const matches = (request) => {
                const url = new URL(request.url());
                return (
                    request.method() === "GET" &&
                    url.origin === bindings.origin &&
                    url.pathname === api + "/catalog/search" &&
                    JSON.stringify([...url.searchParams].sort()) === identity
                );
            };
            const request = page.waitForRequest(matches, { timeout: 35000 });
            const response = page.waitForResponse(
                async (row) =>
                    matches(row.request()) && row.request() === (await request),
                { timeout: 35000 },
            );
            await filters
                .getByRole("button", { name: "Apply filters", exact: true })
                .click();
            const [sent, received] = await Promise.all([request, response]);
            assert.equal(received.request(), sent);
            assert.equal(received.status(), 200);
            await page.waitForFunction(
                ({ identity, total, path }) =>
                    globalThis.location.pathname === path &&
                    JSON.stringify(
                        [
                            ...new URLSearchParams(
                                globalThis.location.hash.slice(1),
                            ),
                        ].sort(),
                    ) === identity &&
                    ![...document.querySelectorAll('[role="status"]')].some(
                        (node) =>
                            node.textContent.includes("Updating the Library."),
                    ) &&
                    document
                        .querySelector(
                            '[aria-label="Library read scope"] > p > strong',
                        )
                        ?.textContent.trim() ===
                        "Known matching repositories: " +
                            total.toLocaleString("en-US") &&
                    document.querySelectorAll(".library-table tbody tr")
                        .length === total,
                { identity, total, path: ui + "library" },
            );
            const hrefs = await page
                .locator(".library-table tbody a")
                .evaluateAll((nodes) =>
                    nodes
                        .map((node) => node.getAttribute("href"))
                        .filter((value) => value?.endsWith("#tab=overview")),
                );
            assert.deepEqual(
                hrefs,
                total
                    ? [
                          ui +
                              "repositories/model/" +
                              repositoryId +
                              "#tab=overview",
                      ]
                    : [],
            );
            if (variant) {
                const row = page.locator(".library-table tbody tr");
                await row
                    .getByText("1 matching variants", { exact: true })
                    .waitFor();
                await row
                    .getByText(
                        [
                            variant.quantization_method,
                            variant.quantization,
                            String(variant.bits) + "-bit declaration",
                        ]
                            .filter((value) => value !== null)
                            .join(" · "),
                        { exact: true },
                    )
                    .waitFor();
                const matching = row.getByText("Matching variant publication", {
                    exact: true,
                });
                await matching.click();
                const details = matching.locator("..");
                await details
                    .getByText(source.pair.commit_sha, { exact: true })
                    .waitFor();
                assert.deepEqual(
                    await details.locator("code").allTextContents(),
                    [source.pair.commit_sha, source.pair.publication_id],
                );
            }
            result.queries.push({
                id,
                values,
                expectedMatches: total,
                expectedVariantId: variant?.variant_id ?? null,
                queryIdentity: identity,
                matchingHttpStatus: received.status(),
                settledHash: new URL(page.url()).hash,
                bodyCompletionClaimed: false,
            });
        });
        assert.equal(evidence.cases.at(-1)?.id, id);
        assert.equal(
            evidence.cases.at(-1)?.passed,
            true,
            "Stop after failed real technical filter assertion",
        );
    }
}

/** Existing-driver read cases for the explicitly constructed browser_reads corpus.
 * No capture, fixture mutation, synthetic response, credential injection or replay.
 */
export async function libraryPublicationReadCases({
    page,
    bindings,
    evidence,
    test,
}) {
    const prefix = bindings.prefix,
        ui = prefix + "/ui/",
        api = prefix + "/api/v1";
    const model = bindings.mcp_arguments.get_current_reference;
    assert.deepEqual(model, {
        repository_type: "model",
        repository_id: "fixture/model",
    });
    assert.ok(["application", "native", "rootless"].includes(bindings.profile));
    assert.ok(["", "/management"].includes(prefix));
    let archiveId;
    const result = {
        steps: [],
        queries: [],
        publications: [],
        card_states: [],
        non_get: [],
    };
    evidence.library_publication_reads = result;
    const observe = (request) => {
        if (!["GET", "HEAD"].includes(request.method()))
            result.non_get.push({
                method: request.method(),
                path: new URL(request.url()).pathname,
            });
    };
    page.on("request", observe);
    const filters = page.getByRole("form", {
        name: "Library filters",
        exact: true,
    });
    const types = page.getByRole("group", {
        name: "Repository type",
        exact: true,
    });
    const clear = () =>
        filters
            .getByRole("button", { name: "Clear filters", exact: true })
            .click();
    const repoPath = (entry) =>
        ui +
        "repositories/" +
        entry.repository_type +
        "/" +
        entry.repository_id;
    async function read(route) {
        const response = await browserRead(page, api + route);
        assert.equal(response.status, 200);
        assertApiHeaders(response.headers);
        const body = JSON.parse(response.text);
        assert.equal(body.archive_id, archiveId);
        return { wire: body, value: envelope(body) };
    }
    async function search(values = {}) {
        const query = new URLSearchParams();
        for (const [key, value] of Object.entries({
            scope: "all",
            revision_scope: "current",
            tag_source: "current_or_last_observed",
            limit: 100,
            ...values,
        }))
            for (const item of Array.isArray(value) ? value : [value])
                query.append(key, String(item));
        const response = await read("/catalog/search?" + query);
        assert(Number.isSafeInteger(response.value.total_matches));
        assert(response.value.entries.length <= 100);
        return response;
    }
    async function choose(label, option) {
        if (label !== "Repository scope")
            await openLibraryDisclosure(page, "Filters and page size");
        await filters
            .getByRole("button", { name: new RegExp("^" + label + ": ", "u") })
            .click();
        await filters
            .getByRole("listbox", { name: label, exact: true })
            .getByRole("option", { name: option, exact: true })
            .click();
    }
    async function rows(label, expected, action) {
        await action();
        const hrefs = expected.entries
            .slice(0, 25)
            .map((entry) => repoPath(entry) + "#tab=overview");
        await page.waitForFunction(
            ({ ui, hrefs, total, publications }) => {
                const knownMatches = document
                    .querySelector(
                        '[aria-label="Library read scope"] > p > strong',
                    )
                    ?.textContent.trim();
                const scopedPublications = [
                    ...document.querySelectorAll(".library .coverage-facts dt"),
                ]
                    .filter(
                        (node) =>
                            node.textContent.trim() === "Scoped publications",
                    )
                    .map((node) => node.nextElementSibling?.textContent.trim());
                const rows = [
                    ...document.querySelectorAll(".library-table tbody tr"),
                ];
                const links = [
                    ...document.querySelectorAll(".library-table tbody a"),
                ]
                    .map((node) => node.getAttribute("href"))
                    .filter(
                        (value) =>
                            value?.startsWith(ui + "repositories/") &&
                            value.endsWith("#tab=overview"),
                    );
                return (
                    knownMatches ===
                        "Known matching repositories: " +
                            total.toLocaleString("en-US") &&
                    scopedPublications.length === 1 &&
                    scopedPublications[0] ===
                        publications.toLocaleString("en-US") &&
                    rows.length === hrefs.length &&
                    JSON.stringify(links) === JSON.stringify(hrefs)
                );
            },
            {
                ui,
                hrefs,
                total: expected.total_matches,
                publications: expected.coverage.publications,
            },
        );
        result.queries.push({
            label,
            total_matches: expected.total_matches,
            page_rows: hrefs.length,
            canonical_hrefs: hrefs,
            coverage: expected.coverage,
        });
    }
    async function fact(region, label, expected) {
        const values = await region
            .locator("dl dt")
            .evaluateAll(
                (nodes, name) =>
                    nodes
                        .filter((node) => node.textContent.trim() === name)
                        .map((node) =>
                            node.nextElementSibling.textContent.trim(),
                        ),
                label,
            );
        assert.deepEqual(values, [String(expected)], label);
    }
    async function step(id, operation) {
        await test(id, operation);
        assert.equal(evidence.cases.at(-1)?.id, id);
        assert.equal(
            evidence.cases.at(-1)?.passed,
            true,
            "Stop after a failed real read assertion",
        );
        result.steps.push(id);
    }
    let all, retained, selectedModel, selectedDataset, cards;
    try {
        await step("library-type-and-repository-scopes", async () => {
            const bootstrap = JSON.parse(
                (await browserRead(page, ui + "bootstrap.json")).text,
            );
            assert.equal(bootstrap.configured_origin, bindings.origin);
            assertBootstrapPaths(bootstrap.paths, prefix);
            assert.equal(
                bootstrap.build.asset_manifest_sha256,
                bindings.asset_manifest_sha256,
            );
            assert.deepEqual(
                bootstrap.build.metadata,
                bindings.asset_manifest.build,
            );
            archiveId = bootstrap.configured_archive_id;
            assert.match(
                archiveId,
                /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u,
            );
            all = (await search()).value;
            assert(
                all.total_matches > 25 &&
                    all.entries.length === all.total_matches,
                "The declared corpus needs >25 bounded repositories",
            );
            assert(
                all.entries.some(
                    (entry) =>
                        entry.configured &&
                        !entry.archived &&
                        entry.enabled === false,
                ),
            );
            assert(
                all.entries.some(
                    (entry) => !entry.configured && entry.archived,
                ),
            );
            assert.equal(
                (await page.goto(bindings.origin + ui + "library")).status(),
                200,
            );
            await rows("all", all, clear);
            for (const [label, type] of [
                ["Models", "model"],
                ["Datasets", "dataset"],
            ]) {
                const expected = (await search({ type })).value;
                assert(
                    expected.entries.every(
                        (entry) => entry.repository_type === type,
                    ),
                );
                await rows(type, expected, () =>
                    types
                        .getByRole("button", { name: label, exact: true })
                        .click(),
                );
                for (const field of [
                    "Quantization method",
                    "Quantization scheme",
                    "Bits",
                ])
                    assert.equal(
                        await filters
                            .getByLabel(field, { exact: true })
                            .isDisabled(),
                        type === "dataset",
                    );
            }
            await rows("all-types", all, () =>
                types
                    .getByRole("button", {
                        name: "All repositories",
                        exact: true,
                    })
                    .click(),
            );
            for (const [value, label] of [
                ["configured", "Configured"],
                ["archived", "Archived"],
                ["all", "All: archived and configured"],
            ]) {
                const expected = (await search({ scope: value })).value;
                assert.deepEqual(
                    expected.entries.map(
                        (entry) =>
                            entry.repository_type + ":" + entry.repository_id,
                    ),
                    all.entries
                        .filter((entry) => value === "all" || entry[value])
                        .map(
                            (entry) =>
                                entry.repository_type +
                                ":" +
                                entry.repository_id,
                        ),
                );
                await rows(value, expected, () =>
                    choose("Repository scope", label),
                );
            }
        });
        await step("library-literal-id-tag-not-readme", async () => {
            await rows("clear", all, clear);
            const byId = (await search({ q: model.repository_id })).value;
            assert.deepEqual(
                byId.entries.map((entry) => entry.repository_id),
                [model.repository_id],
            );
            await rows("literal-id", byId, () =>
                filters
                    .getByLabel("Find repositories", { exact: true })
                    .fill(model.repository_id),
            );
            await rows("clear", all, clear);
            const byTag = (await search({ q: "functional" })).value;
            assert(
                byTag.entries.length > 0 &&
                    byTag.entries.every((entry) =>
                        entry.tags.includes("functional"),
                    ),
            );
            await rows("literal-tag", byTag, () =>
                filters
                    .getByLabel("Find repositories", { exact: true })
                    .fill("functional"),
            );
            await rows("clear", all, clear);
            const prose = (await search({ q: "Owned browser read corpus" }))
                .value;
            assert.equal(
                prose.total_matches,
                0,
                "README prose is not the local ID/tag index",
            );
            await rows("no-readme-fulltext", prose, () =>
                filters
                    .getByLabel("Find repositories", { exact: true })
                    .fill("Owned browser read corpus"),
            );
            await rows("clear", all, clear);
            const literalPattern = (await search({ q: ".*" })).value;
            assert.equal(literalPattern.total_matches, 0);
            await rows("regexp-text-is-literal", literalPattern, () =>
                filters
                    .getByLabel("Find repositories", { exact: true })
                    .fill(".*"),
            );
            await rows("restore-all", all, clear);
        });
        await step("library-current-and-retained-publications", async () => {
            retained = (await search({ revision_scope: "retained" })).value;
            assert(retained.coverage.publications > all.coverage.publications);
            await rows("retained", retained, () =>
                choose("Publication scope", "Retained publications"),
            );
            await page
                .getByRole("group", { name: "Library read scope", exact: true })
                .getByText(/Retained publication evidence\./u)
                .waitFor();
            await rows("current", all, () =>
                choose("Publication scope", "Current publications"),
            );
            await page
                .getByRole("group", { name: "Library read scope", exact: true })
                .getByText(/Current publication evidence\./u)
                .waitFor();
        });
        await libraryTagProvenanceSplit({
            page,
            bindings,
            evidence,
            test: step,
        });
        await step("library-total-page-coverage-and-zero", async () => {
            const first = await search({ limit: 25 });
            assert(first.wire.next_cursor);
            assert(first.value.total_matches > first.value.entries.length);
            await rows("first-page", first.value, clear);
            const next = await search({
                limit: 25,
                cursor: first.wire.next_cursor,
            });
            assert(next.value.entries.length > 0);
            await rows("second-page", next.value, () =>
                page
                    .getByRole("button", { name: "Next page", exact: true })
                    .click(),
            );
            assert.equal(next.value.total_matches, first.value.total_matches);
            assert(
                !next.value.entries.some((entry) =>
                    first.value.entries.some(
                        (old) =>
                            old.repository_type === entry.repository_type &&
                            old.repository_id === entry.repository_id,
                    ),
                ),
            );
            await rows("first-page-restored", first.value, () =>
                page
                    .getByRole("button", { name: "Previous page", exact: true })
                    .click(),
            );
            assert(
                retained.coverage.partial > 0 &&
                    retained.coverage.unsupported > 0 &&
                    retained.coverage.missing > 0,
            );
            await rows("retained-coverage", retained, () =>
                choose("Publication scope", "Retained publications"),
            );
            await openLibraryDisclosure(page, "Scope and coverage");
            const coverage = page.getByRole("region", {
                name: "Know your coverage",
                exact: true,
            });
            for (const [label, key] of [
                ["Partial observations", "partial"],
                ["Unsupported observations", "unsupported"],
                ["Missing observations", "missing"],
            ])
                await fact(
                    coverage,
                    label,
                    retained.coverage[key].toLocaleString("en-US"),
                );
            await page
                .getByRole("region", {
                    name: "Repository library",
                    exact: true,
                })
                .getByText(
                    "Coverage is incomplete. Zero known matches does not prove absence.",
                    { exact: true },
                )
                .waitFor();
            const zero = (
                await search({
                    revision_scope: "retained",
                    q: "browser-no-such-identity",
                })
            ).value;
            assert.equal(zero.total_matches, 0);
            assert.equal(zero.coverage.incomplete, true);
            await rows("zero-known-qualified", zero, () =>
                filters
                    .getByLabel("Find repositories", { exact: true })
                    .fill("browser-no-such-identity"),
            );
            await page
                .getByRole("heading", {
                    name: "No known matches; metadata coverage is incomplete",
                    exact: true,
                })
                .waitFor();
            await rows("restore-all", all, clear);
        });
        async function exact(entry, tab = "overview") {
            const reference = (
                await read(
                    "/repositories/" +
                        entry.repository_type +
                        "/" +
                        entry.repository_id +
                        "/references/current",
                )
            ).value;
            assert.equal(reference.locator_base, "published/");
            const pair = reference.reference,
                manifest = (
                    await read(
                        "/repositories/" +
                            entry.repository_type +
                            "/" +
                            entry.repository_id +
                            "/manifests/" +
                            pair.commit_sha +
                            "/" +
                            pair.publication_id,
                    )
                ).value;
            assert.equal(manifest.tree_base, "archive-root/");
            assert.equal(manifest.manifest.tree, "published/" + pair.tree);
            const target =
                repoPath(entry) +
                "#commit_sha=" +
                pair.commit_sha +
                "&publication_id=" +
                pair.publication_id +
                "&tab=" +
                tab;
            assert.equal(
                (await page.goto(bindings.origin + target)).status(),
                200,
            );
            const selected = page.getByRole("region", {
                name: "Selected publication",
                exact: true,
            });
            await selected.waitFor();
            assert.deepEqual(await selected.locator("code").allTextContents(), [
                pair.commit_sha,
                pair.publication_id,
            ]);
            return { entry, pair, manifest: manifest.manifest, target };
        }
        await step("publication-files-locators-and-history", async () => {
            for (const entry of [
                all.entries.find(
                    (entry) =>
                        entry.repository_type === "model" &&
                        entry.repository_id === model.repository_id,
                ),
                all.entries.find(
                    (entry) =>
                        entry.repository_type === "dataset" &&
                        entry.repository_id === "fixture/data",
                ),
            ]) {
                const item = await exact(entry, "files");
                const panel = page.getByRole("tabpanel", {
                        name: "Files & manifest",
                        exact: true,
                    }),
                    table = panel.getByRole("table", {
                        name: "Manifest files",
                        exact: true,
                    });
                await table.waitFor();
                assert(item.manifest.files.length <= 25);
                assert.equal(
                    await table.locator("tbody tr").count(),
                    item.manifest.file_count,
                );
                for (const file of item.manifest.files) {
                    const row = table
                        .getByRole("rowheader", {
                            name: file.path,
                            exact: true,
                        })
                        .locator("..");
                    assert.equal(
                        (
                            await row.getByRole("cell").first().innerText()
                        ).trim(),
                        file.size.toLocaleString("en-US"),
                    );
                    await row
                        .getByText("Hashes and provenance", { exact: true })
                        .click();
                    await fact(row, "Expected SHA256", file.sha256);
                }
                await fact(
                    panel,
                    "Manifest path (archive-root-relative)",
                    "published/" + item.pair.manifest,
                );
                const sidebar = page.getByRole("complementary", {
                    name: "Selected publication facts",
                    exact: true,
                });
                await fact(
                    sidebar,
                    "Archive-relative tree",
                    item.manifest.tree,
                );
                await fact(sidebar, "Published-relative tree", item.pair.tree);
                const raw = await browserRead(
                    page,
                    prefix +
                        "/published/" +
                        item.pair.tree +
                        "/" +
                        item.manifest.files[0].path,
                );
                assert.equal(raw.status, 404);
                assert.ok(!raw.headers["content-type"]?.includes("text/html"));
                const reload = await page.reload();
                assert.equal(reload.status(), 200);
                await selectedPair(item);
                await page
                    .getByRole("tab", { name: "Overview", exact: true })
                    .click();
                await page.goBack();
                await selectedPair(item);
                await page.goForward();
                await selectedPair(item, "overview");
                const summary = {
                    type: entry.repository_type,
                    id: entry.repository_id,
                    commit_sha: item.pair.commit_sha,
                    publication_id: item.pair.publication_id,
                    manifest_files: item.manifest.file_count,
                    logical_bytes: item.manifest.total_bytes,
                };
                result.publications.push(summary);
                if (entry.repository_type === "model") selectedModel = item;
                else selectedDataset = item;
            }
        });
        async function selectedPair(item, tab = "files") {
            const selected = page.getByRole("region", {
                name: "Selected publication",
                exact: true,
            });
            await selected.waitFor();
            assert.deepEqual(await selected.locator("code").allTextContents(), [
                item.pair.commit_sha,
                item.pair.publication_id,
            ]);
            const query = new URLSearchParams(
                new URL(page.url()).hash.slice(1),
            );
            assert.equal(query.get("commit_sha"), item.pair.commit_sha);
            assert.equal(query.get("publication_id"), item.pair.publication_id);
            assert.equal(query.get("tab"), tab);
            assert.equal(
                await page
                    .getByRole("tab", {
                        name: tab === "files" ? "Files & manifest" : "Overview",
                        exact: true,
                    })
                    .getAttribute("aria-selected"),
                "true",
            );
        }
        await step("publication-model-dataset-static-evidence", async () => {
            for (const item of [selectedModel, selectedDataset]) {
                const query =
                    "?commit_sha=" +
                    item.pair.commit_sha +
                    "&publication_id=" +
                    item.pair.publication_id;
                const detail = (
                    await read(
                        "/catalog/repositories/" +
                            item.entry.repository_type +
                            "/" +
                            item.entry.repository_id +
                            query,
                    )
                ).value;
                assert(
                    detail.observations.some(
                        (observation) => observation.sources.length > 0,
                    ),
                );
                await exact(item.entry, "details");
                if (item.entry.repository_type === "model") {
                    const variants = (
                        await read(
                            "/catalog/repositories/model/" +
                                item.entry.repository_id +
                                "/variants" +
                                query,
                        )
                    ).value;
                    item.variants = variants.entries;
                    assert(
                        variants.entries.some(
                            (entry) =>
                                entry.variant.role === "primary" &&
                                entry.variant.completeness === "complete" &&
                                entry.variant.evidence === "header",
                        ),
                    );
                    for (const entry of variants.entries) {
                        assert.equal(entry.commit_sha, item.pair.commit_sha);
                        assert.equal(
                            entry.publication_id,
                            item.pair.publication_id,
                        );
                        const article = page
                            .locator(".repository-variant")
                            .filter({ hasText: entry.variant.variant_id });
                        await article.waitFor();
                        await fact(article, "Role", entry.variant.role);
                        await fact(
                            article,
                            "Completeness",
                            entry.variant.completeness,
                        );
                        await fact(article, "Evidence", entry.variant.evidence);
                        await article
                            .getByText(
                                "Source paths: " +
                                    entry.variant.source_paths.join(", "),
                                { exact: true },
                            )
                            .waitFor();
                        await fact(
                            article,
                            "Bits",
                            entry.variant.bits === null
                                ? "Not observed"
                                : entry.variant.bits.toLocaleString("en-US"),
                        );
                    }
                    await page
                        .getByText(
                            "All exposed roles and completeness states remain inspectable. These are discovery declarations, not partial download choices or hardware-fit estimates.",
                            { exact: true },
                        )
                        .waitFor();
                } else {
                    assert.equal(detail.entry.representative_variant, null);
                    assert.equal(detail.entry.matching_variant_count, 0);
                    assert.equal(
                        await page.locator(".repository-variant").count(),
                        0,
                    );
                    await page
                        .getByRole("heading", {
                            name: "Dataset declarations",
                            exact: true,
                        })
                        .waitFor();
                    const sources = detail.observations
                        .flatMap((observation) => observation.sources)
                        .filter(
                            (source) =>
                                source.field.startsWith("dataset_") ||
                                source.field === "format",
                        );
                    for (const field of [
                        "dataset_config",
                        "dataset_split",
                        "dataset_feature",
                    ])
                        assert(
                            sources.some(
                                (source) =>
                                    source.field === field &&
                                    source.values.length > 0,
                            ),
                        );
                    const labels = {
                        dataset_config: "Dataset configuration",
                        dataset_split: "Dataset split",
                        dataset_feature: "Dataset feature",
                        format: "Format",
                    };
                    const declarations = page.getByRole("table", {
                        name: "Attributed declarations",
                        exact: true,
                    });
                    await declarations.waitFor();
                    assert.deepEqual(
                        await declarations
                            .locator("tbody th")
                            .allTextContents(),
                        sources.map((source) => labels[source.field]),
                        "Only attributed static declaration fields are shown",
                    );
                    const datasetPanel = page.getByRole("tabpanel", {
                        name: "Dataset details",
                        exact: true,
                    });
                    assert.equal(
                        await datasetPanel
                            .locator(".repository-variant, dl")
                            .count(),
                        0,
                        "Dataset details expose no model or inferred metric facts",
                    );
                    for (const source of sources) {
                        const row = declarations
                            .locator("tbody tr")
                            .filter({ hasText: source.sha256 })
                            .filter({
                                has: page.getByRole("rowheader", {
                                    name: labels[source.field],
                                    exact: true,
                                }),
                            });
                        assert.equal(await row.count(), 1);
                        assert.equal(
                            (
                                await row.getByRole("cell").first().innerText()
                            ).trim(),
                            source.values.join(", ") || "Not observed",
                        );
                        await row
                            .getByText(source.path, { exact: true })
                            .waitFor();
                    }
                    await page
                        .getByText(
                            "Configuration, split, feature and format names are static declarations. No dataset loader or sample is executed; row counts are not inferred.",
                            { exact: true },
                        )
                        .waitFor();
                }
            }
        });
        await libraryTechnicalFilterCases({
            page,
            bindings,
            evidence,
            test: step,
            source: selectedModel,
        });
        async function cardPair(item) {
            if (new URL(page.url()).pathname !== repoPath(selectedModel.entry))
                await exact(selectedModel.entry);
            const selected = page.getByRole("region", {
                name: "Selected publication",
                exact: true,
            });
            await selected.waitFor();
            if (
                JSON.stringify(
                    await selected.locator("code").allTextContents(),
                ) !== JSON.stringify([item.commit_sha, item.publication_id])
            ) {
                await page
                    .getByRole("tab", { name: "Revisions", exact: true })
                    .click();
                await page
                    .getByRole("button", {
                        name: "View publication " + item.publication_id,
                        exact: true,
                    })
                    .click();
            }
            await page
                .getByRole("tab", { name: "Overview", exact: true })
                .click();
            await page.waitForFunction(
                (pair) =>
                    JSON.stringify(
                        [
                            ...document.querySelectorAll(
                                '[aria-label="Selected publication"] code',
                            ),
                        ].map((node) => node.textContent),
                    ) === JSON.stringify(pair),
                [item.commit_sha, item.publication_id],
            );
            const query = new URLSearchParams(
                new URL(page.url()).hash.slice(1),
            );
            assert.equal(query.get("commit_sha"), item.commit_sha);
            assert.equal(query.get("publication_id"), item.publication_id);
            return page.getByRole("region", {
                name: "Archived README",
                exact: true,
            });
        }
        await step("readme-active-corpus-fails-closed", async () => {
            const revisions = (
                await read(
                    "/repositories/revisions?selector=model%3A" +
                        encodeURIComponent(model.repository_id) +
                        "&limit=100",
                )
            ).value.revisions;
            assert.equal(revisions.length, 5);
            cards = [];
            for (const revision of revisions) {
                const manifest = (
                    await read(
                        "/repositories/model/" +
                            model.repository_id +
                            "/manifests/" +
                            revision.commit_sha +
                            "/" +
                            revision.publication_id,
                    )
                ).value.manifest;
                const source = manifest.files.find(
                    (file) => file.path === "README.md",
                );
                assert(source);
                const response = await read(
                        "/repositories/model/" +
                            model.repository_id +
                            "/publications/" +
                            revision.commit_sha +
                            "/" +
                            revision.publication_id +
                            "/card",
                    ),
                    card = response.value;
                assert.equal(card.archive_id, archiveId);
                assert.equal(card.commit_sha, revision.commit_sha);
                assert.equal(card.publication_id, revision.publication_id);
                assert.equal(card.expected_source_sha256, source.sha256);
                assert(
                    !JSON.stringify(response.wire).includes(
                        "hf_" + "A".repeat(32),
                    ),
                );
                cards.push({ ...revision, card });
                result.card_states.push({
                    commit_sha: revision.commit_sha,
                    publication_id: revision.publication_id,
                    state: card.state,
                });
            }
            const byGeneration = (generation) =>
                cards.find(
                    (item) => item.publication_generation === generation,
                );
            for (const [generation, state] of [
                [1, "unsafe"],
                [2, "unsupported"],
                [3, "unsafe"],
            ]) {
                const item = byGeneration(generation);
                assert.equal(item.card.state, state);
                assert.equal(item.card.markdown, null);
                const region = await cardPair(item);
                await region.getByText(state, { exact: true }).waitFor();
                await region
                    .getByText(
                        "Sanitized source is unavailable for this capture state. Capture changes require a separate explicit operation.",
                        { exact: true },
                    )
                    .waitFor();
                assert.equal(
                    await region
                        .locator(
                            "script,iframe,form,img,svg,style,object,embed,link,[onclick],[onerror],[style]",
                        )
                        .count(),
                    0,
                );
                assert.equal(
                    await page.evaluate(
                        () =>
                            globalThis.fixtureExecuted === undefined &&
                            globalThis.browserCorpusExecuted === undefined,
                    ),
                    true,
                );
                assert(
                    !(await region.textContent()).includes(
                        "hf_" + "A".repeat(32),
                    ),
                );
            }
        });
        await step("readme-blocked-resources-and-pinned-links", async () => {
            const item = cards.find(
                (item) => item.publication_generation === 5,
            );
            assert.equal(item.card.state, "present");
            assert.equal(
                createHash("sha256").update(item.card.markdown).digest("hex"),
                item.card.presentation_sha256,
            );
            const region = await cardPair(item);
            await region
                .getByRole("heading", {
                    name: "Owned browser read corpus",
                    exact: true,
                })
                .waitFor();
            assert.equal(
                await region
                    .locator(
                        "img,iframe,object,embed,script,style,link,source,video,audio",
                    )
                    .count(),
                0,
            );
            assert(
                (await region.textContent()).includes("[image omitted]"),
                "The captured image placeholder remains visible",
            );
            const guide = region.getByRole("link", {
                name: "relative guide",
                exact: true,
            });
            assert.equal(
                await guide.getAttribute("href"),
                "https://huggingface.co/fixture/model/blob/" +
                    item.commit_sha +
                    "/docs/guide.md",
            );
            for (const link of await region.getByRole("link").all()) {
                assert.equal(
                    new URL(await link.getAttribute("href")).protocol,
                    "https:",
                );
                assert.equal(await link.getAttribute("target"), "_blank");
                assert.equal(
                    await link.getAttribute("rel"),
                    "noopener noreferrer",
                );
                assert.equal(
                    await link.getAttribute("referrerpolicy"),
                    "no-referrer",
                );
            }
            assert.equal(
                await page.evaluate(
                    () =>
                        globalThis.fixtureExecuted === undefined &&
                        globalThis.browserCorpusExecuted === undefined,
                ),
                true,
            );
        });
        await step(
            "readme-sanitized-source-secret-and-format-bounds",
            async () => {
                for (const generation of [4, 5]) {
                    const item = cards.find(
                        (item) => item.publication_generation === generation,
                    );
                    assert.equal(item.card.state, "present");
                    const region = await cardPair(item);
                    if (generation === 5) {
                        await region.getByRole("table").first().waitFor();
                        await region.locator("pre code").first().waitFor();
                        assert((await region.getByRole("table").count()) > 0);
                        assert((await region.locator("pre code").count()) > 0);
                    } else
                        await region
                            .getByRole("alert")
                            .filter({
                                hasText:
                                    "The source is too deeply nested for formatting.",
                            })
                            .waitFor();
                    assert.equal(
                        await page.locator("#main-content").count(),
                        1,
                    );
                    assert.equal(
                        await region.locator("#main-content").count(),
                        0,
                    );
                    await region
                        .getByRole("button", {
                            name: "Sanitized source",
                            exact: true,
                        })
                        .click();
                    const source = region.getByRole("group", {
                        name: "Sanitized README source",
                        exact: true,
                    });
                    assert.equal(
                        await source.textContent(),
                        item.card.markdown,
                    );
                    assert(
                        Buffer.byteLength(item.card.markdown) <= 1024 * 1024,
                    );
                    assert.equal(
                        await source
                            .locator("script,iframe,form,img,svg,style,[id]")
                            .count(),
                        0,
                    );
                    assert.equal(
                        await page.locator("#main-content").count(),
                        1,
                    );
                }
                const suppressed = cards.find(
                    (item) => item.publication_generation === 1,
                );
                assert.equal(suppressed.card.markdown, null);
                assert.equal(suppressed.card.state, "unsafe");
                assert.equal(
                    await page.evaluate(
                        () =>
                            globalThis.fixtureExecuted === undefined &&
                            globalThis.browserCorpusExecuted === undefined,
                    ),
                    true,
                );
            },
        );
        assert.deepEqual(result.non_get, []);
    } finally {
        page.off("request", observe);
        assert.deepEqual(
            result.non_get,
            [],
            "Read workflow must not transmit mutations",
        );
    }
}

/** INV-001/ADR153: normal supported configuration controls on the owned fresh corpus.
 * Library's independent GET-only observer has returned before these two pure validations.
 * No sizing, Apply, accepted job, protocol injection or complete CONFIG-row claim.
 */
export const CONFIGURATION_UI_ASSERTIONS = [
    "ordinary-config-read-projection",
    "ordinary-tag-draft-first-validation",
    "ordinary-explicit-second-validation",
    "ordinary-discard-fresh-UI-read",
    "config-numeric-lexical-leading-zero",
    "config-numeric-lexical-exponent",
    "config-numeric-lexical-fraction",
    "config-numeric-lexical-unsafe-integer",
    "config-numeric-range-free-gib-upper",
    "config-numeric-range-free-percent-upper",
    "config-numeric-range-workers-upper",
    "config-numeric-range-sync-wait-upper",
    "config-numeric-range-staging-lower",
    "config-numeric-range-verification-wait-upper",
    "config-numeric-range-repair-grace-lower",
    "config-tag-refusal-raw-count-before-deduplication",
    "config-tag-refusal-raw-length-before-trim",
    "config-tag-refusal-nonascii",
    "config-tag-refusal-empty-line",
    "config-json-refusal-malformed",
    "config-json-refusal-mixed-managed-and-candidate",
    "config-json-refusal-json-pointer",
    "config-json-refusal-protected-root",
    "config-json-refusal-coercive-integer",
    "config-json-refusal-coercive-boolean",
    "config-json-refusal-noninteger-lexeme",
    "config-json-refusal-duplicate-identity",
    "config-json-refusal-reordered-existing",
];
// Real configuration edits use two independent authenticated sessions and the fresh F8 corpus.
export const CONFIGURATION_CONFLICT_ASSERTIONS = [
    "config-two-sessions-same-full-byte-base",
    "config-session-a-tag-only-validate",
    "config-session-a-reviewed-empty-preview",
    "config-session-b-tag-only-validate",
    "config-session-b-reviewed-empty-preview",
    "config-session-a-one-reviewed-apply",
    "config-session-a-confirm-original-host-outcome",
    "config-session-b-stale-apply-refusal",
    "config-session-b-compare-retains-original-intent",
    "config-session-a-original-preview-after-reload",
    "config-session-a-original-apply-after-reload",
    "config-session-a-original-host-outcome-after-reload",
    "config-session-b-original-preview-after-reload",
];
export async function configurationConflictCases({
    browser,
    bindings,
    credentials,
    evidence,
    test,
    observeNetwork,
    engine,
}) {
    const prefix = bindings.prefix,
        api = prefix + "/api/v1",
        archiveId = evidence.configured_archive_id;
    const result = {
        scope: "Two independent authenticated sessions; tag-only reviewed Apply and stale full-byte-base refusal",
        steps: [],
        actors: [],
        consoleErrors: [],
        expectedResourceDiagnostics: [],
        unexpectedRequests: [],
        fullConfigurationSuiteAcceptanceClaimed: false,
        externalPrivateFsyncBeforeForwardClaimed: false,
        prerequisite:
            "Current installed helper, configuration permission/config-write capability and fresh browser_reads F8 corpus; no authority is provisioned by this driver",
    };
    evidence.configuration_conflict = result;
    const actors = [],
        keys = new Set();
    let before,
        after,
        outcome,
        primaryError = null,
        cleanupError = null;
    const clean =
        "The editable draft matches its installed base. Raw draft text is not stored in localStorage.";
    async function step(id, fn) {
        await test(id, async () => {
            try {
                await fn();
            } catch (error) {
                for (const key of keys)
                    for (const value of [
                        key,
                        encodeURIComponent(key),
                        Buffer.from(key).toString("base64"),
                    ])
                        error.message = error.message.replaceAll(
                            value,
                            "[private original key]",
                        );
                throw error;
            }
        });
        assert.equal(evidence.cases.at(-1)?.passed, true, id);
        result.steps.push(id);
    }
    async function privateJson(name, value) {
        const file = await open(
            path.join(
                bindings.workspace,
                `configuration-conflict-${bindings.profile}-${prefix ? "prefixed" : "root"}-${engine}-${name}.private.json`,
            ),
            "wx",
            0o600,
        );
        try {
            await file.writeFile(JSON.stringify(value, null, 2) + "\n");
            await file.sync();
        } finally {
            await file.close();
        }
        const directory = await open(bindings.workspace, "r");
        try {
            await directory.sync();
        } finally {
            await directory.close();
        }
    }
    function healthy() {
        assert.deepEqual(result.unexpectedRequests, []);
        for (const actor of actors) {
            assert.deepEqual(actor.pageErrors, []);
            assert.deepEqual(actor.failedResponses, []);
        }
    }
    async function navigate(actor, name) {
        await actor.page
            .getByRole("navigation", { name: "Main navigation", exact: true })
            .getByRole("link", { name, exact: true })
            .click();
        await actor.page.getByRole("heading", { name, exact: true }).waitFor();
    }
    async function read(actor, suffix, key) {
        const row = await browserRead(
            actor.page,
            api + suffix,
            key ? { "Idempotency-Key": key } : {},
        );
        assert.equal(row.status, 200);
        assertApiHeaders(row.headers);
        const wire = JSON.parse(row.text);
        assert.equal(wire.archive_id, archiveId);
        assert.equal(wire.envelope.exit_code, 0);
        return wire;
    }
    async function registry(actor, key) {
        return await actor.page.evaluate((key) => {
            const raw = localStorage.getItem("hfcache.web.operations.v1");
            if (raw === null) return null;
            if (new globalThis.TextEncoder().encode(raw).length > 65536)
                throw new Error("Original registry exceeds64KiB");
            const value = JSON.parse(raw);
            if (value.schemaVersion !== 1 || !Array.isArray(value.records))
                throw new Error("Original registry shape");
            const found = value.records.filter(
                (row) =>
                    row.handles?.kind === "basic-key" &&
                    row.handles.key === key,
            );
            if (found.length !== 1) return null;
            return { raw, record: found[0] };
        }, key);
    }
    async function createActor(label) {
        const context = await browser.newContext({
                httpCredentials: {
                    username: credentials.username,
                    password: credentials.password,
                },
                ignoreHTTPSErrors: false,
                serviceWorkers: "block",
                viewport: { width: 1440, height: 1000 },
            }),
            page = await context.newPage();
        page.setDefaultTimeout(30000);
        page.setDefaultNavigationTimeout(15000);
        const actor = {
            label,
            context,
            page,
            editor: page.getByRole("region", {
                name: "Configuration and tags",
                exact: true,
            }),
            posts: [],
            pageErrors: [],
            failedResponses: [],
            consoles: [],
            action: null,
        };
        actors.push(actor);
        context.on("request", (request) => observeNetwork(request.url()));
        page.on("pageerror", (error) =>
            actor.pageErrors.push(secretDiagnostic(error, credentials)),
        );
        page.on("console", (message) => {
            if (message.type() === "error")
                actor.consoles.push({
                    text: message.text().slice(0, 4096),
                    url: message.location().url ?? "",
                });
        });
        page.on("response", (response) => {
            if (response.status() >= 500)
                actor.failedResponses.push({
                    url: response.url(),
                    status: response.status(),
                });
        });
        page.on("request", (request) => {
            if (["GET", "HEAD"].includes(request.method())) return;
            try {
                assert(actor.action);
                assert.equal(request.method(), "POST");
                assert.equal(
                    request.url(),
                    bindings.origin + api + actor.action.suffix,
                );
                assert.equal(actor.action.request, null);
                actor.action.request = request;
                const body = request.postDataJSON();
                assert.deepEqual(body, actor.action.body);
                const key = request.headers()["idempotency-key"];
                if (actor.action.suffix === "/config/validate")
                    assert.equal(key, undefined);
                else {
                    assert.match(
                        key,
                        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u,
                    );
                    assert(!keys.has(key));
                    keys.add(key);
                    actor.action.key = key;
                }
                actor.posts.push({
                    suffix: actor.action.suffix,
                    status: null,
                    key,
                    body,
                    requestObservedEpochMs: Date.now(),
                });
            } catch {
                result.unexpectedRequests.push({
                    method: request.method(),
                    path: new URL(request.url()).pathname,
                });
            }
        });
        const navigation = await page.goto(
            bindings.origin + prefix + "/ui/library",
        );
        assert(navigation);
        assert.equal(navigation.status(), 200);
        await page
            .getByRole("heading", { name: "Library", exact: true })
            .waitFor();
        return actor;
    }
    async function clickPost(actor, label, suffix, body, status) {
        healthy();
        assert.equal(actor.action, null);
        const action = { suffix, body, request: null, key: null };
        actor.action = action;
        try {
            const sent = actor.page.waitForRequest(
                (request) =>
                    request.method() === "POST" &&
                    request.url() === bindings.origin + api + suffix,
                { timeout: 35000 },
            );
            const received = actor.page.waitForResponse(
                async (response) => response.request() === (await sent),
                { timeout: 35000 },
            );
            const [request, response] = await Promise.all([
                sent,
                received,
                actor.editor
                    .getByRole("button", { name: label, exact: true })
                    .click(),
            ]);
            assert.equal(request, action.request);
            assert.equal(response.status(), status);
            actor.posts.at(-1).status = status;
            if (action.key) {
                // Product persists its original Basic key before transport. This is a post-dispatch collector copy, not an interception/pre-forward claim.
                if (status === 202)
                    await actor.page.waitForFunction((key) => {
                        const value = JSON.parse(
                            localStorage.getItem("hfcache.web.operations.v1") ??
                                "null",
                        );
                        return value?.records.some(
                            (row) =>
                                row.handles?.kind === "basic-key" &&
                                row.handles.key === key &&
                                /^[0-9a-f]{32}$/u.test(
                                    row.handles.operationId ?? "",
                                ),
                        );
                    }, action.key);
                const saved = await registry(actor, action.key);
                assert(saved);
                assert.equal(
                    saved.record.route,
                    suffix === "/plans"
                        ? "/api/v1/plans"
                        : "/api/v1/config/applications",
                );
                assert.equal(
                    saved.record.originalAuthority.scope.origin,
                    bindings.origin,
                );
                assert.equal(
                    saved.record.originalAuthority.scope.publicPrefix,
                    prefix,
                );
                assert.equal(
                    saved.record.originalAuthority.scope.archiveId,
                    archiveId,
                );
                await privateJson(
                    actor.label +
                        "-" +
                        actor.posts.length +
                        "-original-request-and-product-registry",
                    {
                        key: action.key,
                        body,
                        registry: saved,
                        requestObservedEpochMs:
                            actor.posts.at(-1).requestObservedEpochMs,
                        collectorCopyAfterDispatch: true,
                    },
                );
                return {
                    key: action.key,
                    body,
                    recordId: saved.record.recordId,
                    operationId: saved.record.handles.operationId ?? null,
                    status,
                };
            }
            return { status };
        } finally {
            actor.action = null;
        }
    }
    async function loaded(actor) {
        await navigate(actor, "Administration");
        const button = actor.editor.getByRole("button", {
            name: "Read installed configuration",
            exact: true,
        });
        const sent = actor.page.waitForRequest(
            (request) =>
                request.method() === "GET" &&
                request.url() === bindings.origin + api + "/config",
            { timeout: 35000 },
        );
        let wire;
        const received = actor.page.waitForResponse(
            async (response) => {
                if (response.request() !== (await sent)) return false;
                assert.equal(response.status(), 200);
                const [headers, bytes] = await Promise.all([
                    response.allHeaders(),
                    response.body(),
                ]);
                assert(bytes.length <= MAX_BODY);
                assertApiHeaders(headers);
                wire = JSON.parse(
                    new TextDecoder("utf-8", { fatal: true }).decode(bytes),
                );
                assert.equal(wire.archive_id, archiveId);
                assert.equal(wire.envelope.exit_code, 0);
                return true;
            },
            { timeout: 35000 },
        );
        await Promise.all([sent, received, button.click()]);
        await actor.editor.getByText(clean, { exact: true }).waitFor();
        const config = wire.envelope.data;
        assert.equal(
            (
                await actor.editor
                    .getByText("Exact draft base revision", { exact: true })
                    .locator("xpath=following-sibling::dd[1]")
                    .locator("code")
                    .innerText()
            ).trim(),
            config.base_revision,
        );
        return config;
    }
    async function editAndValidate(actor, tag) {
        const model = before.editable.repositories.find(
            (row) => row.type === "model" && row.id === "fixture/model",
        );
        assert(model.tags.length < 64 && !model.tags.includes(tag));
        actor.updated = { ...model, tags: [...model.tags, tag].sort() };
        actor.managed = {
            base_revision: before.base_revision,
            edits: [{ kind: "repository-upsert", repository: actor.updated }],
        };
        await actor.editor
            .getByRole("button", {
                name: "Edit model fixture/model",
                exact: true,
            })
            .click();
        await actor.editor
            .getByRole("textbox", { name: "Tags (one per line)", exact: true })
            .fill(actor.updated.tags.join("\n"));
        await actor.editor
            .getByRole("button", {
                name: "Update draft repository",
                exact: true,
            })
            .click();
        const diff = actor.editor.locator(".configuration-diff");
        assert.equal(await diff.count(), 1);
        assert.deepEqual(
            (await diff.locator("pre").allTextContents()).map(JSON.parse),
            [model, actor.updated],
        );
        assert(
            await actor.editor
                .getByRole("button", { name: "Validate draft", exact: true })
                .isEnabled(),
            "Actual session must expose configuration-write readiness",
        );
        await clickPost(
            actor,
            "Validate draft",
            "/config/validate",
            { managed: actor.managed },
            200,
        );
        const validation = actor.editor.getByText(/Validated exact base/u);
        await validation.waitFor();
        [actor.base, actor.candidate] = await validation
            .locator("code")
            .allTextContents();
        assert.equal(actor.base, before.base_revision);
        assert.match(actor.candidate, /^[0-9a-f]{64}$/u);
        assert.match(
            await validation.innerText(),
            /0 repositories require sizing/u,
        );
    }
    async function preview(actor) {
        actor.preview = await clickPost(
            actor,
            "Preview sizing",
            "/plans",
            { managed: actor.managed },
            202,
        );
        const assessment = actor.editor.getByText(
            /Complete sizing assessment for base/u,
        );
        await assessment.waitFor();
        assert.deepEqual(await assessment.locator("code").allTextContents(), [
            actor.base,
            actor.candidate,
        ]);
        const saved = await registry(actor, actor.preview.key);
        assert.match(saved.record.handles.operationId, /^[0-9a-f]{32}$/u);
        Object.assign(actor.preview, {
            operationId: saved.record.handles.operationId,
            recordId: saved.record.recordId,
        });
        actor.preview.receipt = (
            await read(actor, "/operations/" + actor.preview.operationId)
        ).envelope.data.operation;
        actor.preview.wire = await read(
            actor,
            "/operations/" + actor.preview.operationId + "/result",
        );
        const assessed = actor.preview.wire.envelope.data;
        assert.equal(actor.preview.receipt.state, "succeeded");
        assert.equal(assessed.base_revision, before.base_revision);
        assert.equal(assessed.candidate_revision, actor.candidate);
        assert.equal(assessed.complete, true);
        assert.deepEqual(assessed.required_selectors, []);
        assert.equal(assessed.sizing, null);
        assert.match(actor.preview.wire.config_fingerprint, /^[0-9a-f]{64}$/u);
        assert(
            await actor.editor
                .getByRole("button", {
                    name: "Apply reviewed changes",
                    exact: true,
                })
                .isEnabled(),
        );
    }
    function applyBody(actor) {
        return {
            managed: actor.managed,
            preview: {
                operation_id: actor.preview.operationId,
                key: actor.preview.key,
            },
        };
    }
    async function observeOriginal(actor, original) {
        await navigate(actor, "Operations");
        const recovery = actor.page.getByRole("article", {
            name: "Recovery record " + original.recordId,
            exact: true,
        });
        const observe = recovery.getByRole("button", {
            name: "Observe original operation",
            exact: true,
        });
        await observe.click();
        await recovery.getByText(/Verified in this session\./u).waitFor();
        await observe.waitFor({ state: "visible" });
        const summary = recovery
            .locator("summary")
            .filter({ hasText: /^Validated original result$/u });
        if (!(await summary.locator("..").evaluate((node) => node.open)))
            await summary.click();
        const rendered = recovery.getByRole("region", {
            name: "Original operation result",
            exact: true,
        });
        await rendered.waitFor();
        for (const [label, value] of [
            ["Operation admission ID", original.operationId],
            ["Exit code", "0"],
        ])
            assert.equal(
                (
                    await rendered
                        .getByText(label, { exact: true })
                        .locator("xpath=following-sibling::dd[1]")
                        .innerText()
                ).trim(),
                value,
            );
        assert.deepEqual(
            (await read(actor, "/operations/" + original.operationId)).envelope
                .data.operation,
            original.receipt,
        );
        assert.deepEqual(
            (
                await read(
                    actor,
                    "/operations/" + original.operationId + "/result",
                )
            ).envelope,
            original.wire.envelope,
        );
        return recovery;
    }
    try {
        const A = await createActor("A"),
            B = await createActor("B");
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[0], async () => {
            const [first, other] = await Promise.all([loaded(A), loaded(B)]);
            before = first;
            assert.deepEqual(other, before);
            assert.equal(before.archive_id, archiveId);
            assert.equal(before.editable.repositories.length, 28);
            assert(
                before.editable.repositories.every(
                    (row) => row.enabled === false,
                ),
            );
            if (evidence.configuration_ui === undefined) {
                assert.equal(bindings.configuration_conflict_only, true);
                const prior = evidence.configuration_readonly_prerequisite;
                assert.deepEqual(Object.keys(prior).sort(), [
                    "assertionIds",
                    "engine",
                    "prefix",
                    "receiptSha256",
                ]);
                assert.match(prior.receiptSha256, /^[0-9a-f]{64}$/u);
                assert.equal(prior.engine, engine);
                assert.equal(prior.prefix, prefix);
            }
            assert.deepEqual(
                evidence.configuration_ui?.steps ??
                    evidence.configuration_readonly_prerequisite?.assertionIds,
                CONFIGURATION_UI_ASSERTIONS,
            );
            assert.deepEqual(
                before.editable.repositories.map(({ type, id }) => ({
                    type,
                    id,
                })),
                [
                    { type: "model", id: "fixture/model" },
                    { type: "dataset", id: "fixture/data" },
                    ...Array.from({ length: 26 }, (_, index) => ({
                        type: index % 2 === 0 ? "model" : "dataset",
                        id:
                            "browser/unpublished-" +
                            String(index).padStart(2, "0"),
                    })),
                ],
            );
            result.baseRevision = before.base_revision;
        });
        const suffix =
            bindings.profile +
            "-" +
            (prefix ? "prefixed" : "root") +
            "-" +
            evidence.version.replaceAll(".", "-");
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[1], () =>
            editAndValidate(A, "web022-tab-a-" + suffix),
        );
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[2], () => preview(A));
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[3], () =>
            editAndValidate(B, "web022-tab-b-" + suffix),
        );
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[4], async () => {
            await preview(B);
            assert.notEqual(A.candidate, B.candidate);
            assert.equal(
                A.preview.wire.config_fingerprint,
                B.preview.wire.config_fingerprint,
            );
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[5], async () => {
            A.application = await clickPost(
                A,
                "Apply reviewed changes",
                "/config/applications",
                applyBody(A),
                202,
            );
            const saved = await registry(A, A.application.key);
            assert.match(saved.record.handles.operationId, /^[0-9a-f]{32}$/u);
            Object.assign(A.application, {
                operationId: saved.record.handles.operationId,
                recordId: saved.record.recordId,
            });
            await A.editor
                .getByText(
                    "Original operation " +
                        A.application.operationId +
                        ": succeeded. API receipt state is separate from installed configuration.",
                    { exact: true },
                )
                .waitFor();
            const receipt = (
                await read(A, "/operations/" + A.application.operationId)
            ).envelope.data.operation;
            assert.equal(receipt.state, "succeeded");
            A.application.receipt = receipt;
            A.application.wire = await read(
                A,
                "/operations/" + A.application.operationId + "/result",
            );
            outcome = A.application.wire.envelope.data;
            assert.equal(outcome.state, "confirmed");
            assert.equal(outcome.pending, false);
            assert.equal(
                outcome.config_fingerprint,
                A.preview.wire.config_fingerprint,
            );
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[6], async () => {
            await A.editor
                .getByRole("button", {
                    name: "Observe original application outcome",
                    exact: true,
                })
                .click();
            await A.editor
                .getByText(
                    "Installed configuration confirmed. The exact host outcome is independent of the API receipt.",
                    { exact: true },
                )
                .waitFor();
            await A.editor.getByText(clean, { exact: true }).waitFor();
            after = (await read(A, "/config")).envelope.data;
            assert.notEqual(after.base_revision, before.base_revision);
            assert.equal(outcome.candidate_revision, A.candidate);
            const expected = globalThis.structuredClone(before);
            expected.base_revision = after.base_revision;
            expected.editable.repositories.find(
                (row) => row.type === "model" && row.id === "fixture/model",
            ).tags = A.updated.tags;
            assert.deepEqual(after, expected);
            assert.equal(
                (await read(A, "/status")).config_fingerprint,
                A.preview.wire.config_fingerprint,
            );
            assert.deepEqual(
                (
                    await read(
                        A,
                        "/config/applications/" + A.application.operationId,
                        A.application.key,
                    )
                ).envelope.data,
                outcome,
            );
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[7], async () => {
            B.stale = await clickPost(
                B,
                "Apply reviewed changes",
                "/config/applications",
                applyBody(B),
                409,
            );
            assert.equal(B.stale.operationId, null);
            assert.deepEqual((await read(B, "/config")).envelope.data, after);
            result.staleStatus = 409;
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[8], async () => {
            await B.editor
                .getByRole("button", {
                    name: "Compare installed configuration",
                    exact: true,
                })
                .click();
            await B.editor
                .getByText(
                    "Installed configuration changed. The original draft and base are preserved; reload and re-edit explicitly. Validation and Apply readiness were retired.",
                    { exact: true },
                )
                .waitFor();
            const comparison = B.editor.getByText(/Original draft base/u);
            assert.deepEqual(
                await comparison.locator("code").allTextContents(),
                [before.base_revision, after.base_revision],
            );
            assert(
                await B.editor
                    .getByRole("button", {
                        name: "Apply reviewed changes",
                        exact: true,
                    })
                    .isDisabled(),
            );
            assert.deepEqual(
                (
                    await B.editor
                        .locator(".configuration-diff pre")
                        .allTextContents()
                ).map(JSON.parse),
                [
                    before.editable.repositories.find(
                        (row) =>
                            row.type === "model" && row.id === "fixture/model",
                    ),
                    B.updated,
                ],
            );
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[9], async () => {
            await navigate(A, "Operations");
            assert.equal((await A.page.reload()).status(), 200);
            await A.page
                .getByRole("heading", { name: "Operations", exact: true })
                .waitFor();
            await observeOriginal(A, A.preview);
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[10], async () => {
            await observeOriginal(A, A.application);
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[11], async () => {
            const recovery = A.page.getByRole("article", {
                    name: "Recovery record " + A.application.recordId,
                    exact: true,
                }),
                region = recovery.getByRole("region", {
                    name: "Original configuration outcome",
                    exact: true,
                });
            await region
                .getByRole("button", {
                    name: "Observe original configuration outcome",
                    exact: true,
                })
                .click();
            await region
                .getByText(
                    "Installed configuration confirmed. The original API receipt is unchanged.",
                    { exact: true },
                )
                .waitFor();
            for (const [label, value] of [
                ["Protected host outcome", "confirmed"],
                ["Pending protected work", "No"],
                ["Original application ID", A.application.operationId],
            ])
                assert.equal(
                    (
                        await region
                            .getByText(label, { exact: true })
                            .locator("xpath=following-sibling::dd[1]")
                            .innerText()
                    ).trim(),
                    value,
                );
            assert.deepEqual(
                (
                    await read(
                        A,
                        "/config/applications/" + A.application.operationId,
                        A.application.key,
                    )
                ).envelope.data,
                outcome,
            );
            assert.deepEqual((await read(A, "/config")).envelope.data, after);
            assert.equal(keys.size, 4);
            assert.equal(A.posts.length, 3);
            assert.equal(B.posts.length, 3);
            result.actualScope = {
                tagOnlyApplied: 1,
                staleApplyRefusals: 1,
                pureValidations: 2,
                emptyScopePreviews: 2,
                newKeys: 4,
                HubSizing: false,
                SyncSubmissions: 0,
                fullConfigurationSuiteAcceptanceClaimed: false,
            };
        });
        await step(CONFIGURATION_CONFLICT_ASSERTIONS[12], async () => {
            await B.page
                .getByRole("navigation", {
                    name: "Main navigation",
                    exact: true,
                })
                .getByRole("link", { name: "Operations", exact: true })
                .click();
            await B.page
                .getByRole("dialog", {
                    name: "Unsaved configuration changes",
                    exact: true,
                })
                .getByRole("button", {
                    name: "Discard draft and leave",
                    exact: true,
                })
                .click();
            await B.page
                .getByRole("heading", { name: "Operations", exact: true })
                .waitFor();
            assert.equal((await B.page.reload()).status(), 200);
            await B.page
                .getByRole("heading", { name: "Operations", exact: true })
                .waitFor();
            await observeOriginal(B, B.preview);
            const retained = await registry(B, B.stale.key);
            assert(retained);
            assert.equal(retained.record.recordId, B.stale.recordId);
            assert.equal(retained.record.handles.operationId, null);
            assert.equal(B.posts.length, 3);
        });
        assert.deepEqual(result.steps, CONFIGURATION_CONFLICT_ASSERTIONS);
        healthy();
    } catch (error) {
        primaryError = error;
        throw error;
    } finally {
        try {
            for (const actor of actors) {
                await privateJson(
                    actor.label + "-storage-final",
                    await actor.context.storageState(),
                );
                await actor.context.close();
                for (const message of actor.consoles) {
                    const expected =
                        actor.posts.some(
                            (row) =>
                                row.status === 409 &&
                                row.suffix === "/config/applications",
                        ) &&
                        message.url ===
                            bindings.origin + api + "/config/applications" &&
                        /^Failed to load resource: the server responded with a status of 409(?: \(.*\))?$/u.test(
                            message.text,
                        );
                    if (expected)
                        result.expectedResourceDiagnostics.push({
                            method: "POST",
                            url: message.url,
                            status: 409,
                            text: message.text,
                        });
                    else
                        result.consoleErrors.push({
                            text: secretDiagnostic(
                                new Error(message.text),
                                credentials,
                            ).message,
                            url: message.url,
                        });
                }
                result.actors.push({
                    label: actor.label,
                    contextClosed: true,
                    posts: actor.posts.map(({ suffix, status, key }) => ({
                        suffix,
                        status,
                        keyDigest: key
                            ? createHash("sha256").update(key).digest("hex")
                            : null,
                    })),
                    pageErrors: actor.pageErrors,
                    failedResponses: actor.failedResponses,
                });
            }
            healthy();
            assert.deepEqual(result.consoleErrors, []);
            assert(result.expectedResourceDiagnostics.length <= 1);
        } catch (error) {
            result.cleanupDiagnostic = secretDiagnostic(error, credentials);
            if (primaryError === null) cleanupError = error;
        }
    }
    if (cleanupError !== null) throw cleanupError;
}

export async function configurationReadOnlyCases({
    page,
    bindings,
    evidence,
    test,
    observeUiResponse,
}) {
    const api = bindings.prefix + "/api/v1",
        editor = page.getByRole("region", {
            name: "Configuration and tags",
            exact: true,
        }),
        clean =
            "The editable draft matches its installed base. Raw draft text is not stored in localStorage.";
    const result = {
        steps: [],
        refusals: [],
        supplementaryCollectorRequests: 0,
        callbackDeadlineMs: 45000,
        productionApiReadDeadlineMs: 30000,
        validationRequests: [],
        unexpectedUnsafeRequests: [],
        configApplies: 0,
        sizingJobs: 0,
        acceptedJobs: 0,
        server422Claimed: false,
        restNegativeValidationClause:
            "The supported controls reject these values locally before managed validation.",
        fullWirePrivacyClaimed: false,
    };
    evidence.configuration_ui = result;
    const fields = [
        [
            "storage.archive_root",
            "Archive root is fixed by installed deployment authority.",
        ],
        [
            "storage.archive_id",
            "Archive identity is fixed by installed deployment authority.",
        ],
        [
            "hub",
            "Hub endpoint and credential authority are preserved privately.",
        ],
        ["verification.algorithm", "The verification algorithm is fixed."],
        ["verification.hash_new_content", "Hashing new content is required."],
        [
            "server",
            "Server policy and credentials are managed outside archive configuration.",
        ],
    ];
    const expectedRepositories = [
        { type: "model", id: "fixture/model" },
        { type: "dataset", id: "fixture/data" },
        ...Array.from({ length: 26 }, (_, index) => ({
            type: index % 2 === 0 ? "model" : "dataset",
            id: "browser/unpublished-" + String(index).padStart(2, "0"),
        })),
    ];
    let installed,
        original,
        managed,
        updated,
        candidate,
        activeValidation = null;
    const observe = (request) => {
        if (["GET", "HEAD"].includes(request.method())) return;
        try {
            assert(activeValidation, "Unexpected unsafe configuration request");
            assert.equal(request.method(), "POST");
            assert.equal(
                request.url(),
                bindings.origin + api + "/config/validate",
            );
            assert.equal(request.headers()["idempotency-key"], undefined);
            assert.deepEqual(request.postDataJSON(), { managed });
            assert.equal(
                activeValidation.requests,
                0,
                "One pure POST per explicit Validate click",
            );
            activeValidation.requests++;
            result.validationRequests.push({
                id: activeValidation.id,
                method: "POST",
                path: api + "/config/validate",
                unkeyed: true,
                bodyMatched: true,
            });
        } catch {
            result.unexpectedUnsafeRequests.push({
                method: request.method(),
                path: new URL(request.url()).pathname,
            });
        }
    };
    page.on("request", observe);
    async function step(id, operation) {
        await test(id, async () => {
            await operation();
            assert.deepEqual(result.unexpectedUnsafeRequests, []);
        });
        assert.equal(evidence.cases.at(-1)?.id, id);
        assert.equal(evidence.cases.at(-1)?.passed, true);
        assert.deepEqual(result.unexpectedUnsafeRequests, []);
        result.steps.push(id);
    }
    async function navigate(name) {
        await page
            .getByRole("navigation", { name: "Main navigation", exact: true })
            .getByRole("link", { name, exact: true })
            .click();
        await page.getByRole("heading", { name, exact: true }).waitFor();
    }
    async function clicked(button, method, path, label) {
        const request = page.waitForRequest(
                (row) =>
                    row.method() === method &&
                    row.url() === bindings.origin + path,
                { timeout: 35000 },
            ),
            response = page.waitForResponse(
                async (row) => row.request() === (await request),
                { timeout: 35000 },
            );
        const [sent, received] = await Promise.all([
            request,
            response,
            button.click(),
        ]);
        assert.equal(received.request(), sent);
        assert.equal(received.status(), 200);
        return { request: sent, attempt: observeUiResponse(received, label) };
    }
    function decode(body) {
        assert.equal(body.archive_id, bindings.archiveId);
        assert.equal(body.schema_version, 1);
        assert.equal(body.envelope.exit_code, 0);
        assert.deepEqual(body.envelope.errors, []);
        return body.envelope.data;
    }
    async function visibleProjection() {
        await editor
            .getByText("Exact draft base revision", { exact: true })
            .waitFor();
        await editor.getByText(clean, { exact: true }).waitFor();
        const baseRevision = (
            await editor
                .getByText("Exact draft base revision", { exact: true })
                .locator("xpath=following-sibling::dd[1]")
                .locator("code")
                .innerText()
        ).trim();
        assert.match(baseRevision, /^[0-9a-f]{64}$/u);
        const archiveId = (
            await editor
                .getByText("Archive identity", { exact: true })
                .locator("xpath=following-sibling::dd[1]")
                .locator("code")
                .innerText()
        ).trim();
        assert.equal(archiveId, bindings.archiveId);
        const authority = editor.locator("summary").filter({
            hasText: /^Protected fields and manual authority changes$/u,
        });
        if (!(await authority.locator("..").evaluate((node) => node.open)))
            await authority.click();
        for (const [field, description] of fields) {
            const row = authority
                .locator("..")
                .getByRole("listitem")
                .filter({ has: page.getByText(field, { exact: true }) });
            await row.waitFor();
            assert.equal(
                (await row.innerText()).replace(/\s+/gu, " ").trim(),
                field + ": " + description,
            );
        }
        await editor
            .getByRole("button", { name: "Supported JSON view", exact: true })
            .click();
        const json = editor.getByRole("textbox", {
                name: "Editable configuration JSON",
                exact: true,
            }),
            text = await json.inputValue();
        assert(Buffer.byteLength(text) <= 1048576);
        const editable = JSON.parse(text);
        assert.deepEqual(
            Object.keys(editable).sort(),
            [
                "storage",
                "sync",
                "verification",
                "repair",
                "repositories",
            ].sort(),
        );
        assert.deepEqual(
            Object.keys(editable.storage).sort(),
            [
                "publication_mode",
                "minimum_free_space_gib",
                "minimum_free_space_percent",
                "maximum_revisions",
            ].sort(),
        );
        assert.deepEqual(Object.keys(editable.verification), [
            "lock_wait_seconds",
        ]);
        // tests/web_functional_fixture.py seed_archive(browser_reads=True): this is not
        // a precondition for arbitrary installed native/rootless configurations.
        assert.deepEqual(
            editable.repositories.map(({ type, id }) => ({ type, id })),
            expectedRepositories,
            "The ordinary configuration subset requires the owned fresh browser_reads corpus",
        );
        assert(editable.repositories.every((row) => row.enabled === false));
        assert(!("hub" in editable) && !("server" in editable));
        await editor
            .getByRole("button", { name: "Cancel form edits", exact: true })
            .click();
        await editor.getByText(clean, { exact: true }).waitFor();
        return {
            baseRevision,
            archiveId,
            editable,
            protectedFields: fields.map(([field, description]) => ({
                field,
                description,
            })),
        };
    }
    function verifyConfigBody(attempt, expected) {
        attempt.verify = (body) => {
            const dto = decode(body);
            assert.equal(dto.base_revision, expected.baseRevision);
            assert.equal(dto.archive_id, expected.archiveId);
            assert.deepEqual(dto.editable, expected.editable);
            assert.deepEqual(dto.protected_fields, expected.protectedFields);
            assert.deepEqual(
                Object.keys(dto).sort(),
                [
                    "schema_version",
                    "archive_id",
                    "base_revision",
                    "editable",
                    "editable_fields",
                    "protected_fields",
                ].sort(),
            );
        };
    }
    async function validate(id, label) {
        activeValidation = { id, requests: 0 };
        try {
            const observed = await clicked(
                editor.getByRole("button", {
                    name: "Validate draft",
                    exact: true,
                }),
                "POST",
                api + "/config/validate",
                label,
            );
            assert.equal(activeValidation.requests, 1);
            assert.equal(
                observed.request.headers()["idempotency-key"],
                undefined,
            );
            assert.deepEqual(observed.request.postDataJSON(), { managed });
            const text = editor.getByText(/Validated exact base/u);
            await text.waitFor();
            const codes = await text.locator("code").allTextContents();
            assert.equal(codes[0], installed.baseRevision);
            assert.match(codes[1], /^[0-9a-f]{64}$/u);
            assert.match(
                await text.innerText(),
                /0 repositories require sizing/u,
            );
            assert.equal(
                await editor
                    .getByRole("button", {
                        name: "Apply reviewed changes",
                        exact: true,
                    })
                    .isDisabled(),
                true,
            );
            observed.attempt.verify = (body) => {
                const dto = decode(body);
                assert.equal(dto.base_revision, installed.baseRevision);
                assert.equal(dto.candidate_revision, codes[1]);
                assert.equal(dto.valid, true);
                assert.deepEqual(dto.required_selectors, []);
            };
            return codes[1];
        } finally {
            activeValidation = null;
        }
    }
    async function assertClean() {
        await editor.getByText(clean, { exact: true }).waitFor();
        assert.equal(
            await editor
                .getByRole("button", {
                    name: "Apply reviewed changes",
                    exact: true,
                })
                .isDisabled(),
            true,
        );
        assert.equal(
            (
                await editor
                    .getByText("Exact draft base revision", { exact: true })
                    .locator("xpath=following-sibling::dd[1]")
                    .locator("code")
                    .innerText()
            ).trim(),
            installed.baseRevision,
        );
        assert.deepEqual(result.unexpectedUnsafeRequests, []);
        assert.equal(result.validationRequests.length, 2);
    }
    async function assertOriginalDraftAndClearNotice() {
        await editor
            .getByRole("button", { name: "Supported JSON view", exact: true })
            .click();
        const field = editor.getByRole("textbox", {
            name: "Editable configuration JSON",
            exact: true,
        });
        assert.deepEqual(
            JSON.parse(await field.inputValue()),
            installed.editable,
        );
        await editor
            .getByRole("button", { name: "Use JSON as draft", exact: true })
            .click();
        await field.waitFor({ state: "hidden" });
        await assertClean();
        assert.equal(await editor.getByText(/^Draft refused \(/u).count(), 0);
    }
    async function closeAndCheck() {
        await editor
            .getByRole("button", { name: "Cancel form edits", exact: true })
            .click();
        await assertOriginalDraftAndClearNotice();
    }
    async function record(id, actual, details) {
        result.refusals.push({
            id,
            diagnostic: actual,
            scope: "Actual local UI refusal; zero request; prior valid projection preserved",
            ...details,
        });
        await closeAndCheck();
    }
    async function editOriginal() {
        const edit = editor.getByRole("button", {
            name: "Edit " + original.type + " " + original.id,
            exact: true,
        });
        for (let index = 0; !(await edit.count()) && index < 3; index++) {
            const next = editor.getByRole("button", {
                name: "Next repositories",
                exact: true,
            });
            assert(await next.isEnabled());
            await next.click();
        }
        await edit.click();
        return editor.getByRole("form", {
            name: "Repository draft",
            exact: true,
        });
    }
    try {
        await step(CONFIGURATION_UI_ASSERTIONS[0], async () => {
            await navigate("Administration");
            const observed = await clicked(
                editor.getByRole("button", {
                    name: "Read installed configuration",
                    exact: true,
                }),
                "GET",
                api + "/config",
                "initial-installed-config-UI-read",
            );
            installed = await visibleProjection();
            original = installed.editable.repositories.find(
                (row) => row.type === "model" && row.id === "fixture/model",
            );
            assert(original);
            verifyConfigBody(observed.attempt, installed);
            result.initialProjection = {
                baseRevision: installed.baseRevision,
                archiveId: installed.archiveId,
                configuredRepositories: expectedRepositories,
                bodyCapture: observed.attempt,
            };
        });
        await step(CONFIGURATION_UI_ASSERTIONS[1], async () => {
            assert(
                original.tags.length < 64 &&
                    !original.tags.includes("web022-ordinary-ui-validation"),
            );
            updated = {
                ...original,
                tags: [
                    ...original.tags,
                    "web022-ordinary-ui-validation",
                ].sort(),
            };
            const form = await editOriginal();
            await form
                .getByRole("textbox", {
                    name: "Tags (one per line)",
                    exact: true,
                })
                .fill(updated.tags.join("\n"));
            await form
                .getByRole("button", {
                    name: "Update draft repository",
                    exact: true,
                })
                .click();
            const diff = editor.locator(".configuration-diff").filter({
                has: page.getByRole("heading", {
                    name: original.type + ":" + original.id,
                    exact: true,
                }),
            });
            await diff.locator("pre").last().waitFor();
            assert.deepEqual(
                (await diff.locator("pre").allTextContents()).map((text) =>
                    JSON.parse(text),
                ),
                [original, updated],
            );
            managed = {
                base_revision: installed.baseRevision,
                edits: [{ kind: "repository-upsert", repository: updated }],
            };
            candidate = await validate(
                CONFIGURATION_UI_ASSERTIONS[1],
                "first-explicit-UI-validation",
            );
        });
        await step(CONFIGURATION_UI_ASSERTIONS[2], async () => {
            assert.equal(
                await validate(
                    CONFIGURATION_UI_ASSERTIONS[2],
                    "second-explicit-UI-validation",
                ),
                candidate,
            );
            result.deterministicCandidate = candidate;
        });
        await step(CONFIGURATION_UI_ASSERTIONS[3], async () => {
            await editor
                .getByRole("button", { name: "Discard draft", exact: true })
                .click();
            await editor.getByText(clean, { exact: true }).waitFor();
            const observed = await clicked(
                    editor.getByRole("button", {
                        name: "Read installed configuration",
                        exact: true,
                    }),
                    "GET",
                    api + "/config",
                    "fresh-installed-config-after-explicit-discard",
                ),
                fresh = await visibleProjection();
            assert.deepEqual(fresh, installed);
            verifyConfigBody(observed.attempt, fresh);
            installed = fresh;
            result.freshDiscardReadPreservesOriginalProjection = true;
            await assertClean();
        });
        const lexical = [
            ["leading-zero", "01"],
            ["exponent", "1e1"],
            ["fraction", "1.5"],
            ["unsafe-integer", "9007199254740992"],
        ];
        for (const [id, value] of lexical)
            await step("config-numeric-lexical-" + id, async () => {
                await editor
                    .getByRole("button", {
                        name: "Edit global settings",
                        exact: true,
                    })
                    .click();
                const form = editor.getByRole("form", {
                        name: "Global settings draft",
                        exact: true,
                    }),
                    field = form.getByRole("textbox", {
                        name: "Maximum sync workers",
                        exact: true,
                    });
                await field.fill(value);
                assert.equal(await field.inputValue(), value);
                await form
                    .getByRole("button", {
                        name: "Update draft settings",
                        exact: true,
                    })
                    .click();
                const diagnostic =
                    "Settings require exact whole numbers within the supported limits. The prior valid draft is preserved.";
                await editor
                    .getByRole("alert")
                    .filter({ hasText: diagnostic })
                    .waitFor();
                await record(id, diagnostic, {
                    field: "sync.max_workers",
                    entered: value,
                });
            });
        const ranges = [
            [
                "free-gib-upper",
                "Minimum free space (GiB)",
                "1048577",
                "storage.minimum_free_space_gib",
            ],
            [
                "free-percent-upper",
                "Minimum free space (%)",
                "101",
                "storage.minimum_free_space_percent",
            ],
            ["workers-upper", "Maximum sync workers", "33", "sync.max_workers"],
            [
                "sync-wait-upper",
                "Sync lock wait (seconds)",
                "86401",
                "sync.lock_wait_seconds",
            ],
            [
                "staging-lower",
                "Stale staging age (hours)",
                "0",
                "sync.stale_staging_age_hours",
            ],
            [
                "verification-wait-upper",
                "Verification lock wait (seconds)",
                "604801",
                "verification.lock_wait_seconds",
            ],
            [
                "repair-grace-lower",
                "Retired instance grace (hours)",
                "167",
                "repair.retired_instance_grace_hours",
            ],
        ];
        for (const [id, label, value, path] of ranges)
            await step("config-numeric-range-" + id, async () => {
                await editor
                    .getByRole("button", {
                        name: "Edit global settings",
                        exact: true,
                    })
                    .click();
                const form = editor.getByRole("form", {
                    name: "Global settings draft",
                    exact: true,
                });
                await form
                    .getByRole("textbox", { name: label, exact: true })
                    .fill(value);
                await form
                    .getByRole("button", {
                        name: "Update draft settings",
                        exact: true,
                    })
                    .click();
                const diagnostic = "Draft refused (invalid) at " + path + ".";
                await editor.getByText(diagnostic, { exact: true }).waitFor();
                await record(id, diagnostic, { field: path, entered: value });
            });
        const tags = [
            [
                "raw-count-before-deduplication",
                Array(65).fill("gpu").join("\n"),
            ],
            ["raw-length-before-trim", " ".repeat(128) + "g"],
            ["nonascii", "é"],
            ["empty-line", "gpu\n"],
        ];
        for (const [id, value] of tags)
            await step("config-tag-refusal-" + id, async () => {
                const form = await editOriginal(),
                    field = form.getByRole("textbox", {
                        name: "Tags (one per line)",
                        exact: true,
                    });
                await field.fill(value);
                assert.equal(await field.inputValue(), value);
                await form
                    .getByRole("button", {
                        name: "Update draft repository",
                        exact: true,
                    })
                    .click();
                const diagnostic =
                    "Repository fields are invalid. Check the repository identity, revision, tags and declared dependencies. The prior valid draft is preserved.";
                await editor
                    .getByRole("alert")
                    .filter({ hasText: diagnostic })
                    .waitFor();
                await record(id, diagnostic, {
                    repositoryType: original.type,
                    repositoryId: original.id,
                    rawLines: value.split("\n").length,
                    rawCharacters: [...value].length,
                });
            });
        const copy = () => JSON.parse(JSON.stringify(installed.editable)),
            jsonCases = [
                ["malformed", () => "{", "invalid", "editable"],
                [
                    "mixed-managed-and-candidate",
                    () =>
                        JSON.stringify({
                            ...copy(),
                            candidate: "schema_version = 1",
                            managed: {
                                base_revision: installed.baseRevision,
                                edits: [],
                            },
                        }),
                    "invalid",
                    "editable",
                ],
                [
                    "json-pointer",
                    () =>
                        JSON.stringify({
                            ...copy(),
                            "/storage/minimum_free_space_gib": 0,
                        }),
                    "invalid",
                    "editable",
                ],
                [
                    "protected-root",
                    () => {
                        const dto = copy();
                        dto.storage.archive_root =
                            "/owned-not-an-editable-path";
                        return JSON.stringify(dto);
                    },
                    "invalid",
                    "storage",
                ],
                [
                    "coercive-integer",
                    () => {
                        const dto = copy();
                        dto.storage.minimum_free_space_gib = "1";
                        return JSON.stringify(dto);
                    },
                    "invalid",
                    "storage.minimum_free_space_gib",
                ],
                [
                    "coercive-boolean",
                    () => {
                        const dto = copy();
                        dto.sync.continue_on_repository_error = 1;
                        return JSON.stringify(dto);
                    },
                    "invalid",
                    "sync.continue_on_repository_error",
                ],
                [
                    "noninteger-lexeme",
                    () => {
                        const dto = copy();
                        dto.storage.minimum_free_space_gib = 1;
                        const source = JSON.stringify(dto);
                        assert(source.includes('"minimum_free_space_gib":1'));
                        return source.replace(
                            '"minimum_free_space_gib":1',
                            '"minimum_free_space_gib":1.0',
                        );
                    },
                    "invalid",
                    "storage.minimum_free_space_gib",
                ],
                [
                    "duplicate-identity",
                    () => {
                        const dto = copy();
                        dto.repositories.push(
                            JSON.parse(JSON.stringify(dto.repositories[0])),
                        );
                        return JSON.stringify(dto);
                    },
                    "duplicate",
                    "repositories.28",
                ],
                [
                    "reordered-existing",
                    () => {
                        const dto = copy();
                        [dto.repositories[0], dto.repositories[1]] = [
                            dto.repositories[1],
                            dto.repositories[0],
                        ];
                        return JSON.stringify(dto);
                    },
                    "order",
                    "repositories",
                ],
            ];
        for (const [id, build, reason, path] of jsonCases)
            await step("config-json-refusal-" + id, async () => {
                await editor
                    .getByRole("button", {
                        name: "Supported JSON view",
                        exact: true,
                    })
                    .click();
                const form = editor.getByRole("form", {
                        name: "Supported JSON draft",
                        exact: true,
                    }),
                    field = form.getByRole("textbox", {
                        name: "Editable configuration JSON",
                        exact: true,
                    }),
                    source = build();
                await field.fill(source);
                assert.equal(await field.inputValue(), source);
                await form
                    .getByRole("button", {
                        name: "Use JSON as draft",
                        exact: true,
                    })
                    .click();
                const diagnostic =
                    "Draft refused (" + reason + ") at " + path + ".";
                await editor.getByText(diagnostic, { exact: true }).waitFor();
                assert.equal(await form.isVisible(), true);
                await record(id, diagnostic, {
                    field: path,
                    reason,
                    sourceBytes: Buffer.byteLength(source),
                });
            });
        assert.deepEqual(result.steps, CONFIGURATION_UI_ASSERTIONS);
        assert.equal(result.refusals.length, 24);
        assert.equal(result.validationRequests.length, 2);
        await assertClean();
        result.priorValidDraftAndBasePreserved = true;
        result.passed = true;
        return result;
    } finally {
        page.off("request", observe);
        assert.deepEqual(result.unexpectedUnsafeRequests, []);
    }
}

/** Call only after the owned fresh cell's original recovery and technical
 * capture have completed. The existing caller supplies its hash-checked
 * fixture.json explicitly; this read does not capture, submit, or replay work.
 * The exact pair's manifest drives both legacy and opt-in browser-read file checks.
 */
export async function richCardRead({
    page,
    bindings,
    evidence,
    test,
    fixture,
    engine,
}) {
    assert.equal(bindings.profile, "native");
    assert.deepEqual(selectedEngines(bindings), [engine]);
    assert.equal(fixture.schema_version, 1);
    assert.match(
        fixture.archive_id,
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u,
    );
    const rich = fixture.rich;
    assert.equal(rich.model_repository, "model:fixture/model");
    assert.match(rich.current_commit_sha, /^[0-9a-f]{40}$/u);
    assert.match(rich.current_publication_id, /^[0-9a-f]{32}$/u);
    assert.match(rich.readme_sha256, /^[0-9a-f]{64}$/u);
    assert.equal(bindings.asset_manifest.build.source_dirty, false);
    const prefix = bindings.prefix,
        ui = prefix + "/ui/";
    assert.ok(["", "/management"].includes(prefix));
    const bootstrapPath = fixedEndpoint(
        bindings.origin,
        prefix,
        "/ui/bootstrap.json",
    ).pathname;
    assert.equal(new URL(page.url()).origin, bindings.origin);
    const id = "rich-card-dom-and-pinned-files";
    await test(id, async () => {
        let unsafeRequests = 0;
        const observe = (request) => {
            if (!["GET", "HEAD"].includes(request.method())) unsafeRequests++;
        };
        page.on("request", observe);
        try {
            const bootstrap = JSON.parse(
                (await browserRead(page, bootstrapPath)).text,
            );
            assert.equal(bootstrap.configured_archive_id, fixture.archive_id);
            assert.equal(bootstrap.configured_origin, bindings.origin);
            assertBootstrapPaths(bootstrap.paths, prefix);
            assert.equal(
                bootstrap.build.asset_manifest_sha256,
                bindings.asset_manifest_sha256,
            );
            assert.deepEqual(
                bootstrap.build.metadata,
                bindings.asset_manifest.build,
            );
            const pair =
                rich.current_commit_sha + "/" + rich.current_publication_id;
            const manifestResponse = await browserRead(
                page,
                prefix +
                    "/api/v1/repositories/model/fixture/model/manifests/" +
                    pair,
            );
            assert.equal(manifestResponse.status, 200);
            assertApiHeaders(manifestResponse.headers);
            const manifestWire = JSON.parse(manifestResponse.text);
            assert.equal(manifestWire.archive_id, fixture.archive_id);
            const manifest = envelope(manifestWire).manifest;
            assert.equal(manifest.repository_type, "model");
            assert.equal(manifest.repository_id, "fixture/model");
            assert.equal(manifest.commit_sha, rich.current_commit_sha);
            assert.equal(manifest.publication_id, rich.current_publication_id);
            assert.equal(manifest.file_count, manifest.files.length);
            assert(manifest.file_count > 0 && manifest.file_count <= 25);
            const readme = manifest.files.find(
                (file) => file.path === "README.md",
            );
            assert(readme);
            assert.equal(readme.sha256, rich.readme_sha256);
            const response = await browserRead(
                page,
                prefix +
                    "/api/v1/repositories/model/fixture/model/publications/" +
                    pair +
                    "/card",
            );
            assert.equal(response.status, 200);
            assertApiHeaders(response.headers);
            const wire = JSON.parse(response.text);
            assert.equal(wire.archive_id, fixture.archive_id);
            const captured = envelope(wire);
            assert.equal(captured.state, "present");
            assert.equal(captured.archive_id, fixture.archive_id);
            assert.equal(captured.commit_sha, rich.current_commit_sha);
            assert.equal(captured.publication_id, rich.current_publication_id);
            assert.equal(captured.expected_source_sha256, rich.readme_sha256);
            assert.equal(
                createHash("sha256").update(captured.markdown).digest("hex"),
                captured.presentation_sha256,
            );
            await page
                .getByRole("navigation", {
                    name: "Main navigation",
                    exact: true,
                })
                .getByRole("link", { name: "Library", exact: true })
                .click();
            await page
                .getByRole("heading", { name: "Library", exact: true })
                .waitFor();
            await page
                .getByRole("button", { name: "Clear filters", exact: true })
                .click();
            await page
                .getByLabel("Find repositories", { exact: true })
                .fill("fixture/model");
            await page
                .getByRole("button", { name: "Apply filters", exact: true })
                .click();
            await page
                .locator(
                    `a[href="${ui}repositories/model/fixture/model#tab=overview"]`,
                )
                .click();
            const selected = page.getByRole("region", {
                name: "Selected publication",
                exact: true,
            });
            await selected.waitFor();
            await selected
                .getByText(rich.current_commit_sha, { exact: true })
                .waitFor();
            await selected
                .getByText(rich.current_publication_id, { exact: true })
                .waitFor();
            assert.deepEqual(await selected.locator("code").allTextContents(), [
                rich.current_commit_sha,
                rich.current_publication_id,
            ]);
            const card = page.getByRole("region", {
                name: "Archived README",
                exact: true,
            });
            const title = captured.markdown.match(/^# ([^\r\n]+)$/mu);
            assert(
                title,
                "The exact captured README has its owned primary heading",
            );
            await card
                .getByRole("heading", {
                    name: title[1],
                    exact: true,
                })
                .waitFor();
            assert.equal(
                await card
                    .locator(
                        "script,iframe,form,img,svg,style,object,embed,[onclick],[onerror]",
                    )
                    .count(),
                0,
            );
            assert.equal(
                await page.evaluate(
                    () =>
                        globalThis.fixtureExecuted === undefined &&
                        globalThis.browserCorpusExecuted === undefined,
                ),
                true,
            );
            const guide = card.getByRole("link", {
                name: "relative guide",
                exact: true,
            });
            assert.equal(
                await guide.getAttribute("href"),
                "https://huggingface.co/fixture/model/blob/" +
                    rich.current_commit_sha +
                    "/docs/guide.md",
            );
            assert.equal(await guide.getAttribute("target"), "_blank");
            assert.equal(
                await guide.getAttribute("rel"),
                "noopener noreferrer",
            );
            await card
                .getByRole("button", { name: "Sanitized source", exact: true })
                .click();
            assert.equal(
                await card
                    .getByRole("group", {
                        name: "Sanitized README source",
                        exact: true,
                    })
                    .textContent(),
                captured.markdown,
            );
            await page
                .getByRole("tab", { name: "Files & manifest", exact: true })
                .click();
            const table = page.getByRole("table", {
                name: "Manifest files",
                exact: true,
            });
            await table.waitFor();
            assert.equal(
                await table.locator("tbody tr").count(),
                manifest.file_count,
            );
            for (const file of manifest.files) {
                const row = table
                    .getByRole("rowheader", { name: file.path, exact: true })
                    .locator("..");
                assert.equal(
                    (await row.getByRole("cell").first().innerText()).trim(),
                    file.size.toLocaleString("en-US"),
                );
                await row
                    .getByText("Hashes and provenance", { exact: true })
                    .click();
                assert.equal(
                    (
                        await row
                            .getByText("Expected SHA256", { exact: true })
                            .locator("xpath=following-sibling::dd[1]")
                            .innerText()
                    ).trim(),
                    file.sha256,
                );
            }
            assert.equal(unsafeRequests, 0);
            evidence.rich_card_read = {
                archive_id: fixture.archive_id,
                commit_sha: rich.current_commit_sha,
                publication_id: rich.current_publication_id,
                expected_source_sha256: rich.readme_sha256,
                presentation_sha256: captured.presentation_sha256,
                manifest_rows: manifest.file_count,
                manifest_files: manifest.files.map(
                    ({ path, size, sha256 }) => ({ path, size, sha256 }),
                ),
            };
        } finally {
            page.off("request", observe);
        }
    });
    const record = evidence.cases.at(-1);
    assert.ok(
        record?.id === id && record.passed === true,
        "Stop after failed rich card read.",
    );
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
    const evidence = {
        version: null,
        cases: [],
        owned_descendants: [],
        page_errors: [],
        failed_responses: [],
    };
    const retained = new Map();
    const uiBodyWork = [],
        uiBodyResponses = new WeakSet(),
        uiBodyValues = new Map();
    function observeUiResponse(response, label) {
        assert.equal(
            uiBodyResponses.has(response),
            false,
            "One attempt per matched UI response",
        );
        uiBodyResponses.add(response);
        const attempt = {
            label,
            url: response.url(),
            method: response.request().method(),
            status: response.status(),
            bodyState: "pending",
            completedTransferClaimed: false,
        };
        evidence.configuration_body_attempts ??= [];
        evidence.configuration_body_attempts.push(attempt);
        assert.ok(evidence.configuration_body_attempts.length <= 4);
        uiBodyWork.push(
            (async () => {
                let bytes;
                try {
                    bytes = await response.body();
                } catch (error) {
                    attempt.bodyState = "unavailable";
                    attempt.failure = secretDiagnostic(error, credentials);
                    attempt.limit =
                        "UI decoded evidence is asserted separately; no completed-transfer or full-wire privacy claim";
                    return;
                }
                try {
                    assert.ok(bytes.length <= 1048576);
                    const body = JSON.parse(
                        new TextDecoder("utf-8", { fatal: true }).decode(bytes),
                    );
                    const encoded = JSON.stringify(body);
                    assert.equal(encoded.includes(credentials.password), false);
                    assert.equal(
                        encoded.includes(
                            Buffer.from(
                                credentials.username +
                                    ":" +
                                    credentials.password,
                            ).toString("base64"),
                        ),
                        false,
                    );
                    assert.match(label, /^[a-z0-9-]+$/u);
                    await writeFile(
                        path.join(
                            bindings.workspace,
                            `configuration-ui-${name}-${label}.private.json`,
                        ),
                        JSON.stringify(
                            {
                                url: response.url(),
                                method: response.request().method(),
                                status: response.status(),
                                body,
                            },
                            null,
                            2,
                        ) + "\n",
                        { flag: "wx", mode: 0o600 },
                    );
                    uiBodyValues.set(attempt, body);
                    attempt.bodyState = "captured";
                    attempt.bytes = bytes.length;
                    attempt.sha256 = createHash("sha256")
                        .update(bytes)
                        .digest("hex");
                } catch (error) {
                    attempt.bodyState = "invalid";
                    attempt.failure = secretDiagnostic(error, credentials);
                    evidence.infrastructure_failed = true;
                }
            })(),
        );
        return attempt;
    }
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
                id === "static-abort-drain"
                    ? 55000
                    : [
                            "workspaces-deep-refresh",
                            "exact-publication-refresh-history",
                            "library-type-and-repository-scopes",
                            "library-literal-id-tag-not-readme",
                            "library-current-and-retained-publications",
                            ...TAG_FILTER_ASSERTIONS,
                            ...TECHNICAL_FILTER_ASSERTIONS,
                            "library-total-page-coverage-and-zero",
                            "publication-files-locators-and-history",
                            "publication-model-dataset-static-evidence",
                            "readme-active-corpus-fails-closed",
                            "readme-blocked-resources-and-pinned-links",
                            "readme-sanitized-source-secret-and-format-bounds",
                            ...CONFIGURATION_UI_ASSERTIONS,
                            ...CONFIGURATION_CONFLICT_ASSERTIONS,
                        ].includes(id)
                      ? 45000
                      : 20000,
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
        page = await context.newPage();
        page.setDefaultTimeout(10000);
        page.setDefaultNavigationTimeout(15000);
        page.on("pageerror", (error) => {
            if (evidence.page_errors.length >= 64)
                evidence.browser_error_overflow = true;
            else
                evidence.page_errors.push(secretDiagnostic(error, credentials));
        });
        page.on("response", (response) => {
            if (response.status() < 500) return;
            if (evidence.failed_responses.length >= 128)
                evidence.browser_error_overflow = true;
            else
                evidence.failed_responses.push({
                    path: new URL(response.url()).pathname,
                    status: response.status(),
                });
        });
        // Settle WebKit's initial frame before the one external navigation.
        // A cancelled startup navigation is never certificate-refusal evidence.
        if (phase === "untrusted") await page.goto("about:blank");
        observer = nativeNetworkObserver({ trusted: bindings.origin });
        evidence.network_observation = observer.state;
        // No route/HAR/CDP interception: Playwright otherwise synthesizes Chromium
        // preflights. The positively owned guest network is separately confined.
        context.on("request", (request) => observer.observe(request.url()));
        const ui = bindings.prefix + "/ui/";
        if (phase === "untrusted") {
            await test("untrusted-certificate-refused", async () => {
                const target = bindings.origin + ui;
                const failedRequest = page
                    .waitForEvent("requestfailed", {
                        predicate: (request) =>
                            request.isNavigationRequest() &&
                            request.url() === target,
                        timeout: 15000,
                    })
                    .then(
                        (request) => ({
                            url: request.url(),
                            navigation: request.isNavigationRequest(),
                            errorText: request.failure()?.errorText,
                        }),
                        () => null,
                    );
                let caught;
                let response = null;
                try {
                    response = await page.goto(target);
                } catch (error) {
                    caught = error;
                }
                const failure = await failedRequest;
                evidence.certificate_navigation_diagnostic = secretDiagnostic(
                    caught ?? new Error("navigation-unexpectedly-succeeded"),
                    credentials,
                );
                evidence.certificate_transport_diagnostic = failure
                    ? secretDiagnostic(
                          new Error(failure.errorText),
                          credentials,
                      )
                    : null;
                evidence.certificate_navigation_attempts = 1;
                evidence.certificate_response_observed = response !== null;
                evidence.certificate_error_source = certificateRefusal(caught)
                    ? "navigation"
                    : "requestfailed";
                evidence.certificate_diagnostic = secretDiagnostic(
                    certificateRefusal(caught)
                        ? caught
                        : new Error(failure?.errorText),
                    credentials,
                );
                assert.ok(
                    certificateNavigationRefusal(
                        caught,
                        failure,
                        target,
                        response,
                    ),
                );
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
                    .getByRole("heading", { name: "Library", exact: true })
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
                assertBootstrapPaths(result.body.paths, bindings.prefix);
                evidence.bootstrap_paths = result.body.paths;
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
                assert.match(
                    result.body.configured_archive_id,
                    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u,
                );
                evidence.configured_archive_id =
                    result.body.configured_archive_id;
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
                        .getByRole("heading", { name: label, exact: true })
                        .waitFor();
                    assert.equal((await page.reload()).status(), 200);
                    await page
                        .getByRole("heading", { name: label, exact: true })
                        .waitFor();
                }
            });
            await test("history-back-forward", async () => {
                await page
                    .getByRole("navigation", {
                        name: "Main navigation",
                        exact: true,
                    })
                    .getByRole("link", { name: "Library", exact: true })
                    .click();
                await page
                    .getByRole("navigation", {
                        name: "Main navigation",
                        exact: true,
                    })
                    .getByRole("link", { name: "Operations", exact: true })
                    .click();
                await page.goBack();
                assert.equal(new URL(page.url()).pathname, ui + "library");
                await page
                    .getByRole("heading", { name: "Library", exact: true })
                    .waitFor();
                await page.goForward();
                assert.equal(new URL(page.url()).pathname, ui + "operations");
                await page
                    .getByRole("heading", { name: "Operations", exact: true })
                    .waitFor();
            });
            await test("exact-publication-refresh-history", async () => {
                assert.equal(
                    (
                        await page.goto(bindings.origin + ui + "library")
                    ).status(),
                    200,
                );
                await page
                    .getByLabel("Find repositories", { exact: true })
                    .fill("fixture/model");
                await page
                    .getByRole("button", { name: "Apply filters", exact: true })
                    .click();
                const repository = page.locator(
                    `a[href="${ui}repositories/model/fixture/model#tab=overview"]`,
                );
                await repository.waitFor();
                await repository.click();
                const selected = page.getByRole("region", {
                    name: "Selected publication",
                    exact: true,
                });
                await selected.waitFor();
                const pair = await selected.locator("code").allTextContents();
                assert.equal(pair.length, 2);
                const [commitSha, publicationId] = pair;
                assert.match(commitSha, /^[0-9a-f]{40}$/u);
                assert.match(publicationId, /^[0-9a-f]{32}$/u);
                const detail = new URL(page.url());
                assert.equal(detail.origin, bindings.origin);
                assert.ok(detail.pathname.startsWith(ui + "repositories/"));
                const target = detail.pathname.slice(
                    (ui + "repositories/").length,
                );
                assert.match(target, /^(model|dataset)\/[^/]+\/[^/]+$/u);
                const exact =
                    detail.pathname +
                    `#commit_sha=${commitSha}&publication_id=${publicationId}&tab=files`;
                await page.goto(bindings.origin + exact);
                await page.waitForFunction(
                    () =>
                        document
                            .getElementById("repository-tab-files")
                            ?.getAttribute("aria-selected") === "true",
                );
                assert.equal(
                    await page
                        .getByRole("tab", {
                            name: "Files & manifest",
                            exact: true,
                        })
                        .getAttribute("aria-selected"),
                    "true",
                );
                assert.deepEqual(
                    await selected.locator("code").allTextContents(),
                    pair,
                );
                assert.equal((await page.reload()).status(), 200);
                await selected.waitFor();
                assert.deepEqual(
                    await selected.locator("code").allTextContents(),
                    pair,
                );
                assert.equal(
                    new URL(page.url()).pathname + new URL(page.url()).hash,
                    exact,
                );
                await page
                    .getByRole("navigation", {
                        name: "Main navigation",
                        exact: true,
                    })
                    .getByRole("link", { name: "Library", exact: true })
                    .click();
                await page
                    .getByRole("heading", { name: "Library", exact: true })
                    .waitFor();
                await page.goBack();
                await selected.waitFor();
                assert.equal(
                    new URL(page.url()).pathname + new URL(page.url()).hash,
                    exact,
                );
                assert.deepEqual(
                    await selected.locator("code").allTextContents(),
                    pair,
                );
                await page.goForward();
                await page
                    .getByRole("heading", { name: "Library", exact: true })
                    .waitFor();
                evidence.exact_publication = {
                    path: detail.pathname,
                    target,
                    commit_sha: commitSha,
                    publication_id: publicationId,
                };
            });
            await libraryPublicationReadCases({
                page,
                bindings,
                evidence,
                test,
            });
            await configurationReadOnlyCases({
                page,
                bindings: {
                    ...bindings,
                    archiveId: evidence.configured_archive_id,
                },
                evidence,
                test,
                observeUiResponse,
            });
            await test("api-pagination", async () => {
                const endpoint =
                    bindings.prefix + "/api/v1/repositories?limit=1";
                const first = await browserRead(page, endpoint);
                assert.equal(first.status, 200);
                const firstPage = JSON.parse(first.text);
                const initial = envelope(firstPage).repositories;
                assert.equal(initial.length, 1);
                assert.ok(
                    typeof firstPage.next_cursor === "string" &&
                        firstPage.next_cursor.length > 0,
                );
                const second = await browserRead(
                    page,
                    endpoint +
                        "&cursor=" +
                        encodeURIComponent(firstPage.next_cursor),
                );
                assert.equal(second.status, 200);
                const following = envelope(
                    JSON.parse(second.text),
                ).repositories;
                assert.equal(following.length, 1);
                assert.notDeepEqual(following, initial);
                evidence.api_cursor_followed = true;
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
                const publication = evidence.exact_publication;
                assert.ok(publication);
                const api = bindings.prefix + "/api/v1";
                for (const endpoint of [
                    api + "/version",
                    api + "/capabilities",
                    api +
                        "/repositories/" +
                        publication.target +
                        "/publications/" +
                        publication.commit_sha +
                        "/" +
                        publication.publication_id +
                        "/card",
                ]) {
                    const row = await browserRead(page, endpoint);
                    assert.equal(row.status, 200);
                    assertApiHeaders(row.headers);
                    envelope(JSON.parse(row.text));
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
                            headers: Object.fromEntries(response.headers),
                            text: await response.text(),
                        });
                    }
                    return result;
                }, ui);
                for (const row of rows) {
                    assert.ok(row.status >= 400);
                    assert.ok(!row.type?.includes("text/html"));
                    assert.ok(!row.text.includes('<div id="root"'));
                    assertUiHeaders(row.headers);
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
                        referrerPolicy: "same-origin",
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
                        referrerPolicy: "same-origin",
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
                    assert.deepEqual(
                        capabilities.capabilities,
                        key === "writer" ? ["read", "write"] : ["read"],
                    );
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
                const validated = await nodeRequest(
                    fixedEndpoint(
                        bindings.origin,
                        bindings.prefix,
                        "/api/v1/config/validate",
                    ),
                    {
                        ca,
                        token: credentials.tokens.writer,
                        method: "POST",
                        body: {},
                    },
                );
                assert.equal(validated.status, 200);
                envelope(JSON.parse(validated.body));
                evidence.rest_classes = rows;
            });
            await test("credential-class-isolation", async () => {
                const rows = [];
                for (const [credential, token, suffix] of [
                    ["anonymous", undefined, "/api/v1/version"],
                    ["anonymous", undefined, "/ui/"],
                    ["anonymous", undefined, "/mcp/"],
                    ["writer", credentials.tokens.writer, "/mcp/"],
                    ["reader", credentials.tokens.reader, "/mcp/"],
                    [
                        "mcp_reader",
                        credentials.tokens.mcp_reader,
                        "/api/v1/version",
                    ],
                    ["mcp_reader", credentials.tokens.mcp_reader, "/ui/"],
                ]) {
                    const row = await nodeRequest(
                        fixedEndpoint(bindings.origin, bindings.prefix, suffix),
                        { ca, token },
                    );
                    assertCredentialRefusal(
                        row,
                        suffix === "/ui/"
                            ? "basic"
                            : credential === "anonymous" && suffix !== "/mcp/"
                              ? "both"
                              : "bearer",
                    );
                    rows.push({
                        credential,
                        path: bindings.prefix + suffix,
                        status: row.status,
                    });
                }
                const basic = await browserRead(
                    page,
                    bindings.prefix + "/mcp/",
                );
                assertCredentialRefusal(basic, "bearer");
                rows.push({
                    credential: "basic",
                    path: bindings.prefix + "/mcp/",
                    status: basic.status,
                });
                const readerWrite = await nodeRequest(
                    fixedEndpoint(
                        bindings.origin,
                        bindings.prefix,
                        "/api/v1/config/validate",
                    ),
                    {
                        ca,
                        token: credentials.tokens.reader,
                        method: "POST",
                        body: { candidate: {} },
                    },
                );
                assert.equal(readerWrite.status, 403);
                rows.push({
                    credential: "reader",
                    path: bindings.prefix + "/api/v1/config/validate",
                    status: readerWrite.status,
                });
                evidence.credential_class_refusals = rows;
            });
            await test("denied-basic-read-auth", async () => {
                const endpoint = fixedEndpoint(
                    bindings.origin,
                    bindings.prefix,
                    "/api/v1/version",
                );
                const rows = [];
                for (const probe of basicReadProbes(credentials)) {
                    try {
                        const response = await nodeRequest(endpoint, {
                            ca,
                            authorization: probe.authorization,
                            maximumResponseBytes: 4096,
                            agent: `hfcache-functional-node/${name}`,
                        });
                        rows.push({
                            ...basicReadRefusal(response, probe, credentials),
                            method: "GET",
                            path: endpoint.pathname,
                            origin: endpoint.origin,
                            transport: "trusted-node-https",
                        });
                    } catch {
                        throw new Error(
                            `Basic read refusal failed: ${probe.label}`,
                        );
                    }
                }
                assert.equal(
                    new Set(rows.map((row) => row.request_id)).size,
                    rows.length,
                );
                assert.equal(
                    new Set(rows.map((row) => row.problem_sha256)).size,
                    1,
                );
                // Partial AUTH-02: actual installed logs/hash-work/non-effect
                // proof remain separate. These13 GETs are not an auth flood.
                evidence.basic_read_refusals = rows;
            });
            await test("denied-basic-csrf", async () => {
                const rows = await page.evaluate(async (endpoint) => {
                    const result = [];
                    for (const kind of [
                        "missing-intent",
                        "text",
                        "form",
                        "multipart",
                    ]) {
                        const headers =
                            kind === "missing-intent"
                                ? { "Content-Type": "application/json" }
                                : { "X-Hfcache-Request": "1" };
                        let body = "{}";
                        if (kind === "text")
                            headers["Content-Type"] = "text/plain";
                        else if (kind === "form")
                            body = new globalThis.URLSearchParams({
                                candidate: "owned",
                            });
                        else if (kind === "multipart") {
                            body = new FormData();
                            body.set("candidate", "owned");
                        }
                        const response = await fetch(endpoint, {
                            method: "POST",
                            credentials: "same-origin",
                            redirect: "error",
                            referrerPolicy: "same-origin",
                            headers,
                            body,
                        });
                        result.push({
                            kind,
                            status: response.status,
                            headers: Object.fromEntries(response.headers),
                            problem: await response.json(),
                        });
                    }
                    return result;
                }, bindings.prefix + "/api/v1/config/validate");
                assert.equal(rows.length, 4);
                for (const row of rows) {
                    assert.equal(row.status, 403);
                    assert.equal(row.problem.code, "HFAPI010");
                    assert.match(row.problem.request_id, /^[0-9a-f]{32}$/u);
                    assertApiHeaders(row.headers);
                }
                // These pure-validation denials are partial AUTH-05 evidence;
                // cross-origin/Origin-shape and every unsafe route remain open.
                evidence.denied_basic_csrf = rows.map(
                    ({ kind, status, problem }) => ({
                        kind,
                        status,
                        code: problem.code,
                        request_id: problem.request_id,
                    }),
                );
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
                assertBootstrapPaths(row.body.paths, bindings.prefix);
                assert.deepEqual(row.body.paths, evidence.bootstrap_paths);
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
            await configurationConflictCases({
                browser,
                bindings,
                credentials,
                evidence,
                test,
                engine: name,
                observeNetwork: (url) => observer.observe(url),
            });
            await page.screenshot({
                path: path.join(
                    bindings.workspace,
                    `functional-${bindings.profile}-${bindings.prefix ? "prefixed" : "root"}-${name}.png`,
                ),
                fullPage: true,
            });
            await test("no-browser-errors", async () => {
                assert.notEqual(evidence.browser_error_overflow, true);
                assert.deepEqual(evidence.page_errors, []);
                assert.deepEqual(evidence.failed_responses, []);
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
        // ApiClient may abort after typed decode; settle the single passive
        // attempt after context close, without issuing a replacement request.
        await Promise.allSettled(uiBodyWork);
        for (const attempt of evidence.configuration_body_attempts ?? []) {
            if (attempt.bodyState === "captured" && attempt.verify) {
                try {
                    attempt.verify(uiBodyValues.get(attempt));
                    attempt.capturedBodyMatchedActualUI = true;
                } catch (error) {
                    attempt.bodyMatchFailure = secretDiagnostic(
                        error,
                        credentials,
                    );
                    evidence.infrastructure_failed = true;
                }
            }
        }
        evidence.configuration_body_observability = {
            attempted: uiBodyWork.length,
            captured: (evidence.configuration_body_attempts ?? []).filter(
                (row) => row.bodyState === "captured",
            ).length,
            unavailable: (evidence.configuration_body_attempts ?? []).filter(
                (row) => row.bodyState === "unavailable",
            ).length,
            fullWirePrivacyClaimed: false,
        };
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

export function selectedEngines(runtime) {
    const engines = ["chromium", "firefox", "webkit"];
    assert.ok(
        runtime !== null &&
            typeof runtime === "object" &&
            !Array.isArray(runtime),
    );
    if (!Object.hasOwn(runtime, "browser_engine")) return engines;
    assert.ok(
        typeof runtime.browser_engine === "string" &&
            engines.includes(runtime.browser_engine),
    );
    return [runtime.browser_engine];
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
    const engines = selectedEngines(runtime);
    const hasRunId = Object.hasOwn(runtime, "run_id");
    if (hasRunId) {
        assert.equal(typeof runtime.run_id, "string");
        assert.match(runtime.run_id, /^[0-9a-f]{32}$/u);
    }
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
    if (phase === "trusted")
        assert.deepEqual(
            Object.keys(bindings.untrusted.engines).sort(),
            [...engines].sort(),
        );
    if (phase === "trusted") {
        assert.equal(Object.hasOwn(bindings.untrusted, "run_id"), hasRunId);
        if (hasRunId) assert.equal(bindings.untrusted.run_id, runtime.run_id);
    }
    const report = {
        schema_version: 1,
        fixture_id: runtime.fixture_id,
        ...(hasRunId ? { run_id: runtime.run_id } : {}),
        profile: runtime.profile,
        prefix: runtime.prefix,
        asset_manifest_sha256: runtime.asset_manifest_sha256,
        engines: {},
    };
    process.once("SIGTERM", () => {
        interrupted = true;
        void activeServer?.close().catch(() => {});
    });
    for (const name of engines) {
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
