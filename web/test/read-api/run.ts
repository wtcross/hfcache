/** Own only the fixture browser/runner; the Python parent owns the real API. */
import { spawn } from "node:child_process";
import type { ChildProcess } from "node:child_process";
import {
    existsSync,
    mkdirSync,
    mkdtempSync,
    readFileSync,
    writeFileSync,
} from "node:fs";
import { fileURLToPath } from "node:url";
import { isAbsolute, join } from "node:path";
import type { BrowserServer } from "@playwright/test";
import { requirePassingBrowserReport } from "../../scripts/test-report.ts";
import { requireOwnedProfile } from "./ownership.ts";

const arguments_ = process.argv.slice(2);
if (arguments_.length !== 0) {
    if (arguments_.length === 1 && arguments_[0] === "--help")
        console.log(
            "Usage: run through scripts/check-web-read-fixture.py. Retains an owned real API read fixture; no Caddy or installed acceptance.",
        );
    else {
        console.error("Unknown read-fixture browser argument.");
        process.exitCode = 2;
    }
} else {
    const root = fileURLToPath(new URL("../../", import.meta.url));
    const origin = process.env.HFCACHE_READ_FIXTURE_ORIGIN;
    const workspace = process.env.HFCACHE_READ_FIXTURE_WORKSPACE;
    const cache = process.env.PLAYWRIGHT_BROWSERS_PATH;
    const tokenFile = process.env.HFCACHE_READ_FIXTURE_TOKEN_FILE;
    if (
        origin === undefined ||
        !/^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}$/u.test(origin) ||
        workspace === undefined ||
        !isAbsolute(workspace) ||
        cache === undefined ||
        !isAbsolute(cache) ||
        tokenFile === undefined
    )
        throw new Error(
            "A positively owned loopback read fixture is required.",
        );
    requireOwnedProfile(workspace, root, cache, tokenFile);
    const { chromium } = await import("@playwright/test");
    if (!existsSync(chromium.executablePath()))
        throw new Error(
            "Required pinned Chromium is missing; provision it separately. No test was skipped.",
        );
    mkdirSync(join(workspace, "browser"), { recursive: false });
    const evidence = mkdtempSync(join(workspace, "browser/run-"));
    let browser: BrowserServer | undefined;
    let closed: Promise<void> | undefined;
    let cli: ChildProcess | undefined;
    let force: ReturnType<typeof setTimeout> | undefined;
    const lifecycle = { interrupted: false, timedOut: false };
    function signalCli(signal: NodeJS.Signals) {
        if (cli?.pid === undefined) return;
        try {
            process.kill(-cli.pid, signal);
        } catch (error) {
            if (!(
                error instanceof Error &&
                "code" in error &&
                error.code === "ESRCH"
            ))
                throw error;
        }
    }
    function interrupt() {
        lifecycle.interrupted = true;
        signalCli("SIGTERM");
        if (cli !== undefined && force === undefined)
            force = setTimeout(() => {
                signalCli("SIGKILL");
            }, 5000);
    }
    process.on("SIGTERM", interrupt);
    process.on("SIGINT", interrupt);
    async function bounded(operation: Promise<void>) {
        let timer: ReturnType<typeof setTimeout> | undefined;
        try {
            await Promise.race([
                operation,
                new Promise<never>((_resolve, reject) => {
                    timer = setTimeout(() => {
                        reject(
                            new Error(
                                "Owned browser drain is unknown after five seconds.",
                            ),
                        );
                    }, 5000);
                }),
            ]);
        } finally {
            clearTimeout(timer);
        }
    }
    try {
        browser = await chromium.launchServer({
            host: "127.0.0.1",
            port: 0,
            headless: true,
            chromiumSandbox: true,
            timeout: 15000,
        });
        const child = browser.process();
        console.log(
            `Owned read-fixture Chromium PID ${String(child.pid)}; sandbox enabled.`,
        );
        closed = new Promise<void>((resolve) => {
            child.once("close", () => {
                resolve();
            });
        });
        if (lifecycle.interrupted)
            throw new Error(
                "Owned read fixture was interrupted before execution.",
            );
        cli = spawn(
            process.execPath,
            [
                join(root, "node_modules/@playwright/test/cli.js"),
                "test",
                "--config=test/read-api/playwright.config.ts",
            ],
            {
                cwd: root,
                env: {
                    ...process.env,
                    HFCACHE_READ_BROWSER_EVIDENCE: evidence,
                    HFCACHE_READ_BROWSER_ENDPOINT: browser.wsEndpoint(),
                },
                stdio: "inherit",
                detached: true,
            },
        );
        const timer = setTimeout(() => {
            lifecycle.timedOut = true;
            signalCli("SIGTERM");
            force = setTimeout(() => {
                signalCli("SIGKILL");
            }, 5000);
        }, 100000);
        let status: number;
        try {
            status = await new Promise<number>((resolve, reject) => {
                cli?.once("error", reject);
                cli?.once("close", (code) => {
                    resolve(code ?? 1);
                });
            });
        } finally {
            clearTimeout(timer);
            clearTimeout(force);
            signalCli("SIGKILL");
        }
        if (
            [lifecycle.timedOut, lifecycle.interrupted].includes(true) ||
            status !== 0
        ) {
            process.exitCode = status !== 0 ? status : 1;
        } else {
            const raw = readFileSync(join(evidence, "report.json"));
            if (raw.length > 8 * 1024 * 1024)
                throw new Error("Required browser report is oversized.");
            const value: unknown = JSON.parse(raw.toString("utf8"));
            const count = requirePassingBrowserReport(value);
            console.log(
                `Real HTTP/API React read fixture: ${String(count)} passed; no skipped or retried tests.`,
            );
        }
    } finally {
        try {
            if (browser !== undefined) {
                try {
                    await bounded(browser.close());
                } catch {
                    await bounded(browser.kill());
                }
                if (closed === undefined)
                    throw new Error(
                        "Exact browser closure was not observable.",
                    );
                await bounded(closed);
                const pid = browser.process().pid;
                writeFileSync(
                    join(evidence, "owned-browser.json"),
                    JSON.stringify({
                        schema_version: 1,
                        pid,
                        close_observed: true,
                        proc_absent: !existsSync(`/proc/${String(pid)}`),
                    }) + "\n",
                );
                if (existsSync(`/proc/${String(pid)}`))
                    throw new Error("Owned browser PID remained after close.");
                console.log(
                    `Owned read-fixture Chromium PID ${String(pid)} closed.`,
                );
            }
        } finally {
            process.off("SIGTERM", interrupt);
            process.off("SIGINT", interrupt);
        }
    }
}
