import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, mkdtempSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { requirePassingReport } from "./test-report.ts";

const arguments_ = process.argv.slice(2);
if (
    arguments_.length !== 1 ||
    !["unit", "component"].includes(arguments_[0] ?? "")
) {
    console.error("Usage: node scripts/test-suite.ts unit|component");
    process.exitCode = 2;
} else {
    const root = fileURLToPath(new URL("../", import.meta.url));
    mkdirSync(new URL("../.artifacts/", import.meta.url), { recursive: true });
    const evidence = mkdtempSync(
        join(root, `.artifacts/${arguments_[0] ?? ""}-`),
    );
    const report = join(evidence, "report.json");
    console.log(`Retaining test evidence in ${evidence}.`);
    const options =
        arguments_[0] === "unit"
            ? ["--project", "unit"]
            : [
                  "--coverage",
                  `--coverage.reportsDirectory=${join(evidence, "coverage")}`,
              ];
    const result = spawnSync(
        process.execPath,
        [
            fileURLToPath(
                new URL("../node_modules/vitest/vitest.mjs", import.meta.url),
            ),
            "run",
            ...options,
            "--reporter=default",
            "--reporter=json",
            `--outputFile=${report}`,
        ],
        { cwd: root, stdio: "inherit", timeout: 120000 },
    );
    if (
        result.error !== undefined ||
        result.signal !== null ||
        result.status !== 0
    ) {
        console.error(
            "Required test subprocess failed, timed out or was signalled; no acceptance recorded.",
        );
        process.exitCode =
            result.status !== null && result.status !== 0 ? result.status : 1;
    } else {
        try {
            const raw = readFileSync(report);
            if (raw.length > 8 * 1024 * 1024)
                throw new Error("Test report exceeds its bounds.");
            const parsed: unknown = JSON.parse(raw.toString("utf8"));
            console.log(
                `Required ${arguments_[0] ?? ""} check: ${String(requirePassingReport(parsed))} passed; no skipped tests.`,
            );
        } catch {
            console.error(
                "Required test report refused: missing, skipped, failed or inconsistent execution.",
            );
            process.exitCode = 1;
        }
    }
}
