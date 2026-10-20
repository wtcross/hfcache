/** Unit metadata refusals supplement the real guest/browser sandbox proof. */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
import { createInterface } from "node:readline";
import test from "node:test";
import {
    commandProof,
    assertVersionPayload,
    assertApplicationIdentity,
    descendantsClosed,
    parseStatus,
    parseStat,
    classifyProcess,
    ownedDescendants,
    ownedProcessIdentities,
    ownedCleanupInventory,
    processIdentity,
    processProof,
    requireUnprivileged,
    safeDiagnostic,
    nativeNetworkObserver,
    assertNativeNetworkObservation,
} from "./sandbox.mjs";

const STATUS =
    "Name:\towned\nState:\tS (sleeping)\nPPid:\t42\nUid:\t1000\t1000\t1000\t1000\nCapEff:\t0000000000000000\nNoNewPrivs:\t1\nSeccomp:\t2\n";
const proof = () => ({
    kind: "live",
    status: parseStatus(STATUS),
    command: commandProof("/owned/chrome\0--type=renderer\0"),
});
const CHROME = "/ms-playwright/chromium-1248/chrome-linux64/chrome";

test("passive origin observer records bounded origin facts without URL credentials/query/path", () => {
    const origins = {
        trusted: "https://127.0.0.1:20101",
        foreign: "https://127.0.0.1:20102",
        untrusted: "https://127.0.0.1:20103",
    };
    const observer = nativeNetworkObserver(origins);
    for (const origin of Object.values(origins))
        observer.observe(origin + "/private-path?secret-query=never-retain");
    assertNativeNetworkObservation(observer.state);
    assert.equal(observer.state.request_interception, false);
    const text = JSON.stringify(observer.state);
    assert.ok(!text.includes("private-path") && !text.includes("secret-query"));
    for (const bad of [
        "not a URL",
        "https://private-user:private-password@127.0.0.1:20101/path?hidden=yes",
        "https://external-secret-host.invalid/",
        "http://127.0.0.1:20101/",
        "x".repeat(4097),
    ]) {
        const badObserver = nativeNetworkObserver(origins);
        badObserver.observe(bad);
        assert.throws(() => {
            assertNativeNetworkObservation(badObserver.state);
        });
        const badText = JSON.stringify(badObserver.state);
        for (const forbidden of [
            "private-user",
            "private-password",
            "external-secret-host",
            "hidden=yes",
        ])
            assert.ok(!badText.includes(forbidden));
    }
    const excess = nativeNetworkObserver(origins);
    for (let index = 0; index < 257; index += 1)
        excess.observe(origins.trusted);
    assert.equal(excess.state.observations.length, 256);
    assert.throws(() => {
        assertNativeNetworkObservation(excess.state);
    });
});

test("the exact pinned Chromium title is observed lossy metadata, never reconstructed argv", () => {
    const title = `${CHROME} --type=renderer --top-chrome-webui --lang=en-US`;
    const value = commandProof(title + "\0");
    assert.equal(value.representation, "chromium-process-title");
    assert.deepEqual(value.arguments, [title]);
    assert.equal(value.raw_command_line, title + "\0");
    assert.equal(value.renderer, true);
    assert.equal(value.original_argument_boundaries_recoverable, false);
    assert.equal(value.title_may_be_truncated, true);
    assert.equal(value.flag_check_scope, "observed-title-only");
    assert.equal(value.observed_disabling_flags_absent, true);
    assert.equal(value.disabling_flags_absent, undefined);
    assert.equal(commandProof(`${CHROME}\0--type=renderer\0`).renderer, true);
    for (const raw of [
        "/unknown/chrome --type=renderer\0",
        `${CHROME}-other --type=renderer\0`,
        `${CHROME} --type=renderer\0--lang=en\0`,
        `${CHROME}  --type=renderer\0`,
        `${CHROME} --type=renderer \0`,
        `${CHROME}\t--type=renderer\0`,
        `${CHROME} --type=renderer --name='ambiguous value'\0`,
        `${CHROME} --type=renderer --name=ambiguous\\ value\0`,
        `${CHROME} --type=unknown\0`,
        `${CHROME} --type=renderer --type=utility\0`,
        `${CHROME} --value=--type=renderer\0`,
    ])
        assert.throws(() => {
            commandProof(raw);
        });
});

test("actual owned Node process.title rewriting exercises presentation only, not Chromium acceptance", async () => {
    const title = `${CHROME} --type=renderer --lang=en-US`;
    const child = spawn(
        process.execPath,
        [
            "-e",
            "process.title=process.argv[1];process.stdout.write('ready\\n');process.stdin.resume()",
            title,
            "x".repeat(2048),
        ],
        { stdio: ["pipe", "pipe", "ignore"] },
    );
    const closed = once(child, "close");
    const lines = createInterface({ input: child.stdout });
    try {
        assert.deepEqual(
            await once(lines, "line", {
                signal: globalThis.AbortSignal.timeout(5000),
            }),
            ["ready"],
        );
        const value = await processProof(child.pid);
        assert.equal(value.pid, child.pid);
        assert.equal(value.status.parent_pid, process.pid);
        assert.equal(value.command.representation, "chromium-process-title");
        assert.equal(value.command.renderer, true);
        assert.deepEqual(value.command.arguments, [title]);
        child.stdin.end();
        await closed;
        assert.equal(await descendantsClosed([value]), true);
    } finally {
        if (child.exitCode === null && child.signalCode === null)
            child.kill("SIGTERM");
        await closed;
        lines.close();
    }
});

test("actual unrelated spaced process title gets cleanup identity without sandbox authority", async () => {
    const child = spawn(
        process.execPath,
        [
            "-e",
            "process.title='owned unrelated native browser title';process.stdout.write('ready\\n');process.stdin.resume()",
            "x".repeat(2048),
        ],
        { stdio: ["pipe", "pipe", "ignore"] },
    );
    const closed = once(child, "close");
    const lines = createInterface({ input: child.stdout });
    try {
        assert.deepEqual(
            await once(lines, "line", {
                signal: globalThis.AbortSignal.timeout(5000),
            }),
            ["ready"],
        );
        await assert.rejects(processProof(child.pid));
        const identity = await processIdentity(child.pid);
        assert.equal(identity.pid, child.pid);
        assert.equal(identity.status.parent_pid, process.pid);
        assert.equal(identity.kind, "cleanup-identity");
        assert.equal(identity.authority, "cleanup-only");
        assert.equal("command" in identity, false);
        assert.throws(() => {
            requireUnprivileged(identity);
        });
        const descendants = await ownedProcessIdentities(process.pid);
        assert.ok(
            descendants.some(
                (value) =>
                    value.pid === identity.pid &&
                    value.start_ticks === identity.start_ticks &&
                    value.kind === "cleanup-identity",
            ),
        );
        let completed = false;
        const drain = descendantsClosed([identity]).then((value) => {
            completed = true;
            return value;
        });
        await new Promise((resolve) => {
            setTimeout(resolve, 100);
        });
        assert.equal(completed, false);
        child.stdin.end();
        await closed;
        assert.equal(await drain, true);
    } finally {
        if (child.exitCode === null && child.signalCode === null)
            child.kill("SIGTERM");
        await closed;
        lines.close();
    }
});

test("zombies require corroborated stable identity and state; live empty argv refuses", () => {
    const before = { pid: 50, parent_pid: 42, start_ticks: "100", state: "Z" };
    const status = { parent_pid: 42, state: "Z" };
    assert.deepEqual(classifyProcess(before, before, status, ""), {
        kind: "zombie",
        command: null,
    });
    for (const delta of [
        { pid: 51 },
        { parent_pid: 41 },
        { start_ticks: "101" },
    ])
        assert.throws(() => {
            classifyProcess(before, { ...before, ...delta }, status, "");
        });
    assert.throws(() => {
        classifyProcess(before, before, { ...status, parent_pid: 1 }, "");
    });
    assert.equal(
        classifyProcess({ ...before, state: "R" }, before, status, ""),
        null,
    );
    assert.equal(
        classifyProcess(before, before, status, "unexpected-command\0"),
        null,
    );
    const live = { ...before, state: "R" };
    assert.throws(() => {
        classifyProcess(live, live, { ...status, state: "R" }, "");
    }, /Empty command refused: pid=50 start=100 parent=42 stat_before=R stat_after=R status=R/);
    assert.throws(() => {
        commandProof("");
    });
    assert.throws(() => {
        requireUnprivileged({ ...proof(), kind: "zombie" });
    });
});

test("stat identity uses the kernel PID, parent and start-time fields", () => {
    const text = `50 (owned ) comm) S 42 ${Array(17).fill("0").join(" ")} 100 0\n`;
    assert.deepEqual(parseStat(text, 50), {
        pid: 50,
        parent_pid: 42,
        state: "S",
        start_ticks: "100",
    });
    for (const value of [
        "",
        text.replace(" S ", " ? "),
        text.replace(" 100 ", " 100x "),
        text.replace(" S 42 ", " S 4x "),
    ])
        assert.throws(() => {
            parseStat(value, 50);
        });
    assert.throws(() => {
        parseStat(text, 51);
    });
});

test("an actual owned zombie is retained and is not drained until its parent reaps it", async () => {
    const child = spawn(
        "/usr/bin/python3",
        [
            "-I",
            "-S",
            "-c",
            [
                "import os,sys",
                "pid=os.fork()",
                "if pid==0: os._exit(0)",
                "print(pid,flush=True)",
                "sys.stdin.readline()",
                "os.waitpid(pid,0)",
                "print('reaped',flush=True)",
                "sys.stdin.readline()",
            ].join("\n"),
        ],
        { stdio: ["pipe", "pipe", "ignore"] },
    );
    const closed = once(child, "close");
    const lines = createInterface({ input: child.stdout });
    try {
        const [first] = await once(lines, "line", {
            signal: globalThis.AbortSignal.timeout(5000),
        });
        const pid = Number(first);
        assert.ok(Number.isSafeInteger(pid) && pid > 1);
        let zombie;
        const expires = Date.now() + 5000;
        do {
            zombie = await processProof(pid);
            if (zombie.kind === "zombie") break;
            await new Promise((resolve) => {
                setTimeout(resolve, 10);
            });
        } while (Date.now() < expires);
        assert.equal(zombie.kind, "zombie");
        assert.equal(zombie.state, "Z");
        assert.equal(zombie.status.state, "Z");
        assert.equal(zombie.status.parent_pid, child.pid);
        assert.equal(zombie.command, null);
        const descendants = await ownedDescendants(child.pid);
        assert.ok(
            descendants.some(
                (value) =>
                    value.pid === pid &&
                    value.start_ticks === zombie.start_ticks &&
                    value.kind === "zombie",
            ),
        );
        let completed = false;
        const drain = descendantsClosed([zombie]).then((value) => {
            completed = true;
            return value;
        });
        await new Promise((resolve) => {
            setTimeout(resolve, 100);
        });
        assert.equal(completed, false);
        const reaped = once(lines, "line", {
            signal: globalThis.AbortSignal.timeout(5000),
        });
        child.stdin.write("reap\n");
        assert.deepEqual(await reaped, ["reaped"]);
        assert.equal(await drain, true);
    } finally {
        // Reap the exact fork even if an assertion failed before the normal request.
        child.stdin.end("reap\nexit\n");
        await closed;
        lines.close();
    }
});

test("version checks the installed application's real four-key payload", () => {
    const payload = {
        schema_version: 1,
        envelope: {
            data: {
                application: "0.15.4",
                huggingface_hub: "1.8.0",
                python: "3.14.5",
                transfer_backend: "http",
            },
        },
    };
    assertVersionPayload(payload, "0.15.4");
    for (const replacement of [
        { version: "0.15.4" },
        { ...payload.envelope.data, application: "different" },
        { ...payload.envelope.data, huggingface_hub: "" },
        { ...payload.envelope.data, unexpected: "extra" },
    ])
        assert.throws(() => {
            assertVersionPayload(
                { ...payload, envelope: { data: replacement } },
                "0.15.4",
            );
        });
});

test("application identity refuses trailing line endings and non-printable bytes", () => {
    assertApplicationIdentity("0.15.4");
    for (const invalid of [
        "",
        "0.15.4\n",
        "0.15.4\r\n",
        "0.15.4\u0000",
        "snow\u2603",
        "x".repeat(129),
    ])
        assert.throws(() => {
            assertApplicationIdentity(invalid);
        });
});

test("bounded diagnostics scrub plaintext, encoded credentials, headers and hashes before truncation", () => {
    const credentials = {
        username: "owned-secret-user",
        password: "owned:/+?= password",
    };
    const pair = Buffer.from(
        `${credentials.username}:${credentials.password}`,
    ).toString("base64");
    const encoded = encodeURIComponent(credentials.password);
    const password64 = Buffer.from(credentials.password).toString("base64");
    const error = new Error(
        [
            "Protocol error: owned launch refused",
            credentials.password,
            encoded,
            pair,
            password64,
            `credentials=${JSON.stringify(credentials)}`,
            "Authorization: Basic UNRELATEDSECRETVALUE",
            "Bearer UNRELATEDTOKENVALUE",
            "$argon2id$v=19$m=65536,t=3,p=1$SALTVALUE$HASHVALUE",
            "https://otheruser:otherpassword@127.0.0.1/",
        ].join("\n"),
    );
    error.stack = "UNCONTROLLEDSTACK";
    const value = JSON.stringify(safeDiagnostic(error, credentials));
    for (const forbidden of [
        credentials.username,
        credentials.password,
        encoded,
        pair,
        password64,
        "UNRELATEDSECRETVALUE",
        "UNRELATEDTOKENVALUE",
        "SALTVALUE",
        "HASHVALUE",
        "otherpassword",
        "UNCONTROLLEDSTACK",
    ])
        assert.ok(!value.includes(forbidden));
    assert.ok(value.includes("owned launch refused"));
    assert.ok(
        safeDiagnostic(new Error("x".repeat(9000))).message.length <= 8192,
    );
    assert.equal(
        safeDiagnostic(new Error("x".repeat(65_537))).message,
        "oversized diagnostic withheld",
    );
});

test("source-shaped nonroot zero-capability NNP metadata passes", () => {
    requireUnprivileged(proof());
});

for (const flag of [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-seccomp-filter-sandbox",
    "--disable-namespace-sandbox",
    "--single-process",
]) {
    test(`actual disabling argument ${flag} refuses`, () => {
        assert.throws(() => {
            commandProof(`/owned/chrome\0${flag}\0`);
        });
        assert.throws(() => {
            commandProof(`/owned/chrome\0${flag}=true\0`);
        });
        for (const suffix of ["", "=true"]) {
            assert.throws(() => {
                commandProof(`${CHROME} --type=renderer ${flag}${suffix}\0`);
            });
            assert.throws(() => {
                commandProof(
                    `${CHROME} --type=renderer --top-chrome-webui ${flag}${suffix} --lang=en\0`,
                );
            });
        }
    });
}

for (const [field, replacement] of [
    ["Uid", "0\t0\t0\t0"],
    ["CapEff", "0000000000000001"],
    ["NoNewPrivs", "0"],
]) {
    test(`unsafe ${field} metadata refuses`, () => {
        const value = proof();
        value.status = parseStatus(
            STATUS.replace(
                new RegExp(`${field}:.*`),
                `${field}:\t${replacement}`,
            ),
        );
        assert.throws(() => {
            requireUnprivileged(value);
        });
    });
}

test("missing, duplicate, oversized and malformed proc metadata refuses", () => {
    for (const value of [
        "",
        STATUS + "Uid:\t1000\t1000\t1000\t1000\n",
        STATUS.replace("0000000000000000", "bad"),
        STATUS + "x".repeat(65_536),
    ]) {
        assert.throws(() => {
            parseStatus(value);
        });
    }
});

test("an exact owned child is observed live and its real exit is then proved", async () => {
    const child = spawn(process.execPath, ["-e", "process.stdin.resume()"], {
        stdio: ["pipe", "ignore", "ignore"],
    });
    const closed = new Promise((resolve) => {
        child.once("close", resolve);
    });
    try {
        const value = await processProof(child.pid);
        assert.equal(value.pid, child.pid);
        assert.equal(value.status.parent_pid, process.pid);
        assert.ok(value.status.uids.every((uid) => uid > 0));
        assert.deepEqual(await ownedCleanupInventory(child, value), []);
        await assert.rejects(
            ownedCleanupInventory(child, { ...value, start_ticks: "0" }),
            /root identity changed/,
        );
        child.stdin.end();
        await closed;
        await assert.rejects(
            ownedCleanupInventory(child, value),
            /root exited before final cleanup inventory/,
        );
        assert.equal(await descendantsClosed([value]), true);
    } finally {
        if (child.exitCode === null && child.signalCode === null)
            child.kill("SIGTERM");
        await closed;
    }
});
