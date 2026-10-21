/** Metadata refusal tests supplement the separately required real Caddy fixture. */
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { requirePassingTap } from "./test-report.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
mkdirSync(join(root, ".artifacts"), { recursive: true });
const evidence = mkdtempSync(join(root, ".artifacts/functional-driver-"));
console.log(`Retaining functional driver metadata evidence in ${evidence}.`);
const result = spawnSync(
    process.execPath,
    ["--test", "--test-reporter=tap", "test/functional-api/driver.test.mjs"],
    { cwd: root, encoding: "utf8", timeout: 30000, maxBuffer: 4 * 1024 * 1024 },
);
writeFileSync(join(evidence, "report.tap"), result.stdout);
writeFileSync(join(evidence, "stderr.log"), result.stderr);
try {
    if (
        result.error !== undefined ||
        result.signal !== null ||
        result.status !== 0
    )
        throw new Error("Required functional metadata subprocess failed.");
    console.log(
        `Required functional metadata tests: ${String(requirePassingTap(result.stdout))} passed; no skipped tests.`,
    );
} catch {
    console.error(
        "Functional metadata tests failed, timed out or omitted required execution.",
    );
    process.exitCode = 1;
}
