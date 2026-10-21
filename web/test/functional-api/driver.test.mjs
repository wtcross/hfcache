/** Pure guard checks supplement real shared-Caddy/browser acceptance. */
import assert from "node:assert/strict";
import test from "node:test";
import { mkdtemp, writeFile, lstat, rename, symlink } from "node:fs/promises";
import path from "node:path";
import { createServer, connect, constants as http2Constants } from "node:http2";
import { once } from "node:events";
import {
    certificateRefusal,
    secretDiagnostic,
    assertUiHeaders,
    protocolMessage,
    fixedEndpoint,
    nodeRequest,
    assertPhase,
    largestJavascript,
    zeroWindowProbe,
} from "./driver.mjs";

const CSP =
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'none'; worker-src 'none'";
const headers = () => ({
    "cache-control": "no-store",
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "content-security-policy": CSP,
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
    ]) {
        assert.equal(certificateRefusal(new Error(message)), false);
    }
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
