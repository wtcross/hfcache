/** Built startup and owned synthetic UI workflows; no installed/API/host acceptance. */
import { spawn } from "node:child_process";
import type { BrowserServer } from "@playwright/test";
import { createServer } from "node:http";
import {
    existsSync,
    mkdirSync,
    readFileSync,
    readdirSync,
    mkdtempSync,
} from "node:fs";
import { fileURLToPath } from "node:url";
import { join, isAbsolute } from "node:path";
import { requirePassingBrowserReport } from "./test-report.ts";

const options = process.argv.slice(2);
if (options.length > 0) {
    if (options.length === 1 && options[0] === "--help")
        console.log(
            "Usage: pnpm --dir web run test:browser\nChecks built startup refusal, missing-script fallback and owned synthetic UI workflows; requires separately provisioned Chromium. Connected UI acceptance requires the installed shared-Caddy functional runner.",
        );
    else {
        console.error("Unrecognized browser smoke argument.");
        process.exitCode = 2;
    }
} else {
    const root = fileURLToPath(new URL("../", import.meta.url));
    const cache =
        process.env.PLAYWRIGHT_BROWSERS_PATH ??
        join(root, ".cache/ms-playwright");
    if (!isAbsolute(cache))
        throw new Error(
            "PLAYWRIGHT_BROWSERS_PATH must be an absolute owned cache.",
        );
    process.env.PLAYWRIGHT_BROWSERS_PATH = cache;
    const { chromium } = await import("@playwright/test");
    // Playwright resolves its executable from the current explicit cache, never downloads at runtime.
    if (!existsSync(chromium.executablePath()))
        throw new Error(
            "Required Chromium is missing. Provision the pinned browser separately in web/.cache/ms-playwright; no test was skipped.",
        );
    const index = readFileSync(join(root, "dist/index.html"), "utf8");
    // This fixture supplies no successful bootstrap or connected API values.
    // Main must refuse startup; an absent main chunk must preserve inert HTML.
    function refusalIndex(base: string): Buffer {
        return Buffer.from(
            index
                .replaceAll("__HFCACHE_UI_BASE_V1__", base)
                .replaceAll(
                    "__HFCACHE_UI_BOOTSTRAP_V1__",
                    base + "bootstrap.json",
                )
                .replaceAll("__HFCACHE_UI_FINGERPRINT_V1__", "0".repeat(64))
                .replaceAll("__HFCACHE_UI_CONTRACT_V1__", "1"),
        );
    }
    const assets = new Map<string, Buffer>();
    for (const member of readdirSync(join(root, "dist/assets"), {
        withFileTypes: true,
    })) {
        if (!member.isFile()) throw new Error("Unexpected fixture asset type.");
        assets.set(
            `/ui/assets/${member.name}`,
            readFileSync(join(root, "dist/assets", member.name)),
        );
    }
    const indexes = new Map([
        ["/ui/", refusalIndex("/ui/")],
        ["/missing-script/ui/", refusalIndex("/missing-script/ui/")],
    ]);
    const server = createServer((request, response) => {
        const path = request.url;
        const body =
            path === undefined
                ? undefined
                : (indexes.get(path) ?? assets.get(path));
        if (request.method !== "GET" || body === undefined) {
            response.writeHead(404);
            response.end();
            return;
        }
        const contentType =
            path?.endsWith(".js") === true
                ? "text/javascript"
                : path?.endsWith(".css") === true
                  ? "text/css"
                  : path?.endsWith(".png") === true
                    ? "image/png"
                    : "text/html";
        response.writeHead(200, {
            "Content-Type": contentType,
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy":
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'none'",
        });
        response.end(body);
    });
    await new Promise<void>((resolve, reject) => {
        server.once("error", reject);
        server.listen(0, "127.0.0.1", resolve);
    });
    let browserServer: BrowserServer | undefined;
    let browserClosed: Promise<void> | undefined;
    async function boundedDrain(operation: Promise<void>) {
        let deadline: ReturnType<typeof setTimeout> | undefined;
        try {
            await Promise.race([
                operation,
                new Promise<never>((_resolve, reject) => {
                    deadline = setTimeout(() => {
                        reject(
                            new Error(
                                "Owned browser shutdown exceeded five seconds.",
                            ),
                        );
                    }, 5000);
                }),
            ]);
        } finally {
            clearTimeout(deadline);
        }
    }
    try {
        browserServer = await chromium.launchServer({
            headless: true,
            chromiumSandbox: true,
            host: "127.0.0.1",
            port: 0,
            timeout: 15000,
        });
        const browserProcess = browserServer.process();
        console.log(
            `Owned Chromium PID ${String(browserProcess.pid)}; sandbox enabled.`,
        );
        browserClosed = new Promise<void>((resolve) => {
            browserProcess.once("close", () => {
                resolve();
            });
        });
        const address = server.address();
        if (address === null || typeof address === "string")
            throw new Error("The fixture listener is unavailable.");
        mkdirSync(join(root, ".artifacts"), { recursive: true });
        const evidence = mkdtempSync(join(root, ".artifacts/browser-"));
        const report = join(evidence, "report.json");
        console.log(`Retaining browser evidence in ${evidence}.`);
        const child = spawn(
            process.execPath,
            [
                join(root, "node_modules/@playwright/test/cli.js"),
                "test",
                "--config=playwright.config.ts",
            ],
            {
                cwd: root,
                stdio: "inherit",
                env: {
                    ...process.env,
                    HFCACHE_BROWSER_ARTIFACT_DIR: evidence,
                    HFCACHE_BROWSER_ENDPOINT: browserServer.wsEndpoint(),
                    HFCACHE_SHELL_TEST_URL: `http://127.0.0.1:${String(address.port)}`,
                },
                detached: process.platform !== "win32",
            },
        );
        // Chromium is owned separately by this wrapper because Playwright
        // detaches browsers into their own process groups. Bound CLI shutdown
        // independently; browserServer.close/kill below drains the exact browser.
        function signalCli(signal: NodeJS.Signals) {
            if (child.pid === undefined) return;
            try {
                if (process.platform === "win32") child.kill(signal);
                else process.kill(-child.pid, signal);
            } catch (error) {
                if (!(
                    error instanceof Error &&
                    "code" in error &&
                    error.code === "ESRCH"
                ))
                    throw error;
            }
        }
        let forcedShutdown: ReturnType<typeof setTimeout> | undefined;
        const deadlineState = { timedOut: false };
        const deadline = setTimeout(() => {
            deadlineState.timedOut = true;
            signalCli("SIGTERM");
            forcedShutdown = setTimeout(() => {
                signalCli("SIGKILL");
            }, 5000);
        }, 150000);
        let status: number;
        try {
            status = await new Promise<number>((resolve, reject) => {
                child.once("error", reject);
                child.once("close", (code) => {
                    resolve(code ?? 1);
                });
            });
        } finally {
            clearTimeout(deadline);
            clearTimeout(forcedShutdown);
            signalCli("SIGKILL");
        }
        if (deadlineState.timedOut) {
            console.error(
                "Required browser smoke exceeded its outer deadline; no acceptance recorded.",
            );
            process.exitCode = 1;
        } else if (status !== 0) process.exitCode = status;
        else {
            const raw = readFileSync(report);
            if (raw.length > 8 * 1024 * 1024)
                throw new Error("Browser report exceeds its bounds.");
            const parsed: unknown = JSON.parse(raw.toString("utf8"));
            console.log(
                `Built startup and source-fixture Chromium checks: ${String(requirePassingBrowserReport(parsed))} passed; no skipped tests. No installed/Caddy/API/production acceptance claimed.`,
            );
        }
    } finally {
        try {
            if (browserServer !== undefined) {
                try {
                    await boundedDrain(browserServer.close());
                } catch {
                    await boundedDrain(browserServer.kill());
                }
                if (browserClosed === undefined)
                    throw new Error(
                        "Owned browser closure observation is unavailable.",
                    );
                await boundedDrain(browserClosed);
                console.log(
                    `Owned Chromium PID ${String(browserServer.process().pid)} closed.`,
                );
            }
        } finally {
            server.closeAllConnections();
            await new Promise<void>((resolve, reject) => {
                server.close((error) => {
                    if (error) reject(error);
                    else resolve();
                });
            });
            console.log("Owned HTTP fixture listener closed.");
        }
    }
}
