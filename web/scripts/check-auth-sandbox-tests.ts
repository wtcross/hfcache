/** Bounded metadata tests supplement, never substitute for, real browser proof. */
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { requirePassingTap } from "./test-report.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
mkdirSync(join(root, ".artifacts"), { recursive: true });
const evidence = mkdtempSync(join(root, ".artifacts/auth-sandbox-"));
console.log(`Retaining sandbox metadata test evidence in ${evidence}.`);
const result = spawnSync(
    process.execPath,
    ["--test", "--test-reporter=tap", "test/auth-api/sandbox.test.mjs"],
    {
        cwd: root,
        encoding: "utf8",
        timeout: 30000,
        maxBuffer: 4 * 1024 * 1024,
    },
);
writeFileSync(join(evidence, "report.tap"), result.stdout);
writeFileSync(join(evidence, "stderr.log"), result.stderr);
try {
    if (
        result.error !== undefined ||
        result.signal !== null ||
        result.status !== 0
    )
        throw new Error("Required sandbox metadata subprocess failed.");
    console.log(
        `Required sandbox metadata tests: ${String(requirePassingTap(result.stdout))} passed; no skipped tests.`,
    );
} catch {
    console.error(
        "Sandbox metadata tests failed, timed out or omitted required execution.",
    );
    process.exitCode = 1;
}
