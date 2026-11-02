import { defineConfig } from "@playwright/test";
import { isAbsolute, join } from "node:path";

const evidence = process.env.HFCACHE_BROWSER_ARTIFACT_DIR;
const endpoint = process.env.HFCACHE_BROWSER_ENDPOINT;
if (endpoint === undefined || !endpoint.startsWith("ws://127.0.0.1:"))
    throw new Error("The owned Chromium endpoint is unavailable.");
if (evidence === undefined || !isAbsolute(evidence))
    throw new Error(
        "Run the owned browser-smoke wrapper to retain per-run evidence.",
    );

export default defineConfig({
    testDir: "./test/browser",
    forbidOnly: true,
    retries: 0,
    workers: 1,
    timeout: 15000,
    globalTimeout: 120000,
    reporter: [
        ["list"],
        ["json", { outputFile: join(evidence, "report.json") }],
    ],
    outputDir: join(evidence, "results"),
    use: {
        browserName: "chromium",
        headless: true,
        connectOptions: { wsEndpoint: endpoint },
        baseURL: process.env.HFCACHE_SHELL_TEST_URL,
        viewport: { width: 1440, height: 1000 },
        trace: "off",
        screenshot: "only-on-failure",
    },
});
