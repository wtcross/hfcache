/** Pure guard checks supplement real shared-Caddy/browser acceptance. */
import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, writeFile, lstat, rename, symlink } from "node:fs/promises";
import path from "node:path";
import { createServer, connect, constants as http2Constants } from "node:http2";
import { once } from "node:events";
import { request as httpRequest } from "node:http";
import { Duplex } from "node:stream";
import {
    certificateRefusal,
    certificateNavigationRefusal,
    secretDiagnostic,
    assertUiHeaders,
    assertApiHeaders,
    assertCredentialRefusal,
    assertBootstrapPaths,
    browserRead,
    protocolMessage,
    fixedEndpoint,
    nodeRequest,
    assertPhase,
    largestJavascript,
    zeroWindowProbe,
    selectedEngines,
    basicReadProbes,
    basicReadHeaders,
    basicReadRefusal,
    richCardRead,
    openLibraryDisclosure,
} from "./driver.mjs";

test("Library disclosure access stays within the named region and preserves an already open group", async () => {
    let open = false,
        clicks = 0;
    const page = {
        getByRole(role, options) {
            assert.equal(role, "region");
            assert.deepEqual(options, {
                name: "Repository library",
                exact: true,
            });
            return {
                getByText(label, options) {
                    assert.equal(label, "Filters and page size");
                    assert.deepEqual(options, { exact: true });
                    return {
                        evaluate: async (predicate) =>
                            predicate({
                                closest(selector) {
                                    assert.equal(selector, "details");
                                    return { open };
                                },
                            }),
                        async click() {
                            open = true;
                            clicks++;
                        },
                    };
                },
            };
        },
    };
    await openLibraryDisclosure(page, "Filters and page size");
    assert.equal(open, true);
    assert.equal(clicks, 1);
    await openLibraryDisclosure(page, "Filters and page size");
    assert.equal(open, true);
    assert.equal(
        clicks,
        1,
        "Reusing the helper must not close the entered form",
    );
});

test("internal engine selection preserves all engines by default and refuses malformed selectors", () => {
    assert.deepEqual(selectedEngines({}), ["chromium", "firefox", "webkit"]);
    for (const browser_engine of ["chromium", "firefox", "webkit"])
        assert.deepEqual(selectedEngines({ browser_engine }), [browser_engine]);
    for (const browser_engine of [
        undefined,
        null,
        false,
        true,
        [],
        {},
        "",
        "all",
        "Chromium",
        "unknown",
    ])
        assert.throws(() => selectedEngines({ browser_engine }));
    for (const runtime of [null, [], "chromium"])
        assert.throws(() => selectedEngines(runtime));
});

test("optional rich card reads require the explicit native engine and original fixture before any browser work", async () => {
    const argumentsFor = () => ({
        bindings: {
            profile: "native",
            browser_engine: "chromium",
            prefix: "",
            origin: "https://127.0.0.1:22443",
            asset_manifest: { build: { source_dirty: false } },
        },
        fixture: {
            schema_version: 1,
            archive_id: "8ac4089b-1960-429e-b67c-04c6fbd45cbb",
            rich: {
                model_repository: "model:fixture/model",
                current_commit_sha: "f".repeat(40),
                current_publication_id: "f".repeat(32),
                readme_sha256: "a".repeat(64),
            },
        },
        engine: "chromium",
        evidence: { cases: [] },
        page: { url: () => "https://127.0.0.1:22443/ui/operations" },
    });
    for (const change of [
        (args) => {
            args.bindings.profile = "rootless";
        },
        (args) => {
            delete args.bindings.browser_engine;
        },
        (args) => {
            args.engine = "firefox";
        },
        (args) => {
            args.fixture.schema_version = 2;
        },
        (args) => {
            args.fixture.archive_id = "unknown";
        },
        (args) => {
            args.fixture.rich.model_repository = "model:other/repository";
        },
        (args) => {
            args.fixture.rich.current_commit_sha = "unknown";
        },
        (args) => {
            args.fixture.rich.current_publication_id = "unknown";
        },
        (args) => {
            args.fixture.rich.readme_sha256 = "unknown";
        },
        (args) => {
            args.bindings.asset_manifest.build.source_dirty = true;
        },
        (args) => {
            args.bindings.prefix = "/outside";
        },
        (args) => {
            args.bindings.origin = "http://127.0.0.1:22443";
            args.page.url = () => "http://127.0.0.1:22443/ui/operations";
        },
        (args) => {
            args.page.url = () => "https://outside.invalid/ui/operations";
        },
    ]) {
        const args = argumentsFor();
        let entered = false;
        change(args);
        await assert.rejects(
            richCardRead({
                ...args,
                test: async () => {
                    entered = true;
                },
            }),
        );
        assert.equal(entered, false);
        assert.deepEqual(args.evidence.cases, []);
    }
    let named;
    await assert.rejects(
        richCardRead({
            ...argumentsFor(),
            test: async (id) => {
                named = id;
                throw new Error("unit intercept before browser work");
            },
        }),
        /unit intercept before browser work/u,
    );
    assert.equal(named, "rich-card-dom-and-pinned-files");
});

const CSP =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'none'; worker-src 'none'";
const headers = () => ({
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "content-security-policy": CSP,
});

test("bootstrap alias paths retain the configured prefix without accepting a forged effective prefix", () => {
    const paths = (prefix, configured = prefix) => ({
        public_prefix: configured,
        effective_prefix: prefix,
        ui_base: prefix + "/ui/",
        bootstrap: prefix + "/ui/bootstrap.json",
        api_base: prefix + "/api/v1",
        mcp_base: prefix + "/mcp/",
    });
    assertBootstrapPaths(paths(""), "");
    assertBootstrapPaths(paths("", "/management"), "");
    assertBootstrapPaths(paths("/management"), "/management");
    for (const changed of [
        { public_prefix: "/forged" },
        { effective_prefix: "/management" },
        { bootstrap: "//outside.invalid/ui/bootstrap.json" },
        { api_base: "/management/api/v1" },
        { mcp_base: "/mcp" },
    ])
        assert.throws(() =>
            assertBootstrapPaths({ ...paths(""), ...changed }, ""),
        );
    assert.throws(() =>
        assertBootstrapPaths(paths("/management", ""), "/management"),
    );
});

test("API and card success/error headers refuse HTML policy and public caching", () => {
    const api = {
        ...headers(),
        "content-security-policy": "frame-ancestors 'none'",
    };
    assertApiHeaders(api);
    for (const changed of [
        { "cache-control": "public, max-age=60" },
        { "content-security-policy": CSP },
        { "x-content-type-options": undefined },
        { "set-cookie": "session=unsafe" },
        { "access-control-allow-origin": "*" },
    ])
        assert.throws(() => assertApiHeaders({ ...api, ...changed }));
});

test("credential-class denials preserve Basic-only UI, bearer-only MCP and combined anonymous REST challenges", () => {
    for (const [kind, challenge] of Object.entries({
        basic: 'Basic realm="hfcache", charset="UTF-8"',
        bearer: 'Bearer realm="hfcache"',
        both: 'Basic realm="hfcache", charset="UTF-8", Bearer realm="hfcache"',
    })) {
        const row = {
            status: 401,
            headers: {
                "content-type": "application/json",
                "www-authenticate": challenge,
            },
        };
        assertCredentialRefusal(row, kind);
        for (const changed of [
            { status: 200 },
            { headers: { ...row.headers, location: "/ui/" } },
            { headers: { ...row.headers, "content-type": "text/html" } },
            { headers: { ...row.headers, "www-authenticate": "Basic" } },
        ])
            assert.throws(() =>
                assertCredentialRefusal({ ...row, ...changed }, kind),
            );
    }
    assert.throws(() =>
        assertCredentialRefusal({ status: 401, headers: {} }, "unknown"),
    );
});

test("Basic refusal vectors are finite and keep actual duplicate fields in Node's request encoder", async () => {
    const credentials = {
        username: "owned-unit-login",
        password: "private-unit-password",
    };
    const probes = basicReadProbes(credentials);
    assert.equal(probes.length, 13);
    assert.equal(new Set(probes.map((probe) => probe.label)).size, 13);
    const byLabel = Object.fromEntries(
        probes.map((probe) => [probe.label, probe.authorization]),
    );
    assert.equal(byLabel["oversized-authorization"][0].length, 8193);
    assert.equal(
        Buffer.from(byLabel["oversized-user"][0].slice(6), "base64").indexOf(
            58,
        ),
        129,
    );
    assert.equal(
        Buffer.from(
            byLabel["oversized-password"][0].slice(6),
            "base64",
        ).subarray(credentials.username.length + 1).length,
        1025,
    );
    assert.equal(byLabel["duplicate-headers"].length, 2);
    const target = new URL("https://127.0.0.1:19443/api/v1/version");
    const chunks = [];
    const socket = new Duplex({
        read() {},
        write(chunk, _encoding, done) {
            chunks.push(Buffer.from(chunk));
            done();
        },
    });
    const request = httpRequest({
        hostname: "127.0.0.1",
        path: target.pathname,
        headers: basicReadHeaders(target, byLabel["duplicate-headers"]),
        createConnection: () => socket,
    });
    request.on("error", () => {});
    try {
        request.end();
        await once(request, "finish");
        const wire = Buffer.concat(chunks).toString("ascii");
        assert.ok(wire.startsWith("GET /api/v1/version HTTP/1.1\r\n"));
        assert.equal(
            wire
                .split("\r\n")
                .filter((line) => line.startsWith("Authorization: ")).length,
            2,
        );
        assert.ok(wire.includes("\r\nHost: 127.0.0.1:19443\r\n"));
    } finally {
        request.destroy();
        socket.destroy();
    }
    for (const values of [
        ["Basic x\r\nInjected: x"],
        ["x".repeat(8194)],
        ["a", "b", "c"],
        "Basic x",
    ])
        assert.throws(() => basicReadHeaders(target, values));
});

test("Basic refusal projections require exact private uniform401 and never retain reflected secrets", () => {
    const credentials = {
        username: "owned-unit-login",
        password: "private-unit-password",
    };
    const probes = basicReadProbes(credentials);
    const problem = {
        request_id: "a".repeat(32),
        code: "HFAPI001",
        message: "Not authenticated",
        exit_code: 10,
    };
    const row = {
        status: 401,
        headers: {
            ...headers(),
            "content-type": "application/json",
            "content-security-policy": "frame-ancestors 'none'",
            "www-authenticate": 'Basic realm="hfcache", charset="UTF-8"',
        },
        body: Buffer.from(JSON.stringify(problem)),
    };
    for (const probe of probes) {
        const current = {
            ...row,
            headers: {
                ...row.headers,
                "www-authenticate":
                    probe.label === "missing"
                        ? 'Basic realm="hfcache", charset="UTF-8", Bearer realm="hfcache"'
                        : row.headers["www-authenticate"],
            },
        };
        const proof = basicReadRefusal(current, probe, credentials);
        assert.equal(proof.status, 401);
        assert.equal(proof.code, "HFAPI001");
        assert.ok(!JSON.stringify(proof).includes(credentials.password));
        assert.deepEqual(Object.keys(proof).sort(), [
            "authorization_fields",
            "body_bytes",
            "body_sha256",
            "code",
            "label",
            "problem_sha256",
            "request_id",
            "status",
        ]);
    }
    const probe = probes.find((value) => value.label === "duplicate-headers");
    for (const changed of [
        { status: 200 },
        { status: 413 },
        { status: 429 },
        { body: Buffer.from(JSON.stringify({ ...problem, code: "HFAPI002" })) },
        {
            body: Buffer.from(
                JSON.stringify({ ...problem, message: credentials.password }),
            ),
        },
        {
            body: Buffer.from(
                JSON.stringify({ ...problem, extra: "unexpected" }),
            ),
        },
        {
            body: Buffer.from(
                JSON.stringify({
                    ...problem,
                    request_id: [problem.request_id],
                }),
            ),
        },
        { body: Buffer.alloc(4097) },
        { body: Buffer.from([255]) },
        { body: Buffer.from(credentials.password) },
        { headers: { ...row.headers, "x-reflection": probe.authorization[0] } },
        {
            headers: {
                ...row.headers,
                "x-reflection": probe.authorization[0].slice(6),
            },
        },
        {
            headers: {
                ...row.headers,
                "x-reflection": Buffer.from(credentials.password).toString(
                    "base64",
                ),
            },
        },
        { headers: { ...row.headers, "cache-control": "public" } },
    ]) {
        assert.throws(
            () => basicReadRefusal({ ...row, ...changed }, probe, credentials),
            (error) =>
                error.message === "Basic read refusal was not proven." &&
                !error.message.includes(credentials.password),
        );
    }
});

test("owned browser reads cannot select another origin or inject authentication headers", async () => {
    let evaluated = false;
    const page = {
        url: () => "https://127.0.0.1:48209/ui/library",
        evaluate: async () => {
            evaluated = true;
        },
    };
    for (const endpoint of [
        "https://outside.invalid/",
        "//outside.invalid/",
        "/\\outside.invalid/",
        "/ui/#fragment",
    ])
        await assert.rejects(browserRead(page, endpoint));
    for (const headers of [
        { Authorization: "Basic secret" },
        { COOKIE: "secret" },
        { Origin: "https://outside.invalid" },
    ])
        await assert.rejects(browserRead(page, "/api/v1/version", headers));
    assert.equal(evaluated, false);
    await browserRead(page, "/management/api/v1/repositories?limit=1", {
        "X-Forwarded-Prefix": "/forged",
    });
    assert.equal(evaluated, true);
});

test("stall probes select actual largest JavaScript and refuse insecure origins before credentials", async () => {
    const small = {
        path: "assets/small-12345678.js",
        bytes: 20,
        mime: "text/javascript",
    };
    const large = {
        path: "assets/large-12345678.js",
        bytes: 200000,
        mime: "text/javascript",
    };
    assert.deepEqual(
        largestJavascript({
            members: [
                small,
                { path: "assets/style.css", bytes: 900000, mime: "text/css" },
                large,
            ],
        }),
        large,
    );
    assert.throws(() => largestJavascript({ members: [] }));
    for (const origin of [
        "http://127.0.0.1:48209",
        "https://attacker.invalid",
        "https://user:password@127.0.0.1:48209",
    ])
        await assert.rejects(
            zeroWindowProbe(
                new URL(origin + "/ui/assets/main.js"),
                {},
                undefined,
                "chromium",
                "cancel",
            ),
        );
});

test(
    "owned credential-free HTTP2 transport actually blocks DATA with acknowledged zero stream window",
    { timeout: 5000 },
    async () => {
        // Supplemental Node protocol evidence only: this h2c fixture is not API,
        // Caddy, TLS or browser authentication acceptance and carries no credential.
        const server = createServer();
        let writeCompleted = false,
            remoteWindow,
            serverStream,
            client,
            request;
        server.on("stream", (stream) => {
            serverStream = stream;
            stream.on("error", () => {});
            remoteWindow = stream.session.remoteSettings.initialWindowSize;
            stream.respond({ ":status": 200 });
            stream.write(Buffer.alloc(65536), () => {
                writeCompleted = true;
            });
        });
        await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
        let timer;
        try {
            client = connect(`http://127.0.0.1:${server.address().port}`, {
                settings: { initialWindowSize: 0, enablePush: false },
            });
            client.on("error", () => {});
            timer = setTimeout(() => client.destroy(), 3000);
            await once(client, "localSettings");
            request = client.request({ ":path": "/owned-protocol-fixture" });
            request.on("error", () => {});
            let bytes = 0;
            request.on("data", (chunk) => {
                bytes += chunk.length;
            });
            await once(request, "response");
            assert.equal(remoteWindow, 0);
            assert.equal(request.state.localWindowSize, 0);
            assert.equal(bytes, 0);
            assert.equal(writeCompleted, false);
            const closed = once(request, "close");
            request.close(http2Constants.NGHTTP2_CANCEL);
            await closed;
        } finally {
            clearTimeout(timer);
            request?.destroy();
            serverStream?.destroy();
            client?.destroy();
            await new Promise((resolve) => server.close(resolve));
        }
        assert.equal(server.listening, false);
    },
);

test("phase corroboration binds the same owned inode and exact public phase", async () => {
    const workspace = await mkdtemp(
        path.join(process.cwd(), ".artifacts/functional-phase-"),
    );
    const filename = path.join(workspace, "browser-phase.txt");
    await writeFile(filename, "untrusted\n", { mode: 0o644 });
    const facts = await lstat(filename);
    const runtime = {
        phase_path: filename,
        phase_identity: { device: facts.dev, inode: facts.ino },
    };
    await assertPhase(runtime, "untrusted", workspace);
    await assert.rejects(assertPhase(runtime, "trusted", workspace));
    await writeFile(filename, "trusted\n");
    await assertPhase(runtime, "trusted", workspace);
    await rename(filename, filename + ".original");
    await writeFile(filename, "trusted\n");
    await assert.rejects(assertPhase(runtime, "trusted", workspace));
    await rename(filename, filename + ".replacement");
    await symlink(filename + ".original", filename);
    await assert.rejects(assertPhase(runtime, "trusted", workspace));
});

test("exact UI headers do not accept public caching, CDN, inline code or credential reflection", () => {
    assertUiHeaders(headers());
    for (const [name, value] of [
        ["cache-control", "public, max-age=3600"],
        ["content-security-policy", CSP + "; script-src 'unsafe-inline'"],
        ["referrer-policy", "unsafe-url"],
        ["x-content-type-options", ""],
        ["set-cookie", "credential=unsafe"],
        ["access-control-allow-origin", "*"],
    ])
        assert.throws(() => assertUiHeaders({ ...headers(), [name]: value }));
    assertUiHeaders(
        { ...headers(), "cache-control": "private, max-age=3600, immutable" },
        "private, max-age=3600, immutable",
    );
});

test("specific certificate signatures are distinct from arbitrary network failure", () => {
    for (const message of [
        "net::ERR_CERT_AUTHORITY_INVALID",
        "SEC_ERROR_UNKNOWN_ISSUER",
        "Unacceptable TLS certificate",
    ]) {
        assert.equal(certificateRefusal(new Error(message)), true);
    }
    for (const message of [
        "timeout",
        "ECONNREFUSED",
        "net::ERR_CONNECTION_RESET",
        "Navigation interrupted",
        "certificate unavailable",
        "Operation was cancelled; maybe frame was detached?",
    ]) {
        assert.equal(certificateRefusal(new Error(message)), false);
    }
});

test("certificate refusal requires the exact failed navigation and no HTTP response", () => {
    const target = "https://127.0.0.1:19443/ui/";
    const cancelled = new Error(
        "Operation was cancelled; maybe frame was detached?",
    );
    const failure = {
        url: target,
        navigation: true,
        errorText: "Unacceptable TLS certificate",
    };
    assert.equal(
        certificateNavigationRefusal(cancelled, failure, target, null),
        true,
    );
    for (const [error, observed, response] of [
        [cancelled, { ...failure, errorText: "Operation was cancelled" }, null],
        [cancelled, { ...failure, url: target + "other" }, null],
        [cancelled, { ...failure, navigation: false }, null],
        [undefined, failure, null],
        [cancelled, null, null],
        [cancelled, failure, { status: 401 }],
    ])
        assert.equal(
            certificateNavigationRefusal(error, observed, target, response),
            false,
        );
});

test("credentials and all token forms are scrubbed before bounded diagnostic retention", () => {
    const credentials = {
        username: "fixture-admin-user",
        password: "fixture-pass-:word-unique",
        tokens: {
            reader: "reader-token-long-unique-0123456789",
            writer: "writer-token-long-unique-9876543210",
        },
    };
    const values = [
        credentials.username,
        credentials.password,
        ...Object.values(credentials.tokens),
    ];
    const text = values
        .flatMap((value) => [
            value,
            encodeURIComponent(value),
            Buffer.from(value).toString("base64"),
        ])
        .join(" ");
    const result = secretDiagnostic(new Error(text), credentials);
    for (const value of values) assert.ok(!result.message.includes(value));
    for (const token of Object.values(credentials.tokens))
        assert.ok(
            !result.message.includes(Buffer.from(token).toString("base64")),
        );
    assert.ok(result.message.length <= 8192);
});

test("named fixture endpoints preserve exact same origin and prefix", () => {
    const target = fixedEndpoint(
        "https://127.0.0.1:48209",
        "/management",
        "/api/v1/capabilities",
    );
    assert.equal(target.origin, "https://127.0.0.1:48209");
    assert.equal(target.pathname, "/management/api/v1/capabilities");
    for (const prefix of ["//attacker.invalid", "/other", "/management/.."]) {
        assert.throws(() =>
            fixedEndpoint("https://127.0.0.1:48209", prefix, "/api/v1/version"),
        );
    }
    for (const suffix of [
        "//attacker.invalid/api",
        "/api/../outside",
        "/api\\outside",
        "/api?secret",
        "/api#secret",
    ]) {
        assert.throws(() =>
            fixedEndpoint("https://127.0.0.1:48209", "", suffix),
        );
    }
    assert.throws(() =>
        fixedEndpoint("https://attacker.invalid:48209", "", "/api/v1/version"),
    );
});

test("plaintext negative probes cannot carry any credential or request body", async () => {
    const target = new URL("http://127.0.0.1:48209/ui/");
    await assert.rejects(
        nodeRequest(target, { token: "test-only-no-transmission" }),
    );
    await assert.rejects(nodeRequest(target, { method: "POST", body: {} }));
    await assert.rejects(nodeRequest(target, { authorization: [] }));
    const secure = new URL("https://127.0.0.1:48209/api/v1/version");
    await assert.rejects(
        nodeRequest(secure, { authorization: [], method: "POST" }),
    );
    await assert.rejects(
        nodeRequest(secure, { authorization: [], token: "never-transmitted" }),
    );
    await assert.rejects(
        nodeRequest(secure, { maximumResponseBytes: 8 * 1024 * 1024 + 1 }),
    );
    await assert.rejects(nodeRequest(new URL("https://attacker.invalid/ui/")));
});

test("actual MCP JSON and SSE framing must preserve one exact original request id", () => {
    const value = { jsonrpc: "2.0", id: 7, result: { tools: [] } };
    assert.deepEqual(
        protocolMessage(
            Buffer.from(JSON.stringify(value)),
            "application/json",
            7,
        ),
        value.result,
    );
    assert.deepEqual(
        protocolMessage(
            Buffer.from(
                "event: message\ndata: " + JSON.stringify(value) + "\n\n",
            ),
            "text/event-stream",
            7,
        ),
        value.result,
    );
    for (const body of [
        { ...value, id: 8 },
        { ...value, error: { code: -1 } },
        { ...value, jsonrpc: "1.0" },
    ])
        assert.throws(() =>
            protocolMessage(
                Buffer.from(JSON.stringify(body)),
                "application/json",
                7,
            ),
        );
    assert.throws(() =>
        protocolMessage(
            Buffer.from(
                "data: " +
                    JSON.stringify(value) +
                    "\ndata: " +
                    JSON.stringify(value) +
                    "\n",
            ),
            "text/event-stream",
            7,
        ),
    );
    assert.throws(() =>
        protocolMessage(Buffer.from([0xff]), "application/json", 7),
    );
    assert.throws(() => protocolMessage(Buffer.from("{}"), "text/html", 7));
});
