import { defineConfig } from "@playwright/test";
import { lstatSync, readFileSync } from "node:fs";
import { isAbsolute, join } from "node:path";

const evidence = process.env.HFCACHE_READ_BROWSER_EVIDENCE;
const endpoint = process.env.HFCACHE_READ_BROWSER_ENDPOINT;
const origin = process.env.HFCACHE_READ_FIXTURE_ORIGIN;
const tokenFile = process.env.HFCACHE_READ_FIXTURE_TOKEN_FILE;
if (
    evidence === undefined ||
    !isAbsolute(evidence) ||
    endpoint === undefined ||
    !endpoint.startsWith("ws://127.0.0.1:") ||
    origin === undefined ||
    !/^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}$/u.test(origin) ||
    tokenFile === undefined ||
    !isAbsolute(tokenFile)
)
    throw new Error("Run the owned read-fixture wrapper.");
const facts = lstatSync(tokenFile);
if (
    !facts.isFile() ||
    facts.isSymbolicLink() ||
    (facts.mode & 0o777) !== 0o600 ||
    facts.size > 256 ||
    facts.uid !== process.getuid?.()
)
    throw new Error("The generated fixture reader credential is unsafe.");
const token = readFileSync(tokenFile, "ascii");
if (!/^[A-Za-z0-9_-]{32,128}$/u.test(token))
    throw new Error("The generated fixture credential has invalid grammar.");

export default defineConfig({
    testDir: ".",
    testMatch: "read-api.spec.ts",
    forbidOnly: true,
    retries: 0,
    workers: 1,
    timeout: 15000,
    globalTimeout: 90000,
    reporter: [
        ["list"],
        ["json", { outputFile: join(evidence, "report.json") }],
    ],
    outputDir: join(evidence, "results"),
    use: {
        browserName: "chromium",
        connectOptions: { wsEndpoint: endpoint },
        baseURL: origin,
        extraHTTPHeaders: { Authorization: "Bearer " + token },
        trace: "off",
        screenshot: "only-on-failure",
    },
});
