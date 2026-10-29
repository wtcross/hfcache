/** Read bounded metadata from the exact browser process and its owned tree. */
import assert from "node:assert/strict";
import { readFile, readdir, readlink } from "node:fs/promises";

const MAX_BYTES = 65_536;
const MAX_PROCESSES = 128;
const MAX_THREADS = 1024;
const CHROMIUM_EXECUTABLE =
    "/ms-playwright/chromium-1248/chrome-linux64/chrome";
const PROCESS_STATES = new Set([
    "R",
    "S",
    "D",
    "Z",
    "T",
    "t",
    "X",
    "x",
    "K",
    "W",
    "P",
    "I",
]);
const DISABLED = new Set([
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-seccomp-filter-sandbox",
    "--disable-namespace-sandbox",
    "--single-process",
]);

/** Diagnostic messages are scrubbed before truncation; no stacks or headers. */
export function safeDiagnostic(error, credentials = {}) {
    let message =
        typeof error?.message === "string" ? error.message : "unknown failure";
    // Refuse oversized input rather than searching an unbounded dependency message.
    if (message.length > 65_536) message = "oversized diagnostic withheld";
    const pair = `${credentials.username ?? ""}:${credentials.password ?? ""}`;
    const secrets = [
        credentials.password,
        credentials.username,
        credentials.password && encodeURIComponent(credentials.password),
        credentials.password &&
            Buffer.from(credentials.password).toString("base64"),
        credentials.password && Buffer.from(pair).toString("base64"),
    ].filter((value) => typeof value === "string" && value.length > 0);
    for (const value of secrets.sort((a, b) => b.length - a.length))
        message = message.split(value).join("[REDACTED]");
    message = message
        .replace(/[^\x20-\x7e\n\t]/g, "?")
        .replace(
            /^.*(?:authorization|password|username|password_hash)\s*["']?\s*[:=].*$/gim,
            "[credential line withheld]",
        )
        .replace(/\b(?:Basic|Bearer)\s+[^\s"']+/gi, "[authentication withheld]")
        .replace(/\$argon2[^\s"']+/g, "[password hash withheld]")
        .replace(
            /(https?:\/\/)[^\s/@]+:[^\s/@]+@/gi,
            "$1[credentials withheld]@",
        )
        .slice(0, 8192);
    const name = [
        "Error",
        "AssertionError",
        "TimeoutError",
        "ProtocolError",
    ].includes(error?.name)
        ? error.name
        : "Error";
    return { name, message };
}

export function assertApplicationIdentity(value) {
    assert.equal(typeof value, "string");
    assert.ok(value.length > 0 && value.length <= 128);
    assert.ok(
        [...value].every(
            (character) =>
                character.charCodeAt(0) >= 0x20 &&
                character.charCodeAt(0) <= 0x7e,
        ),
    );
}

export function assertVersionPayload(payload, expectedApplication) {
    assertApplicationIdentity(expectedApplication);
    assert.equal(payload.schema_version, 1);
    const data = payload.envelope.data;
    assert.deepEqual(Object.keys(data).sort(), [
        "application",
        "huggingface_hub",
        "python",
        "transfer_backend",
    ]);
    for (const value of Object.values(data)) {
        assert.equal(typeof value, "string");
        assert.ok(value.length > 0 && value.length <= 256);
    }
    assert.equal(data.application, expectedApplication);
}

export function nativeNetworkObserver(origins) {
    const state = {
        mode: "passive-origin-observer",
        request_interception: false,
        limit: 256,
        request_count: 0,
        expected_origins: { ...origins },
        invalid: false,
        overflow: false,
        observations: [],
    };
    const observe = (raw) => {
        state.request_count = Math.min(
            state.request_count + 1,
            state.limit + 1,
        );
        if (state.request_count > state.limit) {
            state.overflow = true;
            return;
        }
        let category;
        let scheme = "other";
        let host = "[outside-owned-origins]";
        let port = null;
        try {
            assert.equal(typeof raw, "string");
            assert.ok(Buffer.byteLength(raw) <= 4096);
            const target = new URL(raw);
            scheme = ["http:", "https:"].includes(target.protocol)
                ? target.protocol
                : "other";
            port = target.port ? Number(target.port) : null;
            category =
                Object.keys(origins).find(
                    (key) => origins[key] === target.origin,
                ) ?? "unexpected";
            if (target.username || target.password) category = "userinfo";
            if (["trusted", "foreign", "untrusted"].includes(category))
                host = target.hostname;
        } catch {
            category = "unparseable";
        }
        if (!["trusted", "foreign", "untrusted"].includes(category))
            state.invalid = true;
        state.observations.push({ category, scheme, host, port });
    };
    return { state, observe };
}

export function assertNativeNetworkObservation(state) {
    assert.equal(state.mode, "passive-origin-observer");
    assert.equal(state.request_interception, false);
    assert.equal(state.invalid, false);
    assert.equal(state.overflow, false);
    assert.ok(
        Number.isSafeInteger(state.request_count) &&
            state.request_count > 0 &&
            state.request_count <= state.limit,
    );
    assert.equal(state.observations.length, state.request_count);
}

function exited(error) {
    return error?.code === "ENOENT" || error?.code === "ESRCH";
}

async function bounded(file) {
    const value = await readFile(file);
    assert.ok(value.byteLength <= MAX_BYTES);
    return value.toString("utf8");
}

export function parseStatus(text) {
    assert.ok(Buffer.byteLength(text) <= MAX_BYTES);
    const values = new Map();
    for (const line of text.split("\n")) {
        const separator = line.indexOf(":");
        if (separator < 0) continue;
        const key = line.slice(0, separator);
        assert.ok(!values.has(key));
        values.set(key, line.slice(separator + 1).trim());
    }
    const uids = values.get("Uid")?.split(/\s+/).map(Number);
    assert.ok(uids?.length === 4 && uids.every(Number.isSafeInteger));
    const capEff = values.get("CapEff");
    assert.match(capEff, /^[0-9a-f]{16}$/);
    const parent = Number(values.get("PPid"));
    assert.ok(Number.isSafeInteger(parent) && parent >= 0);
    const nnp = Number(values.get("NoNewPrivs"));
    const seccomp = Number(values.get("Seccomp"));
    const state = values.get("State")?.split(/\s+/)[0];
    assert.ok(PROCESS_STATES.has(state));
    assert.ok([0, 1].includes(nnp));
    assert.ok([0, 1, 2].includes(seccomp));
    return {
        uids,
        cap_eff: capEff,
        parent_pid: parent,
        no_new_privs: nnp,
        seccomp,
        state,
    };
}

export function parseStat(text, expectedPid) {
    // Linux6.12 proc field authority and PID reuse warning:
    // https://docs.kernel.org/6.12/filesystems/proc.html
    assert.ok(Buffer.byteLength(text) <= MAX_BYTES);
    const separator = text.indexOf(" (");
    const closing = text.lastIndexOf(") ");
    assert.ok(separator > 0 && closing > separator);
    const pidText = text.slice(0, separator);
    assert.ok(
        [...pidText].every((character) => character >= "0" && character <= "9"),
    );
    const pid = Number(pidText);
    assert.ok(Number.isSafeInteger(pid) && pid > 1);
    assert.equal(pid, expectedPid);
    const fields = text
        .slice(closing + 2)
        .trimEnd()
        .split(" ");
    assert.ok(fields.length >= 20 && PROCESS_STATES.has(fields[0]));
    const parentText = fields[1];
    const start = fields[19];
    for (const value of [parentText, start])
        assert.ok(
            value.length > 0 &&
                [...value].every(
                    (character) => character >= "0" && character <= "9",
                ),
        );
    const parent = Number(parentText);
    assert.ok(Number.isSafeInteger(parent) && parent >= 0);
    return { pid, parent_pid: parent, state: fields[0], start_ticks: start };
}

export function classifyProcess(before, after, status, command) {
    // proc_pid_cmdline(5): zombies have zero-byte cmdline; live tasks can also
    // rewrite argv. Empty bytes alone therefore never establish exit.
    // https://man7.org/linux/man-pages/man5/proc_pid_cmdline.5.html
    assert.equal(before.pid, after.pid);
    assert.equal(before.start_ticks, after.start_ticks);
    assert.equal(before.parent_pid, after.parent_pid);
    assert.equal(status.parent_pid, after.parent_pid);
    if (
        before.state === "Z" &&
        after.state === "Z" &&
        status.state === "Z" &&
        command === ""
    )
        return { kind: "zombie", command: null };
    if ([before.state, after.state, status.state].includes("Z")) return null;
    if (command === "")
        throw new Error(
            `Empty command refused: pid=${after.pid} start=${after.start_ticks} parent=${after.parent_pid} stat_before=${before.state} stat_after=${after.state} status=${status.state}`,
        );
    assert.ok(
        ![before.state, after.state, status.state].some(
            (state) => state === "X" || state === "x",
        ),
    );
    return { kind: "live", command: commandProof(command) };
}

export function commandProof(raw) {
    assert.ok(Buffer.byteLength(raw) <= MAX_BYTES);
    const args = raw.split("\0").filter(Boolean);
    assert.ok(args.length > 0 && args.length < 256);
    let tokens = args;
    let title = false;
    if (args[0].includes(" ")) {
        // Chromium156 joins its executable and original argv with literal spaces,
        // losing boundaries and potentially truncating at the available memory.
        // This is observed title syntax, never reconstructed/executable argv:
        // https://raw.githubusercontent.com/chromium/chromium/156.0.8078.4/base/process/set_process_title.cc
        // https://raw.githubusercontent.com/chromium/chromium/156.0.8078.4/base/process/set_process_title_linux.cc
        assert.equal(args.length, 1);
        assert.ok(args[0].startsWith(CHROMIUM_EXECUTABLE + " "));
        assert.ok(
            [...args[0]].every(
                (character) =>
                    character.charCodeAt(0) >= 0x20 &&
                    character.charCodeAt(0) <= 0x7e,
            ),
        );
        assert.ok(!/["'\\]/.test(args[0]));
        // A real Chromium title can be truncated immediately after a separator.
        // Drop exactly that one final separator for token checks, retaining the
        // original bytes and the existing lossy/observed-only qualifications.
        const tokenTitle = args[0].endsWith(" ")
            ? args[0].slice(0, -1)
            : args[0];
        tokens = tokenTitle.split(" ");
        assert.ok(
            tokens.length < 256 && tokens.every((token) => token.length > 0),
        );
        assert.ok(
            [
                "--type=renderer",
                "--type=zygote",
                "--type=utility",
                "--type=gpu-process",
            ].includes(tokens[1]),
        );
        title = true;
    } else {
        // A combined unknown title using other whitespace is not a normal argv0.
        assert.ok(!/\s/.test(args[0]));
    }
    assert.ok(!tokens.some((arg) => DISABLED.has(arg.split("=", 1)[0])));
    const types = tokens
        .slice(1)
        .filter((token) => token.startsWith("--type="));
    assert.ok(types.length <= 1);
    return {
        raw_command_line: raw,
        arguments: args,
        representation: title ? "chromium-process-title" : "nul-separated-argv",
        ...(title
            ? {
                  title_tokens: tokens,
                  original_argument_boundaries_recoverable: false,
                  title_may_be_truncated: true,
                  observed_disabling_flags_absent: true,
                  flag_check_scope: "observed-title-only",
              }
            : {
                  disabling_flags_absent: true,
                  flag_check_scope: "observed-nul-argv",
              }),
        renderer:
            tokens[0] === CHROMIUM_EXECUTABLE && types[0] === "--type=renderer",
    };
}

export function requireUnprivileged(proof) {
    assert.equal(proof.kind, "live");
    assert.ok(proof.status.uids.every((uid) => uid > 0));
    assert.equal(BigInt("0x" + proof.status.cap_eff), 0n);
    assert.equal(proof.status.no_new_privs, 1);
    if (proof.command.representation === "chromium-process-title") {
        assert.equal(proof.command.observed_disabling_flags_absent, true);
        assert.equal(proof.command.flag_check_scope, "observed-title-only");
        assert.equal(
            proof.command.original_argument_boundaries_recoverable,
            false,
        );
    } else {
        assert.equal(proof.command.representation, "nul-separated-argv");
        assert.equal(proof.command.disabling_flags_absent, true);
    }
}

export async function processProof(pid) {
    assert.ok(Number.isSafeInteger(pid) && pid > 1);
    for (let attempt = 0; attempt < 3; attempt += 1) {
        const before = parseStat(await bounded(`/proc/${pid}/stat`), pid);
        const [statusText, command, uidMap] = await Promise.all([
            bounded(`/proc/${pid}/status`),
            bounded(`/proc/${pid}/cmdline`),
            bounded(`/proc/${pid}/uid_map`),
        ]);
        const status = parseStatus(statusText);
        const namespaces = {};
        for (const kind of ["pid", "user", "net"]) {
            try {
                namespaces[kind] = await readlink(`/proc/${pid}/ns/${kind}`);
            } catch {
                namespaces[kind] = "unreadable-by-unprivileged-observer";
            }
        }
        const after = parseStat(await bounded(`/proc/${pid}/stat`), pid);
        const classification = classifyProcess(before, after, status, command);
        if (classification === null) {
            if (attempt < 2) continue;
            throw new Error(
                `Unstable zombie transition refused: pid=${pid} start=${after.start_ticks} parent=${after.parent_pid} stat_before=${before.state} stat_after=${after.state} status=${status.state} command_bytes=${Buffer.byteLength(command)}`,
            );
        }
        return {
            pid,
            start_ticks: after.start_ticks,
            state: after.state,
            ...classification,
            status,
            uid_map: uidMap,
            namespaces,
        };
    }
}

export async function processIdentity(pid) {
    assert.ok(Number.isSafeInteger(pid) && pid > 1);
    const before = parseStat(await bounded(`/proc/${pid}/stat`), pid);
    const status = parseStatus(await bounded(`/proc/${pid}/status`));
    const after = parseStat(await bounded(`/proc/${pid}/stat`), pid);
    assert.equal(before.pid, after.pid);
    assert.equal(before.start_ticks, after.start_ticks);
    assert.equal(before.parent_pid, after.parent_pid);
    assert.equal(status.parent_pid, after.parent_pid);
    // Cleanup only follows exact owned identities. A native browser may rewrite
    // its display title; that text supplies no executable/renderer authority.
    return {
        kind: "cleanup-identity",
        pid,
        start_ticks: after.start_ticks,
        state: after.state,
        status: { parent_pid: status.parent_pid, state: status.state },
        authority: "cleanup-only",
    };
}

async function walkOwnedProcesses(rootPid, readProcess) {
    const queue = [rootPid];
    const seen = new Set(queue);
    const results = [];
    while (queue.length) {
        const parent = queue.shift();
        let threads;
        try {
            threads = await readdir(`/proc/${parent}/task`);
        } catch (error) {
            if (exited(error)) continue;
            throw error;
        }
        assert.ok(threads.length <= MAX_THREADS);
        for (const thread of threads) {
            assert.match(thread, /^[0-9]+$/);
            let children;
            try {
                children = await bounded(
                    `/proc/${parent}/task/${thread}/children`,
                );
            } catch (error) {
                if (exited(error)) continue;
                throw error;
            }
            for (const value of children.trim().split(/\s+/).filter(Boolean)) {
                assert.match(value, /^[0-9]+$/);
                const pid = Number(value);
                if (seen.has(pid)) continue;
                assert.ok(seen.size < MAX_PROCESSES);
                seen.add(pid);
                let proof;
                try {
                    proof = await readProcess(pid);
                } catch (error) {
                    if (exited(error)) continue;
                    throw error;
                } // Exited owned children are not proof of a live renderer.
                assert.equal(proof.status.parent_pid, parent);
                results.push(proof);
                if (
                    proof.kind === "live" ||
                    (proof.kind === "cleanup-identity" && proof.state !== "Z")
                )
                    queue.push(pid);
            }
        }
    }
    return results;
}

export async function ownedDescendants(rootPid) {
    return walkOwnedProcesses(rootPid, processProof);
}

export async function ownedProcessIdentities(rootPid) {
    return walkOwnedProcesses(rootPid, processIdentity);
}

export async function ownedCleanupInventory(child, rootProof) {
    assert.equal(rootProof?.kind, "live");
    assert.equal(child.pid, rootProof.pid);
    const assertRunning = () => {
        if (child.exitCode !== null || child.signalCode !== null)
            throw new Error(
                "Owned browser root exited before final cleanup inventory",
            );
    };
    const assertIdentity = (identity) => {
        if (
            identity.pid !== rootProof.pid ||
            identity.start_ticks !== rootProof.start_ticks
        )
            throw new Error(
                "Owned browser root identity changed during cleanup inventory",
            );
        assert.ok(
            ![identity.state, identity.status.state].some((state) =>
                ["Z", "X", "x"].includes(state),
            ),
        );
    };
    assertRunning();
    assertIdentity(await processIdentity(child.pid));
    const descendants = await ownedProcessIdentities(child.pid);
    assertIdentity(await processIdentity(child.pid));
    assertRunning();
    return descendants;
}

export async function descendantsClosed(proofs) {
    const expires = Date.now() + 5000;
    do {
        const live = [];
        for (const proof of proofs) {
            try {
                const value = parseStat(
                    await bounded(`/proc/${proof.pid}/stat`),
                    proof.pid,
                );
                // An unreaped zombie still has this exact identity and is not
                // complete drain. Only disappearance/reuse retires this proof.
                if (value.start_ticks === proof.start_ticks)
                    live.push(proof.pid);
            } catch (error) {
                if (!exited(error)) live.push(proof.pid);
            }
        }
        if (live.length === 0) return true;
        await new Promise((resolve) => {
            setTimeout(resolve, 50);
        });
    } while (Date.now() < expires);
    return false;
}

export async function chromiumProof(
    browser,
    rootProof,
    result = { verified: false },
) {
    const context = await browser.newContext({
        serviceWorkers: "block",
        ignoreHTTPSErrors: false,
    });
    try {
        const page = await context.newPage();
        await page.goto("chrome://sandbox", { timeout: 15_000 });
        const rows = await page
            .locator("#sandbox-status tr")
            .evaluateAll((elements) =>
                elements.map((row) =>
                    [...row.querySelectorAll("td")].map(
                        (item) => item.textContent,
                    ),
                ),
            );
        const status = Object.fromEntries(rows);
        result.diagnostics = status;
        const evaluation = await page.locator("#evaluation").innerText();
        result.evaluation = evaluation;
        assert.equal(status["Layer 1 Sandbox"], "Namespace");
        assert.equal(status["PID namespaces"], "Yes");
        assert.equal(status["Network namespaces"], "Yes");
        assert.equal(status["Seccomp-BPF sandbox"], "Yes");
        assert.equal(evaluation, "You are adequately sandboxed.");
        const descendants = await ownedDescendants(rootProof.pid);
        result.observed_descendants = descendants;
        const renderers = descendants.filter(
            (item) => item.kind === "live" && item.command.renderer,
        );
        result.renderers = renderers;
        assert.ok(renderers.length > 0);
        for (const renderer of renderers) {
            requireUnprivileged(renderer);
            assert.equal(renderer.status.seccomp, 2);
            for (const kind of ["pid", "user", "net"]) {
                const value = renderer.namespaces[kind];
                if (value !== "unreadable-by-unprivileged-observer") {
                    assert.notEqual(value, rootProof.namespaces[kind]);
                }
            }
        }
        result.verified = true;
    } finally {
        await context.close();
    }
    return result;
}
